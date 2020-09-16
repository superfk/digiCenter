FOR /F "usebackq" %%i IN (`hostname`) DO SET MYVAR=%%i
ECHO %MYVAR%
REM sqlcmd -S %MYVAR%\SQLEXPRESS -v FullScriptDir="%CD%\script" -i %~dp0\drop_temp.sql -b
sqlcmd -S "(localdb)\BareissLocalDB" -v FullScriptDir="%CD%\script" -i %~dp0\drop_temp.sql -b