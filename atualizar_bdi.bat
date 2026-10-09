@echo off
rem Coleta diária do Boletim Diário da B3 (negócios, minis, aluguel por participante, PF) -> data\b3_bdi_diario.csv
rem Chamado pela tarefa agendada "XP-BDI-Diario" (ver agendar_bdi.ps1). Idempotente: só baixa pregões ainda não coletados.
cd /d "%~dp0"
if not exist logs mkdir logs
set PYTHONIOENCODING=utf-8
python dados_b3_bdi_diario.py >> "logs\bdi_%date:~6,4%-%date:~3,2%.log" 2>&1
python dados_anbima_debentures_diario.py >> "logs\debentures_%date:~6,4%-%date:~3,2%.log" 2>&1
