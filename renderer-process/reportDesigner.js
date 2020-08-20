const { ipcRenderer } = require("electron");
const appRoot = require('electron-root-path').rootPath;
const path = require('path');


var designer, report;

Stimulsoft.Base.StiLicense.key = "6vJhGtLLLz2GNviWmUTrhSqnOItdDwjBylQzQcAOiHmu2ExFZfV4X456jKoOffeNxTQJ1EIeZEkqTZHJNsXGhctzPx" + 
"91G5llbM2R3ilLBE3nZDpSkukMTMN6PGIheMsO8tukhmzubmUpIRDFBrVhsL7WhvAxLhzvXi77tjWcPn6js1jNN0rG" + 
"zNU8xp1Jy9EiC83KaDOz6r850NZ5F9bSGd3tnAdZLcB1/7tyDq24B+MzpZV4e9yjsAgAMjoCmHOjoCgZmwHyoq14gK" + 
"GNYiZB/6QkBbd5ZrYYVn9B1yiGLKv82Rb5kGrrGRx0S72qO28p+ijke1mlF9aeWlrjUOStCrMjDAPK+0F4l/asflKW" + 
"23gFBdK3caRDHiNf9JOSilkLRfTA/tGRTZhx6nuDPkwh4sDytJV17GpC0p03bNNC6OlvsPBgqkuiHqUCBu0oaMnsfO" + 
"ZMlGHdSTlhI/PFdT3qXL6MpgjdgAVsp4hMwPGQSxpUlhgUj/iAbwdakAszu2eKJh/ybXJ5BoShLwBSVsevt8Ji49kf" + 
"onSZtCYvW/KpKyMyp4Ahxv4TMBwML7T4iv8S";

var options = new Stimulsoft.Designer.StiDesignerOptions();
options.appearance.fullScreenMode = true;


Stimulsoft.Base.Localization.StiLocalization.addLocalizationFile(path.join(appRoot, "Localization", 'en.xml'), false, 'en');
Stimulsoft.Base.Localization.StiLocalization.addLocalizationFile(path.join(appRoot, "Localization", 'de.xml'), false, 'de');
Stimulsoft.Base.Localization.StiLocalization.addLocalizationFile(path.join(appRoot, "Localization", 'zh-CHS.xml'), false, 'zh-CHS');
Stimulsoft.Base.Localization.StiLocalization.addLocalizationFile(path.join(appRoot, "Localization", 'zh-CHT.xml'), false, 'zh-CHT');
// Stimulsoft.System.NodeJs.localizationPath = "locales";

ipcRenderer.on('set-lang', (event, lang) => {
    let langName = 'en';
    switch (lang) {
        case 'en':
            langName = 'en'
            break;
        case 'de':
            langName = 'de'
            break;
        case 'zh_cn':
            langName = 'zh-CHS'
            break;
        case 'zh_tw':
            langName = 'zh-CHT'
            break;
        default:

    }
    Stimulsoft.Base.Localization.StiLocalization.cultureName = langName;
})

ipcRenderer.on('import-data-to-designer', (event, data) => {

    // Create the report viewer with specified options
    designer = new Stimulsoft.Designer.StiDesigner(options, "StiDesigner", false);

    // Create a new report instance
    report = new Stimulsoft.Report.StiReport();

    try {
        // Load report from url
        report.loadFile(path.join(appRoot, "Report.mrt"));
        // Assign report to the viewer, the report will be built automatically after rendering the viewer
        designer.report = report;

        // Create new DataSet object
        var dataSet = new Stimulsoft.System.Data.DataSet("Data");
        // Load JSON data file from specified URL to the DataSet object
        dataSet.readJson(data);
        // Remove all connections from the report template
        report.dictionary.databases.clear();
        // Register DataSet object
        report.regData("Data", "Data", dataSet);
    } catch{

    } finally {
        designer.renderHtml('designerContent');
    }

})