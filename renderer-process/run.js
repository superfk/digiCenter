const {ipcRenderer} = require("electron");
let tools = require('../assets/shared_tools');
let ws

// **************************************
// variable define
// **************************************

let defaultSeqPath = null;
let batchForm = document.getElementById('batchInfoForm');
let batchFormContent  = document.getElementById('batchFormContent');
let batchNew = document.getElementById('new_a_batch');
let batchLoad  = document.getElementById('load_a_batch');
let seqNameInForm = document.querySelectorAll("#batchFormContent > input[name='SeqName']")[0]
let projInForm = document.querySelectorAll("#batchFormContent > input[name='Project']")[0]
let batchInForm = document.querySelectorAll("#batchFormContent > input[name='Batch']")[0]
let numsampleInForm = document.querySelectorAll("#batchFormContent > input[name='NumberOfSample']")[0]
let noteInForm = document.querySelectorAll("#batchFormContent > textarea[name='Note']")[0]
let selectHistoryBatch = document.getElementById('SelectBatch')
let batchConfirmBtn = document.getElementById('batchConfirm');
let startSeqBtn = document.getElementById('start_test');
let stopSeqBtn = document.getElementById('stop_test');
let loadSeqBtn = document.getElementById('open_test_seq');
let setup_seq = {};
let teardown_seq = {};
let seq = [];
let loop_seq = [];
let test_flow = {
    setup: setup_seq,
    main: seq,
    loop: loop_seq,
    teardown: teardown_seq
};
const plotMargin = { t: 40, r: 80, l: 40, b: 50};
const config = {
  displaylogo: false,
  modeBarButtonsToRemove: ['toImage','lasso2d','select2d', 'pan2d','zoom2d','hoverClosestCartesian','hoverCompareCartesian','toggleSpikelines'],
  responsive: false
};


// **************************************
// init functions
// **************************************
generateEventPlot()
generateHardnessPlot()
repositionChart()
generateGauge('actualTempGauge', 23, -40, 200,'Temperature');
generateGauge('actualHumGauge', 50, 0, 100,'Humidity');



// **************************************
// generate graph functions
// **************************************

function generateEventPlot(){

  var trace1 = {
        // x: h_data_x,
        type: "scattergl",
        name: 'temperature',
        x:[],
        y: [],
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
      x:[],
      y: [],
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
        title: 'Time(s)'
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
      height: 300,
      margin: plotMargin,
      autosize: false,
      font: { color: "dimgray", family: "Arial", size: 10}
    };
    
    Plotly.newPlot('event_graph', data, layout,config);
}

function generateHardnessPlot(){
  
    var trace = {
      // x: h_data_x,
      type: "scattergl",
      x:[],
      y: [],
      mode: 'markers',
      marker: { size: 6},
      line: {
        width: 2
      }
    };
  
    var data = [trace];
    
    var layout = {
      xaxis: {
        title: '℃'
      },
      yaxis: {
        title: 'hardness',
        range: [0, 100]
      },
      width: 400,
      height: 250,
      margin: plotMargin,
      autosize: true,
      font: { color: "dimgray", family: "Arial", size: 10}
    };
    
    Plotly.newPlot('hardness_graph', data, layout, config);
  }

  
function repositionChart(){
  var update = {
    autosize: true,
  };
  if (!$('#hardness_graph').html()===''){
    // check if chart has data, if no data, the following function will throw error
    Plotly.relayout('hardness_graph', update);
    Plotly.relayout('event_graph', update);
  }

  Plotly.relayout('hardness_graph', update);
  Plotly.relayout('event_graph', update);

}

function genrateBatchHistory(batchRecords){

  $('#batchHistoryTable').DataTable().destroy();
  
  var my_columns = [
    {data: 'Project_Name'},
    {data: 'Batch_Name'},
    {data: 'Creation_Date'},
    {data: 'Note'},
    {data: 'Last_seq_name'}
  ];

$('#batchHistoryTable').DataTable({
    select: true,
    data: batchRecords,
    columns: my_columns,
    deferRender:    true,
    scrollX: true,
    scrollY:        400,
    scrollCollapse: true,
    scroller:       true,
  }).draw();

  $('#batchHistoryTable tbody').on( 'click', 'tr', function () {
    
  } );

}



// **************************************
// generate gauge functions
// **************************************
function generateGauge(locationID, refvalue=23, min=-40, max=200, titleText='Temperature'){
    var data = [
      {
        type: "indicator",
        mode: "gauge+number+delta",
        value: 0,
        title: { text: titleText, font: { size: 12 } },
        delta: { reference: refvalue, increasing: { color: "green" }, decreasing: { color: "red" } },
        gauge: {
          axis: { range: [min, max], tickwidth: 1, tickcolor: "darkblue" },
          bar: { color: "darkgreen"},
          bgcolor: "lightgreen",
          borderwidth: 0,
          bordercolor: "lightgreen",
          steps: [
            { range: [min, refvalue], color: "limegreen" },
            { range: [refvalue, max], color: "lightgreen" }
          ],
          threshold: {
            line: { color: "red", width: 5 },
            thickness: 0.8,
            value: refvalue+Math.random()*0.001+0.0001
          }
        }
      }
    ];
    
    var layout = {
      width: 200,
      height: 150,
      margin: { t: 20, r: 25, l: 25, b: 0 },
      paper_bgcolor: "transparent",
      font: { color: "dimgray", family: "Arial", size: 10}
    };
  
    Plotly.newPlot(locationID, data, layout,{
      displaylogo: false,
      modeBarButtonsToRemove: ['toImage','lasso','select'],
      responsive: true
    });
  }

function updateValue(locationID, val){
  var data_update = 
      {
        value: val,
      }

      Plotly.update(locationID, data_update);
}

function updateGaugeRefValue(locationID, refvalue, selection='t'){
  let minRange = -40;
  let maxRange = 200;
  if (selection=='h'){
    minRange = 0;
    maxRange = 100;
  }
  var data_update = 
      {
        delta: { reference: refvalue, increasing: { color: "green" }, decreasing: { color: "red" } },
        gauge: {
          axis: { range: [minRange, maxRange], tickwidth: 1, tickcolor: "darkblue" },
          bar: { color: "darkgreen"},
          bgcolor: "lightgreen",
          borderwidth: 0,
          bordercolor: "lightgreen",
          steps: [
            { range: [minRange, refvalue], color: "limegreen" },
            { range: [refvalue, maxRange], color: "lightgreen" }
          ],
          threshold: {
            line: { color: "red", width: 5 },
            thickness: 0.8,
            value: refvalue+Math.random()*0.001+0.0001,
          }
        }
      }

      Plotly.restyle(locationID, data_update);
}

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
    console.log('websocket in run connected')
    ws.send(tools.parseCmd('hello'))
    init();
  });

  ws.on('ping',()=>{
    ws.send(tools.parseCmd('pong','from run'));
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
        case 'reply_init_hw':
          if(data.resp_code==1){
            monitorValue = setInterval(monitorFunction,1000);
            startBtn_disable();
            stopBtn_disable();
            batchInfo_disable();
            batchSelector_enable();
          }else{
            ipcRenderer.send('show-alert-alert','Alert',data.res + '\n' + data.reason);
          }
          break;
        case 'update_sequence':
          updateSequence(data)
          break;
        case 'update_sys_default_config':
          updateServerSeqFolder(data);
          break;
        case 'update_cur_status':
          updateValue('actualTempGauge', data.temp);
          updateValue('actualHumGauge', data.hum);
          break;
        case 'update_step_result':
          // console.log(data)
          updateSingleStep(data);
          break;
        case 'update_cursor':
          console.log(data);
          break;
        case 'update_gauge_ref':
          updateGaugeRefValue('actualTempGauge', data,'t');
          break;
        case 'show_move_sample_dialog':
          showMovingSampleDialog(data);
          break;
        case 'reply_query_batch_history':
          genrateBatchHistory(data);
          break;
        case 'reply_create_batch':
          if (data.resp_code == 1){
            // confirmed batch
            batch_confirmed();
          }else if (data.resp_code == 0){
            ipcRenderer.send('show-option-dialog', 'Batch Existed!', data.reason, 'continue-batch');            
          }
          break;
        case 'end_of_test':
          console.log('end of test')
          endOfTest(data)
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

// **************************************
// event functions
// **************************************

batchForm.addEventListener('submit',(e)=>{
  e.preventDefault();
  let batchinfo = getBatchInfo();
  let seqName = $('#batchInfoForm input[name=SeqName]').val();
  let proj = batchinfo.filter(item=>item.name=='Project')[0].value;
  let batch = batchinfo.filter(item=>item.name=='Batch')[0].value;
  let numSample = batchinfo.filter(item=>item.name=='NumberOfSample')[0].value;
  let note = batchinfo.filter(item=>item.name=='Note')[0].value;
  batchinfo = {'project':proj, 'batch':batch, 'notes':note, 'seq_name':seqName, 'numSample':numSample}
  console.log(batchinfo)
  ws.send(tools.parseCmd('create_batch',batchinfo));
})

batchNew.addEventListener('click', ()=>{

  $(seqNameInForm).val('');
  $(projInForm).val('');
  $(batchInForm).val('');
  $(numsampleInForm).val(1);
  $(noteInForm).val('');

  batchInfo_enable();
})

batchLoad.addEventListener('click', ()=>{
  showBatchSelectDialog();
  batchContent_disable();
  batchConfirmBtn_enable();
})

selectHistoryBatch.addEventListener('click', ()=>{
  selectedHistoryBatch();
})

loadSeqBtn.addEventListener('click', ()=>{
    loadSeqFromServer();
})

ipcRenderer.on('load-seq-run', (event, path) => {

  $('#batchInfoForm input[name=SeqName]').val(path)

  ws.send(tools.parseCmd('run_cmd',tools.parseCmd('load_seq',{path: path})));

});

ipcRenderer.on('continue-batch', (event, resp)=>{
  if (resp == 0){
    let batchinfo = getBatchInfo();
    let seqName = $('#batchInfoForm input[name=SeqName]').val();
    let proj = batchinfo.filter(item=>item.name=='Project')[0].value;
    let batch = batchinfo.filter(item=>item.name=='Batch')[0].value;
    let numSample = batchinfo.filter(item=>item.name=='NumberOfSample')[0].value;
    let note = batchinfo.filter(item=>item.name=='Note')[0].value;
    batchinfo = {'project':proj, 'batch':batch, 'notes':note, 'seq_name':seqName, 'numSample':numSample}
    ws.send(tools.parseCmd('continue_batch',batchinfo));
    batch_confirmed();
  }
  
})

$( window ).resize(function() {
  repositionChart();
});

startSeqBtn.addEventListener('click',()=>{
  startBtn_disable();
  stopBtn_enable();
  $('#testSeqContainer li').css('background-color', 'white');
  clearInterval(monitorValue);
  getBatchInfo();
  generateEventPlot();
  generateHardnessPlot();
  repositionChart();
  markers=[];
  ws.send(tools.parseCmd('run_seq',''));
})

stopSeqBtn.addEventListener('click',()=>{
  ws.send(tools.parseCmd('stop_seq',''));
  startBtn_enable();
  stopBtn_disable();
})

// **************************************
// general functions
// **************************************

let monitorValue;

function init(){
  ws.send(tools.parseCmd('run_cmd',tools.parseCmd('get_default_seq_path')));
  ws.send(tools.parseCmd('init_hw'));
}

function batchSelector_enable(){
  $(batchNew).removeClass('btnEnable btnDisable').addClass('btnEnable');
  $(batchLoad).removeClass('btnEnable btnDisable').addClass('btnEnable');
}

function batchSelector_disable(){
  $(batchNew).removeClass('btnEnable btnDisable').addClass('btnDisable');
  $(batchLoad).removeClass('btnEnable btnDisable').addClass('btnDisable');
}

function batchInfo_enable(){
  batchContent_enable();
  batchConfirmBtn_enable();
}

function batchInfo_disable(){
  batchContent_disable();
  batchConfirmBtn_disable();
}

function batchContent_enable(){
  $(batchFormContent).removeClass('btnEnable btnDisable').addClass('btnEnable');
  $(seqNameInForm).removeClass('btnEnable btnDisable').addClass('btnEnable');
  $(projInForm).removeClass('btnEnable btnDisable').addClass('btnEnable');
  $(batchInForm).removeClass('btnEnable btnDisable').addClass('btnEnable');
  $(numsampleInForm).removeClass('btnEnable btnDisable').addClass('btnEnable');
  $(noteInForm).removeClass('btnEnable btnDisable').addClass('btnEnable');
}

function batchContent_disable(){
  $(seqNameInForm).removeClass('btnEnable btnDisable').addClass('btnDisable');
  $(projInForm).removeClass('btnEnable btnDisable').addClass('btnDisable');
  $(batchInForm).removeClass('btnEnable btnDisable').addClass('btnDisable');
  $(numsampleInForm).removeClass('btnEnable btnDisable').addClass('btnEnable');
  $(noteInForm).removeClass('btnEnable btnDisable').addClass('btnEnable');
}

function batchConfirmBtn_enable(){
  $(batchConfirmBtn).removeClass('btnEnable btnDisable').addClass('btnEnable');
}

function batchConfirmBtn_disable(){
  $(batchConfirmBtn).removeClass('btnEnable btnDisable').addClass('btnDisable');
}

function startBtn_disable(){
  $(startSeqBtn).removeClass('btnEnable btnDisable').addClass('btnDisable');
}

function startBtn_enable(){
  $(startSeqBtn).removeClass('btnEnable btnDisable').addClass('btnEnable');
}

function stopBtn_disable(){
  $(stopSeqBtn).removeClass('btnEnable btnDisable').addClass('btnDisable');
}

function stopBtn_enable(){
  $(stopSeqBtn).removeClass('btnEnable btnDisable').addClass('btnEnable');
}

function updateServerSeqFolder(path){
  defaultSeqPath = path;
}

function loadSeqFromServer(){
  ipcRenderer.send('open-file-dialog',defaultSeqPath,'load-seq-run')
};

function monitorFunction(){
  ws.send(tools.parseCmd('run_cmd',tools.parseCmd('get_cur_temp_and_humi')));
}

function updateSequence(res){
  test_flow.setup = res.setup;
  test_flow.main = res.main;
  seq = res.main
  test_flow.loop = res.loop;
  test_flow.teardown = res.teardown;
  sortSeq();
}

function getBatchInfo(){
  let batchData = $('#batchInfoForm').serializeArray();
  console.log(batchData)
  return batchData;
}

function selectedHistoryBatch(){
  let table = $('#batchHistoryTable').DataTable();
  let isSelected = table.rows( '.selected' ).any();
  if (isSelected){
    let selectedData = table.row( '.selected' ).data();
    $(seqNameInForm).val(selectedData.Last_seq_name);
    $(projInForm).val(selectedData.Project_Name);
    $(batchInForm).val(selectedData.Batch_Name);
    $(noteInForm).val(selectedData.Note);
    let dialog = document.getElementById('modal_batch_select_dialog');
    dialog.style.display='none';
    ws.send(tools.parseCmd('run_cmd',tools.parseCmd('load_seq',{path: selectedData.Last_seq_name})));
  }else{
    ipcRenderer.send('show-info-alert','Please Select Batch','Please select at least one batch');
  }
  
}

function batch_confirmed(){
  startBtn_enable();
  batchInfo_disable();
  batchSelector_disable();
}

function updateSingleStep(res){
  let stepid = res.stepid;
  let stepname = res.name;
  let value = res.value;
  let unit = res.unit;
  let result = res.status;
  let timestamp = res.timestamp;
  let actTemp = res.actTemp;

  let curstep = $('#testSeqContainer').find(`[data-stepid='${stepid}']`);
  let curResult = $(curstep).find('.stepResult');
  curResult.html(value + unit)
  if (result == 'PASS'){
    updateStepByCat(res);
    curstep.css('background-color', 'lightgreen');
  }else if (result == 'WAITING'){
    updateStepByCat(res);
    curstep.css('background-color', 'orange');
  }else if (result == 'PAUSE'){
    curstep.css('background-color', 'yellow');
  }else if (result == 'SKIP'){
    updateStepByCat(res);
    curstep.css('background-color', 'gray');
  }else if (result == 'MEAR_NEXT'){
    updateStepByCat(res);
    curstep.css('background-color', 'orange');
  }else{
    updateStepByCat(res);
    curstep.css('background-color', 'red');
  }
  
}

function updateStepByCat(res){
  let stepid = res.stepid;
  let stepname = res.name;
  let value = res.value;
  let result = res.status;
  let relTime = res.relTime;
  let actTemp = res.actTemp;
  let eventName = res.eventName;

  switch(stepname) {
    case 'ramp':
      updateValue('actualTempGauge', value);
      tools.plotly_addNewDataToPlot('event_graph',relTime,actTemp)
      break;
    case 'measure':
      // h_data_y.push(value)
      if (result == 'PASS'){
        tools.plotly_addNewDataToPlot('hardness_graph',actTemp,value)
        tools.plotly_addNewDataToPlot('event_graph',relTime,actTemp,value)
      }else if (result == 'MEAR_NEXT'){
        tools.plotly_addNewDataToPlot('hardness_graph',actTemp,value)
        tools.plotly_addNewDataToPlot('event_graph',relTime,actTemp,value)
      }   
      if (eventName !== null){
        // tools.plotly_addAnnotation('event_graph',eventName,relTime,actTemp,markers)
      }
      // updateValue('hardness_graph', value);
      break;
    case 'time':      
      tools.plotly_addNewDataToPlot('event_graph',relTime,actTemp)
      break;
    default:
      console.log('Not found this stepname: ' + stepname)
      break;
  }

}

function listDataset(data){
  let liComponent = `
    <thead>
    <tr class="w3-black">
      <th>No.</th>
      <th>Value</th>
    </tr>
    </thead>
  `;
  data.forEach((item,index)=>{
    liComponent += `
    <tr>
      <td>${index+1}</td>
      <td>${item}</td>
    </tr>
    `
  })
  return liComponent
}

function showBatchSelectDialog(){
  ws.send(tools.parseCmd('query_batch_history'));
  let dialog = document.getElementById('modal_batch_select_dialog');
  dialog.style.display='block';
}

function showMovingSampleDialog(data){
  let dialog = document.getElementById('modal_moving_sample_dialog');
  let dialog_text = document.getElementById('modal_moving_sample_dialog_text');
  let dialog_dataset_list = document.getElementById('modal_moving_sample_dialog_dataset');
  let dialog_dataset_id = document.getElementById('dataset_sampleid');
  let dialog_dataset_counter = document.getElementById('dataset_counter');
  let dialog_dataset_mean = document.getElementById('dataset_mean');
  let dialog_dataset_stdev = document.getElementById('dataset_stdev');
  let start_btn = document.getElementById('start_mear_after_move_sample');
  let retry_btn = document.getElementById('retry_mear_after_move_sample');
  let curData = data;

  dialog_dataset_id.innerHTML = `Sample ID: ${curData.sampleid}`
  dialog_dataset_counter.innerHTML = `Measured Data (${curData.dataset.length} / ${curData.totalCounts})`
  dialog_dataset_list.innerHTML = listDataset(curData.dataset);
  dialog_dataset_mean.innerHTML = `${curData.method}: ${curData.result}`;
  dialog_dataset_stdev.innerHTML = `stdev: ${curData.std}`
  dialog_text.innerHTML = `
  <h3>Press <strong>Retry</strong> if last value is not acceptable!</h3>
  <h3>Press <strong>Next</strong> to mearsure at next position!</h3>
  `;

  dialog.style.display='block';

  start_btn.addEventListener('click',()=>{
    start_mear_after_move_sample();
  })
  retry_btn.addEventListener('click',()=>{
    start_mear_after_move_sample(true);
  })
}

function start_mear_after_move_sample(isRetry=false){
  let dialog = document.getElementById('modal_moving_sample_dialog');
  dialog.style.display='none';
  ws.send(tools.parseCmd('continue_seq',isRetry));
}

function endOfTest(res){
  let interrupted = res.interrupted;
  let reason = res.reason;
  clearInterval(monitorValue);
  console.log(reason);
  monitorValue = setInterval(monitorFunction,1000);
  startBtn_disable();
  stopBtn_disable();
  batchInfo_disable();
  batchSelector_enable();
  if (!interrupted){
    ipcRenderer.send('show-info-alert','Test Finished',reason);
  }else{
    ipcRenderer.send('show-warning-alert','Test Interrupted',reason);
  }
}

// **************************************
// Sequence render functions
// **************************************

function sortSeq(){
  let middleSeqs =  generateSeq();
  $('#testSeqContainer').html(generateStartSeq() + middleSeqs + generateEndSeq());
  test_flow.main = seq;
  let revSeq = seq.slice();
  revSeq.reverse().forEach((item,index)=>{
    if(item.cat==='loop' && item.subitem['item']=='loop end'){
        let loopid = item.subitem.paras.filter(item=>item.name=='loop id')[0].value;
        let ids = searchLoopStartEndByID(loopid);
        genLoopIndicator(ids[0],ids[1]);
    }
    
  })
}

function genUnit(unit) {
  if (unit === '' || unit === null) {
      return '';
  }else{
      return '(' + unit + ')';
  }
}

function genParas (paras,input=false) {
  let c = '';
  paras.forEach(function(item, index, array){
      if (input) {
          let t = item['type'];
          let ronly = item['readOnly']?'disabled':'';
          if (t === 'text'){
              c += `<li><label>${tools.capitalize(item['name'])} ${genUnit(item['unit'])}</label> <input class='w3-input w3-border-bottom w3-cell' value='${item['value']}' type='text' ${ronly}></li>`;
          }else if (t === 'number'){
              c += `<li><label>${tools.capitalize(item['name'])} ${genUnit(item['unit'])}</label> <input class='w3-input w3-border-bottom w3-cell' value='${item['value']}' type='number' ${ronly}></li>`;

          }else if (t === 'bool'){
              c += `<li><input class='w3-check w3-border-bottom w3-cell' checked=${item['value']} type='checkbox' ${ronly}><label> ${tools.capitalize(item['name'])} ${genUnit(item['unit'])}
              </label></li>`;
              
          }else if (t === 'select'){
              let op = item['options'];
              let selectedOP = item['value']
              let ops = op.split(',');
              let opItems = '';
              ops.forEach((item)=>{
                  if(selectedOP==item){
                      opItems += `<option value="${item}" ${ronly} selected>${item}</option>`;
                  }else{
                      opItems += `<option value="${item}" ${ronly}>${item}</option>`;
                  }
                  
              })
              c += `<li><label>${tools.capitalize(item['name'])} ${genUnit(item['unit'])}</label> 
              <select class="w3-select w3-border" name="option">${opItems}</select></li>`;
          }
      }else{
          c += `<li style='font-size:12px;'><label><b>${tools.capitalize(item['name'])} ${genUnit(item['unit'])}</b></label>: ${item['value']}</li>`;
      }
    
  });
  return c;
}

function genIconByCat(cat,paras=null){
  let iconset = '';
  let loopColor = '';
  if (cat === 'temperature'){
      iconset = 'fas fa-thermometer-quarter';
  }else if (cat === 'hardness'){
      iconset = 'fas fa-download';
  }else if (cat === 'waiting'){
      iconset = 'fas fa-hourglass-start';
  }else if (cat === 'loop'){
      loopColor = paras.filter(item=>item.name=='loop color')[0].value;
      iconset = 'fas fa-retweet';
  }else if (cat === 'subprog'){
      iconset = 'fas fa-indent';
  }
  return `<i class="${iconset} w3-margin-right fa-lg w3-center" style='width:20px;color:${loopColor}'></i>`
}


function genShortParaText(cat,subitem){
  let {item, paras} = subitem;
  let mainText = '';
  
  if (cat === 'temperature'){
      let tTempPara = paras.filter(item=>item.name=='target temperature')[0];
      let slopePara = paras.filter(item=>item.name=='slope')[0];
      let increPara = paras.filter(item=>item.name=='increment')[0];
      mainText = `target:${tTempPara.value} ${tTempPara.unit}, slope:${slopePara.value} ${slopePara.unit}, 
      incre:${increPara.value} ${increPara.unit}`;
  }else if (cat === 'hardness'){
      let methodPara = paras.filter(item=>item.name=='method')[0];
      let modePara = paras.filter(item=>item.name=='mode')[0];
      let mtPara = paras.filter(item=>item.name=='measuring time')[0];
      let nomearPara = paras.filter(item=>item.name=='number of measurement')[0];
      let nummethodPara = paras.filter(item=>item.name=='numerical method')[0];
      mainText = `${methodPara.value}, ${modePara.value}, mearTime:${mtPara.value} ${mtPara.unit}, mearCounts:${nomearPara.value}, ${nummethodPara.value} `;
  }else if (cat === 'waiting'){
      let cdtPara = paras.filter(item=>item.name=='conditioning time')[0];
      mainText = `conditioningTime:${cdtPara.value} ${cdtPara.unit}`;
  }else if (cat === 'loop'){
      if(item=='loop start'){
          let loopPara = paras.filter(item=>item.name=='loop id')[0];
          let loopCountPara = paras.filter(item=>item.name=='loop counts')[0];
          mainText = `Loop START, id:${loopPara.value}, counts:${loopCountPara.value}`;
      }else{
          let loopPara = paras.filter(item=>item.name=='loop id')[0];
          let loopStop = paras.filter(item=>item.name=='stop on')[0];
          mainText = `Loop END, id:${loopPara.value}, stop on: loopCount=${loopStop.value}`;
      }
  }else if (cat === 'subprog'){
      let pathPara = paras.filter(item=>item.name=='path')[0];
      mainText = `path:${pathPara.value}`;
  }
  return `<div class="paraText">${mainText}</div>`
}

function genStepTitles(){
  let titles = [];
  for (i = 0; i < seq.length; i++) {
      let {cat, subitem} = seq[i];
      let parms = genParas(subitem['paras']);
      let en = subitem['enabled'];
      // titles.push(`Step ${i+1} :: ${tools.capitalize(cat)} :: ${tools.capitalize(subitem['item'])}`);
      titles.push(`Step ${i+1} :: ${tools.capitalize(cat)}`);
  }

  return titles;
}

function generateSeq() {
  let stepTitles = genStepTitles();
  let curstr = '';
  seq.forEach((item,index)=>{
      seq[index].id = index;
      let {cat, subitem} = seq[index];
      let parms = genParas(subitem['paras']);
      let en = subitem['enabled']?'':'disabledStep';
      let stepParaText = genShortParaText(cat,subitem);
      curstr += `
      <li data-stepid=${index} data-sortable=true ${en}' >
          <div class='w3-bar'>
              <a href="#" class='w3-bar-item stepParas'>
                  ${genIconByCat(cat,subitem['paras'])}${stepTitles[index]}${stepParaText}
              </a>
              <div class="w3-bar-item w3-right lopCount">00</div>
              <div class="w3-bar-item w3-right stepResult"></div>
          </div>              
      </li>
      
      `;
  });
  return curstr;
}

function generateStartSeq() {
  test_flow.setup = setup_seq;
  let curstr = `
  <li data-stepid=-1>
    <div class='w3-bar'>
      <a href="#" class='w3-bar-item'><i class="far fa-play-circle w3-margin-right fa-lg"></i>Sequence Setup</a>
    </div> 
  </li>
  `;
  return curstr;
}

function generateEndSeq() {
  test_flow.teardown = teardown_seq;
  let curstr = `
  <li data-stepid=9999>
    <div class='w3-bar'>
      <a href="#" class='w3-bar-item'><i class="far fa-stop-circle w3-margin-right fa-lg"></i>Sequence Teardown</a>
    </div>
  </li>
  `;
  return curstr;
}

function genLoopIndicator(start, end){
  if(start<0 || end<0){
      return null;
  }
  let liItem = $('#testSeqContainer li');
  // ignore settup step
  start+=1;
  end+=1;
  // $('.lopCount').removeClass('lopCount-enabled');
  // liItem.removeClass('loop loopStart loopEnd');
  liItem.each((index,item)=>{
      let loopCount = seq[start-1].subitem['paras'].filter(item=>item.name=='loop counts')[0].value;
      let loopColor = seq[start-1].subitem['paras'].filter(item=>item.name=='loop color')[0].value;
      if(index==start){
          $(item).addClass('loop loopStart');
          $(item).find('.lopCount').addClass('lopCount-start-enabled').html(loopCount).css("cssText","border-color:"+loopColor + ' !important');
          $(item).css("cssText","box-shadow: 2px 0px 0px 0px "+ loopColor + ' !important');
      }else if (index > start && index < end){
          $(item).addClass('loop');
          $(item).css("cssText","box-shadow: 2px 0px 0px 0px "+ loopColor + ' !important');
      }else if (index===end){
          loopCount = seq[start-1].subitem['paras'].filter(item=>item.name=='loop counts')[0].value;
          loopColor = seq[start-1].subitem['paras'].filter(item=>item.name=='loop color')[0].value;
          $(item).addClass('loop loopEnd');
          $(item).find('.lopCount').addClass('lopCount-enabled').html(loopCount).css("background-color",loopColor);
          $(item).css("cssText","box-shadow: 2px 0px 0px 0px "+ loopColor + ' !important');
      }else{
          
      }
      
      
  })
  
}

function searchLoopStartEndByID(loopid, dummyseq=null){
  if(dummyseq==null){
      dummyseq = seq.slice();
  }
  let loopStartID=loopid;
  let loopEndID=loopid;
  dummyseq.forEach((item,index)=>{
      if(item.cat=='loop' && item.subitem.item=='loop start'){
          if(item.subitem.paras.filter(item=>item.name=='loop id')[0].value==loopid){
              loopStartID=index;
          }
      }else if(item.cat=='loop' && item.subitem.item=='loop end'){
          if(item.subitem.paras.filter(item=>item.name=='loop id')[0].value==loopid){
              loopEndID=index;
          }
      }
  })
  return [loopStartID,loopEndID]
}