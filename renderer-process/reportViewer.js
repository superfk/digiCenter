
Stimulsoft.Base.StiLicense.key = 
"6vJhGtLLLz2GNviWmUTrhSqnOItdDwjBylQzQcAOiHncDzQDe6bFww6Bip9/CL33fxnJPP3QrZTug8MsoatxwE/til" + 
"JCvOzAnn3tlnwD3NkpkdTB0eQ4cqj8Y3/86PwkdFOyHWQxiCdcnMTkAiAdIm0byV81l0zvJ6mXmozg+LvK7u3cb/hP" + 
"1nJoUkyT0ycq1fs3N7zB6KedopoBV4bu6UqbxbXgdV80vdKvwueQReBIN9vNu0q5v3ZInPNJEG9iGGEXUduUpU0dFX" + 
"zq29KdJDc53GV0sXvOhzcJP9uyIY2Yk2Rb0H74aJqivQsVUPBkicLDFr1DWmV7hHFMhqztC39YlOFboj+o/SRe4vhx" + 
"Ey/zWZnzJTkHb4U/JWCs1KvD3PgKPmqCXlwPMOifMPE0/XpvXwCrRDx4C9DgGgb0YdMUCeW/o7v2XrJjRmvqc+itsz" + 
"5XZIMU9KICb9Hm9CLmdBbX79eHSnBsDmxM2wjn6bIqQpSUoSpjOR31lW5b1K4eRqEzl9UmxWzp+w7SNNdbiIf51ok+" + 
"+WoJ6KhcwRrvF4hROVsnKWZAP1s3m1u6Zhot";


var options = new Stimulsoft.Viewer.StiViewerOptions();
options.appearance.scrollbarsMode = true;
options.appearance.fullScreenMode = true;

// Create the report viewer with specified options
var viewer = new Stimulsoft.Viewer.StiViewer(options, "StiViewer", false);

// Create a new report instance
var report = new Stimulsoft.Report.StiReport();
// Load report from url
report.loadFile("../Report.mrt");
// Assign report to the viewer, the report will be built automatically after rendering the viewer
viewer.report = report;

viewer.renderHtml('viewerContent');