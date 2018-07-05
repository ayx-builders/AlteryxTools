import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import App from './App';


var render = ()=> ReactDOM.render(<App />, document.getElementById('root'));

if ("Alteryx" in window) {
    var gui = window.Alteryx.Gui;

    gui.AfterLoad = function(manager, AlteryxDataItems) {
        var config = manager.toolInfo.Configuration == null ? [] : manager.toolInfo.Configuration.SortedFields;

        window.FieldSorter = {
            incomingFields: manager.getIncomingFields(),
            sortedFields: config,
        };

        render();
    };

    gui.GetConfiguration = function() {
        window.Alteryx.JsEvent(JSON.stringify({
            Event: 'GetConfiguration',
            Configuration: {
                SortedFields: window.FieldSorter.sortedFields
            },
            Annotation: ''
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
