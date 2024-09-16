#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# OANDA Conditional Orders - OliverTwist

# Jackrabbit Relay
# 2021 Copyright © Robert APM Darin
# All rights reserved unconditionally.

# This is the framework used by OliverTwist to process conditional/orphan orders.

# SellAction of Close sets Units to all and closes the entire position. Sell uses the Oanda ticket system.

import sys
#sys.path.append('/home/JackrabbitRelay2/Base/Library')
sys.path.append('/home/GitHub/JackrabbitRelay/Base/Library')
import os
import json
import datetime
import time

import JRRsupport
import JackrabbitRelay as JRR

# Write this orphan list to disk

JRLog=JRR.JackrabbitLog()
JRLog.SetBaseName('JackrabbitOliverTwist')

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
                    JRLog.Write(f"Broken: {Entry}",stdOut=False)
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
                    JRLog.Write(f"Broken: {Entry}",stdOut=False)
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

# Find the oldest unit size and reduce it by value amount.

# We find the oldest, then the lowest and reduce that way, but there is a hgh risk the reduction won't be
# the exact amount we want to reduce by. The goal of this is to shave off losses with each full winning
# trade, so predictability is absolutely critical to ensure micro losses are always minimal. This is a
# strategic approach to constantly reduce margin while still profiting as a whole.

def ReduceLotSize(relay,oldestTrade=None,val=1):
    try:
        relay.JRLog.Write(f"RLS A: {json.dumps(oldestTrade)}")
        if oldestTrade==None:
            return
        Order=lowestTrade['Order']
        pair=Order['Asset']

        # Verify the trade exists. If it doesn't, delete the key
        if not TradeExists(relay,oldestTrade['ID'],pair):
            print("RLS B",oldestTrade['id'])
            return

        lossID=oldestTrade['ID']

        # Get the direction of the reduction trade right.

        if lossIU<0:
            runits=val
            Dir='short'
            Action='Buy'
        else:
            runits=val*-1
            Dir='long'
            Action='Sell'

        print("RLS C")
        newOrder={}
        newOrder['OliverTwist']='Conditional ReduceBy'
        newOrder['Exchange']=Order['Exchange']
        newOrder['Account']=Order['Account']
        newOrder['Asset']=Order['Asset']
        newOrder['Action']=Action.lower()
        if 'EnforceFIFO' in Order:
            newOrder['EnforceFIFO']=Order['EnforceFIFO']
        newOrder['Units']=runits
        newOrder['Ticket']=str(lossID)
        if 'OrderType' in Order:
            newOrder['OrderType']=Order['OrderType']
        else:
            newOrder['OrderType']='market'
        newOrder['Identity']=relay.Active['Identity']

#        print("RLS D")
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
        relay.JRLog.Write(f"ReduceLotSize: {sys.exc_info()[-1].tb_lineno}/{str(e)}")

# Process a single order and log it. Handles bot profit and loss.

def ProcessOrder(relay,Order,cid,units,price,strikePrice,ds,lowestOrder=None):
    try:
        # Get the action
        saction=Order['SellAction'].lower()
        # Get the direction of the trade, long/short
        dir=Order['Direction'].lower()

        # Build "strike" order. TakeProfit or StopLoss has been triggered
        newOrder={}
        newOrder['OliverTwist']='Conditional'
        newOrder['Exchange']=Order['Exchange']
        newOrder['Account']=Order['Account']
        newOrder['Asset']=Order['Asset']
        newOrder['Action']=Order['SellAction'].lower()
        if 'EnforceFIFO' in Order:
            newOrder['EnforceFIFO']=Order['EnforceFIFO']
        newOrder['Price']=str(strikePrice)
        if saction=='close':
            # Set trade polarity
            if dir=='long':
                newOrder['Units']='ALL'
            else:
                newOrder['Units']='-ALL'
        else:
            newOrder['Units']=Order['Units']
            newOrder['Ticket']=str(cid)
        if 'OrderType' in Order:
            newOrder['OrderType']=Order['OrderType']
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
            relay.JRLog.Write(f"{LogMSG}")

            relay.JRLog.Write(f"RPL: {rpl}")
            if rpl>0:
                # Don't reduce if we have a loss

                if 'ReduceBy' in relay.Active:
                    val=abs(int(relay.Active['ReduceBy']))
                    if val>0:
                        ReduceLotSize(relay,lowestOrder,val)
                elif 'ReduceBy' in Order:
                    val=abs(int(Order['ReduceBy']))
                    if val>0:
                        ReduceLotSize(relay,lowestOrder,val)

            # Order must be closed as it succedded
            newOrder['ID']=oid

            # Write out the ledger entry
            relay.WriteLedger(Order=newOrder,Response=None)

            return
        else:
            # Give OliverTwist a response
            relay.JRLog.Write(f"{id} -> {cid}: Order failed with {relay.GetFailedReason(result)}")
            return
    except Exception as e:
        # Something broke or went horrible wrong
        relay.JRLog.Write(f"CONDoanda {id}: {sys.exc_info()[-1].tb_lineno}/{str(e)}",stdOut=False)
        return

# Make sure the trade exists on the broker.

def TradeExists(relay,id,asset):
    try:
        openTrades=relay.GetOpenTrades(symbol=asset)
        # no open trades
        if openTrades==[]:
            return False

        for cur in openTrades:
            if cur['id']==id:
                return True
    except Exception as e:
        # Something broke or went horrible wrong
        relay.JRLog.Write(f"CONDoanda TradeExists {id}: {sys.exc_info()[-1].tb_lineno}/{str(e)}")

    return False

# Check to see of the order is in profit.
# return the key of the seccessful order, otherwise return None

def CheckTakeProfit(relay,Orphan,lowestTrade):
    try:
        Order=Orphan['Order']

        # Check to see if order is still open and return current state
        # Handle OANDa's weird order id sequencing
        id=Orphan['ID']
        if 'cID' in Orphan:
            cid=Orphan['cID']
        else:
            # Figure out a way to handle when an order ID nolong exists.
            orderDetail=relay.GetOrderDetails(OrderID=Orphan['ID'])
            cid=orderDetail[-1]['id']

        # Verify the trade exists. If it doesn't, delete the key
        if not TradeExists(relay,cid,Order['Asset']):
#            print("CPT ",Orphan)
            return Orphan['Key']

        # Get selling action
        saction=Order['SellAction'].lower()

        # Get the direction of the trade, long/short
        dir=Order['Direction'].lower()

#        print("CTP A",dir,id,cid)

        # Has to be pulled EVERYTIME
        # Manage average and close extire position. MUST be checked every time
        if saction=='close':
            positions=relay.GetPositions()
            if positions!=None:
                for pos in positions:
                    if pos['instrument'].replace('_','/')==Order['Asset']:
                        foundPrice=True
                        price=float(pos[dir]['averagePrice'])
                        units=abs(float(pos[dir]['units']))
                        break
        else:
            price=float(Orphan['Price'])

            # We need to check TakeProfit and StopLoss. If one of them is hit, we need to build and order and backfeed it in
            # to Relay. It will place a new order.

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

        # Fsilsafe, in the WORST way possible. Do NOT leave a take profit out of the order. At this
        # stage, the whole thing is an absolute nightmare to fix. The is a very brutal way of dealing
        # with poor user choices.
        if 'TakeProfit' not in Order:
            Order['TakeProfit']='10p'
        # Calculate Take Profit
        tp=round(CalculatePriceExit(Order,'TakeProfit',dir,price,relay.Broker.onePip),5)

        # Get the "strikePrice". This handles both TakeProfit.

        StrikeHappened=False
        if dir=='long':
            if 'Diagnostics' in relay.Active:
                relay.JRLog.Write(f"{id} -> {cid}: {relay.Asset} {dir} Price: {price}, Bid: {ticker['Bid']}/{ticker['Spread']} TP: {tp}/{Order['TakeProfit']}")

            if ticker['Bid']>(tp+ticker['Spread']):
                strikePrice=ticker['Bid']
                StrikeHappened=True
        else:
            if 'Diagnostics' in relay.Active:
                relay.JRLog.Write(f"{id} -> {cid}: {relay.Asset}/{abs(units)} {dir} Price: {price}, Ask: {ticker['Ask']}/{ticker['Spread']} TP: {tp}/{Order['TakeProfit']}, SL {sl}/{Order['StopLoss']}")

#            print(f"CTP C {id} -> {cid}: {relay.Asset} {dir} Price: {ticker['Ask']}, TP: {tp-ticker['Spread']:.5f} {price}")
#            print("CTP D",ticker['Ask'],(tp-ticker['Spread']),price)

            if ticker['Ask']<(tp-ticker['Spread']):
                strikePrice=ticker['Ask']
                StrikeHappened=True

#        print("CTP B",StrikeHappened)

        if StrikeHappened==True:
            # find trade open time
            orderDetail=relay.GetOrderDetails(OrderID=Orphan['ID'])
            parts=orderDetail[0]['time'].split('.')
            dsS=f"{parts[0]}.{parts[1][:6]}Z"
            ds=datetime.datetime.strptime(dsS,'%Y-%m-%dT%H:%M:%S.%fZ')
            units=abs(float(orderDetail[-1]['units']))

            ProcessOrder(relay,Order,cid,units,price,strikePrice,ds,lowestOrder=lowestTrade)
            return Orphan['Key']
        else:
            # Strike did not happen
            return None
    except Exception as e:
        # Something broke or went horrible wrong
        relay.JRLog.Write(f"CONDoanda CheckTakeProfit {id}: {sys.exc_info()[-1].tb_lineno}/{str(e)}")
    return None

# Check to see of the order is in loss.

def CheckStopLoss(relay,Orphan,MarginStrike):
    try:
        Order=Orphan['Order']

        # if there is not a stoploss, dont waste cycles...
        if 'StopLoss' not in Order:
            return None

        # Check to see if order is still open and return current state
        # Handle OANDa's weird order id sequencing
        id=Orphan['ID']
        if 'cID' in Orphan:
            cid=Orphan['cID']
        else:
            # Figure out a way to handle when an order ID nolong exists.
            orderDetail=relay.GetOrderDetails(OrderID=Orphan['ID'])
            cid=orderDetail[-1]['id']

        # Verify the trade exists. If it doesn't, delete the key
        if not TradeExists(relay,cid,Order['Asset']):
            return Orphan['Key']

        # Get selling action
        saction=Order['SellAction'].lower()

        # Get the direction of the trade, long/short
        dir=Order['Direction'].lower()

        # Has to be pulled EVERYTIME
        # Manage average and close extire position. MUST be checked every time
        if saction=='close':
            positions=relay.GetPositions()
            if positions!=None:
                for pos in positions:
                    if pos['instrument'].replace('_','/')==Order['Asset']:
                        foundPrice=True
                        price=float(pos[dir]['averagePrice'])
                        units=abs(float(pos[dir]['units']))
                        break
        else:
            price=float(Orphan['Price'])

        # We need to check StopLoss. If one of them is hit, we need to build and order and backfeed it in
        # to Relay. It will place a new order.

        # Get Ticker
        ticker=relay.GetTicker(symbol=Order['Asset'])

        sl=round(CalculatePriceExit(Order,'StopLoss',dir,price,relay.Broker.onePip),5)

        # Get the "strikePrice". This handles StopLoss.

        StrikeHappened=False
        if dir=='long':
            if 'Diagnostics' in relay.Active:
                relay.JRLog.Write(f"{id} -> {cid}: {relay.Asset}/{units} {dir} Price: {price}, Bid: {ticker['Bid']}/{ticker['Spread']} SL {sl}/{Order['StopLoss']}")

            if MarginStrike or ticker['Bid']<(sl-ticker['Spread']):
                strikePrice=ticker['Bid']
                StrikeHappened=True
        else:
            if 'Diagnostics' in relay.Active:
                relay.JRLog.Write(f"{id} -> {cid}: {relay.Asset}/{abs(units)} {dir} Price: {price}, Ask: {ticker['Ask']}/{ticker['Spread']} SL {sl}/{Order['StopLoss']}")

            if MarginStrike or ticker['Ask']>(sl+ticker['Spread']):
                strikePrice=ticker['Ask']
                StrikeHappened=True

        if StrikeHappened==True:
            # find trade open time
            orderDetail=relay.GetOrderDetails(OrderID=Orphan['ID'])
            parts=orderDetail[0]['time'].split('.')
            dsS=f"{parts[0]}.{parts[1][:6]}Z"
            ds=datetime.datetime.strptime(dsS,'%Y-%m-%dT%H:%M:%S.%fZ')
            units=abs(float(orderDetail[-1]['units']))

            ProcessOrder(relay,Order,cid,units,price,strikePrice,ds)
            return Orphan['Key']
        else:
            # Strike did not happen
            return None
    except Exception as e:
        # Something broke or went horrible wrong
        relay.JRLog.Write(f"CONDoanda CheckStopLoss {id}: {sys.exc_info()[-1].tb_lineno}/{str(e)}",stdOut=False)
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
#    print("OP B",idx)
    exchange,account,asset=idx.split('.')

    # Open channel to Relay
    relay=JRR.JackrabbitRelay(exchange=exchange,account=account,asset=asset,RaiseError=True)
    relay.JRLog.SetBaseName('OliverTwist')

    # Get the lock ID correct for Storehouse (sh)
    shLock=JRRsupport.Locker(f"OliverTwist.{idx}",ID=f"{idx}.{osh['lID']}")

    # Locking is not really needed if OliverTwist is the only player in town, but we can't assume that as
    # there might be some other program that wants this storehouse, so we play it safe.

#    shLock.Lock()
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

        # Check margin available and take a stoploss if needed
        MarginStrike=False
        if float(relay.Broker.Summary['account']['marginAvailable'])<=0:
            MarginStrike=True

        # Take profit starts at the lowest order priced and works upward for long.

        # Check take profit
#        print("OP C1",highestTrade)
#        print("OP C2",lowestTrade)
        if lowestTrade['Order']['Direction'].lower()=='long':
            DeleteKey=CheckTakeProfit(relay,lowestTrade,highestTrade)
        else:
            DeleteKey=CheckTakeProfit(relay,highestTrade,lowestTrade)

        # Delete the order from the Storehouse.
        if DeleteKey!=None:
            WriteStorehouse(idx,OrphanList,deleteKey=DeleteKey)

        # Check stop loss. If a margin strike occured, force the stoploss
#        print("OP D")
        if lowestTrade['Order']['Direction'].lower()=='long':
            DeleteKey=CheckStopLoss(relay,lowestestTrade,MarginStrike)
        else:
            DeleteKey=CheckStopLoss(relay,highestTrade,MarginStrike)

        # Delete the order from the Storehouse.
        if DeleteKey!=None:
            WriteStorehouse(idx,OrphanList,deleteKey=DeleteKey)

        #
        # Handle LIMIT orders.... one by one.
        #

        # Check to see if order is still open and return current state
        openOrders=relay.GetOpenOrders(symbol=asset)
        if openOrders!=None and openOrders!=[]:
            for order in list(OrphanList.keys()):
                if Orphan['Class'].lower()!='orphan':
                    continue
                foumd=False
                Orphan=Orphanlist[order]
                id=Orphan['ID']
                cid=Orphan['cID']
                for cur in openOrders:
                    if cur['id']==id or cur['id']==cid:
                        found=True
                        break

                # Order must be closed
                WriteStorehouse(idx,OrphanList,deleteKey=Orphan['Key'])
                relay.WriteLedger(Order=Orphan,Response=None)
                OrphanList.pop(Orphan['Key'],None)

    except Exception as err:
        relay.JRLog.Write(f"OT OANDA Broke {sys.exc_info()[-1].tb_lineno}: {idx}, {err}")
#    shLock.Unlock()

    EndTime=datetime.datetime.now()
    JRLog.Write(f"OP OANDA Elapsed {idx}/{len(OrphanList)}: {EndTime-StartTime} seconds")

    return 'Waiting'
