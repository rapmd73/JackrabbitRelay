#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Jackrabbit Relay
# 2021 Copyright © Robert APM Darin
# All rights reserved unconditionally.

import sys
sys.path.append('/home/JackrabbitRelay/Base/Library')
import os
from datetime import datetime

import JRRconfig

def ElapsedTime(StartTime):
    EndTime=datetime.now()
    Elapsed=(EndTime-StartTime)
    WriteLog("Processing Completed: "+str(Elapsed)+" seconds")

# Write log entry

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

def ErrorLog(func,e):
    msg=func+' failed with: '+str(e)

    WriteLog(msg)
    ElapsedTime(JRRconfig.StartTime)
    sys.stdout.flush()
    sys.exit(3)

def SuccessLog(func,e):
    msg=func+' successful with: '+str(e)

    WriteLog(msg)
    ElapsedTime(JRRconfig.StartTime)
    sys.stdout.flush()
    sys.exit(3)

