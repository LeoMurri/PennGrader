import json
import urllib.request
import dill
import base64
import types
from urllib.error import HTTPError
import ast
import types

api_url = 'https://wyv616tp17.execute-api.us-east-1.amazonaws.com/default/Grader'
api_key = 'Kd32fl3g3p917iM0zwjiO23Bitj4PO9ga4LektOa'


class PennGrader:
    
    def __init__(self, homework_id, student_id):
        self.homework_id = homework_id
        self.student_id = student_id

    def grade(self, test_case_id, answer):
        payload = { 
            'homework_id' : self.homework_id, 
            'student_id' : self.student_id, 
            'test_case_id' : test_case_id,
            'answer' : self.serialize(answer)
        }
        self.send_payload(payload, api_url, api_key)
    
    def get_total_score(self):
        pass
    
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

    def serialize(self, obj):
        '''Dill serializes Python object into a UTF-8 string'''
        byte_serialized = dill.dumps(obj, recurse = True)
        return base64.b64encode(byte_serialized).decode("utf-8")