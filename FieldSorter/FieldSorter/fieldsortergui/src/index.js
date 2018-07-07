import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import App from './App';


var render = ()=> ReactDOM.render(<App />, document.getElementById('root'));

if ("Alteryx" in window) {
    if (!("Gui" in window.Alteryx)) window.Alteryx.Gui = {};
    let gui = window.Alteryx.Gui;


    gui.AfterLoad = function(manager, AlteryxDataItems) {
        let sortedFields = [];
        let config = manager.toolInfo.Configuration.Configuration == null ? {} : manager.toolInfo.Configuration.Configuration;
        let alphabetical = false;

        for (let prop in config) {
            if (config[prop].hasOwnProperty('text') && config[prop].hasOwnProperty('isPattern')) {
                sortedFields.push({
                    text: config[prop].text,
                    isPattern: config[prop].isPattern === 'true',
                    selected: false,
                });
            } else if (prop === 'alphabetical') {
                alphabetical = config[prop].alphabetical === 'true';
            }
        }

        window.FieldSorter = {
            incomingFields: manager.getIncomingFields(),
            sortedFields: sortedFields,
            alphabetical: alphabetical,
        };

        render();
    };

    gui.GetConfiguration = function() {
        let config = {alphabetical: window.FieldSorter.alphabetical};
        for (let i = 0; i < window.FieldSorter.sortedFields.length; i++) {
            let field = window.FieldSorter.sortedFields[i];
            config["Field" + i] = {text: field.text, isPattern: field.isPattern};
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
            {text: "Id", isPattern: false, selected: false},
            {text: "Group\\d", isPattern: true, selected: false},
            {text: "SuperDuperDuper DuperLongFieldName", isPattern: false, selected: false},
        ],
        alphabetical: false,
    };
    render();
}
