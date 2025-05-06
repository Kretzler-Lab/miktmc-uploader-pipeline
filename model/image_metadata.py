from lib.halolink_connection import HLField
from lib.redcap_connection import get_disease, get_stain
from model.redcap_metadata import RedcapMetadata


class ImageMetadata:
    def __init__(self, parent_metadata: RedcapMetadata = None):
        self.parent_metadata = parent_metadata
        self.level = ""
        self.barcode = ""
        self.slide_stain = ""
        self.image_type = ""
        self.in_error = False
        self.missing_metadata = False
        self.error_message = ""

    def fill_wsi_with_redcap_result(self, redcap_result: dict, slide_num: int):
        self.level = redcap_result["slidelevel" + str(slide_num)]
        self.image_type = 'WSImage'
        self.barcode = redcap_result["slidebarcode" + str(slide_num)]
        if redcap_result["slidestain" + str(slide_num)]:
            self.slide_stain = get_stain(int(redcap_result["slidestain" + str(slide_num)]))
        else:
            self.slide_stain = ""


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

    def get_metadata_header_string(self):
        field_str = "Barcode,Stain"
        hl_updates = self.get_halolink_updates()
        for field in hl_updates:
            field_str = field_str + "," + field["field_enum"].value["name"]
        return field_str + ",Error Message"

    def get_metadata_update_string(self):
        hl_updates = self.get_halolink_updates()
        field_list = ["barcode:" + str(self.barcode), "stain:" + str(self.slide_stain)]
        for field in hl_updates:
            field_list.append(field["field_enum"].value["name"] + ":" + str(field["value"]))
        return ",".join(field_list)

    def get_metadata_update_string_plain(self):
        hl_updates = self.get_halolink_updates()
        field_list = [str(self.barcode), str(self.slide_stain)]
        for field in hl_updates:
            if "," in field["value"]:
                field_list.append("\"" + str(field["value"])+ "\"")
            else:
                field_list.append(str(field["value"]))
        update_string = ",".join(field_list)
        update_string = update_string + "," + "\"" + self.error_message + "\""
        return update_string

    def validate_metadata(self):
        validation_exemptions = ["error_message", "npt_patient_study_id", "cgn_patient_study_id", "em_count"]
        fields = {}
        missing_fields = []
        # We only have to validate all of the image metadata if it's a WSI. Otherwise just check image type.
        if self.image_type == "WSImage":
            fields = vars(self)
        else:
            fields["image_type"] = self.image_type
        fields = fields | vars(self.parent_metadata)
        for name, value in fields.items():
            if not name.startswith("__") and not callable(value) and name not in validation_exemptions:
                if value is None or value == "":
                    self.missing_metadata = True
                    missing_fields.append(name)
        if fields["npt_patient_study_id"] == "" and fields["cgn_patient_study_id"] == "":
            self.missing_metadata = True
            missing_fields.append("patient_study_id")
        if self.missing_metadata:
            self.error_message = self.error_message + "WARNING: field(s) " + ",".join(missing_fields) + " are/is missing."






