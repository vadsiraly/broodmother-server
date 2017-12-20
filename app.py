# -*- coding:utf8 -*-
# !/usr/bin/env python
# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import json
import os

import base64

from flask import Flask
from flask import request
from flask import make_response

from flask_sslify import SSLify

accepted_actions = ["lights.action","mood.action"]

# Flask app should start in global layout
app = Flask(__name__)
sslify = SSLify(app)

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    if req.get("result").get("action") not in accepted_actions:
        return {}

    print("Headers:")
    print(request.headers)
    print("Request:")
    print(json.dumps(req, indent=4))

    res = ""
    if not authorizeOrigin(request.headers['Authorization']):
        res = makeWebhookResult(createErrorSpeech("AUTH_FAILURE"))
    else:
        res = makeWebhookResult(createSpeech(req))

    res = json.dumps(res, indent=4)
    # print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r

def answerLightAction(iotType, room, stateChange):
    return "I have successfully set the " + iotType + " to " + stateChange + " in the " + room + "."

def answerMoodAction(mood):
    return "Setting the mood to " + mood + "."

def createErrorSpeech(reason):
    if (reason == "AUTH_FAILURE"):
        return "Warning: The Broodmother received a command from an unauthorized user."

def createCustomErrorSpeech(message):
    return message

def createSpeech(data):
    if data.get("result").get("action") == "lights.action":
        print("Preparing response for lights.action...")
        iot_type = data.get("result").get("parameters").get("iot-type")
        room = data.get("result").get("parameters").get("room")
        stateChange = data.get("result").get("parameters").get("state-change")
        speech = answerLightAction(iot_type, room, stateChange)
    elif data.get("result").get("action") == "mood.action":
        print("Preparing response for mood.action...")
        iot_type = data.get("result").get("parameters").get("iot-type")
        if iot_type != "mood":
            return createCustomErrorSpeech("You cannot set the mood of the "+iot_type+". Duh!")
        room = data.get("result").get("parameters").get("room")
        if room != "living room":
            return createCustomErrorSpeech("You cannot set the mood of the "+room+" yet!")
        mood = data.get("result").get("parameters").get("mood")
        speech = answerMoodAction(mood)
    else:
        return createCustomErrorSpeech("Warning: The broodmother has received invalid action!")

    return speech

def makeWebhookResult(speech):
    print("Response:")
    print(speech)

    data = createGoogleData(ssml = True)

    return {
        "speech": "<speak>"+speech+"</speak>", #speech, <audio src='https://actions.google.com/sounds/v1/alarms/alarm_clock.ogg'>sound</audio>
        "displayText": speech,
        "data": data,
        # "contextOut": [],
        "source": "broodmother"
    }

def createGoogleData(ssml):
    return {
      "google": {
      "expect_user_response": False,
      "is_ssml": True
      }
    }

def authorizeOrigin(header):
    auth_type = header.split()[0]
    username, password = decodeCredentials(header.split()[1])

    print("Using authorization type: " + auth_type)
    print("Username: " + username)
    print("Password: " + password)

    if (username == "jarvis") and (password == "jarvis"):
        print("Credentials are correct!")
        return True
    else:
        print("Credentials are INCORRECT!")
        return False

def decodeCredentials(cred_base64):
    decoded_creds = base64.b64decode(cred_base64).decode("utf-8").split(":")

    username = decoded_creds[0]
    password = decoded_creds[1]

    return username, password

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')
