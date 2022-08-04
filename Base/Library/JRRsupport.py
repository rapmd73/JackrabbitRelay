#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Jackrabbit Relay
# 2021 Copyright © Robert APM Darin
# All rights reserved unconditionally.

import sys
sys.path.append('/home/JackrabbitRelay/Base/Library')
import os
import pathlib
import time
import json
import requests

import JRRconfig
import JRRapi
import JRRlog

# Reusable file locks, using atomic operations
# NOT suitable for distributed systems or 
# Windows. Linux ONLY
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

    # Try to get a lock on the file

    def TestLock(self):
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

        isLocked=False
        try:
            os.rename(tn,self.filename)
        except:
            pass
        else:
            isLocked=True
        return isLocked

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

# Doubly lisked list with sentinel for bidirectional intertion
#
# Comparison example
#def compare(node1,d2):
#    d1=node1.GetData()
#
#    if int(d2)<int(d1):
#        return 1
#    elif int(d2)>int(d1):
#        return -1
#    else: #if int(d2)==int(d1):
#        return 0
#
# Driver example
#
#if __name__=='__main__':
#    dlist=DList()
#    x=1000
#    l=10000 #random.randrange(1000,9999)
#    for i in range(l):
#        x+=1 #=random.randrange(1000,9999)
#        dlist.insert(x,compare)
#
#    dlist.list()
#    print(dlist.len())
#    print("")
#
#    for i in range(5):
#        x=random.randrange(1,dlist.Length()-1)
#        c=dlist.GetHead()
#        while x>0:
#            x-=1
#            if c!=None:
#                c=c.GetNext()
#        dlist.dump(dlist.find(c.GetData(),compare))
#    print("")
#
#    for i in range(2000):
#        x=random.randrange(1,dlist.Length()-1)
#        c=dlist.GetHead()
#        while x>0:
#            x-=1
#            if c!=None:
#                c=c.GetNext()
#        if c!=None:
#            dlist.delete(c.GetData(),compare)
#    print("")
#    dlist.list()
#    print(dlist.len())
#    print("")

class DListNode:
    def __init__(self,data=None,parent=None,prev=None,next=None,left=None,right=None):
        self.data=data
        self.prev=prev
        self.next=next

    def GetData(self):
        return self.data

    def SetData(self,data):
        self.data=data

    def GetPrev(self):
        return self.prev

    def SetPrev(self,prev):
        self.prev=prev

    def GetNext(self):
        return self.next

    def SetNext(self,next):
        self.next=next

class DList:
    def __init__(self):
        self.head=None
        self.tail=None
        self.sentinel=None
        self.size=0

    def GetHead(self):
        return self.head

    def SetHead(self,head):
        self.head=head

    def GetTail(self):
        return self.tail

    def SetTail(self,tail):
        self.tail=tail

    def Length(self):
        return self.size

    def find(self,data,compare=None):
        if self.head:
            if compare(self.head,data)==0:
                return self.head
            elif compare(self.tail,data)==0:
                return self.tail
            else:
                if self.sentinel==None:
                    self.sentinel=self.head
                res=compare(self.sentinel,data)
                if res>0:
                    while self.sentinel.GetNext()!=None and compare(self.sentinel,data)>0:
                        self.sentinel=self.sentinel.GetNext()
                    if compare(self.sentinel,data)==0:
                        return self.sentinel
                    else:
                        return None
                elif res<0:
                    while self.sentinel.GetPrev()!=None and compare(self.sentinel,data)<0:
                        self.sentinel=self.sentinel.GetPrev()
                    if compare(self.sentinel,data)==0:
                        return self.sentinel
                    else:
                        return None
                else: # res==0
                    return self.sentinel
        else:
            return None

    def insert(self,data,compare=None):
        if self.head:
            # Initialize sentinel ptr. This will move according to direction of
            # comparisons. Will befaster then always starting at head of list.

            # New head of list test
            if compare(self.head,data)<0:
                newNode=DListNode(data)
                newNode.SetNext(self.head)
                newNode.GetNext().SetPrev(newNode)
                self.head=newNode
                self.size+=1
                return
            # New tail of list test
            elif compare(self.tail,data)>0:
                newNode=DListNode(data)
                newNode.SetPrev(self.tail)
                newNode.GetPrev().SetNext(newNode)
                self.tail=newNode
                self.size+=1
                return
            # Add to the middle based on sentinel for locating
            else:
                if self.sentinel==None:
                    self.sentinel=self.head
                res=compare(self.sentinel,data)
                if res>0:
                    while self.sentinel.GetNext()!=None and compare(self.sentinel.GetNext(),data)>0:
                        self.sentinel=self.sentinel.GetNext()
                    newNode=DListNode(data)
                    newNode.SetNext(self.sentinel.GetNext())
                    if self.sentinel.GetNext()!=None:
                        newNode.GetNext().SetPrev(newNode)
                    self.sentinel.SetNext(newNode)
                    newNode.SetPrev(self.sentinel)
                    self.size+=1
                    return
                elif res<0:
                    while self.sentinel.GetPrev()!=None and compare(self.sentinel.GetPrev(),data)<0:
                        self.sentinel=self.sentinel.GetPrev()
                    newNode=DListNode(data)
                    newNode.SetPrev(self.sentinel.GetPrev())
                    if self.sentinel.GetPrev()!=None:
                        newNode.GetPrev().SetNext(newNode)
                    self.sentinel.SetPrev(newNode)
                    newNode.SetNext(self.sentinel)
                    self.size+=1
                    return
        else:
            # Create list with new node
            newNode=DListNode(data)
            self.head=newNode
            self.tail=newNode
            self.sintinel=self.head
            self.size+=1
            return

    def delete(self,data,compare=None):
        if self.head:
            node=self.find(data,compare)
            # Not in list
            if node==None:
                return

            if node==self.head:
                n=self.head.GetNext()
                n.SetPrev(None)
                self.head=n
                self.size-=1
                return
            elif node==self.tail:
                p=self.tail.GetPrev()
                p.SetNext(None)
                self.tail=p
                self.size-=1
                return
            else:
                p=node.GetPrev()
                n=node.GetNext()
                p.SetNext(n)
                n.SetPrev(p)
                self.size-=1
                return
        else:
            return

    def dump(self,current):
        if current==None:
            return

        if self.head!=None:
            h=self.head.GetData()
        else:
            h="None"
        if self.tail!=None:
            t=self.tail.GetData()
        else:
            t="None"
        if current.GetPrev()!=None:
            p=str(current.GetPrev().GetData())
        else:
            p="None"
        if current!=None:
            c=str(current.GetData())
        else:
            c="None"
        if current.GetNext()!=None:
            n=str(current.GetNext().GetData())
        else:
            n="None"
        print(f"H: {h} P: {p} C: {c} N: {n} T: {t}")

    def list(self):
        if self.head:
            current=self.head
            while current:
                self.dump(current)
                current=current.GetNext()


# Remap TradingView symbol to the exchange symbol

def TradingViewRemap(en,pair):
    np=pair
    JRRlog.WriteLog('Symbol Remap')
    JRRlog.WriteLog('|- In: '+pair)
    fn=JRRconfig.DataDirectory+'/'+en+'.symbolmap'
    if os.path.exists(fn):
        try:
            raw=pathlib.Path(fn).read_text()
        except:
            JRRlog.ErrorLog("TradingView Remap",f"Can't read symbol map for {en}")

        TVlist=json.loads(raw)
        if pair in TVlist:
            np=TVlist[pair]
        else:
            JRRlog.WriteLog('|- Pair not in symbol file, reverting')
    else:
        JRRlog.WriteLog('|- No symbol file, reverting')

    JRRlog.WriteLog('|- Out: '+np)
    return np

# Get the order ID from the result provided

def GetOrderID(res):
    s=res.find('ID:')+4
    for e in range(s,len(res)):
        if res[e]=='\n':
            break
    oid=res[s:e]

    return oid

# Webhook processing. This unified layer will communicate with Relay for
# placing the order and return the results.

def SendWebhook(Active,exchangeName,market,account,orderType,pair,action,amount,price,OverrideMaxAssets=False):
    if OverrideMaxAssets==True:
        exc='"OverrideMaxAssets":"Yes", "Exchange":"'+exchangeName+'", "Market":"'+market+'"'
    else:
        exc='"Exchange":"'+exchangeName+'", "Market":"'+market+'"'

    account='"Account":"'+account+'", "OrderType":"'+orderType+'"'
    sym='"Asset":"'+pair+'"'
    direction='"Action":"'+action.lower()+'"'
    psize='"Base":"'+str(amount)+'"'+',"Close":"'+str(price)+'"'

    if "Identity" in Active:
        idl='"Identity":"'+Active['Identity']+'"'
        cmd='{ '+idl+', '+exc+', '+account+', '+direction+', '+sym+', '+psize+' }'
    else:
        cmd='{ '+exc+', '+account+', '+direction+', '+sym+', '+psize+' }'

    headers={'content-type': 'text/plain', 'Connection': 'close'}

    resp=None
    res=None
    try:
        resp=requests.post(Active['Webhook'],headers=headers,data=cmd)
        try:
            r=json.loads(resp.text)
            try:
                res=r['message']
            except:
                res=json.dumps(r)
        except:
            res=resp.text
    except:
        res=None

    return res

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
    fn=JRRconfig.DataDirectory+'/'+exchange+'.'+account+'.MaxAssets'

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
    fn=JRRconfig.DataDirectory+'/'+exchange+'.'+account+'.MaxAssets'

    if coins=={}:
        try:
            os.remove(fn)
        except:
            pass
    else:
        fh=open(fn,'w')
        fh.write(json.dumps(coins))
        fh.close()

# Figure out the PCT type. Needs to identify %B and B%, %Q and Q%
# Default is previous functionality

def GetPCTtype(currency):
    c=currency.lower()
    if 'b%' in c or '%b' in c:
        vs=c.replace('b%','').replace('%b','').strip()
        PCTtype='B'
        pct=float(vs)
    elif 'q%' in c or '%q' in c:
        vs=c.replace('q%','').replace('%q','').strip()
        PCTtype='Q'
        pct=float(vs)
    else:
        vs=c.replace('%','').strip()
        PCTtype='B'
        pct=float(vs)
    return pct,PCTtype

# This list determines a fixed percentage for a coin per balance for the
# life of the trade, bot just the individual position

def ReadPCTValueList(exchange,account,pair,pct,pcttype,close,delete,RetryLimit):
    coins={}
    amount=0
    en=exchange.name.lower().replace(' ','')
    quote=exchange.markets[pair]['quote']
    fn=JRRconfig.DataDirectory+'/'+en+'.'+account+'.PCTvalue'

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
                jpkt={}
                bal=JRRapi.GetBalance(exchange,quote,RetryLimit)
                jpkt['Time']=time.time()
                jpkt['Volume']=round(((pct/100)*bal),8)
                jpkt['Amount']=round(jpkt['Volume']/close,8)
                amount=jpkt['Amount']
                coins[p]=json.dumps(jpkt)
                JRRlog.WriteLog('|- '+p+' added')
                JRRlog.WriteLog('|- Amount: '+str(amount))
                JRRlog.WriteLog('|- Volume: '+str(jpkt['Volume']))
            else:
                if p in coins:
                    if delete:
                        # Even if deleted, amount needs to be returned for consistency
                        jpkt=json.loads(coins[p])
                        jpkt['Time']=time.time()
                        if pcttype=='B':
                            amount=jpkt['Amount']
                        else:
                            jpkt['Amount']=round(jpkt['Volume']/close,8)
                            amount=jpkt['Amount']
                        JRRlog.WriteLog('|- '+p+' removed')
                        JRRlog.WriteLog('|- Amount: '+str(amount))
                        JRRlog.WriteLog('|- Volume: '+str(jpkt['Volume']))
                        try:
                            coins.pop(p,None)
                        except:
                            pass
                    else:
                        # Return existing amount
                        jpkt=json.loads(coins[p])
                        jpkt['Time']=time.time()
                        if pcttype=='B':
                            amount=jpkt['Amount']
                        else:
                            jpkt['Amount']=round(jpkt['Volume']/close,8)
                            amount=jpkt['Amount']
                        coins[p]=json.dumps(jpkt)
                        JRRlog.WriteLog('|- '+p+' updated')
                        JRRlog.WriteLog('|- Amount: '+str(amount))
                        JRRlog.WriteLog('|- Volume: '+str(jpkt['Volume']))
        else:
            if not delete:
                jpkt={}
                bal=JRRapi.GetBalance(exchange,quote,RetryLimit)
                jpkt['Time']=time.time()
                jpkt['Volume']=round(((pct/100)*bal),8)
                jpkt['Amount']=round(jpkt['Volume']/close,8)
                amount=jpkt['Amount']
                coins[p]=json.dumps(jpkt)
                JRRlog.WriteLog('|- '+p+' added')
                JRRlog.WriteLog('|- Amount: '+str(amount))
                JRRlog.WriteLog('|- Volume: '+str(jpkt['Volume']))

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
    fn=JRRconfig.DataDirectory+'/'+en+'.'+account+'.PCTvalue'

    if coins=={}:
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

# Verify number is an integer from JSON payload

def verifyInt(s):
    if s.lower()=="null" or s==None:
        return(False)
    f=float(s)
    i=int(s)

    return(f==i)

# Base 64 math

def int2base(n, b):
    if n < 0:
        raise ValueError("no negative numbers")
    if n < b:
        return dsrConfig.Base62Digits[n]
    res = []
    q = n
    while q:
        q, r = divmod(q, b)
        res.append(dsrConfig.Base62Digits[r])
    return ''.join(reversed(res))

def base2int(s, base):
    if not (2 <= base <= len(dsrConfig.Base62Digits)):
        raise ValueError("base must be >= 2 and <= %d" % len(Base62Digits))
    res = 0
    for i, v in enumerate(reversed(s)):
        digit = digits.index(v)
        res += digit * (base ** i)
    return res

def base62(s):
    n=0
    for i in range(len(s)):
        n+=ord(s[i])*i
    return(int2base(n,62))
