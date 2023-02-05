from fastapi import FastAPI, Header, HTTPException, Depends, status, Response, Request, APIRouter, Form
from pydantic import BaseModel
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.datastructures import URL

from typing import Optional, Any
from pathlib import Path
import random

from employee_auth import *
from classes import *

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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_token_employee(token: str = Depends(oauth2_scheme)):
    employee_uid = employee_verify_login(token['token'])
    print(token)
    print(employee_uid)
    if not employee_uid['status'] == 'success':
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )
    return_dict = employee_uid['body']


def verify_token_employee2(token: str = Depends(oauth2_scheme)):
    print(token)
    # return True
    if 'token' not in req.headers:
        raise HTTPException(
            status_code=401,
            status="Unauthorized"
        )
    token = req.headers["token"]
    # Here your code for verifying the token or whatever you use
    employee_uid = employee_verify_login(token)
    if not employee_uid['status'] == 'success':
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )
    return_dict = employee_uid['body']
    return_dict['refresh_token'] = req.headers['refresh_token']
    print(return_dict)
    return return_dict



""" EMPLOYEE ROUTES """
@api_router.get("/", status_code=200)
def employee_landing(request: Request, alert=None) -> dict:
    '''Landing Page with auth options'''
    print(verify_token_employee(oauth2_scheme))
    return EMPLOYEE_TEMPLATES.TemplateResponse(
        "landing.html",
        {
            "request": request,
            "alert":alert
        }
    )


@api_router.post("/member/login", status_code=200)
def employee_login_api(request: Request, email: str = Form(), password:str = Form()) -> dict:
    """
    Employee login endpoint
    Parameters:
    ----------
    email (str): email of the employee
    password (str): password of the employee
    
    Returns:
    -------
    status code 201 success
    dict: token: login auth token

    """
    state = employee_login(email, password)
    if state['status'] == 'success':
        set_token(state['token'], state['refresh_token'])
        return RedirectResponse(url="/member", status_code=302)
    else:
        # return landing page with error
        redirect_url = URL(request.url_for('employee_landing')).include_query_params(alert=str(state['body']))
        return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@app.post("/token")
def set_token(token, refresh):
    print(token)
    return {"access_token": token, "refresh_token": refresh, "token_type": "bearer"}


@api_router.post("/member/signup", status_code=200)
def employee_signup(request: Request, email: str = Form(), password:str = Form(), fName:str = Form(), lName:str = Form()) -> dict:
    """
    Root GET
    """
    state = employee_create_account(fName, lName, email, password)
    if state['status'] == 'success':
        redirect_url = URL(request.url_for('member_root'))
        return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    else:
        redirect_url = URL(request.url_for('employee_landing')).include_query_params(alert=str(state['body']))
        return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@api_router.get("/member", status_code=200)
def member_root(request: Request ) -> dict:
    """
    Root GET
    """
    # print(current_user)
    # current_user: bool = Depends(verify_token_employee)

    training = [
    {
        "id": 1,
        "title": "Driving Fedex",
        "description": "Some quick example text to build on the card title and make up the bulk of the card's content.",
        "status": 100,
    },
    {
        "id": 1,
        "title": "Warehouse Associate",
        "description": "Some quick example text to build on the card title and make up the bulk of the card's content.",
        "status": 50,
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
        "status": 75,
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


@api_router.get("/member/finish/{val}", status_code=200)
def complete_training(request: Request) -> dict:
    """
    Root GET
    """
    metrics = [
    {
        "id": 1,
        "title": "Accuracy",
        "value": "98%"
    },
    {
        "id": 2,
        "title": "Hours",
        "value": 2
    },
    {
        "id": 3,
        "title": "Percentile",
        "value": 15
    }
    ]
    return EMPLOYEE_TEMPLATES.TemplateResponse(
        "complete.html",
        {
            "request": request,
            "metrics": metrics
        }
    )


"""EMPLOYER ROUTES"""

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


@api_router.get("/company/add_modules/{role_id}", status_code=200)
def add_modules(role_id:str, request: Request) -> dict:
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
        "addModules.html",
        {
            "request": request,
            "modules": modules
        }
    )


@api_router.get("/company/onboarding_preview/{role_id}", status_code=200)
def onboarding_preview(role_id:str, request: Request) -> dict:
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
        "onboardingPreview.html",
        {
            "request": request,
            "modules": modules,
            "sections": modules
        }
    )


@api_router.get("/company/account", status_code=200)
def view_account(request: Request) -> dict:
    """
    Root GET
    """
    info = {
        "company_name": "Owlo",
        "email": "sample@owlo.co"
    }
    invoices = [
    {
        "month": "January",
        "custom_software_runs": 2,
        "members_trained": 2,
        "invoice": "$100",
        "status": "Paid"
    },
    {
        "month": "February",
        "custom_software_runs": 2,
        "members_trained": 2,
        "invoice": "$100",
        "status": "Paid"
    },
    {
        "month": "March",
        "custom_software_runs": 2,
        "members_trained": 2,
        "invoice": "$100",
        "status": "Paid"
    }]
        
    
    return EMPLOYER_TEMPLATES.TemplateResponse(
        "account.html",
        {
            "request": request,
            "invoices": invoices,
            "info": info
        }
    )


app.include_router(api_router)