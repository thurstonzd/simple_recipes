CREATE OR REPLACE FUNCTION measurements_json() RETURNS JSON AS $$
BEGIN
RETURN ARRAY_TO_JSON
(
    ARRAY_AGG
    (
        JSON_BUILD_OBJECT
        (
            'measurement_id', measurement_id,
            'measurement_plural', measurement_plural,
            'measurement_singular', measurement_singular,
            'measurement_abbr', measurement_abbr,
            'measurement_system', measurement_system,
            'measurement_category', measurement_category,
            'relative_size', relative_size,
            'include_in_conversions', include_in_conversions
        )
    ORDER BY 
        -- use descending order for category, so volume (with fl oz)
        -- comes before mass (with ounce).
        measurement_category DESC, 
        measurement_system ASC, 
        relative_size ASC
    )
)
FROM measurements;
END;
$$
LANGUAGE PLPGSQL