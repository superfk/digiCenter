const { ipcRenderer } = require("electron");
let tools = require('../assets/shared_tools');
let seqRend = require('../assets/seq_render_lib');
let ws

// **************************************
// variable define
// **************************************

let defaultSeqPath = null;
let batchForm = document.getElementById('batchInfoForm');
let sampleBatchConfigForm = document.getElementById('sampleBatchConfigForm');
let batchNew = document.getElementById('new_a_batch');
let batchLoad = document.getElementById('load_a_batch');
let seqNameInFormInput = document.querySelectorAll("#sampleBatchConfigForm  input[name='SeqName']")[0]
let noteInForm = document.querySelectorAll("#sampleBatchConfigForm > textarea[name='Note']")[0]
let selectHistoryBatch = document.getElementById('SelectBatch');
let openSampleSetupListBtn = document.getElementById('openSampleSetupList');
let sampleSetup = document.getElementById('sampleSetupList');
let sampleSetupDialog = document.getElementById('modal_batch_setup_dialog');
let sampleBatchListContainer = document.getElementById('sampleBatchListContainer')
let sampleBatchCircleContainer = document.getElementById('sampleBatchCircleContainer')
let batchConfirmAndStartBtn = document.getElementById('batchConfirmAndStart');
let stopSeqBtn = document.getElementById('stop_test');
let loadSeqBtn = document.getElementById('open_test_seq');
const batchViewList = document.getElementById('batchViewList')
let dialog = document.getElementById('modal_moving_sample_dialog');
let dialog_dataset_list = document.getElementById('modal_moving_sample_dialog_dataset');
let dialog_dataset_index = document.getElementById('dataset_sampleIndex');
let dialog_dataset_id = document.getElementById('dataset_sampleid');
let dialog_dataset_counter = document.getElementById('dataset_counter');
let dialog_dataset_mean = document.getElementById('dataset_mean');
let dialog_dataset_stdev = document.getElementById('dataset_stdev');
let start_btn = document.getElementById('start_mear_after_move_sample');
let retry_btn = document.getElementById('retry_mear_after_move_sample');
const statusCircle = document.getElementById('sampleCircleStatus')
let hard_idct_status = document.querySelectorAll('#machine_hard_idct .idct-status')[0]
let temp_idct_status = document.querySelectorAll('#machine_tempr_idct .idct-status')[0]
let humi_idct_status = document.querySelectorAll('#machine_hum_idct  .idct-status')[0]
let batchInfoForSamples = [];
let batches = [];
let batchCounter = 0
let baseR = 250;
let baseRStatus = 140;
let uutN = 25;
let curSampleIndex = 1;
let smallCircleOption = {
  childR: baseR - 30, childTxtR: baseR - 60, radius: 15, textOption: {
    "font-size": "1.2rem",
    "style": 'fill: black',
    "text-anchor": "middle",
    "alignment-baseline": "central"
  }
};
let smallCircleStatusOption = {
  childR: baseRStatus - 25, childTxtR: baseRStatus - 50, radius: 8, textOption: {
    "font-size": "0.8rem",
    "style": 'fill: black',
    "text-anchor": "middle",
    "alignment-baseline": "central"
  }
}

const svgns = "http://www.w3.org/2000/svg";
const svgContainer = document.getElementById('sampleCircle');
let setup_seq = {};
let teardown_seq = {};
let loop_seq = [];
let test_flow = {
  setup: setup_seq,
  main: [],
  loop: loop_seq,
  teardown: teardown_seq
};
let loadSeqPathObj = { path: '', name: '' };
const plotMargin = { t: 80, r: 100, l: 50, b: 60, pad: 4 };
const config = {
  displaylogo: false,
  modeBarButtonsToRemove: ['lasso2d', 'select2d', 'pan2d', 'zoom2d', 'hoverClosestCartesian', 'hoverCompareCartesian', 'toggleSpikelines'],
  responsive: true
};
let enableKeyDetect = false;

const run_status_classes = 'run-init run-pass run-wait run-skip run-next run-fail run-pause'

let machine_hard_idct = document.querySelectorAll('#machine_hard_idct .idct-number')[0]
let machine_temp_idct = document.querySelectorAll('#machine_tempr_idct .idct-number')[0]
let machine_humi_idct = document.querySelectorAll('#machine_hum_idct  .idct-number')[0]

let forceManualMode = false;
let digitestIsRotationMode = false;
let runningTest = false;

// **************************************
// init functions
// **************************************
generateEventPlot()
tools.generateHardnessPlot('hardness_graph', 0)



// **************************************
// generate graph functions
// **************************************


function generateEventPlot() {

  var trace1 = {
    // x: h_data_x,
    type: "scattergl",
    name: 'temperature',
    x: [],
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
    x: [],
    y: [],
    yaxis: 'y2',
    mode: 'markers',
    marker: { size: 4, color: 'blue' },
    line: {
      dash: 'dot',
      width: 1,
      color: 'blue'
    }
  };

  var data = [trace1, trace2];

  var layout = {
    xaxis: {
      title: 'Time(H:M:S)',
      zeroline: false,
      showline: true,
      type: 'date',
      tickformat: '%H:%M:%S'
    },
    yaxis: {
      title: 'Temperature(℃)',
      zeroline: false,
      showline: true
    },
    yaxis2: {
      title: 'Hardness',
      titlefont: { color: 'rgb(148, 103, 189)' },
      tickfont: { color: 'rgb(148, 103, 189)' },
      overlaying: 'y',
      side: 'right',
      range: [0, 100]
    },
    showlegend: true,
    legend: { "orientation": "h", x: 0, xanchor: 'left', y: 1.2, yanchor: 'top' },
    width: 400,
    height: 300,
    margin: plotMargin,
    autosize: false,
    font: { color: "dimgray", family: "Arial", size: 10 }
  };

  Plotly.newPlot('event_graph', data, layout, config);
}

function repositionChart() {
  var update = {
    autosize: true,
  };
  if (!$('#hardness_graph').html() === '') {
    // check if chart has data, if no data, the following function will throw error
    Plotly.relayout('hardness_graph', update);
    Plotly.relayout('event_graph', update);
  }

  Plotly.relayout('hardness_graph', update);
  Plotly.relayout('event_graph', update);

}

function genrateBatchHistory(batchRecords) {
  $('#batchHistoryTable').DataTable().destroy();

  var my_columns = [
    { data: 'Project_Name' },
    { data: 'Batch_Name' },
    { data: 'Creation_Date' },
    { data: 'Note' },
    { data: 'Last_seq_name' }
  ];

  $('#batchHistoryTable').DataTable({
    select: true,
    data: batchRecords,
    columns: my_columns,
    deferRender: true,
    scrollX: true,
    scrollY: 400,
    scrollCollapse: true,
    scroller: true,
    order: [[2, 'desc']]
  }).draw();

  $('#batchHistoryTable tbody').on('click', 'tr', function () {

  });

}

// **************************************
// websocket functions
// **************************************
function connect() {
  try {
    const WebSocket = require('ws');
    ws = new WebSocket('ws://127.0.0.1:5678');
  } catch (e) {
    console.log('Socket init error. Reconnect will be attempted in 1 second.', e.reason);
  }

  ws.on('open', function open() {
    console.log('websocket in run connected')
  });

  ws.on('ping', () => {
    ws.send(tools.parseCmd('pong', 'from run'));
  })

  ws.on('message', function incoming(message) {

    try {

      msg = tools.parseServerMessage(message);
      let cmd = msg.cmd;
      let data = msg.data;
      switch (cmd) {
        case 'ping':
          // console.log('got server data ' + data)
          ws.send(tools.parseCmd('pong', data));
          break;
        case 'reply_log_to_db':
          break;
        case 'reply_init_hw':
          console.log('reply_init_hw')
          if (data.resp_code == 1) {
            runningTest = false
            batchSelector_enable();
          } else {
            ipcRenderer.send('show-alert-alert', window.lang_data.modal_alert_title, data.res + '\n' + data.reason);
          }
          break;
        case 'getRotationTable_N':
          uutN = parseInt(data);
          break;
        case 'get_digitest_manual_mode':
          console.log('mode changed', data)
          forceManualMode = data;
          createInstance()
          updateDigiTestModeCallback()
          break;
        case 'get_digitest_is_rotaion_mode':
          digitestIsRotationMode = data;
          createInstance();
          updateDigiTestModeCallback();
          break;
        case 'reply_load_seq':
          updateSequence(data)
          break;
        case 'update_sys_default_config':
          updateServerSeqFolder(data);
          break;
        case 'update_step_result':
          updateSingleStep(data);
          break;
        case 'update_cursor':
          console.log(data);
          break;
        case 'update_gauge_ref':
          break;
        case 'show_move_sample_dialog':
          showMovingSampleDialog(data);
          break;
        case 'reply_query_batch_history':
          genrateBatchHistory(data);
          break;
        case 'reply_create_batch':
          if (data.resp_code == 1) {
            ipcRenderer.send('show-info-alert', data.title, data.reason);
            batch_confirmed();
          } else if (data.resp_code == 0) {
            let args = { batchName: data.batchName }
            ipcRenderer.send('show-option-dialog', data.title, data.reason, 'continue-batch', args);
          }
          break;
        case 'reply_continue_batch':
          if (data.resp_code == 1) {
            ipcRenderer.send('show-info-alert', data.title, data.reason);
            batch_confirmed();
          }
          break;
        case 'only_update_hardness_indicator':
          machine_hard_idct.innerText = data;
          break;
        case 'update_machine_status':
          updateStatusIndicator(data.dt, data.temp, data.hum)
          break;
        case 'end_of_test':
          endOfTest(data)
          break;
        case 'reply_server_error':
          ipcRenderer.send('show-server-error', data.error);
          runningTest = false
          break;
        default:
          console.log('Not found this cmd' + cmd)
          break;
      }
    } catch (e) {
      console.error(e)
      runningTest = false
    }

  });

  ws.onclose = function (e) {
    console.log('Socket is closed. Reconnect will be attempted in 1 second.', e.reason);
    setTimeout(function () {
      connect();
    }, 1000);
  };

  ws.onerror = function (err) {
    console.error('Socket encountered error: ', err.message, 'Closing socket');
    ws.close();
  };
}

connect()

// **************************************
// event functions
// **************************************

batchNew.addEventListener('click', () => {
  $("#sampleBatchConfigForm input[name!='NumberOfSample'],textarea").each((i, elm) => {
    elm.value = ''
  })
  batchInfo_enable();
})
batchLoad.addEventListener('click', () => {
  showBatchSelectDialog();
  // batchContent_disable();
  batchConfirmAndStartBtn_enable();
})
selectHistoryBatch.addEventListener('click', () => {
  selectedHistoryBatch();
})
loadSeqBtn.addEventListener('click', () => {
  loadSeqFromServer();
})
batchConfirmAndStartBtn.addEventListener('click', () => {
  immediate_start_test()
})

$('#setupBatchModal').on('click', () => enableKeyDetect = false);

openSampleSetupListBtn.addEventListener('click', () => {
  sampleSetupDialog.style.display = 'block';
  switchStatusMonitorPanel()
  enableKeyDetect = true;
})
ipcRenderer.on('load-seq-run', (event, path) => {
  updateLoadedPathObj(path)
  $("#sampleBatchConfigForm input[name='SeqName']").val(loadSeqPathObj.name)
  ws.send(tools.parseCmd('run_cmd', tools.parseCmd('load_seq', { path: path })));
});
ipcRenderer.on('continue-batch', (event, resp, args) => {
  if (resp == 0) {
    let batchName = args.batchName;
    const targetBatch = batches.find(elm => { return elm.batch === batchName })
    ws.send(tools.parseCmd('continue_batch', [targetBatch]));
  }
})

stopSeqBtn.addEventListener('click', () => {
  ws.send(tools.parseCmd('stop_seq', ''));
})

// **************************************
// general functions
// **************************************

function init() {
  console.log('run.js inited')
  ws.send(tools.parseCmd('run_cmd', tools.parseCmd('get_default_seq_path')));
  ws.send(tools.parseCmd('get_digitest_manual_mode'));
  ws.send(tools.parseCmd('get_digitest_is_rotaion_mode'));
}

function switchStatusMonitorPanel() {
  $(sampleBatchCircleContainer).addClass('displayHide')
  $(sampleBatchListContainer).addClass('displayHide')
  $('#sampleListStatusContainer').addClass('displayHide')
  $('#sampleCircleStatus').addClass('displayHide')
  if (forceManualMode || !digitestIsRotationMode) {
    $(sampleBatchListContainer).removeClass('displayHide')
    $('#sampleListStatusContainer').removeClass('displayHide')
    initSampleList()
  } else {
    $(sampleBatchCircleContainer).removeClass('displayHide')
    $('#sampleCircleStatus').removeClass('displayHide')
    initCirclePlot();
  }
}

function batchSelector_enable() {
  $(batchNew).removeClass('btnEnable btnDisable').addClass('btnEnable');
  $(batchLoad).removeClass('btnEnable btnDisable').addClass('btnEnable');
}

function batchSelector_disable() {
  $(batchNew).removeClass('btnEnable btnDisable').addClass('btnDisable');
  $(batchLoad).removeClass('btnEnable btnDisable').addClass('btnDisable');
}

function batchInfo_enable() {
  batchContent_enable();
  batchConfirmAndStartBtn_enable();
}

function batchInfo_disable() {
  batchContent_disable();
  batchConfirmAndStartBtn_disable();
}

function batchContent_enable() {
  $(sampleBatchConfigForm).removeClass('btnEnable btnDisable').addClass('btnEnable');
  $(seqNameInFormInput).removeClass('btnEnable btnDisable').addClass('btnEnable');
  $(loadSeqBtn).removeClass('btnEnable btnDisable').addClass('btnEnable');
  $(noteInForm).removeClass('btnEnable btnDisable').addClass('btnEnable');
}

function batchContent_disable() {
  $(seqNameInFormInput).removeClass('btnEnable btnDisable').addClass('btnDisable');
  $(loadSeqBtn).removeClass('btnEnable btnDisable').addClass('btnDisable');
  $(noteInForm).removeClass('btnEnable btnDisable').addClass('btnEnable');
}

function batchSetupBtn_enable() {
  $(openSampleSetupListBtn).removeClass('btnEnable btnDisable').addClass('btnEnable');
}

function batchSetupBtn_disable() {
  $(openSampleSetupListBtn).removeClass('btnEnable btnDisable').addClass('btnDisable');
}

function batchConfirmAndStartBtn_enable() {
  $(batchConfirmAndStartBtn).removeClass('btnEnable btnDisable').addClass('btnEnable');
}

function batchConfirmAndStartBtn_disable() {
  $(batchConfirmAndStartBtn).removeClass('btnEnable btnDisable').addClass('btnDisable');
}

function stopBtn_disable() {
  $(stopSeqBtn).removeClass('btnEnable btnDisable').addClass('btnDisable');
}

function stopBtn_enable() {
  $(stopSeqBtn).removeClass('btnEnable btnDisable').addClass('btnEnable');
}

function updateServerSeqFolder(path) {
  defaultSeqPath = path;
}

function loadSeqFromServer() {
  console.log(defaultSeqPath)
  ipcRenderer.send('open-file-dialog', defaultSeqPath, 'load-seq-run')
};

function updateSequence(res) {
  const errorReason = res.error;
  const script = res.script;
  if (errorReason === null) {
    test_flow.setup = script.setup;
    test_flow.main = script.main;
    test_flow.loop = script.loop;
    test_flow.teardown = script.teardown;
    seqRend.sortSeq('testSeqContainer', test_flow.setup, test_flow.main, test_flow.teardown, false);
    const statsOfSeqs = seqRend.calcApproxTimeAndTemperature(test_flow, 20);
    document.getElementById('batchMaxTemperature').innerHTML=statsOfSeqs.stats.maxTemp;
    document.getElementById('batchMinTemperature').innerHTML=statsOfSeqs.stats.mintemp;
    document.getElementById('batchMaxTime').innerHTML=tools.sec2dt(statsOfSeqs.stats.overallTime*60).substr(11, 8);
  } else {
    ipcRenderer.send('show-warning-alert', window.lang_data.modal_warning_title, errorReason);
  }

}

function getBatchInfo() {
  let batchData = $('#sampleBatchConfigForm').serializeArray();
  return batchData;
}

function selectedHistoryBatch() {
  let table = $('#batchHistoryTable').DataTable();
  let isSelected = table.rows('.selected').any();
  const seqjInput = $("#sampleBatchConfigForm input[name='SeqName']")[0];
  const projInput = $("#sampleBatchConfigForm input[name='Project']")[0];
  const batchjInput = $("#sampleBatchConfigForm input[name='Batch']")[0];
  if (isSelected) {
    let selectedData = table.row('.selected').data();
    ret = updateLoadedPathObj(selectedData.Last_seq_name)
    $(seqjInput).val(ret.name)
    $(projInput).val(selectedData.Project_Name)
    $(batchjInput).val(selectedData.Batch_Name)
    $(noteInForm).val(selectedData.Note);
    let dialog = document.getElementById('modal_batch_select_dialog');
    dialog.style.display = 'none';
    ws.send(tools.parseCmd('run_cmd', tools.parseCmd('load_seq', { path: selectedData.Last_seq_name })));
  } else {
    ipcRenderer.send('show-info-alert', window.lang_data.modal_info_title, window.lang_data.please_select_one_batch);
  }

}

function immediate_start_test() {
  // start test
  runningTest = true
  ws.send(tools.parseCmd('run_cmd', tools.parseCmd('load_seq', { path: loadSeqPathObj.path })));
  ipcRenderer.send('toggle_monitor', !runningTest);
  batchSetupBtn_disable()
  batchConfirmAndStartBtn_disable();
  stopBtn_enable();
  $('main> nav .nav-item a').removeClass('btnEnable btnDisable').addClass('btnDisable');
  $('.lang-flags').removeClass('btnEnable btnDisable').addClass('btnDisable');
  $('#testSeqContainer li').removeClass(run_status_classes).addClass('run-init');
  getBatchInfo();
  initMonitorCirclePlot()
  markers = [];
  const onlyOccupySamples = batchInfoForSamples.filter(elm => elm.status === 'filled')
  ws.send(tools.parseCmd('run_seq', { batchInfoForSamples: onlyOccupySamples }));
  tools.generateHardnessPlot('hardness_graph', onlyOccupySamples.length);
  generateEventPlot();
  repositionChart();
  markCurrentSample(0)
}

function markCurrentSample(sampldIdx) {
  if (forceManualMode || !digitestIsRotationMode) {
    $('#sampleListStatusContainer .uutfilled').removeClass('curSample');
    $('#sampleListStatusContainer .uutfilled').each((idx, elm) => {
      if (idx === sampldIdx) {
        $(elm).addClass('curSample')
      }
    })
  } else {
    $('#sampleCircleStatus .uutfilled').removeClass('curSample');
    $('#sampleCircleStatus .uutfilled').each((idx, elm) => {
      if (idx === sampldIdx) {
        $(elm).addClass('curSample')
      }
    })
  }

}

function updateSingleStep(res) {
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
  tools.updateNumIndicator(machine_temp_idct, actTemp, 1)
  tools.updateNumIndicator(machine_humi_idct, actHumi, 1)

  // update value in step
  curResult.html(value + unit)
  curstep.removeClass(run_status_classes)
  updateStepByCat(res);
  if (result == 'PASS') { curstep.addClass('run-pass'); }
  else if (result == 'WAITING') { curstep.addClass('run-wait'); }
  else if (result == 'UPDATE_PROGRESS_ONLY') { curstep.addClass('run-wait'); }
  else if (result == 'PAUSE') { curstep.addClass('run-pause'); }
  else if (result == 'SKIP') { curstep.addClass('run-skip'); }
  else if (result == 'MEAR_NEXT') { curstep.addClass('run-next'); }
  else if (result == 'UPDATE_CURRENT_SAMPLEINDEX') { }
  else { curstep.addClass('run-fail'); }

}

function logdata(res) {
  console.log('[add data: sampleIndex]', res.sampleIndex)
  console.log('[add data: result]', res.status)
  console.log('[add data: hardness value]', res.value)
  console.log('[add data: temperature value]', res.actTemp)
}

function updateStepByCat(res) {
  let batch = res.batch;
  let sampleIndex = res.sampleIndex;
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

  switch (stepname) {
    case 'ramp':
      if (result !== 'UPDATE_PROGRESS_ONLY') {
        tools.plotly_addNewDataToPlot('event_graph', tools.sec2dt(relTime), actTemp)
      }
      curProgs.val(progs);
      break;
    case 'measure':
      if (result == 'PASS') {
        logdata(res)
        curProgs.val(progs);
        tools.updateNumIndicator(machine_hard_idct, value, 1)
        tools.plotly_addNewDataToPlot('hardness_graph', actTemp, value, y2val = null, sampleId = sampleIndex)
        tools.plotly_addNewDataToPlot('event_graph', tools.sec2dt(relTime), actTemp, value)
      } else if (result == 'MEAR_NEXT') {
        logdata(res)
        curProgs.val(progs);
        tools.updateNumIndicator(machine_hard_idct, value, 1)
        tools.plotly_addNewDataToPlot('hardness_graph', actTemp, value, y2val = null, sampleId = sampleIndex)
        tools.plotly_addNewDataToPlot('event_graph', tools.sec2dt(relTime), actTemp, value)
      } else if (result == 'WAITING') {
        markCurrentSample(sampleIndex)
        curProgs.val(progs);
      } else if (result == 'UPDATE_CURRENT_SAMPLEINDEX') {
        logdata(res)
        markCurrentSample(sampleIndex)
      }
      if (eventName !== null) {
        // tools.plotly_addAnnotation('event_graph',eventName,relTime,actTemp,markers)
      }
      // updateValue('hardness_graph', value);
      break;
    case 'time':
      if (result !== 'UPDATE_PROGRESS_ONLY') {
        tools.plotly_addNewDataToPlot('event_graph', tools.sec2dt(relTime), actTemp)
      }
      curProgs.val(progs);
      break;

    case 'teardown':
      // updateValue('actualTempGauge', actTemp);
      tools.plotly_addNewDataToPlot('event_graph', tools.sec2dt(relTime), actTemp)
      curProgs.val(progs);
      break;
    default:
      console.log('Not found this stepname: ' + stepname)
      break;
  }

}

function listDataset(data) {
  let liComponent = `
    <thead>
    <tr class="w3-black">
      <th>No.</th>
      <th>Value</th>
    </tr>
    </thead>
  `;
  data.forEach((item, index) => {
    liComponent += `
    <tr>
      <td>${index + 1}</td>
      <td>${item}</td>
    </tr>
    `
  })
  return liComponent
}

function showBatchSelectDialog() {
  ws.send(tools.parseCmd('query_batch_history'));
  let dialog = document.getElementById('modal_batch_select_dialog');
  dialog.style.display = 'block';
}

function showMovingSampleDialog(data) {
  let curData = data;
  dialog_dataset_index.innerHTML = curData.curSampleIdx
  dialog_dataset_id.innerHTML = curData.curSampleIdInBatch
  dialog_dataset_counter.innerHTML = `(${curData.dataset.length} / ${curData.totalCounts})`
  dialog_dataset_list.innerHTML = listDataset(curData.dataset);
  dialog_dataset_mean.innerHTML = `${curData.method}: ${curData.result}`;
  dialog_dataset_stdev.innerHTML = `stdev: ${curData.std}`
  dialog.style.display = 'block';
}

start_btn.addEventListener('click', () => {
  start_mear_after_move_sample();
})
retry_btn.addEventListener('click', () => {
  start_mear_after_move_sample(true);
})

function start_mear_after_move_sample(isRetry = false) {
  let dialog = document.getElementById('modal_moving_sample_dialog');
  dialog.style.display = 'none';
  ws.send(tools.parseCmd('continue_seq', isRetry));
}

function endOfTest(res) {
  console.log('[end of test]', res)
  let interrupted = res.interrupted;
  let title = res.title;
  let reason = res.reason;
  batchSelector_enable();
  batchContent_enable()
  batchConfirmAndStartBtn_enable();
  batchSetupBtn_enable();
  stopBtn_disable();
  $('main> nav .nav-item a').removeClass('btnEnable btnDisable').addClass('btnEnable');
  $('.lang-flags').removeClass('btnEnable btnDisable').addClass('btnEnable');
  if (!interrupted) {
    ipcRenderer.send('show-info-alert', title, reason);
  } else {
    ipcRenderer.send('show-warning-alert', title, reason);
  }
  runningTest = false
  ipcRenderer.send('toggle_monitor', !runningTest);
}

const updateLoadedPathObj = (abspath) => {
  loadSeqPathObj.path = abspath;
  loadSeqPathObj.name = abspath.replace(/^.*[\\\/]/, '')
  return loadSeqPathObj
}



// **************************************
// generate gauge functions
// **************************************
const createCircle = (container, cx, cy, r, className = '', color = 'white') => {
  let circle = document.createElementNS(svgns, 'circle');
  circle.setAttributeNS(null, 'class', className);
  circle.setAttributeNS(null, 'cx', cx);
  circle.setAttributeNS(null, 'cy', cy);
  circle.setAttributeNS(null, 'r', r);
  circle.setAttributeNS(null, 'style', `fill: ${color}`);
  // circle.setAttributeNS(null, 'style', 'fill: lightyellow; stroke: black; stroke-width: 1px;' );
  container.appendChild(circle);
}

const createText = (container, cx, cy, strTxt = '', options = {}, className = '') => {
  var text = document.createElementNS(svgns, 'text');
  text.setAttributeNS(null, 'class', className);
  text.setAttributeNS(null, 'x', cx);
  text.setAttributeNS(null, 'y', cy);
  Object.keys(options).forEach((elm, idx) => {
    text.setAttributeNS(null, elm, options[elm])
  })
  let textNode = document.createTextNode(strTxt);
  text.appendChild(textNode);
  container.appendChild(text);
}

function createListInstance() {
  batchInfoForSamples = [];
  batches = [];
  for (let i = 0; i < 50; i++) {
    batchInfoForSamples.push({ id: i, status: 'empty', batchInfo: {}, color: 'white' });
  }
}

function createCirclesInstance() {
  batchInfoForSamples = [];
  batches = [];
  for (let i = 0; i < uutN; i++) {
    batchInfoForSamples.push({ id: i, status: 'empty', batchInfo: {}, color: 'white' });
  }
}

function plotBaseTable(targetElm, raduis) {
  createCircle(targetElm, '50%', '50%', raduis, 'baseCircle', '#bdc3c7')
}

function plotSmallHoles(targetElm, circleN = 25, option) {
  let bboxRect = targetElm.getBBox()
  const newCenterX = bboxRect.x + bboxRect.width / 2;
  const newCenterY = bboxRect.y + bboxRect.height / 2;

  batchInfoForSamples.forEach((elm) => {
    let theda = elm.id * 2 * (Math.PI) / circleN;
    let smcx = newCenterX + option.childR * Math.cos(theda - 0.5 * Math.PI);
    let smcy = newCenterY + option.childR * Math.sin(theda + 0.5 * Math.PI);
    let txtcx = newCenterX + option.childTxtR * Math.cos(theda - 0.5 * Math.PI);
    let txtcy = newCenterY + option.childTxtR * Math.sin(theda + 0.5 * Math.PI);
    singleCircle = { 'cx': smcx, 'cy': smcy, 'radius': option.radius };
    if (elm.status === 'empty') {
      createCircle(targetElm, smcx, smcy, option.radius, 'uut', 'white')
    } else if (elm.status === 'filled') {
      createCircle(targetElm, smcx, smcy, option.radius, 'uutfilled', elm.color)
    }
    createText(targetElm, txtcx, txtcy, strTxt = elm.id + 1, option.textOption, className = 'textuut')
  })
}

function plotList() {
  const sampleListContainer = document.getElementById('sampleListContainer');
  const sampleMonitorContainer = document.getElementById('sampleListStatusContainer')
  let listContents = '';
  let blockContents = '';
  batchInfoForSamples.forEach((elm) => {
    let listItem = ''
    let blockItem = ''
    if (elm.status !== 'empty') {
      listItem = `
        <li class="sampleListItem">
          <div class="w3-tag w3-large" style='color:white;background-color:${elm.color}'>${elm.id + 1}</div>          
          <div class="batchInfoContent">
            <div><span style='font-weight: bold;' data-lang='run_batch_title' data-lang_type='innertext'>${window.lang_data.run_batch_title}: </span>${elm.batchInfo.batch}</div>
            <div class="w3-small" data-lang='modal_moving_sample_sampleID' data-lang_type='innertext'>${window.lang_data.modal_moving_sample_sampleID}: ${elm.batchInfo.sampleId + 1}</div>
          </div>
          
        </li>
      `;
      blockItem = `<div class="w3-tag ${elm.status === 'empty' ? 'uut' : 'uutfilled'}" style='color:white;background-color:${elm.color}'>${elm.id + 1}</div>`
    }
    listContents += listItem;
    blockContents += blockItem;
  })

  $(sampleListContainer).html(listContents);
  $(sampleMonitorContainer).html(blockContents);
}

function setSampleOccupy(index = 0, batchInfo = {}, color = 'white') {
  let spcCirlce = batchInfoForSamples.find(elm => elm.id === index)
  spcCirlce.status = 'filled'
  spcCirlce.batchInfo = { ...batchInfo }
  spcCirlce.color = color
  batchInfoForSamples.splice(index, 1, spcCirlce)
}

function refreshSeqsInAllSamples(seqPath) {
  batchInfoForSamples.forEach(elm => {
    elm.batchInfo.seq_name = seqPath;
  })

}

const initSampleList = () => {
  $('#sampleBatchListContainer ul').html = '';
  $('#sampleListStatusContainer').html = '';
  plotList();
}

const initCirclePlot = () => {
  svgContainer.innerHTML = ''
  plotBaseTable(svgContainer, baseR);
  plotSmallHoles(svgContainer, uutN, smallCircleOption);
}

$('#sampleBatchConfigForm').on('submit', (e) => {
  e.preventDefault();
  let batchinfos = getBatchInfo();
  let seqPath = loadSeqPathObj.path;
  let proj = batchinfos.filter(item => item.name == 'Project')[0].value;
  let batch = batchinfos.filter(item => item.name == 'Batch')[0].value;
  let numSample = batchinfos.filter(item => item.name == 'NumberOfSample')[0].value;
  let emptySamples = batchInfoForSamples.filter((elm) => elm.status === 'empty');
  numSample = parseInt(numSample) > emptySamples.length ? emptySamples.length : parseInt(numSample);
  let note = batchinfos.filter(item => item.name == 'Note')[0].value;
  let curBatchinfo = { 'project': proj, 'batch': batch, 'notes': note, 'seq_name': seqPath, 'numSample': parseInt(numSample), 'sampleId': 0 }

  let sampleCounterInBatch = 0;
  let sampleColor = 'red';
  const existedBatch = batches.find(elm => elm.batch === batch);
  const existedBatchIndex = batches.findIndex(elm => elm.batch === batch);
  let isNewBatch = existedBatch === undefined ? true : false;
  if (isNewBatch) {
    sampleColor = tools.pick_color_hsl(batchCounter)
  } else {
    sampleCounterInBatch = existedBatch.numSample;
    const existedSample = batchInfoForSamples.find((elm) => elm.batchInfo.batch === existedBatch.batch);
    if (existedSample !== undefined) {
      sampleColor = existedSample.color;
    }
  }
  console.log('sampleCounterInBatch', sampleCounterInBatch)
  let counter = 0
  batchInfoForSamples.forEach(elm => {
    if (counter < numSample) {
      if (elm.status === 'filled') {
        const thisBatchName = elm.batchInfo.batch;
        let thisBatchTotalSamples = elm.batchInfo.numSample;
        if (thisBatchName === curBatchinfo.batch) {
          curBatchinfo.numSample = thisBatchTotalSamples + parseInt(numSample)
          sampleCounterInBatch += 1
        }
      } else if (elm.status === 'empty') {
        curBatchinfo.sampleId = sampleCounterInBatch
        setSampleOccupy(elm.id, { ...curBatchinfo }, sampleColor)
        sampleCounterInBatch += 1
        counter += 1
      }
    }
  })
  if (isNewBatch) {
    batches.push({ ...curBatchinfo })
    batchCounter += 1
  } else {
    batches.splice(existedBatchIndex, 1, { ...curBatchinfo })
  }
  refreshSeqsInAllSamples(seqPath)

  if (forceManualMode || !digitestIsRotationMode) {
    initSampleList()
  } else {
    initCirclePlot()
  }

})

function createInstance() {
  if (forceManualMode || !digitestIsRotationMode) {
    createListInstance()
  } else {
    createCirclesInstance()
  }
  initSampleList();
  initCirclePlot();
}

createInstance()

confirmSampleBatchConfigBtn.addEventListener('click', () => {
  ws.send(tools.parseCmd('create_batch', batches));
})

function createBatchViewList() {
  // batchInfo:
  //   batch: "segher"
  //   notes: ""
  //   numSample: 3
  //   project: "rh"
  //   sampleId: 0
  //   seq_name: "C:\data_exports\seq_files\singletest.seq"
  let batchViewContent = '';
  batches.forEach((elm, idx) => {
    batchViewContent += `
      <button class="batchAccordion"><span data-lang='run_batch_title' data-lang_type='innertext'>${window.lang_data.run_batch_title}</span>: ${elm.batch}</button>
      <div class="panel">
        <i class="fab fa-product-hunt"></i><label data-lang='run_project_title' data-lang_type='innertext'> ${window.lang_data.run_project_title}</label>
        <p>${elm.project}</p>
        <i class="fab fa-buffer"></i><label data-lang='run_n_sample_title' data-lang_type='innertext'> ${window.lang_data.run_n_sample_title}</label>
        <p>${elm.numSample}</p>
        <i class="fas fa-align-left"></i><label data-lang='run_load_seq_title' data-lang_type='innertext'> ${window.lang_data.run_load_seq_title}</label>
        <p>${elm.seq_name}</p>
        <i class="far fa-sticky-note"></i><label data-lang='run_note_title' data-lang_type='innertext'> ${window.lang_data.run_note_title}</label>
        <p>${elm.notes}</p>
      </div>
    `
  })
  batchViewList.innerHTML = batchViewContent;
  var acc = document.getElementsByClassName("batchAccordion");
  var i;

  for (i = 0; i < acc.length; i++) {
    acc[i].addEventListener("click", function () {
      this.classList.toggle("active");
      var panel = this.nextElementSibling;
      if (panel.style.maxHeight) {
        panel.style.maxHeight = null;
      } else {
        panel.style.maxHeight = panel.scrollHeight + "px";
      }
    });
  }
}

function batch_confirmed() {
  initMonitorCirclePlot()
  createBatchViewList()
  document.getElementById('modal_batch_setup_dialog').style.display = 'none'
}

$('#sampleBatchConfigClearAllBtn').on('click', () => {
  batchCounter = 0
  createInstance();
  initSampleList();
  initCirclePlot();
})

// for move rotation table
$('#goToIndexBtn').on('click', () => {
  const nextIndex = $("#goToIndexValue").val()
  ws.send(tools.parseCmd('run_cmd', tools.parseCmd('goToIndex', nextIndex)));
})

$('#moveHomeBtn').on('click', () => {
  ws.send(tools.parseCmd('run_cmd', tools.parseCmd('moveTableHome')));
})

function initMonitorCirclePlot() {
  statusCircle.innerHTML = ''
  plotBaseTable(statusCircle, baseRStatus);
  plotSmallHoles(statusCircle, uutN, smallCircleStatusOption);
}

$(window).resize((e) => {
  initMonitorCirclePlot();
  initCirclePlot();
})

function updateDigiTestModeCallback() {
  switchStatusMonitorPanel();
  initMonitorCirclePlot();
  initCirclePlot();
  repositionChart();
}

$('#button-run').on('click', () => {
  if (runningTest) {
  } else {
    updateDigiTestModeCallback()
  }
})


// detect select language
ipcRenderer.on('trigger_tanslate', (event) => {
  console.log('[test_flow.setup.para]', test_flow.setup.subitem)
  if (test_flow.setup.subitem !== undefined) {
    $('#testSeqContainer').html(seqRend.refreshSeq(test_flow, false))
  }
})

// detect config changed
ipcRenderer.on('update_config', (event) => {
  console.log('[config changed detected in run section]')
  ws.send(tools.parseCmd('get_digitest_manual_mode'));
  ws.send(tools.parseCmd('get_digitest_is_rotaion_mode'));
})

function updateStatusIndicator(hard = null, temp = null, hum = null) {
  if (hard != null) {
    tools.updateStatusIndicator(hard_idct_status, hard.status, window.lang_data['machine_connected'], window.lang_data['machine_disconnected'], window.lang_data['machine_running'])
  }
  if (temp != null) {
    tools.updateStatusIndicator(temp_idct_status, temp.status, window.lang_data['machine_connected'], window.lang_data['machine_disconnected'], window.lang_data['machine_running'])
  }
  if (hum != null) {
    tools.updateStatusIndicator(humi_idct_status, hum.status, window.lang_data['machine_connected'], window.lang_data['machine_disconnected'], window.lang_data['machine_running'])
  }

}

// init after system initialized
ipcRenderer.on('system-inited', (event) => {
  init()
})
