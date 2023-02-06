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

