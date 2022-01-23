from dateutil.parser import parse
import datetime

def isdigit(string):
    try:
        float(string)
        return True
    except ValueError:
        try:
            float(string.replace(',', '.'))
            return True
        except ValueError:
            return string.isdigit()
        
def is_date_or_time(string, fuzzy=False):
    if isdigit(string):
        return False
    
    try:
        parse(string, fuzzy=fuzzy)
        return True
    except ValueError:
        return False
    
def contains_date(string):
    for word in string.split(' '):
        if is_date_or_time(word):
            return True
        
    GERMAN_DATES = ('montag', 'dienstag', 'mittwoch', 
                'donnerstag', 'freitag', 'samstag', 'sonntag')
    for day in GERMAN_DATES:
        if day in string.lower():
            return True
        
    return False
