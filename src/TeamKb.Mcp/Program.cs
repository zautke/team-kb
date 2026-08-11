using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using TeamKb.Core;

// Config SSoT: vault root from env (TEAMKB_VAULT), no hardcoded paths.
var vaultRoot = Environment.GetEnvironmentVariable("TEAMKB_VAULT")
    ?? throw new InvalidOperationException("Set TEAMKB_VAULT to the vault root directory.");

var builder = Host.CreateApplicationBuilder(args);
builder.Services.AddSingleton(new VaultStore(vaultRoot));
builder.Services
    .AddMcpServer()
    .WithStdioServerTransport()
    .WithToolsFromAssembly();

await builder.Build().RunAsync();
