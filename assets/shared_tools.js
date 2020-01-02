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
      
    }
  };