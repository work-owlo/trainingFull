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
import re
import random

from employee_auth import *
from employees import *
from classes import *
from auth_classes import *

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

oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="token")


"""MUTUAL AUTH"""

@app.get("/logout", response_class=HTMLResponse)
def logout_get(token: str = Depends(oauth2_scheme)):
    response = RedirectResponse(url="/")
    delete_session_token_db(token)
    response.delete_cookie("access_token")
    return response

""" EMPLOYEE ROUTES """
@api_router.get("/", status_code=200)
def employee_landing(response:Response, request: Request, alert=None) -> dict:
    '''Landing Page with auth options'''
    # print(verify_token_employee(oauth2_scheme))
    cookie = request.cookies.get('access_token')
    if cookie:
        return RedirectResponse(url="/member") 
    return EMPLOYEE_TEMPLATES.TemplateResponse(
        "landing.html",
        {
            "request": request,
            "alert":alert
        }
    )


def get_current_employee(response: Response, token: str = Depends(oauth2_scheme)) -> User:
    """
    Get the current user from the cookies in a request.
    Use this function when you want to lock down a route so that only 
    authenticated users can see access the route.
    """
    if token == None:
        return False
    user = employee_verify_login(token)
    if user['status'] == 'error':
        return False
    # refreshed_token = employee_refresh_token(user['body']['token'])
    # print(refreshed_token)
    # response.set_cookie(
    #     key="access_token", 
    #     value=f"Bearer {refreshed_token['token']}", 
    #     httponly=True
    # )  
    return user['body']['user']


@app.post("/token")
async def login(response: Response, input_data: OAuth2PasswordRequestForm = Depends()):
    ''' Login a user '''
    login_state = employee_login(input_data.username, input_data.password)
    if login_state['status'] == 'error':
        return RedirectResponse(url="/?alert=Invalid Credentials", status_code=302)
    access_token = login_state['token']
    rr = RedirectResponse(url="/member", status_code=302)
    rr.set_cookie(
        key=settings.COOKIE_NAME, 
        value=f"Bearer {access_token}", 
        httponly=True

    )  
    return rr


@api_router.post("/member/signup", status_code=200)
async def employee_signup(request: Request, email: str = Form(), password:str = Form(), fName:str = Form(), lName:str = Form()) -> dict:
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

# @app.get("/member/search")
@app.get("/member")
async def member_root(request: Request, response: Response, user: User = Depends(get_current_employee)):
    """
    Get training modules
    """
    # get query params from url
    keyword = request.query_params.get('keyword')
    filter_status =  request.query_params.get('filter')
    training = get_training_invited(user.uid,keyword,filter_status)
    explore = training[0::]
    random.shuffle(training)
    invited = training[0::]
    return EMPLOYEE_TEMPLATES.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "FastAPI",
            "explore": explore,
            "invited": invited,
            "name": user.first_name
        }
    )


@api_router.get("/member/onboard/{val}", status_code=200)
def start_training(request: Request, response: Response, user: User = Depends(get_current_employee)):
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
            "modules": modules + modules,
            "name": user.first_name
        }
    )


@api_router.get("/member/finish/{val}", status_code=200)
def complete_training(request: Request, response: Response, user: User = Depends(get_current_employee)):
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

@api_router.post("/member/account", status_code=200)
@api_router.get("/member/account", status_code=200)
def member_view_account(request: Request, response: Response, user: User = Depends(get_current_employee)):
    """
    Root GET
    """
    if not user:
        return RedirectResponse(url="/logout", status_code=302)
   
    training = [
    {
        "id": 1,
        "role": "Dispatch",
        "company": "Owlo",
        "status": "Completed",
    }
    ]
        
        
    
    return EMPLOYEE_TEMPLATES.TemplateResponse(
        "account.html",
        {
            "request": request,
            "training": training,
            "email": user.email,
            "name": user.first_name,
            "alert": request.query_params.get('alert')
        }
    )


@api_router.post("/member/update_email", status_code=200)
async def update_email(request: Request, response: Response, user: User = Depends(get_current_employee), email: str = Form()) -> dict:
    """
    Update email for the current member
    """
    state = employee_change_self_email(user.uid, email, user.email)
    if state['status'] == 'success':
        return RedirectResponse(url='/member/account')
    else:
        return RedirectResponse(url='/member/account?alert='+str(state['body']))
    return state


@api_router.post("/member/update_password", status_code=200)
async def update_password(request: Request, response: Response, user: User = Depends(get_current_employee), cur_password: str = Form(), new_password:str = Form()) -> dict:
    """
    Update password for the current member
    """
    if len(new_password) < 6:
        return RedirectResponse(url='/member/account?alert=Password must be at least 6 characters long')
    if not re.search(r'[A-Z]', new_password):
        return RedirectResponse(url='/member/account?alert=Password must contain at least one uppercase letter')
    if not re.search(r'[a-z]', new_password):
        return RedirectResponse(url='/member/account?alert=Password must contain at least one lowercase letter')
    if not re.search(r'[0-9]', new_password):
        return RedirectResponse(url='/member/account?alert=Password must contain at least one number')
    
    state = employee_change_password(user.uid, user.email, cur_password, new_password)
    if state['status'] == 'success':
        return RedirectResponse(url='/member/account')
    else:
        return RedirectResponse(url='/member/account?alert='+str(state['body']))
    return state

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