import re
from fractions import Fraction
from decimal import Decimal, getcontext

from simple_recipes.formatting import fractionalize, pluralize
from simple_recipes import ureg, Q_

# set precision for decimal library
getcontext().prec = 6

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

quantity_pattern = re.compile(r'''
    (           # start of capturing group
	\d+         # must start with digit
	[\d\/\.\s]*	# optionally followed by more digits, '/', '.' and spaces
    )           # end of capturing group
    (.*)        # and then the rest of it, which is presumably the unit.
    ''', re.VERBOSE)

quantity_token_pattern = re.compile(r'''
    {{\s*   # start of token: `{{`, followed by optional whitespace.
    (\!?)   # optional `!` to signify no multiplication
    \s*     # optional space
    ([^}]*) # the tokenized text: Anything between curly brackets.
    \s*}}   # more optional space, followd by token end
''', re.VERBOSE)

def parse_quantity_string(quantity_text):
    '''parses a string into a pint quantity,
    where the magnitude is a float. Takes care of things
    like vulgar fraction code points and mixed fractions.
    Naked numbers turn into dimensionless quantities.
    Examples:
    parse_quantity_string('3 cups')     => <Quantity(3.0, 'cup')>
    parse_quantity_string('¼ cup')      => <Quantity(0.25, 'cup')>
    parse_quantity_string('1 1/2 cup')  => <Quantity(1.5, 'cup')>
    parse_quantity_string('7')          => <Quantity(7.0, 'dimensionless')>
    '''
    
    # strip text and replace vulgar fractions with parsable characters
    # (e.g. ¼ -> 1/4)
    trans = str.maketrans(fraction_translation)
    quantity_text = quantity_text.strip().translate(trans)

    # remove periods from unit string, and replace spaces with underscores.
    # e.g. `fl. oz` => `fl_oz`
    quantity_text = re.sub(
        r'([A-Z])\.', r'\1', 
        quantity_text, 
        flags=re.IGNORECASE)
    
    quantity_text = re.sub(
        r'([A-Z])\s+', r'\1_', 
        quantity_text, 
        flags=re.IGNORECASE)

    my_match = quantity_pattern.search(quantity_text)
    number_part = my_match.group(1)
    numbers = number_part.split(maxsplit=1)

    if len(numbers) == 1: 
        n = Fraction(numbers[0]).limit_denominator(10)
    elif len(numbers) == 2:
        n = int(numbers[0]) + Fraction(numbers[1]).limit_denominator(10)

    n = n.numerator / Decimal(n.denominator)

    if len(my_match.groups()) > 1: # there's a unit string.
        return Q_(n, my_match.group(2))
    else: return Q_(n)

def convert_quantity(quantity, to_system, units, min_threshold=None, max_threshold=None):
    '''Converts a Pint quantity to another measurement system, 
    based on provided units. to_system must be either US or SI.
    Example: 
    convert_quantity(Q_('1 cup'), 'SI', units) => <Quantity(236.5882, 'ml')>
    '''
    if not min_threshold: min_threshold = 0.25
    if not max_threshold: max_threshold = 5 if to_system == 'US' else 100

    to_quantity = quantity
    from_unit = units[str(quantity.u)]
    for k in units.keys():
        to_unit = units[k]
        if to_unit['unit_category'] == from_unit['unit_category']:
            if to_unit['unit_system'] == to_system:
                to_quantity = quantity.to(k)
                    
                 # use direct comparisons rather than `in range` construct, 
                 # since thresholds are floats.
                if (to_quantity.magnitude >= min_threshold and 
                    to_quantity.magnitude <= max_threshold):
                    break

    return to_quantity

def convert_recipe_text(recipe_text, multiplier=1, to_system=None, units=None, quantity_tag=None, **quantity_attribs):
    '''parses the provided text for tokenized measurements
    multiplies measurements by multipler
    (e.g. if multiplier is 3, {{ 3 cups }} becomes {{ 9 cupes }}
    if to_system is specified (US or SI), measurements not in that to_system
    are "coerced" to the unit system.
    (e.g. if to_system is SI, {{ 2 cups }} might be converted to {{ 0.47 Litres }}
    '''

    if units == None:
        raise ValueError("units must be defined")

    def my_repl(matchobj):
        do_not_multiply = False
        quantity_string = matchobj.group(2).strip()
        if matchobj.group(1) == '!': 
            do_not_multiply = True
        try:
            quantity = parse_quantity_string(quantity_string)
            if not do_not_multiply: quantity *= Decimal(multiplier)
            magnitude = quantity.magnitude
            #quantity.default_format = "~P" # short pretty format

            if quantity.dimensionless:
                quantity_string =  str(magnitude)
            else:
                # quantity_string = str(quantity)
                # continue with unit conversion if requested
                if to_system:
                    quantity = convert_quantity(quantity, to_system, units)

                quantity_unit = units[str(quantity.u)]
                if quantity_unit['unit_system'] == 'SI':
                    quantity_string = '{:.2f} {}'.format(
                        quantity.magnitude,
                        quantity_unit['unit_abbr'])
                else:
                    quantity_string = '{} {}'.format(
                        fractionalize(quantity.magnitude),
                       pluralize(
                            quantity.magnitude, 
                            quantity_unit['unit_singular'], 
                            quantity_unit['unit_plural']))

        except Exception as e:
            # return matchobj.group(0)
            print(e)

        if quantity_tag:
            attribs = ' '.join(f"{k.lower()}=\"{quantity_attribs[k]}\"" for k in quantity_attribs)
            quantity_string = f"<{quantity_tag} {attribs}>{quantity_string}</{quantity_tag}>"
        return quantity_string
        
    converted = recipe_text
    converted = re.sub(quantity_token_pattern, my_repl, recipe_text)

    return converted
