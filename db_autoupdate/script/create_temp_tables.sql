USE [DigiChamber]
GO

-- Verify that the stored procedure does not already exist.  
IF OBJECT_ID ( 'usp_GetErrorInfo', 'P' ) IS NOT NULL   
    DROP PROCEDURE usp_GetErrorInfo;  
GO  
  
-- Create procedure to retrieve error information.  
CREATE PROCEDURE usp_GetErrorInfo
AS  

--�t�Ωߦ^�T����
	DECLARE @ErrorMessage As VARCHAR(1000) = CHAR(10)+'Error Code:' +CAST(ERROR_NUMBER() AS VARCHAR)
											+CHAR(10)+'Error Message:'+	ERROR_MESSAGE()
											+CHAR(10)+'Error Line:'+	CAST(ERROR_LINE() AS VARCHAR)
	DECLARE @ErrorSeverity As Numeric = ERROR_SEVERITY()
	DECLARE @ErrorState As Numeric = ERROR_STATE()
	RAISERROR( @ErrorMessage, @ErrorSeverity, @ErrorState);--�^�ǿ��~��T
GO  

/****** Object:  Table [dbo].[FunctionList]    Script Date: 10/16/2019 11:51:52 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

BEGIN TRY

IF OBJECT_ID('dbo.FunctionList_temp', 'U') IS NOT NULL 
  DROP TABLE dbo.FunctionList_temp; 

CREATE TABLE [dbo].[FunctionList_temp](
	[ID] [int] IDENTITY(1,1) NOT NULL,
	[Functions] [varchar](255) NULL,
	[Tree_index] [tinyint] NULL,
	[Display_order] [smallint] NULL,
	[en] [varchar](255) NULL,
	[zh_tw] [nvarchar](255) NULL,
	[de] [nvarchar](255) NULL
PRIMARY KEY CLUSTERED 
(
	[ID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]

BULK INSERT [DigiChamber].[dbo].[FunctionList_temp]
    FROM '$(FullScriptDir)\functionlist_default.csv'
    WITH
    (
        FIRSTROW = 2,
        FIELDTERMINATOR = ',',
        ROWTERMINATOR = '\n',
        CODEPAGE = '65001',
        DATAFILETYPE = 'char'
    )

END TRY


BEGIN CATCH
EXECUTE usp_GetErrorInfo;  
END CATCH;
GO

/****** Object:  Table [dbo].[System_log]    Script Date: 10/16/2019 11:58:23 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

/****** Object:  Table [dbo].[UserPermission]    Script Date: 10/16/2019 11:59:44 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

BEGIN TRY

IF OBJECT_ID('dbo.UserPermission_temp', 'U') IS NOT NULL 
  DROP TABLE dbo.UserPermission_temp; 

CREATE TABLE [dbo].[UserPermission_temp](
	[ID] [int] IDENTITY(1,1) NOT NULL,
	[User_Role] [varchar](255) NULL,
	[Functions] [varchar](255) NULL,
	[Enabled] [bit] NULL,
	[Visibled] [bit] NULL,
PRIMARY KEY CLUSTERED 
(
	[ID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]

BULK INSERT [DigiChamber].[dbo].UserPermission_temp
    FROM '$(FullScriptDir)\user_permission_default.csv'
    WITH
    (
        FIRSTROW = 2,
        FIELDTERMINATOR = ',',
        ROWTERMINATOR = '\n'
    )

END TRY

BEGIN CATCH
EXECUTE usp_GetErrorInfo;  
END CATCH;

/****** Object:  Table [dbo].[UserList]    Script Date: 10/16/2019 11:59:30 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

BEGIN TRY

IF OBJECT_ID('dbo.UserList_temp', 'U') IS NOT NULL 
  DROP TABLE dbo.UserList_temp; 

CREATE TABLE [dbo].[UserList_temp](
	[ID] [int] IDENTITY(1,1) NOT NULL,
	[User_Name] [varchar](255) NULL,
	[PW] [varchar](255) NULL,
	[User_Role] [varchar](255) NULL,
	[Creation_Date] [datetime2](7) NULL,
	[Expired_Date] [datetime2](7) NULL,
	[Status] [tinyint] NULL,
	[First_login] [bit] NULL,
PRIMARY KEY CLUSTERED 
(
	[ID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]

BULK INSERT [DigiChamber].[dbo].[UserList_temp]
    FROM '$(FullScriptDir)\user_list_default.csv'
    WITH
    (
        FIRSTROW = 2,
        FIELDTERMINATOR = ',',
        ROWTERMINATOR = '\n'
    )

END TRY

BEGIN CATCH
EXECUTE usp_GetErrorInfo;  
END CATCH;

/****** Object:  Table [dbo].[UserRoleList]    Script Date: 10/16/2019 11:59:55 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

BEGIN TRY

IF OBJECT_ID('dbo.UserRoleList_temp', 'U') IS NOT NULL 
  DROP TABLE dbo.UserRoleList_temp; 

CREATE TABLE [dbo].[UserRoleList_temp](
	[ID] [int] IDENTITY(1,1) NOT NULL,
	[User_Role] [varchar](255) NULL,
	[User_Level] [tinyint] NULL,
PRIMARY KEY CLUSTERED 
(
	[ID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]

BULK INSERT [DigiChamber].[dbo].[UserRoleList_temp]
    FROM '$(FullScriptDir)\user_role_list_default.csv'
    WITH
    (
        FIRSTROW = 2,
        FIELDTERMINATOR = ',',
        ROWTERMINATOR = '\n'
    )

END TRY

BEGIN CATCH
EXECUTE usp_GetErrorInfo;  
END CATCH;

GO