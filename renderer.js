const { ipcRenderer } = require('electron');
const { app } = require('electron').remote;
const appRoot = require('electron-root-path').rootPath;

let appVer = '';
let appName = 'digiCenter';

if (process.env.NODE_ENV === 'development') {
  appVer = require('../../../package.json').version;
  appName = require('../../../package.json').name;
} else {
  appVer = require('electron').remote.app.getVersion();
  appName = require('electron').remote.app.name;
}

document.title= appName + ' v' + appVer;

var moment = require('moment');
var systime_hook = document.getElementById('systime');
let tools = require('./assets/shared_tools');
let ws;
// let lang_data = {};
let monitorValue = null;
window.lang_data = {};

let login_ok = false;
let reason = '';
let user = '';
let role = '';
let fn_list = [];
let first = false;

let machine_hard_idct = document.querySelectorAll('#machine_hard_idct .idct-number')[0]
let machine_temp_idct = document.querySelectorAll('#machine_tempr_idct .idct-number')[0]
let machine_humi_idct = document.querySelectorAll('#machine_hum_idct  .idct-number')[0]

let machine_hard_idct_status = document.querySelectorAll('#machine_hard_idct .idct-status')[0]
let machine_temp_idct_status = document.querySelectorAll('#machine_tempr_idct .idct-status')[0]
let machine_humi_idct_status = document.querySelectorAll('#machine_hum_idct  .idct-status')[0]
// login button
var hasLogin = false;
const loginBtn = document.getElementById('login');
const useridInput = document.getElementById('input-userid');
const pwInput = document.getElementById('input-password');
const confirmloginBtn = document.getElementById('confirm-login');
const confirmlogoutBtn = document.getElementById('confirm-logout');
const current_login_user = document.getElementById('login_username');
const current_login_role = document.getElementById('login_userrole');


// **************************************
// websocket functions
// **************************************
function connect() {
  try{
    const WebSocket = require('ws');
    ws = new WebSocket('ws://127.0.0.1:5678');
  }catch(e){
    console.log('Socket init error. Reconnect will be attempted in 1 second.', e.reason);
  }

  ws.on('open', function open() { 
    console.log('websocket in renderer connected')
    getDefaultLang();
    init_login();
    init_hw();
  });

  ws.on('ping',()=>{
    
    ws.send(tools.parseCmd('pong','from renderer'));
  })

  ws.on('message', function incoming(message) {

    try{
      
      msg = tools.parseServerMessage(message);
      let cmd = msg.cmd;
      let data = msg.data;
      switch(cmd) {
        case 'ping':
          // console.log('got server data ' + data)
          ws.send(tools.parseCmd('pong',data));
          break;
        case 'reply_log_to_db':
          console.log(data);
          break;
        case 'reply_login':
          login_ok = data[0];
          reason = data[1];
          user = data[2];
          role = data[3];
          fn_list = data[4];
          first = data[5];
          if (login_ok){
            // login as guest
            user=='Guest'?hasLogin=false:hasLogin=true;
            current_login_user.innerHTML = user;
            current_login_role.innerHTML = '(' + role + ")";
            changeLoginColor(user=='Guest'?false:true);
            changeLoginAuth(fn_list);
            $('#modal_login').hide();
            ipcRenderer.send('login-changed');
            window.removeEventListener('keypress', checkkeypressLogin);
          }else{
            changeLoginAuth(fn_list);
            // first login
            if (first){
              ipcRenderer.send('show-warning-alert',window.lang_data.modal_warning_title, reason);
              $('#first_login_panel').show();
              $('#normal_login_panel').hide();
              window.addEventListener('keypress', checkkeypressFirstLogin);
              hasLogin = false;
            }else{
              user=='Guest'?hasLogin=false:hasLogin=true;
              ipcRenderer.send('show-warning-alert',window.lang_data.modal_warning_title, reason);
              $('#modal_login').hide();
              window.removeEventListener('keypress', checkkeypressLogin);
            }
          }
          break;
        case 'reply_logout':
          login_ok = data[0];
          reason = data[1];
          user = data[2];
          role = data[3];
          fn_list = data[4];
          first = data[5];
          hasLogin=false
          current_login_user.innerHTML = user;
          current_login_role.innerHTML = '(' + role + ")";
          changeLoginColor(false);
          changeLoginAuth(fn_list);
          $('#modal_login').hide();
          ipcRenderer.send('login-changed');
          window.removeEventListener('keypress', checkkeypressLogin);
          break;
        case 'reply_set_new_password_when_first_login':
          if (data[0]){
              ipcRenderer.send('show-info-alert',window.lang_data.modal_info_title, data[1]);
              $('#first_login_panel').hide();
              $('#normal_login_panel').show();
            }else{
              ipcRenderer.send('show-warning-alert',window.lang_data.modal_warning_title, data[1]);
            }
            window.addEventListener('keypress', checkkeypressLogin);
            window.removeEventListener('keypress', checkkeypressFirstLogin);
          break;
        case 'reply_update_default_lang':
          let lang_ID = data.langID;
          window.lang_data = data.langData;
          setLang(lang_ID);
          autoUpdateLang();
          break;
        case 'reply_init_hw':
          if(data.resp_code==0){
            ipcRenderer.send('show-alert-alert','Alert',data.res + '\n' + data.reason);
          }else{
            clearInterval(monitorValue);
            monitorValue = setInterval(monitorFunction,1000)
            ipcRenderer.send('system-inited');
          }
          break;
        case 'reply_init_hw_status':
          tools.updateStatusIndicator(machine_hard_idct_status,data.digitest,window.lang_data['machine_connected'],window.lang_data['machine_disconnected'],window.lang_data['machine_running'] )
          tools.updateStatusIndicator(machine_temp_idct_status,data.digichamber,window.lang_data['machine_connected'],window.lang_data['machine_disconnected'],window.lang_data['machine_running'] )
          tools.updateStatusIndicator(machine_humi_idct_status,data.digichamber,window.lang_data['machine_connected'],window.lang_data['machine_disconnected'],window.lang_data['machine_running'] )
          break;
        case 'update_cur_status':
          updateIndicator(data.dt,data.temp,data.hum)
          break;
        case 'reply_server_error':
          ipcRenderer.send('show-server-error',  data.error);
          break;
        default:
          console.log('Not found this cmd' + cmd)
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

function refresh_systemtime(intv) {
  setInterval(function(){ 
    systime_hook.innerText = moment().format("YYYY-MM-DD HH:mm:ss");
   }, intv);
}

refresh_systemtime(1000);

function updatefoot(msg, color='w3-red'){
  document.getElementById("footStatus").innerHTML=msg;
}

// show modal event
ipcRenderer.on('show-info-alert',(event,title,msg)=>{
  document.getElementById("modal_info_message_title").innerHTML = title;
  document.getElementById("modal_info_message_text").innerHTML = msg;
  document.getElementById("modal_info_message").style.display="block";
})
ipcRenderer.on('show-warning-alert',(event,title,msg)=>{
  document.getElementById("modal_warning_message_title").innerHTML = title;
  document.getElementById("modal_warning_message_text").innerHTML = msg;
  document.getElementById("modal_warning_message").style.display="block";
})
ipcRenderer.on('show-alert-alert',(event,title,msg)=>{
  document.getElementById("modal_alert_message_title").innerHTML = title;
  document.getElementById("modal_alert_message_text").innerHTML = msg;
  document.getElementById("modal_alert_message").style.display="block";
})

ipcRenderer.on('show-server-error',(event,msg)=>{
  document.getElementById("modal_internal_exception_title").innerHTML = window.lang_data.internal_exception_title;
  document.getElementById("modal_internal_exception_text").innerHTML = window.lang_data.internal_exception_msg;
  document.getElementById("modal_internal_exception_button").innerHTML = window.lang_data.internal_exception_detail;
  document.getElementById("error_detail").innerHTML = msg;
  document.getElementById("modal_server_alert_message").style.display="block";
})

// change section event
list = document.getElementsByClassName("nav-button");
for (var i = 0; i < list.length; i++) {
  list[i].addEventListener("click", function (e) {
    let btstr = e.target.textContent.trim()
    ipcRenderer.send('save_log',`Click ${btstr} nav button`, 'info', 0);
    e.preventDefault();
    ipcRenderer.send('updateFootStatus',"");
  });
}

var checkkeypressLogin = function(e){
  var keyCode = e.keyCode;
  // detect enter
    if(keyCode == 13){
      confirm_login();
    }
}

var checkkeypressFirstLogin = function(e){
  var keyCode = e.keyCode;
  // detect enter
    if(keyCode == 13){
      confirm_first_login();
    }
}

loginBtn.addEventListener('click', (event) => {
  ipcRenderer.send('save_log','Click login button', 'info', 1);
  useridInput.value = "";
  pwInput.value = "";
  ipcRenderer.send('show-login');
  $('#first_login_panel').hide();
  $('#normal_login_panel').show();
  window.addEventListener('keypress', checkkeypressLogin);
})

var changeLoginColor = function(loginOK){
  loginBtn.classList.remove("loginOK");
  loginBtn.classList.remove("loginNG");
  if (loginOK){
    loginBtn.classList.add("loginOK");
  }else{
    loginBtn.classList.add("loginNG");
  }
}

var changeLoginAuth = function(fn_list){
  fn_list.forEach(function(item, index, array){
    // let elem = document.getElementById(item["function"]);
    let elem = $(`[data-auth="${item['function']}"]`);
    let en = item["enable"];
    let vis = item["visible"];
    if (en){
      elem.removeClass('auth_disabled').addClass('auth_enabled');
    }else{
      elem.removeClass('auth_enabled').addClass('auth_disabled');
    }
    if (vis){
      elem.removeClass('auth_invisibled').addClass('auth_visibled');
    }else{
      elem.removeClass('auth_visibled').addClass('auth_invisibled');
      
    }

  })
  
}

// actual login confirmation function
function init_login(){
  hasLogin = false;
  ipcRenderer.send('save_log','Initial login function', 'info', 1);
  ws.send(tools.parseCmd('logout'));
}

confirmlogoutBtn.addEventListener('click', ()=>{
  ipcRenderer.send('save_log','Click confirm logout button', 'info', 1);
  ws.send(tools.parseCmd('logout'));
})

// confirm login button
confirmloginBtn.addEventListener('click', confirm_login);


// actual login confirmation function
function confirm_login(){
  ipcRenderer.send('save_log','Click confirm login button', 'info', 1);
  ws.send(tools.parseCmd('login',{'username':useridInput.value, 'password':pwInput.value}));
}


// for first login
var current_pw = document.getElementById('confirm_current_pw')
var new_pw = document.getElementById('confirm_new_pw')
var new_pw_again = document.getElementById('confirm_new_pw_again')
var new_pw_confirm_btn = document.getElementById('confirm_new_pw_btn')
var back_to_normal_login = document.getElementById('back_to_normal_login')

back_to_normal_login.addEventListener('click', function(){
  $('#first_login_panel').hide();
  $('#normal_login_panel').show();
  window.addEventListener('keypress', checkkeypressLogin);
  window.removeEventListener('keypress', checkkeypressFirstLogin)
})

new_pw_confirm_btn.addEventListener('click', ()=>{
  confirm_first_login();
})

function confirm_first_login() {
  console.log('comfirmFirstLogin')
  ws.send(tools.parseCmd('set_new_password_when_first_login',
  {'userid':useridInput.value, 'curpw':current_pw.value, 'newpw':new_pw.value, 'newpaagain':new_pw_again.value}));
}


// $( function() {
//   $( document ).tooltip();
// });

// =========================
// language functions
// =========================


function getDefaultLang(){
  ws.send(tools.parseCmd('load_default_lang',appRoot));
}

function setLang(lang){
  $('.lang-flags').each(function(index, element){
    if (element.id === lang){
      $('.lang-flags').removeClass('langSelected');
      $(element).addClass('langSelected');
      $('#lang-button').text($(element).html())
      window.langID = lang;
    }
  })
}

const findLangs = (langKey)=>{
  const langKeys = Object.keys(window.lang_data)
  const langValues = Object.values(window.lang_data)
  const langRowIndex = langKeys.findIndex(elm=>elm===langKey)
  if (langRowIndex !== undefined){
    return langValues[langRowIndex]
  }else{
    return ''
  }
}

// detect select language
$('.lang-flags').on('click', function(){
  var elem = $(this);
  var langID = elem.attr('id')
  setLang(langID)
  ws.send(tools.parseCmd('update_default_lang',{'appRoot':appRoot, 'lang':langID}));
})

function autoUpdateLang(){
  $('[data-lang!=""]').each(function(i, elt){
    var elt = $(elt);
    let txt = window.lang_data[elt.data('lang')];
    var field_type = elt.data('lang_type');
    if (hasLogin && elt.attr('id') ==='login_username'){
      // do nothing
    }else{
      switch(field_type) {
        case 'innerhtml':
          elt.html(txt);
          break;
        case 'innertext':
          elt.text(txt);
          break;
        case 'plhd':
          elt.attr('placeholder',txt);
          break;
        case 'title':
          elt.attr('title',txt);
          break;
        default:
          // code block
      }
    }
  });
  ipcRenderer.send('trigger_tanslate')
}

function init_hw(){
  ws.send(tools.parseCmd('init_hw'));
}

function monitorFunction(){
  try{
    ws.send(tools.parseCmd('run_cmd',tools.parseCmd('get_cur_temp_and_humi')));
  }catch{
    console.log('websocket disconnected')
  }
  
}

function updateIndicator(hard=null, temp=null, hum=null){
  if (hard!=null){
    tools.updateNumIndicator(machine_hard_idct,hard.value, 1)
    tools.updateStatusIndicator(machine_hard_idct_status,hard.status,window.lang_data['machine_connected'],window.lang_data['machine_disconnected'],window.lang_data['machine_running'] )
  }
  if (temp!=null){
    tools.updateNumIndicator(machine_temp_idct,temp.value, 1)
    tools.updateStatusIndicator(machine_temp_idct_status,temp.status,window.lang_data['machine_connected'],window.lang_data['machine_disconnected'],window.lang_data['machine_running'] )
  }
  if (hum!=null){
    tools.updateNumIndicator(machine_humi_idct,hum.value, 1)
    tools.updateStatusIndicator(machine_humi_idct_status,hum.status,window.lang_data['machine_connected'],window.lang_data['machine_disconnected'],window.lang_data['machine_running'] )
  }
  
}

ipcRenderer.on('toggle_monitor',(event,start)=>{
  if(start){
    clearInterval(monitorValue);
    monitorValue = setInterval(monitorFunction,1000)
  }else{
    clearInterval(monitorValue);
  }
})
