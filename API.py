from fastapi import FastAPI, Header, HTTPException, Depends, status, Response, Request, APIRouter, Form
from pydantic import BaseModel
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.datastructures import URL
from fastapi.encoders import jsonable_encoder

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
from training import *

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
    alert = request.query_params.get('alert')
    print(keyword, filter_status)
    invited = get_training_invited(user.uid,keyword,filter_status)
    return EMPLOYEE_TEMPLATES.TemplateResponse(
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


@api_router.get("/member/onboard/{team_id}", status_code=200)
def start_training(request: Request, response: Response, team_id:str, user: User = Depends(get_current_employee)):
    """
    Root GET
    """
    if user == None or not user:
        return RedirectResponse(url="/logout", status_code=302)

    role_name = get_training_permission(user.uid, team_id)
    modules = get_training_tools(team_id)
    if not role_name:
        return RedirectResponse(url="/member?alert=" + str("You are not permitted to view this role"), status_code=302)

    # modules = [
    # {
    #     "id": 1,
    #     "title": "Customer Simulation",
    #     "icon": "people-outline"
    # },
    # {
    #     "id": 2,
    #     "title": "Co-worker Simulation",
    #     "icon": "chatbubbles-outline"
    # },
    # {
    #     "id": 3,
    #     "title": "Software Simulation",
    #     "icon": "desktop-outline"
    # }
    # ]
    return EMPLOYEE_TEMPLATES.TemplateResponse(
        "train.html",
        {
            "request": request,
            "modules": modules,
            "name": user.first_name,
            "role_name": role_name
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
    keyword = request.query_params.get('keyword')
    if keyword != None:
        keyword = keyword.strip()

    if not manager:
        return RedirectResponse(url="/company/logout", status_code=302)
    elif manager.company_id == None:
        return RedirectResponse(url="/company/add_company", status_code=302)
    roles = get_role_comprehensive(manager.company_id, keyword)
    return EMPLOYER_TEMPLATES.TemplateResponse(
        "roles.html",
        {
            "request": request,
            "roles": roles,
            "keyword": keyword if keyword != None else '',
            "name": manager.first_name
        }
    )


@api_router.get("/company/employee/view/{employee_id}", status_code=200)
def view_employee(response: Response, request: Request, employee_id: str, manager: Manager = Depends(get_current_manager)) -> dict:
    """
    Get all the roles of this company
    """
    if not manager:
        return RedirectResponse(url="/company/logout", status_code=302)
    elif manager.company_id == None:
        return RedirectResponse(url="/company/add_company", status_code=302)
    # employee = get_employee(manager.company_id, employee_id)
    if not check_emp_in_team(manager.company_id, employee_id):
        return RedirectResponse(url="/company/team", status_code=302)
    return EMPLOYER_TEMPLATES.TemplateResponse(
        "employee.html",
        {
            "request": request,
            "employee": 'Hi',
            "name": manager.first_name
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

    modules = get_tools()
    return EMPLOYER_TEMPLATES.TemplateResponse(
        "addRole.html",
        {
            "request": request,
            "modules": modules,
            "name": manager.first_name,
            "alert": request.query_params.get('alert') if request.query_params.get('alert') != None else ''
        }
    )


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
    print(tool)
    if not tool:
        complete = complete_role(manager.company_id, role_id)
        if complete['status'] == 'error':
            return RedirectResponse(url="/company/roles?alert="+str(complete['body']), status_code=302)
        else:
            return RedirectResponse(url="/company/roles?alert=Role Added", status_code=302)

    public_modules = get_public_modules(tool.tool_id)
    modules = []
    return EMPLOYER_TEMPLATES.TemplateResponse(
        "addModules.html",
        {
            "request": request,
            "modules": modules,
            "public_modules": public_modules,
            "name": manager.first_name, 
            "tool": tool,
            "role_id": role_id
        }
    )


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

    valid_modules = []
    for module in form_data:
        if module == 'role_id':
            continue
        permission = verify_module_access(manager.company_id, module, tool_id)
        if permission:
            valid_modules.append(module)
            
    if len(valid_modules) == 0:    
        return RedirectResponse(url='/company/add_modules/'+str(role_id) + "?alert=" + str('Please add atleast one module'), status_code=302)
    
    # add modules to role
    for module in valid_modules:
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
    return EMPLOYER_TEMPLATES.TemplateResponse(
        "editRole.html",
        {
            "request": request,
            "modules": modules,
            "sections": modules,
            "name": manager.first_name,
            "role": role
        }
    )

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
    return EMPLOYER_TEMPLATES.TemplateResponse(
        "viewRole.html",
        {
            "request": request,
            "name": manager.first_name,
            "role": role
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