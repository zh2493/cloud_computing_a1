import json
import boto3
from boto3.dynamodb.conditions import Key
import requests
from requests.auth import HTTPBasicAuth 

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('yelp-restaurants')
fn = getattr(requests, 'post')


def send(url, body=None):
    fn(url, data=body,
       headers={"Content-Type": "application/json"})

def putRequests():
    resp = table.scan()
    i = 1
    url = 'https://search-assigment1lh-p27bvhr4o5kezzynj54fuucowm.us-east-1.es.amazonaws.com/restaurants/Restaurant'
    headers = {"Content-Type": "application/json"}
    while True:
        #print(len(resp['Items']))
        for item in resp['Items']:
            body = {"RestaurantID": item['insertedAtTimestamp'], "Cuisine": item['cuisine']}
            r = requests.post(url, data=json.dumps(body).encode("utf-8"), headers=headers,auth=HTTPBasicAuth("lh","#Sl5009zh2493"))
            #print(r)  
            i += 1
            #break;
        if 'LastEvaluatedKey' in resp:
            resp = table.scan(
                ExclusiveStartKey=resp['LastEvaluatedKey']
            )
            #break;
        else:
            break;
    print(i)

def lambda_handler(event, context):
    # TODO implement
    putRequests()
    # scrape()
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
    
# import requests
# from requests.auth import HTTPBasicAuth elastic_headers = {"Content-Type": "application/json"} es_response = requests.get(<opensearch_domain>, headers=elastic_headers, data=json.dumps(search_query),auth=HTTPBasicAuth(<username>,<password>))
