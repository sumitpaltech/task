DEPARTMENT_HEADS = {
    "Accounts": "KanhaiyaLal",
    "Marketing": "Divya",
    "Tender": "Divya",
    "Technical": "Devendra",
    "Sales & Marketing": "Divya",
    "Supply Chain Management": "Divya",
    "Services": "Divya",
    "New Projects": "Bibhu",
    "Digital Marketing ": "Divya",
    "Ecommerce": "Mayank",
    "Dispatch": "Mayank",
}

def is_user_dept_head(username, department):
    if not username or not department:
        return False
    return DEPARTMENT_HEADS.get(department) == username