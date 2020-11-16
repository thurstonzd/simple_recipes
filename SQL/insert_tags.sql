TRUNCATE TABLE tags, recipe_tags RESTART IDENTITY;

INSERT INTO tags
(tag_name)
VALUES
('Beef'),
('Chocolate'),
('Dairy'),
('Lamb'),
('Nuts'),
('Pork'),
('Poultry'),
('Seafood'),
('Appetizer'),
('Cake'),
('Dessert'),
('Entree'),
('Pie'),
('Sauce/Pudding/Frosting'),
('Bread'),
('Cookies/Brownies/Bars'),
('Soups/Sandwiches'),
('Drinks'),
('Vegetarian');