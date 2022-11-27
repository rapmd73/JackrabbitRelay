#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Jackrabbit Relay blueprint for adding exchanges/brokers

# 2021-2022 Copyright © Robert APM Darin
# All rights reserved unconditionally.

# This document is a work in progress.

# All of your import needed to carry out functionality for your broker

import sys
sys.path.append('/home/JackrabbitRelay2/Base/Library')
import os
import json
import requests
from datetime import datetime

# Needed to be able to reference the basic support functions, locker, lists, and
# other basic primitives.

import JRRsupport

# The Broker class. The name must be unique as there is a strong possibility
# that more than one broker may be used at once or simultaneously.

# Please be aware that this is the BASIC harness that connect to Relay. Be sure
# to build around it appripriately for readability and functionality. While code
# should be kept compact, it must be easily read and understood. Gimmicks and
# cutesy tricks are not sustainable in the long run, whereas simplicity,
# readability, and functionality will live forever. There's a reason why over 2
# BILLION lines of COBOL are still in service.

# The goal of this class is NOT to normalize the output, but to normalize the
# input shared by all exchanges/brokers. Every exchange/broker will have its own
# PlaceOrder module specfic to the main Relay server. This class give a basic
# standardized entry point.

# IN ALL CASES: Compare and contrast the differences with the existing modules
# to see how the interconnectivity is achieved and how input is normalized.

class JRRbroker:

    # Initialize everything for this broker. See the CCXT and OANDA files for
    # examples. Needs to auto-login during the initialization.

    def __init__(self,framework=None,payload=None,secondary=None):
        pass

    # Handle the retry functionality and send the request to the broker. This is
    # a centralized API wrapper for any communications to the exchange/broker.

    def API(self,function,**kwargs):
        pass

    # Login to the broker. This is typically called by the initialization, but
    # needed for future expansion where automated login may not be desirable.

    def Login(self):
        pass

    # Get the markets that are available to the user.

    def GetMarkets(self):
        pass

    # Get the balance of th account. Be sure to compare the CCXT vs the OANDA
    # functions of this primitive to see the diversity by which
    # exchanges/brokers function.

    # Cryptocurrency exchanges typically use balance for spot markets. Futures
    # or other markets may use it for the Quote amount of the contract, ie, the
    # available amount of spending power.

    def GetBalance(self,**kwargs):
        pass

    # Get the positions held. This is the common functionality for futures or
    # forex.

    def GetPositions(self,**kwargs):
        pass

    # Pull OHLCV data from the broker given various supplied information.

    def GetOHLCV(self,**kwargs):
        pass

    # Get the ticker of the asset and return bid, ask, and spread information.

    def GetTicker(self,**kwargs):
        pass

    # Get the order book fromthe exchange/broker.

    def GetOrderBook(self,**kwargs):
        pass

    # List of open orders. These will typically be open limit orders

    def GetOpenOrders(self,**kwargs):
        pass

    # Get the list of trades or owned position. OANDA is a good example where
    # every trade is itemized. Crypto exchages don't support this, so its an
    # empty pass through.

    def GetOpenTrades(self,**kwargs):
        pass

    # The heart and soul of this class. this method is expected to handle buy,
    # sell, and close functionality for long/short positions. Short positions
    # are exressed as negative values to uniformity.

    def PlaceOrder(self,**kwargs):
        pass

    # For crypto exchanges, this is the minimum amount and cost of an asset. For
    # forex, this is the minimum number of units/current bid price. If your
    # broker allows partial unit values, then this should reflect it.

    def GetMinimum(self,**kwargs):
        pass

    # Get the full details of a closed order. If your broker is like OANDA,
    # where every ticket is a new number, then you need to trace the ENTIRE
    # order process to ensure a complete ledger entry.

    def GetOrderDetails(self,**kwargs):
        pass

    # This is the bridging point between Relay and Oliver Twist. Ideally, orphan
    # orders should not exist. However, platform like TradingView are charting
    # platforms, not technically meant for trading. Limit orders need to be
    # tracked and managed.

    def MakeOrphanOrder(self,id,Order):
        pass

    # The ledger is a legal responsibility that must be taken seriously. Many
    # juristions require it by law and have substantial consequences if not
    # followed. This method logs an entire transaction that includes the
    # original order and the full broker details of that order.

    def WriteLedger(self,**kwargs):
        pass

