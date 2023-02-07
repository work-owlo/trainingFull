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
from manager_auth import *
from company import *
from managers import *
from roles import *

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
oauth2_company = OAuth2PasswordBearerWithCookie(tokenUrl="/company/token")

"""MUTUAL AUTH"""
@app.post("/logout", response_class=HTMLResponse)
@app.get("/logout", response_class=HTMLResponse)
def logout_get(token: str = Depends(oauth2_scheme)):
    response = RedirectResponse(url="/")
    delete_session_token_db(token)
    response.delete_cookie("access_token")
    return response


@app.post("/forgotPassword", response_class=HTMLResponse)
def forgot_password(response:Response, request: Request, email: str = Form()):
    state = employee_forgot_password(email)
    return RedirectResponse(url="/?alert=Password Reset Email Sent", status_code=302)


@app.post("/company/forgotPassword", response_class=HTMLResponse)
def company_forgot_password(response:Response, request: Request, email: str = Form()):
    state = manager_forgot_password(email)
    return RedirectResponse(url="/company?alert=Password Reset Email Sent", status_code=302)


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
async def login(response: Response, username: str = Form(), password: str = Form()):
    ''' Login a user '''
    login_state = employee_login(username, password)
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
async def employee_signup(response: Response,request: Request, email: str = Form(), password:str = Form(), fName:str = Form(), lName:str = Form()) -> dict:
    """
    Root GET
    """
    state = employee_create_account(fName, lName, email, password)
    if state['status'] == 'success':
        rr = await login(response, email, password)
        return rr
    else:
        redirect_url = URL(request.url_for('employee_landing')).include_query_params(alert=str(state['body']))
        return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@app.get("/member")
async def member_root(request: Request, response: Response, user: User = Depends(get_current_employee)):
    """
    Get training modules
    """
    if user == None or not user:
        return RedirectResponse(url="/logout", status_code=302)

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
    if user == None or not user:
        return RedirectResponse(url="/logout", status_code=302)

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
    if user == None or not user:
        return RedirectResponse(url="/logout", status_code=302)
        
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
    if user == None or not user:
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
    if user == None or not user:
        return RedirectResponse(url="/logout", status_code=302)
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
    if user == None or not user:
        return RedirectResponse(url="/logout", status_code=302)
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


def get_current_manager(response: Response, token: str = Depends(oauth2_company)) -> User:
    """
    Get the current user from the cookies in a request.
    Use this function when you want to lock down a route so that only 
    authenticated users can see access the route.
    """
    if token == None:
        return False
    user = manager_verify_login(token)
    if user['status'] == 'error':
        return False
    # refreshed_token = manager_refresh_token(user['body']['token'])
    # print(refreshed_token)
    # response.set_cookie(
    #     key="access_token", 
    #     value=f"Bearer {refreshed_token['token']}", 
    #     httponly=True
    # )  
    return user['body']['user']


@api_router.post("/company", status_code=200)
@api_router.get("/company", status_code=200)
def company_landing(response:Response, request: Request, alert=None) -> dict:
    '''Landing Page with auth options'''
    # print(verify_token_employee(oauth2_scheme))
    cookie = request.cookies.get('access_token')
    if cookie:
        return RedirectResponse(url="/company/team") 
    return EMPLOYER_TEMPLATES.TemplateResponse(
        "landing.html",
        {
            "request": request,
            "alert":alert
        }
    )

'''AUTH'''


@app.post("/company/token")
async def company_login(response: Response, username: str = Form(), password: str = Form()):
    ''' Login a user '''
    login_state = manager_login(username, password)
    if login_state['status'] == 'error':
        return RedirectResponse(url="/company/?alert=Invalid Credentials", status_code=302)
    access_token = login_state['token']
    rr = RedirectResponse(url="/company/team", status_code=302)
    rr.set_cookie(
        key=settings.COOKIE_NAME, 
        value=f"Bearer {access_token}", 
        httponly=True
    )  
    return rr


@api_router.post("/company/signup", status_code=200)
async def employee_signup(response: Response,request: Request, email: str = Form(), password:str = Form(), fName:str = Form(), lName:str = Form()) -> dict:
    """
    Create a new company account
    """
    state = manager_create_admin_account(fName, lName, email, password)
    if state['status'] == 'success':
        rr = await company_login(response, email, password)
        return rr
        # redirect_url = URL(request.url_for('member_root'))
        # return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    else:
        redirect_url = URL(request.url_for('company_landing')).include_query_params(alert=str(state['body']))
        return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@app.post("/company/logout", response_class=HTMLResponse)
@app.get("/company/logout", response_class=HTMLResponse)
def logout_get(token: str = Depends(oauth2_scheme)):
    ''' Logout a user '''
    response = RedirectResponse(url="/company")
    delete_session_token_db(token)
    response.delete_cookie("access_token")
    return response


@api_router.get("/company/add_company", status_code=200)
def company_add_company(response:Response, request: Request, alert=None, manager: Manager = Depends(get_current_manager)) -> dict:
    '''Form to input company information'''
    if not manager:
        return RedirectResponse(url="/company/logout")
    elif manager.company_id != None:
        return RedirectResponse(url="/company/team")

    return EMPLOYER_TEMPLATES.TemplateResponse(
        "addCompany.html",
        {
            "request": request,
            "alert":alert,
            "name":manager.first_name,
        }
    )

@api_router.post("/company/add_company", status_code=200)
async def company_add_company_post(response:Response, request: Request, manager: Manager = Depends(get_current_manager), name: str = Form(), description: str = Form()) -> dict:
    '''Form to input company information'''
    if not manager:
        return RedirectResponse(url="/company/logout")
    elif manager.company_id != None:
        return RedirectResponse(url="/company/team")
    state = add_company(manager.uid, name, description)
    if state['status'] == 'success':
        return RedirectResponse(url="/company/team", status_code=302)
    else:
        return RedirectResponse(url="/company/add_company?alert="+str(state['body']))


@api_router.post("/company/update_email", status_code=200)
async def company_update_email(request: Request, response: Response, manager: Manager = Depends(get_current_manager), email: str = Form()) -> dict:
    """
    Update email for the current member
    """
    if not manager:
        return RedirectResponse(url="/company/logout")
    elif manager.company_id == None:
        return RedirectResponse(url="/company/add_company")

    state = manager_change_self_email(manager.uid, manager.email, email)
    if state['status'] == 'success':
        return RedirectResponse(url='/company/account')
    else:
        return RedirectResponse(url='/company/account?alert='+str(state['body']))
    return state


@api_router.post("/company/update_company_name", status_code=200)
async def company_update_email(request: Request, response: Response, manager: Manager = Depends(get_current_manager), company_name: str = Form()) -> dict:
    """
    Update email for the current member
    """
    if not manager:
        return RedirectResponse(url="/company/logout")
    elif manager.company_id == None:
        return RedirectResponse(url="/company/add_company")

    state = update_company_name(manager.uid, company_name, manager.company_id)
    if state['status'] == 'success':
        return RedirectResponse(url='/company/account')
    else:
        return RedirectResponse(url='/company/account?alert='+str(state['body']))
    return state


@api_router.post("/company/update_password", status_code=200)
async def company_update_password(request: Request, response: Response, manager: Manager = Depends(get_current_manager), cur_password: str = Form(), new_password:str = Form()) -> dict:
    """
    Update password for the current company
    """
    if not manager:
        return RedirectResponse(url="/company/logout")
    elif manager.company_id == None:
        return RedirectResponse(url="/company/add_company")

    if len(new_password) < 6:
        return RedirectResponse(url='/company/account?alert=Password must be at least 6 characters long')
    if not re.search(r'[A-Z]', new_password):
        return RedirectResponse(url='/company/account?alert=Password must contain at least one uppercase letter')
    if not re.search(r'[a-z]', new_password):
        return RedirectResponse(url='/company/account?alert=Password must contain at least one lowercase letter')
    if not re.search(r'[0-9]', new_password):
        return RedirectResponse(url='/company/account?alert=Password must contain at least one number')
    
    state = manager_change_password(manager.uid, manager.email, cur_password, new_password)
    if state['status'] == 'success':
        return RedirectResponse(url='/company/account')
    else:
        return RedirectResponse(url='/company/account?alert='+str(state['body']))
    return state


@api_router.get("/company/team", status_code=200)
def view_company_team(response: Response, request: Request,  manager: Manager = Depends(get_current_manager)) -> dict:
    """
    Get all the members of this company
    """
    if not manager:
        return RedirectResponse(url="/company/logout")
    elif manager.company_id == None:
        return RedirectResponse(url="/company/add_company")
    keyword = request.query_params.get('keyword')
    filter_search = request.query_params.get('filter')
    if keyword != None:
        keyword = keyword.strip()
    if filter_search != None:
        filter_search = filter_search.strip()
    members = get_team(manager.company_id, keyword, filter_search)
    roles = get_roles(manager.company_id)
    print(roles)
    return EMPLOYER_TEMPLATES.TemplateResponse(
        "team.html",
        {
            "request": request,
            "members": members,
            "name": manager.first_name,
            "keyword": keyword if keyword != None else '',
            "filter": filter_search if filter_search != None else '',
            "roles": roles

        }
    )

@api_router.post("/company/assign_employee", status_code=200)
def assign_employee(response: Response, request: Request,  id_input: str = Form(), first_name: str = Form(), last_name: str = Form(), email: str = Form(), role_id: str = Form(), employment_type: str = Form(), manager: Manager = Depends(get_current_manager)) -> dict:
    if not manager:
        return RedirectResponse(url="/company/logout")
    elif manager.company_id == None:
        return RedirectResponse(url="/company/add_company")

    assign = assign_employee_role(manager.company_id, id_input, first_name, last_name, email, role_id, employment_type)
    if assign['status'] == 'success':
        return RedirectResponse(url='/company/team', status_code=302)
    else:
        return RedirectResponse(url='/company/team?alert='+str(assign['body']), status_code=302)
    

@api_router.get("/company/roles", status_code=200)
def view_company_roles(response: Response, request: Request,  manager: Manager = Depends(get_current_manager)) -> dict:
    """
    Get all the roles of this company
    """
    if not manager:
        return RedirectResponse(url="/company/logout", status_code=302)
    elif manager.company_id == None:
        return RedirectResponse(url="/company/add_company", status_code=302)

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
def add_company_role(response: Response, request: Request,  manager: Manager = Depends(get_current_manager)) -> dict:
    """
    Add new role to this company
    """
    if not manager:
        return RedirectResponse(url="/company/logout")
    elif manager.company_id == None:
        return RedirectResponse(url="/company/add_company")

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
def add_modules(role_id:str, response: Response, request: Request,  manager: Manager = Depends(get_current_manager)) -> dict:
    """
    Add new module
    """
    if not manager:
        return RedirectResponse(url="/company/logout")
    elif manager.company_id == None:
        return RedirectResponse(url="/company/add_company")

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
def onboarding_preview(role_id:str, response: Response, request: Request,  manager: Manager = Depends(get_current_manager)) -> dict:
    """
    Preview the onboarding
    """
    if not manager:
        return RedirectResponse(url="/company/logout")
    elif manager.company_id == None:
        return RedirectResponse(url="/company/add_company")
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

@api_router.post("/company/account", status_code=200)
@api_router.get("/company/account", status_code=200)
def view_account(response: Response, request: Request,  manager: Manager = Depends(get_current_manager)) -> dict:
    """
    View and edit the company account
    """
    if not manager:
        return RedirectResponse(url="/company/logout")
    elif manager.company_id == None:
        return RedirectResponse(url="/company/add_company")

    company_name = get_company(manager.company_id)['body']['company_name']

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
            "email": manager.email,
            "company_name": company_name,
            "name": manager.first_name,
            "alert": request.query_params.get("alert", None)
        }
    )



app.include_router(api_router)