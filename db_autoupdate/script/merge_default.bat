FOR /F "usebackq" %%i IN (`hostname`) DO SET MYVAR=%%i
ECHO %MYVAR%
sqlcmd -S %MYVAR%\SQLEXPRESS -v FullScriptDir="%CD%\script" -i %~dp0\merge_default.sql -b