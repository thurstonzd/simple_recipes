DROP TABLE IF EXISTS 
    user_statuses,
    users,
    tags,
    measurement_systems,
    measurement_categories,
    measurements,
    recipes,
    recipe_ingredients,
    recipe_instructions,
    recipe_tags,
    recipe_images;

-- 0
CREATE TABLE user_statuses
(
    status_id INT NOT NULL GENERATED BY DEFAULT AS IDENTITY
    (START WITH 1 INCREMENT BY 1),
    status_name VARCHAR(255) NOT NULL,
    status_desc TEXT NULL,
    PRIMARY KEY (status_id)
);

-- 1
CREATE TABLE users
(
    user_id INT NOT NULL GENERATED BY DEFAULT AS IDENTITY
        (START WITH 1 INCREMENT BY 1),
    user_name VARCHAR(255) NOT NULL UNIQUE,
    about_user TEXT NULL,
    user_status INT,
    password_hash BYTEA NULL,
    password_salt BYTEA NULL,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (user_id),
    FOREIGN KEY (user_status)
        REFERENCES user_statuses(status_id)
);

-- 2
CREATE TABLE tags
(
	tag_id INT NOT NULL GENERATED BY DEFAULT AS IDENTITY
		(START WITH 1 INCREMENT BY 1),
	tag_name VARCHAR(255) NOT NULL,
    tag_desc TEXT NULL,
    created_by INT NULL ,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (tag_id),
    FOREIGN KEY (created_by)
        REFERENCES users(user_id)
        ON DELETE SET NULL
        ON UPDATE NO ACTION
);

-- 3.0
CREATE TABLE measurement_systems
(
    -- US, SI
    system_code VARCHAR(10) NOT NULL PRIMARY KEY,
    system_name VARCHAR(255) NOT NULL
);

-- 3.1
CREATE TABLE measurement_categories
(
    category_code CHAR(1) NOT NULL PRIMARY KEY,
    category_name VARCHAR(255) NOT NULL
);

-- 3.2
CREATE TABLE measurements
(
    measurement_id INT NOT NULL GENERATED BY DEFAULT AS IDENTITY 
		( INCREMENT 1 START 1) PRIMARY KEY,
    measurement_plural VARCHAR(255) NOT NULL,
    measurement_singular VARCHAR(255) NOT NULL ,
    measurement_abbr VARCHAR(255) NULL,
    measurement_system VARCHAR(10) NOT NULL,
    measurement_category CHAR(1) NOT NULL,
    relative_size INT NOT NULL,
    include_in_conversions BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (measurement_system)
        REFERENCES measurement_systems(system_code)
        ON DELETE NO ACTION
        ON UPDATE NO ACTION,
    FOREIGN KEY (measurement_category)
        REFERENCES measurement_categories(category_code)
        ON DELETE NO ACTION
        ON UPDATE NO ACTION,
    CONSTRAINT u_measurement UNIQUE 
        (measurement_system, measurement_category, relative_size)
);

-- 6
CREATE TABLE recipes
(
	recipe_id INT NOT NULL GENERATED BY DEFAULT AS IDENTITY
		(START WITH 1 INCREMENT BY 1),
	recipe_name VARCHAR(255) NOT NULL,
	recipe_desc TEXT NULL,
	servings INT NOT NULL DEFAULT 1,
	total_time INTERVAL NULL,
    created_by INT NULL,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (recipe_id),
    FOREIGN KEY (created_by)
        REFERENCES users(user_id)
        ON DELETE SET NULL
        ON UPDATE NO ACTION
);

-- 7
CREATE TABLE recipe_ingredients
(
    recipe_ingredient_id INT NOT NULL 
		PRIMARY KEY
		GENERATED BY DEFAULT AS IDENTITY
		(START WITH 1 INCREMENT BY 1),
	recipe_id INT NOT NULL,
    quantity NUMERIC(18,2) NOT NULL,
    measurement_id INT NULL,
    ingredient_name VARCHAR(255) NOT NULL,
	FOREIGN KEY (recipe_id)
        REFERENCES recipes (recipe_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
	FOREIGN KEY (measurement_id)
		REFERENCES measurements(measurement_id)
		ON DELETE NO ACTION
		ON UPDATE NO ACTION
);

-- 8
CREATE TABLE recipe_instructions
(
	recipe_id INT NOT NULL,
	step_number INT NOT NULL,
	instruction TEXT NOT NULL,
	PRIMARY KEY (recipe_id, step_number),
	FOREIGN KEY (recipe_id) 
		REFERENCES recipes(recipe_id)
		ON DELETE CASCADE
		ON UPDATE CASCADE
);

-- 9
CREATE TABLE recipe_tags
(
	recipe_id INT NOT NULL,
	tag_id INT NOT NULL,
	FOREIGN KEY (recipe_id)
		REFERENCES recipes(recipe_id)
		ON DELETE CASCADE
		ON UPDATE NO ACTION,
	FOREIGN KEY (tag_id)
		REFERENCES tags(tag_id)
		ON DELETE NO ACTION
		ON UPDATE NO ACTION,
	PRIMARY KEY (recipe_id, tag_id)
);

-- 10
CREATE TABLE recipe_images
(
    image_id INT NOT NULL PRIMARY KEY
		GENERATED BY DEFAULT AS IDENTITY
		(START WITH 1 INCREMENT BY 1),
    recipe_id INT NOT NULL,
    image_file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(255) NOT NULL,
    image_desc VARCHAR(255) NULL,
    image_bytes BYTEA NOT NULL,
    FOREIGN KEY (recipe_id)
        REFERENCES recipes(recipe_id)
        ON DELETE CASCADE
        ON UPDATE NO ACTION
);