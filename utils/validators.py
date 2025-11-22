import re


class Validators:
    NAME = re.compile(r'^[A-Za-z ]+$')
    AGE = re.compile(r'^\d{1,3}$')
    WARD = re.compile(r'^(ICU|HDU|Maternity|General)$')
    DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')

    @classmethod
    def validate_name(cls, name):
        return bool(cls.NAME.match(name))

    @classmethod
    def validate_age(cls, age):
        return bool(cls.AGE.match(str(age)))

    @classmethod
    def validate_ward(cls, ward):
        return bool(cls.WARD.match(ward))

    @classmethod
    def validate_date(cls, date_str):
        return bool(cls.DATE.match(date_str))
