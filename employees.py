from utils import * 
import os
from classes import *


def get_training_invited(uid, keyword=None, filter_status=None):
    ''' Get all training programs an employee is invited to '''
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
    if keyword:
        return [t for t in training if keyword in t['description']]
    return training