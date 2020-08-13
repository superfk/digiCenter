const electron = require('electron')
const app = electron.app
const BrowserWindow = electron.BrowserWindow
const path = require('path')
const {ipcMain, dialog, shell} = require('electron')
const appRoot = require('electron-root-path').rootPath;
const ProgressBar = require('electron-progressbar');
const isDev = require('electron-is-dev');
const PDFWindow = require('electron-pdf-window')
let tools = require('./assets/shared_tools');
let ws;
const taskkill = require('taskkill');
const find = require('find-process');

const gotTheLock = app.requestSingleInstanceLock()
let isSecondIndtance = false;

console.log('appRoot:',appRoot)
const curPath = path.join(appRoot, 'config.json')
console.log('config Path:',curPath)

function connect() {
  try{
    const WebSocket = require('ws');
    ws = new WebSocket('ws://127.0.0.1:5678');
  }catch(e){
    console.log('Socket init error. Reconnect will be attempted in 1 second.', e.reason);
  }

  ws.on('open', ()=> {
    console.log('websocket in main connected')
    init_server();
  });

  ws.on('ping',()=>{
    
    ws.send(tools.parseCmd('pong','from main'));
  })

  ws.on('message',(message)=>{
    try{
      msg = tools.parseServerMessage(message);
      let cmd = msg.cmd;
      let data = msg.data;
      console.log('[cmd] ',cmd)
      switch(cmd) {
        case 'ping':
          ws.send(tools.parseCmd('pong',data));
          break;
        case 'reply_log_to_db':
          console.log(data);
          break;
        case 'result_of_backendinit':
          if(data.result == 1){
            console.log(data.resp)
            PY_INIT_OK=true;
            createWindow()
          }else{
            console.log(data.resp)
          }
          break;
        case 'reply_server_error':
          showInternalErrorModal(data.error)
          console.log(data.error);
          break;
        case 'reply_close_all':
          app.quit()
          break;
        default:
          console.log('Not found this cmd ' + cmd)
          break;
      }
    }catch(e){
      console.error(e)
    }
  });

  ws.onclose = function(e) {
    console.log('Socket is closed. Reconnect will be attempted in 1 second.', e.reason);
    setTimeout(function() {
      connect();
    }, 1000);
  };

  ws.onerror = function(err) {
    console.error('Socket encountered error: ', err.message, 'Closing socket');
    ws.close();
  };
}



/*************************************************************
 * py process
 *************************************************************/

const PY_DIST_FOLDER = 'pyserver_dist'
const PY_FOLDER = 'server'
const PY_MODULE = 'api' // without .py suffix
let PY_INIT_OK = false;

let pyProc = null
let pyPort = null

//
const guessPackaged = () => {
  const fullPath = path.join(appRoot, PY_DIST_FOLDER)
  console.log('full server Path:')
  console.log(fullPath);
  console.log('does server existed:')
  console.log(require('fs').existsSync(fullPath))
  return require('fs').existsSync(fullPath)
}

const getScriptPath = () => {
  if (!guessPackaged()) {
    return path.join(appRoot, PY_FOLDER, PY_MODULE + '.py')
  }
  if (process.platform === 'win32') {
    return path.join(appRoot, PY_DIST_FOLDER, PY_MODULE, PY_MODULE + '.exe')
  }
  return path.join(appRoot, PY_DIST_FOLDER, PY_MODULE, PY_MODULE)
}

const selectPort = () => {
  pyPort = 4242
  return pyPort
}

const createPyProc = () => {
  let script = getScriptPath()
  let port = '' + selectPort()

  if (guessPackaged()) {
    pyProc = require('child_process').execFile(script, [port])
    console.log('Found server exe:')
    console.log(script);
  } else {
    pyProc = require('child_process').spawn('python', [script, port],{ stdio: 'ignore' })
  }
 
  if (pyProc != null) {
    //console.log(pyProc)
    console.log('child process success on port ' + port);
  }
  connect();
}

const exitPyProc = (e) => {
  e.preventDefault()
  if(!isSecondIndtance){
    find('name', 'api.exe', true)
    .then(function (list) {
      console.log('there are %s api.exe process(es)', list.length);
      const apiPids = list.map(elm=>elm.pid)
      console.log('api.exe pid:', apiPids);
      try{
        (async () => {
          await taskkill(apiPids,{force: true, tree: true});
          await ws.close()
          ws = null;
          app.exit(0)
        })();
        
      }catch (err) {
    
      }
    });
  }else{
    app.exit(0)
  }
  
}

// init config and database
var init_server = function(){
  ws.send(tools.parseCmd('load_sys_config',curPath));
  ws.send(tools.parseCmd('backend_init'));
  ws.send(tools.parseCmd('load_default_lang',appRoot));
}


app.on('ready', createPyProc)
app.on('before-quit',exitPyProc)
// app.on('will-quit', exitPyProc)


/*************************************************************
 * window management
 *************************************************************/

let mainWindow = null;
let progressBar = null;

if (!gotTheLock) {
  isSecondIndtance = true
  app.quit()
} else {
  app.on('second-instance', (event, commandLine, workingDirectory) => {
    // Someone tried to run a second instance, we should focus our window.
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore()
      mainWindow.focus()
    }
  })
}

const createWindow = () => {
  mainWindow = new BrowserWindow({
    width: 1024, 
    height: 600,
    icon: __dirname + '/img/icon.ico',
    backgroundColor: '#2e2c29',
    webPreferences: {
      nodeIntegration: true
    }
  })
  mainWindow.loadURL(require('url').format({
    pathname: path.join(__dirname, 'index.html'),
    protocol: 'file:',
    slashes: true
  }))

  mainWindow.maximize();

  if (isDev){
    mainWindow.webContents.openDevTools();
  }else {
    mainWindow.removeMenu();
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  })

  mainWindow.on('closed', () => {
    mainWindow = null
  })

  if (!PY_INIT_OK){
    console.log('created window')
    const options = {
      type: 'error',
      title: 'Database connection error',
      message: 'Database connection error'
    }
    dialog.showMessageBox(mainWindow,options, (index) => {
      app.quit();
    })
  }

}



function createProgressBar(title='Progress bar', text='', detail=''){
  progressBar = new ProgressBar({
    title: title,
    text: text,
    detail: detail
  }, app);

}

const createReportViewerWindow = (data, langID='en') => {
  let reportViewerWindow = new BrowserWindow({
    width: 800, 
    height: 600,
    icon: path.join(appRoot,'img/icon.ico'),
    parent: mainWindow,
    webPreferences: {
      nodeIntegration: true
    }
  })
  reportViewerWindow.loadURL(require('url').format({
    pathname: path.join(__dirname, 'sections','reportViewer.html'),
    protocol: 'file',
    slashes: true
  }))
  
  if (isDev) {reportViewerWindow.removeMenu();}

  reportViewerWindow.on('closed', () => {
    reportViewerWindow = null
  })

  reportViewerWindow.webContents.once('did-finish-load', () => {
    console.log('report localization:', langID)
    reportViewerWindow.webContents.send('set-lang', langID)
    reportViewerWindow.webContents.send('import-data-to-viewer', data)
  });

}

const createReportDesignerWindow = (data, langID='en') => {
  let reportDesignerWindow = new BrowserWindow({
    width: 800, 
    height: 600,
    icon: path.join(appRoot,'img/icon.ico'),
    parent: mainWindow,
    modal: false,
    webPreferences: {
      nodeIntegration: true
    }
  })
  reportDesignerWindow.loadURL(require('url').format({
    pathname: path.join(__dirname, 'sections','reportDesigner.html'),
    protocol: 'file:',
    slashes: true
  }))
  
  if (isDev) {reportDesignerWindow.removeMenu();}

  reportDesignerWindow.on('closed', () => {
    reportDesignerWindow = null
  })

  reportDesignerWindow.webContents.once('did-finish-load', () => {
    reportDesignerWindow.webContents.send('set-lang', langID)
    reportDesignerWindow.webContents.send('import-data-to-designer', data)
    
  });

 
}

ipcMain.on('call-report-viewer-window', (event, data, langID='en') =>{
  createReportViewerWindow(data, langID);
})

ipcMain.on('call-report-designer-window', (event, data, langID='en') =>{
  createReportDesignerWindow(data, langID);
})

ipcMain.on('start-indet-progressbar', (event, title, text, msg) =>{
  createProgressBar(title, text, msg);
})

ipcMain.on('completed-indet-progressbar', (event, msg='Task completed. Exiting...') =>{
  progressBar.detail = msg;
  progressBar.setCompleted();
})

ipcMain.on('abort-indet-progressbar', (event) =>{
  console.log('abort progressbar');
  progressBar.close();
})

ipcMain.on('open-file-dialog', (event, default_Path, calback) => {
  console.log(default_Path)
  dialog.showOpenDialog({
    filters: [
      { name: 'Sequence', extensions: ['seq'] }
    ],
    properties: ['openFile'],
    defaultPath: default_Path,
  }).then(result => {
    if (!result.canceled) {
      event.reply(calback, result.filePaths[0])
    }
  }).catch(err => {console.log(err)})
})


ipcMain.on('save-file-dialog', (event, default_Path, calback) => {
  dialog.showSaveDialog({
    filters: [
      { name: 'Sequence', extensions: ['seq'] }
    ],
    defaultPath: default_Path,
    'showOverwriteConfirmation':false
  }).then(result => {
    console.log(result)
    if (!result.canceled) {
      console.log('callback is: ' + calback)
      event.reply(calback, result.filePath)
    }
  }).catch(err => {console.log(err)})
})

ipcMain.on('open-folder-dialog', (event, default_Path, calback) => {
  dialog.showOpenDialog({
    properties: ['openDirectory'],
    defaultPath: default_Path,
  }).then(result => {
    if (!result.canceled) {
      console.log(result.filePaths)
      event.reply(calback, result.filePaths[0])
    }
  }).catch(err=>{console.log(err)})
})

app.on('window-all-closed', (e) => {
  e.preventDefault()
  ws.send(tools.parseCmd('close_all'));
  if (process.platform !== 'darwin') {
    setTimeout(function() {
      app.quit();
    }, 10000);
  }
})

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow()
  }
})

function updatefoot(msg, color='w3-red'){
  let code = `
  document.getElementById("footStatus").innerHTML="${msg}"
  `
  mainWindow.webContents.executeJavaScript(code);
}

function showInternalErrorModal(msg){
  mainWindow.webContents.send('show-server-error', msg);
}

// save_log
ipcMain.on('save_log', (event, msg, type='info', audit=0) => {
  try{
    ws.send(tools.parseCmd('log_to_db',{ 'msg':msg, 'msg_type':type, 'audit':audit}));
  }catch(err){
    console.log('save log error')
  }
  
})

// show info dialog
ipcMain.on('show-info-alert', (event, title, msg) => {
  mainWindow.webContents.send('show-info-alert',title, msg);
})

// show warning dialog
ipcMain.on('show-warning-alert', (event, title, msg) => {
  mainWindow.webContents.send('show-warning-alert',title, msg);
})

// show alert dialog
ipcMain.on('show-alert-alert', (event, title, msg) => {
  mainWindow.webContents.send('show-alert-alert',title, msg);
})

// show internal error dialog
ipcMain.on('show-server-error', (event, msg) => {
  mainWindow.webContents.send('show-server-error', msg);
})

// show login dialog
ipcMain.on('show-login', (event) => {
  let code = `document.getElementById("modal_login").style.display="block";`;
  mainWindow.webContents.executeJavaScript(code);

})

// show file export dialog
ipcMain.on('show-file-export', (event) => {
  let code = `document.getElementById("modal_file_export").style.display="block";`;
  mainWindow.webContents.executeJavaScript(code);
})

ipcMain.on('show-option-dialog', (event, title, msg, callback, args) => {
  const options = {
    type: 'info',
    title: title,
    message: msg,
    buttons: ['Yes', 'No']
  }
  dialog.showMessageBox(mainWindow, options)
  .then(result => {
    if (result.response == 0){
      event.reply(callback, result.response, args);
    }
  }).catch(err => {
    console.log(err)
  })
})
ipcMain.on('ignoreMouse', (event,state) => {
  mainWindow.setIgnoreMouseEvents(state);
})

ipcMain.on('exejavascript', (event,code) => {
  mainWindow.webContents.executeJavaScript(code);
})
ipcMain.on('updateFootStatus', (event,msg) => {
  updatefoot(msg);
})
ipcMain.on('login-changed', (event) => {
  mainWindow.webContents.send('refresh_user_accounts');
})
ipcMain.on('trigger_tanslate', (event) => {
  mainWindow.webContents.send('trigger_tanslate');
})


// detect config changed
ipcMain.on('trigger_config_changed', (event)=>{
  mainWindow.webContents.send('update_config');
  ws.send(tools.parseCmd('load_sys_config',curPath));
})

ipcMain.on('openTeachPosPdf', (event, langID) => {
  let teachPdfWin = new PDFWindow({
    width: 800,
    height: 600
  })

  let pdfPath = path.join(appRoot, `doc/${langID}/Teach_digitest.pdf`);
  if(langID===undefined){
    pdfPath =path.join(appRoot, 'doc/en/Teach_digitest.pdf');
  }

  teachPdfWin.loadURL(pdfPath)
  teachPdfWin.maximize();
  teachPdfWin.removeMenu();
  teachPdfWin.once('ready-to-show', () => {
    teachPdfWin.show();
  })
  teachPdfWin.on('closed', () => {
    teachPdfWin = null
  })

})
ipcMain.on('toggle_monitor',(event,start)=>{
  mainWindow.webContents.send('toggle_monitor', start);
})

ipcMain.on('system-inited', (event) => {
  mainWindow.webContents.send('system-inited');
})