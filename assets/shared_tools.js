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

    capitalize: (s) => {
      if (typeof s !== 'string') return ''
      return s.charAt(0).toUpperCase() + s.slice(1)
    },
    
    parseCmd: function (sriptName, data=null) {
      return JSON.stringify({'cmd':sriptName, 'data':data})
    },
    

    plotly_addNewDataToPlot: function (locationID, xval,yval, y2val=null){
      if(y2val == null){
        Plotly.extendTraces(locationID, {x: [[xval]],y: [[yval]]}, [0])
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
      let preState = false
      let curState = false
      if (status){
        $(html_elem).removeClass('idct-status-conn').addClass('idct-status-conn');
      }else{
        $(html_elem).removeClass('idct-status-conn');
      }
    },
    
    updateNumIndicator: function (html_elem, value=null, pres=1){
      // update values
      html_elem.innerText = value==null?'--':value.toFixed(pres);
    },

    updateStatusIndicator: function (html_elem, status=null){
      // update status
      html_elem.innerText = status==false?'disconnected':'connected';
      // update indicator color
      module.exports.changeStatus(html_elem, status);
    }
    
  };