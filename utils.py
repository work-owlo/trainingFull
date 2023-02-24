import sqlite3
import psycopg2.extras
import random 
import logging
import rds_config
import sys
import psycopg2
import os

def error(msg):
    '''Print an error message and exit.'''
    print(msg)
    return False


# def get_db_connection():
#     '''Return a connection to the database.'''''
#     conn = sqlite3.connect('db/database.db')
#     conn.row_factory = sqlite3.Row
#     return conn

# connect to heroku postgress
# db_info = os.environ.get('DATABASE_URL')
# db_info example: postgres://username:password@host:port/database
def get_db_connection():
    '''Return a connection to the database.'''
    db_info = os.environ.get('DATABASE_URL')
    conn = psycopg2.connect(db_info)
    return conn
    
def get_db_connection():
    '''Get a connection to the RDS database.'''
    rds_host  = rds_config.db_host
    rds_username = rds_config.db_username
    rds_user_pwd = rds_config.db_password
    rds_db_name = rds_config.db_name

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    try:
        conn_string = "host=%s user=%s password=%s dbname=%s" % \
                        (rds_host, rds_username, rds_user_pwd, rds_db_name)
        conn = psycopg2.connect(conn_string)
        logger.info("SUCCESS: Connection to RDS Postgres instance succeeded")
        return conn
    except:
        logger.error("ERROR: Could not connect to Postgres instance.")
        sys.exit()
        return_error()

# print(get_db_connection())

def generate_uid():
    '''Generate a random 15 character string.'''
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', k=25))

def generate_eid():
    '''Generate a random 15 character string.'''
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', k=5))


def return_success(message="success"):
    return {"status": "success", "body": message, "code": 200}


def return_error(message="error"):
    return {"status": "error", "body": message, "code": 400}
