FOR /F "usebackq" %%i IN (`hostname`) DO SET MYVAR=%%i
ECHO %MYVAR%
REM sqlcmd -S %MYVAR%\SQLEXPRESS -v FullScriptDir="%CD%\script" -i %~dp0\insert_default.sql -b
sqlcmd -S "(localdb)\BareissLocalDB" -v FullScriptDir="%CD%\script" -i %~dp0\insert_default.sql -b