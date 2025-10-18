@echo off
ECHO Compilando o backend em C...

REM Navega para a pasta do backend
cd backend_c

REM Comando de compilação usando GCC
REM Junta os arquivos .c e cria o executável 'sistema_academico.exe'
gcc main.c funcoes.c -o sistema_academico.exe -Wall -Wextra

REM Verifica se a compilação foi bem-sucedida
if %errorlevel% == 0 (
    ECHO.
    ECHO Compilacao concluida com sucesso!
    ECHO O executavel "sistema_academico.exe" foi criado dentro da pasta 'backend_c'.
) else (
    ECHO.
    ECHO ERRO: A compilacao falhou.
    ECHO Verifique se o GCC (MinGW) esta instalado e configurado no PATH do sistema.
)

ECHO.
pause