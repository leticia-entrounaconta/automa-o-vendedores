#Requires -RunAsAdministrator
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$taskName = "RPA - Vendedores e Produção"
$projectPath = $PSScriptRoot
$rpaScript = Join-Path $projectPath "run_rpa.ps1"
$powershellExe = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
$setupLog = Join-Path $projectPath "logs\scheduled_task_setup.log"

if (-not (Test-Path -LiteralPath $rpaScript -PathType Leaf)) {
    throw "Script do RPA não encontrado: $rpaScript"
}

try {
    # A senha é solicitada pela interface segura do Windows e só é usada para
    # o registro da tarefa. Ela não é gravada neste script nem no log.
    $defaultUser = "$env:USERDOMAIN\$env:USERNAME"
    $credential = Get-Credential `
        -UserName $defaultUser `
        -Message "Informe a senha da conta que já executa o Docker Desktop e o RPA."

    if ($null -eq $credential) {
        throw "A criação da tarefa foi cancelada."
    }

    $password = [System.Net.NetworkCredential]::new("", $credential.Password).Password

    $arguments = '-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + $rpaScript + '"'

    $action = New-ScheduledTaskAction `
        -Execute $powershellExe `
        -Argument $arguments `
        -WorkingDirectory $projectPath

    $trigger = New-ScheduledTaskTrigger `
        -Weekly `
        -DaysOfWeek Monday `
        -At 3:00PM

    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -WakeToRun `
        -MultipleInstances IgnoreNew

    Register-ScheduledTask `
        -TaskName $taskName `
        -Description "Executa semanalmente o RPA Docker de vendedores, produção e SharePoint." `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -User $credential.UserName `
        -Password $password `
        -RunLevel Highest `
        -Force | Out-Null

    # Habilita o log operacional para que a aba Histórico e o Visualizador de
    # Eventos registrem início, término e código de retorno da tarefa.
    wevtutil sl Microsoft-Windows-TaskScheduler/Operational /e:true

    Write-Host "Tarefa '$taskName' criada." -ForegroundColor Green
    Write-Host "Próxima execução: segunda-feira, às 15:00."
    Write-Host "A conta configurada é: $($credential.UserName)"
}
catch {
    $message = "{0:u} | Falha ao criar a tarefa: {1}" -f (Get-Date), $_.Exception.Message
    New-Item -ItemType Directory -Path (Split-Path -Parent $setupLog) -Force | Out-Null
    Add-Content -LiteralPath $setupLog -Value $message
    Write-Host $message -ForegroundColor Red
    throw
}
finally {
    $password = $null
    $credential = $null
}
