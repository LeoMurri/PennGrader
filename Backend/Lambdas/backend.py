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
        homework_id, secret_key, request_type, payload = parse_event(event)
        validate_secret_key(homework_id, secret_key)
        if request_type == 'credentials':
            return build_http_response(SUCCESS, '')
        if request_type ==  'tests':
            libraries = get_additional_libraries(payload['libraries'])
            test_cases = payload['test_cases']
            upload_tests(homework_id, test_cases, libraries)
            return build_http_response(SUCCESS, 'Success: Test cases updated successfully.')
    except Exception as exception:
        return build_http_response(ERROR, exception)
        

def parse_event(event):
    try:
        body = ast.literal_eval(event['body'])
        return body['homework_id'],  \
               body['secret_key'], body['request_type'],  \
               deserialize(body['payload']) 
    except:
        raise Exception('Malformed payload.')
        
        
def validate_secret_key(homework_id, secret_key):
    if not secret_key == get_secret_key(homework_id):
        raise Exception('Secret key is incorrect.')


def get_additional_libraries(libraries): # TO-FINISH #
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
        error_message += 'Restart Jupyter runtime to clear imported modules.'
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
        
    
def get_secret_key(homework_id):
    try:
        response = dynamo.get_item(TableName = HOMEWORKS_TABLE, Key={'homework_id': {'S': homework_id}})
        return response['Item']['secret_key']['S']
    except:
        raise Exception('Homework ID was not found.')


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
    
    
    
    
#s3 = boto3.client('s3')
# def install_libraries(libraries):
    # os.system('rm -r /tmp/*')
    # print(os.system('mkdir /tmp/additional_libs'))

    # for package, nickname in libraries:

    #     print("Trying to install library: " + package)
    #     print(os.system('du -sh /tmp'))
    #     os.system('pip install ' + package +  ' -t /tmp/additional_libs/')
        
    # shutil.make_archive("/tmp/" + 'libs' , 'zip', '/tmp/additional_libs/')
    # s3.upload_file('/tmp/' + 'libs' + '.zip','penngrader-libraries',  'libs.zip')
