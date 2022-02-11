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
import JRRsupport

# {
#     'id': '620044897ee3b40001827bf9', 
#     'clientOrderId': 'b693934e-5f91-4b29-97b3-c7e5f775e865', 
#     'info': 
#         {'orderId': '620044897ee3b40001827bf9'}, 
#         'timestamp': 1644184713911, 
#         'datetime': '2022-02-06T21:58:33.911Z', 
#         'lastTradeTimestamp': None, 
#         'symbol': 'SLP/USDT', 
#         'type': 'market', 
#         'side': 'buy', 
#         'price': 0.01258, 
#         'amount': 0.7949, 
#         'cost': None, 
#         'average': None, 
#         'filled': None, 
#         'remaining': None, 
#         'status': None, 
#         'fee': None, 
#         'trades': None
# }

def WriteLedger(exchange, account, pair, market, action, amount, close, order, RetryLimit):
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
            fo=exchange.fetchOrder(oi,symbol=pair)
        except Exception as e:
            if retry>=RetryLimit:
                done=True
                fo=None
            else:
                JRRlog.WriteLog('Fetch Order Retrying ('+str(retry+1)+'), '+StopHTMLtags(str(e)))
        else:
            done=True
        retry+=1

    if fo!=None:
        for i in fo:
            n=en+i.upper()
            ledger[n]=fo[i]

    fw=JRRsupport.FileWatch(fn)
    fw.Lock()

    s=json.dumps(ledger)+'\n'
    try:
        fh=open(fn,'a')
        fh.write(s)
        fh.close()
    except Exception as e:
        fw.Unlock()
        JRRlog.ErrorLog("Ledger",str(e))

    fw.Unlock()

