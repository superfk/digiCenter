FOR /F "usebackq" %%i IN (`hostname`) DO SET MYVAR=%%i
ECHO %MYVAR%
REM sqlcmd -S %MYVAR%\SQLEXPRESS -i %~dp0\create_tables.sql
sqlcmd -S "(localdb)\BareissLocalDB" -i %~dp0\create_tables.sql