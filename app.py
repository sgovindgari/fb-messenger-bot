import os
import sys
import json
import time
from datetime import datetime

import requests
from flask import jsonify
from flask import Flask, request

if sys.version_info[0] >= 3:
    unicode = str

app = Flask(__name__)

plaid_server = "https://peaceful-fortress-19275.herokuapp.com/liabilities"

# hardcoding this token for now
# TODO - use cookies to pass this back to messenger
access_token = "access-sandbox-28e8315a-845e-42bb-8848-6683411cfc9f"


@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = messaging_event["message"]["text"]  # the message's text

                    send_message(sender_id, "Welcome to Pixy. We help you lower and pay off your student loan and credit card debt faster.")
                    add_bank_account(sender_id)

                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    pass

    return "ok", 200


def add_bank_account(recipient_id):
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    
    headers = {
        "Content-Type": "application/json"
    }

    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message":{
            "attachment":{
                "type":"template",
                    "payload":{
                        "template_type":"generic",
                        "elements":[{
                            "title":"Hi!",
                            "image_url":"https://s3.amazonaws.com/gethyped.io/pixycover.png",
                            "subtitle":"We help you manage your student loans and credit card debt.",
                            "default_action": {
                                "type": "web_url",
                                "url": "https://peaceful-fortress-19275.herokuapp.com/",
                                "webview_height_ratio": "tall",
                            },
                        "buttons":[{
                            "type":"web_url",
                            "url":"https://peaceful-fortress-19275.herokuapp.com/",
                            "title":"Add account",
                            "webview_height_ratio": "tall",
                        },
                        {
                            "type":"web_url",
                            "url":"https://www.nerdwallet.com/blog/pay-off-debt/",
                            "title":"Credit Card Guide",
                            "webview_height_ratio": "tall",
                        },
                        {
                            "type":"web_url",
                            "url":"https://www.creditkarma.com/advice/i/student-loans-101/",
                            "title":"Student Loan Guide",
                            "webview_height_ratio": "tall",
                        }]
                    }]
                }
            }
        }
    })

    r = requests.post("https://graph.facebook.com/v4.0/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)

# TODO - show liabilities
# TODO - show workflows 

def show_current_liabilities(recipient_id):
    response = json.loads(requests.get(plaid_server))
    credit_card_debt = list(response['liabilities']['credit'])[0]
    student_debt = list(response['liabilities']['student'])[0]

    # student debt data
    expected_payoff_date = student_debt["expected_payoff_date"]
    guarantor = student_debt["guarantor"]
    interest_rate_percentage = float(student_debt["interest_rate_percentage"])
    last_payment_amount = float(student_debt["last_payment_amount"])
    loan_name = student_debt["loan_name"]
    minimum_payment_amount = float(student_debt["minimum_payment_amount"])
    origination_date = student_debt["origination_date"]
    origination_principal_amount = float(student_debt["origination_principal_amount"])
    outstanding_interest_amount = float(student_debt["outstanding_interest_amount"])
    ytd_interest_paid = float(student_debt["ytd_interest_paid"])
    ytd_principal_paid = float(student_debt["ytd_principal_paid"])

    # credit card debt
    aprs = list(credit_card_debt["aprs"])
    last_statement_balance = float(credit_card_debt["last_statement_balance"])
    last_payment_amount = float(credit_card_debt["last_payment_amount"])
    minimum_payment_amount = float(credit_card_debt["minimum_payment_amount"])

    cc_list = []
    cc_debt = 0

    for cc_balance in aprs:
        apr_percentage = float(cc_balance["apr_percentage"])
        apr_type = cc_balance["apr_type"]
        balance_subject_to_apr = float(cc_balance["balance_subject_to_apr"])
        interest_charge_amount = float(cc_balance["interest_charge_amount"])
        total_debt += balance_subject_to_apr

    total_debt = cc_debt + (origination_principal_amount - ytd_principal_paid)

    send_message(
        recipient_id,
        "Your current credit card debt is " + 
        str(cc_debt) + 
        " and your student loan is " + 
        str(origination_principal_amount - ytd_principal_paid)
    )



def refinance_loan(recipient_id):
    pass


def habit_forming(recipient_id):
    pass

def insights(recipient_id):
    pass


def send_message_with_button(recipient_id, message_text, button_url, button_text):
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    
    headers = {
        "Content-Type": "application/json"
    }

    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message":{
            "attachment":{
                "type":"template",
                    "payload":{
                        "template_type":"button",
                        "text":message_text,
                        "buttons":[{
                            "type":"web_url",
                            "url":button_url,
                            "title":button_text,
                            "webview_height_ratio": "tall",
                        }]
                    }
            }
        }
    })

    r = requests.post("https://graph.facebook.com/v4.0/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        },
    })
    r = requests.post("https://graph.facebook.com/v4.0/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)

    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "sender_action": "mark_seen",
    })

    r = requests.post("https://graph.facebook.com/v4.0/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def log(msg, *args, **kwargs):  # simple wrapper for logging to stdout on heroku
    try:
        if type(msg) is dict:
            msg = json.dumps(msg)
        else:
            msg = unicode(msg).format(*args, **kwargs)
        print(u"{}: {}".format(datetime.now(), msg))
    except UnicodeEncodeError:
        pass  # squash logging errors in case of non-ascii text
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True, port=3000)
