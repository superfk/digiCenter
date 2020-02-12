const { ipcRenderer } = require('electron');
const app = require('electron').remote.app;
const path = require('path');
const appRoot = app.getAppPath();
var moment = require('moment');
var systime_hook = document.getElementById('systime');
let tools = require('./assets/shared_tools');
let ws;
let lang_data = {};


// login button
var hasLogin = false;
const loginBtn = document.getElementById('login');
const useridInput = document.getElementById('input-userid');
const pwInput = document.getElementById('input-password');
const confirmloginBtn = document.getElementById('confirm-login');
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
          console.log(data)
          let login_ok = data[0];
          let reason = data[1];
          let user = data[2];
          let role = data[3];
          let fn_list = data[4];
          let first = data[5];
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
              ipcRenderer.send('show-warning-alert',"First Login!", reason);
              $('#first_login_panel').show();
              $('#normal_login_panel').hide();
              window.addEventListener('keypress', checkkeypressFirstLogin);
              hasLogin = false;
            }else{
              // ipcRenderer.send('show-warning-alert',"Login Failed", reason);
              $('#modal_login').hide();
              window.removeEventListener('keypress', checkkeypressLogin);
            }
          }
          break;
        case 'reply_set_new_password_when_first_login':
        console.log(data)
          if (data[0]){
              ipcRenderer.send('show-info-alert',"Set Password OK", data[1]);
              $('#first_login_panel').hide();
              $('#normal_login_panel').show();
            }else{
              ipcRenderer.send('show-warning-alert',"Set Password Failed", data[1]);
            }
            window.addEventListener('keypress', checkkeypressLogin);
            window.removeEventListener('keypress', checkkeypressFirstLogin);
          break;
        case 'reply_update_default_lang':
          console.log(data)
          let lang_ID = data.langID;
          lang_data = data.langData;
          setLang(lang_ID);
          autoUpdateLang();
          break;
        case 'reply_server_error':
          console.log(data.error);
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

// change section event
list = document.getElementsByClassName("nav-button");
for (var i = 0; i < list.length; i++) {
  list[i].addEventListener("click", function (e) {
    let btstr = e.target.textContent.trim()
    ipcRenderer.send('save_log',`Click ${btstr} nav button`, 'info', 1);
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
  ws.send(tools.parseCmd('login',{'username':'Guest', 'password':''}));
}

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


$( function() {
  $( document ).tooltip();
});

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
    }
  })
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
    let txt = lang_data[elt.data('lang')];
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
        default:
          // code block
      }
    }
    
  });

}
