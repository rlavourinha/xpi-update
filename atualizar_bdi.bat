@echo off
rem Coleta diária do Boletim Diário da B3 (negócios, minis, aluguel por participante, PF) -> data\b3_bdi_diario.csv
rem Chamado pela tarefa agendada "XP-BDI-Diario" (ver agendar_bdi.ps1). Idempotente: só baixa pregões ainda não coletados.
cd /d "%~dp0"
if not exist logs mkdir logs
set PYTHONIOENCODING=utf-8
rem log com nome fixo: %date% neste Windows vem em formato americano (10/13/2026) e quebrava o nome do arquivo
set "PY=C:\Users\rlavourinha\AppData\Local\Python\pythoncore-3.14-64\python.exe"
"%PY%" dados_b3_bdi_diario.py >> "logs\dados_b3_bdi_diario.log" 2>&1
"%PY%" dados_anbima_debentures_diario.py >> "logs\dados_anbima_debentures_diario.log" 2>&1
"%PY%" dados_spread_incentivadas.py >> "logs\dados_spread_incentivadas.log" 2>&1
"%PY%" slides\spread_incentivadas.py >> "logs\slide_spread_incentivadas.log" 2>&1
