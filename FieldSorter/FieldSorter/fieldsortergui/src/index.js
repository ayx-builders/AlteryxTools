import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import App from './App';


var render = ()=> ReactDOM.render(<App />, document.getElementById('root'));

if ("Alteryx" in window) {
    if (!"Gui" in window.Alteryx) window.Alteryx.Gui = {};
    let gui = window.Alteryx.Gui;


    gui.AfterLoad = function(manager, AlteryxDataItems) {
        let sortedFields = [];
        let config = manager.toolInfo.Configuration.Configuration == null ? {} : manager.toolInfo.Configuration.Configuration;

        for (let prop in config) {
            if (config[prop].hasOwnProperty('text') && config[prop].hasOwnProperty('isPattern')) {
                sortedFields.push({
                    text: config[prop].text,
                    isPattern: config[prop].isPattern === 'true',
                });
            }
        }

        window.FieldSorter = {
            incomingFields: manager.getIncomingFields(),
            sortedFields: sortedFields,
        };

        render();
    };

    gui.GetConfiguration = function() {
        let config = {};
        for (let i = 0; i < window.FieldSorter.sortedFields.length; i++) {
            config["Field" + i] = window.FieldSorter.sortedFields[i];
        }

        console.log(config);

        window.Alteryx.JsEvent(JSON.stringify({
            Event: 'GetConfiguration',
            Configuration: {
                Configuration: config
            },
            Annotation: '',
        }))
    };
} else {
    // populate with sample data
    window.FieldSorter = {
        incomingFields: [
            {strName: "Id"},
            {strName: "Value"},
            {strName: "Category"},
            {strName: "Created On"},
            {strName: "Group1"},
            {strName: "Group2"},
            {strName: "Group3"},
        ],
        sortedFields: [
            {text: "Id", isPattern: false},
            {text: "Group\\d", isPattern: true},
            {text: "SuperDuperDuper DuperLongFieldName", isPattern: false},
        ]
    };
    render();
}
