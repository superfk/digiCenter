USE [DigiChamber]
GO



BULK INSERT [DigiChamber].[dbo].[UserPermission]
    FROM '$(FullScriptDir)\user_permission_default.csv'
    WITH
    (
        FIRSTROW = 2,
        FIELDTERMINATOR = ';',
        ROWTERMINATOR = '\n'
    )
GO

BULK INSERT [DigiChamber].[dbo].[UserRoleList]
    FROM '$(FullScriptDir)\user_role_list_default.csv'
    WITH
    (
        FIRSTROW = 2,
        FIELDTERMINATOR = ';',
        ROWTERMINATOR = '\n'
    )
GO

BULK INSERT [DigiChamber].[dbo].[UserList]
    FROM '$(FullScriptDir)\user_list_default.csv'
    WITH
    (
        FIRSTROW = 2,
        FIELDTERMINATOR = ';',
        ROWTERMINATOR = '\n'
    )
GO

BULK INSERT [DigiChamber].[dbo].[FunctionList]
    FROM '$(FullScriptDir)\functionlist_default.csv'
    WITH
    (
        FIRSTROW = 2,
        FIELDTERMINATOR = ';',
        ROWTERMINATOR = '\n',
        CODEPAGE = '65001',
        DATAFILETYPE = 'char'
    )
GO