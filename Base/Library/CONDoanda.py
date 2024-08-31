#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# OANDA Conditional Orders - OliverTwist

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
import datetime
import time

import JRRsupport
import JackrabbitRelay as JRR

# Calculate Price

def CalculatePriceExit(order,ts,dir,price,onePip):
    # Figure out TakeProfit or Stoploss
    if ts=='TakeProfit':
        if '%' in order[ts]:
            if dir=='long':
                val=price+((float(order[ts].replace('%','').strip())/100)*price)
            else:
                val=price-((float(order[ts].replace('%','').strip())/100)*price)
        # Pips
        elif 'p' in order[ts].lower():
            if dir=='long':
                val=price+(float(order[ts].lower().replace('p','').strip())*onePip)
            else:
                val=price-(float(order[ts].lower().replace('p','').strip())*onePip)
        else:
            val=float(order[ts])
    elif ts=='StopLoss':
        if '%' in order[ts]:
            if dir=='long':
                val=price-((float(order[ts].replace('%','').strip())/100)*price)
            else:
                val=price+((float(order[ts].replace('%','').strip())/100)*price)
        # Pips
        elif 'p' in order[ts].lower():
            if dir=='long':
                val=price-(float(order[ts].lower().replace('p','').strip())*onePip)
            else:
                val=price+(float(order[ts].lower().replace('p','').strip())*onePip)
        else:
            val=float(order[ts])

    return val

# Return the oldest trade in the list

def GetOldestTrade(relay,pair):
    openTrades=relay.GetOpenTrades(symbol=pair)

    if openTrades==[]:
        return None

    # Find the OLDEST entry in the trades for reduction
    oldestTrade=None
    oldestTime=time.time()
    for trade in openTrades:
        # find trade open time
        parts=trade['openTime'].split('.')
        dsS=f"{parts[0]}.{parts[1][:6]}Z"
        ds=datetime.datetime.strptime(dsS,'%Y-%m-%dT%H:%M:%S.%fZ')
        ts=ds.timestamp()

        if ts<oldestTime:
            oldestTime=ts
            oldestTrade=trade

    return oldestTrade

# Find the oldest unit size and reduce it by value amount.

# We find the oldest, then the lowest and reduce that way, but there is a hgh risk the reduction won't be
# the exact amount we want to reduce by. The goal of this is to shave off losses with each full winning
# trade, so predictability is absolutely critical to ensure micro losses are always minimal. This is a
# strategic approach to constantly reduce margin while still profiting as a whole.

def ReduceLotSize(relay,pair,val):
    try:
        oldestTrade=GetOldestTrade(relay,pair)
        if oldestTrade==None:
            return

        lossID=oldestTrade['id']
        lossIU=int(oldestTrade['currentUnits'])
        price=float(oldestTrade['price'])

        # Get the direction of the reduction trade right.

        if lossIU<0:
            runits=val
            Dir='short'
            Action='Buy'
        else:
            runits=val*-1
            Dir='long'
            Action='Sell'

        newOrder={}
        newOrder['OliverTwist']='Conditional ReduceBy'
        newOrder['Exchange']=relay.Order['Exchange']
        newOrder['Account']=relay.Order['Account']
        newOrder['Asset']=relay.Order['Asset']
        newOrder['Action']=Action.lower()
        if 'EnforceFIFO' in relay.Order:
            newOrder['EnforceFIFO']=relay.Order['EnforceFIFO']
        newOrder['Units']=runits
        newOrder['Ticket']=str(lossID)
        if 'OrderType' in relay.Order:
            newOrder['OrderType']=relay.Order['OrderType']
        else:
            newOrder['OrderType']='market'
        newOrder['Identity']=relay.Active['Identity']

        # Feed the new order to Relay
        result=relay.SendWebhook(newOrder)
        oid=relay.GetOrderID(result)
        if oid!=None:
            orderDetail=relay.GetOrderDetails(OrderID=oid)

            sprice=float(orderDetail[-1]['price'])
            rpl=float(orderDetail[-1]['pl'])
            relay.JRLog.Write(f"{lossID} -> {oid} Rduc {Dir}, {val}: {price:.5f} -> {sprice:5f}/{rpl:.5f}")
    except Exception as e:
        # Something broke or went horrible wrong
        relay.JRLog.Write(f"ReduceLotSize: {sys.exc_info()[-1].tb_lineno}/{str(e)}",stdOut=False)

# Process a single order and log it. Handles bot profit and loss.

def ProcessOrder(relay,cid,units,price,strikePrice,ds):
    try:
        # Get the action
        saction=relay.Order['SellAction'].lower()
        # Get the direction of the trade, long/short
        dir=relay.Order['Direction'].lower()

        # Build "strike" order. TakeProfit or StopLoss has been triggered
        newOrder={}
        newOrder['OliverTwist']='Conditional'
        newOrder['Exchange']=relay.Order['Exchange']
        newOrder['Account']=relay.Order['Account']
        newOrder['Asset']=relay.Order['Asset']
        newOrder['Action']=relay.Order['SellAction'].lower()
        if 'EnforceFIFO' in relay.Order:
            newOrder['EnforceFIFO']=relay.Order['EnforceFIFO']
        newOrder['Price']=str(strikePrice)
        if saction=='close':
            # Set trade polarity
            if dir=='long':
                newOrder['Units']='ALL'
            else:
                newOrder['Units']='-ALL'
        else:
            newOrder['Units']=relay.Order['Units']
            newOrder['Ticket']=str(cid)
        if 'OrderType' in relay.Order:
            newOrder['OrderType']=relay.Order['OrderType']
        else:
            newOrder['OrderType']='market'

        newOrder['Identity']=relay.Active['Identity']

        # Feed the new order to Relay
        result=relay.SendWebhook(newOrder)
        oid=relay.GetOrderID(result)
        if oid!=None:
            orderDetail=relay.GetOrderDetails(OrderID=oid)

            # find trade close time and  duration
            parts=orderDetail[0]['time'].split('.')
            deS=f"{parts[0]}.{parts[1][:6]}Z"
            de=datetime.datetime.strptime(deS,'%Y-%m-%dT%H:%M:%S.%fZ')
            duration=de-ds

            rpl=float(orderDetail[-1]['pl'])
            sprice=float(orderDetail[-1]['price'])

            # rpl is reported by broker. This is the actual profit/loss of trade.
            if rpl>=0:
                LogMSG=f"{oid} -> {cid} Prft {dir}, {units}: {price:.5f} -> {sprice:5f}/{abs(rpl):.5f}, {duration}"
            else:
                LogMSG=f"{oid} -> {cid} Loss {dir}, {units}: {price:.5f} -> {sprice:5f}/{abs(rpl):.5f}, {duration}"
            relay.JRLog.Write(f"{LogMSG}",stdOut=False)

            if rpl>0:
                # Don't reduce if we have a loss

                if 'ReduceBy' in relay.Active:
                    val=abs(int(relay.Active['ReduceBy']))
                    if val>0:
                        ReduceLotSize(relay,relay.Order['Asset'],val)
                elif 'ReduceBy' in relay.Order:
                    val=abs(int(relay.Order['ReduceBy']))
                    if val>0:
                        ReduceLotSize(relay,relay.Order['Asset'],val)

            # Order must be closed as it succedded
            newOrder['ID']=oid
            relay.WriteLedger(Order=newOrder,Response=None)
            return 'Delete'
        else:
            # Give OliverTwist a response
            relay.JRLog.Write(f"{id} -> {cid}: Order failed with {relay.GetFailedReason(result)}",stdOut=False)
            return 'Waiting'
    except Exception as e:
        # Something broke or went horrible wrong
        relay.JRLog.Write(f"CONDoanda {id}: {sys.exc_info()[-1].tb_lineno}/{str(e)}",stdOut=False)
        return 'Waiting'

###
### Main driver
###

def OrderProcessor(Orphan):
    # Use Relay to process and validate the order
    if type(Orphan['Order']) is dict:
        order=json.dumps(Orphan['Order'])
    else:
        order=Orphan['Order']

    relay=JRR.JackrabbitRelay(framework=Orphan['Framework'],payload=order,NoIdentityVerification=True,RaiseError=True)
    relay.JRLog.SetBaseName('OliverTwist')
    LogMSG=None

    try:
        # Check to see if order is still open and return current state
        # Handle OANDa's weird order id sequencing
        id=Orphan['ID']
        if 'cID' in Orphan:
            cid=Orphan['cID']
        else:
            # Figure out a way to handle when an order ID nolong exists.
            orderDetail=relay.GetOrderDetails(OrderID=Orphan['ID'])
            cid=orderDetail[-1]['id']

        # Get selling action
        saction=relay.Order['SellAction'].lower()

        # Get the direction of the trade, long/short
        dir=relay.Order['Direction'].lower()

        # Used to determin if the asset/poition has been found
        foundPrice=False

        # Check margin available. If no margin is left, force an unconditional stoploss of the oldest
        # position. Because multiple orders are processed simultaneously, it is possible for multiple orders
        # to be triggered. So we use the oldest reference to target the oldest position in the orderlist.
        # Its a creative way to avoid locking.

        MarginStrike=False
        if float(relay.Broker.Summary['account']['marginAvailable'])<=0:
            oldestTrade=GetOldestTrade(relay,relay.Order['Asset'])
            if oldestTrade!=None and oldestTrade['id']==cid:
                MarginStrike=True

        # Manage average and close extire position. MUST be checked every time
        if saction=='close':
            positions=relay.GetPositions()
            if positions!=None:
                for pos in positions:
                    if pos['instrument'].replace('_','/')==relay.Order['Asset']:
                        foundPrice=True
                        price=float(pos[dir]['averagePrice'])
                        units=abs(float(pos[dir]['units']))
                        break
        else:
            # Manage a single ticket
            if 'Price' in Orphan:
                price=float(Orphan['Price'])
                foundPrice=True
            else:
                # Brute force find the price.
                openTrades=relay.GetOpenTrades(symbol=relay.Order['Asset'])
                # no open trades
                if openTrades==[]:
                    # Fall through. No order matching the ID.
                    return 'Waiting'

                for cur in openTrades:
                    if cur['id']==cid:
                        # Get the fill price from the response entry
                        foundPrice=True
                        price=float(cur['price'])
                        units=abs(float(cur['currentUnits']))
                        break

        # Process the position
        if foundPrice==True:
            # We need to check TakeProfit and StopLoss. If one of them is hit, we need to build and order and backfeed it in
            # to Relay. It will place a new order.

            # Get Ticker
            ticker=relay.GetTicker(symbol=relay.Order['Asset'])

            # Check the spreads. It is possible that a fast moving market will pass this test, then drastically increase by
            # the time the position is closed.

            if 'Spread' in relay.Active:
                if ticker['Spread']>=float(relay.Active['Spread']):
                    s=f"excessivew spread, {relay.Order['SellAction'].lower()} delayed, {ticker['Spread']:.5f} > {relay.Active['Spread']:.5f}"
                    relay.JRLog.Write(f"{id} -> {cid}: {relay.Asset}/{units} {dir} {s}",stdOut=False)
                    return 'Waiting'

            if 'Spread' in relay.Order:
                if ticker['Spread']>=float(relay.Order['Spread']):
                    s=f"excessivew spread, {relay.Order['SellAction'].lower()} delayed, {ticker['Spread']:.5f} > {relay.Order['Spread']:.5f}"
                    relay.JRLog.Write(f"{id} -> {cid}: {relay.Asset}/{units} {dir} {s}",stdOut=False)
                    return 'Waiting'

            # Fsilsafe, in the WORST way possible. Do NOT leave a take profit out of the order. At this
            # stage, the whole thing is an absolute nightmare to fix. The is a very brutal way of dealing
            # with poor user choices.
            if 'TakeProfit' not in relay.Order:
                relay.Order['TakeProfit']='10p'
            # Calculate Take Profit
            tp=round(CalculatePriceExit(relay.Order,'TakeProfit',dir,price,relay.Broker.onePip),5)

            # Figure out StopLoss, if there is one
            if 'StopLoss' in relay.Order:
                sl=round(CalculatePriceExit(relay.Order,'StopLoss',dir,price,relay.Broker.onePip),5)

            # Get the "strikePrice". This handles both TakeProfit and StopLoss. It doesn't matter which as both
            # are processed the same way.

            StrikeHappened=False
            if dir=='long':
                if 'Diagnostics' in relay.Active:
                    relay.JRLog.Write(f"{id} -> {cid}: {relay.Asset}/{units} {dir} Price: {price}, Bid: {ticker['Bid']}/{ticker['Spread']} TP: {tp}/{relay.Order['TakeProfit']}, SL {sl}/{relay.Order['StopLoss']}",stdOut=False)

                if MarginStrike==True or (ticker['Bid']>(tp+ticker['Spread']) or ('StopLoss' in relay.Order and ticker['Bid']<(sl-ticker['Spread']))):
                    strikePrice=ticker['Bid']
                    StrikeHappened=True
            else:
                if 'Diagnostics' in relay.Active:
                    relay.JRLog.Write(f"{id} -> {cid}: {relay.Asset}/{abs(units)} {dir} Price: {price}, Ask: {ticker['Ask']}/{ticker['Spread']} TP: {tp}/{relay.Order['TakeProfit']}, SL {sl}/{relay.Order['StopLoss']}",stdOut=False)

                if MarginStrike==True or (ticker['Ask']<(tp-ticker['Spread']) or ('StopLoss' in relay.Order and ticker['Ask']>(sl+ticker['Spread']))):
                    strikePrice=ticker['Ask']
                    StrikeHappened=True

            if StrikeHappened==True:
                # find trade open time
                orderDetail=relay.GetOrderDetails(OrderID=Orphan['ID'])
                parts=orderDetail[0]['time'].split('.')
                dsS=f"{parts[0]}.{parts[1][:6]}Z"
                ds=datetime.datetime.strptime(dsS,'%Y-%m-%dT%H:%M:%S.%fZ')
                units=abs(float(orderDetail[-1]['units']))

                return ProcessOrder(relay,cid,units,price,strikePrice,ds)
            else:
                # Strike did not happen
                return 'Waiting'
        else:
            # Fall through. No order matching the ID.
            relay.JRLog.Write(f"{id} -> {cid}: Ticket not found on broker",stdOut=False)
            return 'Delete'
    except Exception as e:
        # Something broke or went horrible wrong
        relay.JRLog.Write(f"CONDoanda {id}: {sys.exc_info()[-1].tb_lineno}/{str(e)}",stdOut=False)
    return 'Waiting'
