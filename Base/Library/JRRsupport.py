#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Jackrabbit Relay
# 2021 Copyright © Robert APM Darin
# All rights reserved unconditionally.

import sys
sys.path.append('/home/JackrabbitRelay2/Base/Library')
import os
import signal
import datetime
import time
import random
import socket
import json
import psutil
import signal

# Brute fore exit a program. Needed for multiprocessing programs that have sub-processes which can exit on a broker error.

def ForceExit(val,Parent=None):
    if Parent==None:
        print("No Parent")
        sys.exit(val)
    else:
        print("Parent:",Parent)
        parent = psutil.Process(Parent)
        for child in parent.children():
            if child.pid != os.getpid():
                print("Signalling child:", child.pid)
                os.kill(child.pid,2)

        print("Killing parent:", Parent)
        os.kill(Parent,2)

        print("Killing self:", os.getpid())
        psutil.Process(os.getpid()).kill()

# Signal Interceptor for critical areas

class SignalInterceptor():
    def __init__(self):
        self.critical=False
        self.original={}
        self.triggered={}

        self.parent_id=os.getppid()

        for sig in signal.valid_signals():
            self.triggered[sig]=False
            try:
                self.original[sig]=signal.getsignal(sig)
                signal.signal(sig,self.ProcessSignal)
            except:
                pass

    def SignalInterrupt(self,signal_num,frame):
        print('signal:', signal_num)
        ForceExit(signal_num,Parent=self.parent_id)

    def Critical(self,IsCrit=False):
        self.critical=IsCrit

    def ProcessSignal(self,signum,frame):
        if self.critical==True:
            self.triggered[signum]=True
        else:
            if callable(self.original[signum]):
                self.SignalInterrupt(signum,frame)

    def ResetSignals(self):
        for sig in signal.valid_signals():
            self.triggered[sig]=False

    def RestoreOriginalSignals(self):
        for sig in signal.valid_signals():
            try:
                signal.signal(sig,self.original[sig])
            except:
                pass

    def Triggered(self,signum):
        return self.triggered[signum]

    def SafeExit(self,now=False):
        for sig in signal.valid_signals():
            if self.triggered[sig]==True or now==True:
                if now==True:
                    sig=2
                self.SignalInterrupt(sig,None)

# Reusable file locks, using atomic operations
# NOT suitable for distributed systems or
# Windows. Linux ONLY
#
# fw=Locker(filename)
# fw.Lock()
# ( do somwething )
# fw.Unlock()

# { "ID":"DEADBWEEF", "FileName":"testData", "Action":"Lock", "Expire":"300" }

class Locker:
    # Initialize the file name
    def __init__(self,filename,Retry=7,Timeout=300,Log=None,ID=None):
        self.ulResp=['badpayload','locked','unlocked','failure']

        if ID==None:
            self.ID=self.GetID()
        else:
            self.ID=ID
        self.filename=filename
        self.retryLimit=Retry
        self.timeout=Timeout
        self.Log=Log
        self.port=37373
        self.host=''

    # Generate an ID String

    def GetID(self):
        letters="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        llen=len(letters)

        pw=""
        oc=""

        for i in range(20):
            done=False
            while not done:
                for z in range(random.randrange(73,237)):
                    c=random.randrange(llen)
                if pw=="" or (len(pw)>0 and letters[c]!=oc):
                    done=True
            oc=letters[c]
            pw+=oc
        return pw

    # Contact the Locker Server and WAIT for response. NOT thread safe.

    def Talker(self,msg,casefold=True):
        try:
            ls=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ls.connect((self.host, self.port))
            sfn=ls.makefile('rw')
            sfn.write(msg)
            sfn.flush()
            buf=None
            while buf==None:
                buf=sfn.readline()
            ls.close()
            if len(buf)!=0:
                if casefold==True:
                    return buf.lower().strip()
                else:
                    return buf.strip()
            else:
                return None
        except:
            return None

    # Contact Lock server

    def Retry(self,action,expire,casefold=True):
        outbuf='{ '+f'"ID":"{self.ID}", "FileName":"{self.filename}", "Action":"{action}", "Expire":"{expire}"'+' }\n'

        retry=0
        done=False
        while not done:
            buf=self.Talker(outbuf,casefold)
            if buf==None:
                if retry>self.retryLimit:
                    if self.Log!=None:
                        self.Log.Error("Locker",f"{self.filename}: {action} request failed")
                    else:
                        print("Locker",f"{self.filename}: {action} request failed")
                        ForceExit(1)
                retry+=1
                time.sleep(1)
            else:
                if len(buf)!=0:
                    # Received JSON, brak done and get status
                    try:
                        bData=json.loads(buf)
                        # IMPORTANT: This IS casefolded
                        buf=bData['status']
                    except:
                        pass
                    if casefold==True:
                        buf=buf.lower()
                    if buf in self.ulResp:
                        done=True
                    else:
                        time.sleep(0.1)
                else:
                    time.sleep(0.1)
        return buf

    def RetryData(self,action,expire,data):
        outbuf='{ '+f'"ID":"{self.ID}", "FileName":"{self.filename}", "Action":"{action}", "Expire":"{expire}", "DataStore":"{data}"'+' }\n'

        retry=0
        done=False
        while not done:
            buf=self.Talker(outbuf,casefold=False)
            if buf==None:
                if retry>self.retryLimit:
                    if self.Log!=None:
                        self.Log.Error("Locker",f"{self.filename}: {action} request failed")
                    else:
                        print("Locker",f"{self.filename}: {action} request failed")
                        ForceExit(1)
                retry+=1
                time.sleep(1)
            else:
                if len(buf)!=0:
                    done=True
                else:
                    time.sleep(0.1)
        return buf

    # Lock the file

    def Lock(self,expire=300):
        resp=None
        done=False
        timeout=time.time()+self.timeout
        while not done:
            resp=self.Retry("Lock",expire,casefold=True)
            if resp=="locked":
                done=True
            else:
                if time.time()>timeout:
                    if self.Log!=None:
                        self.Log.Error("Locker",f"{self.filename}: lock request failed")
                    else:
                        print("Locker",f"{self.filename}/{os.getpid()}: lock request failed")
                        ForceExit(1)
            # Prevent race conditions
            time.sleep(0.1)
        return resp

    # Unlock the file

    def Unlock(self):
        return self.Retry("Unlock",0)

    def Get(self):
        return self.RetryData("Get",0,None)

    def Put(self,expire,data):
        return self.RetryData("Put",expire,data)

    def Erase(self):
        return self.RetryData("Erase",0,None)

# General file tools

def ReadFile(fn):
    if os.path.exists(fn):
        cf=open(fn,'r')
        buffer=cf.read()
        cf.close()
    else:
        buffer=None
    return buffer

def WriteFile(fn,data):
    cf=open(fn,'w')
    cf.write(data)
    cf.close()

def AppendFile(fn,data):
    cf=open(fn,'a')
    cf.write(data)
    cf.close()

# Doubly lisked list with sentinel for bidirectional intertion
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
    def __init__(self,Compare=None):
        self.head=None
        self.tail=None
        self.sentinel=None
        self.size=0
        if Compare==None:
            self.DoCompare=self.compare
        else:
            self.DoCompare=Compare

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

    def compare(self,node,d2):
        d1=str(node.GetData())

        if d1<str(d2):
            return -1
        elif d1>str(d2):
            return 1
        else:
            return 0

    def find(self,data):
        if self.head:
            if self.DoCompare(self.head,data)==0:
                return self.head
            elif self.DoCompare(self.tail,data)==0:
                return self.tail
            else:
                if self.sentinel==None:
                    self.sentinel=self.head
                # Find out which direction we need to search based upon sentinel
                res=self.DoCompare(self.sentinel,data)
                if res>0:
                    while self.sentinel.GetNext()!=None and self.DoCompare(self.sentinel,data)>0:
                        self.sentinel=self.sentinel.GetNext()
                    # Did we find the item we wanted?
                    if self.DoCompare(self.sentinel,data)==0:
                        return self.sentinel
                    else:
                        return None
                elif res<0:
                    while self.sentinel.GetPrev()!=None and self.DoCompare(self.sentinel,data)<0:
                        self.sentinel=self.sentinel.GetPrev()
                    # Did we find the item we wanted?
                    if self.DoCompare(self.sentinel,data)==0:
                        return self.sentinel
                    else:
                        return None
                else: # res==0
                    return self.sentinel
        else:
            return None

    def insert(self,data):
        if self.head:
            # Initialize sentinel ptr. This will move according to direction of
            # comparisons. Will befaster then always starting at head of list.

            # New head of list test
            if self.DoCompare(self.head,data)<0:
                newNode=DListNode(data)
                newNode.SetNext(self.head)
                newNode.GetNext().SetPrev(newNode)
                self.head=newNode
                self.size+=1
                return
            # New tail of list test
            elif self.DoCompare(self.tail,data)>0:
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
                res=self.DoCompare(self.sentinel,data)
                if res>0:
                    while self.sentinel.GetNext()!=None and self.DoCompare(self.sentinel.GetNext(),data)>0:
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
                    while self.sentinel.GetPrev()!=None and self.DoCompare(self.sentinel.GetPrev(),data)<0:
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

    def delete(self,data):
        if self.head:
            node=self.find(data)
            # Not in list
            if node==None:
                return

            if node==self.head:
                n=self.head.GetNext()
                if n!=None:
                    n.SetPrev(None)
                self.head=n
                self.size-=1
                return
            elif node==self.tail:
                p=self.tail.GetPrev()
                if p!=None:
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

# Get Yesterday's date

def Yesterday(ds=None):
    if ds!=None:
        date=datetime.datetime.strptime(date_str,'%Y-%m-%d')
    else:
        date=datetime.datetime.now()
    yesterday=date-datetime.timedelta(days=1)
    return yesterday.strftime('%Y-%m-%d')

# Dirty support function to block HTML exchange payloads

def StopHTMLtags(text,full=False):
    clean_text=""
    in_tag=False
    i=0

    while i<len(text):
        char=text[i]
        if char=="<":
            # Check if this is the start of an HTML tag
            if i==0 or text[i-1] not in ('\\',"'",'"'):
                in_tag=True
        elif char==">":
            # Check if this is the end of an HTML tag
            if i==len(text)-1 or text[i+1] not in ('\\',"'",'"'):
                in_tag=False
        elif not in_tag:
            clean_text+=char
        i+=1

    clean_text=clean_text.strip()

    if full==True:
        return clean_text
    else:
        return clean_text[:clean_text.find('\n')]

# Filter end of line and hard spaces

def pFilter(s,FilterSpace=True):
    d=s.replace("\\n","").replace("\\t","").replace("\\r","")

    if FilterSpace==True:
        filterText='\t\r\n \u00A0'
    else:
        filterText='\t\r\n\u00A0'

    for c in filterText:
        d=d.replace(c,'')

    return(d)

# Elastic Delay. This is designed to prevent the VPS from being overloaded

def GetLoadAVG():
    fh=open('/proc/loadavg')
    l=fh.readline()
    fh.close()

    LoadAVG=l.split(' ')

    return(LoadAVG)

# Convert load average to seconds

def ElasticSleep(s):
    throttle=0
    LoadAVG=GetLoadAVG()
    d=float(max(LoadAVG[0],LoadAVG[1],LoadAVG[2]))

    c=os.cpu_count()

    # Convert lo into seconds

    i=int(d)
    f=d-i

    delay=i+(f/100)

    # if load is greater then cpu count, begin throttling the delay factor.

    if (d>c):
        throttle=(d-c)*delay

    time.sleep(s+delay+throttle)

# Returns milliseconds

def ElasticDelay():
    throttle=0
    LoadAVG=GetLoadAVG()
    d=int(float(max(LoadAVG[0],LoadAVG[1],LoadAVG[2])))

    c=os.cpu_count()

    # Convert lo into seconds

    i=int(d)
    f=d-i

    delay=int((i+(f/100))*1000)

    # if load is greater then cpu count, begin throttling the delay factor.

    if (d>c):
        throttle=int((d-c)*delay)

    return delay+throttle

# Read a timed list. Add data if not present.

# The DSR, MaxAssets, and PCTvalue lists are all built on this functionality

# Driver Test

#lines=sys.stdin.readlines()

#for line in lines:
#    line=line.strip()
#    tList=TimedList("timedList.test")
#    dataTV=json.loads(line)
#    key=dataTV['Recipe'].replace(" ","")+dataTV['Exchange']+dataTV['Asset']+dataTV['TCycles']+dataTV['TBuys']
#    results=tList.add(key,line,10)
#    if results!=None:
#        print("Found    ",results)

#tList=TimedList("timedList.test")
#tList.delete()

class TimedList():
    def __init__(self,title,fname,maxsize=0,Timeout=180,Log=None):
        self.Log=Log
        self.Timeout=Timeout
        self.fname=fname
        self.title=title
        self.maxsize=maxsize
        self.fw=Locker(self.fname,Timeout=self.Timeout,Log=self.Log)

    # Read the data from the table and return to user

    def read(self):
        dataDB=None

        self.fw.Lock()
        try:
            data=ReadFile(self.fname)
            dataDB=json.loads(data)
        except:
            pass
        self.fw.Unlock()

        return dataDB

    # Return a count that does NOT include expired items

    def countDB(self,dataDB):
        count=0
        for cur in dataDB:
            dataItem=json.loads(dataDB[cur])
            if dataItem['Expire']>time.time():
                count+=1
        return count

    # Update the table and add new items if needed

    def update(self,key,payload,expire):
        dataDB={}
        results={}

        self.fw.Lock()
        try:
            data=ReadFile(self.fname)

            if data!=None and data!='':
                dataDB=json.loads(data)
                if dataDB!=None:
                    if key in dataDB:
                        dataItem=json.loads(dataDB[key])
                        if dataItem['Expire']>time.time():
                            # Found and not expired, return result
                            if expire==0:
                                # Force kill item
                                dataItem['Expire']=expire
                                dataDB[key]=json.dumps(dataItem)
                                results['Status']='Expired'
                                results['Payload']=dataItem
                            else:
                                results['Status']='Found'
                                results['Payload']=dataItem
                        else: # Found and expired, replace old data with new data
                            c=self.countDB(dataDB)
                            if (self.maxsize==0) or (self.maxsize>0 and c<self.maxsize):
                                dataItem['Expire']=time.time()+expire
                                dataItem['Payload']=payload
                                dataDB[key]=json.dumps(dataItem)
                                results['Status']='Replaced'
                                results['Payload']=dataItem
                            else: # Size limit hit
                                results['Status']='Error'
                                results['Payload']='Maximum size limit exceeded'
                    else: # New item
                        # Needs to deal with expired item not being counted in limits
                        c=self.countDB(dataDB)
                        if (self.maxsize==0) or (self.maxsize>0 and c<self.maxsize):
                            dataItem={}
                            dataItem['Expire']=time.time()+expire
                            dataItem['Payload']=payload
                            dataDB[key]=json.dumps(dataItem)
                            results['Status']='Added'
                            results['Payload']=dataItem
                        else: # Size limit hit
                            results['Status']='ErrorLimit'
                            results['Payload']='Maximum size limit exceeded'
            else: # First Item
                dataItem={}
                dataItem['Expire']=time.time()+expire
                dataItem['Payload']=payload
                dataDB[key]=json.dumps(dataItem)
                results['Status']='Added'
                results['Payload']=dataItem

            WriteFile(self.fname,json.dumps(dataDB))
            self.fw.Unlock()
        except:
            self.fw.Unlock()
        return results

    # Search for a specific item

    def search(self,key):
        dataDB={}
        data=ReadFile(self.fname)

        if data!=None and data!='':
            dataDB=json.loads(data)
            if dataDB!=None:
                if key in dataDB:
                    # Don't report expired items
                    dataItem=json.loads(dataDB[key])
                    if dataItem['Expire']>time.time():
                        return dataDB[key]
        return None

    # Purge the list of all expired items

    def purge(self):
        dataDB={}
        self.fw.Lock()
        try:
            data=ReadFile(self.fname)
            if data!=None and data!='':
                dataDB=json.loads(data)

                # Remove expired entries
                NewDataDB={}
                for cur in dataDB:
                    dataItem=json.loads(dataDB[cur])
                    if dataItem['Expire']>time.time():
                        NewDataDB[cur]=dataDB[cur]
                WriteFile(self.fname,json.dumps(NewDataDB))
            self.fw.Unlock()
        except:
            self.fw.Unlock()

