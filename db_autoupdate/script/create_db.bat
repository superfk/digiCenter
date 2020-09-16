FOR /F "usebackq" %%i IN (`hostname`) DO SET MYVAR=%%i
ECHO %MYVAR%
REM sqlcmd -S %MYVAR%\SQLEXPRESS -i %~dp0\create_db.sql
REM sqlcmd -S "(localdb)\BareissLocalDB" -i %~dp0\create_db.sql
sqlcmd -S "(localdb)\BareissLocalDB" -v UserAppLocal="%LocalAppData%" -i %~dp0\create_db.sql