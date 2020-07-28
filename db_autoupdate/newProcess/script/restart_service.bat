REM net stop "SQL Server (SQLEXPRESS)"
REM net start "SQL Server (SQLEXPRESS)"
"%programfiles%\Microsoft SQL Server\120\Tools\Binn\SqlLocalDB.exe" stop BareissLocalDB
"%programfiles%\Microsoft SQL Server\120\Tools\Binn\SqlLocalDB.exe" start BareissLocalDB