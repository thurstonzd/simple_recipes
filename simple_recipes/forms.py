from flask_wtf import FlaskForm
from wtforms import *
from flask_wtf.file import FileField, FileRequired

class UserForm(FlaskForm):
    user_name = StringField('User Name')
    current_pw = StringField("Current Password", render_kw = {"type" : "password"})
    new_pw = StringField("New Password", render_kw = {"type" : "password"})
    new_pw_confirmation = StringField("Confirm new password",
        render_kw = {
            "type" : "password", 
            "title" : "Please enter the same password as above."})

class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.

    from https://wtforms.readthedocs.io/en/stable/specific_problems.html
    """
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class DeletionForm(FlaskForm):
    '''placeholder for a form used to delete a record.
    no fields are needed, since the URL contains the
    field to delete.
    '''
    pass

class TagForm(FlaskForm):
    tag_name = StringField('Tag Name', 
        validators=[validators.required()])
    tag_desc = TextAreaField('Tag Description',
        render_kw = {'rows' : 10, 'cols' : 40})
        
class RecipeConversionForm(FlaskForm):
    unit_system = RadioField('Unit System',
        choices = [
            ('US', 'US Customary System'),
            ('SI', 'Metric System')
        ])
    multiplier = IntegerField('Multiplier', 
        default=1, 
        render_kw = {'type': 'number', 'min': 0.1, 'step': 0.1})
        
class RecipeSearchForm(FlaskForm):
    how = RadioField('Type of Search', 
        choices=[
            ('all', 'all'), 
            ('any', 'any'),
            ('custom', 'custom')
        ])
    what = StringField('Search',
        render_kw={
            'type': 'search', 
            'placeholder': 'Enter search here…'})
    
class RecipeForm(FlaskForm):
    ingredients_placeholder = (
        'Enter each ingredient on a separate line, like this.\n'
        ' - or like this.\n'
        '\n'
        ' - or even like this, with a blank line in between.'
    )

    instructions_placeholder = (
        'Enter each instruction on a separate line, like this.\n'
        ' 2. Or like this.\n'
        '\n'
        ' 3. or even like this, with a blank line in between.'
    )

    recipe_name = StringField('Recipe Name', render_kw={'size' : 40})
    recipe_desc = TextAreaField('Recipe Description', 
        render_kw={'rows': 10, 'cols': 40})
    servings = IntegerField('Servings', 
        default=1, 
        render_kw={'type': 'number', 'min': 1})
    total_time_minutes = IntegerField('Total Time (minutes)',
        [validators.optional()],
        render_kw={'type': 'number', 'min': 1})
    recipe_ingredients = TextAreaField('Ingredients',
        render_kw={
            'rows': 10, 'cols': 40, 'wrap': 'off', 
            'placeholder': ingredients_placeholder})
    recipe_instructions = TextAreaField('Directions',
        render_kw={
            'rows': 10, 'cols': 40, 'wrap': 'off',
            'placeholder' : instructions_placeholder})
    recipe_tags = SelectMultipleField('Tags', coerce=int,
        render_kw={'size': 20})
        
    image_uploads = FileField('Choose images to upload', 
        render_kw={
            'accept' : 'image/*', 
            'multiple' : True})
    
    image_descriptions = TextAreaField('Image Descriptions',
        render_kw={
            'rows': 10, 'cols': 50, 'wrap': 'off',
            'placeholder': 'Place each description on a separate line.'})
    image_deletions = MultiCheckboxField('Images to delete', 
        [validators.optional()], coerce=int)
    created_by = HiddenField("Created By")