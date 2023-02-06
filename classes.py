from pydantic import BaseModel

class User(BaseModel):
    email: str
    first_name: str
    last_name: str
    uid: str


class Manager(BaseModel):
    company_id: str = None
    company_name: str = None
    first_name: str
    last_name: str
    uid: str
    email: str


class Member(BaseModel):
    id: str
    id_input: str
    first_name: str
    last_name: str
    email: str
    role: str
    employee_id: str
    role_id: str
    employment_type: str
    status: str


class Assignment(BaseModel):
    id_input: str
    first_name: str
    last_name: str
    email: str
    role_id: str
    employment_type: str