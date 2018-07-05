import React, { Component } from 'react';
import 'react-beautiful-dnd';
import './App.css';
import Paper from "@material-ui/core/es/Paper/Paper";
import SvgIcon from '@material-ui/core/SvgIcon';

function getUnmatchedFields() {
    let unmatchedFields = [];
    let incomingFields = window.FieldSorter.incomingFields;
    let sortedFields = window.FieldSorter.sortedFields;

    for (let iIn = 0; iIn < incomingFields.length; iIn++) {
        let isFound = false;

        for (let iSorted = 0; iSorted < sortedFields.length; iSorted++) {
            let matcher = sortedFields[iSorted];
            let searchFor = matcher.isPattern ? new RegExp("^" + matcher.text + "$", "i") : matcher.text;

            if (incomingFields[iIn].strName.search(searchFor) >= 0) {
                isFound = true;
                break;
            }
        }

        if (!isFound) {
            unmatchedFields.push(incomingFields[iIn]);
        }
    }
    return unmatchedFields;
}

class App extends Component {
    constructor(props) {
        super(props);
        this.addUnsorted = this.addUnsorted.bind(this);
    }

    unmatchedFields = [];

    addUnsorted() {
        let unsorted = document.getElementById("Unsorted");

        for (let i = 0; i < unsorted.options.length; i++) {
            let option = unsorted.options[i];
            if (option.selected) {
                window.FieldSorter.sortedFields.push({
                    text: option.text,
                    isPattern: false
                });
            }
        }

        this.unmatchedFields = getUnmatchedFields();
        this.forceUpdate();
    };

    render() {
        this.unmatchedFields = getUnmatchedFields();

        let displaySize = Math.min(20,window.FieldSorter.incomingFields.length);

        return (
            <div className="App">
                <div>Unsorted fields</div>
                <div>
                    <select id="Unsorted" className="UnmatchedFields" multiple="multiple" size={displaySize}>
                        {this.unmatchedFields.map(item => {
                            return <option key={item.strName}>{item.strName}</option>;
                        })}
                    </select>
                </div>
                <div>
                    <button className="AddButton" type="button" onClick={this.addUnsorted} >Add</button>
                </div>
                <div className="SortedFields">
                    {window.FieldSorter.sortedFields.map((sortField, index) => {
                        return <SortRow key={index} sortField={sortField} />
                    })}
                </div>
            </div>
        );
    }
}

class SortRow extends Component {
    constructor(props) {
        super(props);
        this.isPatternChanged = this.isPatternChanged.bind(this);
        this.textChanged = this.textChanged.bind(this);
    }

    isPatternChanged() {
        this.props.sortField.isPattern = !this.props.sortField.isPattern;
        this.forceUpdate();
    }

    textChanged(event) {
        this.props.sortField.text = event.target.value;
        this.forceUpdate();
    }

    render(){
        return <Paper className="SortedField" elevation={0} onClick={()=>console.debug("Click!")}>
            <DragHandle />
            <div className='SortFieldCell IsPatternIndicator'>{this.props.sortField.isPattern ? '(.)*' : ''}</div>
            <div className='SortFieldCell SortFieldText' >{this.props.sortField.text}</div>
        </Paper>
    }
}

class DragHandle extends Component {
    render() {
        return <SvgIcon className="SortFieldCell GrabHandle">
            <path d="M11 18c0 1.1-.9 2-2 2s-2-.9-2-2 .9-2 2-2 2 .9 2 2zm-2-8c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0-6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm6 4c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
        </SvgIcon>;
    }
}

export default App;
