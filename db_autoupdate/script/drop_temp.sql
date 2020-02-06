USE [DigiChamber]
GO

IF OBJECT_ID('dbo.FunctionList_temp', 'U') IS NOT NULL 
  DROP TABLE dbo.FunctionList_temp; 

IF OBJECT_ID('dbo.UserList_temp', 'U') IS NOT NULL 
  DROP TABLE dbo.UserList_temp;

IF OBJECT_ID('dbo.UserRoleList_temp', 'U') IS NOT NULL 
  DROP TABLE dbo.UserRoleList_temp; 

IF OBJECT_ID('dbo.UserPermission_temp', 'U') IS NOT NULL 
  DROP TABLE dbo.UserPermission_temp; 

GO