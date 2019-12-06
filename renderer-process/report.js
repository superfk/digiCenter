const {ipcRenderer} = require("electron");
var moment = require('moment');
const zerorpc = require("zerorpc");
const client = new zerorpc.Client({ timeout: 60, heartbeatInterval: 60000 });
// create zerorpc instance
client.connect("tcp://127.0.0.1:4242");

var now = moment().format("YYYY-MM-DDTHH:mm:ss.000");
const export2fileBtn = document.getElementById('export-test-data-to-file');
const mytable_visible = document.getElementById('report-csv-table-visible');
const batchField = document.getElementById('batch-field');
const operatorField = document.getElementById('operator-field');
var startDateField = document.getElementById('date-start');
var endDateField = document.getElementById('date-end');
const queryData = document.getElementById('query-data');

const exportStart = document.getElementById('export-start');

const lines_main = {
  dash: 'solid',
  width: 4
}
const lines_sub = {
  dash: 'solid',
  width: 1
}

var getNow = function(fmt){
  if(fmt){
    return moment().format(fmt);
  }else{
    return moment().format("YYYY-MM-DDTHH:mm:ss.000");
  }
}

startDateField.value = getNow();
endDateField.value = getNow();

var code = null;

var t = $('#test-data-table-in-report').DataTable({
  deferRender:    true,
  scrollX: true,
  scrollY:        200,
  scrollCollapse: true,
  scroller:       true});

// save log to database function
var savelog = function(msg, type='info', audit=0){
  client.invoke("log_to_db",  msg, type, audit, (error, res) => {
    if(error) {console.error(error);}else{console.log(res);}
    })
}

queryData.addEventListener('click', (event) => {
  savelog('Click query data button', 'info', 1);
  var filter = {
    'batch': batchField.value,
    'operator': operatorField.value,
    'date_start': startDateField.value,
    'date_end': endDateField.value
  }
  ipcRenderer.send('start-indet-progressbar','Waiting for query', 'Waiting for query', '');
  client.invoke("query_data_from_db",  filter, (error, res) => {
    if(error) {
      console.error(error);
      ipcRenderer.send('show-alert-alert',"Saving Data Error", `Error when saving data to database!(${error})`);
      ipcRenderer.send('completed-indet-progressbar','Error!');
        setTimeout(function(){
          ipcRenderer.send('abort-indet-progressbar');
        },1000);
    }
    else{

      if (typeof res !== 'undefined' && res.length > 0){
        createTable(res);
        let t = $('#test-data-table-in-report').DataTable();
        let tableData = t.data().toArray();
        let data = [];
        let colnames = [];
        let legnd_vis = [];
        data.push(tableData.map(a => a.Hardness_1));
        data.push(tableData.map(a => a.Hardness_2));
        data.push(tableData.map(a => a.Hardness_3));
        colnames = ['Hardness_1','Hardness_2','Hardness_3'];
        legnd_vis = [true, true, true];
        showChart(data, colnames, legnd_vis, ['y','y','y'], 'Hardness', '', 'hardness_plot', 'Hardness Data', [lines_main,lines_main, lines_main]);
        data = [];
        data.push(tableData.map(a => a.WeightDry));
        data.push(tableData.map(a => a.WeightWet));
        // data.push(tableData.map(a => a.T_Liquid));
        data.push(tableData.map(a => a.Density));
        colnames = ['WeightDry', 'WeightWet', 'Density'];
        legnd_vis = [true, true, true];
        
        showChart(data, colnames, legnd_vis, ['y2','y2','y'], 'Density(g/cm<sup>3</sup>)', 'Weight(g)', 'density_plot', 'Density Data', [lines_sub,lines_sub, lines_main]);
        repositionChart()
        ipcRenderer.send('completed-indet-progressbar','done!');
        setTimeout(function(){
          ipcRenderer.send('abort-indet-progressbar');
        },500);
        // chartRelayout('hardness_plot');
        // chartRelayout('density_plot');
      }else{
        emptyTable();
        cleraChart('hardness_plot');
        cleraChart('density_plot');
        ipcRenderer.send('completed-indet-progressbar','done!');
        setTimeout(function(){
          ipcRenderer.send('abort-indet-progressbar');
        },500);

      }
      
    }
  })
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
  client.invoke("export_test_data",  tableData, fpath.value, expOpt, (error, res) => {
    if(error) {
      ipcRenderer.send('show-alert-alert',"Saving Data Error", `Error when saving data to database!(${error})`);
    }
    else{
      ipcRenderer.send('show-info-alert',"Saving Data OK", res[1]);
    }
  })
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
  if ($('#export-option-pdf').is(":checked"))
  {
    // it is checked
    opt.push('pdf');
  }
  if ($('#export-option-html').is(":checked"))
  {
    // it is checked
    opt.push('html');
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
  });

  mytable_visible.classList.remove("w3-hide");
  mytable_visible.classList.add("w3-show");
  t.draw();

}

function emptyTable(tableData) {

  t.destroy();
  t = $('#test-data-table-in-report').DataTable({
    deferRender:    true,
    scrollX: true,
    scrollY:        400,
    scrollCollapse: true,
    scroller:       true,
  });
  t.clear()

  mytable_visible.classList.remove("w3-hide");
  mytable_visible.classList.add("w3-show");
  t.draw();

}

function showChart(result, colNames, legend_vis, yaxis, y1_title, y2_title, plot_id, plot_title, lines) {
  let data = [];
  let lg_vis = [];

  legend_vis.forEach(function(item, index, array){
    if (item == true){
      lg_vis.push('True');
    }else{
      lg_vis.push('legendonly');
    }
  })

  result.forEach(function(item, index, array){
    let trace ={
        y: item,
        mode: 'lines+markers',
        marker: {size:8},
        type: 'scatter',
        name: colNames[index],
        visible: lg_vis[index],
        yaxis: yaxis[index],
        line: lines[index]
      };
    data.push(trace);
  })

  var layout = {
    title: plot_title,
    autosize: true,
    xaxis: {
      // rangeselector: selectorOptions,
      rangeslider: {}
  },
    yaxis:{
      title: y1_title,
      rangemode: 'nonnegative'
    },
    yaxis2:{
      title: y2_title,
      side: 'right',
      rangemode: 'nonnegative',
      overlaying: 'y'
    },
    // paper_bgcolor: 'rgba(0,0,0,0)',
    // plot_bgcolor: 'rgba(0,0,0,0)'    
  };

  Plotly.newPlot(plot_id, data, layout,{showSendToCloud:false, displaylogo: false, responsive: true});
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
  if (!$('#hardness_plot').html()===''){
    // check if chart has data, if no data, the following function will throw error
    Plotly.relayout('hardness_plot', update);
    Plotly.relayout('density_plot', update);
  }

  Plotly.relayout('hardness_plot', update);
  Plotly.relayout('density_plot', update);
}

$('#chart-tab').on('click', repositionChart )
