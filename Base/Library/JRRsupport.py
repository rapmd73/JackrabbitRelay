#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Jackrabbit Relay
# 2021 Copyright © Robert APM Darin
# All rights reserved unconditionally.

import sys
sys.path.append('/home/JackrabbitRelay2/Base/Library')
import os
import time
import json

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
    def __init__(self,filename,Log=None):
        self.filename=filename+'.lock'
        self.RetryLimit=37
        self.Log=Log

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
        txt=f"{p}\n"
        WriteFile(tn,txt)

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
        txt=f"{p}\n"
        WriteFile(tn,txt)

        # Let the battle begin...

        done=False
        retry=0
        while not done:
            try:
                os.rename(tn,self.filename)
            except:
                retry+=1
                if retry>=RetryLimit:
                    if self.Log!=None:
                        self.Log.ErrorLog("FileLock","exclusive access request failed")
            else:
                done=True

            time.sleep(0.1)

    # Unlock the file

    def Unlock(self):
        try:
            os.remove(self.filename)
        except:
            pass

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

# Dirty support function to block HTML exchange payloads

def StopHTMLtags(txt):
    try:
        p=txt.find('<')
        if p>-1:
            return txt[:p]
    except:
        pass
    return txt

# Filter end of line and hard spaces

def pFilter(s):
    d=s.replace("\\n","").replace("\\t","").replace("\\r","")

    for c in '\t\r\n \u00A0':
        d=d.replace(c,'')

    return(d)

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
    def __init__(self,fname):
        self.fname=fname
        self.fw=FileWatch(self.fname)

    def add(self,key,payload,expire):
        dataDB={}
        results=None

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
                            results=dataItem
                        else: # Found and expired, replace old data with new data
                            dataItem['Expire']=time.time()+expire
                            dataItem['Payload']=payload
                            dataDB[key]=json.dumps(dataItem)
                    else: # New item
                        dataItem={}
                        dataItem['Expire']=time.time()+expire
                        dataItem['Payload']=payload
                        dataDB[key]=json.dumps(dataItem)
            else: # First Item
                dataItem={}
                dataItem['Expire']=time.time()+expire
                dataItem['Payload']=payload
                dataDB[key]=json.dumps(dataItem)

            WriteFile(self.fname,json.dumps(dataDB))
            self.fw.Unlock()
        except:
            self.fw.Unlock()
        return results

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
