@echo off
REM ===========================================================================
REM  ESPELHAMENTO ADVBOX -> INFINITUM - ALVES CARNEIRO ADVOCACIA
REM
REM  Chamado pelo Agendador de Tarefas do Windows, todo dia as 07:30, ate
REM  30/11/2026 (tarefa "AlvesCarneiro - Espelhamento Infinitum").
REM
REM  So LE o ADVBOX e acumula as mudancas em SYNC\espelhamento\pendencias.json.
REM  A gravacao no Infinitum e feita pelo Claude, a pedido ("aplica o
REM  espelhamento"). Log em SYNC\espelhamento\_log-execucao.txt.
REM ===========================================================================

setlocal
set RAIZ=%~dp0..
set PYTHON=C:\Users\Fabiana Carneiro\AppData\Local\Python\pythoncore-3.14-64\python.exe
set LOGDIR=%~dp0espelhamento
set LOG=%LOGDIR%\_log-execucao.txt

if not exist "%LOGDIR%" mkdir "%LOGDIR%"

cd /d "%RAIZ%"

echo. >> "%LOG%"
echo ======================================================== >> "%LOG%"
echo Execucao: %DATE% %TIME% >> "%LOG%"
echo ======================================================== >> "%LOG%"

"%PYTHON%" -X utf8 "SYNC\advbox_infinitum.py" >> "%LOG%" 2>&1
set CODIGO=%ERRORLEVEL%

echo [saida: %CODIGO%] >> "%LOG%"
endlocal & exit /b %CODIGO%
