const {ipcRenderer} = require("electron");
const path = require('path');
const { clipboard } = require('electron')
const appRoot = require('electron-root-path').rootPath;
const zerorpc = require("zerorpc");
const client = new zerorpc.Client({ timeout: 60, heartbeatInterval: 60000 });
// // create zerorpc instance
client.connect("tcp://127.0.0.1:4242");


// ===============================================================
// General Configuration Panel                                   |
// ===============================================================

// General config
const machine_ip = document.getElementById("machine_ip");
const btn_to_choose_expFolder = document.getElementById("choose_export_folder_btn");
const export_path = document.getElementById("export_path");
const db_server = document.getElementById("db_server");
const apply_change_general = document.getElementById("apply_change_general");
const btn_getHostName = document.getElementById("auto_getHostname_btn");
const computerName = document.getElementById("computerName");

// get current ip
function getMachineIP() {
  client.invoke('getIP', (error, res) => {
    if(error) {
      console.error(error);
    }else{
      machine_ip.value = res;
    }
  })
}
// get current export folder
function getExportFolder() {
  client.invoke("getExportFolder", (error, res) => {
    if(error) {console.error(error);}else{
      export_path.value = res;
    }
  })
}
// get_db_server
function getDbServer() {
  client.invoke("getDBServer", (error, res) => {
    if(error) {console.error(error);}else{
      db_server.value = res;
    }
  })
}

function reload_config(){
  var curPath = path.join(appRoot, 'config.json')
  console.log(curPath);
  client.invoke("load_sys_config", curPath, (error, res) => {
    if(error) {console.error(error);}else{
      console.log(res);
      getMachineIP();
      getExportFolder();
      getDbServer();
    }
  })
}

reload_config();


// set machine ip
function update_machine_remote(ip) {
  client.invoke("update_machine_remote", ip, (error, res) => {
    if(error) {
      console.error(error);
      return false;
    }else{
      return true;
    }
  })
}

// set default export folder
function update_default_export_folder(folder) {
  client.invoke("update_default_export_folder", folder, (error, res) => {
    if(error) {
      console.error(error);
      return false;
    }else{
      return true;
    }
  })
}

// set default export folder
function update_database_server(servername) {
  client.invoke("update_database_server", servername, (error, res) => {
    if(error) {
      console.error(error);
      return false;
    }else{
      return true;
    }
  })
}

function updatesChecker(configs){
  client.invoke("check_config_updated",configs, (error, res) => {
    if(error) {
      console.error(error);
      ipcRenderer.send('show-alert-alert', "Error","Saving Configuration Failed");
    }else{
      if (res){
        ipcRenderer.send('show-info-alert', "Info","Saving Configuration OK");
      }else{
        ipcRenderer.send('show-alert-alert', "Error","Saving Configuration Failed");
      }
    }
  })
}

btn_to_choose_expFolder.addEventListener('click', (event) => {
  ipcRenderer.send('open-folder-dialog', 'update-export-folder');
});

ipcRenderer.on('update-export-folder', (event, folder) => {
  export_path.value = folder;
})

apply_change_general.addEventListener('click', (event) => {

  let ip = machine_ip.value;
  let exp_path = export_path.value;
  let db_ser = db_server.value;
  let result = {};
  result['machine_ip'] = ip;
  result['export_folder'] = exp_path;
  result['db_server'] = db_ser;
  update_machine_remote(ip);
  update_default_export_folder(exp_path);
  update_database_server(db_ser);
  updatesChecker(result);
});

btn_getHostName.addEventListener('click', (event) => {
  client.invoke("getHostName", (error, res) => {
    if(error) {
      console.error(error);
      return false;
    }else{
      computerName.innerHTML = 'Your Computer Name:' + res ;
    }
  })
});

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
  get_user_accounts();
})

function get_user_accounts(){
  client.invoke("get_user_account_list", (error, res) => {
    if(error) {
      console.error(error);
    }else{
      createUserAccountTable(res);
    }
  })
}

get_user_accounts();

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

  client.invoke("add_new_user", new_username, assign_userrole, (error, res) => {
    if(error) {
      console.error(error);
      $('#new-user-account-modal').hide();

    }else{

      switch(res[0]) {
        case 0:
          ipcRenderer.send('show-warning-alert', 'Warning', res[1])
          $('#new-user-account-modal').hide();
          break;
        case 1:
          // code block
          $('#copy_pw').off('click',copy2clipboard);
          var txt = `New password is <b id='rnd_pw'>${res[2]}</b>, Please enter it when next login. <p><button id='copy_pw' class="w3-button w3-border w3-small">Copy</button></p>`;
          $('#rand_pw_indicator').html(txt);
          $('#copy_pw').on('click',copy2clipboard);
          $('#rand_pw_indicator').show();
          get_user_accounts()

          break;
        default:
          $('#new-user-account-modal').hide();
          // code block
      }
    }
    
  })
})

function copy2clipboard(event){
  var rndpw = $('#rnd_pw').text();
  console.log(rndpw);
  clipboard.writeText(rndpw);
}

delete_user_btn.on('click',function(){
  
  client.invoke("delete_user", selected_user, (error, res) => {

    if(error){
      ipcRenderer.send('show-alert-alert', 'Error', res[1]);
    }else{
      if (res[0]===1){
        get_user_accounts();
      }else{
        ipcRenderer.send('show-warning-alert', 'Warning', res[1]);
      }

    }

  })
  
})

activate_user_btn.on('click',function(){

  client.invoke("activate_user", selected_user, (error, res) => {

    if(error){
      ipcRenderer.send('show-alert-alert', 'Error', res[1]);
    }else{
      if (res[0]===1){
        get_user_accounts();
      }else{
        ipcRenderer.send('show-warning-alert', 'Warning', res[1]);
      }

    }

})
  
})

deactivate_user_btn.on('click',function(){
  
  client.invoke("deactivate_user", selected_user, (error, res) => {

    if(error){
      ipcRenderer.send('show-alert-alert', 'Error', res[1]);
    }else{
      if (res[0]===1){
        get_user_accounts();
      }else{
        ipcRenderer.send('show-warning-alert', 'Warning', res[1]);
      }

    }

  })

})

new_pw_btn.on('click',function(){

  client.invoke("give_new_password", selected_user, selected_role_by_user, (error, res) => {

    if(error){
      ipcRenderer.send('show-alert-alert', 'Error', res[1]);
    }else{
      if (res[0]===1){
        get_user_accounts();
      }else{
        ipcRenderer.send('show-warning-alert', 'Warning', res[1]);
      }

    }

  })
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
  {"targets":[0,2,3], "width":"30px"},
  {"targets":4, "visible":false},
  {"targets":5, "visible":false}
 ]
});

user_role_tab.addEventListener('click', (event) =>{
  $($.fn.dataTable.tables(true)).DataTable()
  .columns.adjust();
})

function get_user_roles(){
  client.invoke("get_user_role_list", (error, res) => {
    if(error) {
      console.error(error);
      return false;
    }else{
      createRoleTable(res);
      var role_list = res.map(function(obj){
        return obj.User_Role
      })
      update_user_roles_in_dropdown(role_list)
      table_role_list.row(`:contains(${selected_role})`).select();
    }
  })
}

get_user_roles();

function get_function_list(){
  client.invoke("get_function_list", selected_role, (error, res) => {
    if(error) {
      console.error(error);
      return false;
    }else{
      createFncTable(res);
    }
  })
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

      {"targets": 0, "width": 30},

      {
        "targets":1, 
        'className': 'dt-body-left'
      },

      {"targets": 2,
      "data": "Enabled",
      "render": function ( data, type, row, meta ) {
        if (data){
          return "<i class='far fa-check-square'></i>";
        }else{
          return "<i class='far fa-square'></i>";
        }
      },
      "width": 30   
    },
    {
      "targets": 3,
      "data": "Visibled",
      "render": function ( data, type, row, meta ) {
        if (data){
          return "<i class='far fa-check-square'></i>";
        }else{
          return "<i class='far fa-square'></i>";
        }
      },
      "width": 30 
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
    console.log(selected_role)
    get_function_list();
  }
} );

table_role_list.on( 'deselect', function ( e, dt, type, indexes ) {
  if ( type === 'row' ) {
    selected_role = '';
    get_function_list();
  }
});

// select function
$('#func-list-table tbody').on( 'click', 'td', function () {
  var r = $(this).parent().find('td').html().trim();
  var c = $(this).index();
  var cell = table_func_list.cell( this );
  var data = cell.data();
  console.log(data);
  if (c===2 || c===3){
    cell.data(!data);
  }
});

$('#apply_change_user_fnc').on( 'click', function () {

  let tableData = table_func_list.data().toArray();
  let fnc = tableData.map(a => a.fnc_name);
  let enbs = tableData.map(a => a.Enabled);
  let visbs = tableData.map(a => a.Visibled);
  console.log(selected_role);
  console.log(fnc);
  console.log(enbs);
  console.log(visbs);

  client.invoke("update_fnc_of_role", selected_role, fnc, enbs, visbs, (error, res) => {
    if(error) {
      console.log(error);
      ipcRenderer.send('show-alert-alert', "Error", error);
      get_function_list();
    }else{
      console.log(res);
      if (res[0] === 1){
        // update ok
        ipcRenderer.send('show-info-alert', "Info", res[1]);
        get_function_list();
      }else{
        // update error
        ipcRenderer.send('show-warning-alert', "Warning", res[1]);
        get_function_list();
      }
    }
  })
  
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

  client.invoke("add_role", new_role_val, new_role_level, (error, res) => {
    if(error) {
      console.log(error);
      ipcRenderer.send('show-alert-alert', "Error", error);
      get_user_roles()
      get_function_list();
    }else{
      console.log(res);
      if (res[0] === 1){
        // update ok
        // ipcRenderer.send('show-info-alert', "Info", res[1]);
        selected_role = new_role_val;
        get_user_roles()
        get_function_list();
        
      }else{
        // update error
        ipcRenderer.send('show-warning-alert', "Warning", res[1]);
        get_function_list();
      }
    }
  })

  $('#new-user-role-modal').hide();

});

// delete role
$('#delete_new_role_btn').on( 'click', function () {

  client.invoke("delete_role", selected_role, (error, res) => {
    if(error) {
      console.log(error);
      ipcRenderer.send('show-alert-alert', "Error", error);
      get_user_roles();
      selected_role = "Guest"
      get_function_list();
    }else{
      console.log(res);
      if (res[0] === 1){
        // update ok
        // ipcRenderer.send('show-info-alert', "Info", res[1]);
        get_user_roles();
        selected_role = "Guest"
        get_function_list();
      }else{
        // update error
        ipcRenderer.send('show-warning-alert', "Warning", res[1]);
        get_user_roles()
        selected_role = "Guest"
        get_function_list();
      }
    }
  })

});

// change level of role
table_role_list.on( 'row-reordered', function ( e, diff, edit ) {
  
} );
