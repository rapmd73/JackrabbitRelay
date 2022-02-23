#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Jackrabbit Relay
# 2021 Copyright © Robert APM Darin
# All rights reserved unconditionally.

import sys
sys.path.append('/home/JackrabbitRelay/Base/Library')
from datetime import datetime

Version="0.0.0.0.775"
BaseDirectory='/home/JackrabbitRelay/Base'
ConfigDirectory='/home/JackrabbitRelay/Config'
LedgerDirectory="/home/JackrabbitRelay/Ledger"
LogDirectory="/home/JackrabbitRelay/Logs"
BalancesDirectory='/home/JackrabbitRelay/Statistics/Balances'
ChartsDirectory='/home/JackrabbitRelay/Statistics/Charts'

# This is sorted by market cap. Hopefully it will speed up the conversion
# process. Coins only with 100 million or more listed.

StableCoinUSD=['USDT','USDC','BUSD','UST','DAI','FRAX','TUSD','USDP','LUSD', \
               'USDN','HUSD','FEI','TRIBE','RSR','OUSD','XSGD','GUSD','USDX', \
               'SUSD','EURS','CUSD','USD']

# Needs to be global and above all code

StartTime=datetime.now()

