Set-Location $PSScriptRoot

docker compose run --rm rpa

$exitCode = $LASTEXITCODE

if ($exitCode -ne 0) {
    Write-Error "RPA finalizado com erro. Exit code: $exitCode"
    exit $exitCode
}

exit 0
