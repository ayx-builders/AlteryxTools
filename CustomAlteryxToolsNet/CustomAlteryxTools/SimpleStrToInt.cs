using System.Text;
using System.Xml;
using AlteryxRecordInfoNet;

namespace CustomAlteryxTools
{
    public class SimpleStrToInt : INetPlugin
    {
        public int ToolId { get; private set; }
        public EngineInterface Engine { get; private set; }
        public PluginOutputConnectionHelper Output { get; private set; }
        public string[] Fields { get; private set; }
        public string NewField { get; private set; }
        public bool OnlyNumeric { get; private set; }
        public XmlElement Config { get; private set; }

        public IIncomingConnectionInterface PI_AddIncomingConnection(string pIncomingConnectionType, string pIncomingConnectionName)
        {
            return new SimpleStrToIntIncoming(this);
        }

        public bool PI_AddOutgoingConnection(string pOutgoingConnectionName, OutgoingConnection outgoingConnection)
        {
            Output.AddOutgoingConnection(outgoingConnection);
            return true;
        }

        public void PI_Close(bool bHasErrors) { }

        public void PI_Init(int nToolID, EngineInterface engineInterface, XmlElement pXmlProperties)
        {
            Config = pXmlProperties["Configuration"];
            ToolId = nToolID;
            Engine = engineInterface;
            Output = new PluginOutputConnectionHelper(ToolId, Engine);
            Fields = Config?["Fields"]?.InnerText.Split(',') ?? new string[]{};
            NewField = Config?["IntFieldName"]?.InnerText ?? "";
            OnlyNumeric = Config?["OnlyNumeric"]?.InnerText == "True";
        }

        public bool PI_PushAllRecords(long nRecordLimit)
        {
            SendError("No incoming conncetion provided");
            return false;
        }

        public bool ShowDebugMessages()
        {
            return true;
        }

        internal void SendError(string message)
        {
            Engine.OutputMessage(ToolId, MessageStatus.STATUS_Error, message);
        }

        internal void SendWarning(string message)
        {
            Engine.OutputMessage(ToolId, MessageStatus.STATUS_FieldConversionError, message);
        }
    }

    public class SimpleStrToIntIncoming : IIncomingConnectionInterface
    {
        public SimpleStrToIntIncoming(SimpleStrToInt parent) => _parent = parent;

        private readonly SimpleStrToInt _parent;
        private RecordCopier _copier;
        private RecordInfo _info;
        private RecordInfo _incomingInfo;
        private FieldBase[] _fields;
        private FieldBase _newField;
        private Record _record;
        private int errors = 0;
        
        public void II_Close()
        {
            if (errors>0) _parent.SendWarning($"{errors} records had conversion errors");
            _parent.Output.Close();
        }

        public XmlElement II_GetPresortXml(XmlElement pXmlProperties)
        {
            return null;
        }

        public bool II_Init(RecordInfo recordInfo)
        {
            _info = new RecordInfo();
            _incomingInfo = recordInfo;
            _copier = new RecordCopier(_info, _incomingInfo, false);
            for (var i = 0; i < _incomingInfo.NumFields(); i++)
            {
                _info.AddField(_incomingInfo[i]);
                _copier.Add(i,i);
            }
            _copier.DoneAdding();
            _info.AddField(_parent.NewField, FieldType.E_FT_Int64);
            _newField = _info.GetFieldByName(_parent.NewField,false);
            
            _fields = new FieldBase[_parent.Fields.Length];
            for (var i = 0; i < _fields.Length; i++)
            {
                _fields[i] = _incomingInfo.GetFieldByName(_parent.Fields[i],false);
            }

            _record = _info.CreateRecord();
            _parent.Output.Init(_info, "Output", null, _parent.Config);
            return true;
        }

        public bool II_PushRecord(RecordData pRecord)
        {
            _record.Reset();
            var builder = new StringBuilder();
            foreach (var field in _fields)
            {
                if (!field.IsNull(pRecord))
                {
                    builder.Append(field.GetAsString(pRecord));
                }
            }
            
            _copier.Copy(_record, pRecord);
            long? convertedInt;
            if (_parent.OnlyNumeric)
                convertedInt = SimpleStrToIntLogic.ConvertNumericOnly(builder.ToString());
            else
                convertedInt = SimpleStrToIntLogic.Convert(builder.ToString());
            
            if (convertedInt.HasValue)
                _newField.SetFromInt64(_record, convertedInt.Value);
            else
            {
                _newField.SetNull(_record);
                errors++;
            }

            _parent.Output.PushRecord(_record.GetRecord());
            return true;
        }

        public void II_UpdateProgress(double dPercent)
        {
            _parent.Engine.OutputToolProgress(_parent.ToolId, dPercent);
        }

        public bool ShowDebugMessages()
        {
            return true;
        }
    }
}
