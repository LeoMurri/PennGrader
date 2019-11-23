import json
import urllib.request
import dill
import base64

api_endpoint = 'https://d9w676u8n0.execute-api.us-east-1.amazonaws.com/default/PennGrader'
    
class PennGrader:
    
    def __init__(self, student_id, homework_id = 'CIS545_Fall19_HW5'):
        if student_id == None:
            print('Error Autograder Not Setup: Enter your 8 digit PennID in the cell above.') 
        self.student_id         = str(student_id)
        self.api_endpoint       = api_endpoint
        self.class_homework_id  = homework_id 
        
    def grade(self, test_case_id, answer):
        student_test_case_id = self.student_id + '_' + test_case_id
        payload = {'student_test_case_id'   : student_test_case_id,
                   'class_homework_id'      : self.class_homework_id,
                   'test_case_id'           : test_case_id,
                   'answer'                 : self.serialize(answer)}
        params = json.dumps(payload).encode('utf-8')
        request = urllib.request.Request(self.api_endpoint, 
                                         data    = params, 
                                         headers = {'content-type': 'application/json'})
        try:
            response = urllib.request.urlopen(request)
            response_body = response.read().decode('utf-8')
            print('{}'.format(response_body))
        except:
            print('Error: Grading request could not be completed.')

    def serialize(self, obj):
        byte_serialized = dill.dumps(obj)
        return base64.b64encode(byte_serialized).decode("utf-8")

    def deserialize(self, obj):
        byte_decoded = base64.b64decode(obj)
        return dill.loads(byte_decoded)

grader = PennGrader(student_id = STUDENT_PENN_ID, homework_id = 'CIS545_Fall19_HW5') 