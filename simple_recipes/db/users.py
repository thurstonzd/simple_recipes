from os import urandom

from psycopg2 import sql
import scrypt

from simple_recipes.db import get_connection, get_cursor

def get_user_by_username(user_name):

    statement = sql.SQL(    "SELECT user_id, user_name, password_hash, password_salt "
                            "FROM users "
                            "WHERE LOWER(user_name) = LOWER(%s)")
    
    with get_connection() as cn:
        with get_cursor(cn) as cur:
            cur.execute(statement, (user_name,))
            record = cur.fetchone()
            return dict(record) if record else None
                
def get_user_by_id(user_id):
    statement = sql.SQL(    "SELECT user_id, user_name, password_hash, password_salt "
                            "FROM users "
                            "WHERE user_id = %s")
    
    with get_connection() as cn:
        with get_cursor(cn) as cur:
            cur.execute(statement, (user_id,))
            record = cur.fetchone()
            return dict(record)

def is_user_password_valid(user_name, password):
    user_dict = get_user_by_username(user_name)
    if not user_dict: return False
    salt = bytes(user_dict['password_salt'])
    h1 = bytes(user_dict['password_hash'])
    h2 = scrypt.hash(password, salt)

    return h1 == h2

def add_user(user_name, password_hash, salt):
    statement = sql.SQL(    "INSERT INTO users "
                            "(user_name, password_hash, password_salt) "
                            "VALUES (%s, %s, %s) "
                            "RETURNING user_id")
    
    with get_connection() as cn:
        with get_cursor(cn) as cur:
            cur.execute(statement, (user_name, password_hash, salt))
            return cur.fetchone()['user_id']

def update_user_name(old_user_name, new_user_name):
    statement = sql.SQL(    "UPDATE users "
                            "SET user_name = %(new)s "
                            "WHERE user_name = %(old)s;")

    with get_connection() as cn:
        with get_cursor(cn) as cur:
            cur.execute(statement, {
                'old' : old_user_name, 
                'new': new_user_name
                })

def update_user_password(old_user_name, password_hash, salt=None):
    if not salt: salt = urandom(16)

    statement = sql.SQL(    "UPDATE users "
                            "SET "
                                "password_hash=%(password)s, "
                                "password_salt=%(salt)s "
                            "WHERE user_name = %(old)s")

    with get_connection() as cn:
        with get_cursor(cn) as cur:
            cur.execute(statement, {
                'old': old_user_name,
                'password': password_hash,
                'salt': salt
            })