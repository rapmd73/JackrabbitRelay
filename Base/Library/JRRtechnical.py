#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Jackrabbit Relay Technical Analysis

# 2021-2025 Copyright © Robert APM Darin
# All rights reserved unconditionally.

# This is NOT multiprocessing or thread safe.

import sys
sys.path.append('/home/GitHub/JackrabbitRelay/Base/Library')
import os
import math
import json
import datetime
import time

import JackrabbitRelay as JRR

class TechnicalAnalysis:
    def __init__(self, exchange, account, asset, timeframe, count=200):
        self.exchange = exchange
        self.account = account
        self.asset = asset
        self.tf = timeframe
        self.count = count+1 # historical (count) + live candles
        self.window = []
        self.relay = JRR.JackrabbitRelay(exchange=self.exchange,account=self.account)

    # Print the fancy numbers

    def Display(self,idx,length=16,precision=8):
        if idx==-1 and len(self.window)<1:
            return

        try:
            epoch=float(self.window[idx][0])
            dt=datetime.datetime.utcfromtimestamp(int(epoch/1000))
            sdt=dt.strftime('%Y-%m-%d %H:%M:%S')

            out=f"{sdt} "

            slice=self.window[idx]
            for i in range(1,len(slice)):
                if slice[i]!=None:
                    out+=f"{float(slice[i]):{length}.{precision}f} "
                else:
                    dashes='-'*80
                    out+=f"{dashes[:length]:{length}} "
            print(out)
        except Exception as err:
            print(f"{err}")

    # Rolling window

    def Rolling(self,slice=None):
        # If the window is None, initialize it with a list of `None` values of the specified size
        if self.window is None or self.window==[]:
            self.window=[[None]*6 for _ in range(self.count)]

        # Append the new data slice to the window
        if slice is not None:
            self.window.append(slice)

        # Ensure the window only contains the last 'size' elements
        if len(self.window)>self.count:
            self.window=self.window[-self.count:]  # Keep only the last `size` elements

        return self.window

    # Read OHLCV from file

    def ReadOHLCV(self,fn):
        def ReadFile2List(fname):
            # Something broke. Keep the responses in character
            if not os.path.exists(fname):
                return None

            cf=open(fname,'r')
            buffer=cf.read().strip()
            cf.close()

            if not buffer:
                return None

            responses=buffer.strip().split('\n')
            while '' in responses:
                responses.remove('')
            return responses

        ohlcv=[]
        data=ReadFile2List(fn)
        for line in data:
            numbers=line.strip().split(',')
            for i in range(1,len(numbers)):
                if numbers[i]!=None and numbers[i]!='None':
                    numbers[i]=float(numbers[i])
            ohlcv.append(numbers)
        return ohlcv

    # Pull the OHLCV data to the limit requested.

    def GetOHLCV(self):
        try:
            ohlcv=self.relay.GetOHLCV(symbol=self.asset,timeframe=self.tf, limit=self.count)
        except Exception:
            ohlcv=[]

        if not ohlcv:
            # Return a blank padded window if fetch fails
            self.window=[[None,None,None,None,None,None] for _ in range(self.count)]
            return self.window

        # Replace the window entirely with new data
        self.window=[list(slice_) for slice_ in ohlcv]

        # Enforce fixed window size
        if len(self.window)>self.count:
            self.window=self.window[-self.count:]
        elif len(self.window)<self.count:
            padding=[[None,None,None,None,None,None] for _ in range(self.count-len(self.window))]
            self.window=padding+self.window

        return self.window

    # Update the window with the last two OHLCV values. This replaces the
    # incomplete candle from the previous call.

    def UpdateOHLCV(self):
        try:
            ohlcv=self.relay.GetOHLCV(symbol=self.asset, timeframe=self.tf, limit=2)
        except Exception:
            ohlcv=[]

        # If no data is returned, append two None entries at the bottom
        if not ohlcv:
            self.window.append([None, None, None, None, None, None])
            self.window.append([None, None, None, None, None, None])
            # Enforce fixed window size
            if len(self.window) > self.count:
                self.window = self.window[-self.count:]
            return self.window

        # Replace the last candle with the first fetched slice
        if self.window:
            self.window[-1] = list(ohlcv[0])
        else:
            self.Rolling(ohlcv[0])

        # Append the second fetched slice as the new last candle
        self.window.append(list(ohlcv[1]))

        # Enforce fixed window size
        if len(self.window) > self.count:
            self.window = self.window[-self.count:]

        return self.Rolling(ohlcv[1])

    # Make an OHLCV record. No partial records generated.

    def MakeOHLCV(self,days=0,hours=0,minutes=0,seconds=60):
        """
        Construct an OHLCV record for a given duration using Jackrabbit Relay ticker.

        Parameters:
            days (int): Number of days for the bar duration.
            hours (int): Number of hours for the bar duration.
            minutes (int): Number of minutes for the bar duration.
            seconds (int): Number of seconds for the bar duration.

        Returns:
            list: [epoch, open, high, low, close, volume]
                  epoch = start timestamp of bar
                  volume = abs(close - open) * duration
        """
        # Convert total duration to seconds
        duration = days*86400 + hours*3600 + minutes*60 + seconds
        if duration <= 0:
            return []

        # Initialize OHLCV
        o=h=l=c=None

        start_time = time.time()
        epoch = int(start_time)

        while (time.time() - start_time) < duration:
            ticker=self.relay.GetTicker(symbol=self.asset)
            price=(float(ticker['Bid'])+float(ticker['Ask']))/2  # midpoint

            if o is None:
                o=h=l=c=price
            else:
                h = max(h, price)
                l = min(l, price)
                c = price

            time.sleep(1)  # Prevent hammering the relay

        # Volume definition per your spec
        v=abs(c - o)*duration

        return [epoch, o, h, l, c, v]

    # Calculate difference between two moving averages and where or not they
    # crossed over/user each other

    def Cross(self,idx1,idx2):
        # Ensure there are at least two data points to compare
        if len(self.window) < 2:
            self.window[-1].append(None)  # Not enough data to calculate difference or crossing
            self.window[-1].append(None)
            return self.window

        try:
            # Get the previous and current values for idx1 and idx2
            prev_idx1 = self.window[-2][idx1]  # Previous value of idx1
            prev_idx2 = self.window[-2][idx2]  # Previous value of idx2
            curr_idx1 = self.window[-1][idx1]  # Current value of idx1
            curr_idx2 = self.window[-1][idx2]  # Current value of idx2
        except Exception as err:
            self.window[-1].append(None)  # Not enough data to calculate difference or crossing
            self.window[-1].append(None)
            return self.window

        # Check if all values are valid for detecting difference and crossing
        if prev_idx1 is None or prev_idx2 is None or curr_idx1 is None or curr_idx2 is None:
            self.window[-1].append(None)  # Not enough data to calculate difference or crossing
            self.window[-1].append(None)
            return self.window

        # Calculate the difference between idx1 and idx2
        difference = curr_idx1 - curr_idx2

        # Detect crossing:
        # Crossover (idx1 crosses above idx2) => Return 1
        # Cross-under (idx1 crosses below idx2) => Return -1
        # No crossing => Return 0
        if prev_idx1 <= prev_idx2 and curr_idx1 > curr_idx2:
            cross_value = 1  # Crossover (idx1 crosses above idx2)
        elif prev_idx1 >= prev_idx2 and curr_idx1 < curr_idx2:
            cross_value = -1  # Cross-under (idx1 crosses below idx2)
        else:
            cross_value = 0  # No crossing

        # Append both the difference and the crossing result to the current slice
        self.window[-1].append(difference)   # Append the difference
        self.window[-1].append(cross_value)  # Append the crossing result

        return self.window

    # Calculate a simple moving average

    def SMA(self,idx,period=17):
        if len(self.window)<period+1:
            self.window[-1].append(None) # Update the last slice with None
            return self.window  # Not enough valid closing prices to calculate SMA

        # Get the last 'period' closing prices (index 4), extract closing price
        idxptr = [row[idx] for row in self.window[-period:] if len(row)>idx and row[idx] is not None]

        # Check if we have exactly the required number of closing prices
        if len(idxptr) < period:
            self.window[-1].append(None) # Update the last slice with None
            return self.window  # Not enough valid closing prices to calculate SMA

        # Calculate the SMA of the last `period` closing prices
        sma = sum(idxptr) / period

        self.window[-1].append(sma)  # Update the last slice with the SMA

        return self.window

    # Calculate an exponential moving average

    def EMA(self, idx, period=17):
        # Get the last 'period' closing prices
        idxptr = [row[idx] for row in self.window[-period:] if len(row)>idx and row[idx] is not None]

        # Check if we have exactly the required number of closing prices
        if len(idxptr) < period:
            self.window[-1].append(None)  # Update the last slice with None
            return self.window  # Not enough valid closing prices to calculate EMA

        # Smoothing factor
        k = 2 / (period + 1)

        # Start EMA with the SMA of the first 'period' values
        ema = sum(idxptr) / period

        # Apply EMA formula for remaining values
        for price in idxptr[1:]:
            ema = (price * k) + (ema * (1 - k))

        # Append EMA to the last slice
        self.window[-1].append(ema)

        return self.window

    # Calculate a weighted moving average

    def WMA(self, idx, period=17):
        # Get the last 'period' closing prices
        idxptr = [row[idx] for row in self.window[-period:] if len(row)>idx and row[idx] is not None]

        # Check if we have exactly the required number of closing prices
        if len(idxptr) < period:
            self.window[-1].append(None)  # Update the last slice with None
            return self.window  # Not enough valid closing prices to calculate WMA

        # Standard WMA weights: 1, 2, ..., period
        weights = list(range(1, period + 1))

        # Weighted sum
        weighted_sum = sum(price * weight for price, weight in zip(idxptr, weights))

        # Normalize by total weight
        wma = weighted_sum / sum(weights)

        # Append WMA to the last slice
        self.window[-1].append(wma)

        return self.window

    # Calculate a Hull Moving Average (HMA) using the existing WMA
    # Problem Child.

    def HMA(self, idx, period=21):
        """
        Calculate the Hull Moving Average (HMA) for the series at column `idx`.

        Formula:
            HMA(p) = WMA( 2 * WMA(p/2) - WMA(p), sqrt(p) )

        Parameters:
            idx (int): Column index of the price series in the rolling window (e.g., closing price).
            period (int): Lookback period for the HMA calculation. Default is 21.

        Behavior:
            - Works directly on the **last row** of self.window (`self.window[-1]`).
            - Adds exactly 4 new columns to that row:
                * WMA(p/2)
                * WMA(p)
                * Synthetic value = 2*WMA(p/2) - WMA(p)
                * HMA(p)
            - If there is not enough valid history, it still appends 4 None values.

        Returns:
            self.window (list of lists): Updated rolling data window with 4 new values
            (either floats or None).
        """

        # Step 0: Ensure enough historical data
        closes = [row[idx] for row in self.window[-period:] if len(row)>idx and row[idx] is not None]
        if len(closes) < period:
            self.window[-1].extend([None, None, None, None])
            return self.window

        # Step 1: WMA(period/2)
        self.WMA(idx, period // 2)
        wma_half = self.window[-1][-1]

        # Step 2: WMA(period)
        self.WMA(idx, period)
        wma_full = self.window[-1][-1]

        # Check validity
        if wma_half is None or wma_full is None:
            self.window[-1].extend([None, None])  # synthetic + HMA placeholders
            return self.window

        # Step 3: Synthetic = 2*WMA(p/2) - WMA(p)
        synthetic_value = (2 * wma_half) - wma_full
        self.window[-1].append(synthetic_value)

        # Step 4: WMA(synthetic, sqrt(period))
        sqrt_period = max(1, int(period ** 0.5))
        synthetic_idx = len(self.window[-1]) - 1
        self.WMA(synthetic_idx, sqrt_period)    # HMA value, last column

        return self.window

    # Calculate a volume weighted moving average

    def VWMA(self, idx, vol_idx=5, period=20):
        # Collect the last 'period' closing prices and volumes
        prices = [row[idx] for row in self.window[-period:] if len(row)>idx and row[idx] is not None and row[vol_idx] is not None]
        volumes = [row[vol_idx] for row in self.window[-period:] if len(row)>idx and row[idx] is not None and row[vol_idx] is not None]

        # Ensure we have enough data
        if len(prices) < period or len(volumes) < period:
            self.window[-1].append(None)  # Append None if not enough data
            return self.window

        # Calculate VWMA = sum(price * volume) / sum(volume)
        weighted_sum = sum(p * v for p, v in zip(prices, volumes))
        total_volume = sum(volumes)

        if total_volume == 0:
            vwma = None
        else:
            vwma = weighted_sum / total_volume

        # Append VWMA to the last slice
        self.window[-1].append(vwma)

        return self.window

    # Wilder moving average used by TradingView and other platforms, known as
    # the Relative Moving Average. Does NOT need a full window, unlike other
    # moving averages.

    def RMA(self, idx, period=14):
        """
        Calculate a Wilder Moving Average (used in ATR, ADX, DI+, DI-) for a given column.

        Parameters:
            idx (int): Column index of the source series in self.window (e.g., TR, DM+, DM-, Close).
            period (int): Lookback period for Wilder smoothing (default 14).

        Behavior:
            - Works directly on the rolling window self.window.
            - Appends the WilderMA result to the last row.
            - Uses previous row's WilderMA value for recursive smoothing.
            - If not enough history exists, appends None.

        Returns:
            self.window (list of lists): Updated rolling window with new WilderMA column.
        """

        if len(self.window) < 1:
            return self.window  # Nothing to calculate

        # Collect the last `period` values that exist in the rolling window
        history = []
        for row in self.window[-period:]:
            if len(row) > idx and row[idx] is not None:
                history.append(row[idx])

        if not history:
            self.window[-1].append(None)
            return self.window

        # If this is the first RMA (less than period candles), use simple average
        if len(history) < period:
            rma = sum(history) / len(history)
        else:
            # Wilder's smoothing: RMA_today = (prev_RMA*(period-1) + current_value)/period
            prev_rma = history[-2] if len(history) > 1 else history[0]
            rma = (prev_rma * (period - 1) + history[-1]) / period

        self.window[-1].append(rma)
        return self.window

    # Calculate a generalized Zero-Lag value for any indicator column

    def ZeroLag(self, idx, period=17):
        """
        Compute a generalized zero-lag value for the series in column `idx`.

        Parameters:
            idx (int): Column index of the series to apply zero-lag to (e.g., last EMA, SMA, RSI, etc.).
            period (int): Lookback period to compute the lag (default 17). Lag is calculated as (period-1)//2.

        Behavior:
            - Works directly on self.window[-1], appending the zero-lag value.
            - If insufficient history exists, appends None to maintain column consistency.
            - This function does NOT apply any smoothing itself; it only calculates the zero-lag derivative.

        Returns:
            self.window (list of lists): The updated rolling window with one new column containing
            the zero-lag value for the selected series.
        """

        if len(self.window[-1])<idx:
            self.window[-1].append(None)
            return self.window

        lag = (period - 1) // 2

        # Ensure sufficient history
        if len(self.window) <= lag or self.window[-1][idx] is None or self.window[-lag-1][idx] is None:
            # Append None for zero-lag column
            self.window[-1].append(None)
            return self.window

        # Compute zero-lag value
        current_value = self.window[-1][idx]
        lagged_value = self.window[-lag-1][idx]
        zero_lag_value = current_value + (current_value - lagged_value)

        # Append the zero-lag value to the last row
        self.window[-1].append(zero_lag_value)

        return self.window

    # Calculate a generalized Sine-Weighted value for any indicator column

    def SineWeight(self, idx, period=17):
        """
        Compute a generalized sine-weighted value for the series in column `idx`.

        Parameters:
            idx (int): Column index of the series to apply sine weighting to (e.g., last EMA, SMA, RSI, etc.).
            period (int): Lookback period over which to apply the sine weighting.

        Behavior:
            - Works directly on self.window[-1], appending the sine-weighted value.
            - If insufficient history exists, appends None to maintain column consistency.
            - The weights follow a sine curve from 0 to pi, emphasizing the middle of the period.

        Returns:
            self.window (list of lists): The updated rolling window with one new column containing
            the sine-weighted value for the selected series.
        """

        if len(self.window[-1])<idx:
            self.window[-1].append(None)
            return self.window

        # Extract last 'period' values from the selected column
        series = [row[idx] for row in self.window[-period:] if len(row)>idx and row[idx] is not None]

        # Ensure sufficient history
        if len(series) < period:
            self.window[-1].append(None)
            return self.window

        # If any value is None, return None
        if any(v is None for v in series):
            self.window[-1].append(None)
            return self.window

        # Generate sine weights (0 -> pi)
        weights = [math.sin((i + 1) * math.pi / period) for i in range(period)]

        # Weighted sum / normalize
        weighted_sum = sum(val * w for val, w in zip(series, weights))
        sine_weighted_value = weighted_sum / sum(weights)

        # Append sine-weighted value to the last row
        self.window[-1].append(sine_weighted_value)

        return self.window

    # Calculate Relative Strength Index (RSI) for the last candle in the window.

    def RSI(self, idx, period=14):
        # Collect the last 'period + 1' closing prices
        prices = [row[idx] for row in self.window[-(period+1):] if len(row)>idx and row[idx] is not None]

        if len(prices) < period + 1:
            # Not enough data to calculate RSI
            self.window[-1].append(None)
            return self.window

        # Calculate gains and losses
        gains = []
        losses = []
        for i in range(1, len(prices)):
            delta = prices[i] - prices[i-1]
            if delta > 0:
                gains.append(delta)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(-delta)  # Losses as positive numbers

        # Calculate average gain and loss
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        # Avoid division by zero
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

        # Append RSI to the last slice
        self.window[-1].append(rsi)

        return self.window

    # ADX indicator

    def ADX(self, high_idx=2, low_idx=3, close_idx=4, period=14):
        """
        Calculate standard ADX with +DI and -DI using Wilder's smoothing.

        Parameters:
            high_idx (int): Column index for high prices
            low_idx (int): Column index for low prices
            close_idx (int): Column index for close prices
            period (int): Lookback period (default 14)

        Appends to self.window[-1]:
            +DI, -DI, ADX
        """

        n = len(self.window)

        # Not enough history
        if n < period + 1:
            self.window[-1].extend([None, None, None])
            return self.window

        # Prepare lists for TR, +DM, -DM
        tr_list = []
        plus_dm_list = []
        minus_dm_list = []

        for i in range(-period, 0):
            try:
                high = self.window[i][high_idx]
                low = self.window[i][low_idx]
                prev_high = self.window[i-1][high_idx]
                prev_low = self.window[i-1][low_idx]
                prev_close = self.window[i-1][close_idx]
            except Exception:
                self.window[-1].extend([None, None, None])
                return self.window

            if None in [high, low, prev_high, prev_low, prev_close]:
                self.window[-1].extend([None, None, None])
                return self.window

            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            plus_dm = high - prev_high if (high - prev_high) > (prev_low - low) and (high - prev_high) > 0 else 0
            minus_dm = prev_low - low if (prev_low - low) > (high - prev_high) and (prev_low - low) > 0 else 0

            tr_list.append(tr)
            plus_dm_list.append(plus_dm)
            minus_dm_list.append(minus_dm)

        # Wilder smoothing for first TR, +DM, -DM
        sm_tr = sum(tr_list)
        sm_plus_dm = sum(plus_dm_list)
        sm_minus_dm = sum(minus_dm_list)

        # +DI and -DI
        plus_di = 100 * sm_plus_dm / sm_tr if sm_tr != 0 else 0
        minus_di = 100 * sm_minus_dm / sm_tr if sm_tr != 0 else 0

        self.window[-1].append(plus_di)
        self.window[-1].append(minus_di)

        # DX = abs(+DI - -DI) / (+DI + -DI) * 100
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di) if (plus_di + minus_di) != 0 else 0

        # Calculate ADX recursively if previous ADX exists
        if len(self.window[-2]) >= 3 and self.window[-2][-1] is not None:
            prev_adx = self.window[-2][-1]
            adx = (prev_adx * (period - 1) + dx) / period
        else:
            adx = dx  # first ADX = first DX

        self.window[-1].append(adx)

        return self.window

    def BollingerBands(self, idx, period=20, stddev_mult=2):
        """
        Calculate Bollinger Bands using an existing moving average column (idx).

        Appends to self.window[-1]:
            Upper Band, Lower Band
        """

        n = len(self.window)

        if n < period:
            self.window[-1].extend([None, None])
            return self.window

        series = [row[idx] for row in self.window[-period:] if len(row) > idx and row[idx] is not None]

        if len(series) < period:
            self.window[-1].extend([None, None])
            return self.window

        middle_band = self.window[-1][idx]  # existing MA
        mean = sum(series) / period
        variance = sum((x - mean) ** 2 for x in series) / period
        stddev = math.sqrt(variance)

        upper_band = middle_band + stddev_mult * stddev
        lower_band = middle_band - stddev_mult * stddev

        self.window[-1].extend([upper_band, lower_band])

        return self.window

    # MACD indicator, adds 3 columns. Crossing is NOT included

    def MACD(self, idxFAST, idxSLOW, period=9, signal_func=None):
        """
        Calculate MACD line, Signal line, and Histogram using precomputed moving averages
        from self.window.

        Parameters:
            idxFAST (int): Column index for the fast moving average
            idxSLOW (int): Column index for the slow moving average
            period (int): Period for the Signal line (default 9)
            signal_func (callable): Function to calculate moving average for signal line.
                                    Must take (idx, period) and return self.window.

        Behavior:
            - Uses existing moving averages stored in self.window.
            - Appends 3 new columns to self.window[-1]: MACD line, Signal line, Histogram.
            - If signal_func is None, defaults to EMA over MACD line.
        """

        # Ensure enough history
        if len(self.window) < 1 or len(self.window[-1]) <= max(idxFAST, idxSLOW):
            self.window[-1].extend([None, None, None])
            return self.window

        fast = self.window[-1][idxFAST]
        slow = self.window[-1][idxSLOW]

        if fast is None or slow is None:
            self.window[-1].extend([None, None, None])
            return self.window

        # MACD line
        macd_value = fast - slow
        self.window[-1].append(macd_value)

        # If no custom signal_func is provided, use EMA as default
        if signal_func is None:
            signal_func = self.EMA

        # Prepare a synthetic column for MACD line temporarily
        temp_idx = len(self.window[-1]) - 1  # MACD column index
        # Apply the moving average function to get the signal line
        self.window = signal_func(temp_idx, period)

        # The signal line is appended at the last column
        signal_idx = len(self.window[-1]) - 1
        signal_value = self.window[-1][signal_idx]

        # Histogram = MACD - Signal
        histogram = macd_value - signal_value if signal_value is not None else None
        self.window[-1].append(histogram)

        return self.window

    # ATR indicator

    def ATR(self, high_idx=1, low_idx=2, close_idx=4, period=14, malen=14, smooth_func=None):
        """
        Calculate Average True Range (ATR) using a pluggable smoothing function.

        Parameters:
            high_idx (int): Column index of High prices in self.window
            low_idx (int): Column index of Low prices in self.window
            close_idx (int): Column index of Close prices in self.window
            period (int): Lookback period for ATR calculation (default 14)
            malen (int): Smoothing period for ATR (default 14)
            smooth_func (callable): Function to smooth TR values. Defaults to self.RMA

        Returns:
            self.window (list of lists): Updated rolling window with TR and ATR appended
        """

        if smooth_func is None:
            smooth_func = self.RMA  # default smoothing

        # Ensure at least one previous candle exists
        if len(self.window) < 2:
            self.window[-1].extend([None, None])
            return self.window

        row = self.window[-1]
        prev_row = self.window[-2]

        # Check for missing data
        if (len(row) <= max(high_idx, low_idx, close_idx) or
            len(prev_row) <= close_idx or
            row[high_idx] is None or
            row[low_idx] is None or
            row[close_idx] is None or
            prev_row[close_idx] is None):
            self.window[-1].extend([None, None])
            return self.window

        # Calculate True Range (TR)
        high = row[high_idx]
        low = row[low_idx]
        prev_close = prev_row[close_idx]

        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        self.window[-1].append(tr)
        tr_idx = len(self.window[-1]) - 1  # index of TR in row

        # Collect TR values for initial ATR calculation
        TRs = []
        for r in self.window[-period:]:
            if len(r) > tr_idx and r[tr_idx] is not None:
                TRs.append(r[tr_idx])

        # If we have exactly 'period' TRs, set initial ATR as simple average
        if len(TRs) == period:
            initial_atr = sum(TRs) / period
            self.window[-1].append(initial_atr)
        else:
            # Apply chosen smoothing function to TR
            smooth_func(tr_idx, malen)

        return self.window

    # Stochastic indicators


    def Stochastic(self, k_col, period=14, d_period=3, d_func=None):
        """
        Stochastic Oscillator (%K, D line, %D), ATR/MACD style

        Parameters:
            k_col   : index of %K column in self.window
            period  : lookback for raw %K (default 14)
            d_period: smoothing period for %D (default 3)
            d_func  : function to smooth %D (default SMA)

        Appends to self.window[-1] in order:
            %K, D line (smoothed), %D (smoothed value)
        """

        if d_func is None:
            d_func = self.SMA  # default smoothing

        # Filter rows with valid high/low
        recent_rows = [row for row in self.window[-period:] if len(row) > 3 and row[2] is not None and row[3] is not None]

        if not recent_rows:
            self.window[-1].extend([None, None, None])
            return self.window

        # Compute %K if k_col is empty or invalid
        if k_col >= len(self.window[-1]) or self.window[-1][k_col] is None:
            highest_high = max(row[2] for row in recent_rows)
            lowest_low = min(row[3] for row in recent_rows)
            close = self.window[-1][4] if len(self.window[-1]) > 4 and self.window[-1][4] is not None else None
            if close is None or highest_high == lowest_low:
                k_value = 0.0 if close is not None else None
            else:
                k_value = ((close - lowest_low) / (highest_high - lowest_low)) * 100.0
        else:
            k_value = self.window[-1][k_col]

        # Append %K to the last row
        self.window[-1].append(k_value)
        k_idx = len(self.window[-1]) - 1

        # Apply smoothing to get %D (D line)
        d_func(k_idx, d_period)        # D line
        d_value = self.window[-1][-1]  # smoothed value

        # Append D line and final %D after %K
        self.window[-1].append(d_value)  # %D

        return self.window

    def Stochastic(self, high_idx, low_idx, close_idx, k_period=14, k_smooth=3, d_smooth=3, ma_func=None):
        """
        Calculate the Stochastic Oscillator for the last candle in the window.

        Parameters:
            high_idx (int): Column index for high prices
            low_idx (int): Column index for low prices
            close_idx (int): Column index for close prices
            k_period (int): Lookback period for raw %K (default 14)
            k_smooth (int): Smoothing period for %K (default 3)
            d_smooth (int): Smoothing period for %D (default 3)
            ma_func (callable): Moving average function to smooth (default EMA)

        Appends to self.window[-1]:
            K line, %K, %D
        """

        n = len(self.window)
        if n < k_period:
            self.window[-1].extend([None, None, None])
            return self.window

        # Extract last k_period highs, lows, closes
        highs = [row[high_idx] for row in self.window[-k_period:] if len(row) > high_idx and row[high_idx] is not None]
        lows = [row[low_idx] for row in self.window[-k_period:] if len(row) > low_idx and row[low_idx] is not None]
        closes = [row[close_idx] for row in self.window[-k_period:] if len(row) > close_idx and row[close_idx] is not None]

        if len(highs) < k_period or len(lows) < k_period or len(closes) < k_period:
            self.window[-1].extend([None, None,None])
            return self.window

        high_max = max(highs)
        low_min = min(lows)
        close_last = closes[-1]

        if high_max == low_min:
            raw_k = 0.0
        else:
            raw_k = 100 * (close_last - low_min) / (high_max - low_min)

        # Append raw %K first
        self.window[-1].append(raw_k)
        k_idx = len(self.window[-1]) - 1

        # Smooth %K using moving average (k_smooth)
        if ma_func is None:
            ma_func = self.EMA
        ma_func(k_idx, k_smooth)
        smoothed_k = self.window[-1][-1]  # %K smoothed

        # Append smoothed %K
        d_idx = len(self.window[-1]) - 1

        # Smooth %D using moving average (d_smooth) of smoothed %K
        self.window = ma_func(d_idx, d_smooth)

        return self.window

###
### END of code
###

