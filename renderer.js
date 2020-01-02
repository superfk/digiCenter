const { ipcRenderer } = require('electron');
const app = require('electron').remote.app;
const path = require('path');
var moment = require('moment');
var systime_hook = document.getElementById('systime');
// const zerorpc = require("zerorpc");

// const client = new zerorpc.Client({ timeout: 60, heartbeatInterval: 60000 });
// // create zerorpc instance
// client.connect("tcp://127.0.0.1:4242");

function refresh_systemtime(intv) {
  setInterval(function(){ 
    systime_hook.innerText = moment().format("YYYY-MM-DD HH:mm:ss");
   }, intv);
}

refresh_systemtime(1000);

function hidePlot(){
  let charts = document.querySelectorAll('#run-section .svg-container');
  if(e.target.id !=='button-run'){
     
    charts.forEach((item,index)=>{
      $(item).hide()
    })
  }else{
    let charts = document.querySelectorAll('#run-section .svg-container');
    charts.forEach((item,index)=>{
      $(item).show()
    })
  }
}

// change section event
list = document.getElementsByClassName("nav-button");
for (var i = 0; i < list.length; i++) {
  list[i].addEventListener("click", function (e) {
    ipcRenderer.send('save_log',`Click ${e.target.textContent} nav button`, 'info', 1);
    e.preventDefault();
    ipcRenderer.send('updateFootStatus',"");
  });
}


// login button
var hasLogin = false;
const loginBtn = document.getElementById('login');
const useridInput = document.getElementById('input-userid');
const pwInput = document.getElementById('input-password');
const confirmloginBtn = document.getElementById('confirm-login');
const current_login_user = document.getElementById('login_username');
const current_login_role = document.getElementById('login_userrole');

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
  // client.invoke("login",  'Guest', '', (error, res) => {
  //   if(error) {
  //     console.error(error);
  //     ipcRenderer.send('show-alert-alert',"Login Failed", res[1]);
  //   }else{
  //     // console.log(res); //login_ok, reason, user, role, fn_list
  //     if (res[0]){
  //       // login as guest
  //       current_login_user.innerHTML = res[2];
  //       current_login_role.innerHTML = '(' + res[3]+ ")";
  //       changeLoginColor(false);
  //       changeLoginAuth(res[4]);
  //       ipcRenderer.send('login-changed');

  //     }else{
  //       current_login_user.innerHTML = "Please Login";
  //       current_login_role.innerHTML = "(Guest)";
  //       changeLoginColor(false);
  //       changeLoginAuth(res[4]);
  //       ipcRenderer.send('login-changed');
  //     }
  //   }
  // })
}

init_login();

// confirm login button
confirmloginBtn.addEventListener('click', confirm_login);


// actual login confirmation function
function confirm_login(){
  ipcRenderer.send('save_log','Click confirm login button', 'info', 1);
  // client.invoke("login",  useridInput.value, pwInput.value, (error, res) => {
  //   if(error) {
  //     console.error(error);
  //     ipcRenderer.send('show-alert-alert',"Login Failed", res[1]);
  //     hasLogin = false;
  //   }else{
  //     console.log(res); //login_ok, reason, user, role, fn_list, first
  //     if (res[0]){
  //       // login ok
  //       hasLogin = true;
  //       current_login_user.innerHTML = res[2];
  //       current_login_role.innerHTML = '(' + res[3]+ ")";
  //       changeLoginColor(true);
  //       changeLoginAuth(res[4]);
  //       $('#modal_login').hide();
  //       ipcRenderer.send('login-changed');
  //     }else{
  //       // first login
  //       if (res[5]){
  //         ipcRenderer.send('show-warning-alert',"First Login!", res[1]);
  //         $('#first_login_panel').show();
  //         $('#normal_login_panel').hide();
  //         window.addEventListener('keypress', checkkeypressFirstLogin);
  //         hasLogin = false;
          
  //       }else{
  //         ipcRenderer.send('show-warning-alert',"Login Failed", res[1]);
  //         init_login();
  //         $('#modal_login').hide();
  //       }
        
  //     }
  //   }window.removeEventListener('keypress', checkkeypressLogin);
  // })
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

new_pw_confirm_btn.addEventListener('click', confirm_first_login)

var confirm_first_login = function(){
  // set_new_password_when_first_login(userID, curPW, newPW, newPWagain)
  // client.invoke('set_new_password_when_first_login', useridInput.value, current_pw.value, new_pw.value, new_pw_again.value, (error, res) => {

  //   if(error) {
  //     console.error(error);
  //     ipcRenderer.send('show-alert-alert',"Set Password Failed", res[1]);
  //   }else{
  //     console.log(res);
  //     if (res[0]){
  //       ipcRenderer.send('show-info-alert',"Set Password OK", res[1]);
  //       $('#first_login_panel').hide();
  //       $('#normal_login_panel').show();
  //     }else{
  //       ipcRenderer.send('show-warning-alert',"Set Password Failed", res[1]);
  //     }
  //   }
  //   window.addEventListener('keypress', checkkeypressLogin);
  //   window.removeEventListener('keypress', checkkeypressFirstLogin)
  // } )
}


$( function() {
  $( document ).tooltip();
});

// =========================
// language functions
// =========================

var lang_data = {}
var lang_flag = 'en'

function getDefaultLang(){
  // client.invoke('load_default_lang',appRoot, (error,res) => {
  //   if (error){
  //     console.error(error);
  //   }else{
  //     console.log(res);
  //     lang_data = res;
  //     setLang(lang_data['display_name']);
  //     autoUpdateLang()
  //   }
  // })
}

getDefaultLang()


function setLang(lang){
  $('.lang-flags').each(function(index, element){
    if (element.id === lang){
      $('.lang-flags').removeClass('langSelected');
      $(element).addClass('langSelected');
      lang_flag = lang;
    }
  })
}

// detect select language
$('.lang-flags').on('click', function(){
  var elem = $(this);
  var langID = elem.attr('id')

  setLang(langID)

  // Change default lang
  // client.invoke('update_default_lang', appRoot, langID, (error, res) =>{
  //   if (error){
  //     console.error(error)
  //   }else{
  //     lang_data = res;
  //     setLang(lang_data['display_name']);
  //     autoUpdateLang()
  //   }
    

  // } )
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
