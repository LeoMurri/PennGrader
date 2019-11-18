import boto3
import json
import dill
import base64
import time
import uuid 
import ast

ERROR        = 400
SUCCESS      = 200
IS_EXCEPTION = True

# Dynamo connection
dynamo = boto3.client('dynamodb')
DYNAMO_TABLE = 'GallantGrader_CIS545'

def lambda_handler(payload, context):
    log('Beginning new lambda event [{}]..'.format(time.strftime('%Y-%m-%d %H:%M:%s')))
    try:
        print("Reading payload...")
        student_id, homework_id, test_cases_id, answer = read_payload(payload)
        print("Grading question...")
        student_score, max_score = grade_answer(test_cases_id, answer)
        store_submission(student_id, homework_id, test_cases_id, student_score)
        return build_http_response(SUCCESS, build_response_message(int(student_score), max_score))
    except Exception as exception:
        error_message = 'Grading could not be completed. Message:\n{}'.format(exception)
        log(error_message, IS_EXCEPTION)
        return build_http_response(ERROR, error_message)

def read_payload(payload):
    try:
        log('Payload body: {}'.format(payload['body']))
        body = ast.literal_eval(payload['body'])
        student_id   = body['student_key']
        homework_id  = body['homework_id']
        test_case_id = body['test_case_id']
        answer       = deserialize_payload(body['answer'])
        return student_id, homework_id, test_case_id, answer
    except Exception as exception:
        log(exception, IS_EXCEPTION)
        raise Exception('Your answer could not be unpacked. Most likely you are passing the wrong thing.')

def grade_answer(test_case_id, answer):
    if test_case_id not in test_cases:
        raise Exception('Test case with ID {} does not exists.'.format(test_case_id))
    try:
        return test_cases[test_case_id](answer) # Return tuple: (score,max_score)
    except Exception as exception:
        log(exception, IS_EXCEPTION)
        raise Exception('''We tried to run your answer, however it crashed :(\nMake sure your answer is/behaves as instructed. Here is exactly why it crashed if it helps: {}.'''.format(exception))

def store_submission(student_id, homework_id, test_case_id, student_score):
    print("Storing score...")
    try:
        db_entry = {
            'TableName' : DYNAMO_TABLE,
            'Item' : { 
                'student_id'     : { 'S' : student_id },
                'hw_question_id' : { 'S' : homework_id + '_' + test_case_id},
                'score'          : { 'N' : str(student_score) },
                'timestamp'      : { 'S' : str(time.strftime('%Y-%m-%d %H:%M:%s'))}
            }
        }
        log(db_entry)
        dynamo.put_item(**db_entry)
    except Exception as exception:
        log(exception, IS_EXCEPTION)
        raise Exception('''Uhh no, we scored your answer, but we could not record it in the gradebook for some reason :(\nIt is not your fault, please try again or ask a TA.'''.format(student_score))


def build_response_message(student_score, max_score):
    if student_score == max_score:
        return '''Correct! You earned {}/{} points. You are a star!\n\nYour submission has been succesfully recorded in the gradebook.
               '''.format(student_score, max_score)
    else:
        return '''You earned {}/{} points.\n\nBut, don't worry you can re-submit and we will keep only your latest score.
               '''.format(student_score, max_score)

def build_http_response(status_code, body):
    return { 
        'statusCode' : status_code, 
        'body'       : body, 
        'headers'    : {'Content-Type': 'application/json'}
    }

def deserialize_payload(obj):
    byte_decoded = base64.b64decode(obj)
    return dill.loads(byte_decoded)

def log(message, exception = False):
    if not exception:
        print('Log: {}'.format(message))
    else:
        print('Exception: {}'.format(message))
