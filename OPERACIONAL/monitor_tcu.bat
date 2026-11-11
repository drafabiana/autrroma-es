@echo off
REM ===========================================================================
REM  MONITOR DIARIO DE ACORDAOS DO TCU - ALVES CARNEIRO ADVOCACIA
REM
REM  Chamado pelo Agendador de Tarefas do Windows:
REM    - "AlvesCarneiro - Acordaos TCU (coleta)": 9h, 11h, 13h e 15h, com
REM      --sem-enviar (so le e acumula - o TCU bloqueia rajadas de download);
REM    - "AlvesCarneiro - Acordaos TCU": 17:30, ultima rodada + envio do e-mail.
REM
REM  Le os acordaos novos do TCU, filtra pelos temas do escritorio e pelos
REM  clientes citados, resume com a IA e envia por e-mail. Salva copia em
REM  OPERACIONAL\relatorios_tcu\ e o log em relatorios_tcu\_log-execucao.txt.
REM
REM  Para rodar na mao, basta dar duplo clique neste arquivo.
REM ===========================================================================

setlocal
set RAIZ=%~dp0..
set PYTHON=C:\Users\Fabiana Carneiro\AppData\Local\Python\pythoncore-3.14-64\python.exe
set LOGDIR=%~dp0relatorios_tcu
set LOG=%LOGDIR%\_log-execucao.txt

if not exist "%LOGDIR%" mkdir "%LOGDIR%"

cd /d "%RAIZ%"

echo. >> "%LOG%"
echo ======================================================== >> "%LOG%"
echo Execucao: %DATE% %TIME% >> "%LOG%"
echo ======================================================== >> "%LOG%"

"%PYTHON%" -u -X utf8 "OPERACIONAL\monitor_tcu.py" %* >> "%LOG%" 2>&1
set CODIGO=%ERRORLEVEL%

echo [saida: %CODIGO%] >> "%LOG%"
endlocal & exit /b %CODIGO%
