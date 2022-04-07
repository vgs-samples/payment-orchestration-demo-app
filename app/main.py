import sys
import os
import json
import requests
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
# Uncomment when running locally or with ngrok:
# from dotenv import load_dotenv
# load_dotenv()

app = Flask('app.main')

AUTH_API = "https://auth.verygoodsecurity.com/auth/realms/vgs/protocol/openid-connect/token"
CUSTOMER_VAULT_ID = os.environ.get('CUSTOMER_VAULT_ID')
PAYMENT_ORCH_APP_DOMAIN = os.environ.get('PAYMENT_ORCH_APP_DOMAIN')
PAYMENT_ORCH_CLIENT_ID = os.environ.get('PAYMENT_ORCH_CLIENT_ID')
PAYMENT_ORCH_CLIENT_SECRET = os.environ.get('PAYMENT_ORCH_CLIENT_SECRET')
CUSTOMER_VAULT_ACCESS_CREDS_USERNAME = os.environ.get('CUSTOMER_VAULT_ACCESS_CREDS_USERNAME')
CUSTOMER_VAULT_ACCESS_CREDS_SECRET = os.environ.get('CUSTOMER_VAULT_ACCESS_CREDS_SECRET')

CORS(app, resources={'/*': {'origins': '*'}})

@app.route("/")
def index():
    return render_template('./index.html', customerVaultId = CUSTOMER_VAULT_ID)

@app.route("/checkout", methods=['POST'])
def checkout():
    transfer = None
    context = {
        "current_stage": "received-checkout-payload",
        "stages": {
            "received-checkout-payload": {
                "success": True,
                "description": "receiving aliased card data from Checkout.js through the inbound route into /checkout endpoint"
            },
        },
        "events": []
    }
    try:
        trace(context, "====== BEGIN /checkout ENDPOINT ======")
        trace(context, "Received Checkout.js form data. Data has been proxied through the inbound route.")

        fin_instr_data = request.get_json()

        trace(context, "Aliased credit card data:")
        trace(context, json.dumps(fin_instr_data, sort_keys=True, indent=4))

        access_token = get_access_token(context)
        fin_instr = create_financial_instrument(context, fin_instr_data, access_token['access_token'])
        transfer = transfer_money(context, fin_instr, access_token['access_token'])
    except Exception as e:
        curr_stage = context["current_stage"]
        context["stages"][curr_stage]["success"] = False
        trace(context, "An error occured when {0}".format(context['stages'][curr_stage]["description"]))
        print(e)
        
    return {
        "transfer": transfer.json() if transfer else None,
        "events": context["events"],
        "stages": context["stages"]
    }

def create_financial_instrument(context, fin_instr_data, access_token):
    update_stage(context, "create-financial-instrument", "creating financial instrument")
    trace(context, "====== CREATING FINANCIAL INSTRUMENT ======")
    trace(context, 'See documentation page: <a href="https://www.verygoodsecurity.com/docs/payment-optimization/orchestration/api" target="_blank">payment-optimization/<b>orchestration/api</b></a> under "financial instruments" section.')

    fi_create_url = 'https://' + PAYMENT_ORCH_APP_DOMAIN + '/financial_instruments'
    proxy_url = 'https://' + CUSTOMER_VAULT_ACCESS_CREDS_USERNAME + ':' + CUSTOMER_VAULT_ACCESS_CREDS_SECRET + '@' + CUSTOMER_VAULT_ID + '.sandbox.verygoodproxy.com:8443'
    sanitized_proxy_url = 'https://' + CUSTOMER_VAULT_ACCESS_CREDS_USERNAME + ':***ACCESS_CREDENTIAL_PASSWORD***@' + CUSTOMER_VAULT_ID + '.sandbox.verygoodproxy.com:8443'

    trace(context, "Creating Financial Instrument by sending POST request to:")
    trace(context, "- " + fi_create_url)
    trace(context, "Proxying Create Financial Instrument request through outbound route URL:")
    trace(context, "- " + sanitized_proxy_url)

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {0}".format(access_token)
    }

    trace(context, "Create Financial Instrument Request headers:")
    trace(context, json.dumps(headers, sort_keys=True, indent=4))
    trace(context, "Create Financial Instrument Request Body:")
    trace(context, json.dumps(fin_instr_data, sort_keys=True, indent=4))
    
    fin_instr = requests.post(
        fi_create_url,
        proxies = {
            'https': proxy_url,
        },
        headers=headers,
        json = fin_instr_data,
        verify = False,
    )
    
    trace(context, "Create Financial Instrument Response:")
    trace(context, json.dumps(fin_instr.json(), sort_keys=True, indent=4))

    return fin_instr

def transfer_money(context, fin_instr, access_token):
    update_stage(context, "transfer-money", "transfering money using new Financial Instrument")
    trace(context, "====== CHARGING FINANCIAL INSTRUMENT $1.00 ======")
    trace(context, 'See documentation page: <a href="https://www.verygoodsecurity.com/docs/payment-optimization/orchestration/api" target="_blank">payment-optimization/<b>orchestration/api</b></a> under "transfers" section.')

    transfer_url = 'https://' + PAYMENT_ORCH_APP_DOMAIN + '/transfers'
    trace(context, "Transfering money by sending POST request to:")
    trace(context, "- " + transfer_url)

    transfers_data = {
        "amount": 1 * 100,
        "currency": "USD",
        "source": fin_instr.json()['data']['id'],
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {0}".format(access_token)
    }

    trace(context, "Transfer Money Request Headers:")
    trace(context, json.dumps(headers, sort_keys=True, indent=4))
    trace(context, "Transfer Money Request Body:")
    trace(context, json.dumps(transfers_data, sort_keys=True, indent=4))

    transfer = requests.post(
        transfer_url,
        headers = headers,
        json = transfers_data,
    )
    trace(context, "Transfer Money Response:")
    trace(context, json.dumps(transfer.json(), sort_keys=True, indent=4))

    if transfer.json().get("data", {}).get("state") != "successful":
        raise Exception("Credit transaction failed...")
    
    return transfer


def get_access_token(context):
    update_stage(context, "generate-access-token", "generating access token")
    trace(context, "====== GENERATING PAYMENT ORHCESTRATION ACCESS TOKEN ======")
    trace(context, 'See documentation page: <a href="https://www.verygoodsecurity.com/docs/payment-optimization/authentication#how-to-authenticate" target="_blank">/payment-optimization/<b>authentication</b></a>')
    data = {
        'client_id': PAYMENT_ORCH_CLIENT_ID,
        'client_secret': PAYMENT_ORCH_CLIENT_SECRET,
        'grant_type': 'client_credentials', 
    }
    sanitized_data = data.copy()
    sanitized_data['client_secret'] = "XXXX"
    sanitized_json = json.dumps(sanitized_data, indent=4)
    trace(context, "Generating Access Token by sending POST request to:")
    trace(context, "- " + AUTH_API)
    trace(context, "Generate Access Token Request Body:")
    trace(context, sanitized_data)
    response = requests.post(AUTH_API, data=data)
    access_token = response.json()
    trace(context, "Generated access token: {0}".format(access_token['access_token']))
    return response.json()

def update_stage(context, label, description):
    context["stages"][label] = {
        "description": description,
        "success": True,
    }
    context["current_stage"] = label

def trace(context, msg):
    print(msg)
    context["events"].append(msg)
