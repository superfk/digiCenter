CREATE LOGIN BareissAdmin WITH PASSWORD = 'BaAdmin',
CHECK_POLICY = OFF,
DEFAULT_DATABASE = DigiChamber;
GO

EXEC sp_addsrvrolemember 'BareissAdmin', 'sysadmin';  
GO

EXEC xp_instance_regwrite N'HKEY_LOCAL_MACHINE',
N'Software\Microsoft\MSSQLServer\MSSQLServer', N'LoginMode', REG_DWORD, 2