using System;
using System.Data;
using System.Linq;
using System.Xml;
using Microsoft.AnalysisServices.AdomdClient;

namespace CustomAlteryxTools
{
    public class SsasImporter : AlteryxRecordInfoNet.INetPlugin
    {
        private AlteryxRecordInfoNet.PluginOutputConnectionHelper output;
        private int toolId;
        private XmlElement config;
        private string mdx;
        private string dataSource;
        private string catalog;
        private AlteryxRecordInfoNet.EngineInterface engine;

        public AlteryxRecordInfoNet.IIncomingConnectionInterface PI_AddIncomingConnection(string pIncomingConnectionType, string pIncomingConnectionName)
        {
            throw new NotImplementedException("Input tools cannot accept incoming connections.");
        }

        public bool PI_AddOutgoingConnection(string pOutgoingConnectionName, AlteryxRecordInfoNet.OutgoingConnection outgoingConnection)
        {
            output.AddOutgoingConnection(outgoingConnection);
            return true;
        }

        public void PI_Close(bool bHasErrors) { }

        public void PI_Init(int nToolID, AlteryxRecordInfoNet.EngineInterface engineInterface, XmlElement pXmlProperties)
        {
            engine = engineInterface;
            toolId = nToolID;
            output = new AlteryxRecordInfoNet.PluginOutputConnectionHelper(nToolID, engineInterface);
            config = pXmlProperties["Configuration"];

            mdx = config["mdx"]?.InnerText ?? "";
            dataSource = config["dataSource"]?.InnerText ?? "";
            catalog = config["catalog"]?.InnerText ?? "";
        }

        public bool PI_PushAllRecords(long nRecordLimit)
        {
            if (nRecordLimit < 0) nRecordLimit = long.MaxValue;
            bool success = false;
            string connStr = $"Data Source={dataSource};Catalog={catalog}";

            var conn = new AdomdConnection(connStr);

            try
            {
                conn.Open();
                engine.OutputMessage(toolId, AlteryxRecordInfoNet.MessageStatus.STATUS_Info, "Connected to server, processing the query...");
                engine.OutputToolProgress(toolId, 0.05);

                var command = new AdomdCommand(mdx, conn);
                AdomdDataReader reader;
                if (nRecordLimit == 0)
                {
                    reader = command.ExecuteReader(System.Data.CommandBehavior.SchemaOnly);
                }
                else
                {
                    reader = command.ExecuteReader();
                }

                engine.OutputMessage(toolId, AlteryxRecordInfoNet.MessageStatus.STATUS_Info, "Query finished executing, retrieving schema...");
                engine.OutputToolProgress(toolId, 0.50);

                var fields = reader.GetSchemaTable();
                var outputInfo = new AlteryxRecordInfoNet.RecordInfo();

                foreach (DataRow field in fields.Rows)
                {
                    var fieldName = field[0].ToString();

                    outputInfo.AddField(fieldName, AlteryxRecordInfoNet.FieldType.E_FT_V_WString, 1073741823,0,$"SSAS Input ({toolId})","");
                }

                output.Init(outputInfo, "Output", null, config);
                engine.OutputMessage(toolId, AlteryxRecordInfoNet.MessageStatus.STATUS_Info, "Prepared output schema, retrieving data...");
                engine.OutputToolProgress(toolId, 0.55);

                var record = outputInfo.CreateRecord();
                int totalRead = 0;

                while (totalRead < nRecordLimit && reader.Read())
                {
                    record.Reset();
                    for (int i = 0; i < outputInfo.NumFields(); i++)
                    {
                        AlteryxRecordInfoNet.FieldBase fieldBase = outputInfo[i];

                        if (reader[i] == null)
                        {
                            fieldBase.SetNull(record);
                        } else
                        {
                            fieldBase.SetFromString(record, reader[i].ToString());
                        }

                    }
                    output.PushRecord(record.GetRecord());

                    totalRead++;
                }

                engine.OutputMessage(toolId, AlteryxRecordInfoNet.MessageStatus.STATUS_Info, $"Data retrieval completed.  {totalRead} records output.");
                engine.OutputToolProgress(toolId, 1.00);

                success = true;
            }
            catch (Exception ex)
            {
                engine.OutputMessage(toolId, AlteryxRecordInfoNet.MessageStatus.STATUS_Error, $"Error: {ex.Message}  Stack trace: {ex.StackTrace}");
                success = false;
            }
            finally
            {
                conn.Close();
                conn.Dispose();
            }

            return success;
        }

        public bool ShowDebugMessages()
        {
            return true;
        }
    }
}
