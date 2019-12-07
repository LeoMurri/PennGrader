import json
import dill
import base64
import types
import ast
import types
import urllib.request
import pandas as pd
from datetime import datetime

from urllib.error import HTTPError

# Request types
HOMEWORK_ID_REQUEST     = 'GET_HOMEWORK_ID'
UPDATE_METADATA_REQUEST = 'UPDATE_METADATA'
UPDATE_TESTS_REQUEST    = 'UPDATE_TESTS'
GRADES_REQUEST          = 'ALL_STUDENTS_GRADES'

# Lambda endpoints
config_api_url = 'https://uhbuar7r8e.execute-api.us-east-1.amazonaws.com/default/HomeworkConfig'
config_api_key = 'UPK6QWTou1EDI27uIqDW4FHIcMXRVRS4HN6lq148'
grades_api_url = 'https://1rwoprdby6.execute-api.us-east-1.amazonaws.com/default/Grades'
grades_api_key = 'lY1O5NDRML9zEyRvWhf0c1GeEYFe3BE710Olbh3R'

def is_function(val):
    return type(val) == types.FunctionType


def is_module(val):
    return type(val) == types.ModuleType


def is_external(name):
    return name not in ['__builtin__','__builtins__', 'penngrader','_sh', '__main__'] and 'penngrader' not in name


class PennGraderBackend:
    
    
    def __init__(self, secret_key, homework_number):
        self.secret_key = secret_key
        self.homework_number = homework_number
        self.homework_id = self._get_homework_id()
        if 'Error' not in self.homework_id:
            response  = 'Success! Teacher backend initialized.\n\n'
            response += 'Homework ID: {}'.format(self.homework_id)
            print(response)
        else:
            print(self.homework_id)
            

    def update_metadata(self, deadline, total_score, max_daily_submissions):
        request = { 
            'homework_number' : self.homework_number, 
            'secret_key' : self.secret_key, 
            'request_type' : UPDATE_METADATA_REQUEST,
            'payload' : self._serialize({
                'max_daily_submissions' : max_daily_submissions,
                'total_score' : total_score,
                'deadline' : deadline
            })
        }
        print(self._send_request(request, config_api_url, config_api_key))
    
            
    def update_test_cases(self):
        request = { 
            'homework_number' : self.homework_number, 
            'secret_key' : self.secret_key, 
            'request_type' : UPDATE_TESTS_REQUEST,
            'payload' : self._serialize({
                'libraries'  : self._get_imported_libraries(),
                'test_cases' : self._get_test_cases(),
            })
        }
        print(self._send_request(request, config_api_url, config_api_key))
    
    
    def get_raw_grades(self, with_deadline = False):
        request = { 
            'homework_id' : self.homework_id, 
            'secret_key' : self.secret_key, 
            'request_type' : GRADES_REQUEST,
        }
        response = self._send_request(request, grades_api_url, grades_api_key)
        if 'Error' in response:
            print(response)
            return None
        else:
            grades, deadline = self._deserialize(response)
            if with_deadline:
                return pd.DataFrame(grades), deadline
            else:
                return pd.DataFrame(grades)
    
    
    def get_grades(self):
        grades_df, deadline = self.get_raw_grades(with_deadline = True)
        if grades_df is not None:
            
            if grades_df.shape[0] == 0:
                return "There have been no submissions."
            
            # Extract student ID from [student_submission_id]
            grades_df['student_id'] = grades_df['student_submission_id'].apply(lambda x: str(x).split('_')[0])

            # Convert to correct types
            grades_df['timestamp'] = pd.to_datetime(grades_df['timestamp'])
            grades_df['student_score'] = grades_df['student_score'].astype(int)

            # Get total scores per students
            scores_df = grades_df.groupby('student_id').sum().reset_index()[['student_id','student_score']]

            # Get late days
            late_df = grades_df.groupby('student_id').max().reset_index()[['student_id','timestamp']].rename(columns = {'timestamp':'latest_submission'})

            # Calculate number of hours from local to UTC
            local_to_utc = datetime.utcnow() - datetime.now()

            # Subtract timechange offset from timestamp (lambdas are in UTC)
            late_df['latest_submission'] = late_df['latest_submission'] - local_to_utc

            # Add deadline from notebook context
            late_df['deadline'] = pd.to_datetime(deadline)

            # Add delta btw latest_submission and deadline
            late_df['days_late'] = (late_df['latest_submission'] - late_df['deadline']).dt.ceil('D').dt.days

            # Merge final grades
            final_df = scores_df.merge(late_df, on = 'student_id')[['student_id','student_score','latest_submission','deadline','days_late']]
            final_df['days_late'] = final_df['days_late'].apply(lambda x : x if x > 0 else 0)
            return final_df
    
    
    def _get_homework_id(self):
        request = { 
            'homework_number' : self.homework_number,
            'secret_key' : self.secret_key,
            'request_type' : HOMEWORK_ID_REQUEST,
            'payload' : self._serialize(None)
        }
        return self._send_request(request, config_api_url, config_api_key)

        
    def _send_request(self, request, api_url, api_key):
        params = json.dumps(request).encode('utf-8')
        headers = {'content-type': 'application/json', 'x-api-key': api_key}
        request = urllib.request.Request(api_url, data=params, headers=headers)
        try:
            response = urllib.request.urlopen(request)
            return '{}'.format(response.read().decode('utf-8'))
        except HTTPError as error:
            return 'Error: {}'.format(error.read().decode("utf-8")) 
        
    
    def _get_imported_libraries(self):
        # Get all externally imported base packages
        packages = set() # (package, shortname)
        for shortname, val in list(globals().items()):
            if is_module(val) and is_external(shortname):
                base_package = val.__name__.split('.')[0]
                packages.add(base_package)
            if is_function(val) and is_external(val.__module__):
                base_package = val.__module__.split('.')[0]
                packages.add(base_package)

        # Get all sub-imports i.e import sklearn.svm etc 
        imports = set() # (module path , shortname )
        for shortname, val in list(globals().items()):
            if is_module(val) and is_external(shortname):
                imports.add((val.__name__, shortname))

        # Get all function imports 
        functions = set() # (module path , function name)
        for shortname, val in list(globals().items()):
            if is_function(val) and is_external(val.__module__):
                functions.add((val.__module__, shortname))    

        return {
            'packages' : list(packages), 
            'imports' : list(imports), 
            'functions' : list(functions)
        }

    
    def _get_test_cases(self):
        # Get all function imports 
        test_cases = {}
        for shortname, val in list(globals().items()):
            if is_function(val) and not is_external(val.__module__) and 'penngrader' not in val.__module__:
                test_cases[shortname] = val  
        return test_cases

    
    def _serialize(self, obj):
        '''Dill serializes Python object into a UTF-8 string'''
        byte_serialized = dill.dumps(obj, recurse = True)
        return base64.b64encode(byte_serialized).decode("utf-8")

    
    def _deserialize(self, obj):
        byte_decoded = base64.b64decode(obj)
        return dill.loads(byte_decoded)