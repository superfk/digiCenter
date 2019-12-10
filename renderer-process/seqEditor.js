const {ipcRenderer} = require("electron");
const app = require('electron').remote.app
const zerorpc = require("zerorpc");
const client = new zerorpc.Client({ timeout: 60, heartbeatInterval: 60000 });
// create zerorpc instance
client.connect("tcp://127.0.0.1:4242");


const mainContainer = document.getElementById('mainContainer');
const seqContainer = document.getElementById('seqContainer');
const tempBox = document.getElementById('tempBox');
const hardBox = document.getElementById('hardBox');
const waitBox = document.getElementById('waitBox');
const loopBox = document.getElementById('loopBox');
const subprogBox = document.getElementById('subprogBox');
const applyParaBtn = document.getElementById('applyParaPanel');
const createSeq = document.getElementById('create_seq');
const openSeq = document.getElementById('open_seq');
const saveSeq = document.getElementById('save_seq');


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
let activePara = null;
let defaultSeqPath = null;
// 
// singleStep = {
    // id: 0,
    // cat: 'temperature', // 'hardness' | 'waiting' | 'action' 
    // subitem: {
    //  item: 'rampup', //'rampdown' 'keep' | 'measure' | 'sec' 'min' 'hour' 'tempInRange' | 'fanOff' 'fanOn' 'rotate' 'DO_out'
    //     paras: [
    //         {
    //             name: 'temperature',
    //             value: '20',
    //             unit: 'deg'
    //             type: 'number'       
    //         },
    //         {
    //             name: 'temperature',
    //             value: '20',
    //             unit: 'deg',
    //             type: 'number'
    //         },{
    //             name: 'method',
    //             value: 'shoreA',
    //             unit: '',
    //             type: 'select',
    //             options: 'shoreA,shore0'
    //     ]
    // }
    // 
// }

function parseCmd(sriptName, data=null){
    return JSON.stringify({'scriptName':sriptName, 'data':data})
}

createSeq.addEventListener('click', ()=>{
    seq = [];
    initSeq();
})

openSeq.addEventListener('click', ()=>{
    loadSeqFromServer()
})

saveSeq.addEventListener('click', ()=>{
    saveSeqInServer()
})

function random_rgb() {
    var r = Math.floor(Math.random()*256);          // Random between 0-255
    var g = Math.floor(Math.random()*256);          // Random between 0-255
    var b = Math.floor(Math.random()*256);          // Random between 0-255
    var rgb = 'rgb(' + r + ',' + g + ',' + b + ')'; // Collect all to a string
    return rgb;
}

function random_hsl(){
    return "hsla(" + ~~(360 * Math.random()) + "," + "100%,"+ "50%,1)"
}

const capitalize = (s) => {
    if (typeof s !== 'string') return ''
    return s.charAt(0).toUpperCase() + s.slice(1)
  }

function sortSeq(){
    let middleSeqs =  generateSeq();
    $('#seqContainer').html(generateStartSeq() + middleSeqs + generateEndSeq())
    // $( "#seqContainer" ).accordion('refresh');
    // $( "#seqContainer" ).accordion({
    //     header: "> li > a",
    //     collapsible: true,
    //     heightStyle: "content",
    //     active: false
    // });
    // seqContainer.innerHTML = generateStartSeq() + middleSeqs + generateEndSeq();
    makeSortable();
    test_flow.main = seq;
}

function getActiveli(){
   let hasActive = $('#seqContainer li a').hasClass('ui-accordion-header-active');
   if(hasActive){
        let currStepID = $('#seqContainer li a.ui-accordion-header-active').parents('li').data('stepid');
        return currStepID+1;
    }else{
        return seq.length;
    }
    
}

function appendSeq(singleStep){
    let insertID = getActiveli();
    // insert from active item
    seq.splice(insertID,0,singleStep);
    test_flow.main = seq;
    sortSeq();
    
}
 

function makeSingleStep(cat, subitem, paras, enabled=true, stepid=0) {

    let unitStep = {
        id: stepid,
        cat: cat, // 'hardness' | 'waiting' | 'action'
        subitem: {
            item: subitem, //'rampdown' 'keep' | 'measure' | 'sec' 'min' 'hour' 'tempInRange' | 'fanOff' 'fanOn' 'rotate' 'DO_out'
            paras: paras,
            enabled: enabled
        }
        
    }
    return unitStep;
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

function genDeleteIcon(stepID){
    let iconset = 'icon delete_list';
    return `<i data-stepid=${stepID} class="${iconset} w3-right w3-margin-right"></i>`
}

function genLoopIndicator(start, end){
    if(start<0 || end<0){
        return null;
    }
    // ignore settup step
    start+=1;
    end+=1;
    $('.mainSeqContainer > ul > li').each((index,item)=>{
        $(item).removeClass('loop loopStart loopEnd');
        if(index==start){
            $(item).addClass('loop loopStart');
        }else if (index > start && index < end){
            $(item).addClass('loop');
        }else if (index===end){
            $(item).addClass('loop loopEnd');
        }else{
            
        }
    })
    
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
        let en = subitem['enabled'];
        let stepParaText = genShortParaText(cat,subitem);
        curstr += `
        <li data-stepid=${index} data-sortable=true class='w3-bar'>
            
                <a href="#" style="font-size:14px;width:470px;" class='w3-bar-item'>
                    ${genIconByCat(cat,subitem['paras'])}${stepTitles[index]}${stepParaText}
                </a>
                <div class='w3-bar-item w3-right' style='padding:2px;margin:0px;'>${genDeleteIcon(index)}</div>
                <div class='w3-bar-item w3-right' style='padding:2px;margin:0px;'>${genEnableIcon(index,en)}</div>
        </li>
        `;
    });
    return curstr;
}



function genSetupTest(){
    let paras= [
        {
            name: 'Number of samples',
            value: '25',
            unit: '',
            type: 'number',
            readOnly: false
        },
        {
            name: 'Number of test position',
            value: '3',
            unit: '',
            type: 'number',
            readOnly: false
        },
        {
            name: 'Number of test cycle',
            value: '10',
            unit: '',
            type: 'number',
            readOnly: false
        }
    ]
    setup_seq = makeSingleStep('setup','batch',paras, true, -1);
    test_flow.setup = setup_seq;
    // let parms = genParas(setup_seq['subitem']['paras']);
    // return `<div style='margin:0px;padding:5px;'><ul class='w3-ul'>${parms}</ul></div>`
}

function generateStartSeq() {
    genSetupTest();
    let curstr = `
    <li>
        <a href="#" style="font-size:14px;color:#fff;background-color:#1abc9c;width:100%"><i class="far fa-play-circle w3-margin-right fa-lg"></i>Sequence Setup</a>
        
    </li>
    `;
    return curstr;
}

function genTeardownTest(){
    let paras= [
        {
            name: 'Motor Home',
            value: 'true',
            unit: '',
            type: 'bool',
            readOnly: false
        },
        {
            name: 'Turn off chamber',
            value: 'true',
            unit: '',
            type: 'bool',
            readOnly: false
        }
    ]
    teardown_seq = makeSingleStep('teardown','batch', paras, true, 9999);
    test_flow.teardown = teardown_seq;
    // let parms = genParas(teardown_seq['subitem']['paras']);
    // return `<div style='margin:0px;padding:5px;'><ul class='w3-ul'>${parms}</ul></div>`
}

function generateEndSeq() {
    genTeardownTest();
    let curstr = `
    <li>
        <a href="#" style="font-size:14px;color:#fff;background-color:#d35400"><i class="far fa-stop-circle w3-margin-right fa-lg"></i>Sequence Teardown</a>
        
    </li>
    `;
    return curstr;
}

function initSeq() {
    seqContainer.innerHTML = generateStartSeq() + generateEndSeq();
    client.invoke('run_cmd',parseCmd('ini_seq'),(err, res)=>{
        if(err){
            console.error(err)
        }else{
            console.log(res)
        }
    });
    
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

function saveSeqInServer(){
    client.invoke('run_cmd',parseCmd('get_default_seq_path'),(err, resObj)=>{
        if(err){
            console.error(err)
        }else{
            logResponse(resObj);
            let {error,res} = resObj;
            if(!error){
                // do something
                defaultSeqPath = res;
                ipcRenderer.send('save-file-dialog',defaultSeqPath,'save-seq')
            }
        }
    });
    
};
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

ipcRenderer.on('save-seq', (event, path) => {
    client.invoke('run_cmd',parseCmd('save_seq',{path: path,seq: test_flow}),(err, resObj)=>{
        if(err){
            console.error(err)
        }else{
            logResponse(resObj);
            let {error,res} = resObj;
            if(!error){
                // do something
            }
        }
    });
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

tempBox.addEventListener('click', () =>{
    let paras= [
        {
            name: 'target temperature',
            value: '20',
            unit: '&#8451',
            type: 'number',
            readOnly: false
        },
        {
            name: 'slope',
            value: '5',
            unit: 'K/min',
            type: 'number',
            readOnly: false
        }
    ]
    // UIkit.modal('#parasModal').show();
    let step = makeSingleStep('temperature', 'ramp', paras, true);
    appendSeq(step);
    
})


hardBox.addEventListener('click', () =>{
    let paras= [
        {
            name: 'port',
            value: 'COM3',
            unit: '',
            type: 'text',
            readOnly: false
        },
        {
            name: 'method',
            value: 'shoreA',
            unit: '',
            type: 'select',
            options: 'shoreA,shore0',
            readOnly: false
        },
        {
            name: 'mode',
            value: 'STANDARD_M',
            unit: '',
            type: 'select',
            options: 'STANDARD_M,STANDARD_M_GRAPH',
            readOnly: false
        },
        {
            name: 'measuring time',
            value: '5',
            unit: 'sec',
            type: 'number',
            readOnly: false
        }
    ]
    let step = makeSingleStep('hardness', 'measure', paras);
    appendSeq(step);
        
})

waitBox.addEventListener('click', () =>{
    let paras= [
        {
            name: 'conditioning time',
            value: '5',
            unit: 'min',
            type: 'number',
            readOnly: false
        }
    ]
    let step = makeSingleStep('waiting', 'time', paras);
    appendSeq(step);

})

loopBox.addEventListener('click', () =>{
    let stepTitles = genStepTitles();
    let stepTitlesStr = stepTitles.join(',');
    let loopID = Math.floor(Math.random() * 100000000);
    let loopColor = random_hsl();
    let loop_counts = 5;
    let paras= [
        {
            name: 'loop id',
            value: loopID,
            unit: '',
            type: 'number',
            readOnly: true
        },               
        {
            name: 'loop counts',
            value: loop_counts,
            unit: '',
            type: 'number'
        },
        {
            name: 'loop color',
            value: loopColor,
            unit: '',
            type: 'text',
            readOnly: true
        }
    ]
    let step = makeSingleStep('loop', 'loop start', paras);
    appendSeq(step);

    paras= [
        {
            name: 'stop on',
            value: loop_counts,
            unit: '',
            type: 'number',
            readOnly: true
        },
        {
            name: 'loop id',
            value: loopID,
            unit: '',
            type: 'number',
            readOnly: true
        },
        {
            name: 'loop color',
            value: loopColor,
            unit: '',
            type: 'text',
            readOnly: true
        }
    ];
        
    step = makeSingleStep('loop', 'loop end', paras);
    appendSeq(step);
    

})

subprogBox.addEventListener('click', () =>{
    let paras= [
        {
            name: 'path',
            value: 'C:\\test.prgo',
            unit: '',
            type: 'text',
            readOnly: false
        }
    ]
    let step = makeSingleStep('subprog', 'program config', paras);
    appendSeq(step);

})

initSeq();

let preArray = [];
let postArray = [];


function findDiff(oldArr, newArr) {
    let diffIndexes = [];
    newArr.forEach((elem,idx, array) => {
        let newIdx = oldArr.indexOf(elem,0);
        diffIndexes.push(newIdx);
    });
    return diffIndexes;
};

function reorderSeq(newOrder) {
    let newSeq = [];
    let newMainSeqIdx = newOrder.slice(0);
    newMainSeqIdx.forEach((elem, idx)=>{
        newSeq.push(seq[elem]); 
    })
    return newSeq;
}

function checkLoopValid(seqin)
{
    let totalInvalids = [];
    let idxPairs = [];
    let valid = false
    let loopStartCollection = seqin.filter(item=>item.subitem.item=='loop start');
    // check if start greater than end
    loopStartCollection.forEach((item,index)=>{
        let paras = item.subitem.paras;
        paras.forEach((item,index)=>{
            if(item.name=='loop id'){
                let lpID = item.value;
                let ids = searchLoopStartEndByID(lpID,seqin);
                let startidx = ids[0];
                let endidx = ids[1];
                idxPairs.push({'id':lpID, 'start': startidx, 'end':endidx})
                if (startidx>endidx){
                    totalInvalids.push({'valid':false, 'loopid':lpID})
                }
            }
        })        
    })
    
    // check if loop overlap
    idxPairs.sort(function (a, b) {
        return a.idx - b.idx;
      });
    
    function checkValid(valid) {
        return valid;
    }
    console.log('start and end index: ')
    console.log(idxPairs)
    let validsCollection = [];
    idxPairs.forEach((item,index,array)=>{
        let uut = item;
        let copyArr = [...array];
        let valids=[];
        copyArr.forEach((elem, idx)=>{
            let otheruut = elem;
            if(otheruut.start<uut.start && otheruut.end<uut.end && otheruut.end>uut.start ){
                valids.push(false);
            }else if(otheruut.start>uut.start && otheruut.end>uut.end && otheruut.start<uut.end){
                valids.push(false);
            }else{
                valids.push(true);
            }
        })
        validsCollection.push(valids.every(checkValid));
    })
    if(totalInvalids.length>0){
        return {'valid':false, 'loopid':totalInvalids[0]['loopid']}
    }else if (!validsCollection.every(checkValid)){
        return {'valid':false, 'loopid':null}
    }else{
        return {'valid':true, 'loopid':null}
    }
}

function makeSortable(){
    $( "#seqContainer" )
      .sortable({
        axis: "y",
        handle: "a",
        start: function(event, ui) {
            preArray = [];
            let allSteps = document.querySelectorAll('li[data-sortable=true]');
            allSteps.forEach((elem)=>{
                preArray.push(elem.innerText);
            });
        },
        beforeStop: function( event, ui ) {
           
        },
        stop: function( event, ui ) {

            postArray = [];
            let allSteps = document.querySelectorAll('li[data-sortable=true]');
            allSteps.forEach((elem)=>{
                postArray.push(elem.innerText);
            });

            let diffIdx = findDiff(preArray,postArray);
            let tempSeq = reorderSeq(diffIdx);
            let result = checkLoopValid(tempSeq);
            if(!result.valid){
                $( "#seqContainer" ).sortable( "cancel" );
            }else{

                seq = tempSeq;
                sortSeq();
                closeRightMenu();

            }
            

            // IE doesn't register the blur when sorting
            // so trigger focusout handlers to remove .ui-state-focus
            ui.item.children( "a" ).triggerHandler( "focusout" );
        
            
        }
      });
}

makeSortable();

function openRightMenu() {
    document.getElementById("rightMenu").style.display = "block";
}

function closeRightMenu() {
    document.getElementById("rightMenu").style.display = "none";
}

$('#closeParaPanel').on('click', () => {
    closeRightMenu();
})


function genParasPanel(parain){
    activePara = parain;
    if (parain === null || parain === undefined){
        $('#paraContainer').html('');
        closeRightMenu();
    }else{
        let {cat, subitem} = parain;
        let parms = genParas(subitem['paras'], true);
        $('#paraContainer').html(parms);
        openRightMenu();
    }
}

function searchLoopStartEndByID(loopid, dummyseq=null){
    if(dummyseq==null){
        dummyseq = seq;
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


$('body').on('click', '#seqContainer > li > a',function() {
    let nh = this.innerText;
    var regexp = '([0-9]+)';
    var matches_array = nh.match(regexp);
    // get step ID
    if(matches_array !== null){
        let seqID = matches_array[0];
        $('#seqContainer > li').each((index,elem)=>{
            $(elem).removeClass('active-item');
        });
        $(this).parents('li').toggleClass('active-item');
        let curStep = seq[seqID-1];
        let cat = curStep.cat;
        let paras = curStep.subitem.paras;
        let loopStartID=seqID;
        let loopEndID=seqID;
        if(cat=='loop'){
            let loopid = paras.filter(item=>item.name=='loop id')[0].value;
            let ids = searchLoopStartEndByID(loopid);
            genLoopIndicator(ids[0],ids[1]);
        }else{
            genLoopIndicator(-1,-1);
        }
        
        genParasPanel(seq[seqID-1]);
    }else{
        
        var regexp = '(Setup)';
        matches_array = nh.match(regexp);
        console.log(matches_array)
        if (matches_array !== null){
            genParasPanel(test_flow.setup);
        }else{
            genParasPanel(test_flow.teardown);
        }
    }

});

$('body').on('click', '.enable_list, .disable_list', function() {
    let currStepID = $(this).data('stepid');
    if($(this).hasClass('enable_list')){
        $(this).removeClass('enable_list').addClass('disable_list');
        seq[currStepID]['subitem']['enabled']=false;
    }else{
        $(this).removeClass('disable_list').addClass('enable_list');
        seq[currStepID]['subitem']['enabled']=true;
    }
});

$('body').on('click', '.delete_list', function() {
    let currStepID = $(this).data('stepid');
    if(seq[currStepID].cat=='loop'){
        // delete loop start and end together
        let loopid = seq[currStepID].subitem.paras.filter(item=>item.name=='loop id')[0].value;
        let ids = searchLoopStartEndByID(loopid);
        seq.splice(ids[1], 1);
        seq.splice(ids[0], 1);
        
    }else{
        seq.splice(currStepID, 1);
    }
    sortSeq();
    
});


applyParaBtn.addEventListener('click',()=>{
    let {id, cat, subitem} = activePara;
    let {item, paras} = subitem;
    let paraCollection = null;
    if (cat === 'temperature'){
        paraCollection = $('#paraContainer input');
        let newTemp = paraCollection[0].value;
        let newSlope = paraCollection[1].value;
        seq[id].subitem.paras[0].value = newTemp;
        seq[id].subitem.paras[1].value = newSlope;
    }else if (cat === 'hardness'){
        paraCollection = $('#paraContainer input');
        let newCOM = paraCollection[0].value;
        let newTime = paraCollection[1].value;
        seq[id].subitem.paras[0].value = newCOM;
        seq[id].subitem.paras[3].value = newTime;
        paraCollection = $('#paraContainer select');
        let newMethod = $(paraCollection[0]).find('option:selected').text();
        let newMode = $(paraCollection[1]).find('option:selected').text();
        seq[id].subitem.paras[1].value = newMethod;
        seq[id].subitem.paras[2].value = newMode;
    }else if (cat === 'waiting'){
        paraCollection = $('#paraContainer input');
        let newCondTime = paraCollection[0].value;
        seq[id].subitem.paras[0].value = newCondTime;
    }else if (cat === 'loop'){
        let loopid = paras.filter(item=>item.name=='loop id')[0].value;
        let ids = searchLoopStartEndByID(loopid);
        let endloopindex = ids[1]
        paraCollection = $('#paraContainer input');
        let newLoopCounts = paraCollection[1].value;
        seq[id].subitem.paras[1].value = newLoopCounts;
        seq[endloopindex].subitem.paras[0].value = newLoopCounts;
    }else if (cat === 'subprog'){
        paraCollection = $('#paraContainer input');
        let newPath = paraCollection[0].value;
        seq[id].subitem.paras[0].value = newPath;
    }

    sortSeq();

})