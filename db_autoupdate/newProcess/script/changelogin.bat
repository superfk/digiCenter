FOR /F "usebackq" %%i IN (`hostname`) DO SET MYVAR=%%i
ECHO %MYVAR%
REM sqlcmd -S %MYVAR%\SQLEXPRESS -i %~dp0\changelogin.sql
sqlcmd -S "(localdb)\BareissLocalDB" -i %~dp0\changelogin.sql