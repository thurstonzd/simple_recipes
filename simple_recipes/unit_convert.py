from decimal import Decimal

# https://requests.readthedocs.io/
# import requests

API_KEY = "13ca3f6f-d726-4aae-ab35-ec27d4cd6c53"
API_BASE = "https://api.unitconvert.io/api/v1/"

headers = {'api-key' : API_KEY, 'accept' : 'application/json'}

# constants for lookup
US, SI, VOLUME, MASS = 'US', 'SI', 'V', 'M'

# def get_unit_registry():
    # return UnitRegistry()

def convert_to_other_system(from_ingredient, to_system, measurements, ureg=None, **kwargs):
    '''returns to_ingredient conversion
    given a quantity in either US or SI,
    converts to a measurement in the specified system,
    
    supported options:
     - sort_descending : Boolean (default False)
        if False, finds smallest unit that works; otherwise, finds biggest
     - min_threshold : int (default 0.25)
        if sort_ascending=False, finds smallest unit >= this number
     - max_threshold : int (default 10 for US; 100 for SI)
        if sort_ascending=True, finds biggest unit <= this number
    
    example usage:
    convert_to_other_system(
        {
            'quantity': 2, 
            'measurement_plural' : 'teaspoons', 
            'measurement_category': 'V', 
            'measurement_system': 'US'
        }, 
        'SI') 
        ==>
        {
            'quantity': 3.02, 
            'measurement_plural': 'milliliters', 
            'measurement_category': 'V', 
            'measurement_system': 'SI'
        }
    '''
    if not from_ingredient['measurement_id']: 
        return from_ingredient
        
    from_system = from_ingredient['measurement_system']
    
    if not ureg: ureg = UnitRegistry()
    
    # initialize parameters
    default_min = 0.25
    default_max = 5 if to_system == 'US' else 100
    min_threshold = Decimal(kwargs.get('min_threshold', default_min))
    max_threshold = Decimal(kwargs.get('max_threshold', default_max))
    
    # initialize From quantity
    from_quantity = ureg.Quantity(
        from_ingredient['quantity'],
        from_ingredient['measurement_plural'].replace(' ', '_').lower())
    
    # start checking conversions
    if kwargs.get('sort_descending', False): measurements.reverse()
    
    for m in measurements:
        to_unit = m['measurement_plural'].replace(' ', '_').lower()
        to_quantity = from_quantity.to(to_unit)
        to_magnitude = to_quantity.magnitude
        
        from_ingredient.update({'quantity' : to_magnitude})
        from_ingredient.update(m)
        
        if to_magnitude >= min_threshold and to_magnitude <= max_threshold:
            break

# def convert(from_quantity, from_units, to_units):
#     '''returns the quantity of to_units that's equivalent to from_units
    
#     example usage:
#     convert(100, 'ml', 'tsp') -> 20.2844
#     '''
#     url = API_BASE + 'Measurements/Convert'
#     payload = {
#         'from' : '{} {}'.format(from_quantity, from_units),
#         'to' : to_units
#     }
    
#     r = requests.get(url, headers=headers, params=payload)
    
#     if r.status_code == requests.codes.ok:
#         return r.json()['amount']