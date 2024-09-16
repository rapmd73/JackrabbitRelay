#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# CCXT Conditional Orders - OliverTwist

# Jackrabbit Relay
# 2021 Copyright © Robert APM Darin
# All rights reserved unconditionally.

# This is the framework used by OliverTwist to process conditional/orphan orders.

# SellAction of Close sets Units to all and closes the entire position. Sell uses the CCXT ticket system.

import sys
#sys.path.append('/home/JackrabbitRelay2/Base/Library')
sys.path.append('/home/GitHub/JackrabbitRelay/Base/Library')
import os
import json
import datetime
import time

import JRRsupport
import JackrabbitRelay as JRR

JRLog=JRR.JackrabbitLog()
JRLog.SetBaseName('JackrabbitOliverTwist')

# Write this orphan list to disk

def WriteStorehouse(idx,OrphanList,deleteKey=None):
    DataDirectory='/home/JackrabbitRelay2/Data'
    OliverTwistData=DataDirectory+'/OliverTwist'
    Storehouse=f"{OliverTwistData}/{idx}.Storehouse"

    StartTime=datetime.datetime.now()

    fh=open(Storehouse,"w")
    for cur in OrphanList:
        if deleteKey==None or OrphanList[cur]['Key']!=deleteKey:
            fh.write(json.dumps(OrphanList[cur])+'\n')
    fh.close()

    JRLog.Write(f"{idx}/{len(OrphanList)} order(s) written in {str(datetime.datetime.now()-StartTime)} seconds")

# Read the complete list stored on disk, if it exists. Supports both orphans and conditionals.

def ReadStorehouse(idx=None,OrigOrphanList=None):
    # Required as the blobals are modified
    global OliverTwistLock
    global JRLog

    DataDirectory='/home/JackrabbitRelay2/Data'
    OliverTwistData=DataDirectory+'/OliverTwist'

    # Check if Directory exists
    JRRsupport.mkdir(OliverTwistData)

    if idx==None:
        Storehouse=None
        WorkingStorehouse=Receiver
    else:
        Storehouse=f"{OliverTwistData}/{idx}.Storehouse"
        WorkingStorehouse=Storehouse

    if OrigOrphanList==None:
        OrphanList={}
    else:
        OrphanList=OrigOrphanList.copy()

    rc=0
    if os.path.exists(WorkingStorehouse):
        buffer=JRRsupport.ReadFile(WorkingStorehouse).strip()
        if buffer!=None and buffer!='':
            Orphans=buffer.split('\n')

            # Remove empty lines
            while '' in Orphans:
                Orphans.remove('')

            for Entry in Orphans:
                # Force set InMotion to False
                Entry=Entry.strip()

                # Break down entry and set up memory locker
                try:
                    Orphan=Entry
                    while type(Orphan)==str:
                        Orphan=json.loads(Orphan)
                except:
                    JRLog.Write(f"Broken: {Entry}")
                    continue

                if 'Key' in Orphan and Orphan['Key'] in OrphanList:
                    continue

                if 'Order' in Orphan:
                    if type(Orphan['Order'])==str:
                        order=json.loads(Orphan['Order'])
                    else:
                        order=Orphan['Order']
                    order.pop('Identity',None)
                else:
                    JRLog.Write(f"Broken: {Entry}")
                    continue
                Orphan['Order']=order

                if 'Response' in Orphan:
                    if type(Orphan['Response'])==str:
                        resp=json.loads(Orphan['Response'])
                        Orphan['Response']=resp

                # Assign a key, if not already present.

                if 'Key' not in Orphan:
                    Orphan['Key']=f"{time.time()*10000000:.0f}.{GetID()}"

                # Only LIMIT orders are orphans, everything else is conditional

                try:
                    if 'OrderType' in order and 'limit' in order['OrderType'].lower():
                        Orphan['Class']='Orphan'
                    elif 'Conditional' in order:
                        Orphan['Class']='Conditional'
                except Exception as err:
                    JRLog.Write(f"Broken: {order}")
                    continue

                # Make sure price IS of orphan data

                if 'Price' not in Orphan:
                    if Orphan['Framework']=='oanda':
                        try:
                            relay=JRR.JackrabbitRelay(exchange=Orphan['Order']['Exchange'],account=Orphan['Order']['Account'],asset=Orphan['Order']['Asset'],RaiseError=True)
                            od=relay.GetOrderDetails(OrderID=Orphan['ID'])[-1]
                            Orphan['cID']=od['id']
                            Orphan['Price']=od['price']
                        except Exception as err:
                            pass
                    elif Orphan['Framework']=='mimic':
                        Orphan['Price']=Orphan['Response']['Price']
                    elif Orphan['Framework']=='ccxt':
                        Orphan['Price']=Orphan['Response']['price']

                OrphanList[Orphan['Key']]=Orphan
                rc+=1

#    if rc==0:
#        os.remove(WorkingStorehouse)
    return OrphanList

# Get the hiest and lowest priced orders.

def GetHighestLowest(OrphanList):
    hPrice=float('-inf')
    lPrice=float('inf')
    hTrade=None
    lTrade=None

    for cur in OrphanList:
        order=OrphanList[cur]
        # Only concider conditional orders...
        if order['Class'].lower()!='conditional':
            continue

        # Skip oders without a price. We could pull order details, but that is in ReadStorehouse()
        if 'Price' not in order:
            continue

        price=float(order['Price'])
        if price<lPrice:
            lTrade=order
            lPrice=price
        if price>hPrice:
            hTrade=order
            hPrice=price

    return hTrade,lTrade

# Calculate Price Exit

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

# Process a single order and log it. Handles bot profit and loss.

def ProcessOrder(relay,Order,cid,amount,price,strikePrice,ds):
    try:
#        print("PO A")

        # Get the action
        saction=Order['SellAction'].lower()
        # Get the direction of the trade, long/short
        dir=Order['Direction'].lower()

        # Build "strike" order. TakeProfit or StopLoss has been triggered
        newOrder={}
        newOrder['OliverTwist']='Conditional'
        newOrder['Exchange']=Order['Exchange']
        newOrder['Account']=Order['Account']
        newOrder['Market']=Order['Market']
        newOrder['Asset']=Order['Asset']
        newOrder['Action']=Order['SellAction']
        newOrder['Price']=str(strikePrice)
        newOrder['Base']=str(amount)
        if 'OrderType' in Order:
            newOrder['OrderType']=Order['OrderType']
        else:
            newOrder['OrderType']='market'

        newOrder['Identity']=relay.Active['Identity']

#        print("PO B")
        # Feed the new order to Relay
        result=relay.SendWebhook(newOrder)
        oid=relay.GetOrderID(result)
        if oid!=None:
            resp=relay.GetOrderDetails(id=oid,symbol=Order['Asset'])
            # Order must be closed as it succedded
            newOrder['ID']=oid
            sprice=float(resp['price'])

            # find trade close time and  duration
            parts=resp['datetime'].split('.')
            deS=f"{parts[0]}.{parts[1][:6]}Z".replace('ZZ','Z').replace('T',' ')
            de=datetime.datetime.strptime(deS,'%Y-%m-%d %H:%M:%S.%fZ')
            duration=de-ds

            rpl=0
            if dir=='long':
                rpl=round((abs(amount)*sprice)-(abs(amount)*price),8)
            else:
                rpl=round((abs(amount)*price)-(abs(amount)*sprice),8)

#            print("PO C")
            # rpl is reported by broker. This is the actual profit/loss of trade.
            if rpl>=0:
                LogMSG=f"{oid} -> {cid} Prft {dir}, {amount:.8f}: {price:.8f} -> {sprice:8f}/{abs(rpl):.8f}, {duration}"
            else:
                LogMSG=f"{oid} -> {cid} Loss {dir}, {amount:.8f}: {price:.8f} -> {sprice:8f}/{abs(rpl):.8f}, {duration}"
            relay.JRLog.Write(f"{LogMSG}")
            relay.WriteLedger(Order=newOrder,Response=resp)

            return True
        else:
            # Give OliverTwist a response
            reason=relay.GetFailedReason(result).lower()
            relay.JRLog.Write(f"{cid}: Order failed with {reason}")
            # If there isnt enough balance, remove the order
            if 'insufficient balance' in reason \
            or 'not enough to sell/close' in reason \
            or 'not enough balance' in reason:
                return True
            return False
    except Exception as e:
        # Something broke or went horrible wrong
        relay.JRLog.Write(f"CONDccxt PO {id}: {sys.exc_info()[-1].tb_lineno}/{str(e)}")
        return False

# Check to see of the order is in profit.
# return the key of the seccessful order, otherwise return None

def CheckTakeProfit(relay,Orphan,lowestTrade):
    try:
#        print("CTP A")

        Order=Orphan['Order']

        # Check to see if order is still open and return current state
        # Handle OANDa's weird order id sequencing
        id=Orphan['ID']

        # Get selling action
        saction=Order['SellAction'].lower()

        if type(Orphan['Response']) is str:
            Orphan['Response']=json.loads(Orphan['Response'])
        oDetail=Orphan['Response']

        # Manage average and close extire position. Average and price are the same.
        price=float(Orphan['Price'])
        amount=float(oDetail['amount'])
        cid=id      # This is the ID of the original order

        # Get the direction of the trade, long/short
        dir=Order['Direction'].lower()

#        print("CTP B")
        # Get Ticker
        ticker=relay.GetTicker(symbol=Order['Asset'])

        # Check the spreads. It is possible that a fast moving market will pass this test, then drastically increase by
        # the time the position is closed.

        if 'Spread' in relay.Active:
            if ticker['Spread']>=float(relay.Active['Spread']):
                s=f"excessivew spread, {Order['SellAction'].lower()} delayed, {ticker['Spread']:.5f} > {relay.Active['Spread']:.5f}"
                relay.JRLog.Write(f"{id} -> {cid}: {relay.Asset}/{units} {dir} {s}")
                return None

        if 'Spread' in Order:
            if ticker['Spread']>=float(Order['Spread']):
                s=f"excessivew spread, {Order['SellAction'].lower()} delayed, {ticker['Spread']:.5f} > {Order['Spread']:.5f}"
                relay.JRLog.Write(f"{id} -> {cid}: {relay.Asset}/{units} {dir} {s}")
                return None

#        print("CTP C")
        # Fsilsafe, in the WORST way possible. Do NOT leave a take profit out of the order. At this
        # stage, the whole thing is an absolute nightmare to fix. The is a very brutal way of dealing
        # with poor user choices.
        if 'TakeProfit' not in Order:
            Order['TakeProfit']='2%'
        # Calculate Take Profit
        tp=round(CalculatePriceExit(Order,'TakeProfit',dir,price),8)

        # Get the "strikePrice". This handles both TakeProfit.

#        print("CTP D")
        StrikeHappened=False
        if dir=='long':
            if 'Diagnostics' in relay.Active:
                relay.JRLog.Write(f"{id} -> {cid}: {relay.Asset}/{units} {dir} Price: {price}, Bid: {ticker['Bid']}/{ticker['Spread']} TP: {tp}/{Order['TakeProfit']}, SL {sl}/{Order['StopLoss']}")

            if ticker['Bid']>(tp+ticker['Spread']):
                strikePrice=ticker['Bid']
                StrikeHappened=True
        else:
            if 'Diagnostics' in relay.Active:
                relay.JRLog.Write(f"{id} -> {cid}: {relay.Asset}/{abs(units)} {dir} Price: {price}, Ask: {ticker['Ask']}/{ticker['Spread']} TP: {tp}/{Order['TakeProfit']}, SL {sl}/{Order['StopLoss']}")

            if ticker['Ask']<(tp-ticker['Spread']):
                strikePrice=ticker['Ask']
                StrikeHappened=True

#        print("CTP E")
        if StrikeHappened==True:
            # find trade open time
            parts=oDetail['datetime'].split('.')
            dsS=f"{parts[0]}.{parts[1][:6]}Z".replace('ZZ','Z').replace('T',' ')
            ds=datetime.datetime.strptime(dsS,'%Y-%m-%d %H:%M:%S.%fZ')

#            if abs(bal)>abs(amount):
            res=ProcessOrder(relay,Order,cid,amount,price,strikePrice,ds)
            if type(res) is bool and res==True:
               return Orphan['Key']
            elif type(res)==str and res=='PURGE':
                return True
            return None
        else:
            # Strike did not happen
            return None
    except Exception as e:
        # Something broke or went horrible wrong
        relay.JRLog.Write(f"CONDccxt CheckTakeProfit {id}: {sys.exc_info()[-1].tb_lineno}/{str(e)}")
    return None

# Check to see of the order is in loss.

def CheckStopLoss(relay,Orphan):
    try:
#        print("CSL A")

        Order=Orphan['Order']

        # if there is not a stoploss, dont waste cycles...
        if 'StopLoss' not in Order:
#            print("CSL A1")
            return None

        # Check to see if order is still open and return current state
        # Handle OANDa's weird order id sequencing
        id=Orphan['ID']

        # Get selling action
        saction=Order['SellAction'].lower()

        if type(Orphan['Response']) is str:
            Orphan['Response']=json.loads(Orphan['Response'])
        oDetail=Orphan['Response']

#        print("CSL B")
        # Manage average and close extire position. Average and price are the same.
        price=float(Orphan['Price'])
        amount=float(oDetail['amount'])
        cid=id      # This is the ID of the original order

        # Get the direction of the trade, long/short
        dir=Order['Direction'].lower()

        # We need to check StopLoss. If one of them is hit, we need to build and order and backfeed it in
        # to Relay. It will place a new order.

        # Get Ticker
        ticker=relay.GetTicker(symbol=Order['Asset'])

#        print("CSL C")
        sl=round(CalculatePriceExit(Order,'StopLoss',dir,price),8)

        # Get the "strikePrice". This handles StopLoss.

#        print("CSL D")
        StrikeHappened=False
        if dir=='long':
            if 'Diagnostics' in relay.Active:
                relay.JRLog.Write(f"{id} -> {cid}: {relay.Asset}/{units} {dir} Price: {price}, Bid: {ticker['Bid']}/{ticker['Spread']} TP: {tp}/{Order['TakeProfit']}, SL {sl}/{Order['StopLoss']}")

            if ticker['Bid']<(sl-ticker['Spread']):
                strikePrice=ticker['Bid']
                StrikeHappened=True
        else:
            if 'Diagnostics' in relay.Active:
                relay.JRLog.Write(f"{id} -> {cid}: {relay.Asset}/{abs(units)} {dir} Price: {price}, Ask: {ticker['Ask']}/{ticker['Spread']} TP: {tp}/{Order['TakeProfit']}, SL {sl}/{Order['StopLoss']}")

            if ticker['Ask']>(sl+ticker['Spread']):
                strikePrice=ticker['Ask']
                StrikeHappened=True

#        print("CSL E")
        if StrikeHappened==True:
            # find trade open time
            parts=oDetail['datetime'].split('.')
            dsS=f"{parts[0]}.{parts[1][:6]}Z".replace('ZZ','Z').replace('T',' ')
            ds=datetime.datetime.strptime(dsS,'%Y-%m-%d %H:%M:%S.%fZ')

            res=ProcessOrder(relay,Order,cid,amount,price,strikePrice,ds)
            if res:
                return Orphan['Key']
            return None
        else:
            # Strike did not happen
            return None
    except Exception as e:
        # Something broke or went horrible wrong
        relay.JRLog.Write(f"CONDccxt CheckStopLoss {id}: {sys.exc_info()[-1].tb_lineno}/{str(e)}")
    return None

###
### Process the IDX
###

# At this point, we only have the storehouse we are processing... We'll have to figure out everything else,
# including handling orphan (limit) or conditional orders.

# Arguments are the exact same as those of ProcessOrphan, for lock IDs

def OrderProcessor(osh):
    StartTime=datetime.datetime.now()

#    print("OP A")

    # Split off the parts we need.
    idx=osh['IDX']
    exchange,account,asset=idx.split('.')

    # Open channel to Relay
    relay=JRR.JackrabbitRelay(exchange=exchange,account=account,asset=asset,RaiseError=True)
    relay.JRLog.SetBaseName('OliverTwist')

    try:
        OrphanList=ReadStorehouse(idx=idx)
        if len(OrphanList)==0:
            return 'Waiting'

        # Process conditional orders

        # For long positions, highestTrade will be closest to take profit, lowest for stop loss
        # For short positions, lowestestTrade will be closest to take profit, highest for stop loss

        highestTrade,lowestTrade=GetHighestLowest(OrphanList)

        # Now that we have the trades we need to actually check, we convert then to JSOM

        # Make sure we are working with Python dictionaries
        if type(highestTrade['Order']) is not dict:
            highestTrade['Order']=json.loads(highestTrade['Order'])
        if type(lowestTrade['Order']) is not dict:
            lowestTrade['Order']=json.loads(lowestTrade['Order'])

        # Check take profit
        if highestTrade['Order']['Direction'].lower()=='long':
            DeleteKey=CheckTakeProfit(relay,lowestTrade,lowestTrade)
        else:
            DeleteKey=CheckTakeProfit(relay,highestTrade,highestTrade)

        # Delete the order from the Storehouse.
        if DeleteKey!=None:
            WriteStorehouse(idx,OrphanList,deleteKey=DeleteKey)

#        print("OP B")
        # Check stop loss. If a margin strike occured, force the stoploss
        if lowestTrade['Order']['Direction'].lower()=='long':
            DeleteKey=CheckStopLoss(relay,lowestTrade)
        else:
            DeleteKey=CheckStopLoss(relay,highestTrade)

        # Delete the order from the Storehouse.
        if DeleteKey!=None:
            WriteStorehouse(idx,OrphanList,deleteKey=DeleteKey)

        #
        # Handle LIMIT orders.... one by one.
        #

#        print("OP C",asset)
        # Check to see if order is still open and return current state
        openOrders=relay.GetOpenOrders(symbol=asset)
        if openOrders!=None and openOrders!=[]:
            for order in list(OrphanList.keys()):
                Orphan=Orphanlist[order]
                id=Orphan['ID']

                if Orphan['Class'].lower()!='orphan':
                    continue

                found=False
                for cur in openOrders:
                    if cur['id']==id:
                        found=True
                        break

                # Order must be closed
                if not found:
                    WriteStorehouse(idx,OrphanList,deleteKey=Orphan['Key'])
                    relay.WriteLedger(Order=Orphan,Response=None)
                    OrphanList.pop(Orphan['Key'],None)

    except Exception as err:
        relay.JRLog.Write(f"OT CCXT Broke {sys.exc_info()[-1].tb_lineno}: {idx}, {err}",stdOut=False)

    EndTime=datetime.datetime.now()
    JRLog.Write(f"OP CCXT Elapsed {idx}/{len(OrphanList)}: {EndTime-StartTime} seconds")

    return 'Waiting'
