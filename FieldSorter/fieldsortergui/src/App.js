import React, { Component } from 'react';
import './App.css';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import ReactModal from 'react-modal';

const noValueError = 'A value must be provided';
const dupValueError = 'That value already exists';

const reorder = (list, startIndex, endIndex) => {
    const result = Array.from(list);
    const [removed] = result.splice(startIndex, 1);
    result.splice(endIndex, 0, removed);

    return result;
};

function getUnmatchedFields() {
    let unmatchedFields = [];
    let incomingFields = window.FieldSorter.incomingFields;
    let sortedFields = window.FieldSorter.sortedFields;

    for (let iIn = 0; iIn < incomingFields.length; iIn++) {
        let isFound = false;

        for (let iSorted = 0; iSorted < sortedFields.length; iSorted++) {
            let matcher = sortedFields[iSorted];

            if (matcher.isPattern) {
                if (incomingFields[iIn].strName.search(new RegExp("^" + matcher.text + "$", "i")) >= 0) {
                    isFound = true;
                    break;
                }
            } else {
                if (incomingFields[iIn].strName === matcher.text){
                    isFound = true;
                    break;
                }
            }
        }

        if (!isFound) {
            unmatchedFields.push(incomingFields[iIn]);
        }
    }
    return unmatchedFields;
}

function isDuplicate(str) {
    let isDuplicate = false;
    for (let i = 0; i < window.FieldSorter.sortedFields.length; i++){
        if (str === window.FieldSorter.sortedFields[i].text){
            isDuplicate = true;
            break;
        }
    }
    return isDuplicate;
}

class App extends Component {
    constructor(props) {
        super(props);
        this.addUnsorted = this.addUnsorted.bind(this);
        this.onDragEnd = this.onDragEnd.bind(this);
        this.selectAllSorted = this.selectAllSorted.bind(this);
        this.selectNoneSorted = this.selectNoneSorted.bind(this);
        this.deleteSorted = this.deleteSorted.bind(this);
        this.selectAllUnmatched = this.selectAllUnmatched.bind(this);
        this.selectNoneUnmatched = this.selectNoneUnmatched.bind(this);
        this.addSortedManually = this.addSortedManually.bind(this);
        this.textboxEnterKeyHandler = this.textboxEnterKeyHandler.bind(this);
        this.alphabeticalChanged = this.alphabeticalChanged.bind(this);
        this.refreshUnmatched = this.refreshUnmatched.bind(this);
    }

    unmatchedFields = [];
    addErrorVisibility = 'hidden';
    errorText = '';

    refreshUnmatched() {
        this.unmatchedFields = getUnmatchedFields();
        this.forceUpdate();
    }

    alphabeticalChanged() {
        window.FieldSorter.alphabetical = !window.FieldSorter.alphabetical;
        this.forceUpdate();
    }

    textboxEnterKeyHandler(event) {
        if (event.keyCode === 13) {
            event.preventDefault();
            this.addSortedManually();
        }
    }

    addSortedManually(){
        let textbox = document.getElementById("NewSortedText");
        let isPattern = document.getElementById("NewSortedIsPattern");
        let value = textbox.value;

        if (value === ''){
            this.errorText = noValueError;
            this.addErrorVisibility = 'visible';
        } else if (isDuplicate(value)) {
            this.errorText = dupValueError;
            this.addErrorVisibility = 'visible';
        } else {
            this.addErrorVisibility = 'hidden';
            window.FieldSorter.sortedFields.push({
                text: textbox.value,
                isPattern: isPattern.checked,
                selected: false,
            });
            textbox.value = '';
        }

        this.forceUpdate();
    }

    selectAllUnmatched() {
        let unsorted = document.getElementById("Unsorted");

        for (let i = 0; i < unsorted.options.length; i++) {
            unsorted.options[i].selected = true;
        }
    }

    selectNoneUnmatched() {
        let unsorted = document.getElementById("Unsorted");

        for (let i = 0; i < unsorted.options.length; i++) {
            unsorted.options[i].selected = false;
        }
    }

    selectAllSorted() {
        for (let i = 0; i < window.FieldSorter.sortedFields.length; i++) {
            window.FieldSorter.sortedFields[i].selected = true;
        }
        this.forceUpdate();
    }

    selectNoneSorted() {
        for (let i = 0; i < window.FieldSorter.sortedFields.length; i++) {
            window.FieldSorter.sortedFields[i].selected = false;
        }
        this.forceUpdate();
    }

    deleteSorted() {
        for (let i = window.FieldSorter.sortedFields.length - 1; i >= 0; i--) {
            if (window.FieldSorter.sortedFields[i].selected) {
                window.FieldSorter.sortedFields.splice(i, 1);
            }
        }

        this.unmatchedFields = getUnmatchedFields();
        this.forceUpdate();
    }

    onDragEnd(result) {
        // dropped outside the list
        if (!result.destination) {
            return;
        }

        window.FieldSorter.sortedFields = reorder(
            window.FieldSorter.sortedFields,
            result.source.index,
            result.destination.index,
        );

        this.forceUpdate();
    }

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

        let displaySize = 10;

        return (
            <div className="App">
                <table>
                    <tbody>
                    <tr>
                        <td>
                        <input style={{width: 13}} type='checkbox' checked={window.FieldSorter.alphabetical} onChange={this.alphabeticalChanged} />
                        </td>
                    <td>
                        Regex matches and unsorted fields are sorted alphabetically
                    </td>
                    </tr>
                    </tbody>
                </table>
                {
                    this.unmatchedFields.length > 0 ?
                        <div>
                            <div className='SectionMargin'>Unsorted fields</div>
                            <div>
                                <button className="CoreButton EndButton" type="button" onClick={this.selectAllUnmatched} >All</button>
                                <button className="CoreButton MiddleButton" type="button" onClick={this.selectNoneUnmatched} >None</button>
                                <button className="CoreButton EndButton" type="button" onClick={this.addUnsorted} >Add</button>
                            </div>
                            <div>
                                <select id="Unsorted" className="UnmatchedFields" multiple="multiple" size={displaySize}>
                                    {this.unmatchedFields.map(item => {
                                        return <option key={item.strName}>{item.strName}</option>;
                                    })}
                                </select>
                            </div>
                        </div> :
                        <div></div>
                }
                <div className='SectionMargin'>
                    <div>Add sorted field manually</div>
                    <table cellPadding={0} cellSpacing={0} style={{width: '100%', border: 'none'}}>
                        <tbody>
                        <tr>
                        <td style={{width: 1}} ><button style={{width: 24}} onClick={this.addSortedManually}>+</button></td>
                        <td style={{maxWidth: '100%', paddingRight: 4}} ><input style={{width: '100%'}} id='NewSortedText' type='text' onKeyUp={this.textboxEnterKeyHandler} /></td>
                        <td style={{whiteSpace: 'nowrap', width: 1}} ><input style={{width: 13}} id='NewSortedIsPattern' type='checkbox' />regex pattern?</td>
                        </tr>
                        </tbody>
                    </table>
                    <div style={{visibility: this.addErrorVisibility, color: 'red'}} >{this.errorText}</div>
                </div>
                <div className='SectionMargin'>
                    <div>Sorted fields</div>
                    <button className="CoreButton EndButton" type="button" onClick={this.selectAllSorted} >All</button>
                    <button className="CoreButton MiddleButton" type="button" onClick={this.selectNoneSorted} >None</button>
                    <button className="CoreButton EndButton" type="button" onClick={this.deleteSorted} >Delete</button>
                </div>
                <DragDropContext onDragEnd={this.onDragEnd}>
                    <Droppable droppableId="droppable">
                        {(droppableProvided, droppableSnapshot) => (
                            <div className='SortedFields'
                                 ref={droppableProvided.innerRef}
                            >
                                {window.FieldSorter.sortedFields.map((item, index) => (
                                    <Draggable key={item.text} draggableId={item.text} index={index}>
                                        {(draggableProvided, draggableSnapshot) => (
                                            <div
                                                ref={draggableProvided.innerRef}
                                                {...draggableProvided.draggableProps}
                                                {...draggableProvided.dragHandleProps}
                                            >
                                                <SortRow key={index} sortField={item} index={index} updateCallback={this.refreshUnmatched} />
                                            </div>
                                        )}
                                    </Draggable>
                                ))}
                                {droppableProvided.placeholder}
                            </div>
                        )}
                    </Droppable>
                </DragDropContext>
            </div>
        );
    }
}

class SortRow extends Component {
    constructor(props) {
        super(props);
        this.isPatternChanged = this.isPatternChanged.bind(this);
        this.selectionChanged = this.selectionChanged.bind(this);
        this.editText = this.editText.bind(this);
        this.handleClose = this.handleClose.bind(this);
        this.textboxEnterKeyHandler = this.textboxEnterKeyHandler.bind(this);
    }

    isEditing = false;
    errorVisibility = 'hidden';
    errorText = '';

    textboxEnterKeyHandler(event) {
        if (event.keyCode === 13) {
            event.preventDefault();
            let textbox = document.getElementById(this.props.index);
            let value = textbox.value;
            if (value === ''){
                this.errorText = noValueError;
                this.errorVisibility = 'visible';
                this.forceUpdate();
            } else if (isDuplicate(value) && value !== this.props.sortField.text) {
                this.errorText = dupValueError;
                this.errorVisibility = 'visible';
                this.forceUpdate();
            } else {
                this.errorVisibility = 'hidden';
                this.props.sortField.text = textbox.value;
                this.isEditing = false;
                this.props.updateCallback();
            }
        }
    }

    isPatternChanged() {
        this.props.sortField.isPattern = !this.props.sortField.isPattern;
        this.props.updateCallback();
    }

    editText() {
        this.isEditing = true;
        this.forceUpdate();
    }

    selectionChanged() {
        this.props.sortField.selected = !this.props.sortField.selected;
        this.forceUpdate();
    }

    handleClose() {
        this.isEditing = false;
        this.forceUpdate();
    }

    render(){
        return <div className="SortedField" style={{backgroundColor: this.props.sortField.selected ? 'lightblue' : 'white'}} >
            <DragHandleIcon onClick={this.selectionChanged} />
            <div onClick={this.isPatternChanged} className='SortFieldCell IsPatternIndicator'>{this.props.sortField.isPattern ? '(.*)' : ''}</div>
            <div onClick={this.editText} className='SortFieldCell SortFieldText'>{this.props.sortField.text}</div>
            <ReactModal
                isOpen={this.isEditing}
                ariaHideApp={false}
                onRequestClose={()=>{this.isEditing = false;this.errorVisibility = 'hidden';this.forceUpdate();}}
                style={{ content: {height: 40, left: '25%', right: '25%', top: '40%'}}}
            >
                <input id={this.props.index} style={{width: '100%'}} autoFocus defaultValue={this.props.sortField.text} onKeyUp={this.textboxEnterKeyHandler} />
                <div style={{visibility: this.errorVisibility, color: 'red'}} >{this.errorText}</div>
            </ReactModal>
        </div>
    }
}

class DragHandleIcon extends Component {
    render() {
        return <svg onClick={this.props.onClick} className="GrabHandle SortFieldCell" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
            <path fill="none" d="M0 0h24v24H0V0z"/>
            <path d="M11 18c0 1.1-.9 2-2 2s-2-.9-2-2 .9-2 2-2 2 .9 2 2zm-2-8c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0-6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm6 4c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
        </svg>;
    }
}

export default App;

