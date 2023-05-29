from fractions import Fraction
from datetime import timedelta
import json

from psycopg2 import sql

from simple_recipes.db import get_connection, get_cursor
from simple_recipes.db.users import get_user
from simple_recipes.db.recipes.images import *

def get_recipe(recipe_id):
    '''Get a dictionary object based on provided recipe ID
    This function does not return the recipe image;
    a separate function call is required for that.
    Returns None for invalid recipe_id
    '''
    statement = "SELECT recipe_json(%s)"

    with get_connection() as cn:
        with get_cursor(cn) as cur:
            cur.execute(statement, (recipe_id,))
            data = cur.fetchone()[0]

            if data:
                if data['total_time_minutes']:
                    template = ''
                    h, m = divmod(data['total_time_minutes'], 60)
                    data['total_time'] = timedelta(hours=h, minutes=m)

            return data
            
def get_recipes(tsquery):
    '''returns a list of tuples (recipe_id, recipe_name)
    based on provided tsquery
    '''
    recipes = []
    statement = sql.SQL(    "SELECT "
                                "recipe_id, "
                                "recipe_name, "
                                "created_by, "
                                "tags, "
                                "{rank} as rank "
                            "FROM recipe_documents "
                            "WHERE doc @@ TO_TSQUERY(%(q)s) "
                            "ORDER BY {rank} DESC" ).format(
                        rank=sql.SQL("TS_RANK(doc, TO_TSQUERY(%(q)s))"))
                        
    with get_connection() as cn:
        with get_cursor(cn) as cur:
            cur.execute(statement, {'q' : tsquery})
            
            return cur.fetchall()

def add_or_update_recipe(new_data):
    '''updates or adds basic recipe info
    if recipe_id key is not present in new_data dict, it's assumed
    we're adding a new recipe. Otherwise, we use the recipe_id
    to update the given recipe. Only values/keys in the dict are updated.
    
    valid keys in new_data include:
     - recipe_id : int (for updating existing recipes)
     - recipe_name : string (required for adding new recipes)
     - servings : int
     - total_time : TimeDelta object
        OR
     - total_time_minutes : int
     - recipe_desc: string
     - recipe_ingredients: string
     - recipe_instructions: string
    
    examples:
    
    to update an existing recipe's name:
    update_recipe_basic({"recipe_id": 1, "recipe_name": "Yummy cookies"}
    
    to add a new recipe (requires at least recipe_name; servings defaults to 1)
    update_recipe_basic({"recipe_name": "Strawberry cake"})
    
    Thanks to https://stackoverflow.com/a/59855303 for the UPDATE part
    '''
    
    # if necessary, "convert" total_time_minutes to total_time
    if 'total_time_minutes' in new_data:
        m = new_data['total_time_minutes']
        if m: total_time = timedelta(minutes=m)
        else: total_time = m
        new_data['total_time'] = total_time

    # if necessary, get User ID from User Name
    if 'created_by' in new_data:
            user = get_user(user_name=new_data['created_by'])
            if user: new_data['created_by'] = user['user_id']
        
    # keys that will go into UPDATE statement
    valid_keys = ['recipe_id', 'recipe_name', 
        'servings', 'total_time', 'recipe_desc', 'created_by']
    
    # remove invalid keys
    new_data = {k: new_data[k] for k in new_data if k in valid_keys}
    
    if 'recipe_id' in new_data:
        # assume we're editing an existing recipe
        snip = sql.SQL("UPDATE recipes SET {data} WHERE recipe_id = {id}").format(
            data=sql.SQL(', ').join(
                sql.Composed(
                    [sql.Identifier(k), sql.SQL(" = "), sql.Placeholder(k)]) 
                    for k in new_data.keys()), 
            id=sql.Placeholder('recipe_id'))
            
        with get_connection() as cn:
            with cn.cursor() as cur:
                cur.execute(snip, new_data)
    else:
        # assume we're adding a new recipe
        snip = sql.SQL( "INSERT INTO recipes "
                        "({fields}) "
                        "VALUES "
                        "({values}) "
                        "RETURNING recipe_id").format(
            fields=sql.SQL(", ").join(sql.Identifier(k) for k in new_data),
            values=sql.SQL(", ").join(sql.Placeholder(k) for k in new_data))
            
        with get_connection() as cn:
            with cn.cursor() as cur:
                cur.execute(snip, new_data)
                return cur.fetchone()[0]
                
def delete_recipe(recipe_id):
    sql = (    "DELETE FROM recipes "
            "WHERE recipe_id = %s")

    with get_connection() as cn:
        with cn.cursor() as cur:
            cur.execute(sql, (recipe_id,))

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