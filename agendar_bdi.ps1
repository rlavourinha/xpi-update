# Registra no Agendador de Tarefas do Windows (usuário atual, sem elevação) a coleta diária do Boletim Diário da B3.
# Rodar UMA vez, nesta pasta:  powershell -ExecutionPolicy Bypass -File .\agendar_bdi.ps1
# Remover:                     powershell -ExecutionPolicy Bypass -File .\agendar_bdi.ps1 -Remover
# A API do BDI só serve ~21 pregões; a tarefa roda todo dia às 09:30 (pega D-1 e qualquer dia perdido na janela) e
# de novo às 21:30 (caso a máquina estivesse desligada de manhã). O script é idempotente.
param([switch]$Remover)

$pasta = Split-Path -Parent $MyInvocation.MyCommand.Path
$bat = Join-Path $pasta "atualizar_bdi.bat"
$tarefas = @(
    @{ Nome = "XP-BDI-Diario-Manha"; Gatilho = { New-ScheduledTaskTrigger -Daily -At "09:30" }; Descr = "B3 BDI: negócios em ações e minis, aluguel por participante, PF (D-1)" },
    @{ Nome = "XP-BDI-Diario-Noite"; Gatilho = { New-ScheduledTaskTrigger -Daily -At "21:30" }; Descr = "B3 BDI: segunda tentativa do dia (se a manhã falhou ou a máquina estava desligada)" }
)
foreach ($t in $tarefas) {
    if (Get-ScheduledTask -TaskName $t.Nome -ErrorAction SilentlyContinue) { Unregister-ScheduledTask -TaskName $t.Nome -Confirm:$false }
    if ($Remover) { Write-Host "removida: $($t.Nome)"; continue }
    $acao = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$bat`"" -WorkingDirectory $pasta
    $gat = & $t.Gatilho
    $cfg = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 2) -MultipleInstances IgnoreNew
    Register-ScheduledTask -TaskName $t.Nome -Action $acao -Trigger $gat -Settings $cfg -Description $t.Descr | Out-Null
    Write-Host "registrada: $($t.Nome) - $($t.Descr)"
}
