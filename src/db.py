import os, time
from dotenv import load_dotenv
from ibmcloudant.cloudant_v1 import CloudantV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core import ApiException

########################
# Setting Environment Variables and setting up services
load_dotenv()

# Define environment variables
IBM_CLOUDANT_URL = os.getenv('IBM_CLOUDANT_URL')
IBM_CLOUDANT_APIKEY = os.getenv('IBM_CLOUDANT_APIKEY')
IBM_CLOUDANT_DATABASE = os.getenv('IBM_CLOUDANT_DATABASE')

# Configuring and authenticating 
authenticator = IAMAuthenticator(IBM_CLOUDANT_APIKEY)
service = CloudantV1(authenticator=authenticator)
service.set_service_url(IBM_CLOUDANT_URL)

def verify_document_exists(ID: str) -> bool:
    """
    Verify if a document with a specific ID exists in the Cloudant database.

    Parameters
    ----------
    ID : str
        The ID of the document to verify.

    Returns
    -------
    bool
        True if the document exists, False otherwise.

    """
    try:
        all_docs = service.post_all_docs(db=IBM_CLOUDANT_DATABASE, include_docs=False).get_result()
        for doc in all_docs['rows']:
            if doc['id'] == ID:
                return True
        return False
    except ApiException as ae:
        print("DB Method failed")
        print(f" - status code: {str(ae.code)}")
        print(f" - error message: {ae.message}")
        if ("reason" in ae.http_response.json()):
            print(f" - reason: {ae.http_response.json()['reason']}")
            
def reading_doc(ID: str) -> dict:
    """
    Fetches a document with the specified ID from the IBM Cloudant database.
    If the document is not found or there is an error communicating with the 
    database, an exception is raised.
    
    Parameters
    ----------
    ID : str
        The ID of the document to fetch.
    
    Returns
    -------
    dict
        The document with the specified ID.
    """
    try:
        doc = service.get_document(db=IBM_CLOUDANT_DATABASE, doc_id=ID).get_result()
        return doc
    except ApiException as ae:
        print("DB Method failed")
        print(f" - status code: {str(ae.code)}")
        print(f" - error message: {ae.message}")
        if ("reason" in ae.http_response.json()):
            print(f" - reason: {ae.http_response.json()['reason']}")

def viewing_last_session_ID(ID: str) -> str:
    """
    Fetches the session ID of the last conversation in a document
    with the specified ID from the IBM Cloudant database.
    
    Parameters
    ----------
    ID : str
        The ID of the document to fetch.
    
    Returns
    -------
    str
        The session ID of the last conversation in the document.
    """
    doc = reading_doc(ID)
    return doc['conversation'][-1]['session_ID']

def create_new_document(ID: str, session_ID: str):
    """
    Create a new document with the specified ID and session ID in the IBM Cloudant database.
    If the document already exists, it will not create a new document.
    
    Parameters
    ----------
    ID : str
        The ID of the new document
    session_ID : str
        The session ID for the new document
    """
    if not verify_document_exists(ID):
        document = {
            "_id": ID,
            "conversation": [
                {
                    "session_ID": session_ID,
                    "timestamp": str(time.time()),
                    "conversation": []
                }
            ]
        }
        upload_doc(document)

def upload_doc(doc):
    """
    Uploads a document to the IBM Cloudant database.
    If there is an error communicating with the database, an exception is raised.
    
    Parameters
    ----------
    doc : dict
        The document to be uploaded
    """
    try:
        service.post_document(db=IBM_CLOUDANT_DATABASE, document=doc).get_result()
    except ApiException as ae:
        print("DB Method failed")
        print(f" - status code: {str(ae.code)}")
        print(f" - error message: {ae.message}")
        if ("reason" in ae.http_response.json()):
            print(f" - reason: {ae.http_response.json()['reason']}")

def generate_shift(person: str, message: str, timestamp: str) -> dict:
    """
    Generates a shift document with the specified person, message, and timestamp.
    
    Parameters
    ----------
    person : str
        The person who is associated with this shift.
    message : str
        The message for this shift.
    timestamp : str
        The timestamp for this shift.
    
    Returns
    -------
    dict
        The shift document with the specified person, message, and timestamp.
    """
    shift = {
        person: message,
        'timestamp': timestamp}
    return shift

def update_conversation_shift(ID: str, session_ID: str, person: str, message: str, timestamp: str):
    """
    Update the conversation shift with the specified ID, session ID, person, message, and timestamp 
    in the IBM Cloudant database, if conversation does not exist it creates a new one.
    
    Parameters
    ----------
    ID : str
        The ID of the document to be updated
    session_ID : str
        The session ID of the conversation to be updated
    person : str
        Person associated with this conversation shift
    message : str
        message for this conversation shift
    timestamp : str
        timestamp for this conversation shift
    """
    conversation_exists = False
    doc = reading_doc(ID)
    for session in doc['conversation']:
        if session['session_ID'] == session_ID:
            conversation_exists = True
            session['conversation'].append(generate_shift(person, message, str(timestamp)))
    if not conversation_exists:
        new_conversation = {
                "session_ID": session_ID,
                "timestamp": timestamp,
                "conversation":[generate_shift(person, message, timestamp)],
            }
        doc['conversation'].append(new_conversation)
    upload_doc(doc)

def upload_specific_feature(ID: str, feature_name: str, value):
    """
    Update specific feature to a document with the specified ID and feature name and value in the IBM Cloudant database.
    
    Parameters
    ----------
    ID : str
        The ID of the document to be updated
    feature_name : str
        feature name to be updated
    value : any
        The value to be updated for the feature
    """
    doc = reading_doc(ID)
    doc[feature_name] = value
    upload_doc(doc)