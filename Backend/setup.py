import boto3
import json

dynamo = boto3.client('dynamodb')

SUCCESS = 200
ERROR = 400
TESTCASES_TABLE = 'PennGraderTestCases'

def lambda_handler(payload, context):
    print(payload['body'])
    return build_http_response(SUCCESS , "+OK")
    
def build_http_response(status_code, body):
    return {
        'statusCode': status_code,
        'body': body,
        'headers': {'Content-Type': 'application/json'}
    }
    
def deserialize(obj):
    # Add dill library to path
    sys.path.append('./Libs/')
    import dill
    
    byte_decoded = base64.b64decode(obj)
    return dill.loads(byte_decoded)
