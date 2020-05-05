USE [DigiChamber]
GO

MERGE dbo.UserPermission AS Target
USING (SELECT [User_Role], [Functions], [Enabled], [Visibled] FROM dbo.UserPermission_temp) AS Source
ON (Target.[User_Role] = Source.[User_Role] AND Target.[Functions] = Source.[Functions])
WHEN MATCHED THEN
    UPDATE SET Target.[Enabled] = Source.[Enabled], Target.[Visibled] = Source.[Visibled]
WHEN NOT MATCHED BY TARGET THEN
    INSERT ([User_Role], [Functions], [Enabled],[Visibled])
    VALUES (Source.[User_Role], Source.[Functions], Source.[Enabled], Source.[Visibled])
OUTPUT $action;

MERGE dbo.[FunctionList] AS Target
USING (SELECT [Functions], [Tree_index], [Display_order], [en],[zh_tw],[de] FROM dbo.[FunctionList_temp]) AS Source
ON (Target.[Functions] = Source.[Functions])
WHEN MATCHED THEN
    UPDATE SET Target.[Tree_index] = Source.[Tree_index], Target.[Display_order] = Source.[Display_order], 
    Target.[en] = Source.[en], Target.[zh_tw] = Source.[zh_tw], Target.[de] = Source.[de]
WHEN NOT MATCHED BY TARGET THEN
    INSERT ([Functions], [Tree_index], [Display_order], [en], [zh_tw], [de])
    VALUES (Source.[Functions], Source.[Tree_index], Source.[Display_order], Source.[en], Source.[zh_tw], Source.[de])
OUTPUT $action;

MERGE dbo.[UserList] AS Target
USING (SELECT [User_Name], [PW], [User_Role], [Creation_Date],[Expired_Date],[Status],[First_login] FROM dbo.[UserList_temp]) AS Source
ON (Target.[User_Name] = Source.[User_Name])
WHEN MATCHED THEN
    UPDATE SET Target.[PW] = Source.[PW], Target.[User_Role] = Source.[User_Role],Target.[Creation_Date] = Source.[Creation_Date],
	Target.[Expired_Date] = Source.[Expired_Date], Target.[Status] = Source.[Status], Target.[First_login] = Source.[First_login]
WHEN NOT MATCHED BY TARGET THEN
    INSERT ([User_Name], [PW], [User_Role], [Creation_Date],[Expired_Date],[Status],[First_login])
    VALUES (Source.[User_Name], Source.[PW], Source.[User_Role], Source.[Creation_Date], Source.[Expired_Date], Source.[Status], Source.[First_login])
OUTPUT $action;


MERGE dbo.[UserRoleList] AS Target
USING (SELECT [User_Role], [User_Level] FROM dbo.[UserRoleList_temp]) AS Source
ON (Target.[User_Role] = Source.[User_Role])
WHEN MATCHED THEN
    UPDATE SET Target.[User_Level] = Source.[User_Level]
WHEN NOT MATCHED BY TARGET THEN
    INSERT ([User_Role], [User_Level])
    VALUES (Source.[User_Role], Source.[User_Level])
--OUTPUT $action, Inserted.*, Deleted.*;
OUTPUT $action;

GO