class Tag:
	def __init__(self):
		self.tag_id = None
		self.tag_name = None
		self.recipe = None
		
class Measurement:
	def __init__(self):
		self.measurement_id = None
		self.measurement_name = None
		self.RecipeIngredient = None
		
class RecipeIngredient:
	def __init__(self):
		self.recipe_ingredient_id = None
		
		# for storing associated Recipe object
		self.recipe = None 
		
		self.quantity = None
		
		# for storing associated Measurement object
		self.measurement = None
		
		self.ingredient_name = None
		
class RecipeInstruction:
	def __init__(self):
		self.step_number = None
		self.instruction = None
		self.recipe = None # for associated Recipe object
		
class Recipe:
	def __init__(self):
		self.recipe_id = None
		self.recipe_name = None
		self.recipe_desc = None
		self.servings = None
		self.total_time = None
		
		# list of RecipeIngredient objects
		self.ingredients = []
		
		# list of RecipeInstruction objects
		self.instructions = []
		
		# list of Tag objects
		self.tags = []