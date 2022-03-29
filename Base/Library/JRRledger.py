#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Jackrabbit Relay
# 2021 Copyright © Robert APM Darin
# All rights reserved unconditionally.

import sys
sys.path.append('/home/JackrabbitRelay/Base/Library')
from datetime import datetime
import ccxt
import json

import JRRconfig
import JRRlog
import JRRapi
import JRRsupport

def WriteLedger(exchange, account, pair, market, action, amount, close, order, RetryLimit,ledgerNote):
    time=(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))

    en=exchange.name.lower().replace(' ','')
    fn=JRRconfig.LedgerDirectory+'/'+en+'.'+account+'.ledger'

    ledger={}
    ledger['DateTime']=time
    ledger['ID']=order['id']
    ledger['Exchange']=en
    ledger['Account']=account
    ledger['Market']=market
    ledger['Asset']=pair
    ledger['Action']=action
    ledger['Close']=close

    oi=order['id']

    # Try to pull completed order information

    retry=0
    done=False
    fo=None
    while not done:
        try:
            if exchange.has['fetchOrder']:
                fo=exchange.fetchOrder(oi,symbol=pair)
            else:
                fo=exchange.fetchClosedOrder(oi,symbol=pair)
        except Exception as e:
            if retry>=RetryLimit:
                done=True
                fo=None
            else:
                JRRlog.WriteLog('Fetch Order Retrying ('+str(retry+1)+'), '+JRRapi.StopHTMLtags(str(e)))
        else:
            done=True
        retry+=1

    if fo!=None:
        for i in fo:
            n=en+i.upper()
            ledger[n]=fo[i]

    if ledgerNote!=None:
        ledger['LedgerNote']=ledgerNote

    s=json.dumps(ledger)+'\n'

    fw=JRRsupport.FileWatch(fn)
    fw.Lock()

    try:
        fh=open(fn,'a')
        fh.write(s)
        fh.close()
    except Exception as e:
        fw.Unlock()
        JRRlog.ErrorLog("Ledger",str(e))

    fw.Unlock()

