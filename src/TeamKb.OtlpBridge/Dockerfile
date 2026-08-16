# TeamKb.OtlpBridge — multi-stage build, ~110 MB runtime image.
# Built by deploy/otel/docker-compose.yml (service: otlp-bridge).
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src
COPY TeamKb.OtlpBridge.csproj .
RUN dotnet restore
COPY . .
RUN dotnet publish -c Release -o /app --no-restore

FROM mcr.microsoft.com/dotnet/aspnet:10.0
WORKDIR /app
COPY --from=build /app .
EXPOSE 8080
ENTRYPOINT ["dotnet", "TeamKb.OtlpBridge.dll"]
