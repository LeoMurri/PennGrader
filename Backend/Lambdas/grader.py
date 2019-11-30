import sys
sys.path.append('/opt')
import os
import boto3
import json
import dill
import ast
import base64
import shutil

dynamo = boto3.client('dynamodb')

HOMEWORKS_TABLE = 'Homeworks'
TESTCASES_TABLE = 'TestCases'

SUCCESS, ERROR = 200, 400

def lambda_handler(event, context):
    try:
        print('here')
        homework_id, student_id, test_case_id, answer = parse_event(event)
        test_case, libraries = get_test_and_libraries(homework_id, test_case_id)
        import_libraries(libraries)
        student_score, max_score = test_case(answer)
        return build_http_response(SUCCESS, build_response_message(student_score, max_score))
    except Exception as exception:
        return build_http_response(ERROR, exception)
        

def parse_event(event):
    try:
        body = ast.literal_eval(event['body'])
        return body['homework_id'],  \
               body['student_id'], \
               body['test_case_id'],  \
               deserialize(body['answer']) 
    except:
        raise Exception('Malformed payload.')

def get_test_and_libraries(homework_id, test_case_id):
    try:
        response = dynamo.get_item(TableName = TESTCASES_TABLE, Key={'homework_id': {'S': homework_id}})
        return deserialize(response['Item']['test_cases']['S'])[test_case_id], \
               deserialize(response['Item']['libraries']['S']), 
    except:
        raise Exception('Test case {} was not found.'.format(test_case_id))


def import_libraries(libraries): 
    try: 
        for package, shortname, function_name in libraries:
            if package not in globals() and not function_name:
                globals()[shortname] = __import__(package, globals(), locals(), ['*'])
        for package, shortname, function_name in libraries:
            if package not in globals() and function_name:
                globals()[function_name] = eval(package + "." + function_name)
        return libraries
    except Exception as exception:
        error_message = '[{}] is not currently supported. '.format(str(exception).split("'")[1])
        error_message += 'Let a TA know you got this error.'
        raise Exception(error_message)


def grade(test_case, answer):
    try:
        return test_case(answer)
    except Exception as exception:
        error_message = 'Your answer could not be graded because it does not match the expected type or behaviour.'
        error_message += '\nException: ' + str(exception)
        raise Exception(error_message)
     
        
def upload_tests(homework_id, test_cases, libraries):
    try:
        db_entry = {
            'TableName': TESTCASES_TABLE,
            'Item': {
                'homework_id': {'S': homework_id},
                'test_cases': {'S': serialize(test_cases)},
                'libraries' : {'S' : serialize(libraries)}
            }
        }
        dynamo.put_item(**db_entry)
    except Exception as exception:
        raise Exception('Test cases upload failed. Try again in a bit or ask an admin.')  

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

def serialize(obj):
    byte_serialized = dill.dumps(obj, recurse = True)
    return base64.b64encode(byte_serialized).decode("utf-8") 
    

def deserialize(obj):
    byte_decoded = base64.b64decode(obj)
    return dill.loads(byte_decoded)
    
def build_response_message(student_score, max_score):
    if student_score == max_score:
        return 'Correct! You earned {}/{} points. You are a star!\n\n'.format(student_score, max_score) + \
               'Your submission has been successfully recorded in the gradebook.'
    else:
        return 'You earned {}/{} points.\n\n'.format(student_score, max_score) + \
               'But, don\'t worry you can re-submit and we will keep only your latest score.'

def build_http_response(status_code, message):
    return { 
        'statusCode': status_code,
        'body': str(message),
        'headers': {
            'Content-Type': 'application/json',
        }
    }
    
    
    
  