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
        DATABASE_URL = 'host=localhost port=5432 dbname=recipes user=postgres password=admin'
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
        
def get_measurement_units(**criteria):
    statement = "SELECT units_json();"
    with get_connection() as cn:
        with get_cursor(cn) as cur:
            cur.execute(statement)
            data = cur.fetchone()[0]

            '''
            # search data based on provided criteria
            if 'unit_id' in criteria:
                criterion = criteria['unit_id']
                data = [u for u in data if u['unit_id'] == criterion]
            elif 'unit_name' in criteria:
                criterion = criteria['unit_name']
                data = [u for u in data if criterion in (
                    u['unit_plural'],
                    u['unit_singular'],
                    u['unit_abbr'])]
            elif 'unit_system' in criteria or 'unit_category' in criteria:
                cat = criteria.get('unit_category')
                sys = criteria.get('unit_system')
                data = [u for u in data if
                        (u['unit_category'] == cat or not cat) and
                        (u['unit_system'] == sys or not sys)]

            if 'only_include_convertibles' in criteria:
                data = [u for u in data if u['include_in_conversions']]
            '''

            return data
        
def get_unit_strings(**criteria):
    units = get_measurement_units(**criteria)
    strings = []

    # do plurals, then singular, then abbr., to match on longest string first.
    strings.extend([units[k]['unit_plural'] for k in units])
    strings.extend([units[k]['unit_singular'] for k in units])
    strings.extend([units[k]['unit_abbr'] for k in units if units[k]['unit_abbr']])

    return strings

def get_units_concatenated(join_char, **criteria):
    unit_strings = get_unit_strings(**criteria)
    return join_char.join(unit_strings)