class Patient:
    def __init__(self, patient_id=None, name=None, age=None, diagnosis=None):
        self.patient_id = patient_id
        self.name = name
        self.age = age
        self.diagnosis = diagnosis

    def get_info(self):
        return f"{self.patient_id}: {self.name}, {self.age} y, {self.diagnosis}"
