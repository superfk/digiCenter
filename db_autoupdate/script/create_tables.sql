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

CREATE TABLE [dbo].[FunctionList](
	[ID] [int] IDENTITY(1,1) NOT NULL,
	[Functions] [varchar](255) NULL,
	[Tree_index] [tinyint] NULL,
	[Display_order] [smallint] NULL
PRIMARY KEY CLUSTERED 
(
	[ID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]

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

BEGIN TRY

CREATE TABLE [dbo].[System_log](
	[ID] [int] IDENTITY(1,1) NOT NULL,
	[Timestamp] [datetime2](7) NULL,
	[User_Name] [varchar](255) NULL,
	[User_Role] [varchar](255) NULL,
	[Log_Type] [varchar](255) NULL,
	[Log_Message] [varchar](2048) NULL,
	[Audit] [bit] NULL,
PRIMARY KEY CLUSTERED 
(
	[ID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]

END TRY

BEGIN CATCH
EXECUTE usp_GetErrorInfo;  
END CATCH;

/****** Object:  Table [dbo].[Test_Data]    Script Date: 10/16/2019 11:59:14 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

BEGIN TRY

CREATE TABLE [dbo].[Test_Data](
	[ID] [int] IDENTITY(1,1) NOT NULL,
	[Recordtime] [datetime2](7) NOT NULL,
	[Project_name] [nvarchar](255) NOT NULL,
	[Batch_name] [nvarchar](255) NOT NULL,
	[Seq_name] [nvarchar](1024) NOT NULL,
	[Operator] [varchar](255) NOT NULL,
	[Seq_step_id] [smallint] NOT NULL,
	[Sample_counter] [smallint] NOT NULL,
	[Hardness_result] [float] NOT NULL,
	[Temperature] [float] NOT NULL,
	[Humidity] [float] NULL,
	[Raw_data] [varchar](255) NOT NULL,
	[Math_method] [varchar](10) NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[ID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY],
 CONSTRAINT [Recordtime] UNIQUE NONCLUSTERED 
(
	[Recordtime] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]


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

CREATE TABLE [dbo].[UserList](
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

END TRY

BEGIN CATCH
EXECUTE usp_GetErrorInfo;  
END CATCH;

/****** Object:  Table [dbo].[UserPermission]    Script Date: 10/16/2019 11:59:44 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

BEGIN TRY

CREATE TABLE [dbo].[UserPermission](
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

CREATE TABLE [dbo].[UserRoleList](
	[ID] [int] IDENTITY(1,1) NOT NULL,
	[User_Role] [varchar](255) NULL,
	[User_Level] [tinyint] NULL,
PRIMARY KEY CLUSTERED 
(
	[ID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]


END TRY

BEGIN CATCH
EXECUTE usp_GetErrorInfo;  
END CATCH;

/****** Object:  Table [dbo].[Batch_data]    Script Date: 10/16/2019 11:59:14 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

BEGIN TRY

CREATE TABLE [dbo].[Batch_data](
	[ID] [int] IDENTITY(1,1) NOT NULL,
	[Project_Name] [nvarchar](255) NOT NULL,
	[Batch_Name] [nvarchar](255) NOT NULL,
	[Creation_Date] [datetime2](7) NOT NULL,
	[Note] [nvarchar](1024) NULL,
	[Last_seq_name] [nvarchar](255) NOT NULL,
	[NumSample] [smallint] NOT NULL
) ON [PRIMARY]

END TRY


BEGIN CATCH
EXECUTE usp_GetErrorInfo;  
END CATCH;

GO
