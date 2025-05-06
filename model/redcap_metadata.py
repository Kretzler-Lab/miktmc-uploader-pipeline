from lib.redcap_connection import get_disease


class RedcapMetadata:
    def __init__(self, biopsy_id: str):
        self.biopsy_id = biopsy_id
        self.em_count = 0
        self.study_id = ""
        self.organ = "Kidney"
        self.biopsy_date = ""
        self.npt_patient_study_id = ""
        self.cgn_patient_study_id = ""
        self.disease = ""
        self.biopsy_id = biopsy_id
        self.tissue_comment = "Biopsy"
        self.event_type = "Enrollment Biopsy Material"

    def fill_with_redcap_result(self, redcap_result: dict):
        if "subjectid" in redcap_result:
            self.cgn_patient_study_id = redcap_result["subjectid"]
        if "pathdiseasecohort" in redcap_result:
            self.disease = get_disease(redcap_result["pathdiseasecohort"])
        if "neptune_studyid_screen" in redcap_result:
            self.npt_patient_study_id = redcap_result["neptune_studyid_screen"]
        self.em_count = redcap_result["numems_qc"]
        self.biopsy_date = redcap_result["renalbxdate"]
