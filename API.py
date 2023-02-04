from fastapi import FastAPI, Header, HTTPException, Depends, status, Response, Request, APIRouter
from pydantic import BaseModel
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from typing import Optional, Any
from pathlib import Path
import random

app = FastAPI()
api_router = APIRouter()
BASE_PATH = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory="static"), name="static")
EMPLOYEE_TEMPLATES = Jinja2Templates(directory=str(BASE_PATH / "templates/employees"))
EMPLOYER_TEMPLATES = Jinja2Templates(directory=str(BASE_PATH / "templates/employer"))


# # Add the allowed origins here
# origins = ["http://localhost:3000"]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )



@api_router.get("/member", status_code=200)
def root(request: Request) -> dict:
    """
    Root GET
    """
    training = [
    {
        "id": 1,
        "title": "FastAPI",
        "description": "Some quick example text to build on the card title and make up the bulk of the card's content.",
        "status": 100,
    },
    {
        "id": 1,
        "title": "FastAPI",
        "description": "Some quick example text to build on the card title and make up the bulk of the card's content.",
        "status": 0,
    },
    {
        "id": 1,
        "title": "FastAPI",
        "description": "Some quick example text to build on the card title and make up the bulk of the card's content.",
        "status": 25,
    },
    {
        "id": 1,
        "title": "FastAPI",
        "description": "Some quick example text to build on the card title and make up the bulk of the card's content.",
        "status": 85,
    }
    ]
    explore = training[0::]
    random.shuffle(training)
    invited = training[0::]
    return EMPLOYEE_TEMPLATES.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "FastAPI",
            "explore": explore,
            "invited": invited
        }
    )


@api_router.get("/member/onboard/{val}", status_code=200)
def start_training(request: Request) -> dict:
    """
    Root GET
    """
    modules = [
    {
        "id": 1,
        "title": "Customer Simulation",
        "icon": "people-outline"
    },
    {
        "id": 2,
        "title": "Co-worker Simulation",
        "icon": "chatbubbles-outline"
    },
    {
        "id": 3,
        "title": "Software Simulation",
        "icon": "desktop-outline"
    }
    ]
    return EMPLOYEE_TEMPLATES.TemplateResponse(
        "train.html",
        {
            "request": request,
            "modules": modules + modules
        }
    )



@api_router.get("/company/team", status_code=200)
def view_company_team(request: Request) -> dict:
    """
    Root GET
    """
    members = [
    {
        "id": 1,
        "first_name": "John",
        "last_name": "Doe",
        "type": "Employee",
        "status": "Completed",
        "email": "sample@owlo.co",
        "role": "Dispatch"
    },
    {
        "id": 2,
        "first_name": "Jane",
        "last_name": "Doe",
        "type": "Employee",
        "status": "Pending",
        "email": "sample@owlo.co",
        "role": "Driver"
    },
    {
        "id": 3,
        "first_name": "Arda",
        "last_name": "Akman",
        "type": "Contractor",
        "status": "Completed",
        "email": "sample@owlo.co",
        "role": "Manager"
    },
    {
        "id": 4,
        "first_name": "Anshul",
        "last_name": "Paul",
        "type": "Contractor",
        "status": "Incomplete",
        "email": "sample@owlo.co",
        "role": "Manager"
    }
    ]
    return EMPLOYER_TEMPLATES.TemplateResponse(
        "team.html",
        {
            "request": request,
            "members": members
        }
    )

@api_router.get("/company/roles", status_code=200)
def view_company_roles(request: Request) -> dict:
    """
    Root GET
    """
    roles = [
    {   
        "id": 1,
        "name": "Dispatch",
        "num_members": 2,
        "sent_to": 2,
        "comp_rate": 100,
        "avg_score": 4.5,
        "avg_time": 4.5
    },
    {
        "id": 2,
        "name": "Driver",
        "num_members": 2,
        "sent_to": 2,
        "comp_rate": 100,
        "avg_score": 4.5,
        "avg_time": 4.5
    }
    ]
    return EMPLOYER_TEMPLATES.TemplateResponse(
        "roles.html",
        {
            "request": request,
            "roles": roles
        }
    )

@api_router.get("/company/add_role", status_code=200)
def add_company_role(request: Request) -> dict:
    """
    Root GET
    """
    modules = [
    {
        "id": 1,
        "title": "Customer Simulation",
        "icon": "people-outline"
    },
    {
        "id": 2,
        "title": "Co-worker Simulation",
        "icon": "chatbubbles-outline"
    },
    {
        "id": 3,
        "title": "Software Simulation",
        "icon": "desktop-outline"
    }
    ]
    return EMPLOYER_TEMPLATES.TemplateResponse(
        "addRole.html",
        {
            "request": request,
            "modules": modules
        }
    )

app.include_router(api_router)