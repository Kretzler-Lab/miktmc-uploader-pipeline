from lib.halolink_connection import HLField
from lib.redcap_connection import get_disease, get_stain


class ImageMetadata:
    def __init__(self, biopsy_id: str):
        self.study_id = None
        self.organ = "Kidney"
        self.image_type = None
        self.biopsy_date = None
        self.npt_patient_study_id = None
        self.cgn_patient_study_id = None
        self.disease = None
        self.biopsy_id = biopsy_id
        self.tissue_comment = "Biopsy"
        self.event_type = "Enrollment Biopsy Material"
        self.level = None
        self.barcode = None
        self.slide_stain = None

    def fill_with_redcap_result(self, redcap_result: dict, slide_num: int):
        self.cgn_patient_study_id = redcap_result["subjectid"]
        self.disease = get_disease(int(redcap_result["pathdiseasecohort"]))
        self.biopsy_date = redcap_result["renalbxdate"]
        self.npt_patient_study_id = redcap_result["neptune_studyid_screen"]
        self.level = redcap_result["slidelevel" + str(slide_num)]
        self.barcode = redcap_result["slidebarcode" + str(slide_num)]
        self.slide_stain = get_stain(int(redcap_result["slidestain" + str(slide_num)]))

    def get_halolink_updates(self):
        return [
            {"field_enum": HLField.STUDY_ID, "value": self.study_id},
            {"field_enum": HLField.DISEASE, "value": self.disease},
            {"field_enum": HLField.IMAGE_TYPE, "value": self.image_type},
            {"field_enum": HLField.NPT_PATIENT_STUDY_ID, "value": self.npt_patient_study_id},
            {"field_enum": HLField.CGN_PATIENT_STUDY_ID, "value": self.cgn_patient_study_id},
            {"field_enum": HLField.ORGAN, "value": self.organ},
            {"field_enum": HLField.TISSUE_COMMENT, "value": self.tissue_comment},
            {"field_enum": HLField.EVENT_TYPE, "value": self.event_type},
            {"field_enum": HLField.LEVEL, "value": self.level},
            {"field_enum": HLField.BIOPSY_DATE, "value": self.biopsy_date},
            {"field_enum": HLField.BIOPSY_ID, "value": self.biopsy_id},
        ]




