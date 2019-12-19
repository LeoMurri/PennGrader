import json
import urllib.request
import dill
import base64
import types
from urllib.error import HTTPError
import ast
import types
import pandas as pd 

# Lambda endpoints
grader_api_url = 'https://wyv616tp17.execute-api.us-east-1.amazonaws.com/default/Grader'
grader_api_key = 'Kd32fl3g3p917iM0zwjiO23Bitj4PO9ga4LektOa'
grades_api_url = 'https://1rwoprdby6.execute-api.us-east-1.amazonaws.com/default/Grades'
grades_api_key = 'lY1O5NDRML9zEyRvWhf0c1GeEYFe3BE710Olbh3R'

# Request types
STUDENT_GRADE_REQUEST = 'STUDENT_GRADE'


class PennGrader:
    def __init__(self, homework_id, student_id):
        if '_' in str(student_id):
            raise Exception("Student ID cannot contain '_'")
        self.homework_id = homework_id
        self.student_id = str(student_id)

        
    def grade(self, test_case_id, answer):
        request = { 
            'homework_id' : self.homework_id, 
            'student_id' : self.student_id, 
            'test_case_id' : test_case_id,
            'answer' : self._serialize(answer)
        }
        response = self._send_request(request, grader_api_url, grader_api_key)
        print(response)
    
    
    def view_score(self):
        request = { 
            'homework_id' : self.homework_id, 
            'student_id' : self.student_id, 
            'request_type' : STUDENT_GRADE_REQUEST,
        }
        response = self._send_request(request, grades_api_url, grades_api_key)
        if 'Error' in response:
            print(response)
            return None
        else:
            grades, deadline, max_daily_submissions, max_score = self._deserialize(response)
            grades_df = pd.DataFrame(grades)
            
            # Extract student ID from [student_submission_id]
            grades_df['student_id'] = grades_df['student_submission_id'].apply(lambda x: str(x).split('_')[0])
            grades_df['test_case_id'] = grades_df['student_submission_id'].apply(lambda x: '_'.join(str(x).split('_')[1:]))

            # Convert to correct types
            grades_df['student_score'] = grades_df['student_score'].astype(int)
            
            display(grades_df[['student_id', 'test_case_id', 'student_score','max_score']])
            print('Total Score: {}/{}'.format(grades_df['student_score'].sum(), max_score))
            print('Deadline: {}'.format(deadline))
            print('Max daily submission per test case: {}'.format(max_daily_submissions))
            print('\nRemember: If you run any test case after the deadline your homework will be marked late.')
            print('\nAlso, make sure your student ID is correct.')
            print('\nAlso, you are a star!')

    
    def _send_request(self, request, api_url, api_key):
        params = json.dumps(request).encode('utf-8')
        headers = {'content-type': 'application/json', 'x-api-key': api_key}
        request = urllib.request.Request(api_url, data=params, headers=headers)
        try:
            response = urllib.request.urlopen(request)
            return '{}'.format(response.read().decode('utf-8'))
        except HTTPError as error:
            return 'Error: {}'.format(error.read().decode("utf-8")) 
        

    def _serialize(self, obj):
        byte_serialized = dill.dumps(obj, recurse = True)
        return base64.b64encode(byte_serialized).decode("utf-8")
    
    
    def _deserialize(self, obj):
        byte_decoded = base64.b64decode(obj)
        return dill.loads(byte_decoded)