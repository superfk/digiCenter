const {ipcRenderer,shell} = require("electron");
const path = require('path');
const { clipboard } = require('electron')
const remote = require('electron').remote;
const appRoot = require('electron-root-path').rootPath;
let tools = require('../assets/shared_tools');
let ws;

// General config
const machine_ip = document.getElementById("machine_ip");
const digitest_com = document.getElementById("digitest_com");
const digitest_manual_mode_chk = document.getElementById('digitest_mode_switch');
const btn_to_choose_expFolder = document.getElementById("choose_export_folder_btn");
const export_path = document.getElementById("export_path");
const db_server = document.getElementById("db_server");
const apply_change_general = document.getElementById("apply_change_general");
// const btn_getHostName = document.getElementById("auto_getHostname_btn");
const computerName = document.getElementById("computerName");
const openTeachPosPdf = document.getElementById('open_teach_pos_pdf');
let wsReady = false

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
      console.log('websocket in config connected');
      reload_config();
      get_user_accounts();
      get_user_roles();
  });
  
  ws.on('ping',()=>{
    ws.send(tools.parseCmd('pong','from config'));
  })
    
  ws.on('message', function incoming(message) {

      try{
          msg = tools.parseServerMessage(message);
          let cmd = msg.cmd;
          let data = msg.data;
          switch(cmd) {
            case 'ping':
              console.log('got server data ' + data)
              ws.send(tools.parseCmd('pong',data));
              break;
            case 'reply_log_to_db':
              console.log(data);
              break;
            case 'get_ip':
              machine_ip.value = data;
              break;
            case 'get_digitest_com':
              digitest_com.value = data;
              break;
            case 'get_digitest_manual_mode':
              digitest_manual_mode_chk.checked = data;
              break;
            case 'get_export_folder':
              console.log('export_path.value', data)
              export_path.value = data;
              break;
            case 'get_db_server':
              // db_server.value = data;
              break;
            case 'reply_checking_config':
              if (data){
                ipcRenderer.send('show-info-alert', window.lang_data.modal_info_title, window.lang_data.save_config_ok);
                ipcRenderer.send('trigger_config_changed');
              }else{
                ipcRenderer.send('show-alert-alert', window.lang_data.modal_alert_title, window.lang_data.save_config_NG);
              }
              break;
            case 'get_hostname':
              computerName.innerHTML = 'Your Computer Name:' + data ;
              break;
            case 'reply_get_user_account_list':
              createUserAccountTable(data);
              break;
            case 'reply_add_new_user':
              switch(data[0]) {
                case 0:
                  ipcRenderer.send('show-warning-alert', window.lang_data.modal_warning_title, data[1])
                  $('#new-user-account-modal').hide();
                  break;
                case 1:
                  // code block
                  $('#copy_pw').off('click',copy2clipboard);
                  var txt = `New password is <b id='rnd_pw'>${data[2]}</b>, Please enter it when next login. <p><button id='copy_pw' class="w3-button w3-border w3-small">Copy</button></p>`;
                  $('#rand_pw_indicator').html(txt);
                  $('#copy_pw').on('click',copy2clipboard);
                  $('#rand_pw_indicator').show();
                  get_user_accounts()
                  break;
                default:
                  $('#new-user-account-modal').hide();
                  // code block
              }
              break;
            case 'reply_delete_user':
              if (data[0]===1){
                get_user_accounts();
              }else{
                ipcRenderer.send('show-warning-alert', window.lang_data.modal_warning_title, data[1]);
              }
              break;
            case 'reply_activate_user':
              if (data[0]===1){
                get_user_accounts();
              }else{
                ipcRenderer.send('show-warning-alert', window.lang_data.modal_warning_title, data[1]);
              }
              break;
            case 'reply_deactivate_user':
              if (data[0]===1){
                get_user_accounts();
              }else{
                ipcRenderer.send('show-warning-alert', window.lang_data.modal_warning_title, data[1]);
              }
              break;
            case 'reply_give_new_password':
              if (data[0]===1){
                get_user_accounts();
              }else{
                ipcRenderer.send('show-warning-alert', window.lang_data.modal_warning_title, data[1]);
              }
              break;
            case 'reply_get_user_role_list':
              console.log(data)
              createRoleTable(data);
              var role_list = data.map(function(obj){
                return obj.User_Role
              })
              update_user_roles_in_dropdown(role_list)
              table_role_list.row(`:contains(${selected_role})`).select();
              break;
            case 'reply_get_function_list':
              createFncTable(data);
              break;
            case 'reply_update_fnc_of_role':
              if (data[0] === 1){
                // update ok
                ipcRenderer.send('show-info-alert', window.lang_data.modal_info_title, data[1]);
                get_function_list();
              }else{
                // update error
                ipcRenderer.send('show-warning-alert', window.lang_data.modal_warning_title, data[1]);
                get_function_list();
              }
              break;
            case 'reply_add_role':
              let new_role_val = $("#new-role-name").val();
              if (data[0] === 1){
                // update ok
                // ipcRenderer.send('show-info-alert', "Info", res[1]);
                selected_role = new_role_val;
                get_user_roles()
                get_function_list();
              }else{
                // update error
                ipcRenderer.send('show-warning-alert', window.lang_data.modal_warning_title, data[1]);
                get_function_list();
              }
              break;
            case 'reply_delete_role':
              if (data[0] === 1){
                // update ok
                // ipcRenderer.send('show-info-alert', "Info", res[1]);
                get_user_roles();
                selected_role = "Guest"
                get_function_list();
              }else{
                // update error
                ipcRenderer.send('show-warning-alert', window.lang_data.modal_warning_title, data[1]);
                get_user_roles()
                selected_role = "Guest"
                get_function_list();
              }
              break;
            case 'reply_set_new_password_when_first_login':
              break;
            case 'reply_get_syslog_from_db':
              if(data[0] == 1){
                createTable(data[1])
                ipcRenderer.send('show-info-alert', window.lang_data.modal_info_title, data[2]);
                $("#systemlog_link").attr("href", data[3])
                $("#systemlog_link").html(data[3])
              }
              break;
            case 'update_sys_default_config':
              updateServerSeqFolder(data);
              break;
            case 'reply_server_error':
              ipcRenderer.send('show-server-error',  data.error);
              break;
            default:
                console.log('Not found this cmd' + cmd)
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

connect();


// ===============================================================
// General Configuration Panel                                   |
// ===============================================================

// get current ip
function getMachineIP() {
  ws.send(tools.parseCmd('getIP'));
}
// get digitest COM
function getDigiTestCOM() {
  ws.send(tools.parseCmd('get_digitest_com'));
}
// get digitest manual mode
function getDigiTestManualMode() {
  ws.send(tools.parseCmd('get_digitest_manual_mode'));
}
// get current export folder
function getExportFolder() {
  ws.send(tools.parseCmd('getExportFolder'));
}
// get_db_server
function getDbServer() {
  ws.send(tools.parseCmd('getDBServer'));
}

function reload_config(){
  var curPath = path.join(appRoot, 'config.json')
  ws.send(tools.parseCmd('load_sys_config',curPath));
  getMachineIP();
  getDigiTestCOM();
  getDigiTestManualMode();
  getExportFolder();
  getDbServer();
}


// set machine ip
function update_machine_remote(ip) {
  ws.send(tools.parseCmd('update_machine_remote',ip));
}

// set digitest com
function update_digitest_remote(COM) {
  ws.send(tools.parseCmd('update_digitest_remote',COM));
}

// set digitest manual mode
function update_digitest_manual_mode(enableManualMode) {
  ws.send(tools.parseCmd('update_digitest_manual_mode',enableManualMode));
}

// set default export folder
function update_default_export_folder(folder) {
  ws.send(tools.parseCmd('update_default_export_folder',folder));
}

// set default export folder
function update_database_server(servername) {
  ws.send(tools.parseCmd('update_database_server',servername));
}

function updatesChecker(configs){
  ws.send(tools.parseCmd('check_config_updated',configs));
}

btn_to_choose_expFolder.addEventListener('click', (event) => {
  ipcRenderer.send('open-folder-dialog', export_path.value , 'update-export-folder');
});

ipcRenderer.on('update-export-folder', (event, folder) => {
  console.log(folder)
  export_path.value = folder;
})

apply_change_general.addEventListener('click', (event) => {

  let ip = machine_ip.value;
  let COM = digitest_com.value;
  let exp_path = export_path.value;
  let manual_mode_check = digitest_manual_mode_chk.checked;
  // let db_ser = db_server.value;
  let result = {};
  result['machine_ip'] = ip;
  result['digitest_COM'] = COM;
  result['export_folder'] = exp_path;
  result['digitest_manual_mode'] = manual_mode_check;
  // result['db_server'] = db_ser;
  update_machine_remote(ip);
  update_digitest_remote(COM);
  update_digitest_manual_mode(manual_mode_check)
  update_default_export_folder(exp_path);
  // update_database_server(db_ser);
  updatesChecker(result);
});

// btn_getHostName.addEventListener('click', (event) => {
//   ws.send(tools.parseCmd('getHostName'));
// });

// ===============================================================
// Teach Pos Panel                                            |
// ===============================================================
openTeachPosPdf.addEventListener('click', ()=>{
  var langID = window.langID;
  ipcRenderer.send('openTeachPosPdf',langID)
})

// ===============================================================
// User Account Panel                                            |
// ===============================================================

// User config
var selected_user = ''
var selected_role_by_user = ''
const user_account_tab = document.getElementById('user_account_tab');

// define table
var table_user_list = $('#user-list-table').DataTable({
  deferRender:    true,
  scrollX: false,
  scrollY:        400,
  scrollCollapse: true,
  paging: false,
  "lengthChange": false,
  "searching": true,
  'select': {
    'style': 'single'
 }
});

$('.config-sidebar').on('click', function(){
  $($.fn.dataTable.tables(true)).DataTable()
  .columns.adjust();
})

user_account_tab.addEventListener('click', (event) =>{
  $($.fn.dataTable.tables(true)).DataTable()
  .columns.adjust();
  get_user_accounts();
})

ipcRenderer.on('refresh_user_accounts', (event) => {
  if (ws.readyState === 1){
    get_user_accounts();
  }
})

function get_user_accounts(){
  ws.send(tools.parseCmd('get_user_account_list'));
}



function createUserAccountTable(tableData) {
  
  var my_columns = [];

  $.each( tableData[0], function( key, value ) {
          var my_item = {};
          my_item.data = key;
          my_item.title = key;
          my_columns.push(my_item);
  });

  table_user_list.destroy();

  table_user_list = $('#user-list-table').DataTable({
    data: tableData,
    columns: my_columns,
    deferRender:    true,
    scrollX: false,
    scrollY:        400,
    scrollCollapse: true,
    paging: false,
    autowidth: true,
    dom: 'Bfrtip',
    "lengthChange": false,
    "searching": false,
    'select': {
      'style': 'single'
   },
   
    "columnDefs": [ 

      {"targets": 2,
      "data": "Status",
      "render": function ( data, type, row, meta ) {
        if (data===0){
          return "<div class='w3-tooltip'><i class='fas fa-user-slash' style='color:red'></i> D<span class='w3-text'>isabled</span></div>";
        }else if (data===1){
          return "<div class='w3-tooltip'><i class='fas fa-user-check' style='color:green'></i> E<span class='w3-text'>nabled</span></div>";
        }else{
          return "<div class='w3-tooltip'><i class='far fa-trash-alt' style='color:black'></i> R<span class='w3-text'>etired</span></div>";
        }
      },
      "width": 100   
    },
    {
      "targets": 3,
      "data": "First_login",
      "render": function ( data, type, row, meta ) {
        if (data){
          return "<div class='w3-tooltip w3-large'><i class='fas fa-fingerprint' style='color:red'></i> Y<span class='w3-text'>es</span></div>";
        }else{
          return "<div class='w3-tooltip w3-large'><i class='far fa-address-card' style='color:green'></i> N<span class='w3-text'>o</span></div>";
        }
      },
      "width": 100
    }
  ]
  });

  table_user_list.draw();

}

var add_new_user_btn =  $('#add_new_user_btn');
var delete_user_btn = $('#delete_user_btn');
var activate_user_btn = $('#activate_user_btn');
var deactivate_user_btn = $('#deactivate_user_btn');
var new_pw_btn = $('#new_pw_btn');
var new_user_role_drop = $('#new-user-role-dropdown');
var new_use_confirm_btn = $('#new-user-confirm-btn');

function update_user_roles_in_dropdown(roles){

  new_user_role_drop.empty('');

  // clear previous event listener first
  $('#new-user-role-dropdown > a').off('click', listenSelectDrop);
  // map role to dropdown
  roles.forEach(insertItems);
  
  function insertItems(item,index){
    new_user_role_drop.append( `<a href="#" data-roles=${item} class="w3-bar-item w3-button">${item}</a>`);
  }

  $('#new-user-role-dropdown > a').on('click', listenSelectDrop);
  
}

function listenSelectDrop(event){
  var selected_role = $(event.target).data("roles");
  console.log('selected role: '+ selected_role)
  $('#please_select_role_btn').html(selected_role + `<i class="fas fa-sort-down w3-large w3-margin-left"></i>`);
}

// show add user dialog
add_new_user_btn.on('click',function(){
  $('#rand_pw_indicator').hide();
  $('#rand_pw_indicator').empty();
  $('#new-user-account-modal').show();
  $("#new-user-name-input").focus().select();
})

new_use_confirm_btn.on('click',function(){
  var new_username = $("#new-user-name-input").val();
  var assign_userrole = $('#please_select_role_btn').text();
  ws.send(tools.parseCmd('add_new_user',{'userid':new_username, 'role':assign_userrole}));
})

function copy2clipboard(event){
  var rndpw = $('#rnd_pw').text();
  clipboard.writeText(rndpw);
}

delete_user_btn.on('click',function(){
  ws.send(tools.parseCmd('delete_user',{'userid':selected_user}));
})

activate_user_btn.on('click',function(){
  ws.send(tools.parseCmd('activate_user',{'userid':selected_user}));  
})

deactivate_user_btn.on('click',function(){
  ws.send(tools.parseCmd('deactivate_user',{'userid':selected_user}));
})

new_pw_btn.on('click',function(){
  ws.send(tools.parseCmd('give_new_password',{'userid':selected_user, 'role':selected_role_by_user}));
})

table_user_list.on( 'select', function ( e, dt, type, indexes ) {
  if ( type === 'row' ) {
    console.log(table_user_list.row( { selected: true } ).data())
    selected_user = table_user_list.row( { selected: true } ).data()['User Name'];
    selected_role_by_user = table_user_list.row( { selected: true } ).data()['Role'];
  }
} );

table_user_list.on( 'deselect', function ( e, dt, type, indexes ) {
  if ( type === 'row' ) {
    selected_user = '';
    selected_role_by_user='';
  }
} );


// ===============================================================
// User Role Panel                                               |
// ===============================================================

// User config
var selected_role = ''
const user_role_tab = document.getElementById('user_role_tab');

// define table
var table_role_list = $('#role-list-table').DataTable({
  deferRender:    true,
  scrollX: false,
  scrollY:        400,
  scrollCollapse: true,
  paging: false,
  ordering: false,
  "lengthChange": false,
  "searching": false,
  'select': {
    'style': 'single'
 },
  rowReorder: true
});

var table_func_list = $('#func-list-table').DataTable({
  deferRender:    true,
  scrollX: false,
  scrollY:        700,
  scrollCollapse: true,
  paging: false,
  "lengthChange": false,
  "searching": false,
  'select': {
    'style': 'single'
 },
 columnDefs:[
  {"targets":[0,2,3], "width":"20px"},
  {"targets":[1], "width":"200px"},
  {"targets":4, "visible":false},
  {"targets":5, "visible":false}
 ]
});

user_role_tab.addEventListener('click', (event) =>{
  $($.fn.dataTable.tables(true)).DataTable()
  .columns.adjust();
})

function get_user_roles(){
  ws.send(tools.parseCmd('get_user_role_list'));
}

function get_function_list(){
  if(ws.readyState===1){
    ws.send(tools.parseCmd('get_function_list', {'role':selected_role}));
  }
}


function createRoleTable(tableData) {
  
  var my_columns = [];

  $.each( tableData[0], function( key, value ) {
          var my_item = {};
          my_item.data = key;
          my_item.title = key;
          my_columns.push(my_item);
  });

  table_role_list.destroy();

  table_role_list = $('#role-list-table').DataTable({
    data: tableData,
    columns: my_columns,
    deferRender:    true,
    scrollX: false,
    scrollY:        400,
    scrollCollapse: true,
    paging: false,
    ordering: false,
    "lengthChange": false,
    "searching": false,
    'select': {
      'style': 'single'
   },
   rowReorder: true
  });

  table_role_list.draw();

}

function createFncTable(tableData) {
  var my_columns = [];

  $.each( tableData[0], function( key, value ) {
          var my_item = {};
          my_item.data = key;
          my_item.title = key;
          my_columns.push(my_item);
  });

  table_func_list.destroy();

  console.log(tableData)
  console.log(my_columns)

  table_func_list = $('#func-list-table').DataTable({
    data: tableData,
    columns: my_columns,
    deferRender:    true,
    scrollX: false,
    scrollY:        700,
    scrollCollapse: true,
    paging: false,
    "lengthChange": false,
    "searching": false,
    'select': {
      'style': 'single'
   },
   
   "columnDefs": [ 

    {"targets": 0, "width": 20},

    {
      "targets":1, 
      'className': 'dt-body-left',
      "render": function ( data, type, row, meta ) {
        if (data.indent == 0){
          return `<i class="fas fa-caret-right">  <b class='w3-medium'>${data.name}</b></i>`;
        }else{
          let preSpcae = '';
          for(i=0;i<data.indent;i++){
            preSpcae += '&nbsp &nbsp'
          }
          return `${preSpcae}<i class="fas fa-genderless">  ${data.name}</i>`;
        }
      },
      "width": 200
    },

    {"targets": 2,
    "data": "Enabled",
    "render": function ( data, type, row, meta ) {
      if (data){
        return "<i class='far fa-check-square fa-2x'></i>";
      }else{
        return "<i class='far fa-square fa-2x'></i>";
      }
    },
    "width": 20   
  },
  {
    "targets": 3,
    "data": "Visibled",
    "render": function ( data, type, row, meta ) {
      if (data){
        return "<i class='far fa-check-square fa-2x'></i>";
      }else{
        return "<i class='far fa-square fa-2x'></i>";
      }
    },
    "width": 20 
  },
  {"targets":4, "visible":false},
  {"targets":5, "visible":false}
]
  });

  table_func_list.draw();

}

// select role
table_role_list.on( 'select', function ( e, dt, type, indexes ) {

  if ( type === 'row' ) {
    selected_role = table_role_list.row( { selected: true } ).data()['User_Role'];
    get_function_list();
  }
} );

table_role_list.on( 'deselect', function ( e, dt, type, indexes ) {
  if ( type === 'row' ) {
    selected_role = '';
    get_function_list();
  }
});

// update function name when change language
$('.lang-flags').on('click', function(){
  var elem = $(this);
  var langID = elem.attr('id')
  get_function_list();
})

// select function
$('#func-list-table tbody').on( 'click', 'td', function () {
  var r = $(this).parent().find('td').html().trim();
  var c = $(this).index();
  var cell = table_func_list.cell( this );
  var data = cell.data();
  if (c===2 || c===3){
    cell.data(!data);
  }
});

$('#apply_change_user_fnc').on( 'click', function () {

  let tableData = table_func_list.data().toArray();
  let fnc = tableData.map(a => a.fnc_name);
  let enbs = tableData.map(a => a.Enabled);
  let visbs = tableData.map(a => a.Visibled);

  ws.send(tools.parseCmd('update_fnc_of_role', {'role':selected_role, 'funcs':fnc, 'enabled':enbs, 'visibled':visbs}));
  
});

// add new role box
$('#add_new_role_btn').on( 'click', function () {

  $('#new-role-level').val(1);
  $('#new-user-role-modal').show();
  $("#new-role-name").focus().select();
 

});

$('#new-role-add-btn').on( 'click', function () {

  let new_role_val = $("#new-role-name").val();
  let new_role_level = $('#new-role-level').val();
  ws.send(tools.parseCmd('add_role', {'level':new_role_level, 'role':new_role_val}));
  $('#new-user-role-modal').hide();

});

// delete role
$('#delete_new_role_btn').on( 'click', function () {
  ws.send(tools.parseCmd('delete_role', {'role':selected_role}));
});

// change level of role
table_role_list.on( 'row-reordered', function ( e, diff, edit ) {
  
} );

// ===============================================================
// System log Panel                                               |
// ===============================================================

let datafields = ["Timestamp", "User_Name", "User_Role", "Log_Type", "Log_Message", "Audit"]
let dataWidth = [150,150,150,100,450,100]
var startDateField = document.getElementById('syslog_from');
var endDateField = document.getElementById('syslog_to');

var getNow = function(fmt){
  if(fmt){
    return moment().format(fmt);
  }else{
    return moment().format("YYYY-MM-DDTHH:mm");
  }
}

startDateField.value = getNow('YYYY-MM-DDT00:00');
endDateField.value = getNow('YYYY-MM-DDT23:59');

function columnsDefine(){
  let colDefine = [];
  datafields.forEach((item,index)=>{
    let col = {title:"", field:"",align:"left"};
    col.title = item;
    col.field = item;
    col.width = dataWidth[index]
    colDefine.push(col)
  })
  return colDefine;
}

let tableOption = {
  height:'600px', // set height of table (in CSS or here), this enables the Virtual DOM and improves render speed dramatically (can be any valid css height value)
  data:[{}], //assign data to table
  layout:"fitColumns", //fit columns to width of table (optional)
  columns:columnsDefine(),
}

let t = new Tabulator("#syslog-table", tableOption);

function createTable(tableData) {
  
  t = new Tabulator("#syslog-table", tableOption);
  
  t.replaceData(tableData)
  .then(function(){
      //run code after table has been successfuly updated
  })
  .catch(function(error){
      //handle error loading data
      console.log(error)
  });
}

$('#download_syslog_btn').on('click', ()=>{
  let start = startDateField.value + ':00.000'
  let end = endDateField.value + ':59.999'
  $("#systemlog_link").attr("href", '#')
  $("#systemlog_link").html('')
  ws.send(tools.parseCmd('get_syslog_from_db',{'start':start,'end': end}));
})

$('#systemlog_link').on('click', (e)=>{
  e.preventDefault();
  // Open a local file in the default app
  let fpath = $("#systemlog_link").attr("href")
  shell.openItem(fpath);

})