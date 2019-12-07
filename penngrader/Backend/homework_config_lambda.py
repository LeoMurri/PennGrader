import sys
sys.path.append('/opt')
import os
import boto3
import json
import dill
import ast
import base64
import shutil
import pandas as pd

# Dynamo Config
dynamo = boto3.client('dynamodb')
CLASSES_TABLE    = 'Classes'
METADATA_TABLE   = 'HomeworksMetadata'
TEST_CASES_TABLE = 'HomeworksTestCases'

# Return Codes
SUCCESS = 200
ERROR   = 400

# Request types
HOMEWORK_ID_REQUEST     = 'GET_HOMEWORK_ID'
UPDATE_METADATA_REQUEST = 'UPDATE_METADATA'
UPDATE_TESTS_REQUEST    = 'UPDATE_TESTS'


def lambda_handler(event, context):
    try:
        homework_number, secret_key, request_type, payload = parse_event(event)
        secret_key  = get_course_id(secret_key)
        homework_id = get_homework_id(secret_key, homework_number)

        if request_type == HOMEWORK_ID_REQUEST:
            response = str(homework_id)
        elif request_type == UPDATE_METADATA_REQUEST:
            update_metadata(homework_id, payload)
            response  = 'Success! Metadata updated.\n\n'
            response += 'Total HW Points: {}\n'.format(payload['total_score'])
            response += 'Deadline: {}\n'.format(pd.to_datetime(payload['deadline']))
            response += 'Max daily submissions per test case: {}\n'.format(payload['max_daily_submissions'])
        elif request_type ==  UPDATE_TESTS_REQUEST:
            libraries = get_additional_libraries(payload['libraries'])
            test_cases = payload['test_cases'] 
            update_tests(homework_id, test_cases, libraries)
            response = 'Success: Test cases updated successfully.'
        return build_http_response(SUCCESS, response)
    except Exception as exception:
        return build_http_response(ERROR, exception)

def parse_event(event):
    try:
        body = ast.literal_eval(event['body'])
        return body['homework_number'],  \
               body['secret_key'], \
               body['request_type'],  \
               deserialize(body['payload']) 
    except:
        raise Exception('Malformed payload.')
        
        
def get_course_id(secret_key):
    try:
        response = dynamo.get_item(TableName = CLASSES_TABLE, Key={'secret_key': {'S': secret_key}})
        return response['Item']['course_id']['S']
    except:
        raise Exception('Secret key is incorrect.')


def get_homework_id(course_id, homework_number):
    return '{}_HW{}'.format(course_id, homework_number)


def update_metadata(homework_id, payload):
    try:
        db_entry = {
            'TableName': METADATA_TABLE,
            'Item': {
                'homework_id': {
                    'S': homework_id
                },
                'max_daily_submissions' : {
                    'S' : str(payload['max_daily_submissions'])
                },
                'total_score' : {
                    'S':str(payload['total_score'])
                    
                },
                'deadline' : {
                    'S':str(payload['deadline'])
                }
            }
        }
        dynamo.put_item(**db_entry)
    except Exception as exception:
        raise Exception('Metadata upload failed. Try again in a bit or ask an admin.')  


def update_tests(homework_id, test_cases, libraries):
    try:
        db_entry = {
            'TableName': TEST_CASES_TABLE,
            'Item': {
                'homework_id': {
                    'S': homework_id
                },
                'test_cases': {
                    'S': serialize(test_cases)
                },
                'libraries' : {
                    'S' : serialize(libraries)
                }
            }
        }
        dynamo.put_item(**db_entry)
    except Exception as exception:
        raise Exception('Test cases upload failed. Try again in a bit or ask an admin.')  


def get_additional_libraries(libraries): # TO-FINISH #
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
        error_message += 'Reset Jupyter runtime to clear imported modules.'
        raise Exception(error_message)
    return libraries


def serialize(obj):
    byte_serialized = dill.dumps(obj, recurse = True)
    return base64.b64encode(byte_serialized).decode("utf-8") 
    

def deserialize(obj):
    byte_decoded = base64.b64decode(obj)
    return dill.loads(byte_decoded)
    

def build_http_response(status_code, message):
    return { 
        'statusCode': status_code,
        'body': str(message),
        'headers': {
            'Content-Type': 'application/json',
        }
    }
    
    
# SAVING THIS HERE FOR LIBS FUNCTION, I SHALL GET TO IT SOON
# s3 = boto3.client('s3')
# def install_libraries(libraries):
#     os.system('rm -r /tmp/*')
#     print(os.system('mkdir /tmp/additional_libs'))
#     for package, nickname in libraries:
#         print(os.system('du -sh /tmp'))
#         os.system('pip install ' + package +  ' -t /tmp/additional_libs/')
#     shutil.make_archive("/tmp/" + 'libs' , 'zip', '/tmp/additional_libs/')
#     s3.upload_file('/tmp/' + 'libs' + '.zip','penngrader-libraries',  'libs.zip')
