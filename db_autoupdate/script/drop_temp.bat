FOR /F "usebackq" %%i IN (`hostname`) DO SET MYVAR=%%i
ECHO %MYVAR%
sqlcmd -S %MYVAR%\SQLEXPRESS -v FullScriptDir="%CD%\script" -i %~dp0\drop_temp.sql -b