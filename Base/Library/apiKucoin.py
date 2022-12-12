#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Jackrabbit Relay - Kucoin API framework
# 2021-2022 Copyright © Robert APM Darin
# All rights reserved unconditionally.

# IMPORTANT: This is a low level API framework. Do NOT add retries or any other higher level
# functionality. This framework must simple communicate with Kucoin at its most basic level.

import sys
sys.path.append('/home/JackrabbitRelay2/Base/Library')
import os
import json
import requests
import hmac
import hashlib
import base64
import time
from uuid import uuid1
from datetime import datetime

# Needed to be able to reference the basic support functions, locker, lists, and
# other basic primitives.

import JRRsupport

class Broker:

    # Initialize everything for this broker.

    def __init__(self,API=None, SECRET=None, Passphrase=None, Sandbox=False):
        self.Version=0.0.0.0.1
        self.API=API
        self.SECRET=SECRET
        self.Passphrase=Passphrase
        self.Sandbox=Sandbox

        if self.Sandbox==True:
            self.url='https://openapi-sandbox.kucoin.com'
        else:
            self.url='https://api.kucoin.com'

        self.Results=None

    def API(self,**kwargs):
        method=kwargs.get('method')
        req=kwargs.get('request')
        params=kwargs.get('params')
        timeout=5

        uri_path=req
        data_json=''
        if method in ['GET', 'DELETE']:
            if params:
                strl = []
                for key in sorted(params):
                    strl.append("{}={}".format(key, params[key]))
                data_json+='&'.join(strl)
                req+='?'+data_json
                uri_path=req
        else:
            if params!=None:
                data_json=json.dumps(params)
                uri_path=req+data_json

        headers={}
        headers["User-Agent"]="Jackrabbit Relay/"+self.Version

        now_time=int(time.time())*1000
        str_to_sign=str(now_time)+method+uri_path
        sign=base64.b64encode(hmac.new(self.SECRET.encode('utf-8'),str_to_sign.encode('utf-8'),hashlib.sha256).digest())

        passphrase=base64.b64encode(hmac.new(self.SECRET.encode('utf-8'),self.Passphrase.encode('utf-8'),hashlib.sha256).digest())
        headers["User-Agent"]="Jackrabbit Relay/"+self.Version
        headers["KC-API-SIGN"]=sign
        headers["KC-API-TIMESTAMP"]=str(now_time)
        headers["KC-API-KEY"]=self.API
        headers["KC-API-PASSPHRASE"]=self.Passphrase
        headers["Content-Type"]="application/json"
        headers["KC-API-KEY-VERSION"]="2"

        url=self.url+uri

        if method in ['GET', 'DELETE']:
            self.Results=requests.request(method,url,headers=headers,timeout=timeout)
        else:
            self.Results=requests.request(method,url,headers=headers,data=data_json,timeout=timeout)
        return self.check_response_data(self.Results)





"""
    def _request(self, method, uri, timeout=5, auth=True, params=None):
        uri_path = uri
        data_json = ''
        version = 'v1.0.7'
        if method in ['GET', 'DELETE']:
            if params:
                strl = []
                for key in sorted(params):
                    strl.append("{}={}".format(key, params[key]))
                data_json += '&'.join(strl)
                uri += '?' + data_json
                uri_path = uri
        else:
            if params:
                data_json = json.dumps(params)

                uri_path = uri + data_json

        headers = {}
        if auth:
            now_time = int(time.time()) * 1000
            str_to_sign = str(now_time) + method + uri_path
            sign = base64.b64encode(
                hmac.new(self.secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())
            if self.is_v1api:
                headers = {
                    "KC-API-SIGN": sign,
                    "KC-API-TIMESTAMP": str(now_time),
                    "KC-API-KEY": self.key,
                    "KC-API-PASSPHRASE": self.passphrase,
                    "Content-Type": "application/json"
                }
            else:
                passphrase = base64.b64encode(
                    hmac.new(self.secret.encode('utf-8'), self.passphrase.encode('utf-8'), hashlib.sha256).digest())
                headers = {
                    "KC-API-SIGN": sign,
                    "KC-API-TIMESTAMP": str(now_time),
                    "KC-API-KEY": self.key,
                    "KC-API-PASSPHRASE": passphrase,
                    "Content-Type": "application/json",
                    "KC-API-KEY-VERSION": "2"
                }
        headers["User-Agent"] = "Jackrabbit Relay/"+Version
        url = urljoin(self.url, uri)

        if method in ['GET', 'DELETE']:
            response_data = requests.request(method, url, headers=headers, timeout=timeout)
        else:
            response_data = requests.request(method, url, headers=headers, data=data_json,
                                             timeout=timeout)
        return self.check_response_data(response_data)

    @staticmethod
    def check_response_data(response_data):
        if response_data.status_code == 200:
            try:
                data = response_data.json()
            except ValueError:
                raise Exception(response_data.content)
            else:
                if data and data.get('code'):
                    if data.get('code') == '200000':
                        if data.get('data'):
                            return data['data']
                        else:
                            return data
                    else:
                        raise Exception("{}-{}".format(response_data.status_code, response_data.text))
        else:
            raise Exception("{}-{}".format(response_data.status_code, response_data.text))

    @property
    def return_unique_id(self):
        return ''.join([each for each in str(uuid1()).split('-')])
"""
