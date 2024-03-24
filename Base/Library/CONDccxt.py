#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# CCXT Conditional Orders - OliverTwist

# Jackrabbit Relay
# 2021 Copyright © Robert APM Darin
# All rights reserved unconditionally.

# This is the framework used by OliverTwist to process conditional orders.

# Pull the actual fill price from open trades

# SellAction of Close sets Units to all and closes the entire position. Sell uses the Oanda ticket system.

import sys
sys.path.append('/home/GitHub/JackrabbitRelay/Base/Library')
import os
import json
import time

import JRRsupport
import JackrabbitRelay as JRR

# Calculate Proce Exit

def CalculatePriceExit(order,ts,dir,price):
    # Figure out TakeProfit or Stoploss
    if ts=='TakeProfit':
        if '%' in str(order[ts]):
            if dir=='long':
                val=price+((float(order[ts].replace('%','').strip())/100)*price)
            else:
                val=price-((float(order[ts].replace('%','').strip())/100)*price)
        # Pips
        elif 'p' in str(order[ts].lower()):
            if dir=='long':
                val=price+(float(order[ts].lower().replace('p','').strip())*0.0001)
            else:
                val=price-(float(order[ts].lower().replace('p','').strip())*0.0001)
        else:
            val=float(order[ts])
    elif ts=='StopLoss':
        if '%' in str(order[ts]):
            if dir=='long':
                val=price-((float(order[ts].replace('%','').strip())/100)*price)
            else:
                val=price+((float(order[ts].replace('%','').strip())/100)*price)
        # Pips
        elif 'p' in str(order[ts].lower()):
            if dir=='long':
                val=price-(float(order[ts].lower().replace('p','').strip())*0.0001)
            else:
                val=price+(float(order[ts].lower().replace('p','').strip())*0.0001)
        else:
            val=float(order[ts])

    return val

###
### Main driver
###

def OrderProcessor(Orphan):
    # Use Relay to process and validate the order, must be a string
    if type(Orphan['Order']) is dict:
        order=json.dumps(Orphan['Order'])
    else:
        order=Orphan['Order']

    relay=JRR.JackrabbitRelay(framework=Orphan['Framework'],payload=order,NoIdentityVerification=True)
    relay.JRLog.SetBaseName('OliverTwist')

    try:
        # Check to see if order is still open and return current state
        # Handle OANDa's weird order id sequencing
        id=Orphan['ID']
        saction=relay.Order['SellAction'].lower()
        if type(Orphan['Response']) is str:
            Orphan['Response']=json.loads(Orphan['Response'])
        oDetail=Orphan['Response']['Details']

        # Manage average and close extire position
        if saction=='close':
            price=float(oDetail['average'])
            amount=float(oDetail['amount'])
        else:
            price=float(oDetail['price'])
            amount=float(oDetail['amount'])

        # Process the position

        # We need to check TakeProfit and StopLoss. If one of them is hit, we need to build and order and backfeed it in
        # to Relay. It will place a new order.

        # Get the direction of the trade, long/short
        dir=relay.Order['Direction'].lower()
        # Get Ticker
        ticker=relay.GetTicker(symbol=relay.Order['Asset'])

        # Check to see if we have enough balance, if not then delete this order. Deal with futures as well.

        base=relay.Markets[relay.Order['Asset']]['base'].upper()
        if relay.Order['Market']=='spot':
            bal=relay.GetBalance(Base=base)
        else:
            bal=relay.GetPositions(symbols=[relay.Order['Asset']])

        # if ticker is below price and spread, purge and re-purchase

        if bal>amount:
            if "ConditionalRepurchase" in relay.Active:
                relay.JRLog.Write(f"Original: {json.dumps(relay.Order)}",stdOut=False)

                # figure out direction and build replacement order
                makeNewOrder=False
                if dir=='long':
                    makeNewOrder=ticker['Bid']<(price-ticker['Spread'])
                else:
                    makeNewOrder=ticker['Ask']>(price+ticker['Spread'])

                if makeNewOrder==True:
                    # Copy original order
                    newOrder=relay.Order.copy()
                    newOrder['OliverTwist']='Repurchase'
                    if 'OrderType' in relay.Order:
                        newOrder['OrderType']=relay.Order['OrderType']
                    else:
                        newOrder['OrderType']='market'
                    relay.JRLog.Write(f"New: {json.dumps(newOrder)}",stdOut=False)
                    newOrder['Identity']=relay.Identity['Identity']

                    # Feed the new order to Relay
                    result=relay.SendWebhook(newOrder)
                    oid=relay.GetOrderID(result)
                    if oid!=None:
                        # Repurchase was successful, remove this order
                        return 'Delete'
                    else:
                        # Something went wrong, leave it and try again later
                        return 'Waiting'
                else:
                    # Not time to make a new purchase, leave it
                    return 'Delete'
            else:
                relay.JRLog.Write(f"{id}: Amount {amount:.8f} > Balance {bal:.8f} {base}, purge",stdOut=False)
                return 'Delete'

        # Fsilsafe, in the WORST way possible. Do NOT leave a take profit out of the order. At this stage, the whole thing is
        # an absolute nightmare to fix. The is a very brutal way of dealing with poor user choices.
        if 'TakeProfit' not in relay.Order:
            relay.Order['TakeProfit']='2%'
        # Calculate Take Profit
        tp=round(CalculatePriceExit(relay.Order,'TakeProfit',dir,price),5)

        # Figure out StopLoss, if there is one
        if 'StopLoss' in relay.Order:
            sl=round(CalculatePriceExit(relay.Order,'StopLoss',dir,price),5)

        # Get the "strikePrice". This handles both TakeProfit and StopLoss. It doesn't matter which as both are processed
        # the same way.

        LogMSG=None
        StrikeHappened=False
        if dir=='long':
            if 'Diagnostics' in relay.Active:
                relay.JRLog.Write(f"{id}: {dir} Price: {price}, Bid: {ticker['Bid']} TP: {tp}/{relay.Order['TakeProfit']}, SL {sl}/{relay.Order['StopLoss']}",stdOut=False)

            if ticker['Bid']>tp:
                profit=round((amount*ticker['Bid'])-(amount*price),8)
                LogMSG=f"{id}: Prft {dir}, {tp}, {amount}: {price:.5f} -> {ticker['Bid']:5f}/{abs(profit)}"
            if 'StopLoss' in relay.Order and ticker['Bid']<sl:
                loss=round((amount*price)-(amount*ticker['Bid']),8)
                LogMSG=f"{id}: Loss {dir}, {sl}, {amount}: {price:.5f} -> {ticker['Bid']:5f}/{abs(loss)}"

            if ticker['Bid']>tp or ('StopLoss' in relay.Order and ticker['Bid']<sl):
                strikePrice=ticker['Bid']
                StrikeHappened=True
        else:
            if 'Diagnostics' in relay.Active:
                relay.JRLog.Write(f"{id}: {dir} Price: {price}, Ask: {ticker['Ask']} TP: {tp}/{relay.Order['TakeProfit']}, SL {sl}/{relay.Order['StopLoss']}",stdOut=False)

            if ticker['Ask']<tp:
                profit=round((amount*price)-(amount*ticker['Ask']),8)
                LogMSG=f"{id}: Prft {dir}, {tp}, {amount}: {price:.5f} -> {ticker['Ask']:5f}/{abs(profit)}"
            if 'StopLoss' in relay.Order and ticker['Ask']>sl:
                loss=round((amount*ticker['Ask'])-(amounts*price),8)
                LogMSG=f"{id}: Loss {dir}, {sl}, {amount}: {price:.5f} -> {ticker['Ask']:5f}/{abs(loss)}"

            if ticker['Ask']<tp or ('StopLoss' in relay.Order and ticker['Ask']>sl):
                strikePrice=ticker['Ask']
                StrikeHappened=True

        if StrikeHappened==True:
            # Build "strike" order. TakeProfit or StopLoss has been triggered
            newOrder={}
            newOrder['OliverTwist']='Conditional'
            newOrder['Exchange']=relay.Order['Exchange']
            newOrder['Account']=relay.Order['Account']
            newOrder['Market']=relay.Order['Market']
            newOrder['Asset']=relay.Order['Asset']
            newOrder['Action']=relay.Order['SellAction']
            newOrder['Price']=str(strikePrice)
            newOrder['Base']=str(amount)
            if 'OrderType' in relay.Order:
                newOrder['OrderType']=relay.Order['OrderType']
            else:
                newOrder['OrderType']='market'

#            relay.JRLog.Write(f"{id}: {json.dumps(newOrder)}",stdOut=False)

            newOrder['Identity']=relay.Active['Identity']

            # Feed the new order to Relay
            result=relay.SendWebhook(newOrder)
            oid=relay.GetOrderID(result)
            if oid!=None:
                relay.JRLog.Write(LogMSG,stdOut=False)
                resp=relay.GetOrderDetails(id=oid,symbol=relay.Order['Asset'])
                # Order must be closed as it succedded
                newOrder['ID']=oid
                relay.WriteLedger(Order=newOrder,Response=resp)
                return 'Delete'
            else:
                # Give OliverTwist a response
                relay.JRLog.Write(f"{id}: Order failed with {relay.GetFailedReason(result)}",stdOut=False)
                return 'Delete' # 'Waiting'
        else:
            # Strike did not happen
            return 'Waiting'
    except Exception as e:
        # Something went wrong
        relay.JRLog.Write(f"{Orphan['Key']}: Code Error - {sys.exc_info()[-1].tb_lineno}/{str(e)}",stdOut=False)
        return 'Waiting'
