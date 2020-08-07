const {ipcRenderer} = require("electron");
const path = require('path');
var fs = require('fs');
var moment = require('moment');
var Tabulator = require('tabulator-tables');
let tools = require('../assets/shared_tools');
let ws

var Stimulsoft = require("stimulsoft-reports-js");

Stimulsoft.Base.StiLicense.key =
	"6vJhGtLLLz2GNviWmUTrhSqnOItdDwjBylQzQcAOiHm03mN0+gfDK1Lbh88KidC50MUN9xADIxmQc8dC" +
	"8LPhoN7XTOwJGtRN5GNRp4MXQ5jhmJZ0MfzOI5JTNGy/pzOHsBkQkDyjmOYLLv5T0bypmo3RDMUFJKW9" +
	"6KyeaG0ooJLxNY0GPZmpz0H2LdoR9vZ3hzNI9pI2NJ5fBfs6jDeUspLkjOVrIXj7dcrXUSC/0EXy4W/Y" +
	"NIgTTfKI/N+gUeNGO891Gyj/9iNQvymhxCdNtRyy5VGDGBSG0WVatVQDpswDxFvqifTHAQ0YWYUYCrgn" +
	"5frkQqabQPrJvKJJQ6TGd9iDRi15X07I7d8b93cYGYuvLgjJumcEmaFEwK/LL4UkEJmp02EzwTeBhw34" +
	"vS3dg6l1FsuBC37WEN1m9updsrB1yAwwschLj0s42BCCKrteBUTjfYqhg1T/vFXOfazsdlOrWYrFRiar" +
	"MyepmSqrMRplCzqX8AOoe8/Vi2H3zH5JrFjygGZp+pvC5Qlot2GGdP17wiww5ycxrFMp3FrWv+kOrEZK" +
  "AR0HCq68tnlNf+AW";
  

Stimulsoft.Base.StiFontCollection.addOpentypeFontFile("../assets/css/fonts/Roboto-Black.ttf");

var report = Stimulsoft.Report.StiReport.createNewReport();

var now = moment().format("YYYY-MM-DDTHH:mm:ss.000");
const export2fileBtn = document.getElementById('export-test-data-to-file');
const mytable_visible = document.getElementById('report-csv-table-visible');
const projectField = document.getElementById('project-field');
const batchField = document.getElementById('batch-field');
const operatorField = document.getElementById('operator-field');
var startDateField = document.getElementById('date-start');
var endDateField = document.getElementById('date-end');
const queryData = document.getElementById('query-data');
const historyChart = document.getElementById('historyChart_plot')
const hardnessVStempChart = document.getElementById('hardnessVStemp_plot')

const exportStart = document.getElementById('export-start');

const plotMargin = { t: 40, r: 80, l: 40, b: 80};
const config = {
  displaylogo: false,
  modeBarButtonsToRemove: ['toImage','lasso2d','select2d', 'pan2d','zoom2d','hoverClosestCartesian','hoverCompareCartesian','toggleSpikelines'],
  responsive: true
};

let groupDataExportFilename = null;

// Batch_name: "ersgherg"
// Hardness_result: 53.4
// Humidity: 50.086
// Math_method: "mean"
// Operator: "BareissAdmin"
// Project_name: "reheasrh"
// Raw_data: "[53.2, 53.7]"
// Recordtime: "2020/07/20 10:09:37.156020"
// Sample_counter: 0
// Seq_name: "C:\data_exports\seq_files\demoSeq.seq"
// Seq_step_id: 3
// Temperature: 28.246



var groupTable = new Tabulator("#groupTableContainer", {
  height:500,
  layout:"fitColumns",
  printAsHtml:true,
  printStyled:true,
  printHeader:"<h1>Measurement Report<h1>",
  printFooter: historyChart,
  movableRows:true,
  pagination:"local", //enable local pagination.
  paginationSize:50, // this option can take any positive integer value (default = 50)
  groupStartOpen:[true,true],
  groupBy:["Project_name", "Batch_name"],
  initialSort:[
    {column:"Project_name", dir:"asc"}, //sort by this first
    {column:"Batch_name", dir:"asc"},
    {column:"Sample_counter", dir:"asc"},
  ],
  columns:[
      {title: 'Project', field:"Project_name",sorter:"string",dir:"asc",print:false},
      {title: 'Batch', field:"Batch_name",sorter:"string",dir:"asc",print:false},
      {title: 'Sample No.', field:"Sample_counter",sorter:"number",dir:"asc"},
      {title: 'Temperature', field:"Temperature",sorter:"number"},
      {title: 'Hardness', field:"Hardness_result",sorter:"number"},
      
  ],
  groupHeader: function(value, count, data, group){
    console.log(data)
    // tools.generateHardnessPlot('historyChart',0)
    // tools.plotly_addNewDataToPlot('historyChart',actTemp,value,y2val=null,sampleId=sampleIndex)
    const groupField = group._group.field
    if (groupField === 'Project_name'){
      return "<span margin-left:10px;'>Project: " + value + "</span>";
    }else{
      return "<span margin-left:10px;'>Batch: " + value + "</span>" 
      + "<span style='color:#d00; margin-left:10px;'>(" 
      + count + " item)</span>";
    }
  },
  groupHeaderPrint: function(value, count, data, group){
    const groupField = group._group.field
    if (groupField === 'Project_name'){
      return "<span margin-left:10px;'>Project: " + value + "</span>";
    }else{
      return "<span margin-left:20px;'>Batch: " + value + "</span>" 
      + "<span style='color:#d00; margin-left:10px;'>(" 
      + count + " item)</span>";
    }
  },
  downloadReady:function(fileContents, blob){
    console.log('tabledata',fileContents, 'path',groupDataExportFilename)
    let tableData = fileContents.split("\n");
    console.log('tableData',tableData)
    const header = tableData[0]
    console.log('header',header)
    const headerList = header.split(",");
    console.log('headerList',headerList)
    const contents = tableData.splice(1)
    console.log('contents',contents)
    const newtableData = contents.map((elm,idx)=>{
      const valueList = elm.split(",");
      let singleRowObj = {};
      valueList.forEach((val,index)=>{
        let hd = headerList[index]
        const parseVal = extractFirstText(val)
        let source = {[hd]:parseVal}
        Object.assign(singleRowObj, source);
      })
      return singleRowObj
    })
    console.log('tabledata',newtableData)
    //fileContents - the unencoded contents of the file
    ws.send(tools.parseCmd('export_test_data_from_client',{'tabledata':newtableData, 'path':groupDataExportFilename, 'option':['csv']}));
    //blob - the blob object for the download

    //custom action to send blob to server could be included here

    return false; //must return a blob to proceed with the download, return false to abort download
    },
});

const translateCol = ()=> [
  {title: window.lang_data.run_project_title, field:"Project_name",sorter:"string",dir:"asc",print:false},
  {title: window.lang_data.run_batch_title, field:"Batch_name",sorter:"string",dir:"asc",print:false},
  {title: window.lang_data.modal_moving_sample_sampleID, field:"Sample_counter",sorter:"number",dir:"asc"},
  {title: window.lang_data.main_indicator_temperature, field:"Temperature",sorter:"number"},
  {title: window.lang_data.main_indicator_hard, field:"Hardness_result",sorter:"number"},
  ]

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
        case 'get_export_folder':
          console.log('export_path', data)
          exportFolder = data;
          break;
        case 'reply_server_error':
          ipcRenderer.send('show-alert-alert', window.lang_data.modal_alert_title, data.error);
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

function extractFirstText(str){
  const matches = str.match(/"(.*?)"/);
  return matches
    ? matches[1]
    : str;
}

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
  // tools.generateHardnessPlot('hardnessVStemp_plot',onlyOccupySamples.length);
  
  if (typeof res !== 'undefined' && res.length > 0){
    setGroupTableData(res);
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
    // chartRelayout('historyChart_plot');
  }else{
    setGroupTableData([]);
    emptyTable();
    cleraChart('historyChart_plot');
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
  ws.send(tools.parseCmd('getExportFolder'));
  let fpath = document.getElementById('export-filename');
  fpath.value = getNow("YYYY-MM-DD_HHmmss");
  ipcRenderer.send('show-file-export');
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
  return opt;
}

exportStart.addEventListener('click', (event) => {
  savelog('Click export to file button', 'info', 1);
  let t = $('#test-data-table-in-report').DataTable();
  let tableData = t.data().toArray();
  let fpath = document.getElementById('export-filename').value;
  let expOpt = getExportOptions()
  
  console.log('tabledata',tableData, 'path',fpath)
  ws.send(tools.parseCmd('export_test_data_from_client',{'tabledata':tableData, 'path':fpath, 'option':expOpt}));
  groupDataExportFilename = fpath+'_groupData'
  exportGroupTable(groupDataExportFilename)
})

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
        title: 'Temperature(℃)'
      },
      yaxis2: {
        title: 'Hardness',
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
    
    Plotly.newPlot('historyChart_plot', data, layout,config);
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
  if (!$('#historyChart_plot').html()===''){
    // check if chart has data, if no data, the following function will throw error
    Plotly.relayout('historyChart_plot', update);
  }
  Plotly.relayout('historyChart_plot', update);
}

generateEventPlot();
repositionChart();

$('#chart-tab').on('click', repositionChart )

// /////////////////////////////
// StiReport
// /////////////////////////////
$('#call-viewer').on('click', ()=>{
  let tableData = t.data().toArray();
  let data = JSON.stringify({'data':tableData});
  createViewer(data);
})

function createViewer(data) {
  console.log('report data',data)
  ipcRenderer.send('call-report-viewer-window', data);
}

$('#call-designer').on('click', ()=>{
  let tableData = t.data().toArray();
  let data = JSON.stringify({'data':tableData});
  createDesigner(data);
})

function createDesigner(data) {
  ipcRenderer.send('call-report-designer-window', data);
}

function setGroupTableData(res){
  let gpTableData = res.map((elm, idx)=>{
    let newElm = {...elm}
    newElm.id = idx
    return newElm
  })
  groupTable.setColumns(translateCol()) 
  groupTable.setData(gpTableData);
}

function exportGroupTable(dest){
  groupTable.download("csv", dest);
}

function printTable(){
  groupTable.print(false, true);
}

// $('#print-test-data').on('click',()=>{
//   printTable()
// })

// detect select language
ipcRenderer.on('trigger_tanslate', (event)=>{
  groupTable.setColumns(translateCol()) 
})