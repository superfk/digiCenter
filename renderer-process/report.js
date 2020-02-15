const {ipcRenderer} = require("electron");
var moment = require('moment');
let tools = require('../assets/shared_tools');
let ws

var now = moment().format("YYYY-MM-DDTHH:mm:ss.000");
const export2fileBtn = document.getElementById('export-test-data-to-file');
const mytable_visible = document.getElementById('report-csv-table-visible');
const projectField = document.getElementById('project-field');
const batchField = document.getElementById('batch-field');
const operatorField = document.getElementById('operator-field');
var startDateField = document.getElementById('date-start');
var endDateField = document.getElementById('date-end');
const queryData = document.getElementById('query-data');

const exportStart = document.getElementById('export-start');

const plotMargin = { t: 40, r: 80, l: 40, b: 80};
const config = {
  displaylogo: false,
  modeBarButtonsToRemove: ['toImage','lasso2d','select2d', 'pan2d','zoom2d','hoverClosestCartesian','hoverCompareCartesian','toggleSpikelines'],
  responsive: true
};


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
    console.log('websocket in report connected')
    ws.send(tools.parseCmd('hello'))
  });

  ws.on('ping',()=>{
    ws.send(tools.parseCmd('pong','from report'));
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
        case 'reply_query_data_from_db':
          showData(data.res);
          break;
        case 'reply_export_test_data_from_client':
          if(data.resp_code == 0) {
            ipcRenderer.send('show-alert-alert',data.title, data.res);
          }
          else{
            ipcRenderer.send('show-info-alert',data.title, data.res);
          }
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


var getNow = function(fmt){
  if(fmt){
    return moment().format(fmt);
  }else{
    return moment().format("YYYY-MM-DDTHH:mm");
  }
}

startDateField.value = getNow("YYYY-MM-DDT00:00");
endDateField.value = getNow("YYYY-MM-DDT23:59");

var code = null;

var t = $('#test-data-table-in-report').DataTable({
  deferRender:    true,
  scrollX: true,
  scrollY:        200,
  scrollCollapse: true,
  scroller:       true,
  pageLength: 100
});

// save log to database function
var savelog = function(msg, type='info', audit=0){
  ipcRenderer.send('save_log',msg , type, audit);
}

function showData(res){
  if (typeof res !== 'undefined' && res.length > 0){
    createTable(res);
    let x_val = res.map(a=>{
      let dateB = moment(new Date(a.Recordtime)).format('YYYY/MM/DD hh:mm:ss');
      return dateB
    });
    let h_val = res.map(a=>a.Hardness_result);
    let t_val = res.map(a=>a.Temperature);
    generateEventPlot(x_val, h_val, t_val)
    repositionChart()
    ipcRenderer.send('completed-indet-progressbar','done!');
    setTimeout(function(){
      ipcRenderer.send('abort-indet-progressbar');
    },500);
    // chartRelayout('hardnessVStemp_plot');
  }else{
    emptyTable();
    cleraChart('hardnessVStemp_plot');
    ipcRenderer.send('completed-indet-progressbar','done!');
    setTimeout(function(){
      ipcRenderer.send('abort-indet-progressbar');
    },500);

  }
}

queryData.addEventListener('click', (event) => {
  savelog('Click query data button', 'info', 1);
  var filter = {
    'project': projectField.value,
    'batch': batchField.value,
    'operator': operatorField.value,
    'date_start': startDateField.value+':00.000',
    'date_end': endDateField.value+':59.999'
  }
  ipcRenderer.send('start-indet-progressbar','Waiting for query', 'Waiting for query', '');
  ws.send(tools.parseCmd('query_data_from_db',filter));
})

export2fileBtn.addEventListener('click', (event) => {
  savelog('Click export to file button', 'info', 1);
  let fpath = document.getElementById('export-filename');
  fpath.value = getNow("YYYY-MM-DD_HHmmss");
  ipcRenderer.send('show-file-export');
})


exportStart.addEventListener('click', (event) => {
  savelog('Click export to file button', 'info', 1);
  let t = $('#test-data-table-in-report').DataTable();
  let tableData = t.data().toArray();
  let fpath = document.getElementById('export-filename');
  let expOpt = getExportOptions()
  ws.send(tools.parseCmd('export_test_data_from_client',{'tabledata':tableData, 'path':fpath.value, 'option':expOpt}));
})

var getExportOptions = function(){
  var opt = [];
  if ($('#export-option-csv').is(":checked"))
  {
    // it is checked
    opt.push('csv');
  }
  if ($('#export-option-excel').is(":checked"))
  {
    // it is checked
    opt.push('excel');
  }
  console.log(opt);
  return opt;
}




function createTable(tableData) {
  
  var my_columns = [];

  $.each( tableData[0], function( key, value ) {
          var my_item = {};
          my_item.data = key;
          my_item.title = key;
          my_columns.push(my_item);
  });

  t.destroy();

  t = $('#test-data-table-in-report').DataTable({
    data: tableData,
    columns: my_columns,
    deferRender:    true,
    scrollX: true,
    scrollY:        400,
    scrollCollapse: true,
    scroller:       true,
    pageLength: 100
  });

  mytable_visible.classList.remove("w3-hide");
  mytable_visible.classList.add("w3-show");
  t.draw();

}

function emptyTable() {

  t.destroy();
  t = $('#test-data-table-in-report').DataTable({
    deferRender:    true,
    scrollX: true,
    scrollY:        400,
    scrollCollapse: true,
    scroller:       true,
    pageLength: 100
  });
  t.clear()

  mytable_visible.classList.remove("w3-hide");
  mytable_visible.classList.add("w3-show");
  t.draw();

}

function generateEventPlot(xtime,hardnessdata,tempdata){

  var trace1 = {
        // x: h_data_x,
        type: "scattergl",
        name: 'temperature',
        x: xtime,
        y: tempdata,
        mode: 'lines',
        line: {
          width: 2,
          color: 'red',

        }
      };

    var trace2 = {
      // x: h_data_x,
      type: "scattergl",
      name: 'hardness',
      x: xtime,
      y: hardnessdata,
      yaxis: 'y2',
      mode: 'lines+markers',
      marker: { size: 8,color:'blue'},
      line: {
        dash: 'dot',
        width: 2,
        color: 'blue'
      }
    };

    var data = [trace1,trace2];

    var layout = {
      xaxis: {
        title: 'Timestamp',
        automargin: true,
        tickangle: 'auto',
        type: 'datetime'
      },
      yaxis: {
        title: '℃'
      },
      yaxis2: {
        title: 'hardness',
        titlefont: {color: 'rgb(148, 103, 189)'},
        tickfont: {color: 'rgb(148, 103, 189)'},
        overlaying: 'y',
        side: 'right',
        range: [0, 100]
      },
      showlegend: true,
      legend: {"orientation": "h",x:0, xanchor: 'left',y:1.2,yanchor: 'top'},
      width: 400,
      height: 500,
      autosize: true,
      font: { color: "dimgray", family: "Arial", size: 10}
    };
    
    Plotly.newPlot('hardnessVStemp_plot', data, layout,config);
}

function cleraChart(plot_id){
  Plotly.purge(plot_id);
}

$('#table-tab').on('click', function(){
  $($.fn.dataTable.tables(true)).DataTable()
  .columns.adjust();
})

function repositionChart(){
  var update = {
    autosize: true
  };
  if (!$('#hardnessVStemp_plot').html()===''){
    // check if chart has data, if no data, the following function will throw error
    Plotly.relayout('hardnessVStemp_plot', update);
  }
  Plotly.relayout('hardnessVStemp_plot', update);
}

generateEventPlot();
repositionChart();

$('#chart-tab').on('click', repositionChart )
