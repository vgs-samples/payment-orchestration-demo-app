import sys
import os
import json
import requests
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
# Uncomment when running locally or with ngrok:
from dotenv import load_dotenv
load_dotenv()

app = Flask('app.browser_initiated')

AUTH_API = "https://auth.verygoodsecurity.com/auth/realms/vgs/protocol/openid-connect/token"
CUSTOMER_VAULT_ID = os.environ.get('CUSTOMER_VAULT_ID')
PAYMENT_ORCH_APP_DOMAIN = f"{CUSTOMER_VAULT_ID}-4880868f-d88b-4333-ab70-d9deecdbffc4.sandbox.verygoodproxy.com"
PAYMENT_ORCH_CLIENT_ID = os.environ.get('PAYMENT_ORCH_CLIENT_ID')
PAYMENT_ORCH_CLIENT_SECRET = os.environ.get('PAYMENT_ORCH_CLIENT_SECRET')

CORS(app, resources={'/*': {'origins': '*'}})

def _generate_access_token():
    data = {
        'client_id': PAYMENT_ORCH_CLIENT_ID,
        'client_secret': PAYMENT_ORCH_CLIENT_SECRET,
        'grant_type': 'client_credentials', 
    }
    response = requests.post(AUTH_API, data=data)
    return response.json()

@app.route("/")
def index():
    return render_template('./browser-initiated.html', customerVaultId = CUSTOMER_VAULT_ID)

@app.route("/get_access_token")
def get_checkout_settings():
    access_token_response = _generate_access_token()
    return {
        'access_token': access_token_response['access_token']
    }

@app.route("/financial_instrument", methods=['GET'])
def financial_instrument():
    id = request.args.get("id")
    transfer_url = 'https://' + PAYMENT_ORCH_APP_DOMAIN + '/financial_instruments/' + id
    access_token_response = _generate_access_token()
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {0}".format(access_token_response['access_token'])
    }

    transfer = requests.get(
        transfer_url,
        headers = headers,
    )

    return transfer.json()

@app.route("/transfer", methods=['POST'])
def transfer():
    body = request.get_json()
    transfer_url = 'https://' + PAYMENT_ORCH_APP_DOMAIN + '/transfers'
    transfers_data = {
        "amount": int(body['amount']) * 100,
        "currency": body['currency'],
        "source": body['financial_instrument_id'],
        "gateway_options": json.loads(body['gateway_options'])
    }
    access_token_response = _generate_access_token()
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {0}".format(access_token_response['access_token'])
    }

    transfer = requests.post(
        transfer_url,
        headers = headers,
        json = transfers_data,
    )
    print("Transfer response headers")
    print(transfer.headers)
    return transfer.json()
