# -*- coding: utf-8 -*-
import os
import sys
import json
import time
from datetime import datetime

import requests
from flask import jsonify
from flask import Flask, request
import threading

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

                log(messaging_event)

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = messaging_event["message"]["text"]  # the message's text

                    if 'options' in message_text:
                        log('called options')
                        send_all_options(sender_id)
                    elif 'add account' in message_text:
                        add_bank_account(sender_id)
                    elif 'refinance' in message_text:
                        refinance_loan(sender_id)
                    elif 'insights' in message_text:
                        insights(sender_id)
                    elif 'spend' in message_text:
                        habit_forming(sender_id)
                    elif 'new debt' in message_text:
                        updated_debt(sender_id)
                    elif 'yes' in message_text:
                        send_message_with_picture('https://media1.tenor.com/images/04052e9d28831ce512093906edec28f6/tenor.gif')
                        send_message('Pixy will process your payment accordingly.')
                    elif 'demo' in message_text:
                        thread1 = threading.Thread(target=workflow, args=(sender_id,))
                        thread1.start()
                        log('called workflow')
                    else:
                        send_message(sender_id, "Welcome to Pixy. 😀")
                        send_message(sender_id, "I will find the best ways to help you manage you student debt 💰. I can recommend the optimal payment amounts, remind you of upcoming payments, help you manage your expenses and increase savings")
                        add_bank_account(sender_id)
                        

                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    log('received postback')
                    if messaging_event['payload'] is not None:
                        
                        event = messaging_event['postback']['payload']
                        sender_id = messaging_event['sender_id']
                        
                        if event == 'analyze':
                            insights(sender_id)
                        elif event == 'habits':
                            habit_forming(sender_id)
                        elif event == 'refinance':
                            log('refinance')
                            refinance_loan(sender_id)
                        else:
                            pass


    return "ok", 200

def send_all_options(recipient_id):
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
                        "elements":[
                            {
                                "title":"Here are some ways we can help you! Select an option.",
                            "buttons":[
                                {
                                    "type":"postback",
                                    "title":"Analyze expenses",
                                    "payload": "analyze",
                                },
                                {
                                    "type":"postback",
                                    "title":"Show spending habits",
                                    "payload": "habits",
                                },
                                {
                                    "type":"postback",
                                    "title":"Refinance Debt",
                                    "payload": "refinance",
                                }
                            ]
                        }]
                    }
            }
        }
    })

    r = requests.post("https://graph.facebook.com/v4.0/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        print(r.text)
        #log(r.text)

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
                            "title":"Link your bank accounts to get started",
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
                            "title":"Link bank accounts",
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

# {
#     "type":"web_url",
#     "url":"https://www.nerdwallet.com/blog/pay-off-debt/",
#     "title":"Credit Card Guide",
#     "webview_height_ratio": "tall",
# },
# {
#     "type":"web_url",
#     "url":"https://www.creditkarma.com/advice/i/student-loans-101/",
#     "title":"Student Loan Guide",
#     "webview_height_ratio": "tall",
# }

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
                        "text":"I found some refinancing options based on your current payments, payoff date and expenditures. Select to learn more.",
                        "buttons":[{
                            "type":"web_url",
                            "url":"https://www.sofi.com/refinance-student-loan/",
                            "title":"SoFi 2.05-6.48%",
                            "webview_height_ratio": "tall",
                        },
                        {
                            "type":"web_url",
                            "url":"https://www.earnest.com/refinance-student-loans",
                            "title":"Earnest 2.14-7.49%",
                            "webview_height_ratio": "tall",
                        },
                        {
                            "type":"web_url",
                            "url":"https://www.commonbond.co/affiliate/student-loan-hero",
                            "title":"CommonBond 2.14-8.24%",
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

def workflow(recipient_id):

    send_message(recipient_id, "Your account has been successfully connected! 🎉")

    send_message(recipient_id, "You can add more accounts anytime by sending \"add account\"")

    send_message_with_picture(recipient_id, "https://media.giphy.com/media/zNSX3G2LztEyY/giphy.gif")

    send_message(recipient_id, "Building your financial picture...")

    time.sleep(15)

    insights(recipient_id)

    time.sleep(15)

    habit_forming(recipient_id)
    time.sleep(15)

    updated_debt(recipient_id)

    time.sleep(15)

    refinance_loan(recipient_id)


def habit_forming(recipient_id):
    send_message(
        recipient_id,
        "Hey there, hope your day is going great! It looks like you spent $98 on amazon.com this month.  You can save $5 in total interest if you pay $98 towards your loan. Would you like me to save some money towards your student loan?"
    )

def updated_debt(recipient_id):
    send_message(recipient_id, 
        "You paid $300.35 this month towards your student loan. Oustanding loan amount is now $24,328! Keep up the good work!! 🎊"
    )

    debt_breakdown(recipient_id, 300.35)

def debt_breakdown(recipient_id, minus):
    send_message(recipient_id, 
        "Average monthly income: $3320\n" +
        "Average monthly expenses: $2020\n" +
        "Breakdown of your debt: {:.2f}\n\n".format((27503.9-minus)) + 
        "Credit cards: 2775.55\n" + 
        "   APR: 15.24\n" + 
        "   Amount: 1562.32\n" + 
        "   APR: 27.95\n"+
        "   Amount: 56.22\n"+
        "   APR: 12.5\n"+
        "   Amount: 157.01\n"+
        "   APR: 0\n"+
        "   Amount: 1000\n\n" + 
        "Student Loans: {:.2f}\n".format((24728.35-minus)) + 
        "Interest rate: 5.25%\n"
    )

def insights(recipient_id):
    # Monthly payments
        # Total debt remaining
        # Credit cards
            # APR 
            # Amount
        # Student Loan
            # Interest
            # Amount remaining

    # Balance so far
    # Suggested amount to pay

    debt_breakdown(recipient_id, 0)

    send_message_with_picture(recipient_id, "https://s3.amazonaws.com/gethyped.io/pixydebt2.jpg")

    send_message(
        recipient_id,
        "We found that you can save $983 in interest by making $102 additional monthly payment towards your Chase student loan. Do you want me to increase your monthly payment?"
    )

def send_message_with_picture(recipient_id, url):
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
            "attachment": {
                "type": "image",
                "payload": {
                    "url": url,
                }
            }    
        }
    })

    r = requests.post("https://graph.facebook.com/v4.0/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


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

