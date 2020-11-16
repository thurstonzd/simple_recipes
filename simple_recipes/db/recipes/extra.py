import json

from psycopg2 import sql
from pint import UnitRegistry

from simple_recipes.db import get_connection, get_cursor

def update_recipe_instructions(recipe_id, new_instructions):
    '''updates the specified recipe's instructions
    to match what's provided
    Note: This function overwrites any instructions currently
    specified for a recipe.
    new_instructions must be list, either of instruction strings
    or dictionary consisting of step_number and instruction keys
    
    example call:
    update_recipe_instructions(1, [
        'Combine ingredients', 
        'Bake for 30 minutes']
    OR
    update_recipe_instructions(1, [
        {'step_number': 1, 'instruction': 'Combine ingredients'}, 
        {'step_number': 2, 'instruction': 'Bake for 30 minutes'}
        ]
    '''
    sql = "CALL set_recipe_instructions(%s, %s);"
    
    for i, inst in enumerate(new_instructions):
        if type(inst) == str:
            new_instructions[i] = {
                'step_number' : i+1, 
                'instruction' : inst}
            
    with get_connection() as cn:
        with cn.cursor() as cur:
            cur.execute(sql, 
                (recipe_id, json.dumps(new_instructions)))
                
def update_recipe_tags(recipe_id, new_tags):
    '''updates the specified recipe's tags
    to match what's provided
    Note: This function overwrites any tags currently
    specified for a recipe.
    new_tags must be list, either of tag_id ints
    or dictionary consisting of tag_id (tag_name not required)
    
    example call:
    update_recipe_tags(1, [1, 2]
    OR
    update_recipe_tags(1, [{'recipe_id': 1}, {'recipe_id': 2}]
    '''
    sql = "CALL set_recipe_tags(%s, %s);"
    
    for i, inst in enumerate(new_tags):
        if type(inst) == int:
            new_tags[i] = {'tag_id' : new_tags[i]}
            
    with get_connection() as cn:
        with cn.cursor() as cur:
            cur.execute(sql, 
                (recipe_id, json.dumps(new_tags)))
                
def get_measurements(**criteria):
    ''' returns 1 or more measurements based on provided criteria.
    
    If no criteria are provided, returns are measurements
    
    Valid keys in **criteria:
     - measurement_id (int)
     - measurement_name (string)
     - measurement_system (string) in ('US', 'SI')
     - measurement_category (string) in ('V', 'M')
     - only_include_convertibles (bool)
     
    if measurement_id or measurement_name is specified, other criteria
    aren't considered. Otherwise, a list of measurements matching criteria
    is returned.

    This function always returns a list for the sake of consistency.

    example usage:
    get_measurements(measurement_id=1) -> 
    [{'measurement_plural' : 'ounces', ...}]
        
    get_measurements(measurement_system='US', measurement_category='V') =>
    [
        {'measurement_plural' : 'ounces', ...},
        {'measurement_plural' : 'ounces', ...},
        {'measurement_plural' : 'ounces', ...},
        {'measurement_plural' : 'ounces', ...}
    ]
    '''
    statement = "SELECT measurements_json();"
    
    with get_connection() as cn:
        with get_cursor(cn) as cur:
            cur.execute(statement)
            
            data = cur.fetchone()[0]
            
            if 'measurement_id' in criteria:
                criterion = criteria['measurement_id']
                data = [m for m in data if m['measurement_id'] == criterion]
            elif 'measurement_name' in criteria:
                criterion = criteria['measurement_name']
                data = [m for m in data if criterion in (
                    m['measurement_plural'], 
                    m['measurement_singular'],
                    m['measurement_abbr'])]
            elif 'measurement_system' in criteria or 'measurement_category' in criteria:
                cat = criteria.get('measurement_category')
                sys = criteria.get('measurement_system')
                
                data = [m for m in data if 
                    (m['measurement_category'] == cat or not cat) and
                    (m['measurement_system'] == sys or not sys)]
                    
            if 'only_include_convertibles' in criteria:
                data = [m for m in data if m['include_in_conversions']]
            
            return data
            
def get_measurement_strings(**criteria):
    '''returns a list of strings, where each string is a recognized measurement.
    '''
    
    measurements = get_measurements(**criteria)
    strings = []
    
    strings.extend([m['measurement_abbr'] 
        for m in measurements if m['measurement_abbr']])
    strings.extend([m['measurement_singular']
        for m in measurements])
    strings.extend([m['measurement_plural']
        for m in measurements])
    
    return strings
    
def update_recipe_ingredients(recipe_id, new_ingredients):
    '''updates the specified recipe's ingredients
    to match what's provided
    Note: This function overwrites any ingredients currently
    specified for a recipe.
    new_ingredients must be list of dictionaries,
    where each dict contains the following keys
     - quantity : int, float or Decimal (required)
     - ingredient_name : string (required)
     - measurement_name : string (optional)
     
    if measurement_name is specified but invalid,
    it's value is added back to the ingredient_name
    
    example call:
    update_recipe_ingredients(1, [
        {'quantity': 0.5, 'measurement_name': 'cups', 'ingredient_name': 'sugar'},
        {'quantity': 2, 'measurement_name': 'tbsp', 'ingredient_name': 'baking soda'},
        {'quantity': 1, 'ingredient_name': 'banana'}
        ])
    '''
    sql = "CALL set_recipe_ingredients(%s, %s)"
    
    with get_connection() as cn:
        with cn.cursor() as cur:
            cur.execute(sql, 
                (recipe_id, json.dumps(new_ingredients)))