class MockPennGrader: 

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

grader = MockPennGrader()

# Example for test case 1.1
grader.grade(test_case_id = '1.1', answer = ('disnuts'))