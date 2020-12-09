from simple_recipes.db import get_connection, get_cursor

cn = get_connection()
cur = get_cursor(cn)

sql = ( "UPDATE recipe_instructions "
        "SET instruction = REGEXP_REPLACE(REGEXP_REPLACE(instruction, '(\d)ø', '\1°', 'g'), '(\D)ø(\D)', '\1o\2', 'g') "
        "WHERE instruction LIKE '%ø%';")

cur.execute(sql)