import os, time
from dotenv import load_dotenv
from ibmcloudant.cloudant_v1 import CloudantV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core import ApiException

########################
# Setting Environment Variables and setting up services
load_dotenv() # This is used to enable loading environment variables from the
              # .env file
IBM_CLOUDANT_URL      = os.getenv('IBM_CLOUDANT_URL')
IBM_CLOUDANT_APIKEY   = os.getenv('IBM_CLOUDANT_APIKEY')
IBM_CLOUDANT_DATABASE = os.getenv('IBM_CLOUDANT_DATABASE')

authenticator = IAMAuthenticator(IBM_CLOUDANT_APIKEY)
service = CloudantV1(authenticator = authenticator)
service.set_service_url(IBM_CLOUDANT_URL)

def verify_document_exists(ID):
    try:
        all_docs = service.post_all_docs(
            db           = IBM_CLOUDANT_DATABASE,
            include_docs = False
        ).get_result()
        for doc in all_docs['rows']:
            if doc['id'] == ID:
                return True
        return False
    except ApiException as ae:
        print("DB Method failed")
        print(" - status code: " + str(ae.code))
        print(" - error message: " + ae.message)
        if ("reason" in ae.http_response.json()):
            print(" - reason: " + ae.http_response.json()["reason"])

def reading_doc(ID):
    try:
        doc = service.get_document(
            db     = IBM_CLOUDANT_DATABASE,
            doc_id = ID
        ).get_result()
        return doc
    except ApiException as ae:
        print("DB Method failed")
        print(" - status code: " + str(ae.code))
        print(" - error message: " + ae.message)
        if ("reason" in ae.http_response.json()):
            print(" - reason: " + ae.http_response.json()["reason"])

def viewing_last_session_ID(ID):
    doc = reading_doc(ID)
    return doc['conversation'][-1]['session_ID']

def create_new_document(ID, session_ID):
    if not verify_document_exists(ID):
        document = {
            "_id": ID,
            "conversation": [
                {
                    "session_ID": session_ID,
                    "timestamp": str(time.time()),
                    "conversation":[
                    ]
                }
            ]
        }
        upload_doc(document)

def upload_doc(doc):
    try:
        service.post_document(
            db       = IBM_CLOUDANT_DATABASE,
            document = doc
        ).get_result()
    except ApiException as ae:
        print("DB Method failed")
        print(" - status code: " + str(ae.code))
        print(" - error message: " + ae.message)
        if ("reason" in ae.http_response.json()):
            print(" - reason: " + ae.http_response.json()["reason"])

def generate_shift(person, message, timestamp):
    shift = {
        person: message,
        'timestamp': timestamp}
    return shift

def update_context_variables(ID, session_ID, json_context_variables):
    try:
        doc = reading_doc(ID)
        
        for session in doc['conversation']:
            if session['session_ID'] == session_ID:
                for key, value in json_context_variables.items():
                    session[key] = value

        for key, value in json_context_variables.items():
            doc[key] = value

        upload_doc(doc)
    except ApiException as ae:
        print("DB Method failed")
        print(" - status code: " + str(ae.code))
        print(" - error message: " + ae.message)
        if ("reason" in ae.http_response.json()):
            print(" - reason: " + ae.http_response.json()["reason"])

def update_conversation_shift(ID, session_ID, person, message, timestamp):
    conversation_exists = False
    doc = reading_doc(ID)
    for session in doc['conversation']:
        if session['session_ID'] == session_ID:
            conversation_exists = True
            session['conversation'].append(
                generate_shift(person, message, timestamp))
    if not conversation_exists:
        new_conversation = {
                "session_ID": session_ID,
                "timestamp": str(time.time()),
                "conversation":[
                    {
                        person: message,
                        "timestamp": timestamp
                    },
                ]
            }
        doc['conversation'].append(new_conversation)
    upload_doc(doc)

def upload_specific_feature(ID, feature_name, value):
    doc = reading_doc(ID)
    doc[feature_name] = value
    upload_doc(doc)