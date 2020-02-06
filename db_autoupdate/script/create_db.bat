FOR /F "usebackq" %%i IN (`hostname`) DO SET MYVAR=%%i
ECHO %MYVAR%
sqlcmd -S %MYVAR%\SQLEXPRESS -i %~dp0\create_db.sql