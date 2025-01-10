from lib.halolink_connection import HLField
from lib.redcap_connection import get_disease, get_stain
from model.redcap_metadata import RedcapMetadata


class ImageMetadata:
    def __init__(self, parent_metadata: RedcapMetadata):
        self.parent_metadata = parent_metadata
        self.level = None
        self.barcode = None
        self.slide_stain = None
        self.image_type = 'WSImage'

    def fill_with_redcap_result(self, redcap_result: dict, slide_num: int):
        self.level = redcap_result["slidelevel" + str(slide_num)]
        self.barcode = redcap_result["slidebarcode" + str(slide_num)]
        self.slide_stain = get_stain(int(redcap_result["slidestain" + str(slide_num)]))

    def get_halolink_updates(self):
        return [
            {"field_enum": HLField.STUDY_ID, "value": self.parent_metadata.study_id},
            {"field_enum": HLField.DISEASE, "value": self.parent_metadata.disease},
            {"field_enum": HLField.IMAGE_TYPE, "value": self.image_type},
            {"field_enum": HLField.NPT_PATIENT_STUDY_ID, "value": self.parent_metadata.npt_patient_study_id},
            {"field_enum": HLField.CGN_PATIENT_STUDY_ID, "value": self.parent_metadata.cgn_patient_study_id},
            {"field_enum": HLField.ORGAN, "value": self.parent_metadata.organ},
            {"field_enum": HLField.TISSUE_COMMENT, "value": self.parent_metadata.tissue_comment},
            {"field_enum": HLField.EVENT_TYPE, "value": self.parent_metadata.event_type},
            {"field_enum": HLField.LEVEL, "value": self.level},
            {"field_enum": HLField.BIOPSY_DATE, "value": self.parent_metadata.biopsy_date},
            {"field_enum": HLField.BIOPSY_ID, "value": self.parent_metadata.biopsy_id},
        ]




