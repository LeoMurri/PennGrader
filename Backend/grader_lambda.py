"""
    The grader_lambda is the AWS lambda class that will handle test-related events. Its primary responsibility
    is to take in an event, parse out key details, such as which homework it's relevant to, which student,
    which test case, etc., then handle the actual testing.

    The basic flow is:

    event happens   =>  lambda_handler is invoked   =>  dynamo DB is updated w/ submission & score
                        > Examine event
                        > Get submission details
                        > Import any libraries
                        > Test submission
                        > Log the resulting score
"""



import sys
sys.path.append('/opt')
import os
import boto3
import json
import dill
import ast
import base64
import shutil
import time

# Dynamo Config
dynamo = boto3.client('dynamodb')
METADATA_TABLE   = 'HomeworksMetadata'
TEST_CASES_TABLE = 'HomeworksTestCases'
GRADEBOOK_TABLE  = 'Gradebook'

# Return Codes
SUCCESS = 200
ERROR   = 400


def lambda_handler(event, context):
    """ This lambda handler is meant to take in an event and context, then:

        1. Parse out the test details: homework_id, student_id, test_case_id, answer
        2. Get all of the associated libraries and the test function: test_case, libraries
        3. Import those required libraries
        4. Score the students work against the test_case: student_score, max_score
        5. Log the submission in dynamo
    """
    try:
        homework_id, student_id, test_case_id, answer = parse_event(event)
        test_case, libraries = get_test_and_libraries(homework_id, test_case_id)
        import_libraries(libraries)
        student_score, max_score = grade(test_case, answer)
        store_submission(student_score, max_score, homework_id, test_case_id, student_id)
        return build_http_response(SUCCESS, build_response_message(student_score, max_score))
    except Exception as exception:
        return build_http_response(ERROR, exception)
        

def parse_event(event):
    """ Simple helper method to parse an event as a dict.
    Returns: (homework_id, student_id, test_case_id, answer)
    """
    try:
        body = ast.literal_eval(event['body'])
        return body['homework_id'],  \
               body['student_id'], \
               body['test_case_id'],  \
               deserialize(body['answer']) 
    except:
        raise Exception('Malformed payload.')


def get_test_and_libraries(homework_id, test_case_id):
    """ Retrieve the test function and associated libraries required. This pulls down from dynamo,
    then passes back a tuple of (test_case, libraries). It can then be used to import the libraries
    and test the student submission
    """
    try:
        response = dynamo.get_item(TableName = TEST_CASES_TABLE, Key={'homework_id': {'S': homework_id}})
        return deserialize(response['Item']['test_cases']['S'])[test_case_id], \
               deserialize(response['Item']['libraries']['S']), 
    except:
        raise Exception('Test case {} was not found.'.format(test_case_id))


def import_libraries(libraries): # TO-FINISH #
    """ Apparently unfinished, but imports required libraries for a given test. Tests consist of
    the function that actually performs the testing and the required libraries to run that function +
    the function being tested. This takes care of importing those libraries
    """
    try:
        packages = libraries['packages']
        imports = libraries['imports']
        functions = libraries['functions']
        
        for package in packages:
            if package not in globals() and 'penngrader' not in package:
                print('Importing base package: ' + package)
                globals()[package] = __import__(package, globals(), locals(), ['*'])
        
        for package, shortname in imports:
            if shortname not in globals() and 'penngrader' not in package:
                print('Importing: ' + package + ' as ' + shortname)
                globals()[shortname] = __import__(package, globals(), locals(), ['*'])
        
        for package, function_name in functions:
            print('Importing function: ' + function_name + ' from ' + package)
            globals()[function_name] = eval(package + "." + function_name)
    except Exception as exception:
        error_message = '[{}] is not currently supported. '.format(str(exception).split("'")[1])
        error_message += 'Let a TA know you got this error.'
        raise Exception(error_message)


def grade(test_case, answer):
    """ Generate a grade for a given test case. test_case is a function that is passed in. The function
    gets executed here using answer as its param. This will catch any errors in the code and returns
    a tuple of (score, max_score)
    """
    try:
        return test_case(answer) 
    except Exception as exception:
        error_message = 'Test case failed. Test case function could not complete due to an error in your answer.\n'
        error_message += 'Error Hint: {}'.format(exception)
        raise Exception(error_message)
        
        
def store_submission(student_score, max_score, homework_id, test_case_id, student_id):
    """ Log the student submission in the database.
            params:
                - student_score:    the number of points the student received on a problem
                - max_score:        the maximum score on that problem
                - homeword_id:      the key for this particular homework
                - test_case_id:     the key for this particular test case (problem)
                - student_id:       the key for the student

        This will be passed to the dynamo DB as a new record
    """
    try:
        db_entry = {
            'TableName': GRADEBOOK_TABLE,
            'Item': {
                'homework_id': {
                    'S': homework_id
                },
                'student_submission_id': {
                    'S': student_id + '_' + test_case_id
                },
                'student_score': {
                    'S': str(student_score)
                },
                'max_score': {
                    'S': str(max_score)
                },
                'timestamp': {
                    'S': str(time.strftime('%Y-%m-%d %H:%M'))
                }
            }
        }
        dynamo.put_item(**db_entry)
    except Exception as exception:
        error_message = 'Uhh no! We could not record your answer in the gradebook for some reason :(\n' + \
                        'It is not your fault, please try again or ask a TA.'
        raise Exception(error_message)


def serialize(obj):
    """ Simple helper method to encode a serialized object
    """
    byte_serialized = dill.dumps(obj, recurse = True)
    return base64.b64encode(byte_serialized).decode("utf-8") 
    

def deserialize(obj):
    """ Simple helper method to decode a base64 encoded object
    """
    byte_decoded = base64.b64decode(obj)
    return dill.loads(byte_decoded)
    
    
def build_response_message(student_score, max_score, msg=None):
    """ Build the string response message
    """
    out = ""
    if student_score == max_score:
        out = 'Correct! You earned {}/{} points. You are a star!\n\n'.format(student_score, max_score) + \
               'Your submission has been successfully recorded in the gradebook.'
    else:
        out = 'You earned {}/{} points.\n\n'.format(student_score, max_score) + \
               'But, don\'t worry you can re-submit and we will keep only your latest score.'
    if msg is not None:
        out += "\n\n{}".format(msg)
    return out


def build_http_response(status_code, message):
    """ Build formatted http response as string
    """
    return { 
        'statusCode': status_code,
        'body': str(message),
        'headers': {
            'Content-Type': 'application/json',
        }
    }
    
    
    
  