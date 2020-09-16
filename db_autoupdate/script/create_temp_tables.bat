FOR /F "usebackq" %%i IN (`hostname`) DO SET MYVAR=%%i
ECHO %MYVAR%
REM sqlcmd -S %MYVAR%\SQLEXPRESS -v FullScriptDir="%CD%\script" -i %~dp0\create_temp_tables.sql
sqlcmd -S "(localdb)\BareissLocalDB" -v FullScriptDir="%CD%\script" -i %~dp0\create_temp_tables.sql