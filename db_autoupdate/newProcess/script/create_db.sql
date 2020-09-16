USE [master]
GO

-- Verify that the stored procedure does not already exist.  
IF OBJECT_ID ( 'usp_GetErrorInfo', 'P' ) IS NOT NULL   
    DROP PROCEDURE usp_GetErrorInfo;  
GO  
  
-- Create procedure to retrieve error information.  
CREATE PROCEDURE usp_GetErrorInfo  
AS  
--系統拋回訊息用
	DECLARE @ErrorMessage As VARCHAR(1000) = CHAR(10)+'Error Code:' +CAST(ERROR_NUMBER() AS VARCHAR)
											+CHAR(10)+'Error Message:'+	ERROR_MESSAGE()
											+CHAR(10)+'Error Line:'+	CAST(ERROR_LINE() AS VARCHAR)
	DECLARE @ErrorSeverity As Numeric = ERROR_SEVERITY()
	DECLARE @ErrorState As Numeric = ERROR_STATE()
	RAISERROR( @ErrorMessage, @ErrorSeverity, @ErrorState);--回傳錯誤資訊
GO  

BEGIN TRY

/****** Object:  Database [DigiChamber]    Script Date: 2019/10/17 上午 01:18:17 ******/
CREATE DATABASE [DigiChamber]
 CONTAINMENT = NONE
 ON  PRIMARY 
( NAME = N'DigiChamber', FILENAME = N'$(UserAppLocal)\Microsoft\Microsoft SQL Server Local DB\Instances\BareissLocalDB\DigiChamber.mdf' , SIZE = 8192KB , MAXSIZE = UNLIMITED, FILEGROWTH = 65536KB )
 LOG ON 
( NAME = N'DigiChamber_log', FILENAME = N'$(UserAppLocal)\Microsoft\Microsoft SQL Server Local DB\Instances\BareissLocalDB\DigiChamber_log.ldf' , SIZE = 8192KB , MAXSIZE = 2048GB , FILEGROWTH = 65536KB )

END TRY

BEGIN CATCH
EXECUTE usp_GetErrorInfo;  
END CATCH
GO