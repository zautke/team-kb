#!/usr/bin/env pwsh
# otel-stack.ps1 — PowerShell twin of otel-stack.sh (same actions, same .env SSoT).
# Runbook: docs/research/otel-agentic-csharp/09-local-deployment.md
[CmdletBinding()]
param(
    [Alias('a')][string]$Action = '',
    # Named StackProfile because $Profile is a PowerShell automatic variable.
    [Alias('p', 'Profile')][string]$StackProfile = '',
    [Alias('c')][string]$Config = '',
    [Alias('h')][switch]$Help
)

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Usage {
    @'
Usage: otel-stack.ps1 -Action <action> [-Profile <profile>] [-Config <collector-config>]

Actions:
  -Action  (-a)   up | down | status | logs | validate | smoke
  -Profile (-p)   optional compose profile: cosmos  (starts the Cosmos emulator)
  -Config  (-c)   collector config path relative to this dir
                  (default collector/config.yaml; Azure: collector/config-azure.yaml)
  -Help    (-h)   this help

Examples:
  ./otel-stack.ps1 -a up                          # aspire + collector + bridge (file sink)
  ./otel-stack.ps1 -a up -p cosmos                # + Cosmos emulator
  ./otel-stack.ps1 -a up -c collector/config-azure.yaml   # + Azure Monitor pipeline
  ./otel-stack.ps1 -a smoke                       # send one test span, verify end to end
  ./otel-stack.ps1 -a status                      # health of every service
  ./otel-stack.ps1 -a down
'@
}

if ($Help -or -not $Action) { Usage; exit ([int](-not $Help)) }

Set-Location $ScriptDir
if (-not (Test-Path '.env')) {
    Write-Error 'No .env — run: Copy-Item .env.example .env  (then edit)'
}

# Load .env into both $Env and a local table (compose reads .env itself).
$DotEnv = @{}
foreach ($line in Get-Content '.env') {
    if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)=(.*)$') {
        $DotEnv[$Matches[1]] = $Matches[2]
        Set-Item -Path "Env:$($Matches[1])" -Value $Matches[2]
    }
}
function Get-Cfg([string]$Key, [string]$Default = '') {
    if ($DotEnv.ContainsKey($Key) -and $DotEnv[$Key]) { $DotEnv[$Key] } else { $Default }
}

$Compose = @('docker', 'compose')
if ($StackProfile) { $Compose += @('--profile', $StackProfile) }

function Apply-Config {
    if ($Config -and $Config -ne 'collector/config.yaml') {
        if (-not (Test-Path $Config)) { Write-Error "Config not found: $Config" }
        Copy-Item $Config 'collector/config.active.yaml' -Force
        Write-Host "NOTE: using $Config (copied to collector/config.active.yaml)"
        $env:COLLECTOR_CONFIG = '/etc/otelcol/config.active.yaml'
    }
    else {
        $env:COLLECTOR_CONFIG = '/etc/otelcol/config.yaml'
    }
}

switch ($Action) {
    'up' {
        Apply-Config
        if ($Config -like '*azure*' -and -not (Get-Cfg 'AZURE_MONITOR_CONNECTION_STRING')) {
            Write-Error 'AZURE_MONITOR_CONNECTION_STRING is empty in .env — required for the Azure config.'
        }
        & $Compose[0] $Compose[1..($Compose.Count - 1)] up -d --build
        $ui = Get-Cfg 'ASPIRE_UI_PORT'; $grpc = Get-Cfg 'OTLP_GRPC_PORT'
        Write-Host ''
        Write-Host "Aspire dashboard:  http://localhost:$ui"
        Write-Host "OTLP ingest:       grpc://localhost:$grpc  http://localhost:$(Get-Cfg 'OTLP_HTTP_PORT')"
        Write-Host "Bridge health:     http://localhost:$(Get-Cfg 'BRIDGE_PORT')/healthz"
        Write-Host ''
        Write-Host 'Point an app at it with:'
        Write-Host "  `$env:OTEL_EXPORTER_OTLP_ENDPOINT = 'http://localhost:$grpc'"
        Write-Host "  `$env:TEAMKB_SESSION_ID = [guid]::NewGuid().ToString()"
        Write-Host "  `$env:TEAMKB_SESSION_NAME = 'my-session'"
    }
    'down' {
        & $Compose[0] $Compose[1..($Compose.Count - 1)] down
    }
    'status' {
        & $Compose[0] $Compose[1..($Compose.Count - 1)] ps
        Write-Host ''
        try {
            Invoke-RestMethod "http://localhost:$(Get-Cfg 'COLLECTOR_HEALTH_PORT' '14313')/" | Out-Null
            Write-Host 'collector health: OK'
        } catch { Write-Host 'collector health: FAIL' }
        try {
            $h = Invoke-RestMethod "http://localhost:$(Get-Cfg 'BRIDGE_PORT')/healthz"
            Write-Host "bridge health:    OK (sink: $($h.sink))"
        } catch { Write-Host 'bridge health:    FAIL' }
    }
    'logs' {
        & $Compose[0] $Compose[1..($Compose.Count - 1)] logs -f --tail 100
    }
    'validate' {
        Apply-Config
        docker run --rm -v "${ScriptDir}/collector:/etc/otelcol:ro" `
            (Get-Cfg 'OTEL_COLLECTOR_IMAGE') validate --config $env:COLLECTOR_CONFIG
        Write-Host "collector config valid: $($env:COLLECTOR_CONFIG)"
    }
    'smoke' {
        # One synthetic span via OTLP/HTTP JSON. Verifies: collector ingest ->
        # bridge sink (and Aspire display; check the UI for trace 'smoke-step').
        $now = [long]([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()) * 1000000
        $rng = [System.Random]::new()
        $traceId = -join (1..16 | ForEach-Object { '{0:x2}' -f $rng.Next(256) })
        $spanId  = -join (1..8  | ForEach-Object { '{0:x2}' -f $rng.Next(256) })
        $body = @{
            resourceSpans = @(@{
                resource   = @{ attributes = @(@{ key = 'service.name'; value = @{ stringValue = 'smoke' } }) }
                scopeSpans = @(@{
                    scope = @{ name = 'smoke' }
                    spans = @(@{
                        traceId = $traceId; spanId = $spanId; name = 'smoke-step'; kind = 1
                        startTimeUnixNano = "$now"; endTimeUnixNano = "$($now + 250000000)"
                        attributes = @(
                            @{ key = 'session.id';   value = @{ stringValue = 'smoke-session' } },
                            @{ key = 'session.name'; value = @{ stringValue = 'smoke' } }
                        )
                    })
                })
            })
        } | ConvertTo-Json -Depth 12
        Invoke-RestMethod -Method Post -ContentType 'application/json' `
            -Uri "http://localhost:$(Get-Cfg 'OTLP_HTTP_PORT')/v1/traces" -Body $body | Out-Null
        Write-Host "sent trace $traceId"
        Start-Sleep -Seconds 4
        if ((Test-Path 'data/spans.jsonl') -and (Select-String -Quiet -Path 'data/spans.jsonl' -Pattern $traceId)) {
            Write-Host 'SMOKE PASS: span reached the bridge file sink (data/spans.jsonl)'
        }
        else {
            Write-Host "bridge file sink miss — if using Cosmos, query container '$(Get-Cfg 'COSMOS_CONTAINER')' for traceId $traceId"
        }
        Write-Host "Aspire check: http://localhost:$(Get-Cfg 'ASPIRE_UI_PORT') -> Traces -> 'smoke-step'"
    }
    default {
        Write-Host "Unknown action: $Action" -ForegroundColor Red
        Usage; exit 1
    }
}
