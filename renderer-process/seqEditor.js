const { ipcRenderer } = require("electron");
let tools = require('../assets/shared_tools');
let seqRend = require('../assets/seq_render_lib')
let ws;

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
let loop_seq = [];
let test_flow = {
    setup: setup_seq,
    main: [],
    loop: loop_seq,
    teardown: teardown_seq
};
let activePara = null;
let defaultSeqPath = null;
let alwayIncrLoopColorIdx = 0;
let seqPath_under_save = ''

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
        console.log('websocket in seqEditor connected');
        initSeq();
    });

    ws.on('ping', () => {
        ws.send(tools.parseCmd('pong', 'from seqEditor'));
    })

    ws.on('message', function incoming(message) {

        try {
            msg = tools.parseServerMessage(message);
            let cmd = msg.cmd;
            let data = msg.data;
            switch (cmd) {
                case 'ping':
                    ws.send(tools.parseCmd('pong', data));
                    break;
                case 'reply_log_to_db':
                    console.log(data);
                    break;
                case 'reply_load_seq':
                    updateSequence(data)
                    break;
                case 'update_sys_default_config':
                    updateServerSeqFolder(data);
                    break;
                case 'inform_user_seq_differ':
                    ipcRenderer.send('show-option-dialog', data.title, data.reason, 'confirm-save-seq');
                    break;
                case 'reply_server_error':
                    ipcRenderer.send('show-server-error', data.error);
                    break;
                default:
                    console.log('Not found this cmd' + cmd)
            }
        } catch (e) {
            console.error(e)
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

connect();

// **************************************
// generate graph functions
// **************************************

function generateTempTimePlot(xarr = [], yarr = []) {

    const minToFormatedTime = xarr.map(elm => {
        return tools.sec2dt(elm * 60);
    })

    var trace1 = {
        // x: h_data_x,
        type: "scattergl",
        name: `${window.lang_data.lower_letter_temperature}`,
        x: minToFormatedTime,
        y: yarr,
        mode: 'lines+markers',
        line: {
            width: 2,
            color: 'red',

        }
    };

    var data = [trace1];

    var layout = {
        xaxis: {
            type: 'date',
            tickformat: '%H:%M:%S',
            title: `${window.lang_data.lower_letter_time}(H:M:S)`,
            zeroline: false,
            showline: true,
        },
        yaxis: {
            title: `${window.lang_data.lower_letter_temperature}(℃)`
        },
        showlegend: false,
        legend: { "orientation": "h", x: 0, xanchor: 'left', y: 1.2, yanchor: 'top' },
        width: 800,
        height: 280,
        margin: { t: 50, r: 100, l: 50, b: 100, pad: 4 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        autosize: false,
        font: { color: "dimgray", family: "Arial", size: 14 },
        modebar: { orientation: 'h' }
    };

    const config = {
        displaylogo: false,
        modeBarButtonsToRemove: ['toImage', 'lasso2d', 'select2d', 'pan2d', 'zoom2d', 'hoverClosestCartesian', 'hoverCompareCartesian', 'toggleSpikelines'],
        responsive: true
    };

    Plotly.newPlot('tempTime_graph', data, layout, config);
}

function repositionChart() {
    var update = {
        autosize: true,
    };
    if (!$('#tempTime_graph').html() === '') {
        // check if chart has data, if no data, the following function will throw error
        Plotly.relayout('tempTime_graph', update);
    }

    Plotly.relayout('tempTime_graph', update);

}

function reTranslateTempTimeChart() {
    var update = {
        xaxis: {
            title: `${window.lang_data.lower_letter_time}(H:M:S)`,
        },
        yaxis: {
            title: `${window.lang_data.lower_letter_temperature}(℃)`
        },
    };
    Plotly.relayout('tempTime_graph', update);
}

$(window).resize((e) => {
    repositionChart()
})

generateTempTimePlot();
repositionChart();

// **************************************
// general functions
// **************************************

createSeq.addEventListener('click', () => {
    test_flow.main = [];
    initSeq();
})

function updateServerSeqFolder(path) {
    defaultSeqPath = path;
}

openSeq.addEventListener('click', () => {
    loadSeqFromServer()
})

saveSeq.addEventListener('click', () => {
    saveSeqInServer()
})

function updateTempTimeChart() {
    const calObj = seqRend.calcApproxTimeAndTemperature(test_flow, 20);
    generateTempTimePlot(calObj.timeArr, calObj.temperatureArr);
    var layout = {
        annotations: calObj.markers
    };
    Plotly.relayout('tempTime_graph', layout);
    repositionChart();
}

function getActiveli() {
    let hasActive = $('#seqContainer li a').hasClass('ui-accordion-header-active');
    if (hasActive) {
        let currStepID = $('#seqContainer li a.ui-accordion-header-active').parents('li').data('stepid');
        return currStepID + 1;
    } else {
        return test_flow.main.length;
    }

}

function appendSeq(singleStep) {
    let insertID = getActiveli();
    // insert from active item
    test_flow.main.splice(insertID, 0, singleStep);
    seqRend.sortSeq('seqContainer', test_flow.setup, test_flow.main, test_flow.teardown, true);
    makeSortable();
    updateTempTimeChart();

}

function initSeq() {
    seqPath_under_save = ''
    test_flow.setup = seqRend.makeSingleStep('setup', 'setup', [], true, -1);
    test_flow.teardown = seqRend.genTeardownTest();
    seqContainer.innerHTML = seqRend.generateStartSeq(test_flow.setup, true) + seqRend.generateEndSeq(test_flow.teardown, true);
    alwayIncrLoopColorIdx = 0;
    ws.send(tools.parseCmd('run_cmd', tools.parseCmd('ini_seq')));
    ws.send(tools.parseCmd('run_cmd', tools.parseCmd('get_default_seq_path')));
}

function updateServerSeqFolder(path) {
    defaultSeqPath = path;
}

function saveSeqInServer() {
    ipcRenderer.send('save-file-dialog', defaultSeqPath, 'save-seq')
};

function loadSeqFromServer() {
    ipcRenderer.send('open-file-dialog', defaultSeqPath, 'load-seq-editor')
};

ipcRenderer.on('save-seq', (event, path) => {
    console.log(path)
    seqPath_under_save = path;
    ws.send(tools.parseCmd('run_cmd', tools.parseCmd('save_seq', { path: seqPath_under_save, seq: test_flow, force_save: false })));
})

ipcRenderer.on('confirm-save-seq', (event, resp) => {
    console.log(resp)
    if (resp == 0) {
        ws.send(tools.parseCmd('run_cmd', tools.parseCmd('save_seq', { path: seqPath_under_save, seq: test_flow, force_save: true })));
    }

})

ipcRenderer.on('load-seq-editor', (event, path) => {
    seqPath_under_save = path
    ws.send(tools.parseCmd('run_cmd', tools.parseCmd('load_seq', { path: path })));
});

function updateSequence(res) {
    console.log('[res]', res)
    const errorReason = res.error;
    const script = res.script;
    if (errorReason === null) {
        test_flow.setup = script.setup;
        test_flow.main = script.main;
        test_flow.loop = script.loop;
        test_flow.teardown = script.teardown;
        seqRend.sortSeq('seqContainer', test_flow.setup, test_flow.main, test_flow.teardown, true);
        updateTempTimeChart();
    } else {
        ipcRenderer.send('show-warning-alert', window.lang_data.modal_warning_title, errorReason);
    }

}

tempBox.addEventListener('click', () => {
    let step = seqRend.genTempPara();
    appendSeq(step);
})


hardBox.addEventListener('click', () => {
    let step = seqRend.genHardPara();
    appendSeq(step);
})

waitBox.addEventListener('click', () => {
    let step = seqRend.genWaitPara();
    appendSeq(step);
})

loopBox.addEventListener('click', () => {
    let { start, end } = seqRend.genLoopPara(test_flow.main);
    appendSeq(start);
    appendSeq(end);
})

let preArray = [];
let postArray = [];

function makeSortable() {
    $("#seqContainer")
        .sortable({
            axis: "y",
            handle: "a",
            start: function (event, ui) {
                preArray = [];
                let allSteps = document.querySelectorAll('#seqContainer li[data-sortable=true]');
                allSteps.forEach((elem) => {
                    let stepText = elem.innerText;
                    if (stepText !== '') { preArray.push(stepText); }

                });
            },
            beforeStop: function (event, ui) {

            },
            stop: function (event, ui) {

                postArray = [];
                let allSteps = document.querySelectorAll('#seqContainer li[data-sortable=true]');
                allSteps.forEach((elem) => {
                    let stepText = elem.innerText;
                    if (stepText !== '') { postArray.push(stepText); }

                });

                let diffIdx = seqRend.findDiff(preArray, postArray);
                let tempSeq = seqRend.reorderSeq(test_flow.main, diffIdx);
                let result = seqRend.checkLoopValid(tempSeq);
                if (!result.valid) {
                    $("#seqContainer").sortable("cancel");
                } else {
                    test_flow.main = tempSeq;
                    seqRend.sortSeq('seqContainer', test_flow.setup, test_flow.main, test_flow.teardown, true);
                    updateTempTimeChart();
                    closeRightMenu();
                }
                ui.item.children("a").triggerHandler("focusout");
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


function genParasPanel(parain) {
    activePara = parain;
    if (parain === null || parain === undefined) {
        $('#paraContainer').html('');
        closeRightMenu();
    } else {
        let { cat, subitem } = parain;
        let parms = seqRend.genParas(subitem['paras'], true);
        $('#paraContainer').html(parms);
        openRightMenu();
    }
}


$('body').on('click', '#seqContainer > li', function () {
    let dataStepId = $(this).data('stepid');
    if (dataStepId === -1) {
        // genParasPanel(test_flow.setup);
        return;
    }
    if (dataStepId === 9999) {
        genParasPanel(test_flow.teardown);
        return;
    }
    // get step ID
    if (dataStepId >= 0 && dataStepId < 9999) {
        $('#seqContainer > li').each((index, elem) => {
            $(elem).removeClass('active-item');
        });
        $(this).toggleClass('active-item');
        genParasPanel(test_flow.main[dataStepId]);
        return;
    }

});

$('body').on('click', '.enable_list, .disable_list', function () {
    let currStepID = $(this).data('stepid');
    if ($(this).hasClass('enable_list')) {
        $(this).removeClass('enable_list').addClass('disable_list');
        test_flow.main[currStepID]['subitem']['enabled'] = false;
    } else {
        $(this).removeClass('disable_list').addClass('enable_list');
        test_flow.main[currStepID]['subitem']['enabled'] = true;
    }
});

$('body').on('click', '.delete_list', function () {
    let currStepID = $(this).data('stepid');
    if (test_flow.main[currStepID].cat == 'loop') {
        // delete loop start and end together
        let loopid = test_flow.main[currStepID].subitem.paras.filter(item => item.name == 'loop id')[0].value;
        let ids = seqRend.searchLoopStartEndByID(loopid, test_flow.main);
        test_flow.main.splice(ids[1], 1);
        test_flow.main.splice(ids[0], 1);

    } else {
        test_flow.main.splice(currStepID, 1);
    }
    seqRend.sortSeq('seqContainer', test_flow.setup, test_flow.main, test_flow.teardown, true);

});

applyParaBtn.addEventListener('click', () => {
    const tempTestFlow = seqRend.applyChange(paraContainerID = 'paraContainer', test_flow = {...test_flow}, activePara = activePara)
    let calObj = seqRend.calcApproxTimeAndTemperature(tempTestFlow, 20, 1);
    if (calObj.stats.maxTemp>190){
        ipcRenderer.send('show-warning-alert', window.lang_data.modal_warning_title, window.lang_data.exceed_max_temp);
    }else if(calObj.stats.mintemp<-40){
        ipcRenderer.send('show-warning-alert', window.lang_data.modal_warning_title,  window.lang_data.exceed_min_temp);
    }else{
        test_flow = seqRend.applyChange(paraContainerID = 'paraContainer', test_flow = test_flow, activePara = activePara)
        seqRend.sortSeq('seqContainer', test_flow.setup, test_flow.main, test_flow.teardown, true);
        makeSortable();
        updateTempTimeChart();
        ipcRenderer.send('show-info-alert',window.lang_data.modal_info_title, window.lang_data.param_modify_ok);
    }
})

// detect select language
ipcRenderer.on('trigger_tanslate_to_edit_page', (event) => {
    seqContainer.innerHTML = seqRend.refreshSeq(test_flow, true);
    makeSortable();
    reTranslateTempTimeChart();
    console.log('triggerTranslation on edit page')
})