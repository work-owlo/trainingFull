from pydantic import BaseModel

class User(BaseModel):
    email: str
    first_name: str
    last_name: str
    uid: str
    token: str = None


class Manager(BaseModel):
    company_id: str = None
    company_name: str = None
    first_name: str
    last_name: str
    uid: str
    email: str
    token: str = None


class Member(BaseModel):
    id: str
    id_input: str
    first_name: str
    last_name: str
    email: str
    role: str
    employee_id: str = None
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


class Role(BaseModel):
    role_id: str
    role_name: str
    role_description: str = None
    status: str = None


class Role_Info(BaseModel):
    role_id: str
    role_name: str
    count: int
    completed: int = None
    completion_rate: float = None
    average_score: float = None
    average_time: float = None
    status: str


class Tool(BaseModel):
    id: str
    name: str
    icon: str
    status: str


class Tool_info(BaseModel):
    tool_id: str
    tool_name: str
    tool_icon: str


class Module(BaseModel):
    id: str
    name: str
    description: str
    status: str = None


