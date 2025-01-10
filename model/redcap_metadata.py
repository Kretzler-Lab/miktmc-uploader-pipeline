from lib.redcap_connection import get_disease


class RedcapMetadata:
    def __init__(self, biopsy_id: str):
        self.biopsy_id = biopsy_id
        self.em_count = 0
        self.study_id = None
        self.organ = "Kidney"
        self.biopsy_date = None
        self.npt_patient_study_id = None
        self.cgn_patient_study_id = None
        self.disease = None
        self.biopsy_id = biopsy_id
        self.tissue_comment = "Biopsy"
        self.event_type = "Enrollment Biopsy Material"

    def fill_with_redcap_result(self, redcap_result: dict):
        self.cgn_patient_study_id = redcap_result["subjectid"]
        self.disease = get_disease(int(redcap_result["pathdiseasecohort"]))
        self.biopsy_date = redcap_result["renalbxdate"]
        self.npt_patient_study_id = redcap_result["neptune_studyid_screen"]
        self.em_count = redcap_result["numems_qc"]