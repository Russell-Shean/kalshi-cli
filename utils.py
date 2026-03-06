import os
import re

import requests
import datetime

from dotenv import load_dotenv

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.exceptions import InvalidSignature

from unidecode import unidecode

def build_google_service(service_type):
    '''This function builds a drive service for later use manipulating drive
     files and sending emails

    This loads secrets from .env or github secrets and then builds
    authentication and the service based on the provided scopes

    Possible types are gmail and drive (for now)
    '''

    my_scopes = []
    service_version = ""

    if service_type == "gmail":
        my_scopes = ["https://www.googleapis.com/auth/gmail.modify"]
        service_version = "v1"

    elif service_type == "drive":
        my_scopes = ["https://www.googleapis.com/auth/drive"]
        service_version = "v3"

    # Load secrets
    load_dotenv()

    # Load from environment variables
    client_id = os.environ["GOOGLE_OAUTH_CLIENT_ID"]
    client_secret = os.environ["GOOGLE_OAUTH_CLIENT_SECRET"]
    refresh_token = os.environ["GOOGLE_OAUTH_REFRESH_TOKEN"]

    creds = Credentials(
    token=None,
    refresh_token=refresh_token,
    token_uri="https://oauth2.googleapis.com/token",
    client_id=client_id,
    client_secret=client_secret,
    scopes=my_scopes,
    )

    # Refresh the access token
    creds.refresh(Request())

    drive_service = build(service_type, service_version, credentials=creds)

    return drive_service


#########################################3
# Kalshi creds
##########################################


def load_private_key_from_file(file_path):
    with open(file_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,  # or provide a password if your key is encrypted
            backend=default_backend()
        )
    return private_key



def sign_pss_text(private_key: rsa.RSAPrivateKey, text: str) -> str:
    message = text.encode('utf-8')
    try:
        signature = private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH
            ),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode('utf-8')
    except InvalidSignature as e:
        raise ValueError("RSA sign PSS failed") from e


def call_kalshi_api(private_key_path, method, base_url, endpoint_path, kalshi_key_id, params=None):
    current_time = datetime.datetime.now()
    timestamp = current_time.timestamp()
    current_time_milliseconds = int(timestamp * 1000)
    timestampt_str = str(current_time_milliseconds)
    
    private_key = load_private_key_from_file(private_key_path)
    method = method
    base_url = base_url
    path=endpoint_path
    
    # Strip query parameters from path before signing
    path_without_query = path.split('?')[0]
    msg_string = timestampt_str + method + path_without_query
    sig = sign_pss_text(private_key, msg_string)

    headers = {
    'KALSHI-ACCESS-KEY': kalshi_key_id,
    'KALSHI-ACCESS-SIGNATURE': sig,
    'KALSHI-ACCESS-TIMESTAMP': timestampt_str
    }

    print(f"{base_url}{path}")
    
    if params is not None:
        response = requests.get(f"{base_url}{path}", headers=headers, params=params)

    else:
        response = requests.get(f"{base_url}{path}", headers=headers)
    
    
    response.raise_for_status()

    return response



#########################################
# Normalize player names
#########################################

def normalize_name(name):

    name = unidecode(name)
    name = name.lower()

    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", " ", name)

    return name.strip()