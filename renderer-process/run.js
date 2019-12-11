const {ipcRenderer} = require("electron");
const app = require('electron').remote.app
const zerorpc = require("zerorpc");
const client = new zerorpc.Client({ timeout: 60, heartbeatInterval: 60000 });
// create zerorpc instance
client.connect("tcp://127.0.0.1:4242");


// **************************************
// variable define
// **************************************
let h_data_x = Array.from({length: 40}, () => Math.floor(Math.random() * 40));
let h_data_y = Array.from({length: 40}, () => Math.floor(Math.random() * 40));
let datapoints_x = Array.from({length: 40}, () => Math.floor(Math.random() * 40));
let datapoints_y = Array.from({length: 40}, () => Math.floor(Math.random() * 40));
let defaultSeqPath = null;
let startSeqBtn = document.getElementById('start_test');
let stopSeqBtn = document.getElementById('stop_test');
let loadSeqBtn = document.getElementById('open_test_seq')
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
const plotMargin = { t: 40, r: 50, l: 40, b: 50};
const config = {
  displaylogo: false,
  modeBarButtonsToRemove: ['toImage'],
  responsive: true
};


// **************************************
// init functions
// **************************************
generateHardnessVsTempPlot()
generateHardnessPlot()
repositionChart()
generateGauge('actualTempGauge', 23, -40, 200,'Temperature');
generateGauge('actualHumGauge', 50, 0, 100,'Humidity');


// **************************************
// generate graph functions
// **************************************


function generateHardnessVsTempPlot(){
  
    var trace = {
        // x: datapoints_x,
        y: datapoints_y,
      mode: 'lines+markers',
      name: 'Scatter and Lines',
      line: {
        color: 'rgb(219, 64, 82)',
        width: 3
      }
    };
  
    var data = [trace];

    var layout = {
      xaxis: {
        title: 'degree Celsius ℃'
      },
      yaxis: {
        title: 'hardness'
      },
      width: 400,
      height: 200,
      margin: plotMargin,
      autosize: true,
      font: { color: "dimgray", family: "Arial", size: 10}
    };
    
    Plotly.newPlot('hardnessVStemp_graph', data, layout,config);
  }

  function generateHardnessPlot(){
  
    var trace = {
      // x: h_data_x,
      y: h_data_y,
      mode: 'lines+markers',
      name: 'Scatter and Lines',
      line: {
        color: 'rgb(219, 64, 82)',
        width: 3
      }
    };
  
    var data = [trace];
    
    var layout = {
      xaxis: {
        title: 'samples'
      },
      yaxis: {
        title: 'hardness'
      },
      width: 400,
      height: 200,
      margin: plotMargin,
      autosize: true,
      font: { color: "dimgray", family: "Arial", size: 10}
    };
    
    Plotly.newPlot('hardness_graph', data, layout, config);
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
        title: { text: titleText, font: { size: 14 } },
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
            value: refvalue
          }
        }
      }
    ];
    
    var layout = {
      width: 250,
      height: 230,
      margin: { t: 10, r: 25, l: 25, b: 10 },
      paper_bgcolor: "transparent",
      font: { color: "dimgray", family: "Arial", size: 10}
    };
  
    Plotly.newPlot(locationID, data, layout,{
      displaylogo: false,
      modeBarButtonsToRemove: ['toImage'],
      responsive: true
    });
  }

function repositionChart(){
  var update = {
    autosize: true,
  };
  if (!$('#hardness_graph').html()===''){
    // check if chart has data, if no data, the following function will throw error
    Plotly.relayout('hardness_graph', update);
    Plotly.relayout('hardnessVStemp_graph', update);
  }

  Plotly.relayout('hardness_graph', update);
  Plotly.relayout('hardnessVStemp_graph', update);

}

  
// **************************************
// event functions
// **************************************
loadSeqBtn.addEventListener('click', ()=>{
    loadSeqFromServer()
})

ipcRenderer.on('load-seq', (event, path) => {

  $('#batchInfoForm input[name=SeqName]').val(path)

    client.invoke('run_cmd',parseCmd('load_seq',{path: path}),(err, resObj)=>{
        if(err){
            console.error(err)
        }else{
            logResponse(resObj);
            let {error,res} = resObj;
            console.log(res)
            if(!error){
                // do something
                test_flow.setup = res.setup;
                test_flow.main = res.main;
                seq = res.main
                test_flow.loop = res.loop;
                test_flow.teardown = res.teardown;
                sortSeq();
            }
            
        }
    });
});

$( window ).resize(function() {
  repositionChart();
});

// **************************************
// general functions
// **************************************
function parseCmd(sriptName, data=null){
  return JSON.stringify({'scriptName':sriptName, 'data':data})
}

function logResponse(resObj){
  let isError = resObj.error;
  let response = resObj.res;
  if(isError){
      console.log('error:');
      console.log(response);
  }else{
      console.log('response:');
      console.log(response);
  }
}

function loadSeqFromServer(){
  client.invoke('run_cmd',parseCmd('get_default_seq_path'),(err, resObj)=>{
      if(err){
          console.error(err)
      }else{
          logResponse(resObj);
          let {error,res} = resObj;
          if(!error){
              // do something
              defaultSeqPath = res;
              ipcRenderer.send('open-file-dialog',defaultSeqPath,'load-seq')
          }
      }
  });
  
};


// **************************************
// Sequence render functions
// **************************************

function random_hsl(){
  return "hsla(" + ~~(360 * Math.random()) + "," + "100%,"+ "50%,1)"
}

const capitalize = (s) => {
  if (typeof s !== 'string') return ''
  return s.charAt(0).toUpperCase() + s.slice(1)
}

function sortSeq(){
  let middleSeqs =  generateSeq();
  $('#testSeqContainer').html(generateStartSeq() + middleSeqs + generateEndSeq());
  test_flow.main = seq;
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
              c += `<li><label>${capitalize(item['name'])} ${genUnit(item['unit'])}</label> <input class='w3-input w3-border-bottom w3-cell' value='${item['value']}' type='text' ${ronly}></li>`;
          }else if (t === 'number'){
              c += `<li><label>${capitalize(item['name'])} ${genUnit(item['unit'])}</label> <input class='w3-input w3-border-bottom w3-cell' value='${item['value']}' type='number' ${ronly}></li>`;

          }else if (t === 'bool'){
              c += `<li><input class='w3-check w3-border-bottom w3-cell' checked=${item['value']} type='checkbox' ${ronly}><label> ${capitalize(item['name'])} ${genUnit(item['unit'])}
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
              c += `<li><label>${capitalize(item['name'])} ${genUnit(item['unit'])}</label> 
              <select class="w3-select w3-border" name="option">${opItems}</select></li>`;
          }
      }else{
          c += `<li style='font-size:12px;'><label><b>${capitalize(item['name'])} ${genUnit(item['unit'])}</b></label>: ${item['value']}</li>`;
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
      mainText = `target:${tTempPara.value} ${tTempPara.unit}, slope:${slopePara.value} ${slopePara.unit}`;
  }else if (cat === 'hardness'){
      let methodPara = paras.filter(item=>item.name=='method')[0];
      let modePara = paras.filter(item=>item.name=='mode')[0];
      let mtPara = paras.filter(item=>item.name=='measuring time')[0];
      mainText = `${methodPara.value}, ${modePara.value}, mearTime:${mtPara.value} ${mtPara.unit}`;
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

function genEnableIcon(stepID, enabled){
  let iconset = '';
  if (enabled){
      iconset = 'icon enable_list';
  }else{
      iconset = 'icon disable_list';
  }
  return `<i data-stepID=${stepID} class="${iconset} w3-right w3-margin-right"></i>`
}

function genStepTitles(){
  let titles = [];
  for (i = 0; i < seq.length; i++) {
      let {cat, subitem} = seq[i];
      let parms = genParas(subitem['paras']);
      let en = subitem['enabled'];
      // titles.push(`Step ${i+1} :: ${capitalize(cat)} :: ${capitalize(subitem['item'])}`);
      titles.push(`Step ${i+1} :: ${capitalize(cat)}`);
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
      let en = subitem['enabled']?'':'disabled';
      let stepParaText = genShortParaText(cat,subitem);
      curstr += `
      <li data-stepid=${index} data-sortable=true class='w3-bar'>
          
              <a href="#" style="font-size:14px;width:400px;" class='w3-bar-item'>
                  ${genIconByCat(cat,subitem['paras'])}${stepTitles[index]}${stepParaText}
              </a>
      </li>
      `;
  });
  return curstr;
}

function generateStartSeq() {
  test_flow.setup = setup_seq;
  let curstr = `
  <li>
      <a href="#" ><i class="far fa-play-circle w3-margin-right fa-lg"></i>Sequence Setup</a>
      
  </li>
  `;
  return curstr;
}

function generateEndSeq() {
  test_flow.teardown = teardown_seq;
  let curstr = `
  <li>
      <a href="#" ><i class="far fa-stop-circle w3-margin-right fa-lg"></i>Sequence Teardown</a>
      
  </li>
  `;
  return curstr;
}