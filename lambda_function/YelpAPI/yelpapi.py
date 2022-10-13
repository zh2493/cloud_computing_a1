import requests
import json
# import boto3
# import datetime
# import json
# from botocore.vendored import requests
# from decimal import *
# from elasticSearch import putRequests
# from time import sleep
# from urlparse import urljoin

api_key='9-v42ATZ30KIS-opQ6qTDk4X96ioZZJ2f4CCBn8fwdJ0hEHsLvqNnVuifq5iKdTeEGlwj0chuqRNf9zCh8hbEH3gWCBGZvtt8oHZAVH3S6KCtuFUuR0RExCo-x5DY3Yx'
headers = {'Authorization': 'Bearer %s' % api_key}


url='https://api.yelp.com/v3/businesses/search'
 
# In the dictionary, term can take values like food, cafes or businesses like McDonalds

params = {'term':'japanese restaurant','location': 'Manhattan', "categories": [{"alias": "japanese","title": "Japanese"}], 'limit': 50, 'sort_by': 'rating'}


# Making a get request to the API
req=requests.get(url, params=params, headers=headers)
 
# proceed only if the status code is 200
print('The status code is {}'.format(req.status_code))

# printing the text from the response 
# print(json.loads(req.text))

print(req.json())

