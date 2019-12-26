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
    }
  };