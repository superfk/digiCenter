call data\SqlLocalDB.msi
REM Create an instance of LocalDB
"C:\Program Files\Microsoft SQL Server\120\Tools\Binn\SqlLocalDB.exe" create BareissLocalDB
REM Start the instance of LocalDB
"C:\Program Files\Microsoft SQL Server\120\Tools\Binn\SqlLocalDB.exe" start BareissLocalDB
REM Gather information about the instance of LocalDB
"C:\Program Files\Microsoft SQL Server\120\Tools\Binn\SqlLocalDB.exe" info BareissLocalDB

@echo off

:: BatchGotAdmin
:-------------------------------------
REM  --> Check for permissions
    IF "%PROCESSOR_ARCHITECTURE%" EQU "amd64" (
>nul 2>&1 "%SYSTEMROOT%\SysWOW64\cacls.exe" "%SYSTEMROOT%\SysWOW64\config\system"
) ELSE (
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
)

REM --> If error flag set, we do not have admin.
if '%errorlevel%' NEQ '0' (
    echo Requesting administrative privileges...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    set params= %*
    echo UAC.ShellExecute "cmd.exe", "/c ""%~s0"" %params:"=""%", "", "runas", 1 >> "%temp%\getadmin.vbs"

    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    pushd "%CD%"
    CD /D "%~dp0"
:--------------------------------------    

call script\changelogin.bat
call script\create_db.bat
call script\create_tables.bat
CD /D insertDefault
call insertDefault.exe
REM call script\create_tables.bat
REM call script\create_temp_tables.bat
REM call script\merge_default.bat
REM call script\drop_temp.bat
REM call script\restart_service.bat
pause
