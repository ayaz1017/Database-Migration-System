import hashlib
from faker import Faker

fake = Faker()

MASKERS = {
    "email": lambda v: fake.email(),
    "name": lambda v: fake.name(),
    "first_name": lambda v: fake.first_name(),
    "last_name": lambda v: fake.last_name(),
    "phone": lambda v: fake.phone_number(),
    "ssn": lambda v: fake.ssn(),
    "address": lambda v: fake.address(),
    "ip": lambda v: fake.ipv4(),
    "credit_card": lambda v: fake.credit_card_number(),
    "date": lambda v: str(fake.date_of_birth()),
    "random_string": lambda v: fake.pystr(max_chars=len(str(v)) if v and isinstance(v, str) else 10),
    "null": lambda v: None,
    "hash": lambda v: hashlib.sha256(str(v).encode()).hexdigest()[:16],
}

def mask_value(value, masking_type, fixed_value=None):
    if masking_type == "fixed_value":
        return fixed_value
    masker = MASKERS.get(masking_type)
    return masker(value) if (masker and value is not None) else value

def apply_masking_to_row(row_dict: dict, rules: list) -> dict:
    """
    Applies masking rules to a single row represented as a dictionary.
    rules: list of dicts with keys 'column_name', 'masking_type', 'fixed_value'
    """
    masked = dict(row_dict)
    for rule in rules:
        col = rule.get("column_name")
        m_type = rule.get("masking_type")
        f_val = rule.get("fixed_value")
        if col in masked and masked[col] is not None:
            masked[col] = mask_value(masked[col], m_type, f_val)
    return masked

# Alias for consistent naming
mask_row = apply_masking_to_row
