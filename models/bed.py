class Bed:
    def __init__(self, bed_id=None, ward_type=None, status="available", equipment=None):
        self.bed_id = bed_id
        self.ward_type = ward_type
        self.status = status
        self.equipment = equipment or []

    def is_available(self):
        return self.status == "available"

    def to_tuple(self):
        return (self.ward_type, ",".join(self.equipment))
