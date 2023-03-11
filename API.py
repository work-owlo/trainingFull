from fastapi import FastAPI, Header, HTTPException, Depends, status, Response, Request, APIRouter, Form
from pydantic import BaseModel, EmailStr
# from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.datastructures import URL
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

from typing import List
from pathlib import Path
import re

from employee_auth import *
from employees import *
from classes import *
from auth_classes import *
from manager_auth import *
from company import *
from managers import *
from roles import *
from training import *
from soft_training import *
from parse import *
from element import *
from graph import *

app = FastAPI()

origins = [
    "https://owlo.co",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


api_router = APIRouter()
BASE_PATH = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory="static"), name="static")
EMPLOYEE_TEMPLATES = Jinja2Templates(directory=str(BASE_PATH / "templates/employees"))
EMPLOYER_TEMPLATES = Jinja2Templates(directory=str(BASE_PATH / "templates/employer"))

oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="token")

oauth2_company = OAuth2PasswordBearerWithCookie(tokenUrl="/company/token")


@api_router.post("/testCors")
def test_cors(request: Request):
    return {"message": "success"}
    

"""MUTUAL AUTH"""
favicon_path = 'favicon.ico'
@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse(favicon_path)


@app.get("/privacy", response_class=HTMLResponse)
def privacy_policy(request: Request):
    return EMPLOYEE_TEMPLATES.TemplateResponse(
        "privacyPolicy.html",
        {
            "request": request,
        }
    )


@app.get("/terms", response_class=HTMLResponse)
def privacy_policy(request: Request):
    return EMPLOYEE_TEMPLATES.TemplateResponse(
        "terms.html",
        {
            "request": request,
        }
    )


@app.get("/company/privacy", response_class=HTMLResponse)
def privacy_policy(request: Request):
    return EMPLOYER_TEMPLATES.TemplateResponse(
        "privacyPolicy.html",
        {
            "request": request,
        }
    )

@app.get("/company/terms", response_class=HTMLResponse)
def privacy_policy(request: Request):
    return EMPLOYER_TEMPLATES.TemplateResponse(
        "terms.html",
        {
            "request": request,
        }
    )

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
    employee_forgot_password(email)
    return RedirectResponse(url="/?alert=Password Reset Email Sent", status_code=302)


@app.post("/company/forgotPassword", response_class=HTMLResponse)
def company_forgot_password(response:Response, request: Request, email: str = Form()):
    manager_forgot_password(email)
    return RedirectResponse(url="/company?alert=Password Reset Email Sent", status_code=302)


""" EMPLOYEE ROUTES """


@api_router.get("/", status_code=200)
def employee_landing(response:Response, request: Request, alert=None) -> dict:
    '''Landing Page with auth options'''
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
    refreshed_token = employee_refresh_token(user['body']['token'])
    if refreshed_token and refreshed_token['status'] == 'success':
        user['body']['user'].token = refreshed_token['body']['token']
    else:
        user['body']['user'].token = None
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
async def employee_signup(response: Response,request: Request, email: str = Form(), password:str = Form(), fName:str = Form(), lName:str = Form(), legalCheckbox:bool = Form(False)) -> dict:
    """
    Root GET
    """
    if not legalCheckbox:
        redirect_url = URL(request.url_for('employee_landing')).include_query_params(alert='Please agree to the terms and conditions')
        return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    state = employee_create_account(fName, lName, email, password)
    if state['status'] == 'success':
        rr = await login(response, email, password)
        create_account_emp(email)
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
    alert = request.query_params.get('alert')
    invited = get_training_invited(user.uid,keyword,filter_status)
    response = EMPLOYEE_TEMPLATES.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "FastAPI",
            "invited": invited,
            "name": user.first_name,
            "keyword": keyword if keyword else "",
            "filter": filter_status,
            "alert": alert
        }
    )
    if user.token != None:
        response.set_cookie(
            key="access_token",
            value=f"Bearer {user.token}",
            httponly=True
        )
    return response


@api_router.get("/member/onboard/{team_id}", status_code=200)
def start_training(request: Request, response: Response, team_id:str, user: User = Depends(get_current_employee)):
    """
    Root GET
    """
    if user == None or not user:
        return RedirectResponse(url="/logout", status_code=302)

    role_name = get_training_permission(user.uid, team_id)
    modules = get_training_tools(team_id)
    progress = get_training_progress(team_id)
    if not role_name:
        return RedirectResponse(url="/member?alert=" + str("You are not permitted to view this role"), status_code=302)

    response = EMPLOYEE_TEMPLATES.TemplateResponse(
        "train.html",
        {
            "request": request,
            "modules": modules,
            "progress": progress,
            "team_id": team_id,
            "name": user.first_name,
            "role_name": role_name
        }
    )
    if user.token != None:
        response.set_cookie(
            key="access_token",
            value=f"Bearer {user.token}",
            httponly=True
        )
    return response


@api_router.get("/member/onboard/module/{rt_id}", status_code=200)
async def view_module(request: Request, response: Response, rt_id:str, user: User = Depends(get_current_employee)) -> dict:
    """
    Get module for the current user
    """
    if user == None or not user:
        return RedirectResponse(url="/logout", status_code=302)
    
    permissions = get_module_permissions(user.uid, rt_id)
    if not permissions:
        return RedirectResponse(url="/member?alert=" + str("You are not permitted to view this module"), status_code=302)

    modules = get_training_modules_tool(user.uid, rt_id)
    role = get_role_info(permissions)
    response = EMPLOYEE_TEMPLATES.TemplateResponse(
        "module.html",
        {
            "request": request,
            "modules": modules,
            "name": user.first_name,
            "role": role
        }
    )
    if user.token != None:
        response.set_cookie(
            key="access_token",
            value=f"Bearer {user.token}",
            httponly=True
        )
    return response


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
    response = EMPLOYEE_TEMPLATES.TemplateResponse(
        "complete.html",
        {
            "request": request,
            "metrics": metrics
        }
    )
    if user.token != None:
        response.set_cookie(
            key="access_token",
            value=f"Bearer {user.token}",
            httponly=True
        )
    return response


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
        
    response = EMPLOYEE_TEMPLATES.TemplateResponse(
        "account.html",
        {
            "request": request,
            "training": training,
            "email": user.email,
            "name": user.first_name,
            "alert": request.query_params.get('alert')
        }
    )
    if user.token != None:
        response.set_cookie(
            key="access_token",
            value=f"Bearer {user.token}",
            httponly=True
        )
    return response


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
    refreshed_token = manager_refresh_token(user['body']['token'])
    if refreshed_token and refreshed_token['status'] == 'success':
        user['body']['user'].token = refreshed_token['body']['token']
    else:
        user['body']['user'].token = None
    return user['body']['user']


@api_router.get("/company/roles", status_code=200)
def view_company_roles(response: Response, request: Request, manager: Manager = Depends(get_current_manager)) -> dict:
    """
    Get all the roles of this company
    """
    keyword = request.query_params.get('keyword')
    if keyword != None:
        keyword = keyword.strip()

    if not manager:
        return RedirectResponse(url="/company/logout", status_code=302)
    elif manager.company_id == None:
        return RedirectResponse(url="/company/add_company", status_code=302)
    roles = get_role_comprehensive(manager.company_id, keyword)

    response = EMPLOYER_TEMPLATES.TemplateResponse(
        "roles.html",
        {
            "request": request,
            "roles": roles,
            "keyword": keyword if keyword != None else '',
            "name": manager.first_name
        }

    )

    if manager.token != None:
        response.set_cookie(
            key="access_token",
            value=f"Bearer {manager.token}",
            httponly=True
        )
    return response



@api_router.post("/company", status_code=200)
@api_router.get("/company", status_code=200)
def company_landing(response:Response, request: Request, alert=None) -> dict:
    '''Landing Page with auth options'''
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
async def employee_signup(response: Response,request: Request, email: str = Form(), password:str = Form(), fName:str = Form(), lName:str = Form(), legalCheckbox:bool = Form(False)) -> dict:
    """
    Create a new company account
    """
    if not legalCheckbox:
        redirect_url = URL(request.url_for('company_landing')).include_query_params(alert='You must agree to the terms and conditions')
        return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    state = manager_create_admin_account(fName, lName, email, password)
    if state['status'] == 'success':
        rr = await company_login(response, email, password)
        uid = state['body']['uid']
        create_account_comp(email)
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

    response = EMPLOYER_TEMPLATES.TemplateResponse(
        "addCompany.html",
        {
            "request": request,
            "alert":alert,
            "name":manager.first_name,
        }
    )

    if manager.token != None:
        response.set_cookie(
            key="access_token",
            value=f"Bearer {manager.token}",
            httponly=True
        )
    return response


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
    response = EMPLOYER_TEMPLATES.TemplateResponse(
        "team.html",
        {
            "request": request,
            "members": members,
            "name": manager.first_name,
            "keyword": keyword if keyword != None else '',
            "filter": filter_search if filter_search != None else '',
            "roles": roles,
            "alert": request.query_params.get('alert') if request.query_params.get('alert') != None else ''

        }
    )

    if manager.token != None:
        response.set_cookie(
            key="access_token",
            value=f"Bearer {manager.token}",
            httponly=True
        )
    return response


@api_router.post("/company/assign_employee", status_code=200)
def assign_employee(response: Response, request: Request,  id_input: str = Form(), first_name: str = Form(), last_name: str = Form(), email: str = Form(), role_id: str = Form(), employment_type: str = Form(), manager: Manager = Depends(get_current_manager)) -> dict:
    if not manager:
        return RedirectResponse(url="/company/logout")
    elif manager.company_id == None:
        return RedirectResponse(url="/company/add_company")
    email = email.lower()
    email = email.strip()
    assign = assign_employee_role(manager.company_id, id_input, first_name, last_name, email, role_id, employment_type)
    if assign['status'] == 'success':
        training_invite_email(email)
        return RedirectResponse(url='/company/team', status_code=302)
    else:
        return RedirectResponse(url='/company/team?alert='+str(assign['body']), status_code=302)
    

@api_router.get("/company/employee/view/{team_id}", status_code=200)
def view_employee(response: Response, request: Request, team_id: str, manager: Manager = Depends(get_current_manager)) -> dict:
    """
    Get all the roles of this company
    """
    if not manager:
        return RedirectResponse(url="/company/logout", status_code=302)
    elif manager.company_id == None:
        return RedirectResponse(url="/company/add_company", status_code=302)
    # employee = get_employee(manager.company_id, employee_id)
    if not check_emp_in_team(manager.company_id, team_id):
        return RedirectResponse(url="/company/team", status_code=302)
    response = EMPLOYER_TEMPLATES.TemplateResponse(
        "employee.html",
        {
            "request": request,
            "employee": 'Hi',
            "name": manager.first_name
        }
    )

    if manager.token != None:
        response.set_cookie(
            key="access_token",
            value=f"Bearer {manager.token}",
            httponly=True
        )
    return response


@api_router.post("/company/employee/remind/{team_id}", status_code=200)
def remind_employee(response: Response, request: Request, team_id: str, manager: Manager = Depends(get_current_manager)) -> dict:
    """
    Get all the roles of this company
    """
    if not manager:
        return RedirectResponse(url="/company/logout", status_code=302)
    elif manager.company_id == None:
        return RedirectResponse(url="/company/add_company", status_code=302)
    # employee = get_employee(manager.company_id, team_id)
    if not check_emp_in_team(manager.company_id, team_id):
        return RedirectResponse(url="/company/team", status_code=302)
    email = get_employee_email(team_id)
    if email == None:
        return RedirectResponse(url="/company/team", status_code=302)
    training_reminder_email(email)
    response = EMPLOYER_TEMPLATES.TemplateResponse(
        "employee.html",
        {
            "request": request,
            "employee": 'Hi',
            "name": manager.first_name
        }
    )

    if manager.token != None:
        response.set_cookie(
            key="access_token",
            value=f"Bearer {manager.token}",
            httponly=True
        )
    return response



@api_router.get("/company/add_role", status_code=200)
def add_company_role(response: Response, request: Request,  manager: Manager = Depends(get_current_manager)) -> dict:
    """
    Add new role to this company
    """
    if not manager:
        return RedirectResponse(url="/company/logout")
    elif manager.company_id == None:
        return RedirectResponse(url="/company/add_company")

    modules = get_tools()
    response = EMPLOYER_TEMPLATES.TemplateResponse(
        "addRole.html",
        {
            "request": request,
            "modules": modules,
            "name": manager.first_name,
            "alert": request.query_params.get('alert') if request.query_params.get('alert') != None else ''
        }
    )

    if manager.token != None:
        response.set_cookie(
            key="access_token",
            value=f"Bearer {manager.token}",
            httponly=True
        )
    return response


@api_router.post("/company/add_role", status_code=200)
async def add_company_role(response: Response, request: Request,  role_name: str = Form(), role_description: str = Form(), manager: Manager = Depends(get_current_manager)) -> dict:
    """
    Add new role to this company
    """
    if not manager:
        return RedirectResponse(url="/company/logout")
    elif manager.company_id == None:
        return RedirectResponse(url="/company/add_company")
    form_data = await request.form()
    form_data = jsonable_encoder(form_data)
    role_id = generate_uid()
    
    available_tools = get_tools()
    # verify one or more tools are selected
    if sum([1 for tool in available_tools if tool.id in form_data]) == 0:
        return RedirectResponse(url='/company/add_role?alert=Please select at least one tool', status_code=302)

    add = add_role(manager.company_id, role_id, role_name, role_description)
    if add['status'] == 'error':
        return RedirectResponse(url='/company/add_role?alert='+str(add['body']), status_code=302)

    for tool in available_tools:
        if tool.id in form_data:
            add_role_tool_relationship(role_id, tool.id)
    return RedirectResponse(url='/company/add_modules/'+str(role_id), status_code=302)


@api_router.post("/company/role/delete", status_code=200)
def delete_role_api(response: Response, request: Request, delete_role_id: str = Form(), manager: Manager = Depends(get_current_manager)) -> dict:
    """
    Delete role to this company
    """
    if not manager:
        return RedirectResponse(url="/company/logout")
    elif manager.company_id == None:
        return RedirectResponse(url="/company/add_company")

    delete = delete_role(manager.company_id, delete_role_id)
    if delete['status'] == 'success':
        return RedirectResponse(url='/company/roles', status_code=302)
    else:
        return RedirectResponse(url='/company/roles?alert='+str(delete['body']), status_code=302)


@api_router.post("/company/employee/unassign", status_code=200)
def unassign_role(response: Response, request: Request, team_id: str = Form(), manager: Manager = Depends(get_current_manager)) -> dict:
    """
    Unassign role to this company
    """
    if not manager:
        return RedirectResponse(url="/company/logout")
    elif manager.company_id == None:
        return RedirectResponse(url="/company/add_company")

    unassign = unasign_employee_role(manager.company_id, team_id)
    if unassign['status'] == 'success':
        return RedirectResponse(url='/company/team', status_code=302)
    else:
        return RedirectResponse(url='/company/team?alert='+str(unassign['body']), status_code=302)


@api_router.get("/company/add_modules/{role_id}", status_code=200)
def add_modules(role_id:str, response: Response, request: Request,  manager: Manager = Depends(get_current_manager)) -> dict:
    """
    Add new module
    """
    if not manager:
        return RedirectResponse(url="/company/logout")
    elif manager.company_id == None:
        return RedirectResponse(url="/company/add_company")
    # check role belongs to company
    permission = check_role_in_company(manager.company_id, role_id)
    if not permission:
        return RedirectResponse(url="/company/roles", status_code=302)

    # check that role is in process of being edited
    tool = get_role_tools_remaining(role_id)
    if not tool:
        complete = complete_role(manager.company_id, role_id)
        if complete['status'] == 'error':
            return RedirectResponse(url="/company/roles?alert="+str(complete['body']), status_code=302)
        else:
            return RedirectResponse(url="/company/roles?alert=Role Added", status_code=302)

    public_modules = get_public_modules(tool.tool_id,manager.company_id)
    private_modules = get_private_modules(tool.tool_id, manager.company_id)
    # modules = []
    response = EMPLOYER_TEMPLATES.TemplateResponse(
        "addModules.html",
        {
            "request": request,
            "public_modules": public_modules,
            "private_modules": private_modules,
            "name": manager.first_name, 
            "tool": tool,
            "role_id": role_id
        }
    )

    if manager.token != None:
        response.set_cookie(
            key="access_token",
            value=f"Bearer {manager.token}",
            httponly=True
        )
    return response


@api_router.post("/company/add_module_redirect/{tool_id}/{role_id}", status_code=200)
def add_module_redirect(tool_id:str, role_id:str, response: Response, request: Request,  manager: Manager = Depends(get_current_manager)) -> dict:
    # print(tool_id)
    # if not manager:
    #     return RedirectResponse(url="/company/logout")
    # elif manager.company_id == None:
    #     return RedirectResponse(url="/company/add_company")
    
    # # check role belongs to company
    # permission = check_role_in_company(manager.company_id, role_id)
    # if not permission:
    #     return RedirectResponse(url="/company/roles", status_code=302)
    
    # # check that role is in process of being edited
    # tool = get_role_tools_remaining(role_id)
    # if not tool:
    #     complete = complete_role(manager.company_id, role_id)
    #     if complete['status'] == 'error':
    #         return RedirectResponse(url="/company/roles?alert="+str(complete['body']), status_code=302)
    #     else:
    #         return RedirectResponse(url="/company/roles?alert=Role Added", status_code=302)
    # print(tool_id)
    if tool_id == '1':
        return RedirectResponse(url="/company/add_module/simulator/"+str(role_id) + "/" + str(tool_id), status_code=302)
    elif tool_id == '2':
        return RedirectResponse(url="/company/add_module/simulator/"+str(role_id) + "/" + str(tool_id), status_code=302)
    elif tool_id == '3':
        return RedirectResponse(url="/company/add_module/compliance/"+str(role_id), status_code=302)
    elif tool_id == '4':
        return RedirectResponse(url="/company/add_module/software/"+str(role_id), status_code=302)
    else:
        return RedirectResponse(url="/company/roles", status_code=302)
        


@api_router.post("/company/add_modules", status_code=200)
async def add_modules_api(response: Response, request: Request, tool_id:str = Form(), role_id: str = Form(), manager: Manager = Depends(get_current_manager)) -> dict:
    '''Add modules to role'''
    if not manager:
        return RedirectResponse(url="/company/logout")
    elif manager.company_id == None:
        return RedirectResponse(url="/company/add_company")

    # verify permisison to add modules to the role
    permission = check_role_in_company(manager.company_id, role_id)
    if not permission:
        return RedirectResponse(url="/company/roles?alert=Error", status_code=302)

    # check tool_id in roll tools and 
    permission = verify_pending_rool_tool_relationship(role_id, tool_id)
    if not permission:
        return RedirectResponse(url="/company/roles?alert=Error", status_code=302)

    # for each module, verify permissions to add the module (access)
    form_data = await request.form()
    form_data = jsonable_encoder(form_data)

    valid_modules_list = []
    for module in form_data:
        if module == 'role_id':
            continue
        permission = verify_module_access(manager.company_id, module, tool_id)
        if permission:
            valid_modules_list.append(module)
    if len(valid_modules_list) == 0:    
        return RedirectResponse(url='/company/add_modules/'+str(role_id) + "?alert=" + str('Please add atleast one module'), status_code=302)
    
    # add modules to role
    for module in valid_modules_list:
        add_module_to_role(role_id, module)

    # change rool_tool status to active
    update_role_tool_status(role_id, tool_id, 'active')

    return RedirectResponse(url='/company/add_modules/'+str(role_id), status_code=302)


@api_router.get("/company/role/edit/{role_id}", status_code=200)
def edit_role(role_id:str, response: Response, request: Request,  manager: Manager = Depends(get_current_manager)) -> dict:
    """
    Preview the onboarding
    """
    if not manager:
        return RedirectResponse(url="/company/logout")
    elif manager.company_id == None:
        return RedirectResponse(url="/company/add_company")

    # check role belongs to company
    permission = check_role_in_company(manager.company_id, role_id)
    if not permission:
        return RedirectResponse(url="/company/roles", status_code=302)

    role = get_role_info(role_id)
    if role.status != 'active':
        return RedirectResponse(url="/company/roles", status_code=302)
    modules = get_role_modules(role_id)
    response = EMPLOYER_TEMPLATES.TemplateResponse(
        "editRole.html",
        {
            "request": request,
            "modules": modules,
            "sections": modules,
            "name": manager.first_name,
            "role": role
        }
    )

    if manager.token != None:
        response.set_cookie(
            key="access_token",
            value=f"Bearer {manager.token}",
            httponly=True
        )
    return response


@api_router.get("/company/role/view/{role_id}", status_code=200)
def view_role(role_id:str, response: Response, request: Request,  manager: Manager = Depends(get_current_manager)) -> dict:
    """
    Preview the onboarding
    """
    if not manager:
        return RedirectResponse(url="/company/logout")
    elif manager.company_id == None:
        return RedirectResponse(url="/company/add_company")

    # check role belongs to company
    permission = check_role_in_company(manager.company_id, role_id)
    if not permission:
        return RedirectResponse(url="/company/roles", status_code=302)

    role = get_role_info(role_id)
    if role.status != 'active':
        return RedirectResponse(url="/company/roles", status_code=302)
    response = EMPLOYER_TEMPLATES.TemplateResponse(
        "viewRole.html",
        {
            "request": request,
            "name": manager.first_name,
            "role": role
        }
    )

    if manager.token != None:
        response.set_cookie(
            key="access_token",
            value=f"Bearer {manager.token}",
            httponly=True
        )
    return response


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
        
    
    response = EMPLOYER_TEMPLATES.TemplateResponse(
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

    if manager.token != None:
        response.set_cookie(
            key="access_token",
            value=f"Bearer {manager.token}",
            httponly=True
        )
    return response


# COMPANY TRAINING ROUTES

# initiate test 
@api_router.get("/company/test_module/start/{module_id}/{role_id}/{tool_id}", status_code=200)
def startSimulator(response: Response, request: Request, role_id:str, module_id: str, tool_id:str, manager: Manager = Depends(get_current_manager)) -> dict:
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""SELECT access, company_id FROM module WHERE module_id = %s and tool_id = %s""", (module_id, tool_id))
        module = cur.fetchone()
        if module is None:
            return RedirectResponse(url=f"/company/add_modules/{role_id}?alert='Error'", status_code=302)
        else:
            access = module['access']
            company_id = module['company_id']
            if access == 'private' and company_id != manager.company_id:
                return RedirectResponse(url=f"/company/add_modules/{role_id}?alert='Error'", status_code=302)
    
    if tool_id != 4:
        add_training_sample(module_id, manager.company_id, tool_id)
    else:
        add_training_graph(module_id, manager.company_id)

    # redirect to testSimulator
    if tool_id == '1' or tool_id == '2':
        return RedirectResponse(url=f"/company/test_module/simulator/{module_id}/{role_id}", status_code=302)
    elif tool_id == '3':
        return RedirectResponse(url=f"/company/test_module/compliance/{module_id}/{role_id}", status_code=302)
    elif tool_id == '4':
        return RedirectResponse(url=f"/company/test_module/software/{module_id}", status_code=302)
    else:
        return RedirectResponse(url=f"/company/add_modules/{role_id}?alert='Error'", status_code=302)


# SOFTWARE TRAINING ROUTES
@api_router.get("/company/add_module/software", status_code=200)
def add_software_module(response: Response, request: Request,  manager: Manager = Depends(get_current_manager)) -> dict:
    """
    Add new module
    """
    if not manager:
        return RedirectResponse(url="/company/logout")
    elif manager.company_id == None:
        return RedirectResponse(url="/company/add_company")

    response = EMPLOYER_TEMPLATES.TemplateResponse(
        "addSoftware.html",
        {
            "request": request,
            "name": manager.first_name
        }
    )

    if manager.token != None:
        response.set_cookie(
            key="access_token",
            value=f"Bearer {manager.token}",
            httponly=True
        )
    return response


@api_router.get("/company/processSoftware/load/{parse_id}", status_code=200)
def processSoftware(parse_id:str, response: Response, request: Request,  manager: Manager = Depends(get_current_manager)) -> dict:
    if not manager:
        return RedirectResponse(url="/company/logout")
    elif manager.company_id == None:
        return RedirectResponse(url="/company/add_company")
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""SELECT status FROM parse
                    WHERE parse_id = %s""", (parse_id,))
        parse_status = cur.fetchone()
        if parse_status[0] == 'parsed':
            return RedirectResponse(url=f"/company/processSoftware/complete/{parse_id}", status_code=302)
        elif parse_status[0] == 'completed':
            return RedirectResponse(url="/company/add_module/software", status_code=302)
    response = EMPLOYER_TEMPLATES.TemplateResponse(
        "softwareLoading.html",
        {
            "request": request,
            "name": manager.first_name,
            "parse_id": parse_id
        }
    )
    return response


@api_router.post("/company/add_module/software", status_code=200)
def addSoftwarePost(response: Response, request: Request,  manager: Manager = Depends(get_current_manager), url: str = Form(...), website_name: str = Form(...), website_description: str = Form(...)) -> dict:
    if not manager:
        return RedirectResponse(url="/company/logout")
    elif manager.company_id == None:
        return RedirectResponse(url="/company/add_company")
    parse_id = Parse('ai', url, software_name=website_name, company_id  = manager.company_id, description=website_description, add_to_db=True).id
    return RedirectResponse(url=f"/company/processSoftware/load/{parse_id}", status_code=302)


@api_router.get("/company/processSoftware/element/{parse_id}", status_code=200)
def processSoftwareElement(parse_id:str, response: Response, request: Request,  manager: Manager = Depends(get_current_manager)) -> dict:
    '''Comment'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""SELECT status FROM parse
                    WHERE parse_id = %s""", (parse_id,))
        parse_status = cur.fetchone()
        if parse_status[0] == 'parsed':
            return RedirectResponse(url=f"/company/processSoftware/complete/{parse_id}", status_code=302)
        elif parse_status[0] == 'completed':
            return RedirectResponse(url="/company/add_module/software", status_code=302)

    form_id = parser(parse_id)
    if not form_id:
        return RedirectResponse(url=f"/company/processSoftware/complete/{parse_id}", status_code=302)
    
    # get the form
    form = {}
    elements = Webform.get_elements(form_id)
    form['input'] = [element for element in elements if element.type == 'input']
    form['select'] = [element for element in elements if element.type == 'select']
    form['button'] = [element for element in elements if element.type == 'button']
    screenshots = [dict(screenshot) for screenshot in Webform.get_screenshots(form_id, parse_id)]

    element_size_dict = {}
    for element in (elements):
        element_size_dict[element.id] = {'width': element.width, 'height': element.height, 'x': element.x, 'y': element.y}

    select_options = {}
    for select in form['select']:
        select_options[select.id] = [option for option in select.get_select_options()]

    screenshot_size_dict = {}
    for screenshot in screenshots:
        screenshot_size_dict[screenshot['screenshot_name']] = {'y': screenshot['y']}
    
    original_size = {'width': 1000, 'height': 700}
    adjusted_size = {'width': 800, 'height': 300}

    ai_recs = []
    for input in form['input']:
        # random 5 alphanumeric string
        ai_dict = {}
        ai_dict['id'] = input.id
        ai_dict['rec'] = input.generate_sample()
        ai_recs.append(ai_dict)

    response = EMPLOYER_TEMPLATES.TemplateResponse(
        "softwareElement.html",
        {
            "request": request,
            "name": manager.first_name,
            "select_options": select_options,
            "original_size": original_size,
            "size": adjusted_size,
            "form": form,
            "ai_recs": ai_recs,
            "screenshots": screenshots,
            "form_id": form_id,
            "element_size_dict": element_size_dict,
            "screenshot_size_dict": screenshot_size_dict,
            "parse_id": parse_id
        }
    )
    return response


@api_router.post("/company/processSoftware/element/{parse_id}", status_code=200)
def processSoftwareElementSubmit(parse_id:str, response: Response, request: Request,  manager: Manager = Depends(get_current_manager)) -> dict:
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""SELECT status FROM parse
                    WHERE parse_id = %s""", (parse_id,))
        parse_status = cur.fetchone()
        if parse_status[0] == 'parsed':
            return RedirectResponse(url=f"/company/processSoftware/complete/{parse_id}", status_code=302)
        elif parse_status[0] == 'complete':
            return RedirectResponse(url="/company/add_module/software", status_code=302)

    with get_db_connection() as conn:
        cur = conn.cursor()
        for request_key, request_value in request.form.items():
            cur.execute("""UPDATE element 
                        SET generated_value = %s 
                        WHERE id = %s AND parse_id = %s""", (request_value, request_key, parse_id))
            conn.commit()

    return RedirectResponse(url=f"/company/processSoftware/element/{parse_id}", status_code=302)


@api_router.post("/company/processSoftware/deleteElements/{form_id}/{parse_id}", status_code=200)
def processSoftwareDeleteElements(form_id:str, parse_id:str, response: Response, request: Request,  manager: Manager = Depends(get_current_manager)) -> dict:
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""SELECT status FROM parse
                    WHERE parse_id = %s""", (parse_id,))
        parse_status = cur.fetchone()
        if parse_status[0] == 'parsed':
            return RedirectResponse(url=f"/company/processSoftware/complete/{parse_id}", status_code=302)
        elif parse_status[0] == 'complete':
            return RedirectResponse(url="/company/add_module/software", status_code=302)

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""DELETE FROM element 
                    WHERE form_id = %s AND parse_id = %s""", (form_id, parse_id))
        conn.commit()
    return RedirectResponse(url=f"/company/processSoftware/load/{parse_id}", status_code=302)


@api_router.get("/company/processSoftware/complete/{parse_id}", status_code=200)
def processSoftwareComplete(parse_id:str, response: Response, request: Request,  manager: Manager = Depends(get_current_manager)) -> dict:
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""SELECT status FROM parse
                    WHERE parse_id = %s""", (parse_id,))
        parse_status = cur.fetchone()
        if parse_status[0] == 'pending':
            return RedirectResponse(url=f"/company/processSoftware/{parse_id}", status_code=302)
        elif parse_status[0] == 'complete':
            return RedirectResponse(url="/company/add_module/software", status_code=302)

    screenshots = Parse.get_screenshots(parse_id)
    screenshot_size_dict = {}
    for screenshot in screenshots:
        for s in screenshot:
            screenshot_size_dict[s['screenshot_name']] = {'y': s['y']}
    original_size = {'width': 1000, 'height': 700}
    adjusted_size = {'width': 800, 'height': 300}

    response = EMPLOYER_TEMPLATES.TemplateResponse(
        "softwareComplete.html",
        {
            "request": request,
            "name": manager.first_name,
            "screenshot_size_dict": screenshot_size_dict,
            "size": adjusted_size,
            "screenshots": screenshots,
            "parse_id": parse_id
        }
    )
    return response


@api_router.post("/company/processSoftware/deletePage/{parse_id}", status_code=200)
def processSoftwareDeletePage(parse_id:str, page_id:str, response: Response, request: Request,  manager: Manager = Depends(get_current_manager)) -> dict:
    page_id = page_id or request.form['deletingPage']

    # if a child of this page only has one parent, delete it
    with get_db_connection() as conn:
        cur = conn.cursor()
        # get the children of the page
        cur.execute("""SELECT DISTINCT to_page_id FROM element_action WHERE page_id = %s AND page_id != to_page_id""", (page_id,))
        children = cur.fetchall()
        for child in children:
            if int(child[0]) > int(page_id):
                cur.execute("""SELECT COUNT(distinct page_id) as count FROM element_action WHERE to_page_id = %s AND page_id != to_page_id""", (child[0],))
                count = cur.fetchone()
                if count[0] == 1:
                    processSoftwareDeletePage(parse_id, child[0])

    # verify page is in parse
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""DELETE FROM page
                    WHERE page_id = %s AND parse_id = %s""", (page_id, parse_id))
        cur.execute("""DELETE FROM screenshot
                    WHERE node_id = %s AND parse_id = %s""", (page_id, parse_id))
        cur.execute("""DELETE FROM element
                    WHERE page_id = %s AND parse_id = %s""", (page_id, parse_id))
        cur.execute("""DELETE FROM element_action 
                    WHERE page_id = %s""", (page_id,))
        cur.execute("""DELETE FROM cookie 
                    WHERE page_id = %s""", (page_id,))
        cur.execute("""DELETE FROM form
                    WHERE page_id = %s AND parse_id = %s""", (page_id, parse_id))
        conn.commit()

    return RedirectResponse(url=f"/company/processSoftware/complete/{parse_id}", status_code=302)


@api_router.post("/company/processSoftware/completeProcess/{parse_id}", status_code=200)
def completeProcess(parse_id:str, response: Response, request: Request,  manager: Manager = Depends(get_current_manager)) -> dict:
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""SELECT status FROM parse
                    WHERE parse_id = %s""", (parse_id,))
        parse_status = cur.fetchone()
        if parse_status[0] == 'pending':
            # return redirect(url_for('testProcess', parse_id=parse_id))
            return RedirectResponse(url=f"/company/processSoftware/{parse_id}", status_code=302)
        elif parse_status[0] == 'complete':
            return RedirectResponse(url="/company/add_module/software", status_code=302)
    module_id = graph(parse_id, manager.company_id) 
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""UPDATE parse SET status = 'complete'
                    WHERE parse_id = %s""", (parse_id,))
        conn.commit()
    return RedirectResponse(url="/company/processSoftware/testProcess/" + module_id, status_code=302)


@api_router.get("/company/processSoftware/testProcess/{module_id}", status_code=200)
def testProcess(module_id:str, response: Response, request: Request,  manager: Manager = Depends(get_current_manager)) -> dict:

    offsetX = 0
    offsetY = 0
    team_id = manager.company_id
    pending = has_pending_training(team_id, module_id)
    if not pending:
        # return render_template('testSoftware.html', training_id=None, display_next=False, offsetX = offsetX, offsetY = offsetY, size = {'width': 800, 'height': 300}, form = {}, images = [])
        print('ERROR IS HERE')
        response = EMPLOYER_TEMPLATES.TemplateResponse(
            "testSoftware.html",
            {
                "request": request,
                "name": manager.first_name,
                "training_id": None,
                "display_next": False,
                "offsetX": offsetX,
                'element_dict': [{}],
                'screenshot_dict': [{}],
                "offsetY": offsetY,
                "size": {'width': 800, 'height': 300},
                "form": {},
                "images": []
            }
        )
        return response
    original_size = {'width': 1000, 'height': 700}
    adjusted_size = {'width': 800, 'height': 300}
    adjustment_factor =  adjusted_size['width']/original_size['width']
    
    training_id, elements, screenshots = get_next_page(team_id, module_id, adjustment_factor)
    element_size_dict = {}
    for element in (elements['input'] + elements['button']):
        element_size_dict[element['id']] = {'width': element['width'], 'height': element['height'], 'x': element['x'], 'y': element['y']}
    screenshot_size_dict = {}
    for screenshot in screenshots:
        screenshot_size_dict[screenshot['screenshot_name']] = {'y': screenshot['y']}
    
    # get vertical menu
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""SELECT training_status, query_element.element_id
                        FROM training, query_element 
                        WHERE training.module_id = %s AND training.query_id = query_element.query_id
                        ORDER BY training.id ASC
                        """, (module_id,))
        training_status = cur.fetchall()
        training = [dict(status) for status in training_status]
        # get context for each training
        for i in range(len(training)):
            cur.execute("""SELECT context, element_value
                            FROM element
                            WHERE id = %s""", (training[i]['element_id'],))
            context = cur.fetchone()
            training[i]['context'] = context['context']
    
    status_ratio = sum([1 if training[i]['training_status'] == 'completed' else 0 for i in range(len(training))])//len(training)
    display_next = False
    if len(elements['button'] + elements['input']) == 0:
        display_next = True
    
    response = EMPLOYER_TEMPLATES.TemplateResponse(
        "testSoftware.html",
        {
            "request": request,
            "name": manager.first_name,
            "status_ratio": status_ratio,
            "training": training,
            "screenshot_size_dict": screenshot_size_dict,
            "element_size_dict": element_size_dict,
            "training_id": training_id,
            "display_next": display_next,
            "offsetX": offsetX,
            "offsetY": offsetY,
            "original_size": original_size,
            "size": adjusted_size,
            "form": elements,
            "images": screenshots
        }
    )
    return response


@api_router.post("/company/training/reset/{training_id}", status_code=200)
def resetProgress(training_id:str, response: Response, request: Request,  manager: Manager = Depends(get_current_manager)) -> dict:
    '''Update training set status to pending '''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""SELECT team_id, module_id FROM training WHERE training_id = %s""", (training_id,))
        team_id, module_id = cur.fetchone()
        cur.execute("""UPDATE training SET training_status = 'pending', response = ''
                    WHERE team_id = %s AND module_id = %s""", (team_id, module_id))
        conn.commit()
    return RedirectResponse(url=f"/company/processSoftware/testProcess/{module_id}", status_code=302)

# COMPLIANCE TRAINING

@api_router.get("/company/add_module/compliance/{role_id}", status_code=200)
def addCompliance(response: Response, role_id:str, request: Request,  manager: Manager = Depends(get_current_manager)) -> dict:
    response = EMPLOYER_TEMPLATES.TemplateResponse(
        "addCompliance.html",
        {
            "request": request,
            "name": manager.first_name,
            "role_id": role_id,
            "data": [],
            "questions": []
        }
    )
    return response


@api_router.post("/company/add_module/compliance/{role_id}", status_code=200)
def addComplianceSubmit(response: Response, role_id:str, request: Request,  manager: Manager = Depends(get_current_manager), textInput: str = Form(...), moduleName: str = Form(...)) -> dict:
    # textInput = request.form['textInput']
    # moduleName = request.form['moduleName']
    data = {'textInput': textInput, 'moduleName': moduleName}
    questions = generate_compliance_questions(textInput)
    questions = format_questions(questions)
    # return render_template('addCompliance.html', questions=questions, data=data)
    response = EMPLOYER_TEMPLATES.TemplateResponse(
        "addCompliance.html",
        {
            "request": request,
            "role_id": role_id,
            "name": manager.first_name,
            "data": data,
            "questions": questions
        }
    )
    return response


@api_router.get("/company/test_module/compliance/{module_id}/{role_id}", status_code=200)
def testCompliance(response: Response, role_id:str, request: Request, module_id: str,  manager: Manager = Depends(get_current_manager)) -> dict:
    team_id = manager.company_id
    chat = get_training_compliance(module_id, team_id)
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""SELECT module_title, module_text FROM module WHERE module_id = %s""", (module_id,))
        info = cur.fetchone()
        name = info['module_title']
        text = info['module_text']
        # get training id
        cur.execute("""SELECT COUNT(*) as count FROM training WHERE module_id = %s AND training_status = 'completed' and team_id = %s""", (module_id, team_id))
        completed = cur.fetchone()['count']
        cur.execute("""SELECT COUNT(*) as count FROM training WHERE module_id = %s AND team_id = %s""", (module_id, team_id))
        total = cur.fetchone()['count']
        if completed < total:
            cur.execute("""SELECT training_id FROM training WHERE module_id = %s AND training_status = 'pending' and team_id = %s ORDER BY id ASC LIMIT 1""", (module_id, team_id))
            training_id = cur.fetchone()['training_id']
        else:
            cur.execute("""SELECT training_id FROM training WHERE module_id = %s and team_id = %s ORDER BY id ASC LIMIT 1""", (module_id, team_id))
            training_id = cur.fetchone()['training_id']

    response = EMPLOYER_TEMPLATES.TemplateResponse(
        "testCompliance.html",
        {
            "request": request,
            "role_id": role_id,
            "name": manager.first_name,
            "chat": chat,
            "text": text,
            "title": name,
            "completed": completed,
            "total": total,
            "module_id": module_id,
            "training_id": training_id,
        }
    )
    return response


@api_router.post("/company/submit_compliance/{module_id}/{role_id}", status_code=200)
def submitCompliance(response: Response, role_id:str, request: Request, module_id: str, training_id: str = Form(...), chat: str = Form(...), manager: Manager = Depends(get_current_manager)) -> dict:
    # training_id = request.form['training_id']
    # chat = request.form['chat']
    company_id = manager.company_id
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""SELECT module_text FROM module WHERE module_id = %s""", (module_id,))
        context = cur.fetchone()['module_text']
        cur.execute("""SELECT query_id FROM training WHERE training_id = %s AND team_id = %s""", (training_id, company_id))
        question = cur.fetchone()['query_id']
    score = check_response(context, question, chat)
    if 'Yes' in score:
        update_training_status(training_id, chat, 'completed', score)
    else:
        update_training_status(training_id, chat, 'pending', score)
    response = RedirectResponse(url=f"/company/test_module/compliance/{module_id}/{role_id}", status_code=303)
    return response


@api_router.post("/company/test_module/reset/compliance/{training_id}/{role_id}", status_code=200)
def resetCompliance(response: Response, role_id:str, request: Request, training_id: str, manager: Manager = Depends(get_current_manager)) -> dict:
    '''Update training set status to pending '''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""SELECT team_id, module_id FROM training WHERE training_id = %s""", (training_id,))
        team_id, module_id = cur.fetchone()
        cur.execute("""UPDATE training SET response=NULL, training_status=%s
                    WHERE team_id=%s AND module_id = %s""", ('pending', team_id, module_id))
        conn.commit()
    # return redirect(url_for('testCompliance', module_id=module_id))
    response = RedirectResponse(url=f"/company/test_module/compliance/{module_id}/{role_id}", status_code=303)
    return response


@api_router.post("/company/save_module/compliance/{role_id}", status_code=200)
async def saveCompliance(response: Response, role_id:str, request: Request,  manager: Manager = Depends(get_current_manager), moduleName: str = Form(...), textInput: str = Form(...)) -> dict:
    company_id = manager.company_id
    # moduleName = request.form['moduleName']
    # text = request.form['textInput']
    text = textInput
    description = generate_description(text)
    questions = []
    form_data = await request.form()
    form_data = jsonable_encoder(form_data)
    for key in form_data:
        if key.startswith('question'):
            questions.append(form_data[key])
    module_id = add_module(company_id, moduleName, description, 3, text)
    save_queries(module_id, questions)
    return RedirectResponse(url=f"/company/add_modules/{role_id}", status_code=303)


# SIMULATOR TRAINING

@api_router.post("/company/add_module/simulator/{role_id}/{tool_id}", status_code=200)
def addSimulatorSubmit(response: Response, request: Request, role_id:str, tool_id:str, manager: Manager = Depends(get_current_manager), moduleName: str = Form(...), num_chats: int = Form(...), customer: str = Form(...), situation: str = Form(...), problem: str = Form(...), respond: str = Form(...)) -> dict:
    company_id = manager.company_id
    if tool_id not in ['1', '2']:
        # error
        return RedirectResponse(url=f"/company/add_modules/{role_id}?alert='Error'", status_code=302)
    desc = generate_description(customer + situation + problem + respond)
    module_id = add_module_simulator(company_id, moduleName, desc, tool_id, num_chats, customer, situation, problem, respond)
    # generate first chat
    first_chat = generate_simulator(num_chats, customer, situation, problem, respond)
    # get everything after colon if there is a colon
    if ":" in first_chat:
        first_chat = first_chat.split(':')[-1]
    q_list = []
    q_list.append(first_chat)
    # add num_chats - 1 empty chats
    for i in range(num_chats - 1):
        q_list.append(None)
    save_queries(module_id, q_list)
    return RedirectResponse(url=f"/company/add_modules/{role_id}", status_code=302)
    # return RedirectResponse(url=f"/company/test_module/simulator/{module_id}/{role_id}", status_code=302)


@api_router.get("/company/add_module/simulator/{role_id}/{tool_id}", status_code=200)
def addSimulator(response: Response, request: Request, role_id:str, tool_id:str,  manager: Manager = Depends(get_current_manager)) -> dict:
    response = EMPLOYER_TEMPLATES.TemplateResponse(
        "addSimulator.html",
        {
            "request": request,
            "name": manager.first_name,
            "role_id": role_id,
            "tool_id": tool_id,
            "chat": [],
            "data": []
        }
    )
    return response


@api_router.get("/company/test_module/simulator/{module_id}/{role_id}", status_code=200)
def testSimulator(response: Response, request: Request, role_id:str, module_id: str,  manager: Manager = Depends(get_current_manager)) -> dict:
    # check that manager has permission to view the module (either access is public or manager is the creator)
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""SELECT access, company_id FROM module WHERE module_id = %s""", (module_id,))
        access, company_id = cur.fetchone()
        if access == 'private' and company_id != manager.company_id:
            # error
            return RedirectResponse(url=f"/company/add_modules/{role_id}?alert='Error'", status_code=302)
    
    team_id = manager.company_id
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""SELECT module_title, customer, situation, problem, respond FROM module WHERE module_id = %s""", (module_id,))
        module_info = cur.fetchone()
        name = module_info['module_title']
        text = 'Customer: ' + module_info['customer'] + 'Situation: ' + module_info['situation'] + 'Problem: ' + module_info['problem'] + 'Respond: ' + module_info['respond']
        chat = get_training_simulator(module_id, team_id)

        # get training id
        cur.execute("""SELECT COUNT(*) as count FROM training WHERE module_id = %s AND training_status = 'completed' and team_id = %s""", (module_id, team_id))
        completed = cur.fetchone()['count']
        cur.execute("""SELECT COUNT(*) as count FROM training WHERE module_id = %s AND team_id = %s""", (module_id, team_id))
        total = cur.fetchone()['count']
        print('values', completed, total)
        if completed < total:
            cur.execute("""SELECT training_id FROM training WHERE module_id = %s AND training_status = 'pending' and team_id = %s ORDER BY id ASC LIMIT 1""", (module_id, team_id))
            training_id = cur.fetchone()['training_id']
        else:
            cur.execute("""SELECT training_id FROM training WHERE module_id = %s and team_id = %s ORDER BY id ASC LIMIT 1""", (module_id, team_id))
            training_id = cur.fetchone()['training_id']
    # return render_template('testSimulator.html', chat=chat, title=name, completed=completed, total=total, module_id=module_id, training_id=training_id, customer=module_info['customer'], situation=module_info['situation'], problem=module_info['problem'], respond=module_info['respond'])
    response = EMPLOYER_TEMPLATES.TemplateResponse(
        "testSimulator.html",
        {
            "request": request,
            "name": manager.first_name,
            "chat": chat,
            "text": text,
            "role_id": role_id,
            "title": name,
            "completed": completed,
            "total": total,
            "module_id": module_id,
            "training_id": training_id,
            "customer": module_info['customer'],
            "situation": module_info['situation'],
            "problem": module_info['problem'],
            "respond": module_info['respond'],
        }
    )
    return response


@api_router.post("/company/submit_simulator/{module_id}/{role_id}", status_code=200)
def submitSimulator(response: Response, request: Request, role_id:str, module_id: str, training_id: str = Form(...), chat: str = Form(...), manager: Manager = Depends(get_current_manager)) -> dict:
    # training_id = request.form['training_id']
    # chat = request.form['chat']
    company_id = manager.company_id
    time.sleep(1)
    update_training_status(training_id, chat, 'completed')
    response = RedirectResponse(url=f"/company/test_module/simulator/{module_id}/{role_id}", status_code=302)
    return response


@api_router.post("/company/test_module/reset/simulator/{training_id}/{role_id}", status_code=200)
def resetSimulator(response: Response, request: Request, role_id:str, training_id: str, manager: Manager = Depends(get_current_manager)) -> dict:
    '''Update training set status to pending '''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""SELECT team_id, module_id FROM training WHERE training_id = %s""", (training_id,))
        team_id, module_id = cur.fetchone()
        cur.execute("""UPDATE training SET response=NULL, query_id=NULL, training_status=%s
                    WHERE team_id=%s AND module_id = %s and id > 0""", ('pending', team_id, module_id))
        cur.execute("""UPDATE training SET response=NULL, training_status=%s
                    WHERE team_id=%s AND module_id = %s and id = 0""", ('pending', team_id, module_id))
        conn.commit()
    response = RedirectResponse(url=f"/company/test_module/simulator/{module_id}/{role_id}", status_code=302)
    return response


# EMPLOYEE TRAINING

# navigate to next training in the list
@api_router.get("/member/next_training/{team_id}/{tool_id}", status_code=200)
def nextTraining(response: Response, request: Request, team_id:str, tool_id: str, user: User = Depends(get_current_employee)) -> dict:
    ''' Get next incomplete training module with the same tool_id '''
    if user == None or not user:
        return RedirectResponse(url="/logout", status_code=302)
    
    with get_db_connection() as conn:
        # get role_id
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # cur.execute("""SELECT role_id FROM team WHERE team_id = %s""", (team_id,))
        # role_id = cur.fetchone()['role_id']
        cur.execute("""SELECT training.module_id FROM training, module 
                    WHERE training.module_id = module.module_id AND training_status = 'pending' AND module.tool_id = %s AND training.team_id = %s
                    ORDER BY training.id ASC LIMIT 1""", (tool_id, team_id))
        module_id = cur.fetchone()
        if module_id is None:
            return RedirectResponse(url=f"/member/onboard/{team_id}", status_code=302)
        else:
            module_id = module_id['module_id']
    if tool_id == '1' or tool_id == '2':
        response = RedirectResponse(url=f"/member/training/simulator/{module_id}/{team_id}", status_code=302)
    else:
        response = RedirectResponse(url=f"/member/training/compliance/{module_id}/{team_id}", status_code=302)
    return response

# SIMULATOR
@api_router.get("/member/training/simulator/{module_id}/{team_id}", status_code=200)
def trainingSimulator(response: Response, request: Request, module_id:str, team_id: str, user: User = Depends(get_current_employee)) -> dict:
    ''' Get the training module for the employee ''' 
    if user == None or not user:
        return RedirectResponse(url="/logout", status_code=302)

    # role_name = get_training_permission(user.uid, team_id)
    # with get_db_connection() as conn:
    #     cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    #     # check that training_id is valid and tool_id for this module is either '1' or '2'
   
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""SELECT module_title, customer, situation, problem, respond FROM module WHERE module_id = %s""", (module_id,))
        module_info = cur.fetchone()
        name = module_info['module_title']
        text = 'Customer: ' + module_info['customer'] + 'Situation: ' + module_info['situation'] + 'Problem: ' + module_info['problem'] + 'Respond: ' + module_info['respond']
        chat = get_training_simulator(module_id, team_id)

        # get training id
        cur.execute("""SELECT COUNT(*) as count FROM training WHERE module_id = %s AND training_status = 'completed' and team_id = %s""", (module_id, team_id))
        completed = cur.fetchone()['count']
        cur.execute("""SELECT COUNT(*) as count FROM training WHERE module_id = %s AND team_id = %s""", (module_id, team_id))
        total = cur.fetchone()['count']
        print('values', completed, total)
        if completed < total:
            cur.execute("""SELECT training_id FROM training WHERE module_id = %s AND training_status = 'pending' and team_id = %s ORDER BY id ASC LIMIT 1""", (module_id, team_id))
            training_id = cur.fetchone()['training_id']
        else:
            cur.execute("""SELECT training_id FROM training WHERE module_id = %s and team_id = %s ORDER BY id ASC LIMIT 1""", (module_id, team_id))
            training_id = cur.fetchone()['training_id']
    # return render_template('testSimulator.html', chat=chat, title=name, completed=completed, total=total, module_id=module_id, training_id=training_id, customer=module_info['customer'], situation=module_info['situation'], problem=module_info['problem'], respond=module_info['respond'])
    response = EMPLOYEE_TEMPLATES.TemplateResponse(
        "trainSimulator.html",
        {
            "request": request,
            "name": user.first_name,
            "chat": chat,
            "text": text,
            "title": name,
            "completed": completed,
            "total": total,
            "team_id": team_id,
            "module_id": module_id,
            "training_id": training_id,
            "customer": module_info['customer'],
            "situation": module_info['situation'],
            "problem": module_info['problem'],
            "respond": module_info['respond'],
        }
    )
    return response

@api_router.post("/member/submit_simulator/{module_id}/{team_id}", status_code=200)
def trainSimulator(response: Response, request: Request, team_id:str, module_id: str, training_id: str = Form(...), chat: str = Form(...), user: User = Depends(get_current_employee)) -> dict:
    update_training_status(training_id, chat, 'completed')
    response = RedirectResponse(url=f"/member/training/simulator/{module_id}/{team_id}", status_code=302)
    return response


# COMPLIANCE
@api_router.get("/member/training/compliance/{module_id}/{team_id}", status_code=200)
def trainingCompliance(response: Response, request: Request, module_id:str, team_id: str, user: User = Depends(get_current_employee)) -> dict:
    chat = get_training_compliance(module_id, team_id)
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""SELECT module_title, module_text FROM module WHERE module_id = %s""", (module_id,))
        info = cur.fetchone()
        name = info['module_title']
        text = info['module_text']
        # get training id
        cur.execute("""SELECT COUNT(*) as count FROM training WHERE module_id = %s AND training_status = 'completed' and team_id = %s""", (module_id, team_id))
        completed = cur.fetchone()['count']
        cur.execute("""SELECT COUNT(*) as count FROM training WHERE module_id = %s AND team_id = %s""", (module_id, team_id))
        total = cur.fetchone()['count']
        if completed < total:
            cur.execute("""SELECT training_id FROM training WHERE module_id = %s AND training_status = 'pending' and team_id = %s ORDER BY id ASC LIMIT 1""", (module_id, team_id))
            training_id = cur.fetchone()['training_id']
        else:
            cur.execute("""SELECT training_id FROM training WHERE module_id = %s and team_id = %s ORDER BY id ASC LIMIT 1""", (module_id, team_id))
            training_id = cur.fetchone()['training_id']

    response = EMPLOYEE_TEMPLATES.TemplateResponse(
        "trainCompliance.html",
        {
            "request": request,
            "name": user.first_name,
            "chat": chat,
            "text": text,
            "title": name,
            "team_id": team_id,
            "completed": completed,
            "total": total,
            "module_id": module_id,
            "training_id": training_id,
        }
    )
    return response

@api_router.post("/member/submit_compliance/{module_id}/{team_id}", status_code=200)
def trainCompliance(response: Response, request: Request, team_id:str, module_id: str, training_id: str = Form(...), chat: str = Form(...), user: User = Depends(get_current_employee)) -> dict:
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""SELECT module_text FROM module WHERE module_id = %s""", (module_id,))
        context = cur.fetchone()['module_text']
        cur.execute("""SELECT query_id FROM training WHERE training_id = %s AND team_id = %s""", (training_id, team_id))
        question = cur.fetchone()['query_id']
    score = check_response(context, question, chat)
    if 'Yes' in score:
        update_training_status(training_id, chat, 'completed', score)
    else:
        update_training_status(training_id, chat, 'pending', score)
    
    
    progress = get_training_progress(team_id)
    if progress == 1:
        # email comp and emp
        email = get_employee_email(team_id)
        training_completion_comp(email)
        training_completion_emp(email)
    

    response = RedirectResponse(url=f"/member/training/compliance/{module_id}/{team_id}", status_code=303)
    return response


# SOFTWARE


# MAIL

# MAIL CONFIG
conf = ConnectionConfig(
    MAIL_USERNAME = "info@owlo.co",
    MAIL_PASSWORD = rds_config.mail_password,
    MAIL_FROM = "info@owlo.co",
    MAIL_PORT = 587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    TEMPLATE_FOLDER="./templates/employer"
)
class EmailSchema(BaseModel):
    email: List[EmailStr]


@api_router.get("/visualize_email", status_code=200)
async def visualize_email(request: Request):
    # test email in browser
    response = EMPLOYER_TEMPLATES.TemplateResponse(
        "email.html",
        {
            "request": request,
            "title": "Welcome to Owlo",
            "main_message": "Thanks for joining Owlo",
            "sub_message": "We're excited to have you on board.",
            "link_desc": "Click here to get started",
            "link": "https://www.owlo.co",
            "link_cta": "Get Started",
            "unsubscribe_url" : "https://www.owlo.co",
        }
    )
    return response


def get_email_info(email):
    '''Get user info from employee_user or manager_user'''
    uid = None
    first_name = None
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""SELECT * FROM employee_user WHERE email = %s""", (email,))
        info = cur.fetchone()
        if info:
            uid = info['user_id']
            first_name = info['first_name']
        else:
            # get from company AKA manager_user
            cur.execute("""SELECT * FROM manager_user WHERE email = %s""", (email,))
            info = cur.fetchone()
            if info:
                uid = info['user_id']
                first_name = info['first_name']
            
    return uid, first_name

''' create account welcome email for new employees'''
def create_account_emp(email):
    user_id, first_name = get_email_info(email)
    template_data = {
        "title": "Welcome to Owlo, " + first_name + ",",
        "main_message": "Thanks for joining Owlo",
        "sub_message": "We're excited to have you on board.",
        "link_desc": "Click here to start onboarding",
        "link": "https://www.owlo.co",
        "link_cta": "Get Started",
        "user_id": user_id,
        "email": email
    }
    subject = "Welcome to Owlo"
    if user_id and first_name:
        send_email(email, template_data, subject)


''' create account welcome email for company accounts'''
def create_account_comp(email):
    user_id, first_name = get_email_info(email)
    template_data = {
        "title": "Welcome to Owlo",
        "main_message": "Thanks for joining Owlo",
        "sub_message": "We're excited to have you on board.",
        "link_desc": "Click here to start onboarding your new team members",
        "link": "https://www.owlo.co/company",
        "link_cta": "Get Started",
        "user_id": user_id,
        "email": email
    }
    subject = "Welcome to Owlo"
    if user_id and first_name:
        send_email(email, template_data, subject)


'''training invite email'''
def training_invite_email(email):
    user_id, first_name = get_email_info(email)
    template_data = {
        "title": "Onboarding Invite",
        "main_message": "Hi " + first_name + "! ",
        "sub_message": "A company has invited you to onboard for a new role.",
        "link_desc": "Log in or Create an Account below to start onboarding",
        "link": f"https://www.owlo.co/",
        "link_cta": "Begin",
        "user_id": user_id,
        "email": email
    }
    subject = "Let's get started"
    if user_id and first_name:
        send_email(email, template_data, subject)


'''training reminder email'''
def training_reminder_email(email):
    user_id, first_name = get_email_info(email)
    template_data = {
        "title": "Onboarding Reminder",
        "main_message": "Hi " + first_name + "! ",
        "sub_message": "You have pending onboarding for one or more roles",
        "link_desc": "Log in or Create an Account below to start onboarding",
        "link": f"https://www.owlo.co/",
        "link_cta": "Begin",
        "user_id": user_id,
        "email": email
    }
    subject = "Your onboarding is waiting!"
    if user_id and first_name:
        send_email(email, template_data, subject)


'''training completion email for employee'''
def training_completion_emp(email):
    user_id, first_name = get_email_info(email)
    template_data = {
        "title": "Onboarding Complete",
        "main_message": "Hi " + first_name + "! ",
        "sub_message": "You have completed onboarding for a role",
        "link_desc": "We have notified the hiring manager that you are ready to begin. In the meantime, you can log in to your account to view your training history.",
        "link": f"https://www.owlo.co/",
        "link_cta": "Owlo",
        "user_id": user_id,
        "email": email
    }
    subject = "Your onboarding is complete!"
    if user_id and first_name:
        send_email(email, template_data, subject)


'''training completion email for employer'''
def training_completion_comp(email):
    user_id, first_name = get_email_info(email)
    template_data = {
        "title": "Onboarding Complete",
        "main_message": "Hi " + user_name + "! ",
        "sub_message": "A team member has completed onboarding. ",
        "link_desc": "You can log in to your account to view their onboarding history and analysis.",
        "link": f"https://www.owlo.co/company",
        "link_cta": "Analysis",
        "user_id": user_id,
        "email": email
    }
    subject = " A member has completed onboarding!"
    if user_id and first_name:
        send_email(email, template_data, subject)


'''Unsubscribe email'''
def send_unsubscribe_email(email):
    template_data = {
        "title": "Unsubscribe",
        "main_message": "Sorry to see you go!",
        "sub_message": "You have been unsubscribed from Owlo emails. ",
        "link_desc": "You will no longer receive emails from us. You can further change settings in your account.",
        "link": f"https://www.owlo.co/account",
        "link_cta": "Account",
        "email": email,
    }
    subject = "Unsubscribed from Owlo"
    if email:
        send_email(email, template_data, subject)


'''Unsubscribe email'''
@app.get("/unsubscribe/{user_id}/{email}", status_code=200)
def unsubscribe_email(user_id:str, email:str):
    ''' Add user_id to unsubscribe table'''
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO unsubscribe (user_id, email, status) VALUES (%s, %s, %s)", (user_id, email, 'unsubscribed')
        )
        conn.commit()
    # redirect to index
    send_unsubscribe_email(email)
    return RedirectResponse(url='https://www.owlo.co?alert="Unsubscribed!"', status_code=302)


''' Check if email is unsubscribed'''
def check_unsubscribe(email):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM unsubscribe WHERE email = %s", (email,)
            )
            unsubscribe = cursor.fetchone()
            if unsubscribe:
                return True
            else:
                return False


'''SEND EMAIL'''
async def send_email(email:str, template_data: dict, subject: str):
    if not check_unsubscribe(email):
        message = MessageSchema(
            subject=subject,
            recipients=[email],
            template_body=template_data,
            subtype=MessageType.html
        )
        fm = FastMail(conf)
        await fm.send_message(message, template_name="email.html") 
        return JSONResponse(status_code=200, content={"message": "email has been sent"})


app.include_router(api_router)