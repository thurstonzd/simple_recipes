from os import urandom

from psycopg2 import sql
import scrypt

from simple_recipes.db import get_connection, get_cursor

LOCKED = 1
RESET = 2

# how many unsuccessful attempts are allowed before locking the account.
ALLOWED_ATTEMPTS = 3

def check_user_criteria(**user_criteria):
    '''Checks for valid user_criteria
    Either user_id or user_name (just one), and nothing else.
    if criterion is valid, returns the sql.Composable that can be plugged into a query.
    Otherwise, returns a TypeError.
    '''
    if len(user_criteria) != 1: raise TypeError("Only 1 (and exactly 1) criterion allowed")
    field_name = list(user_criteria)[0]
    if field_name not in ['user_id', 'user_name']: 
        raise TypeError(f"'{field_name}'' is invalid criterion name")

    return sql.Composed([
        sql.Identifier(field_name),
        sql.SQL("~*" if field_name == 'user_name' else "="),
        sql.Placeholder(field_name)
    ])

def get_user(**user_criteria):
    '''returns the user specified by the (unique) criteria.
    user_criteria must be either user_id=X or user_name='X'
    raises TypeError for illegal criteria, or no criteria, or both specified.
    '''
    statement = sql.SQL("SELECT * FROM users WHERE {where}")

    where_clause = check_user_criteria(**user_criteria)
    statement = statement.format(where=where_clause)

    with get_connection() as cn:
        with get_cursor(cn) as cur:
            cur.execute(statement, user_criteria)
            record = cur.fetchone()
            return dict(record) if record else None

def change_user_status(new_status=None, **user_criteria):
    '''use this to lock, unlock (reset), or remove a locked/reset status.
    Pass LOCKED or RESET as the first argument to update to that status,
    or just pass the user_criteria to remove the status.
    '''
    
    where_clause = check_user_criteria(**user_criteria)

    # template statement
    statement = sql.SQL(    "UPDATE users "
                            "SET "
                                "user_status={status}, "
                                "unsuccessful_logins={logins} "
                            "WHERE {where}")

    # reset unsuccessful_logins to 0 if the account's being reset.
    # otherwise, keep it.
    if new_status == RESET: 
        logins = sql.Literal(0)
    else: 
        logins = sql.Identifier("unsuccessful_logins")
    
    # format statement
    statement = statement.format(
            status=sql.Literal(new_status),
            where=where_clause,
            logins=logins)

    # execute statement
    with get_connection() as cn:
        with get_cursor(cn) as cur:
            cur.execute(statement, user_criteria)

def lock_user(**user_criteria):
    change_user_status(LOCKED, **user_criteria)

def unlock_user(**user_criteria):
    change_user_status(RESET, **user_criteria)

def register_login_attempt(is_successful, **user_criteria):
    statement = None
    where_clause = check_user_criteria(**user_criteria)

    if is_successful:
        statement = sql.SQL(    "UPDATE users "
                                "SET "
                                    "last_login=CURRENT_TIMESTAMP, "
                                    "unsuccessful_logins=0 "
                                "WHERE {where};").format(where=where_clause)
    else:
        statement = sql.SQL(    "UPDATE users "
                                "SET unsuccessful_logins = unsuccessful_logins + 1 "
                                "WHERE {where};").format(where=where_clause)

    with get_connection() as cn:
        with get_cursor(cn) as cur:
            cur.execute(statement, user_criteria)

def is_user_password_valid(password, **user_criteria):
    user_dict = get_user(**user_criteria)
    if not user_dict: 
        vals = list(user_criteria.items())[0]
        raise PermissionError("{} '{}' not found".format(*vals))

    if user_dict['user_status'] == LOCKED:
        raise PermissionError("This account is locked")
    if user_dict['unsuccessful_logins'] >= ALLOWED_ATTEMPTS:
        lock_user(**criteria)
        raise PermissionError("This account is locked")

    salt = bytes(user_dict['password_salt'])
    h1 = bytes(user_dict['password_hash'])
    h2 = scrypt.hash(password, salt)

    success = (h1 == h2)
    register_login_attempt(success, **user_criteria)
    return success

def add_user(user_name, password_hash, salt):
    statement = sql.SQL(    "INSERT INTO users "
                            "(user_name, password_hash, password_salt) "
                            "VALUES (%s, %s, %s) "
                            "RETURNING user_id")
    
    with get_connection() as cn:
        with get_cursor(cn) as cur:
            cur.execute(statement, (user_name, password_hash, salt))
            return cur.fetchone()['user_id']

def update_user_name(new_user_name, **user_criteria):
    statement = sql.SQL(    "UPDATE users "
                            "SET user_name = %(new)s "
                            "WHERE {where};")

    where_clause = check_user_criteria(**user_criteria)
    data = user_criteria
    data['new'] = new_user_name
    statement = statement.format(where=where_clause)

    with get_connection() as cn:
        with get_cursor(cn) as cur:
            cur.execute(statement, data)

def update_user_password(password_hash, salt=None, **user_criteria):
    if not salt: salt = urandom(64)

    where_clause = check_user_criteria(**user_criteria)
    data = user_criteria
    data['password'] = password_hash
    data['salt'] = salt
    statement = sql.SQL(    "UPDATE users "
                            "SET "
                                "password_hash=%(password)s, "
                                "password_salt=%(salt)s "
                            "WHERE {where}")

    statement = statement.format(where=where_clause)

    with get_connection() as cn:
        with get_cursor(cn) as cur:
            cur.execute(statement, data)