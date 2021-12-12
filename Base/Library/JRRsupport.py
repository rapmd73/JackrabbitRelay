#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Jackrabbit Relay
# 2021 Copyright © Robert APM Darin
# All rights reserved unconditionally.

import sys
sys.path.append('/home/JackrabbitRelay/Base/Library')
import os
import time
from datetime import datetime
import json
import ccxt

import JRRconfig
import JRRlog

# Reusable file locks, using atomic operations
# NOT suitable for distributed systems.
#
# fw=FileWatch(filename)
# fw.Lock()
# ( do somwething )
# fw.Unlock()

class FileWatch:

    # Initialize the file name

    def __init__(self,filename):
        self.filename=filename+'.lock'

    # Lock the file

    def Lock(self):
        p=str(os.getpid())
        tn=self.filename+'.'+p
        fh=open(tn,'w')
        fh.write(f"{p}\n")
        fh.close()

        done=False
        while not done:
            try:
                os.rename(tn,self.filename)
            except:
                pass
            else:
                done=True

            time.sleep(0.1)

    # Unlock the file

    def Unlock(self):
        try:
            os.remove(self.filename)
        except:
            pass

# Read the asset list and verify max asset allowance

def ReadAssetList(exchange,account,pair,mp,delete):
    JRRlog.WriteLog('|- Verifying maximum asset allowwance of '+str(mp))
    coins=[]
    fn=JRRconfig.LogDirectory+'/'+exchange+'.'+account+'.coinlist'

    p=pair.upper()

    fw=FileWatch(fn)
    fw.Lock()

    c=0
    try:
        if os.path.exists(fn):
            cf=open(fn,'rt+')
            for line in cf.readlines():
                l=line.strip().upper()
                if len(l)>0:
                    if not delete:
                        c+=1
                        coins.append(l)
                    else:
                        JRRlog.WriteLog('|-- '+p+' removed')
            cf.close()

            if not p in coins and c<int(mp) and not delete:
                JRRlog.WriteLog('|-- '+p+' added')
                coins.append(p)
        else:
            if not delete:
                c+=1
                JRRlog.WriteLog('|-- '+p+' added')
                coins.append(p)

        WriteAssetList(exchange,account,coins)
    except:
        pass

    fw.Unlock()

    if c>=int(mp):
        JRRlog.ErrorLog("MaxAsset Verification",account+'Exceeded maximum asset limit')

def WriteAssetList(exchange,account,coins):
    fn=JRRconfig.LogDirectory+'/'+exchange+'.'+account+'.coinlist'

    if coins==[]:
        try:
            os.remove(fn)
        except:
            pass
    else:
        fh=open(fn,'a')
        for p in coins:
            s=f"{p}\n"
            fh.write(s)
        fh.close()

# Filter end of line and hard spaces

def pFilter(s):
    d=s.replace("\\n","").replace("\\t","").replace("\\r","")

    for c in '\t\r\n \u00A0':
        d=d.replace(c,'')

    return(d)

# Read the exchange config file and load API/SECRET for a given (sub)account.
# MAIN is reserved for the main account

def ReadConfig(echg,account):
    keys=[]
    fn=JRRconfig.ConfigDirectory+'/'+echg+'.cfg'

    if os.path.exists(fn):
        cf=open(fn,'rt+')
        for line in cf.readlines():
            if len(line.strip())>0 and line[0]!='#':
                key=json.loads(line)
                if key['Account']==account:
                    keys.append(key)
        cf.close()

        if keys==[]:
            JRRlog.ErrorLog("Reading Configuration",account+' reference not found, check spelling/case')

        return keys
    else:
        JRRlog.ErrorLog("Reading Configuration",echg+'.cfg not found in config directory')

# Read the json entry and verify the required elements as present

def ProcessJSON(payload):
    try:
        data=json.loads(payload,strict=False)
    except json.decoder.JSONDecodeError:
        return None

    if "Exchange" not in data:
        JRRlog.WriteLog('Missing exchange identifier')
        return None
    if "Market" not in data:
        JRRlog.WriteLog('Missing market identifier')
        return None
    if "Account" not in data:
        JRRlog.WriteLog('Missing account identifier')
        return None
    if "Action" not in data:
        JRRlog.WriteLog('Missing action (buy/sell/close) identifier')
        return None
    if "Asset" not in data:
        JRRlog.WriteLog('Missing asset identifier')
        return None

    return data

