const {ipcRenderer} = require("electron");
let tools = require('../assets/shared_tools');
let seqRend = require('../assets/seq_render_lib');
let ws

// **************************************
// variable define
// **************************************

let defaultSeqPath = null;
let batchForm = document.getElementById('batchInfoForm');
let sampleBatchConfigForm  = document.getElementById('sampleBatchConfigForm');
let batchNew = document.getElementById('new_a_batch');
let batchLoad  = document.getElementById('load_a_batch');
let seqNameInFormInput = document.querySelectorAll("#sampleBatchConfigForm > input[name='SeqName']")[0]
let noteInForm = document.querySelectorAll("#sampleBatchConfigForm > textarea[name='Note']")[0]
let selectHistoryBatch = document.getElementById('SelectBatch');
let openSampleSetupListBtn = document.getElementById('openSampleSetupList');
let sampleSetup = document.getElementById('sampleSetupList');
let sampleSetupDialog = document.getElementById('modal_batch_setup_dialog');
let batchConfirmAndStartBtn = document.getElementById('batchConfirmAndStart');
let stopSeqBtn = document.getElementById('stop_test');
let loadSeqBtn = document.getElementById('open_test_seq');
let dialog = document.getElementById('modal_moving_sample_dialog');
let dialog_dataset_list = document.getElementById('modal_moving_sample_dialog_dataset');
let dialog_dataset_id = document.getElementById('dataset_sampleid');
let dialog_dataset_counter = document.getElementById('dataset_counter');
let dialog_dataset_mean = document.getElementById('dataset_mean');
let dialog_dataset_stdev = document.getElementById('dataset_stdev');
let start_btn = document.getElementById('start_mear_after_move_sample');
let retry_btn = document.getElementById('retry_mear_after_move_sample');
let setup_seq = {};
let teardown_seq = {};
let loop_seq = [];
let test_flow = {
    setup: setup_seq,
    main: [],
    loop: loop_seq,
    teardown: teardown_seq
};
let loadSeqPathObj = {path:'', name:''};
const plotMargin = { t: 40, r: 80, l: 40, b: 50};
const config = {
  displaylogo: false,
  modeBarButtonsToRemove: ['toImage','lasso2d','select2d', 'pan2d','zoom2d','hoverClosestCartesian','hoverCompareCartesian','toggleSpikelines'],
  responsive: false
};
let enableKeyDetect = false;

const run_status_classes = 'run-init run-pass run-wait run-skip run-next run-fail run-pause'

let machine_hard_idct = document.querySelectorAll('#machine_hard_idct .idct-number')[0]
let machine_temp_idct = document.querySelectorAll('#machine_tempr_idct .idct-number')[0]
let machine_humi_idct = document.querySelectorAll('#machine_hum_idct  .idct-number')[0]

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

function genTraceForHardnessPlot(sampleSize=1){
  const sampleArr = Array(sampleSize);
  const traceArr = sampleArr.map((elm,idx)=>{
    return {
      x: [],
      y: [],
      mode: 'lines+markers',
      type: 'scatter',
      name: `sample${idx+1}`,
      marker: { size: 6},
      line: {
        width: 2
      }
    }
  })
  return traceArr;
}


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
  
    // let batchinfo = getBatchInfo();
    // let numSample = batchinfo.filter(item=>item.name=='NumberOfSample')[0].value;
    // const traceArr = genTraceForHardnessPlot(numSample)
  
    // var data = traceArr;
    
    // var layout = {
    //   xaxis: {
    //     title: '℃'
    //   },
    //   yaxis: {
    //     title: 'hardness',
    //     range: [0, 100]
    //   },
    //   width: 400,
    //   height: 250,
    //   margin: plotMargin,
    //   autosize: false,
    //   font: { color: "dimgray", family: "Arial", size: 10}
    // };
    
    // Plotly.newPlot('hardness_graph', data, layout, config);
  }

  
function repositionChart(){
  // var update = {
  //   autosize: true,
  // };
  // if (!$('#hardness_graph').html()===''){
  //   // check if chart has data, if no data, the following function will throw error
  //   Plotly.relayout('hardness_graph', update);
  //   Plotly.relayout('event_graph', update);
  // }

  // Plotly.relayout('hardness_graph', update);
  // Plotly.relayout('event_graph', update);

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
  let maxRange = 190;
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
          break;
        case 'reply_init_hw':
          if(data.resp_code==1){
            batchSelector_enable();
          }else{
            ipcRenderer.send('show-alert-alert',window.lang_data.modal_alert_title,data.res + '\n' + data.reason);
          }
          break;
        case 'update_sequence':
          updateSequence(data)
          break;
        case 'update_sys_default_config':
          updateServerSeqFolder(data);
          break;
        case 'update_cur_status':
          // updateValue('actualTempGauge', data.temp);
          // updateValue('actualHumGauge', data.hum);
          break;
        case 'update_step_result':
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
            ipcRenderer.send('show-info-alert',data.title, data.reason);
            batch_confirmed();
          }else if (data.resp_code == 0){
            let args = {batchName:data.batchName}
            ipcRenderer.send('show-option-dialog', data.title, data.reason, 'continue-batch', args);            
          }
          break;
        case 'only_update_hardness_indicator':
          machine_hard_idct.innerText = data;
          break;
        case 'end_of_test':
          endOfTest(data)
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

// **************************************
// event functions
// **************************************

batchNew.addEventListener('click', ()=>{
  $("#sampleBatchConfigForm input[name!='NumberOfSample'],textarea").each((i,elm)=>{
    elm.value = ''
  })
  batchInfo_enable();
})
batchLoad.addEventListener('click', ()=>{
  showBatchSelectDialog();
  batchContent_disable();
  batchConfirmAndStartBtn_enable();
})
selectHistoryBatch.addEventListener('click', ()=>{
  selectedHistoryBatch();
})
loadSeqBtn.addEventListener('click', ()=>{
  loadSeqFromServer();
})

$('#setupBatchModal').on('click', ()=>enableKeyDetect = false);

openSampleSetupListBtn.addEventListener('click', ()=>{
  sampleSetupDialog.style.display='block';
  initCirclePlot();
  enableKeyDetect = true;
})
ipcRenderer.on('load-seq-run', (event, path) => {
  updateLoadedPathObj(path)
  $("#sampleBatchConfigForm input[name='SeqName']").val(loadSeqPathObj.name)
  ws.send(tools.parseCmd('run_cmd',tools.parseCmd('load_seq',{path: path})));
});
ipcRenderer.on('continue-batch', (event, resp, args)=>{
  if (resp == 0){
    let batchName = args.batchName;
    const targetBatch = batches.find(elm=>{return elm.batch===batchName})
    ws.send(tools.parseCmd('continue_batch',[targetBatch]));
  }
})

$( window ).resize(function() {
  repositionChart();
});

stopSeqBtn.addEventListener('click',()=>{
  ws.send(tools.parseCmd('stop_seq',''));
})

// **************************************
// general functions
// **************************************

function init(){
  ws.send(tools.parseCmd('run_cmd',tools.parseCmd('get_default_seq_path')));
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
  batchConfirmAndStartBtn_enable();
}

function batchInfo_disable(){
  batchContent_disable();
  batchConfirmAndStartBtn_disable();
}

function batchContent_enable(){
  $(sampleBatchConfigForm).removeClass('btnEnable btnDisable').addClass('btnEnable');
  $(seqNameInFormInput).removeClass('btnEnable btnDisable').addClass('btnEnable');
  $(loadSeqBtn).removeClass('btnEnable btnDisable').addClass('btnEnable');
  $(noteInForm).removeClass('btnEnable btnDisable').addClass('btnEnable');
}

function batchContent_disable(){
  $(seqNameInFormInput).removeClass('btnEnable btnDisable').addClass('btnDisable');
  $(loadSeqBtn).removeClass('btnEnable btnDisable').addClass('btnDisable');
  $(noteInForm).removeClass('btnEnable btnDisable').addClass('btnEnable');
}

function batchConfirmAndStartBtn_enable(){
  $(batchConfirmAndStartBtn).removeClass('btnEnable btnDisable').addClass('btnEnable');
}

function batchConfirmAndStartBtn_disable(){
  $(batchConfirmAndStartBtn).removeClass('btnEnable btnDisable').addClass('btnDisable');
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

function updateSequence(res){
  test_flow.setup = res.setup;
  test_flow.main = res.main;
  test_flow.loop = res.loop;
  test_flow.teardown = res.teardown;
  seqRend.sortSeq('testSeqContainer', test_flow.setup, test_flow.main, test_flow.teardown);
}

function getBatchInfo(){
  let batchData = $('#sampleBatchConfigForm').serializeArray();
  return batchData;
}

function selectedHistoryBatch(){
  let table = $('#batchHistoryTable').DataTable();
  let isSelected = table.rows( '.selected' ).any();
  const projInput = $("#sampleBatchConfigForm input[name='Project']")[0];
  const batchjInput = $("#sampleBatchConfigForm input[name='Batch']")[0];
  if (isSelected){
    let selectedData = table.row( '.selected' ).data();
    console.log(selectedData)
    updateLoadedPathObj(selectedData.Last_seq_name)
    $(seqNameInFormInput).val(loadSeqPathObj.name)
    $(projInput).val(selectedData.Project_Name)
    $(batchjInput).val(selectedData.Batch_Name)
    $(noteInForm).val(selectedData.Note);
    let dialog = document.getElementById('modal_batch_select_dialog');
    dialog.style.display='none';
    ws.send(tools.parseCmd('run_cmd',tools.parseCmd('load_seq',{path: selectedData.Last_seq_name})));
  }else{
    ipcRenderer.send('show-info-alert',window.lang_data.modal_info_title, window.lang_data.please_select_one_batch);
  }
  
}

function immediate_start_test(){
  // start test
  batchConfirmAndStartBtn_disable();
  stopBtn_enable();
  $('#testSeqContainer li').removeClass(run_status_classes).addClass('run-init');
  getBatchInfo();
  generateEventPlot();
  generateHardnessPlot();
  repositionChart();
  markers=[];
  ws.send(tools.parseCmd('run_seq',''));
}

function updateSingleStep(res){
  let stepid = res.stepid;
  let stepname = res.name;
  let value = res.value;
  let unit = res.unit;
  let result = res.status;
  let timestamp = res.timestamp;
  let actTemp = res.actTemp;
  let actHumi = res.actHum;

  let curstep = $('#testSeqContainer').find(`[data-stepid='${stepid}']`);
  let curResult = $(curstep).find('.stepResult');
  // update actTemp
  tools.updateNumIndicator(machine_temp_idct,actTemp,1)
  tools.updateNumIndicator(machine_humi_idct,actHumi,1)
  
  // update value in step
  curResult.html(value + unit)
  curstep.removeClass(run_status_classes)
  if (result == 'PASS'){
    updateStepByCat(res);
    curstep.addClass('run-pass');
  }else if (result == 'WAITING'){
    updateStepByCat(res);
    curstep.addClass('run-wait');
  }else if (result == 'PAUSE'){
    curstep.addClass('run-pause');
  }else if (result == 'SKIP'){
    updateStepByCat(res);
    curstep.addClass('run-skip');
  }else if (result == 'MEAR_NEXT'){
    updateStepByCat(res);
    curstep.addClass('run-next');
  }else{
    updateStepByCat(res);
    curstep.addClass('run-fail');
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
  let progs = res.prograss;

  let curstep = $('#testSeqContainer').find(`[data-stepid='${stepid}']`);
  let curProgs = $(curstep).find('.stepProg');

  switch(stepname) {
    case 'ramp':
      // updateValue('actualTempGauge', value);
      tools.plotly_addNewDataToPlot('event_graph',relTime,actTemp)
      curProgs.val(progs);
      break;
    case 'measure':
      // h_data_y.push(value)
      if (result == 'PASS'){
        curProgs.val(progs);
        tools.updateNumIndicator(machine_hard_idct,value, 1)
        tools.plotly_addNewDataToPlot('hardness_graph',actTemp,value)
        tools.plotly_addNewDataToPlot('event_graph',relTime,actTemp,value)
      }else if (result == 'MEAR_NEXT'){
        curProgs.val(progs);
        tools.updateNumIndicator(machine_hard_idct,value, 1)
        tools.plotly_addNewDataToPlot('hardness_graph',actTemp,value)
        tools.plotly_addNewDataToPlot('event_graph',relTime,actTemp,value)
      }else if (result == 'WAITING'){
        curProgs.val(progs);
      }  
      if (eventName !== null){
        // tools.plotly_addAnnotation('event_graph',eventName,relTime,actTemp,markers)
      }
      // updateValue('hardness_graph', value);
      break;
    case 'time':      
      tools.plotly_addNewDataToPlot('event_graph',relTime,actTemp)
      curProgs.val(progs);
      break;
    
    case 'teardown':
      // updateValue('actualTempGauge', actTemp);
      tools.plotly_addNewDataToPlot('event_graph',relTime,actTemp)
      curProgs.val(progs);
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
  let curData = data;
  dialog_dataset_id.innerHTML = curData.sampleid
  dialog_dataset_counter.innerHTML = `(${curData.dataset.length} / ${curData.totalCounts})`
  dialog_dataset_list.innerHTML = listDataset(curData.dataset);
  dialog_dataset_mean.innerHTML = `${curData.method}: ${curData.result}`;
  dialog_dataset_stdev.innerHTML = `stdev: ${curData.std}`
  dialog.style.display='block';
}

start_btn.addEventListener('click',()=>{
  start_mear_after_move_sample();
})
retry_btn.addEventListener('click',()=>{
  start_mear_after_move_sample(true);
})

function start_mear_after_move_sample(isRetry=false){
  let dialog = document.getElementById('modal_moving_sample_dialog');
  dialog.style.display='none';
  ws.send(tools.parseCmd('continue_seq',isRetry));
}

function endOfTest(res){
  console.log('[end of test]',res)
  let interrupted = res.interrupted;
  let title = res.title;
  let reason = res.reason;
  batchSelector_enable();
  batchContent_enable()
  batchConfirmAndStartBtn_enable();
  stopBtn_disable();
  if (!interrupted){
    ipcRenderer.send('show-info-alert',title,reason);
  }else{
    ipcRenderer.send('show-warning-alert',title,reason);
  }
}

const updateLoadedPathObj = (abspath) => {
  loadSeqPathObj.path = abspath;
  loadSeqPathObj.name = abspath.replace(/^.*[\\\/]/, '')
  return loadSeqPathObj
}

// detect select language
ipcRenderer.on('trigger_tanslate', (event)=>{
  if(test_flow.setup.para !== undefined){
    $('#testSeqContainer').html(seqRend.refreshSeq(test_flow,false))
  }
})


// **************************************
// generate gauge functions
// **************************************
let circles = [];
let batches = [];
let batchCounter = 0
let baseR = 200;
let uutN = 25;
let childR = baseR - 30;
let childTxtR = baseR - 60;
let radius = 15;
const options = {
  "font-size": "1.2rem",
  "style": 'fill: black',
  "text-anchor":"middle",
  "alignment-baseline":"central"
}
const svgns = "http://www.w3.org/2000/svg";
const svgContainer = document.getElementById('sampleCircle');

const createCircle = (container, cx,cy,r, className='', color='white') => {
  let circle = document.createElementNS(svgns, 'circle');
  circle.setAttributeNS(null, 'class', className);
  circle.setAttributeNS(null, 'cx', cx);
  circle.setAttributeNS(null, 'cy', cy);
  circle.setAttributeNS(null, 'r', r);
  circle.setAttributeNS(null, 'style', `fill: ${color}`);
  // circle.setAttributeNS(null, 'style', 'fill: lightyellow; stroke: black; stroke-width: 1px;' );
  container.appendChild(circle);
}

const createText = (container, cx,cy,strTxt='',options={}, className='') => {
  var text = document.createElementNS(svgns, 'text');
  text.setAttributeNS(null, 'class', className);
  text.setAttributeNS(null, 'x', cx);
  text.setAttributeNS(null, 'y', cy);
  Object.keys(options).forEach((elm,idx)=>{
    text.setAttributeNS(null,elm,options[elm])
  })
  let textNode = document.createTextNode(strTxt);
  text.appendChild(textNode);
  container.appendChild(text);
}

function createCirclesInstance(){
  circles = [];
  batches = [];
  for(let i=0; i<uutN; i++) {
    circles.push({id: i, status:'empty', batchInfo:{}, color:'white'});
  }
}

function plotBaseTable(){
  createCircle(svgContainer,'50%','50%',baseR,'baseCircle','#bdc3c7')
}

function plotSmallHoles( circleN = 25){
    let bboxRect = svgContainer.getBBox()
    const newCenterX = bboxRect.x+bboxRect.width/2;
    const newCenterY = bboxRect.y+bboxRect.height/2;

    circles.forEach((elm)=>{
      let theda = elm.id*2*(Math.PI)/circleN;
      let smcx = newCenterX+childR*Math.cos(theda-0.5*Math.PI);
      let smcy = newCenterY+childR*Math.sin(theda+0.5*Math.PI);
      let txtcx = newCenterX+childTxtR*Math.cos(theda-0.5*Math.PI);
      let txtcy = newCenterY+childTxtR*Math.sin(theda+0.5*Math.PI);
      singleCircle = {'cx':smcx, 'cy':smcy, 'radius':radius};
      if(elm.status==='empty'){
        createCircle(svgContainer,smcx,smcy,radius,'uut', 'white')
      }else if (elm.status==='filled'){
        createCircle(svgContainer,smcx,smcy,radius,'uutfilled', elm.color)
      }
      createText(svgContainer,txtcx,txtcy,strTxt=elm.id+1,options,className='textuut')
    })
}

function setCircleOccupy(index=0, batchInfo={}, color='white'){
  let spcCirlce = circles.find(elm=>elm.id===index)
  spcCirlce.status = 'filled'
  spcCirlce.batchInfo = batchInfo
  spcCirlce.color=color
  circles.splice(index,1,spcCirlce)
}

function refreshSeqsInAllSamples(seqPath){
  circles.forEach(elm=>{
    elm.batchInfo.seq_name = seqPath;
  })

}

const initCirclePlot = () => {
  svgContainer.innerHTML=''
  plotBaseTable();
  plotSmallHoles(uutN);
}

createCirclesInstance()

$('#sampleBatchConfigForm').on('submit', (e)=>{
  e.preventDefault();
  let batchinfos = getBatchInfo();
  let seqPath = loadSeqPathObj.path;
  let proj = batchinfos.filter(item=>item.name=='Project')[0].value;
  let batch = batchinfos.filter(item=>item.name=='Batch')[0].value;
  let numSample = batchinfos.filter(item=>item.name=='NumberOfSample')[0].value;
  let note = batchinfos.filter(item=>item.name=='Note')[0].value;
  batchinfo = {'project':proj, 'batch':batch, 'notes':note, 'seq_name':seqPath,'numSample':parseInt(numSample), 'sampleId':0}
  // const randomColor = Math.floor(Math.random()*16777215).toString(16);
  let counter = 0;
  circles.forEach(elm=>{
    if(counter<numSample){
      if(elm.status==='empty'){
        batchinfo.sampleId = counter+1
        setCircleOccupy(elm.id, batchinfo, tools.pick_color_hsl(batchCounter))
        counter += 1
      }
    }
  })
  batches.push(batchinfo)
  batchCounter += 1
  refreshSeqsInAllSamples(seqPath)
  initCirclePlot()
})

confirmSampleBatchConfigBtn.addEventListener('click',()=>{
  ws.send(tools.parseCmd('create_batch',batches));
})

function batch_confirmed(){
  
}

$('#sampleBatchConfigClearAllBtn').on('click', ()=>{
  batchCounter = 0
  createCirclesInstance();
  initCirclePlot();
})

$(document).keydown(function(e){ 
  let code = e.which;
  if (enableKeyDetect){
    if (code == 37){
      // move last
      $('#moveLastBtn').focus();
    }else if (code == 39){
      // move next
      $('#moveNextBtn').focus();
    }else if (code == 38 || code == 40){
      // move home
      $('#moveHomeBtn').focus();
    }else{
  
    }
  }
  
});