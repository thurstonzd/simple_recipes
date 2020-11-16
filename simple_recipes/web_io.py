import re
from fractions import Fraction
from decimal import Decimal, getcontext

fraction_translation = {
    # vulgar fractions
    '\u00BC': '1/4',
    '\u00BD': '1/2',
    '\u00BE': '3/4',
    '\u2150': '1/7',
    '\u2151': '1/9',
    '\u2152': '1/10',
    '\u2153': '1/3',
    '\u2154': '2/3',
    '\u2155': '1/5',
    '\u2156': '2/5',
    '\u2157': '3/5',
    '\u2158': '4/5',
    '\u2159': '1/6',
    '\u215A': '5/6',
    '\u215B': '1/8',
    '\u215C': '3/8',
    '\u215D': '5/8',
    '\u215E': '7/8',
    # fraction slash
    '\u2044': '/',
    # superscripts
    '\u2070': '0',
    '\u00B9': '1',
    '\u00B2': '2',
    '\u00B3': '3',
    '\u2074': '4',
    '\u2075': '5',
    '\u2076': '6',
    '\u2077': '7',
    '\u2078': '8',
    '\u2079': '9',
    # subscripts
    '\u2080': '0',
    '\u2081': '1',
    '\u2082': '2',
    '\u2083': '3',
    '\u2084': '4',
    '\u2085': '5',
    '\u2086': '6',
    '\u2087': '7',
    '\u2088': '8',
    '\u2089': '9',
    }

digit_pattern = re.compile(r'''
	\d+         # must start with digit
	[\d\/\.\s]*	# optionally followed by more digits, '/', '.' and spaces
	\s		    # finally ended by whitespace.''', re.VERBOSE)

alpha_pattern = re.compile(r'''
    (               # EITHER:
        ([A-Za-z]+) # letters
        |           # OR...
        (\d+\-)     # digit(s) followed by a '-'
    )
    .*              # followed by whatever
    ''', re.VERBOSE)
    
token_pattern = re.compile(r'''
    \[              # literal '['
    (               # start of capturing group
    [^\[\]]+      # text that doesn't contain square brackets
    )               # end of capturing group
    \.?             # optional '.'
    \]              # literal ']'
    (\s of)?          # optional ' of' after token
    \s+             # whitespace
    ''', re.VERBOSE)

def format_instructions(data):
    '''formats a list of instruction dicts as a string
    '''
    if 'instructions' in data: data = data['instructions']

    return '\n'.join(['{step_number}. {instruction}'.format(**instr)
                      for instr in data])
    
def format_ingredients(data):
    '''formats a list of ingredients as a string
    '''
    if 'ingredients' in data: data = data['ingredients']

    return '\n'.join(['{quantity_string} {ingredient_concat}'.format(**ingr)
                        for ingr in data])
    

def parse_instructions(instruction_text):
    '''parses a string into a list of instructions.

    This function assumes instruction_text separates each instruction by a \n.
    Each line may optionally begin with white space and/or numbers.
    These are discarded in the returned value
    A list of strings is returned.

    parse_instructions("""
    1. Preheat oven
    
    2. Combine ingredients
    Cook for 15 minutes""")
    -->
    ["Preheat oven", "Combine ingredients", "Cook for 15 minutes"]
    '''
    # strip text and replace vulgar fractions with parsable characters
    # (e.g. ¼ -> 1/4)
    trans = str.maketrans(fraction_translation)
    instruction_text = instruction_text.strip().translate(trans)

    if not instruction_text: return []

    instructions = []

    for i, instr in enumerate(re.split(r'\n\s*', instruction_text)):
        instr = re.sub(r'.*\t', '', instr).strip()
        instr_start = alpha_pattern.search(instr)
        if instr_start:
            instructions.append(instr[instr_start.start():])

    return instructions

def parse_ingredient(ingredient_text):
    '''parses a string into a single ingredient dictionary

    parse_ingredient('3 cups flour') -->
    {"quantity": 3, "measurement_name": "cups", "ingredient_name": "sugar"}
    '''

    # strip text;
    # replace vulgar fractions with parsable characters (e.g. ¼ -> 1/4)
    # remove tabs and anything preceding them.
    trans = str.maketrans(fraction_translation)
    ingredient_text = ingredient_text.translate(trans)
    ingredient_text = re.sub(r'.*\t', '', ingredient_text).strip()

    # set precision for decimal library
    getcontext().prec = 6

    ingr_dict = {}
    quantity_match = digit_pattern.search(ingredient_text)
    alpha_match = alpha_pattern.search(ingredient_text)
    
    # start by assuming that quantity is 1 
    q = 1
    measurement = None
    
    #################################################################
    # for when we can ascertain a quantity
    if quantity_match and quantity_match.start() < alpha_match.start():
        
        # handle quantity part
        quantity_start = quantity_match.start()
        quantity_end = quantity_match.end()
        number_text = ingredient_text[quantity_start:quantity_end].strip()
        numbers = number_text.split(maxsplit=1)
        
        if len(numbers) == 1:
            q = Fraction(numbers[0]).limit_denominator(10)
        elif len(numbers) == 2:
            q = int(numbers[0]) + Fraction(numbers[1]).limit_denominator(10)
            
        # convert number to decimal, so it can be used by psycopg2
        q = float(q.numerator / Decimal(q.denominator))
        
        ingredient_text = ingredient_text[quantity_end:].strip()
        
        # identify measurement token and separate it from rest of text.
        measurement = token_pattern.search(ingredient_text)
        if measurement: measurement = measurement.groups()[0].replace('.', '')
        
        ingredient_text = re.sub(token_pattern, '', ingredient_text, count=1)
    #################################################################
    # no quantity is specified.
    else: ingredient_text = ingredient_text[alpha_match.start():]
    #################################################################
    
    ingr_dict['quantity'] = q
    ingr_dict['ingredient_name'] = ingredient_text
    if measurement: ingr_dict['measurement_name'] = measurement
    return ingr_dict

def pluralize(n, singular, plural):
    return singular if n == 1 else plural

def get_time_format_string(h, m):
    '''returns a human-readable time, based on provided hours and minutes.
    in format of "{h} hours {m} minutes"
    '''
    format_strings = []
    if h > 0:
        format_strings.extend(['{0}', pluralize(h, 'hour', 'hours')])
    if m > 0:
        format_strings.extend(['{1}', pluralize(m, 'minute', 'minutes')])

    return ' '.join(format_strings)
    
def cursor_results_to_html_table(cur):
    headers = ['<th>' + c.name + '</th>' for c in cur.description]
    
    return '<thead>\n\t<trow>\n\t{0}\n\t</trow>\n</thead>'.format(
        '\t'.join(headers))