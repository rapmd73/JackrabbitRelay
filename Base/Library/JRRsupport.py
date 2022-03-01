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
import json

import JRRconfig
import JRRapi
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
        self.RetryLimit=37

    # Lock the file

    def Lock(self):
        # Deal with a dead lock file.
        # This will start a race with other programs waiting and testing
        # Under no circumstances should a lock last more then 5 minutes (300 seconds)

        try:
            st=os.stat(self.filename)
            age=time.time()-st.st_mtime
            if age>300:
                self.Unlock()
        except:
            pass

        # Set up the local lock file

        p=str(os.getpid())
        tn=self.filename+'.'+p
        fh=open(tn,'w')
        fh.write(f"{p}\n")
        fh.close()

        # Let the battle begin...

        done=False
        retry=0
        while not done:
            try:
                os.rename(tn,self.filename)
            except:
                retry+=1
                if retry>=RetryLimit:
                    JRRlog.ErrorLog("FileLock","exclusive access request failed")
            else:
                done=True

            time.sleep(0.1)

    # Unlock the file

    def Unlock(self):
        try:
            os.remove(self.filename)
        except:
            pass

# Elastic Delay. This is designed to prevent the VPS from being overloaded

def GetLoadAVG():
    fh=open('/proc/loadavg')
    l=fh.readline()
    fh.close()

    LoadAVG=l.split(' ')

    return(LoadAVG)

# Returns seconds

def ElasticSleep(s):
    LoadAVG=GetLoadAVG()
    delay=float(max(LoadAVG[0],LoadAVG[1],LoadAVG[2]))

    time.sleep(s+delay)

# Returns milliseconds

def ElasticDelay():
    LoadAVG=GetLoadAVG()
    delay=int(float(max(LoadAVG[0],LoadAVG[1],LoadAVG[2]))*1000)

    return delay

# Read the asset list and verify max asset allowance

def ReadAssetList(exchange,account,pair,mp,delete):
    JRRlog.WriteLog('Verifying maximum asset allowance of '+str(mp))
    coins={}
    fn=JRRconfig.LogDirectory+'/'+exchange+'.'+account+'.coinlist'

    p=pair.upper()

    fw=FileWatch(fn)
    fw.Lock()

    try:
        if os.path.exists(fn):
            cf=open(fn,'rt+')
            buffer=cf.read()
            cf.close()
            coins=json.loads(buffer)

            if not p in coins and len(coins)<int(mp) and not delete:
                JRRlog.WriteLog('|- '+p+' added')
                coins[p]=time.time()
            else:
                if p in coins:
                    if delete:
                        JRRlog.WriteLog('|- '+p+' removed')
                        try:
                            coins.pop(p,None)
                        except:
                            pass
                    else:
                        JRRlog.WriteLog('|- '+p+' updated')
                        coins[p]=time.time()
        else:
            if not delete:
                JRRlog.WriteLog('|- '+p+' added')
                coins[p]=time.time()

        # Remove any coin over 7 days

        for c in coins:
            t=(time.time()-coins[c])
            if t>(7*86400):
                JRRlog.WriteLog('|- '+c+' aged out')
                try:
                    coins.pop(c,None)
                except:
                    pass

        WriteAssetList(exchange,account,coins)
    except:
        pass

    fw.Unlock()

    if len(coins)>=int(mp) and not p in coins:
        JRRlog.ErrorLog("MaxAsset Verification",p+' not allowed to trade')

    return coins

def WriteAssetList(exchange,account,coins):
    fn=JRRconfig.LogDirectory+'/'+exchange+'.'+account+'.coinlist'

    if coins==[]:
        try:
            os.remove(fn)
        except:
            pass
    else:
        fh=open(fn,'w')
        fh.write(json.dumps(coins))
        fh.close()

# This list determines a fixed percentage for a coin per balance for the
# life of the trade, bot just the individual position

def ReadPCTValueList(exchange,account,pair,pct,close,delete,RetryLimit):
    coins={}
    amount=0
    en=exchange.name.lower().replace(' ','')
    quote=exchange.markets[pair]['quote']
    fn=JRRconfig.LogDirectory+'/'+en+'.'+account+'.pctvalue'

    p=pair.upper()
    JRRlog.WriteLog('Checking amount/percentage for '+p)

    fw=FileWatch(fn)
    fw.Lock()

    try:
        if os.path.exists(fn):
            cf=open(fn,'rt+')
            buffer=cf.read()
            cf.close()
            coins=json.loads(buffer)

            if not p in coins and not delete:
                # Read the existing value
                bal=JRRapi.GetBalance(exchange,quote,RetryLimit)
                jpkt['Time']=time.time()
                jpkt['Amount']=round(((pct/100)*bal)/close,8)
                amount=jpkt['Amount']
                coins[p]=json.dumps(jpkt)
                JRRlog.WriteLog('|- '+p+' added')
            else:
                if p in coins:
                    if delete:
                        JRRlog.WriteLog('|- '+p+' removed')
                        try:
                            coins.pop(p,None)
                        except:
                            pass
                    else:
                        # Return existing amount
                        jpkt=json.loads(coin[p])
                        jpkt['Time']=time.time()
                        amount=jpkt['Amount']
                        coins[p]=json.dumps(jpkt)
                        JRRlog.WriteLog('|- '+p+' updated')
        else:
            if not delete:
                jpkt={}
                bal=JRRapi.GetBalance(exchange,quote,RetryLimit)
                jpkt['Time']=time.time()
                jpkt['Amount']=round(((pct/100)*bal)/close,8)
                amount=jpkt['Amount']
                coins[p]=json.dumps(jpkt)
                JRRlog.WriteLog('|- '+p+' added')

        # Remove any coin over 7 days

        for c in coins:
            jpkt=json.loads(coins[c])
            t=(time.time()-jpkt['Time'])
            if t>(7*86400):
                JRRlog.WriteLog('|- '+c+' aged out')
                try:
                    coins.pop(c,None)
                except:
                    pass

        WritePCTValueList(exchange,account,coins)
    except:
        pass

    fw.Unlock()

    return amount

def WritePCTValueList(exchange,account,coins):
    en=exchange.name.lower().replace(' ','')
    fn=JRRconfig.LogDirectory+'/'+en+'.'+account+'.pctvalue'

    if coins==[]:
        try:
            os.remove(fn)
        except:
            pass
    else:
        fh=open(fn,'w')
        fh.write(json.dumps(coins))
        fh.close()

# Filter end of line and hard spaces

def pFilter(s):
    d=s.replace("\\n","").replace("\\t","").replace("\\r","")

    for c in '\t\r\n \u00A0':
        d=d.replace(c,'')

    return(d)

# Read the exchange config file and load API/SECRET for a given (sub)account.
# MAIN is reserved for the main account

# { "Indentity":"F}!2F[PI=-{e:7hM0Q4/642!m8;TL>S5LVfIb%)QzwP%9!@CWKwv#};e:3bPLcmEv/dnjC+NhY1D-rvb~037mOv(0J/9zmB-UD2ig1_I78b3=yK}N]xb4.}g^mLY@mctZ" }

def ReadConfig(echg,account):
    keys=[]

    idl=None
    idf=JRRconfig.ConfigDirectory+'/Identity.cfg'
    if os.path.exists(idf):
        cf=open(idf,'rt+')
        try:
            idl=json.loads(cf.readline())
        except:
            JRRlog.ErrorLog("Reading Configuration",'identity damaged')
        cf.close()

    fn=JRRconfig.ConfigDirectory+'/'+echg+'.cfg'
    if os.path.exists(fn):
        cf=open(fn,'rt+')
        for line in cf.readlines():
            if len(line.strip())>0 and line[0]!='#':
                try:
                    key=json.loads(line)
                except:
                    JRRlog.ErrorLog("Reading Configuration",'damaged: '+line)
                if key['Account']==account:
                    # Add identity to account reference
                    if idl!=None:
                        key= { **idl, **key }
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

