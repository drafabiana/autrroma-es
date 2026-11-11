@echo off
REM ===========================================================================
REM  RELATORIO DIARIO DE PRAZOS - ALVES CARNEIRO ADVOCACIA
REM
REM  Chamado pelo Agendador de Tarefas do Windows, todo dia as 09:00
REM  (tarefa "AlvesCarneiro - Prazos Diarios").
REM
REM  Consulta o ADVBOX, monta a lista de prazos em aberto (vencidos primeiro)
REM  e envia por e-mail. Salva copia em OPERACIONAL\relatorios_prazos\ e o log
REM  da execucao em OPERACIONAL\relatorios_prazos\_log-execucao.txt.
REM
REM  Para rodar na mao, basta dar duplo clique neste arquivo.
REM ===========================================================================

setlocal
set RAIZ=%~dp0..
set PYTHON=C:\Users\Fabiana Carneiro\AppData\Local\Python\pythoncore-3.14-64\python.exe
set LOGDIR=%~dp0relatorios_prazos
set LOG=%LOGDIR%\_log-execucao.txt

if not exist "%LOGDIR%" mkdir "%LOGDIR%"

cd /d "%RAIZ%"

echo. >> "%LOG%"
echo ======================================================== >> "%LOG%"
echo Execucao: %DATE% %TIME% >> "%LOG%"
echo ======================================================== >> "%LOG%"

"%PYTHON%" -X utf8 "OPERACIONAL\prazos_diario.py" >> "%LOG%" 2>&1
set CODIGO=%ERRORLEVEL%

echo [saida: %CODIGO%] >> "%LOG%"
endlocal & exit /b %CODIGO%
