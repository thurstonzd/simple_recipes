CREATE OR REPLACE FUNCTION recipe_json(p_recipe_id INT) RETURNS JSON AS $$
BEGIN
RETURN JSON_BUILD_OBJECT
(
	'recipe_id', recipe_id,
	'recipe_name', recipe_name,
	'recipe_desc', recipe_desc,
	'servings', servings,
	'total_time', TO_CHAR(total_time, 'HH24:MI:SS'),
	'total_time_minutes', (EXTRACT(hours FROM total_time) * 60) + EXTRACT(minutes FROM total_time),
	'created_by', users.user_name,
	'instructions',
	(
		SELECT JSON_AGG(JSON_BUILD_OBJECT(
			'step_number', step_number,
			'instruction', instruction
		))
		FROM 
		(
			SELECT step_number, instruction 
			FROM recipe_instructions 
			WHERE recipe_id = recipes.recipe_id
			ORDER BY step_number
		) AS instructions
	),
	'ingredients',
	(
		SELECT JSON_AGG(JSON_BUILD_OBJECT(
			'recipe_ingredient_id', i.recipe_ingredient_id,
			'quantity', i.quantity,
			'measurement_id', i.measurement_id,
			'measurement_plural', i.measurement_plural,
			'measurement_singular', i.measurement_singular,
			'measurement_abbr', i.measurement_abbr,
            'measurement_category', i.measurement_category,
            'measurement_system', i.measurement_system,
            'measurement_relative_size', i.relative_size,
			'ingredient_name', i.ingredient_name,
            'ingredient_concat',
            CASE
                WHEN i.measurement_id IS NULL
                    THEN i.ingredient_name
                ELSE 
                    '[' || i.measurement_plural || '] ' || 
                    i.ingredient_name
            END
		))
		FROM
		(
			SELECT 
				i.recipe_ingredient_id,
				i.quantity,
				i.ingredient_name,
				m.measurement_id,
				m.measurement_plural,
				m.measurement_singular,
				m.measurement_abbr,
                m.measurement_system,
                m.measurement_category,
                m.relative_size
			FROM recipe_ingredients AS i
				LEFT JOIN measurements AS m ON
					m.measurement_id = i.measurement_id
			WHERE recipe_id = recipes.recipe_id
            ORDER BY i.recipe_ingredient_id
		) AS i
	),
	'tags',
	(
		SELECT JSON_AGG(JSON_BUILD_OBJECT(
			'tag_id', tags.tag_id,
			'tag_name', tags.tag_name
		) ORDER BY tags.tag_name)
		FROM
		(
			SELECT t.tag_id, t.tag_name
			FROM recipe_tags AS rt
				INNER JOIN tags AS t ON
					t.tag_id = rt.tag_id
			WHERE recipe_id = recipes.recipe_id
		) AS tags
	),
    'images',
    (
        SELECT JSON_AGG(JSON_BUILD_OBJECT(
            'image_id', images.image_id,
            'image_file_name', images.image_file_name,
            'image_desc', images.image_desc
        ))
        FROM
        (
            SELECT image_id, image_file_name, image_desc
            FROM recipe_images
            WHERE recipe_id = recipes.recipe_id
        ) as images
    )
)
FROM recipes 
	LEFT JOIN users ON
		users.user_id = recipes.created_by
WHERE recipe_id = p_recipe_id;
END;
$$
LANGUAGE PLPGSQL;