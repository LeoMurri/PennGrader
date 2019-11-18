import json
import urllib.request

class PennGrader: 

    api_endpoint = 'https://q0gtldc2ck.execute-api.us-east-2.amazonaws.com/default/GalantGrader_v0'

    def __init__(self, student_grading_key, homework_key):
        self.student_grading_key = student_grading_key
        self.homework_key        = homework_key
        
    def grade(self, question_id, answer):
        payload = {'student_key'  : self.student_grading_key
                   'homework_id'  : self.homework_id,
                   'test_case_id' : question_id,
                   'answer'       : answer}

        params = json.dumps(payload).encode('utf-8')
        request = urllib.request.Request(self.api_endpoint, 
                                         data    = params, 
                                         headers = {'content-type': 'application/json'})
        try:
            response = urllib.request.urlopen(request)
            response_body = response.read().decode('utf-8')
            print('{}'.format(response_body))
        except:
            print('Error: Grading request could not be complete.')

    def total_score():
        # TODO #
        # Prints total homework score


class PennGraderMock: 

    def __init__(self):
        from tests import *
        
    def grade(self, test_case_id, answer):
        student_score, max_score = grade(test_case_id, answer)
        print(build_response_message(student_score, max_score))
    
    def build_response_message(student_score, max_score):
        if student_score == max_score:
            return '''Correct! You earned {}/{} points. You are a star!\n\nYour submission has been succesfully recorded in the gradebook.
                   '''.format(student_score, max_score)
        else:
            return '''You earned {}/{} points.\n\nBut, don't worry you can re-submit and we will keep only your latest score.
                   '''.format(student_score, max_score)





