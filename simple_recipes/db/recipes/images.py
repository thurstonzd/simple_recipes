from psycopg2 import sql, connect
import psycopg2.extras

from simple_recipes.db import get_connection, get_cursor

def add_recipe_images(recipe_id, images):
    ''' adds the list of images to the specified recipe.
    
    images is a list of dictionaries, where each dictionary 
    consists of the following keys:
    
     - image_file_name
     - file_type (MIME type)
     - image_desc (may be None)
     - image_bytes
    '''
    columns = ['recipe_id', 'image_file_name', 'file_type', 
        'image_desc', 'image_bytes']
    
    statement = sql.SQL(    "INSERT INTO recipe_images "
                            "({column_names})" 
                            "VALUES "
                            "({column_values})"
    ).format(
        column_names=sql.SQL(', ').join(sql.Identifier(s) for s in columns),
        column_values = sql.SQL(', ').join(sql.Placeholder(s) for s in columns))
    
    with get_connection() as cn:
        with get_cursor(cn) as cur:
            for img_dict in images:
                img_dict['recipe_id'] = recipe_id
                cur.execute(statement, img_dict)

def delete_recipe_images(image_ids):
    '''deletes the Image IDs specified in the provided list.
    
    example usage:
    delete_recipe_images([2, 3])
    '''
    
    statement = sql.SQL(    "DELETE FROM recipe_images "
                            "WHERE image_id IN ({image_ids})")
    image_id_literals = sql.SQL(", ").join(
        sql.Literal(i) for i in image_ids)
    
    with get_connection() as cn:
        with get_cursor(cn) as cur:
            cur.execute(statement.format(image_ids=image_id_literals))
                
def get_recipe_image(image_id):
    ''' returns an image and its MIME type.
    {'file_type': 'foo', 'image_bytes': b''}
    '''
    statement = sql.SQL(    "SELECT file_type, image_bytes "
                            "FROM recipe_images "
                            "WHERE image_id = %s")
                            
    with get_connection() as cn:
        with cn.cursor() as cur:
            cur.execute(statement, (image_id,))
            
            record = cur.fetchone()
            
            return {
                'file_type' : record[0],
                'image_bytes' : bytes(record[1])
            }