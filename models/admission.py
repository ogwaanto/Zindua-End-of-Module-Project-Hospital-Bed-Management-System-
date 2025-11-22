class Admission:
    def __init__(self, admission_id=None, patient_id=None, bed_id=None, date_in=None, date_out=None):
        self.admission_id = admission_id
        self.patient_id = patient_id
        self.bed_id = bed_id
        self.date_in = date_in
        self.date_out = date_out

    def discharge(self, date_out):
        self.date_out = date_out
