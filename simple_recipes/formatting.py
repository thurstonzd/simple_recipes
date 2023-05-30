from fractions import Fraction

def pluralize(n, singular, plural):
    return singular if n == 1 else plural

def fractionalize(x):
    '''returns a number formatted as an approximate mixed fraction.
    e.g. `1.25` => `1 1/4`.
    Note that conversion is approximate, using Python's Fraction `limit_denominator(10)`
    Note that this function only works with positive numbers.
    '''
    if type(x) is int:
        return str(x)
    
    i, f = divmod(x, 1)

    f = Fraction(f).limit_denominator(10)

    # handle weird float issues
    if f == 1:
        i += 1
        f = 0

    format_strings = []
    
    if i > 0: format_strings.append('{0:0.0f}')
    if f > 0: format_strings.append('{1}')

    return ' '.join(format_strings).format(i, f)

def get_time_format_string(h=0, m=0):
    '''returns a human-readable time format string, 
    based on provided hours and minutes.
    in format of "{h} hours {m} minutes"
    '''
    format_strings = []
    if h > 0:
        format_strings.extend(['{0}', pluralize(h, 'hour', 'hours')])
    if m > 0:
        format_strings.extend(['{1}', pluralize(m, 'minute', 'minutes')])

    return ' '.join(format_strings)

def get_readable_time(h=0, m=0):
    '''returns a human-readable time, based on provided hours and minutes.
    In format of "{h} hours {m} minutes".
    Example: 
    get_readable_time(1,3) => `1 hour 3 minutes`'''
    format_strings = []

    h += m // 60
    m = m % 60

    if h > 0: 
        format_strings.extend(['{0}', pluralize(h, 'hour', 'hours')])
    if m > 0: 
        format_strings.extend(['{1}', pluralize(m, 'minute', 'minutes')])

    return ' '.join(format_strings).format(h, m)