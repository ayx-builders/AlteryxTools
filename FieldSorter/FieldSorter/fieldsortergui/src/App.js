import React, { Component } from 'react';
import 'react-beautiful-dnd';
import './App.css';
import { withStyles } from '@material-ui/core/styles';
import Table from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';

class App extends Component {


    render() {
        var displaySize = Math.min(20,window.FieldSorter.incomingFields.length);

        return (
            <div className="App">
                <div>Unsorted fields</div>
                <div>
                    <select className="UnmatchedFields" multiple="multiple" size={displaySize}>
                        {window.FieldSorter.incomingFields.map(item => {
                            return <option key={item.strName}>{item.strName}</option>;
                        })}
                    </select>
                </div>
                <div>
                    <button className="AddButton" type="button" onClick={()=>console.log('Click!')}>Add</button>
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

    render(){
        return <TableRow>
            <TableCell component="th" scope="row">
                <form>
                <input className="SortFieldText" type="text" value={this.props.sortField.text} onChange={(event)=>{
                    this.props.sortField.text = event.target.value;
                    this.forceUpdate();
                }} />
                    <input type="checkbox" checked={this.props.sortField.isPattern} onChange={()=>{
                        this.props.sortField.isPattern = !this.props.sortField.isPattern;
                        this.forceUpdate();
                    }} />
                </form>
            </TableCell>
        </TableRow>;
    }
}

export default App;
