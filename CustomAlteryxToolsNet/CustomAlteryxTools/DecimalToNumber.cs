using System.Collections.Generic;
using System.Xml;
using AlteryxRecordInfoNet;

namespace CustomAlteryxTools
{
    public class DecimalToNumber : INetPlugin
    {
        private int _toolId;
        private EngineInterface _engine;
        private PluginOutputConnectionHelper _output;
        private XmlElement _config;
        
        public void PI_Init(int nToolID, EngineInterface engineInterface, XmlElement pXmlProperties)
        {
            _config = pXmlProperties["Configuration"];
            _toolId = nToolID;
            _engine = engineInterface;
            _output = new PluginOutputConnectionHelper(nToolID, engineInterface);
        }

        public void PI_Close(bool bHasErrors) {}

        public IIncomingConnectionInterface PI_AddIncomingConnection(string pIncomingConnectionType, string pIncomingConnectionName)
        {
            return new IncomingDecimalToNumber(this);
        }

        public bool PI_AddOutgoingConnection(string pOutgoingConnectionName, OutgoingConnection outgoingConnection)
        {
            _output.AddOutgoingConnection(outgoingConnection);
            return true;
        }

        public bool PI_PushAllRecords(long nRecordLimit)
        {
            SendError("No incoming connection provided");
            return false;
        }

        public bool ShowDebugMessages() => true;
        
        public void SendError(string message)
        {
            _engine.OutputMessage(_toolId, MessageStatus.STATUS_Error, message);
        }

        public void Close()
        {
            _output.Close();
        }

        public void PushData(RecordData data)
        {
            _output.PushRecord(data);
        }

        public void InitOutput(RecordInfo info)
        {
            _output.Init(info, "Output", null, _config);
        }

        public void OutputToolProgress(double dPercent)
        {
            _engine.OutputToolProgress(_toolId, dPercent);
            _output.UpdateProgress(dPercent);
        }
    }

    public class IncomingDecimalToNumber : IIncomingConnectionInterface
    {
        public IncomingDecimalToNumber(DecimalToNumber parent)
        {
            _parent = parent;
        }

        private readonly DecimalToNumber _parent;
        private RecordInfo _incomingInfo;
        private RecordInfo _info;
        private RecordCopier _copier;
        private Record _record;
        private Dictionary<int, FieldType> _decimalMapping = new Dictionary<int, FieldType>();

        public void II_Close()
        {
            _parent.Close();
        }

        public bool II_Init(RecordInfo recordInfo)
        {
            _incomingInfo = recordInfo;
            _info = new RecordInfo();
            _copier = new RecordCopier(_info, _incomingInfo, false);
            for (var index = 0; index < _incomingInfo.NumFields(); index++)
            {
                var field = _incomingInfo[index];
                if (field.FieldType != FieldType.E_FT_FixedDecimal)
                {
                    _info.AddField(field.GetFieldName(), field.FieldType, (int)field.Size, field.Scale, field.GetSource(), field.GetDescription());
                    _copier.Add(index, index);
                    continue;
                }

                var fieldType = FieldType.E_FT_Double;
                if (field.Scale == 0)
                {
                    fieldType = FieldType.E_FT_Int64;
                }
                _decimalMapping.Add(index, fieldType);
                _info.AddField(field.GetFieldName(), fieldType,0,0,field.GetSource(), field.GetDescription());
            }
            _copier.DoneAdding();
            _record = _info.CreateRecord();
            _parent.InitOutput(_info);
            return true;
        }

        public XmlElement II_GetPresortXml(XmlElement pXmlProperties)
        {
            return null;
        }

        public bool II_PushRecord(RecordData pRecord)
        {
            _record.Reset();
            _copier.Copy(_record, pRecord);
            foreach (var key in _decimalMapping.Keys)
            {
                if (_incomingInfo[key].IsNull(pRecord))
                {
                    _info[key].SetNull(_record);
                    continue;
                }

                var fieldType = _decimalMapping[key];
                if (fieldType == FieldType.E_FT_Double)
                {
                    _info[key].SetFromDouble(_record, double.Parse(_incomingInfo[key].GetAsString(pRecord)));
                }
                else
                {
                    _info[key].SetFromInt64(_record, long.Parse(_incomingInfo[key].GetAsString(pRecord)));
                }
            }

            var data = _record.GetRecord();
            _parent.PushData(data);
            return true;
        }

        public void II_UpdateProgress(double dPercent)
        {
            _parent.OutputToolProgress(dPercent);
        }

        public bool ShowDebugMessages() => true;
    }
}