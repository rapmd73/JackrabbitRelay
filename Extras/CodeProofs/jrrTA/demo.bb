#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Jackrabbit Relay Technical Analysis example

# 2021-2025 Copyright © Robert APM Darin
# All rights reserved unconditionally.

import sys
sys.path.append('/home/JackrabbitRelay2/Base/Library')
import os
import math
import json
import datetime
import time

import JackrabbitRelay as JRR
import JRRtechnical as jrTA

def main():
    ta=jrTA.TechnicalAnalysis('kraken','MAIN','ADA/USD','1m',5000)
    #ohlcv=ta.ReadOHLCV('ADAUSD.txt')
    ohlcv=ta.GetOHLCV()

    SlowLength=197

    Opening=1
    HighIDX=2
    LowIDX=3
    Closing=4
    Volume=5

    for slice in ohlcv:
        ta.Rolling(slice)

        # Create an EMA, column 6
        emaIDX=6
        ta.EMA(Closing,SlowLength)

        # Create a Bollingers Band using a previous EMA, upper boundary will be
        # column 7, lower boundary will be collumn 8

        bbU=7
        bbL=8

        ta.BollingerBands(emaIDX,20,7)

        ta.Display(-1)

    for i in ta.labels:
        print(f"{i:10} {ta.idx(i)} {ta.idx(ta.idx(i))}")

if __name__=='__main__':
    main()

###
### End demo
###
