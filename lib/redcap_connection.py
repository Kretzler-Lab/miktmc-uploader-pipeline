import requests
import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger("lib-RedcapConnection")
logging.basicConfig(level=logging.ERROR)

REDCAP_HOST = "https://rc.rarediseasesnetwork.org/api/"
DEFAULT_FIELD_LIST = ["subjectid", "pathdiseasecohort", "renalbxdate", "numems_qc", "numbarcodes",
                      "neptune_studyid_screen"]
DEFAULT_EVENTS = []
DEFAULT_FORMS = []

slide_nums = list(range(1, 21))
slide_level_fields = []
slide_stain_fields = []
slide_barcode_fields = []
for i in slide_nums:
    slide_stain_fields.append("slidestain" + str(i))
    slide_level_fields.append("slidelevel" + str(i))
    slide_barcode_fields.append("slidebarcode" + str(i))

DEFAULT_FIELD_LIST.extend(slide_level_fields)
DEFAULT_FIELD_LIST.extend(slide_stain_fields)
DEFAULT_FIELD_LIST.extend(slide_barcode_fields)


def get_disease(code: int):
    disease_codes = {
        1: "MCD",
        2: "MCD + C1q",
        3: "FSGS",
        4: "FSGS + C1q",
        5: "MN",
        6: "IgA"
    }
    return disease_codes[code]


def get_stain(code: int):
    stain_codes = {
        1: "HE",
        2: "HE - Frozen Section",
        3: "PAS",
        4: "PAS - Frozen Section",
        5: "Silver",
        6: "TolBlue",
        7: "Trichrome",
        8: "Trichrome-Silver",
        9: "Unknown",
        10: "Other - Actin",
        11: "Other - Acid Fuchsin Orange G (AFOG)",
        12: "Other - Congo Red (CR)/Amyloid",
        13: "Other - CD3",
        14: "Other - CD5",
        15: "Other - CD10",
        16: "Other - CD18",
        17: "Other - CD20",
        18: "Other - CD23",
        19: "Other - CD34",
        20: "Other - CD43",
        21: "Other - CD68",
        22: "Other - CD138",
        23: "Other - Cytokeratin",
        24: "Other - Desmin",
        25: "Other - Elastin",
        26: "Other - EVG",
        27: "Other - Hematoxylin Phloxine Saffron (HSP)",
        28: "Other - IgG",
        29: "Other - IgG4",
        30: "Other - Kappa (IHC or in situ)",
        31: "Other - Ki67",
        32: "Other - Lambda (IHC or in situ)",
        33: "Other - Melan-A",
        34: "Other - PLA2R",
        35: "Other - PNL2",
        36: "Other - ThioFlavin",
        37: "Other - TRP-2",
        38: "Other - WT1"
    }
    return stain_codes[code]


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
        return requests.post(REDCAP_HOST, data=request_data)

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
