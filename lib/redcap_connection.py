import requests
import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger("lib-RedcapConnection")
logging.basicConfig(level=logging.ERROR)

REDCAP_HOST = "https://rc.rarediseasesnetwork.org/api/"
DEFAULT_FIELD_LIST = ["subjectid"]
DEFAULT_EVENTS = ["screening_and_cons_arm_1"]
DEFAULT_FORMS = ["slides_obtained","slide_details", "slide_qc"]

class RedcapConnection:

    def __init__(self):
        load_dotenv(".env")
        self.token = os.environ.get("redcap_token")

    def add_fields(self, request_data: dict):
        i = 0
        for field in DEFAULT_FIELD_LIST:
            request_data[f"fields[{i}]"] = field
            i = i + 1
        return request_data

    def add_events(self, request_data: dict):
        i = 0
        for event in DEFAULT_EVENTS:
            request_data[f"events[{i}]"] = event
            i = i + 1
        return request_data

    def add_forms(self, request_data: dict):
        i = 0
        for event in DEFAULT_FORMS:
            request_data[f"forms[{i}]"] = event
            i = i + 1
        return request_data

    def send_request(self, request_data: dict) -> requests.Response:
        request_data["token"] = self.token
        request_data = self.add_fields(request_data)
        request_data = self.add_events(request_data)
        request_data = self.add_forms(request_data)
        print(request_data)
        return requests.post(REDCAP_HOST,data=request_data)

    def export_records(self, request_data: dict) -> requests.Response:
        request_data.update({
            "content": "record",
            "action": "export",
            "format": "json",
            "type": "flat",
            "csvDelimiter": "",
            "rawOrLabel": "raw",
            "rawOrLabelHeaders": "raw",
            "exportCheckboxLabel": "true",
            "exportSurveyFields": "true",
            "exportDataAccessGroups": "true",
            "returnFormat": "json",
        })
        return self.send_request(request_data)


    def get_filtered_records(self, filter_logic: str) -> str:
        request_data = {
            "filterLogic": filter_logic
        }
        return self.export_records(request_data).json()

    def get_by_biopsy_id(self, biopsy_id: str) -> str:
        return self.get_filtered_records(f"[biopsyid]='{biopsy_id}'")
