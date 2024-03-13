#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Jackrabbit Relay
# 2021 Copyright © Robert APM Darin
# All rights reserved unconditionally.

import sys
sys.path.append('/home/GitHub/JackrabbitRelay/Base/Library')
import os
import json
import time

import JRRsupport
import JackrabbitRelay as JRR

###
### Main driver
###

def OrderProcessor(Orphan):
    # Use Relay to process and validate the order. Order MUST be a JSON string.

    if type(Orphan['Order']) is dict:
        order=json.dumps(Orphan['Order'])
    else:
        order=Orphan['Order']

    relay=JRR.JackrabbitRelay(framework=Orphan['Framework'],payload=order,NoIdentityVerification=True)
    relay.JRLog.SetBaseName('OliverTwist')

    # Check to see if order is still open and return current state
    id=Orphan['ID']
    openOrders=relay.GetOpenOrders(symbol=relay.Order['Asset'])
    #relay.JRLog.Write(f"Orders: {len(openOrders)}",stdOut=False)
    for cur in openOrders:
        if cur['id']==id:
            return 'Waiting'

    # Order must be closed
    relay.WriteLedger(Order=Orphan,Response=None)
    return 'Delete'
