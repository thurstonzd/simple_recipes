-- updates the instructions for a provided recipe 
-- (overwriting any instructions currently specified)

-- the instructions_data is a subset of the recipes JSON, consisting of a JSON array
-- For example:
-- [
-- 	{"step_number": 1, "instruction": "Prepare ingredients"}, 
-- 	{"step_number": 2, "instruction": "Bake for 30 minutes"}
-- ]
CREATE OR REPLACE PROCEDURE set_recipe_instructions(
	p_recipe_id integer,
	instruction_data JSON)
LANGUAGE 'plpgsql'

AS $BODY$
BEGIN
	DELETE FROM recipe_instructions WHERE recipe_id = p_recipe_id;

	INSERT INTO recipe_instructions
	(recipe_id, step_number, instruction)
	VALUES
	(
		p_recipe_id,
		CAST(	json_array_elements(instruction_data)->>'step_number' AS INT),
				json_array_elements(instruction_data)->>'instruction'
	);
END;
$BODY$;
-- ==================================================================
-- updates the tags for a provided recipe 
-- (overwriting any tags currently specified)

-- the tag_data argument is a subset of the recipes JSON, consisting
-- of the tags array. The "tag_name" key is optional.

-- For example:

-- [{"tag_id" : 1, "tag_name" : "Cookies/Brownies/Bars"}, {"tag_id" : 2}]
CREATE OR REPLACE PROCEDURE set_recipe_tags(
	p_recipe_id integer,
	tag_data JSON)
LANGUAGE 'plpgsql'

AS $BODY$
BEGIN
	DELETE FROM recipe_tags WHERE recipe_id = p_recipe_id;

	INSERT INTO recipe_tags
	(recipe_id, tag_id)
	VALUES
	(
		p_recipe_id,
		CAST(	json_array_elements(tag_data)->>'tag_id' AS INT)
	);
END;
$BODY$;
-- ==================================================================
CREATE OR REPLACE PROCEDURE set_recipe_ingredients(
	p_recipe_id INT,
	ingredients_data JSON
)
LANGUAGE 'plpgsql'
AS $BODY$
BEGIN
	DELETE FROM recipe_ingredients WHERE recipe_id = p_recipe_id;
	
	WITH
		data_elems(obj) AS (SELECT JSON_ARRAY_ELEMENTS(ingredients_data)),
		ingredients AS
		(
			SELECT 
				CAST(obj ->> 'quantity' AS DECIMAL) AS quantity,
				obj ->> 'ingredient_name' AS ingredient_name,
				CAST(obj ->> 'measurement_id' AS INT) AS measurement_id,
				obj ->> 'measurement_plural' AS measurement_plural,
				obj ->> 'measurement_singular' AS measurement_singular,
				obj ->> 'measurement_abbr' AS measurement_abbr,
				obj ->> 'measurement_name' AS measurement_name
			FROM data_elems
		)
		
		INSERT INTO recipe_ingredients
		(
			recipe_id, 
			quantity, 
			measurement_id, 
			ingredient_name
		)
		SELECT
			p_recipe_id,
			i.quantity,
			m.measurement_id,
			CASE 
				WHEN 
					m.measurement_id IS NULL  
					AND i.measurement_name IS NOT NULL
				THEN 
					i.measurement_name || 
					' of ' || 
					i.ingredient_name
				ELSE i.ingredient_name
			END as ingredient_name_final
		FROM ingredients AS i
			LEFT JOIN measurements AS m ON
				LOWER(i.measurement_name) IN 
				(
					LOWER(m.measurement_plural),
					LOWER(m.measurement_singular),
					LOWER(m.measurement_abbr)
				);
END;
$BODY$;