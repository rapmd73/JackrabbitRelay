#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Jackrabbit Relay
# 2021 Copyright © Robert APM Darin
# All rights reserved unconditionally.

import sys
sys.path.append('/home/JackrabbitRelay/Base/Library')
from datetime import datetime

Version="0.0.0.0.1055"
BaseDirectory='/home/JackrabbitRelay/Base'
ConfigDirectory='/home/JackrabbitRelay/Config'
DataDirectory="/home/JackrabbitRelay/Data"
BalancesDirectory='/home/JackrabbitRelay/Statistics/Balances'
ChartsDirectory='/home/JackrabbitRelay/Statistics/Charts'
LedgerDirectory="/home/JackrabbitRelay/Ledger"
LogDirectory="/home/JackrabbitRelay/Logs"
StatisticsDirectory='/home/JackrabbitRelay/Extras/Statistics'

NOhtml='<html><title>NO!</title><body style="background-color:#ffff00;display:flex;weight:100vw;height:100vh;align-items:center;justify-content:center"><h1 style="color:#ff0000;font-weight:1000;font-size:10rem">NO!</h1></body></html>'

# This is sorted by market cap. Hopefully it will speed up the conversion
# process. Coins only with 100 million or more listed.

StableCoinUSD=['USDT','USDC','BUSD','UST','DAI','FRAX','TUSD','USDP','LUSD', \
               'USDN','HUSD','FEI','TRIBE','RSR','OUSD','XSGD','GUSD','USDX', \
               'SUSD','EURS','CUSD','USD']

# Needs to be global and above all code

StartTime=datetime.now()


