#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Jackrabbit Relay
# 2021 Copyright © Robert APM Darin
# All rights reserved unconditionally.

import sys
sys.path.append('/home/JackrabbitRelay2/Base/Library')
import os
from datetime import datetime

import JRRconfig

def ElapsedTime(StartTime):
    EndTime=datetime.now()
    Elapsed=(EndTime-StartTime)
    WriteLog("Processing Completed: "+str(Elapsed)+" seconds")

# Write log entry. Basic primitive

def WriteLog(msg):
    PlaceOrderName=os.path.basename(sys.argv[0])

    pid=os.getpid()
    time=(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))

    s=f'{time} {pid:7.0f} {msg}\n'

    fh=open(JRRconfig.LogDirectory+'/'+PlaceOrderName+'.log','a')
    fh.write(s)
    fh.close()
    print(s.rstrip())
    sys.stdout.flush()

# Spot log

def WriteSpotLog(e,a,p,msg):
    PlaceOrderName=os.path.basename(sys.argv[0])
    pn=e+'.'+a+'.'+p.replace("-","").replace("/","").replace(':','')

    pid=os.getpid()
    time=(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))

    s=f'{time} {pid:7.0f} {msg}\n'

    fh=open(JRRconfig.LogDirectory+'/'+PlaceOrderName+'.'+pn+'.log','a')
    fh.write(s)
    fh.close()
    print(s.rstrip())
    sys.stdout.flush()

# Future log

def WriteFutureLog(e,a,p,d,msg):
    PlaceOrderName=os.path.basename(sys.argv[0])
    pn=e+'.'+a+'.'+p.replace("-","").replace("/","").replace(':','')

    pid=os.getpid()
    time=(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))

    s=f'{time} {pid:7.0f} {msg}\n'

    fh=open(JRRconfig.LogDirectory+'/'+PlaceOrderName+'.'+d+'.'+pn+'.log','a')
    fh.write(s)
    fh.close()
    print(s.rstrip())
    sys.stdout.flush()

# Error and exit

def ErrorLog(func,e):
    msg=func+' failed with: '+str(e)

    WriteLog(msg)
    ElapsedTime(JRRconfig.StartTime)
    sys.stdout.flush()
    sys.exit(3)

# Success and exit

def SuccessLog(func,e):
    msg=func+' successful with: '+str(e)

    WriteLog(msg)
    ElapsedTime(JRRconfig.StartTime)
    sys.stdout.flush()
    sys.exit(2)

