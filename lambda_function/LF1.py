import json
import datetime
import time
import os
import dateutil.parser
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


# --- Helpers that build all of the responses ---


def elicit_slot(session_attributes, active_contexts, intent, slot_to_elicit, message):
    return {
        'sessionState': {
            'activeContexts':[{
                'name': 'intentContext',
                'contextAttributes': active_contexts,
                'timeToLive': {
                    'timeToLiveInSeconds': 600,
                    'turnsToLive': 1
                }
            }],
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'ElicitSlot',
                'slotToElicit': slot_to_elicit
            },
            'intent': intent,
        }
    }


def confirm_intent(active_contexts, session_attributes, intent, message):
    return {
        'sessionState': {
            'activeContexts': [active_contexts],
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'ConfirmIntent'
            },
            'intent': intent
        }
    }


def close(session_attributes, active_contexts, fulfillment_state, intent, message):
    response = {
        'sessionState': {
            'activeContexts':[{
                'name': 'intentContext',
                'contextAttributes': active_contexts,
                'timeToLive': {
                    'timeToLiveInSeconds': 600,
                    'turnsToLive': 1
                }
            }],
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'Close',
            },
            'intent': intent,
        },
        'messages': [{'contentType': 'PlainText', 'content': message}]
    }

    return response


def delegate(session_attributes, active_contexts, intent, message):
    return {
        'sessionState': {
            'activeContexts':[{
                'name': 'intentContext',
                'contextAttributes': active_contexts,
                'timeToLive': {
                    'timeToLiveInSeconds': 600,
                    'turnsToLive': 1
                }
            }],
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'Delegate',
            },
            'intent': intent,
        },
        'messages': [{'contentType': 'PlainText', 'content': message}]
    }


def initial_message(intent_name):
    response = {
            'sessionState': {
                'dialogAction': {
                    'type': 'ElicitSlot',
                    'slotToElicit': 'Location' if intent_name=='BookHotel' else 'PickUpCity'
                },
                'intent': {
                    'confirmationState': 'None',
                    'name': intent_name,
                    'state': 'InProgress'
                }
            }
    }
    
    return response

# --- Helper Functions ---


def safe_int(n):
    """
    Safely convert n value to int.
    """
    if n is not None:
        return int(n)
    return n


def try_ex(value):
    """
    Call passed in function in try block. If KeyError is encountered return None.
    This function is intended to be used to safely access dictionary of the Slots section in the payloads.
    Note that this function would have negative impact on performance.
    """

    if value is not None:
        return value['value']['interpretedValue']
    else:
        return None
        
        
# --------------------- Validation driver function ---------------------

def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }

# --------------------- Validation functions for each slot ---------------------

def isvalid_location(location):
    locations = ['queens', 'manhattan']
    if not location:
        return build_validation_result(False,
                               'Location',
                               '')
    if location.lower() not in locations:
        return build_validation_result(False,
                                       'Location',
                                       'Please enter a right location')
    return build_validation_result(True,'','')

def isvalid_cuisine(cuisine):
    if not cuisine :
        return build_validation_result(False,
                                       'Cuisine',
                                       '')
    cuisines = cuisines = ['italian', 'chinese', 'indian', 'american', 'mexican', 'spanish', 'greek', 'latin', 'Persian']
    if cuisine.lower() not in cuisines:
        return build_validation_result(False,
                                       'Cuisine',
                                       'This cuisine is not available')
    print("Debug: cuisine is: ",cuisine)
    return build_validation_result(True,'','')
    
def isvalid_time(time):
    print("Debug: time is:",time)
    if not time:
        return build_validation_result(False,'DiningTime','')
    if time:
        return build_validation_result(True,'','')
    return build_validation_result(False,'DiningTime','Please enter a valid Dining Time')

def isvalid_people(num_people):
    if not num_people:
         return build_validation_result(False,'people','')
    num_people = int(num_people)
    if num_people > 50 or num_people < 1:
        return build_validation_result(False,
                                  'people',
                                  'Range of 1 to 50 people allowed')
    return build_validation_result(True,'','')

def isvalid_phonenum(phone_num):
    if not phone_num:
        return build_validation_result(False, 'phone', '')
    if len(phone_num)!= 10 and (phone_num.startswith('+1') is False and len(phone_num) != 12):
        return build_validation_result(False, 'phone', 'Phone Number must be in form +1xxxxxxxxxx or a 10 digit number')
    elif len(phone_num) == 10 and (phone_num.startswith('+1') is True):
        return build_validation_result(False, 'phone', 'Phone Number must be in form +1xxxxxxxxxx or a 10 digit number')
    return build_validation_result(True,'','')


def validate_reservation(restaurant):
    
    location = restaurant['Location']
    cuisine = restaurant['Cuisine']
    diningtime = restaurant['DiningTime']
    numberpeople = restaurant['people']
    phonenumber = restaurant['phone']

    if not location or not isvalid_location(location)['isValid']:
        return isvalid_location(location)
    
    if not cuisine or not isvalid_cuisine(cuisine)['isValid']:
        return isvalid_cuisine(cuisine)
        
    if not diningtime or not isvalid_time(diningtime)['isValid']:
        return isvalid_time(diningtime)
        
    if not numberpeople or not isvalid_people(numberpeople)['isValid']:
        return isvalid_people(numberpeople)
        
    if not phonenumber or not isvalid_phonenum(phonenumber)['isValid']:
        return isvalid_phonenum(phonenumber)
        
    # return True json if nothing is wrong
    return build_validation_result(True,'','')


def restaurantSQSRequest(requestData):
    
    sqs = boto3.client('sqs')
    queue_url = 'https://sqs.us-east-1.amazonaws.com/257435202191/RestaurantQueue'
    delaySeconds = 5
    messageAttributes = {
        'cuisine': {
            'DataType': 'String',
            'StringValue': requestData['Cuisine']
        },
        'location': {
            'DataType': 'String',
            'StringValue': requestData['Location']
        },
        "time": {
            'DataType': "String",
            'StringValue': requestData['DiningTime']
        },
        'numPeople': {
            'DataType': 'Number',
            'StringValue': requestData['NumberPeople']
        },
        'phone': {
            'DataType' : 'String',
            'StringValue' : requestData['PhoneNumber']
        }
    }
    messageBody=('Recommendation for the food')
    
    response = sqs.send_message(
        QueueUrl = queue_url,
        DelaySeconds = delaySeconds,
        MessageAttributes = messageAttributes,
        MessageBody = messageBody
        )

    print("response", response)
    
    print ('send data to queue')
    print(response['MessageId'])
    
    return response['MessageId']

def make_restaurant_reservation(intent_request):
    """
    Performs dialog management and fulfillment for booking a hotel.
    Beyond fulfillment, the implementation for this intent demonstrates the following:
    1) Use of elicitSlot in slot validation and re-prompting
    2) Use of sessionAttributes to pass information that can be used to guide conversation
    """
    print("Debug: Entered make_restaurant_reservation" )
    location = try_ex(lambda: intent_request['sessionState']['intent']['slots']['Location'])
    print("Debug: Location is  ",location)
    cuisine = try_ex(lambda: intent_request['sessionState']['intent']['slots']['Cuisine'])
    diningtime = try_ex(lambda: intent_request['sessionState']['intent']['slots']['DiningTime'])
    numberpeople = try_ex(lambda: intent_request['sessionState']['intent']['slots']['people'])
    phonenumber = try_ex(lambda: intent_request['sessionState']['intent']['slots']['phone'])

    confirmation_status = intent_request['sessionState']['intent']['confirmationState']
    session_attributes = intent_request['sessionState'].get("sessionAttributes") or {}
    intent = intent_request['sessionState']['intent']
    active_contexts = {}

    logger.debug(confirmation_status)
    # Load confirmation history and track the current reservation.
    reservationJson = json.dumps({
        'Location': location,
        'Cuisine': cuisine,
        'DiningTime': diningtime,
        'people': numberpeople,
        'phone':phonenumber
    })
    reservation = json.loads(reservationJson)
    # session_attributes['currentReservation'] = reservation

    if intent_request['invocationSource'] == 'DialogCodeHook':
        # Validate any slots which have been specified.  If any are invalid, re-elicit for their value
        validation_result = validate_reservation(intent_request['sessionState']['intent']['slots'])
        print("Debug: Validation result is: ", validation_result)
        if not validation_result['isValid']:
            slots = intent_request['sessionState']['intent']['slots']
            slots[validation_result['violatedSlot']] = None
            print(elicit_slot(
                session_attributes,
                active_contexts,
                intent,
                validation_result['violatedSlot'],
                validation_result['message']
            ))
            return elicit_slot(
                session_attributes,
                active_contexts,
                intent,
                validation_result['violatedSlot'],
                validation_result['message']
            )

        # Otherwise, let native DM rules determine how to elicit for slots and prompt for confirmation.  Pass price
        # back in sessionAttributes once it can be calculated; otherwise clear any setting from sessionAttributes.
        output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}

        print("output_session_attributes", output_session_attributes)
        
        # return delegate(output_session_attributes, intent_request['currentIntent']['slots'])
      
    requestData = {
                    'Location': location,
                    'Cuisine': cuisine,
                    'DiningTime': diningtime,
                    'NumberPeople': numberpeople,
                    'PhoneNumber':phonenumber
                }
                
    # print (requestData)
    
    
    messageId = restaurantSQSRequest(requestData)
    print ("Debug: messageId:",messageId)

    return close(intent_request['sessionAttributes'],
                active_contexts,
                'Fulfilled',
                intent,
                {'contentType': 'PlainText',
                 'content': 'I have received your request and will be sending the suggestions shortly. Have a Great Day !!'})

# --- Intents ---


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug(intent_request)
    slots = intent_request['sessionState']['intent']['slots']
    
    intent_name = intent_request['sessionState']['intent']['name']

    logger.debug('dispatch sessionId={}, intentName={}'.format(intent_request['sessionId'], intent_request['sessionState']['intent']['name']))
    # Dispatch to your bot's intent handlers
    if intent_name == 'DiningSuggestIntent':
        return make_restaurant_reservation(intent_request)
    
    raise Exception('Intent with name ' + intent_name + ' not supported')


# --- Main handler ---


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    # logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)