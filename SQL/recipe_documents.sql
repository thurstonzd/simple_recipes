DROP VIEW IF EXISTS recipe_documents;

CREATE OR REPLACE VIEW recipe_documents AS
SELECT 
    r.recipe_id,
    r.recipe_name,
    users.user_name AS created_by,
    (
        SELECT COALESCE(STRING_AGG(
            t.tag_name::text, '; '::text ORDER BY t.tag_name),
            ''::text) 
            AS tags
       FROM recipe_tags rt
         JOIN tags t ON t.tag_id = rt.tag_id
      WHERE rt.recipe_id = r.recipe_id
    ) AS tags,
    (
        SETWEIGHT(TO_TSVECTOR(r.recipe_name::text), 'A') || 
        SETWEIGHT(TO_TSVECTOR(r.recipe_desc), 'B') || 
        -- ingredients
        SETWEIGHT(TO_TSVECTOR
        (
            (
                SELECT COALESCE(STRING_AGG(ingredient_name::text, ' '::text), 
                    ''::text) 
                    AS ingredients
                FROM recipe_ingredients
                WHERE recipe_id = r.recipe_id
            )
        ), 'C') ||
        -- tags
        SETWEIGHT(TO_TSVECTOR
        (
            (
                SELECT 
                    COALESCE
					(
						STRING_AGG(t.tag_name::text, ' '::text),
						''::text
					) || ' ' ||
					COALESCE
					(
						STRING_AGG(t.tag_desc::text, ' '::text),
						''::text
					) AS tags
				FROM recipe_tags rt
					JOIN tags t ON t.tag_id = rt.tag_id
				WHERE rt.recipe_id = r.recipe_id
            )
        ), 'B')
    )  AS doc
FROM recipes AS r
    LEFT JOIN users ON
        users.user_id = r.created_by
    LEFT JOIN recipe_tags AS rt ON
        rt.recipe_id = r.recipe_id
    LEFT JOIN tags AS t ON
        t.tag_id = rt.tag_id
GROUP BY r.recipe_id, r.recipe_name, users.user_name;