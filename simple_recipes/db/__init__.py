from psycopg2 import sql, connect
import psycopg2.extras
import os

from simple_recipes import app

def get_connection():
    DATABASE_URL = None
    if app.config['ENV'] == 'development':
        DATABASE_URL = app.config['DATABASE_URL']
    elif 'DATABASE_URL' in os.environ:
        DATABASE_URL = os.environ['DATABASE_URL']
    else:
        DATABASE_URL = 'host=localhost port=5433 dbname=recipes user=postgres password=admin'
    return connect(DATABASE_URL)
        
def get_cursor(cn):
    return cn.cursor(cursor_factory = psycopg2.extras.DictCursor)
        
def get_table_names():
    table_names = []
    
    statement = sql.SQL(    "SELECT table_name "
                            "FROM information_schema.tables "
                            "WHERE "
                                "table_schema = 'public' "
                                "AND table_type = 'BASE TABLE'")
    
    with get_connection() as cn:
        with get_cursor(cn) as cur:
            cur.execute(statement)
            
            for record in cur:
                table_names.append(record[0])
                
    return table_names
        
def get_table_counts():
    table_names = get_table_names()
    select_template = sql.SQL(  "SELECT "
                                    "{table_as_literal}, "
                                    "COUNT(*) "
                                "FROM {table_as_identifier}")
                                
    table_statements = [select_template.format(
            table_as_literal = sql.Literal(s),
            table_as_identifier = sql.Identifier(s)) 
            for s in table_names]
        
    statement = sql.SQL(" UNION ALL ").join(table_statements)
        
    with get_connection() as cn:
        with cn.cursor() as cur:
            cur.execute(statement)
            return cur.fetchall()