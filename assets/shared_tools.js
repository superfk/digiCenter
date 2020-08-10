module.exports = {
    parseServerMessage: function (message) {
        // console.log(message);
        if(typeof(message)=='string'){
          msg = JSON.parse(message)
        }else{
          msg = message;
        }
        return msg;
    },
    random_hsl: function(){
      return "hsla(" + ~~(360 * Math.random()) + "," + "100%,"+ "50%,1)"
    },
    pick_color_hsl: function(alwayIncrLoopColorIdx=0){
      let colorArr = ['red', 'blue', 'green', 'orange', 'brown', 'sienna', 'blueviolet', 'darkcyan', 'hotpink'];
      let ouputColor = colorArr[alwayIncrLoopColorIdx % colorArr.length];
      alwayIncrLoopColorIdx+=1
      return ouputColor
    },
    sec2dt: function (seconds) {
      return new Date(seconds * 1000).toISOString()
    },
    capitalize: (s) => {
      if (typeof s !== 'string') return ''
      return s.charAt(0).toUpperCase() + s.slice(1)
    },
    parseCmd: function (sriptName, data=null) {
      return JSON.stringify({'cmd':sriptName, 'data':data})
    },
    genTraceForHardnessPlot: function(sampleSize=1){
      const sampleArr = new Array(parseInt(sampleSize));
      sampleArr.fill(0)
      const traceArr = sampleArr.map((elm,idx)=>{
        return {
          x: [],
          y: [],
          mode: 'lines+markers',
          type: 'scatter',
          name: `sample${idx+1}`,
          marker: { size: 4},
          line: {
            width: 1
          }
        }
      })
      return traceArr;
    },    
    generateHardnessPlot: function(domElement, sampleSize){
      const traceArr = module.exports.genTraceForHardnessPlot(sampleSize);
      
      const config = {
        displaylogo: false,
        modeBarButtonsToRemove: ['toImage','lasso2d','select2d', 'pan2d','zoom2d','hoverClosestCartesian','hoverCompareCartesian','toggleSpikelines'],
        responsive: true
      };

      var data = traceArr;
      
      var layout = {
        xaxis: {
          title: '℃',
          zeroline: false,
          showline: true
        },
        yaxis: {
          title: 'hardness',
          range: [0, 100],
          zeroline: false,
          showline: true
        },
        width: 400,
        height: 300,
        margin: { t: 80, r: 100, l:50, b: 60, pad: 4},
        autosize: false,
        font: { color: "dimgray", family: "Arial", size: 10}
      };
      
      Plotly.newPlot(domElement, data, layout, config);
    },

    plotly_addNewDataToPlot: function (locationID, xval,yval, y2val=null, sampleId=0){
      if(y2val == null){
        Plotly.extendTraces(locationID, {x: [[xval]],y: [[yval]]}, [sampleId])
      }else{
        Plotly.extendTraces(locationID, {x: [[xval],[xval]],y: [[yval], [y2val]]}, [0,1])
      }
    },
    plotly_DeleteDataFromPlot: function (locationID){
      try{
        var data_update = {
          x:[],
          y:[]
        };
        Plotly.plot(locationID, data_update);
      }catch(err){
        console.log('no trace in plot')
      }
    },
    plotly_addAnnotation: function (locationID, textin, locateX, locateY, markerArr=[]){
      let ann = {
        x: locateX,
        y: locateY,
        xref: 'x',
        yref: 'y',
        text: textin,
        showarrow: true,
        arrowhead: 3,
        ax: 0,
        ay: -40
      };
    
      markerArr.push(ann)
    
      var layout = {
        annotations: markerArr
      };
    
      Plotly.relayout(locationID, layout);
    },

    changeStatus: function(html_elem, status=null){
      switch (status){
        case 0:
          $(html_elem).removeClass('idct-status-conn idct-status-running');
          break;
        case 1:
          $(html_elem).removeClass('idct-status-conn idct-status-running').addClass('idct-status-conn');
          break;
        case 2:
          $(html_elem).removeClass('idct-status-conn idct-status-running').addClass('idct-status-running');
          break;
        default:
          
      }
    },
    
    updateNumIndicator: function (html_elem, value=null, precision=1){
      // update values
      html_elem.innerText = value==null?'--':value.toFixed(precision);
    },

    updateStatusIndicator: function (html_elem, status=null, langForConn='connected', langForDisonn='disconnected', langForRunning='running'){
      let preStatusCode = $(html_elem).hasClass('idct-status-conn') ? 1 : 0;
      preStatusCode = $(html_elem).hasClass('idct-status-running') ? 2 : preStatusCode ;

      // update status
      // 0: disconnect, 1: ready, 2: running
      let stausTxt = '';
      switch (status){
        case 0:
          stausTxt = langForDisonn;
          break;
        case 1:
          stausTxt = langForConn;
          break;
        case 2:
          stausTxt = langForRunning;
          break;
        default:
          stausTxt = '';
      }

      if (preStatusCode !== status){
        html_elem.innerText = stausTxt
        // update indicator color
        module.exports.changeStatus(html_elem, status);
      }
      
    }
    
  };