const {ipcRenderer} = require("electron");
const app = require('electron').remote.app
const zerorpc = require("zerorpc");
const client = new zerorpc.Client({ timeout: 60, heartbeatInterval: 60000 });
// create zerorpc instance
client.connect("tcp://127.0.0.1:4242");

// variable define
// digitest
var h_data_x = []
var h_data_y = []
var datapoints_x = [];
var datapoints_y = [];

// generate graph
function generateHardnessVsTempPlot(){
  
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
      width: 600,
      height: 200
    };
    
    Plotly.newPlot('hardnessVStemp_graph', data, layout);
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
      width: 600,
      height: 200
    };
    
    Plotly.newPlot('hardness_graph', data, layout);
  }

// generate gauge
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

// seq container
openSeq.addEventListener('click', ()=>{
    loadSeqFromServer()
})

ipcRenderer.on('load-seq', (event, path) => {

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

//   init
generateHardnessVsTempPlot()
generateHardnessPlot()
generateGauge('actualTempGauge', 23, -40, 200);
generateGauge('actualHumGauge', 50, 0, 100);