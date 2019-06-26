import AlteryxPythonSDK as Sdk
import xml.etree.ElementTree as Et
from typing import List
from GlassdoorScrapeCore.GlassdoorScrapeCompany import ScrapeResults, get_company_data


class AyxPlugin:
    def __init__(self, n_tool_id: int, alteryx_engine: object, output_anchor_mgr: object):
        # Default properties
        self.n_tool_id: int = n_tool_id
        self.alteryx_engine: Sdk.AlteryxEngine = alteryx_engine
        self.output_anchor_mgr: Sdk.OutputAnchorManager = output_anchor_mgr

        # Custom properties
        self.CompanyNamesField: str = None
        self.maxPages: int = 0
        self.input: IncomingInterface = None
        self.Output: Sdk.OutputAnchor = None
        self.Reviews: Sdk.OutputAnchor = None
        self.Interviews: Sdk.OutputAnchor = None

    def pi_init(self, str_xml: str):
        # Getting the dataName data property from the Gui.html
        self.CompanyNamesField = Et.fromstring(str_xml).find('CompanyNames').text if 'CompanyNames' in str_xml else None
        self.maxPages = int(Et.fromstring(str_xml).find("maxPages").text) if 'maxPages' in str_xml else 0

        # Validity checks.
        if self.CompanyNamesField is None:
            self.display_error_msg('A field containing company names must be selected.')

        # Getting the output anchor from Config.xml by the output connection name
        self.Output = self.output_anchor_mgr.get_output_anchor('Output')
        self.Reviews = self.output_anchor_mgr.get_output_anchor('Reviews')
        self.Interviews = self.output_anchor_mgr.get_output_anchor('Interviews')

    def pi_add_incoming_connection(self, str_type: str, str_name: str) -> object:
        self.input = IncomingInterface(self)
        return self.input

    def pi_add_outgoing_connection(self, str_name: str) -> bool:
        return True

    def pi_push_all_records(self, n_record_limit: int) -> bool:
        self.alteryx_engine.output_message(self.n_tool_id, Sdk.EngineMessageType.error, 'Missing Incoming Connection.')
        return False

    def pi_close(self, b_has_errors: bool):
        self.Output.assert_close()
        self.Reviews.assert_close()
        self.Interviews.assert_close()

    def display_error_msg(self, msg_string: str):
        self.alteryx_engine.output_message(self.n_tool_id, Sdk.EngineMessageType.error, msg_string)


class IncomingInterface:
    def __init__(self, parent: AyxPlugin):
        # Default properties
        self.parent: AyxPlugin = parent

        # Custom properties
        self.OutputCopier: Sdk.RecordCopier = None
        self.OutputCreator: Sdk.RecordCreator = None
        self.CompanyNamesField: Sdk.Field = None
        self.IdField: Sdk.Field = None
        self.NameField: Sdk.Field = None
        self.ReviewLinkField: Sdk.Field = None
        self.ReviewPagesField: Sdk.Field = None
        self.InterviewLinkField: Sdk.Field = None
        self.InterviewPagesField: Sdk.Field = None

        source = "Glassdoor Scrape (" + str(self.parent.n_tool_id) + ")"

        self.ReviewsRecord: Sdk.RecordInfo = Sdk.RecordInfo(parent.alteryx_engine)
        self.ReviewFields: List[Sdk.Field] = self.generate_review_fields(self.ReviewsRecord, source)
        self.ReviewsCreator: Sdk.RecordCreator = self.ReviewsRecord.construct_record_creator()

        self.InterviewsRecord: Sdk.RecordInfo = Sdk.RecordInfo(parent.alteryx_engine)
        self.InterviewsFields: List[Sdk.Field] = self.generate_interview_fields(self.InterviewsRecord, source)
        self.InterviewsCreator: Sdk.RecordCreator = self.InterviewsRecord.construct_record_creator()


    def ii_init(self, record_info_in: Sdk.RecordInfo) -> bool:
        # Make sure the user provided a field to parse
        if self.parent.CompanyNamesField is None:
            self.parent.display_error_msg('Select a field')
            return False

        self.CompanyNamesField = record_info_in.get_field_by_name(self.parent.CompanyNamesField)

        # Returns a new, empty RecordCreator object that is identical to record_info_in.
        output_record = record_info_in.clone()

        # Adds field to record with specified name and output type.
        self.IdField = output_record.add_field("Glassdoor ID", Sdk.FieldType.v_wstring, 100)
        self.NameField = output_record.add_field("Glassdoor Name", Sdk.FieldType.v_wstring, 100)
        self.ReviewLinkField = output_record.add_field("Begin Review Search Link", Sdk.FieldType.v_wstring, 1000)
        self.ReviewPagesField = output_record.add_field("Review Pages", Sdk.FieldType.int64)
        self.InterviewLinkField = output_record.add_field("Begin Interview Search Link", Sdk.FieldType.v_wstring, 1000)
        self.InterviewPagesField = output_record.add_field("Interview Pages", Sdk.FieldType.int64)

        # Lets the downstream tools know what the outgoing record metadata will look like
        self.parent.Output.init(output_record)
        self.parent.Reviews.init(self.ReviewsRecord)
        self.parent.Interviews.init(self.InterviewsRecord)

        # Creating a new, empty record creator based on record_info_out's record layout.
        self.OutputCreator = output_record.construct_record_creator()

        # Instantiate a new instance of the RecordCopier class.
        self.OutputCopier = Sdk.RecordCopier(output_record, record_info_in)

        # Map each column of the input to where we want in the output.
        for index in range(record_info_in.num_fields):
            # Adding a field index mapping.
            self.OutputCopier.add(index, index)

        # Let record copier know that all field mappings have been added.
        self.OutputCopier.done_adding()

        return True

    def ii_push_record(self, in_record: Sdk.RecordRef) -> bool:
        company: str = self.CompanyNamesField.get_as_string(in_record)
        # try:
        result = get_company_data(company, self.parent.maxPages)
        # except:
        #    self.pushNullOutput(in_record)
        #    return False

        self.push_output(result, in_record)
        self.push_reviews(result)
        self.push_interviews(result)
        return True

    def ii_update_progress(self, d_percent: float):
        # Inform the Alteryx engine of the tool's progress.
        self.parent.alteryx_engine.output_tool_progress(self.parent.n_tool_id, d_percent)

        # Inform the outgoing connections of the tool's progress.
        self.parent.Output.update_progress(d_percent)
        self.parent.Reviews.update_progress(d_percent)

    def ii_close(self):
        # Close outgoing connections.
        self.parent.Output.close()
        self.parent.Reviews.close()

    def push_output(self, result: ScrapeResults, in_record: Sdk.RecordInfo):
        self.OutputCreator.reset()
        self.OutputCopier.copy(self.OutputCreator, in_record)

        self.IdField.set_from_string(self.OutputCreator, result.GlassdoorId)
        self.NameField.set_from_string(self.OutputCreator, result.GlassdoorName)
        self.ReviewLinkField.set_from_string(self.OutputCreator, result.GlassdoorReviewLink)
        self.ReviewPagesField.set_from_int64(self.OutputCreator, result.GlassdoorReviewPages)
        self.InterviewLinkField.set_from_string(self.OutputCreator, result.GlassdoorInterviewLink)
        self.InterviewPagesField.set_from_int64(self.OutputCreator, result.GlassdoorInterviewPages)

        output = self.OutputCreator.finalize_record()
        self.parent.Output.push_record(output)

    def push_null_output(self, in_record: Sdk.RecordInfo):
        self.OutputCreator.reset()
        self.OutputCopier.copy(self.OutputCreator, in_record)

        self.IdField.set_null(self.OutputCreator)
        self.NameField.set_null(self.OutputCreator)
        self.ReviewLinkField.set_null(self.OutputCreator)
        self.ReviewPagesField.set_null(self.OutputCreator)
        self.InterviewLinkField.set_null(self.OutputCreator)
        self.InterviewPagesField.set_null(self.OutputCreator)

        output = self.OutputCreator.finalize_record()
        self.parent.Output.push_record(output)

    def push_reviews(self, result: ScrapeResults):
        for review in result.reviews:
            self.ReviewsCreator.reset()
            self.ReviewFields[0].set_from_string(self.ReviewsCreator, result.GlassdoorId)

            i: int = 0
            while i < len(review):
                self.ReviewFields[i+1].set_from_string(self.ReviewsCreator, review[i])
                i = i + 1

            output = self.ReviewsCreator.finalize_record()
            self.parent.Reviews.push_record(output)

    def push_interviews(self, result: ScrapeResults):
        for interview in result.interviews:
            self.InterviewsCreator.reset()
            self.InterviewsFields[0].set_from_string(self.InterviewsCreator, result.GlassdoorId)

            i: int = 0
            while i < len(interview):
                self.InterviewsFields[i+1].set_from_string(self.InterviewsCreator, interview[i])
                i = i + 1

            output = self.InterviewsCreator.finalize_record()
            self.parent.Interviews.push_record(output)

    def generate_review_fields(self, record: Sdk.RecordInfo, source: str) -> List[Sdk.Field]:
        return [
            record.add_field("Glassdoor ID", Sdk.FieldType.v_wstring, 10, 0, source, ''),
            record.add_field("Company Name", Sdk.FieldType.v_wstring, 100, 0, source, ''),
            record.add_field("Review Date", Sdk.FieldType.v_wstring, 50, 0, source, ''),
            record.add_field("Helpful (count)", Sdk.FieldType.v_wstring, 10, 0, source, ''),
            record.add_field("Title (of the review)", Sdk.FieldType.v_wstring, 256, 0, source, ''),
            record.add_field("Rating (out of 5)", Sdk.FieldType.v_wstring, 3, 0, source, ''),
            record.add_field("Current/ Past Employee", Sdk.FieldType.v_wstring, 10, 0, source, ''),
            record.add_field("Employee Title", Sdk.FieldType.v_wstring, 100, 0, source, ''),
            record.add_field("Employment Type", Sdk.FieldType.v_wstring, 100, 0, source, ''),
            record.add_field("Location", Sdk.FieldType.v_wstring, 100, 0, source, ''),
            record.add_field("Recommends", Sdk.FieldType.v_wstring, 10, 0, source, ''),
            record.add_field("Positive Outlook", Sdk.FieldType.v_wstring, 10, 0, source, ''),
            record.add_field("Approves of CEO", Sdk.FieldType.v_wstring, 10, 0, source, ''),
            record.add_field("Time Employed", Sdk.FieldType.v_wstring, 100, 0, source, ''),
            record.add_field("Pros", Sdk.FieldType.v_wstring, 5000, 0, source, ''),
            record.add_field("Cons", Sdk.FieldType.v_wstring, 5000, 0, source, ''),
            record.add_field("Advice to Management", Sdk.FieldType.v_wstring, 5000, 0, source, '')
            ]

    def generate_interview_fields(self, record: Sdk.RecordInfo, source: str) -> List[Sdk.Field]:
        return [
            record.add_field("Glassdoor ID", Sdk.FieldType.v_wstring, 10, 0, source, ''),
            record.add_field("Company Name", Sdk.FieldType.v_wstring, 100, 0, source, ''),
            record.add_field("Date", Sdk.FieldType.v_wstring, 50, 0, source, ''),
            record.add_field("Title (Analyst Interview)", Sdk.FieldType.v_wstring, 256, 0, source, ''),
            record.add_field("Experience", Sdk.FieldType.v_wstring, 20, 0, source, ''),
            record.add_field("Offer", Sdk.FieldType.v_wstring, 20, 0, source, ''),
            record.add_field("Difficulty", Sdk.FieldType.v_wstring, 20, 0, source, ''),
            record.add_field("Getting an interview", Sdk.FieldType.v_wstring, 20, 0, source, ''),
            record.add_field("Application", Sdk.FieldType.v_wstring, 5000, 0, source, ''),
            record.add_field("Interview (description/verbatim)", Sdk.FieldType.v_wstring, 5000, 0, source, ''),
            record.add_field("Interview (Questions)", Sdk.FieldType.v_wstring, 5000, 0, source, ''),
            ]