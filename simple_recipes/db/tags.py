from psycopg2 import sql
from simple_recipes.db import get_connection, get_cursor

def get_tags():
    tags = []
    statement = sql.SQL(    "SELECT "
                                "tags.tag_id, "
                                "tags.tag_name, "
                                "tags.tag_desc, "
                                "users.user_name AS created_by "
                            "FROM tags "
                                "LEFT JOIN users ON "
                                    "tags.created_by = users.user_id "
                            "ORDER BY tag_name")
    
    with get_connection() as cn:
        with get_cursor(cn) as cur:
            cur.execute(statement)
            return [dict(item) for item in cur.fetchall()]
    
def get_tag(tag_id):
    ''' returns tag information as a DictRow
    '''
    statement = sql.SQL(    "SELECT "
                                "tags.tag_id, "
                                "tags.tag_name, "
                                "tags.tag_desc, "
                                "tags.created_at, "
                                "users.user_name AS created_by "
                            "FROM tags "
                                "LEFT JOIN users ON "
                                    "users.user_id = tags.created_by "
                            "WHERE tag_id = %s")
    
    with get_connection() as cn:
        with get_cursor(cn) as cur:
            cur.execute(statement, (tag_id,))
            record = cur.fetchone()
            return dict(record) if record else None
    
def delete_tag(tag_id):
    statement = (   "DELETE FROM tags "
                    "WHERE tag_id = %s")

    with get_connection() as cn:
        with get_cursor(cn) as cur:
            cur.execute(statement, (tag_id,))
    
def add_tag(tag_name, user_name=None, tag_desc=None):
    ''' adds a tag and returns its ID
    '''
    statement = sql.SQL(    "INSERT INTO tags(tag_name, tag_desc, created_by) " 
                            "SELECT %s, %s, user_id "
                            "FROM users WHERE "
                            "user_name = %s "
                            "RETURNING tag_id")
    
    with get_connection() as cn:
        with get_cursor(cn) as cur:
            cur.execute(statement, (tag_name, tag_desc, user_name))
            return cur.fetchone()["tag_id"]
    
def update_tag(tag_id, new_name, new_desc=None):
    statement = sql.SQL(    "UPDATE tags "
                            "SET " 
                                "tag_name = %(tag_name)s, "
                                "tag_desc = %(tag_desc)s "
                            "WHERE tag_id = %(tag_id)s")
    
    with get_connection() as cn:
        with get_cursor(cn) as cur:
            cur.execute(statement, {
                'tag_id' : tag_id, 
                'tag_name' : new_name,
                'tag_desc' : new_desc})