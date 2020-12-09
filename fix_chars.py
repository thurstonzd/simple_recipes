from simple_recipes.db import get_connection, get_cursor

with get_connection() as cn:
    with get_cursor(cn) as cur:
        sql = ( "UPDATE recipe_instructions "
                "SET instruction = REGEXP_REPLACE(REGEXP_REPLACE(instruction, '(\d)ø', '\1°', 'g'), '(\D)ø(\D)', '\1o\2', 'g') "
                "WHERE instruction LIKE '%ø%';")

        cur.execute(sql)