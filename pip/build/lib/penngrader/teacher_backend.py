import json
import urllib.request
import dill
import base64
import types
from urllib.error import HTTPError
import ast
import types

api_url = 'https://qk1b0ut5z2.execute-api.us-east-1.amazonaws.com/default/TeacherBackend'
api_key = 'LOEn9CIMqFGWBc9UCEyk53SxS0le2Vr2165AkDk4'

def get_imported_libraries():
    '''Retruns a list of (package name, package shortname, fromlist item) tuples for all imported packages'''
    imported_packages = set()
    for name, val in list(globals().items()):
        if type(val) == types.ModuleType and name not in ['__builtin__','__builtins__', 'penngrader','_sh']:
            imported_packages.add((val.__name__, name, None))
        elif type(val) == types.FunctionType and val.__module__ not in ['__main__']:
            imported_packages.add((val.__module__, val.__module__, val.__name__))
    return list(imported_packages)  

def serialize(obj):
    '''Dill serializes Python object into a UTF-8 string'''
    byte_serialized = dill.dumps(obj, recurse = True)
    return base64.b64encode(byte_serialized).decode("utf-8")

def validate_test_cases(test_cases):
    for test_id in test_cases:
        if not type(test_cases[test_id]) == types.FunctionType:
            print('Error: The test_case dictionary defined above should map a string (i.e test case name) to a function.')
            return False
    return True

class PennGraderBackend:
    
    def __init__(self, homework_id, secret_key):
        self.homework_id = homework_id
        self.secret_key = secret_key
        self.validate_credentials()
            
    def validate_credentials(self):
        payload = { 
            'homework_id' : self.homework_id, 
            'secret_key' : self.secret_key, 
            'request_type': 'credentials', 
            'payload' : serialize(None)
        }
        return self.send_payload(payload, api_url, api_key)
    
    def upload_test_cases(self, test_cases):
        payload = { 
            'homework_id' : self.homework_id, 
            'secret_key' : self.secret_key, 
            'request_type' : 'tests',
            'payload' : serialize({
                'libraries'  : get_imported_libraries(),
                'test_cases' : test_cases
            })
        }
        if validate_test_cases(test_cases):
            self.send_payload(payload, api_url, api_key)
        
    def send_payload(self, payload, api_endpoint, api_key):
        params = json.dumps(payload).encode('utf-8')
        headers = {'content-type': 'application/json', 'x-api-key': api_key}
        request = urllib.request.Request(api_endpoint, data = params, headers = headers)
        try:
            response = urllib.request.urlopen(request)
            print('{}'.format(response.read().decode('utf-8')))
            return True
        except HTTPError as error:
            print('Error: {}'.format(error.read().decode("utf-8")))
            return False  
