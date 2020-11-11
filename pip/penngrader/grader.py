import urllib.request
from urllib.error import HTTPError
import json
import dill
import base64
import types
import ast

# Lambda endpoints
grader_api_url = 'https://wyv616tp17.execute-api.us-east-1.amazonaws.com/default/Grader'
grader_api_key = 'Kd32fl3g3p917iM0zwjiO23Bitj4PO9ga4LektOa'

# Request types
STUDENT_GRADE_REQUEST = 'STUDENT_GRADE'

class PennGrader:
    """ The grader is responsible for the actual testing. This is what the student will use
    to test their code
    """
    
    def __init__(self, homework_id, student_id):
        """ Initialization function to start up the grader instance
        """
        if '_' in str(student_id):
            raise Exception("Student ID cannot contain '_'")
        self.homework_id = homework_id
        self.student_id = str(student_id)
        print('PennGrader initialized with Student ID: {}'.format(self.student_id))
        print('\nMake sure this correct or we will not be able to store your grade')

        
    def grade(self, test_case_id, answer):
        """ This function will hit the grader_lambda to test a student's function
        """
        request = { 
            'homework_id' : self.homework_id, 
            'student_id' : self.student_id, 
            'test_case_id' : test_case_id,
            'answer' : self._serialize(answer)
        }
        response = self._send_request(request, grader_api_url, grader_api_key)
        print(response)

    def _send_request(self, request, api_url, api_key):
        """ Function to send requests, regardless of type
        """
        params = json.dumps(request).encode('utf-8')
        headers = {'content-type': 'application/json', 'x-api-key': api_key}
        request = urllib.request.Request(api_url, data=params, headers=headers)
        try:
            response = urllib.request.urlopen(request)
            return '{}'.format(response.read().decode('utf-8'))
        except HTTPError as error:
            return 'Error: {}'.format(error.read().decode("utf-8")) 
        
    def _serialize(self, obj):
        """ Encodes an object to UTF-8
        """
        byte_serialized = dill.dumps(obj, recurse = True)
        return base64.b64encode(byte_serialized).decode("utf-8")