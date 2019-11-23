import boto3
import base64
import time
import ast
import sys

sys.path.append('./Libs/')
dynamo = boto3.client('dynamodb')

SUCCESS = 200
ERROR = 400
GRADEBOOK_TABLE = 'PennGradebook'
CHEATING_TABLE = 'PennCheaters'
ADDITIONAL_LIBS_PATH = './Additional_Libs/'


def lambda_handler(payload, context):
    log('*** Beginning new lambda grading event [{}].'.format(time.strftime('%Y-%m-%d %H:%M:%s')))
    try:
        # Deserialize JSON string payload into a Submission object
        submission = Submission(payload)

        # Download test specific libraries
        download_libraries(submission.homework_id)

        # Download the test case function code
        test_case_function = download_test_case(submission.homework_id, submission.test_case_id)

        # Grade submission
        score = grade(test_case_function, submission.answer)

        # Store score in PennGradebook DynamoDB table
        store_submission(submission, score)

        # Store answer in PennCheaters DynamoDB table
        # TODO

        # Create response
        return build_http_response(SUCCESS, build_response_message(score))

    except Exception as exception:
        error_message = 'Grading could not be completed.\nError Message: {}'.format(exception)
        log(error_message)
        return build_http_response(ERROR, error_message)


class Submission:
    def __init__(self, payload):
        self.homework_id, self.student_id, self.test_case_id, self.answer = deserialize_payload(payload)


class Score:
    def __init__(self, student_score, max_score):
        self.student_score = student_score
        self.max_score = max_score


def deserialize_payload(payload):
    # Inputs : (payload : str)
    # Outputs: (homework_id : str) (student_id : str) (test_case_id : str) (answer : _)
    # Description: This function takes in a string representing the JSON payload received
    # and parses and deserialize it. Finally returns all associated submission parameters.
    # On failure it throws an exception.
    try:
        log('*** Payload body: {}'.format(payload['body']))
        # body = ast.literal_eval(payload['body'])
        body = payload['body']
        return body['homework_id'], body['student_id'], body['test_case_id'], deserialize(body['answer'])
    except Exception as exception:
        log(exception)
        raise Exception('Your answer could not be deserialized.')


def download_libraries(homework_id):
    # raise Exception('Test case with ID {} does not exists.'.format(test_case_id))
    return None


def download_test_case(homework_id, test_case_id):
    # raise Exception('Test case with ID {} does not exists.'.format(test_case_id))
    return lambda x: (5, 5)


def grade(test_case, answer):
    # Inputs: (test_case : function) (answer : _ )
    # Outputs: ((student_score, max_score) : (int, int))
    # Description: This function takes in the test case function and the student answer
    # and returns a tuple representing the student's score on the given test case. On
    # failure it throws an exception.
    try:
        return test_case(answer)
    except Exception as exception:
        log(exception)
        error_message = 'We tried to run your answer, however it crashed :(\n' + \
                        'Make sure your answer is of the right type and behaves as instructed.\n' + \
                        'Here is exactly why it crashed if it helps: {}.'''.format(exception)
        raise Exception(error_message)


def store_submission(submission, score):
    print("Storing score...")
    try:
        db_entry = {
            'TableName': GRADEBOOK_TABLE,
            'Item': {
                'homework_id': {'S': submission.homework_id},
                'student_submission_id': {'S': submission.student_id + '_' + submission.test_case_id},
                'student_score': {'N': str(score.student_score)},
                'max_score': {'N': str(score.max_score)},
                'timestamp': {'S': str(time.strftime('%Y-%m-%d %H:%M:%s'))}
            }
        }
        log(db_entry)
        dynamo.put_item(**db_entry)
    except Exception as exception:
        log(exception)
        error_message = 'Uhh no! We could not record your answer in the gradebook for some reason :(\n' + \
                        'It is not your fault, please try again or ask a TA.'
        raise Exception(error_message)


def deserialize(obj):
    # Add dill library to path
    sys.path.append('./Libs/')
    import dill

    # Deserialize string
    byte_decoded = base64.b64decode(obj)
    return dill.loads(byte_decoded)


def build_response_message(score):
    if score.student_score == score.max_score:
        return 'Correct! You earned {}/{} points. You are a star!\n\n'.format(score.student_score, score.max_score) + \
               'Your submission has been successfully recorded in the gradebook.'
    else:
        return 'You earned {}/{} points.\n\n'.format(score.student_score, score.max_score) + \
               'But, don\'t worry you can re-submit and we will keep only your latest score.'


def build_http_response(status_code, body):
    return {
        'statusCode': status_code,
        'body': body,
        'headers': {'Content-Type': 'application/json'}
    }


def log(message):
    print(message)
