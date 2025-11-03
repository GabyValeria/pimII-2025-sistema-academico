@echo off
set COMPILADOR=gcc
set ARQUIVOS=main.c dados.c
set EXECUTAVEL=sistema_academico.exe
set OPCOES_GCC=-Wall -std=c99

echo.
echo --- INICIANDO COMPILACAO ---
echo Compilador: %COMPILADOR%
echo Arquivos: %ARQUIVOS%
echo Saida: %EXECUTAVEL%
echo Opcoes: %OPCOES_GCC%
echo.

%COMPILADOR% %ARQUIVOS% %OPCOES_GCC% -o %EXECUTAVEL%

REM Verifica o código de erro retornado pelo GCC
if ERRORLEVEL 1 (
    echo.
    echo ❌ ERRO DE COMPILACAO! Verifique as mensagens acima.
) else (
    echo.
    echo ✅ COMPILACAO CONCLUIDA! Executavel criado: %EXECUTAVEL%
    echo.
    REM Oferece a opcao de executar o programa
    :RUN_PROMPT
    set /p RUN_CHOICE="Deseja executar o sistema agora? (S/N): "
    if /i "%RUN_CHOICE%"=="S" (
        echo.
        echo --- EXECUTANDO O SISTEMA ---
        %EXECUTAVEL%
    ) else if /i "%RUN_CHOICE%"=="N" (
        echo Nao executando.
    ) else (
        echo Opcao invalida. Digite S ou N.
        goto RUN_PROMPT
    )
)

echo.
echo Pressione qualquer tecla para sair...
pause > nul
