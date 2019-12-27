const electron = require('electron')
const app = electron.app
const BrowserWindow = electron.BrowserWindow
const path = require('path')
const {ipcMain, dialog, shell} = require('electron')
// const appRoot = require('electron-root-path').rootPath;
const appRoot = app.getAppPath();
console.log(appRoot)
const ProgressBar = require('electron-progressbar');
let tools = require('./assets/shared_tools');
// const zerorpc = require("zerorpc");

// // zerorpc client
// const client = new zerorpc.Client({ timeout: 60, heartbeatInterval: 60000 });
// // create zerorpc instance
// client.connect("tcp://127.0.0.1:4242");
// let socket = require('socket.io-client')('http://127.0.0.1:5678/test',{transports:['WebSocket']});
let ws;

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
    console.log('got ping')
  })

  ws.on('message',(message)=>{
    try{
      msg = tools.parseServerMessage(message);
      let cmd = msg.cmd;
      let data = msg.data;
      switch(cmd) {
        case 'ping':
          console.log('got server data ' + data)
          ws.send(tools.parseCmd('pong',data));
          break;
        case 'result_of_backendinit':
          if(data.result == 1){
            console.log(data.resp)
            PY_INIT_OK=true;
            createWindow();
          }else{
            console.log(data.resp)

          }
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

connect()

/*************************************************************
 * py process
 *************************************************************/

const PY_DIST_FOLDER = 'pyserver'
const PY_FOLDER = 'server'
const PY_MODULE = 'api' // without .py suffix
let PY_INIT_OK = false;

let pyProc = null
let pyPort = null
let isProdct = false

//
const guessPackaged = () => {
  const fullPath = path.join(appRoot, PY_DIST_FOLDER)
  return require('fs').existsSync(fullPath)
}

const getScriptPath = () => {
  if (!guessPackaged()) {
    return path.join(appRoot, PY_FOLDER, PY_MODULE + '.py')
  }
  if (process.platform === 'win32') {
    console.log(path.join(appRoot, PY_DIST_FOLDER, PY_MODULE, PY_MODULE + '.exe'));
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
    console.log(script);
  } else {
    pyProc = require('child_process').spawn('python', [script, port],{ stdio: 'ignore' })
    // var batchFile = path.join(__dirname, PY_FOLDER,'start_python_server.bat')
    // var bat = shell.openItem(batchFile);
    // console.log(bat)
  }
 
  if (pyProc != null) {
    //console.log(pyProc)
    console.log('child process success on port ' + port);
    

  }
}

const exitPyProc = () => {
  pyProc.kill();
  pyProc = null;
  pyPort = null;
}

// init config and database
var init_server = function(){
  var curPath = path.join(appRoot, 'config.json')
  ws.send(tools.parseCmd('load_sys_config',curPath));
  ws.send(tools.parseCmd('backend_init'));
  // ws.send(JSON.stringify({cmd:"load_sys_config", data:'curPath'}), (res) => {
  //   console.log(res);
  //   ws.send(JSON.stringify({cmd:"backend_init", data:'curPath'}), (res,status) => {
  //     console.log(res,status)
  //     if (res === 1){
  //       PY_INIT_OK = true;
  //     }
  //     console.log(res);
  //     createWindow();
  //   })
  // })
}


app.on('ready', createPyProc)
app.on('will-quit', exitPyProc)


/*************************************************************
 * window management
 *************************************************************/

let mainWindow = null;
let progressBar = null;

const createWindow = () => {
  mainWindow = new BrowserWindow({
    width: 1024, 
    height: 600,
    icon: __dirname + '/img/appIcon.jpg', 
    webPreferences: {
      nodeIntegration: true
    }
  })
  mainWindow.loadURL(require('url').format({
    pathname: path.join(__dirname, 'index.html'),
    protocol: 'file:',
    slashes: true
  }))

  if (!guessPackaged()){
    mainWindow.webContents.openDevTools()
  }
  

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
  }, (files) => {
    if (files) {
      event.sender.send(calback, files[0])
    }
  })
})


ipcMain.on('save-file-dialog', (event, default_Path, calback) => {
  dialog.showSaveDialog({
    filters: [
      { name: 'Sequence', extensions: ['seq'] }
    ],
    defaultPath: default_Path,
  }, (file) => {
    console.log(file)
    if (file) {
      event.sender.send(calback, file)
    }
  })
})

ipcMain.on('open-folder-dialog', (event, default_Path, calback) => {
  dialog.showOpenDialog({
    properties: ['openDirectory'],
    defaultPath: default_Path,
  }, (files) => {
    if (files) {
      console.log(files)
      event.sender.send(calback, files[0])
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
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

// save_log
ipcMain.on('save_log', (event, msg, type='info', audit=0) => {
  // ws.send(JSON.stringify({cmd:"log_to_db", data:{ msg, type, audit}}), (res) => {})
    
})

// show info dialog
ipcMain.on('show-info-alert', (event, title, msg) => {
  let code = `document.getElementById("modal_info_message_title").innerHTML="${title}";`;
  code = code + `document.getElementById("modal_info_message_text").innerHTML="${msg}";`;
  code = code + `document.getElementById("modal_info_message").style.display="block";`;
  console.log(code);
  mainWindow.webContents.executeJavaScript(code);

})

// show warning dialog
ipcMain.on('show-warning-alert', (event, title, msg) => {
  let code = `document.getElementById("modal_warning_message_title").innerHTML="${title}";`;
  code = code + `document.getElementById("modal_warning_message_text").innerHTML="${msg}";`;
  code = code + `document.getElementById("modal_warning_message").style.display="block";`;

  mainWindow.webContents.executeJavaScript(code);
  updatefoot(msg, 'w3-yellow');

})

// show alert dialog
ipcMain.on('show-alert-alert', (event, title, msg) => {
  let code = `document.getElementById("modal_alert_message_title").innerHTML="${title}";`;
  code = code + `document.getElementById("modal_alert_message_text").innerHTML="${msg}";`;
  code = code + `document.getElementById("modal_alert_message").style.display="block";`;

  mainWindow.webContents.executeJavaScript(code);

  updatefoot(msg, 'w3-red');

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

ipcMain.on('show-option-dialog', (event, title, msg) => {
  const options = {
    type: 'info',
    title: title,
    message: msg,
    buttons: ['Yes', 'No']
  }
  dialog.showMessageBox(options, (index) => {
    event.returnValue = index;
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