#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Jackrabbit Relay Technical Analysis Library
# 2021 Copyright © Robert APM Darin
# All rights reserved unconditionally.

# Bare bones minimalism technical analysis functions

import sys
import os
import math
import statistics

# Check for a red candle.
#
# A red candle is when the current closing price is lower then the 
# previous closing price OR the current closing price is less than
# the current opening price.

def IsRedCandle(Previous,Current):
    po=Previous[1]
    pc=Previous[4]
    co=Current[1]
    cc=Current[4]

    red=co>cc and cc<pc

    return red

# Check for a green candle.
#
# A red candle is when the current closing price is higher then the 
# previous closing price OR the current closing price is greater than
# the current opening price.

def IsGreenCandle(Previous,Current):
    po=Previous[1]
    pc=Previous[4]
    co=Current[1]
    cc=Current[4]

    green=co<cc and cc>pc

    return green

# Black Crow Algorithm
#
# Count the number of downward candles, must match candle count from command line
# Last candle MUST be upward

def IsBlackCrow(candles,CandleCount):
    i=len(candles)-1
    # Find 3 down candles in a row followed by 1 up candle

    IsDown=False
    IsBuy=False
    IsCandlePattern=False

    offset=1
    for z in range(offset,CandleCount+offset):
        x=i-z
        red=IsRedCandle(candles[x-2],candles[x-1])
        if z==offset:
            IsDown=red
        else:
            IsDown=IsDown and red

    # Last candle shows up swing, if so, BUY
    IsUp=IsGreenCandle(candles[i-1],candles[i])

    if IsDown and IsUp:
        return True
    return False

def Volatility(candles,days):
    # starting candle, ignore last as its incomplete
    l=len(candles)-1
    sc=l-days

    # Get average of days

    dl=[]
    for i in range(days):
        c0=candles[sc+i][4]
        c1=candles[sc+i-1][4]
        d=(c0/c1-1)*100
        dl.append(d)

    sd=statistics.stdev(dl) 

    return sd

def VWAP(candles,days):
    # starting candle, ignore last as its incomplete
    l=len(candles)-1
    sc=l-days

    # Get total volume/VWAP for day range

    tvol=0.0
    tvwp=0.0
    for i in range(days):
        volume=candles[sc+i][5]
        vwp=0.0
        for x in range(1,5):
            vwp+=candles[sc+i][x]
        vwp=(vwp/4)*volume
        tvwp+=vwp
        tvol+=volume

    vwap=tvwp/tvol

    return vwap