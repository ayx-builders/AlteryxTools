import React, { Component } from 'react';
import 'react-beautiful-dnd';
import './App.css';
import Table from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableRow from '@material-ui/core/TableRow';
import TextField from '@material-ui/core/TextField';
import Checkbox from '@material-ui/core/Checkbox';


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
                    <Table>
                        <TableBody>
                            {window.FieldSorter.sortedFields.map((sortField, index) => {
                            return <SortRow key={index} sortField={sortField} />
                            })}
                        </TableBody>
                    </Table>
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
        return <TableRow style={{height: 20}}>
            <TableCell className="SortFieldCheckbox" component="th" scope="row">
                <Checkbox className="SortFieldCheckbox" />
            </TableCell>
            <TableCell className="SortFieldText">
                <TextField fullWidth={true} type="text" value={this.props.sortField.text} onChange={this.textChanged} inputProps={{disableUnderline: true}} />
            </TableCell>
            <TableCell className="SortFieldCheckbox">
                <Checkbox className="SortFieldCheckbox" checked={this.props.sortField.isPattern} onChange={this.isPatternChanged} />
            </TableCell>
        </TableRow>;
    }
}

export default App;
