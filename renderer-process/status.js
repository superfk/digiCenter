const {ipcRenderer} = require("electron");
const zerorpc = require("zerorpc");
const client = new zerorpc.Client({ timeout: 60, heartbeatInterval: 60000 });
// create zerorpc instance
client.connect("tcp://127.0.0.1:4242");


var datapoints_x = [];
var datapoints_y = [];

function machine_conn(){
  client.invoke('machine_connect', (error, res) => {
    if(error){
      console.error(error)
    }else{
      console.log(res)
    }
  })
}

function generateGauge(locationID, refvalue=23, min=-40, max=200){
  var data = [
    {
      type: "indicator",
      mode: "gauge+number+delta",
      value: 0,
      title: { text: "Temperature", font: { size: 16 } },
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
    width: 300,
    height: 250,
    margin: { t: 50, r: 50, l: 50, b: 25 },
    paper_bgcolor: "transparent",
    font: { color: "dimgray", family: "Arial" }
  };

  Plotly.newPlot(locationID, data, layout);
}

function updateGaugeValue(locationID, val){
  var data_update = 
      {
        value: val,
      }

      Plotly.update(locationID, data_update);
}

function getActualTemp(){

  client.invoke('get_actual_temp', (error, res) => {
    if(error){
      console.error(error);
    }else{
      updateGaugeValue('actualTemp', res)
      let curDataSize = datapoints_x.length;
      datapoints_x.push(curDataSize);
      datapoints_y.push(res);
      generateLinePlot();

    }
  }) 
  
}

function getActualControlTemp(){

  client.invoke('get_actual_control_variable_temp_value', (error, res) => {
    if(error){
      console.error(error);
    }else{
      updateGaugeValue('actualControlTemp', res);

    }
  }) 
  
}

function getInfo(){

  client.invoke('get_info', (error, res) => {
    if(error){
      console.error(error);
    }else{
      $('#info').html(res)
    }
  }) 
  
}

function setGradUpTemp (){
  var val = $('#setGradUpTempValue').val();
  client.invoke('set_gradup_temp_value', val, (error, res) => {
    if (error){
      console.error(error)
    }else{
        $('#targetGradUpTempValue').html(res);
    }
  })
}

function setGradDownTemp (){
  var val = $('#setGradDownTempValue').val();
  client.invoke('set_graddown_temp_value', val, (error, res) => {
    if (error){
        console.error(error)
    }else{
      $('targetGradDownTempValue').html(res);
    }
  })
}

function generateLinePlot(){
  
  var trace = {
    x: datapoints_x,
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
    title: 'Temperature',
    xaxis: {
      title: 'samples'
    },
    yaxis: {
      title: 'degree &#8451;'
    },
    width: 500,
    height: 400
  };
  
  Plotly.newPlot('tempHistory', data, layout);
}


function setControlTempValue(){
  var setPoint = $('#settargetTempValue').val();
  client.invoke('set_control_variable_temp_value', setPoint, (error, res) => {
    if(error){
      console.error(error);
    }else{
      refvalue = res;
      $('#targetTempValue').text(refvalue)
      client.invoke('get_control_variable_temp_maxmin', (error, res) => {
        if(error){
          console.error(error);
        }else{
          //  return Min, Max
          console.log(refvalue)
          console.log(res)
          generateGauge('actualTemp', refvalue, res[0], res[1]);
          generateGauge('actualControlTemp', refvalue, res[0], res[1]);
        }
      })
      
    }
  }) 
}

function startRun(){
  client.invoke('start_run', (error, res) => {
    if(error){
      console.error(error);
    }else{
      datapoints_x = [];
      datapoints_y = [];
    }
  }) 
}

function stopRun(){
  client.invoke('stop_run', (error, res) => {
    if(error){
      console.error(error);
    }else{
    }
  }) 
}



machine_conn();
generateGauge('actualTemp');
generateGauge('actualControlTemp');
generateLinePlot()

$('#getActualTempBtn').on('click',function(){
  setInterval(getActualTemp,500);
})

$('#getActualContrTempBtn').on('click',function(){
  setInterval(getActualControlTemp,500);
})

$('#getInfo').on('click',getInfo);
$('#setContrTempBtn').on('click',setControlTempValue);
$('#setGrdUpTempBtn').on('click',setGradUpTemp);
$('#setGrdDnTempBtn').on('click',setGradDownTemp);
$('#run').on('click',startRun);
$('#stop').on('click',stopRun);

// digitest
var h_data_x = []
var h_data_y = []

function DT_conn(){
  client.invoke('connect_DT', (error, res) => {
    if(error){
      console.error(error)
    }else{
      console.log(res)
    }
  })
}

function generateHardnessGauge(locationID, refvalue=0, min=0, max=100){
  var data = [
    {
      type: "indicator",
      mode: "gauge+number",
      value: 0,
      title: { text: "Hardness", font: { size: 16 } },
      gauge: {
        axis: { range: [min, max], tickwidth: 1, tickcolor: "darkblue" },
        bar: { color: "darkgreen"},
        bgcolor: "lightgreen",
        borderwidth: 0,
        bordercolor: "lightgreen",
        steps: [
          { range: [min, max], color: "lightgreen" }
        ],
        threshold: {
          line: { color: "lightgreen", width: 0 },
          thickness: 0,
          value: refvalue
        }
      }
    }
  ];
  
  var layout = {
    width: 300,
    height: 250,
    margin: { t: 50, r: 50, l: 50, b: 25 },
    paper_bgcolor: "transparent",
    font: { color: "dimgray", family: "Arial" }
  };

  Plotly.newPlot(locationID, data, layout);
}

function generateHardnessPlot(){
  
  var trace = {
    x: h_data_x,
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
    title: 'Hardness',
    xaxis: {
      title: 'Time(s)'
    },
    width: 500,
    height: 400
  };
  
  Plotly.newPlot('hardnessHistory', data, layout);
}

function getDigitestInfo(){
  
  client.invoke('get_DT_info',  (error, res) => {
    if (error){
      console.error(error)
    }else{
     console.log(res)
     content_info = ''
      Object.keys(res).forEach(item => {
        content_info = content_info + "<p>" + item + ': ' + res[item] + '</p>'
      })

     $('#digiTestInfo').html(content_info);
    }
  })
}

function regModeSelection(){
  
  let selectMode = $(this).text();
  console.log(selectMode);
  $('#selectedMode').text(selectMode);

};

function getDigitestMode(){
  
  client.invoke('auto_filter_mode',  (error, res) => {
    if (error){
      console.error(error)
    }else{
     console.log(res)
     content_info = ''
     res.forEach(item => {
        
        content_info = content_info + `<a href="#" class="w3-bar-item w3-button" data-modes="${item}">${item}</a>`
        
      })

     $('#digiTestModeSelection').html(content_info);
     $('#digiTestModeSelection > a').on('click', regModeSelection);
    }
  })
}

function setRemote(){
  
  client.invoke('set_DT_remote', true, (error, res) => {
    if (error){
      console.error(error)
    }else{
      
    }
  })
}

function setUnRemote(){
  
  client.invoke('set_DT_remote', false, (error, res) => {
    if (error){
      console.error(error)
    }else{
      
    }
  })
}

function setDuration(){
  let dur = $('#digiTestDurationValue').val();
  client.invoke('set_DT_duration',dur, (error, res) => {
    if (error){
      console.error(error)
    }else{

    }
  })
}



function setMode(){
  let selectMode = $('#selectedMode').text();
  console.log(selectMode);
  client.invoke('set_DT_mode',selectMode, (error, res) => {
    if (error){
      console.error(error)
    }else{
      
    }
  })
}

function startDigiTestMear(){

  client.invoke('set_DT_mode','STANDARD_M', (error, res) => {
    if (error){
      console.error(error)
    }else{
      
        client.invoke('start_DT_mear', (error, res) => {
          if (error){
            console.error(error)
          }else{

            client.invoke('get_DT_single_data', (error, res) => {
              if (error){
                console.error(error)
              }else{
                console.log(res);
                if (res != undefined){
                  if (res[0]){
                    updateGaugeValue('actualHardness', res[1]);
                  }else{
                    ipcRenderer.send('show-alert-alert', 'Error', res[2]);
                  }
                  
                }
                
              }
            })
          }
        })
    }
  })

  
}


function startDigiTestGraphMear(){
  h_data_x = [];
  h_data_y = [];
  client.invoke('set_DT_mode','STANDARD_GRAPH_M', (error, res) => {
    if (error){
      console.error(error)
    }else{

      client.invoke('start_DT_mear', (error, res) => {
        if (error){
          console.error(error)
        }else{
          client.invoke('get_DT_graph_data', (error, res) => {
            if (error){
              console.error(error)
            }else{
              console.log(res);
              if (res != undefined){
                if (res[0]){
                  updateGaugeValue('actualHardness', res[2]);
                  h_data_x.push(res[1]);
                  h_data_y.push(res[2]);
                  generateHardnessPlot();
                }else{
                  ipcRenderer.send('show-alert-alert', 'Error', res[3]);
                }
                
              }
              
            }
          })
        }
      })
    }
  })  
}

function stopDigiTestMear(){
  
  client.invoke('stop_DT_mear', (error, res) => {
    if (error){
      console.error(error)
    }else{

    }
  })
}

function getDTSingleData(){
  client.invoke('get_DT_single_data', (error, res) => {
    if (error){
      console.error(error)
    }else{
      console.log(res)
      if (res != null){
        updateGaugeValue('actualHardness', res);
      }
      
    }
  })
}

function regModeSelection(){
  
  let selectMode = $(this).text();
  console.log(selectMode);
  $('#selectedMode').text(selectMode);

};


// DT_conn()
generateHardnessGauge('actualHardness',0,0,100);
generateHardnessPlot()

$('#digiTestGetInfo').on('click',getDigitestInfo);
$('#digiTestGetMode').on('click',getDigitestMode);
$('#digiTestEnableRemote').on('click',setRemote);
$('#digiTestDisableRemote').on('click',setUnRemote);
$('#digiTestSetDuration').on('click',setDuration);
$('#digiTestSetMode').on('click',setMode);
$('#digiTestStartSingle').on('click',startDigiTestMear);
$('#digiTestStartGraph').on('click',startDigiTestGraphMear);
$('#digiTestStop').on('click',stopDigiTestMear);
$('#digiTestGetDisplay').on('click',getDTSingleData);
