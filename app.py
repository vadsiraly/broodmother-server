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

# Flask app should start in global layout
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Headers:")
    print(request.headers)

    if not authorizeOrigin(request.headers['Authorization']):
        res = makeWebhookResult(request, createErrorSpeech)
    else:
        res = makeWebhookResult(request, createSpeech)
   
    print("Request:")
    print(json.dumps(req, indent=4))

    res = json.dumps(res, indent=4)
    # print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r

def buildResponseSpeech(iotType, room, stateChange):
    return "I have successfully set the " + iotType + " to " + stateChange + " in the " + room + "."

def createErrorSpeech(reason):
    if (reason is "AUTH_FAILURE"):
        return "You are not authorized to command the Broodmother."

def createSpeech(data):
    iotType = data.get("result").get("parameters").get("iot-type")
    room = data.get("result").get("parameters").get("room")
    stateChange = data.get("result").get("parameters").get("state-change")

    speech = buildResponseSpeech(iotType, room, stateChange)

    print("Response:")
    print(speech)

    return speech

def makeWebhookResult(data, speech):
    if req.get("result").get("action") != "light.action":
        return {}

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "broodmother"
    }

def authorizeOrigin(header):
    auth_type = header.split()[0]
    username, password = decodeCredentials(header.split()[1])

    print("Using authorization type: " + auth_type)
    print("Username: " + username)
    print("Password: " + password)

    if (username is "jarvis") and (password is "jarvis"):
        return True
    else:
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
