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
import gc
import random
import math
import json
import datetime
import time

import matplotlib
import matplotlib.pyplot as plt
plt.rcParams['animation.ffmpeg_path']='/usr/bin/ffmpeg'
import matplotlib.animation as animation
import matplotlib.ticker as mticker

import JackrabbitRelay as JRR

matplotlib.use('Agg')

class TechnicalAnalysis:
    def __init__(self, exchange, account, asset, timeframe, count=5000,length=16,precision=8):
        self.Version='0.0.0.0.1110'
        self.exchange = exchange
        self.account = account
        self.asset = asset
        self.tf = timeframe
        self.logname=f"{sys.argv[0]}.{self.exchange}.{self.account}.{self.asset.replace('/','')}.{self.tf}.log"
        self.count = count+1
        self.length=length
        self.precision=precision
        self.Duplicate=False    # duplicate row received
        self.relay = JRR.JackrabbitRelay(exchange=self.exchange,account=self.account)
        if self.tf=='MAX':
            self.tf=self.relay.Timeframes[-1]
        elif self.tf=='MIN':
            self.tf=self.relay.Timeframes[0]
        self.window = []
        self.fig,self.ax=plt.subplots(figsize=(19.2, 10.8), dpi=100) # 1920x1080
        self.ImageNumber=0

    # Conver timestamp to a readable date

    def ts2date(self,timestamp):
        try:
            ts=float(timestamp)
            dt=datetime.datetime.utcfromtimestamp(int(ts/1000))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as err:
            return None

    # Window to string

    def Win2Text(self,idx):
        if idx==-1 and len(self.window)<1:
            return

        sdt=self.ts2date(self.window[idx][0])
        if sdt is None:
            sdt=self.window[idx][0]

        out=f"{sdt} "

        slice=self.window[idx]
        for i in range(1,len(slice)):
            if slice[i]!=None:
                out+=f"{float(slice[i]):{self.length}.{self.precision}f} "
            else:
                dashes='-'*80
                out+=f"{dashes[:self.length]:{self.length}} "
        return out

    # Log the window

    def Log(self,idx,end=0,purge=False):
        def WriteLog(out):
            fh=open(self.logname,'a+')
            fh.write(f"{out}\n")
            fh.close()

        if idx<0 and end==0:
            out=','.join(str(x) for x in self.window[idx])
            WriteLog(out)
            return

        # Log the entire wwindow

        if end>len(self.window) or end==-1:
            end=len(self.window)

        if end>0 and idx<0:
            idx=0

        # Purge the previous data

        if purge:
            try:
                os.remove(self.logname)
            except:
                pass

        # Only write out actual data

        for i in range(idx,end):
            if self.window[i][0]:
                out=','.join(str(x) for x in self.window[i])
                WriteLog(out)

    # Print the fancy numbers

    def Display(self,idx):
        print(self.Win2Text(idx))

    # Return a row from the rolling window. Can be absolute or relative

    def GetSize(self):
        l=0
        for i in range(0,len(self.window)):
            if self.window[i][0]:
                l+=1
        return l

    # Return a row from the rolling window. Can be absolute or relative

    def GetRow(self,row):
        if not self.window or abs(row)>len(self.window):
            return []

        return self.window[row]

    # Return the last row back to the user

    def LastRow(self):
        return self.GetRow(-1)

    # Add a column to the rolling windows
    def AddColumn(self,value):
        if self.window and len(self.window)>0:
            self.window[-1].append(value) # Update the last slice with value
        return self.window

    # Save an image of the chart from index.

    def SaveChart(self, length=0, store=None, visible=[], title=None, subtitle=None, trades=[], labels=[], writer=None):
        ChartName=None
        if store is not None:
            ChartName = f"{store}/{self.ImageNumber:012d}.png"
            if not os.path.exists(ChartName):
                os.makedirs(store, exist_ok=True)

        # 2. Window Slicing
        end = len(self.window)
        start = max(0, end - length)
        ohlcv = self.window[start:end]
        if not ohlcv or ohlcv[0][0] is None:
            return

        # 3. Reset and Style the Axis (The Plotly 'White' Look)
        self.ax.clear()
        self.ax.xaxis.set_visible(True)
        self.ax.yaxis.set_visible(True)

        self.ax.set_facecolor('white')
        self.fig.subplots_adjust(bottom=0.12, top=0.90, left=0.10, right=0.95)
        self.ax.grid(True, color='#E5E5E5', linestyle='-', linewidth=0.5, zorder=0)

        # Show a neat box around the chart (similar to TV)
        self.ax.spines['top'].set_color('#888888')
        self.ax.spines['right'].set_color('#888888')
        self.ax.spines['left'].set_color('#888888')
        self.ax.spines['bottom'].set_color('#888888')
        self.ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.5f'))
        self.ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=20))

        # 4. Draw Candlesticks (Optimized using vlines)
        # Plotly Standard Colors
        up_color = '#26a69a'
        down_color = '#ef5350'

        dt = []
        indices = range(len(ohlcv))
        for i, row in enumerate(ohlcv):
            # Format X-axis timestamp
            dstr = datetime.datetime.fromtimestamp(int(row[0]/1000), datetime.UTC).strftime('%Y-%m-%d %H:%M:%S')
            dt.append(dstr)
            # Build candles
            o, h, l, c = row[1], row[2], row[3], row[4]
            color = up_color if c > o else down_color

            # Wick
            self.ax.vlines(i, l, h, color=color, linewidth=1.5, zorder=1)
            # Body (Thick vline is 10x faster than drawing rectangles)
            self.ax.vlines(i, o, c, color=color, linewidth=8, zorder=2)

        # 5. Draw Indicators
        self.ax.tick_params(axis='y', which="both", labelsize=10, color='#333333',left=True,labelleft=True,right=True,labelright=True)
        for i in range(5, len(visible)):
            if i < len(ohlcv[-1]) and visible[i]:
                # Extract indicator column for the current slice
                data = [r[i] for r in ohlcv]
                if labels!=[] and i<len(labels) and labels[i] is not None:
                    labelstr=f"{labels[i]}({i})"
                else:
                    labelstr=f"Col {i}"
                self.ax.plot(indices, data, linewidth=1, label=labelstr, zorder=3)

        # 6. Open Trades (Blue Lines)
        total_trades = len(trades)
        for idx, entry_price in enumerate(trades):
            if entry_price is not None:
                if idx>=total_trades-10:
                    label_str=f"Trade {idx+1}: {abs(entry_price):.{self.precision}f}"
                else:
                    label_str=f"_Trade {idx+1}: {abs(entry_price):.{self.precision}f}"

                self.ax.axhline(y=abs(entry_price), color='#0078FF',
                                linestyle='-', linewidth=0.5, alpha=0.7,
                                label=label_str, zorder=4)

        # 7. Force the axis line and labels to be visible
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['bottom'].set_visible(True)
        self.ax.tick_params(axis='x', which='both', bottom=True, labelbottom=True, top=True, labeltop=True, labelcolor='black', labelsize=10, length=5)

        # Pick indices for X labels (e.g., 8 labels)
        num_visible = len(dt)
        nticks = 8
        if num_visible >= 2:
            tick_indices=[int(i * (num_visible-1) / (nticks-1)) for i in range(nticks)]
            tick_labels=[dt[i] for i in tick_indices]

            self.ax.set_xticks(tick_indices)
            self.ax.set_xticklabels(tick_labels, fontsize=10, color='black', rotation=0, visible=True)

        # Ensure the x-axis limits are strictly pinned to the window size
        self.ax.set_xlim(-0.5, num_visible - 0.5)

        # 8. Title and Formatting
        title_str = title if title else f"Market Motion | Frame {self.ImageNumber}"
        self.ax.set_title(title_str, fontsize=16, color='#333333', pad=20, fontweight='bold')

        if subtitle:
            # (0.5, 1.03) means centered horizontally (0.5) and 3% above the top of the
            # chart box (1.03)
            self.ax.text(0.5, 1.03, subtitle, transform=self.ax.transAxes, ha='center', va='bottom', fontsize=11, color='#666666', fontweight='normal')

        # 9. Draw the Legend
        handles, labels = self.ax.get_legend_handles_labels()
        if labels:
            # Replicating Plotly's clean, floating legend
            self.ax.legend(
                loc='upper left',
                fontsize=9,
                frameon=True,
                facecolor='white',
                edgecolor='#E5E5E5',
                shadow=False,
                framealpha=0.9
            )

        # Fast Save
        # 'canvas.print_png' is the lowest-level, fastest way to save
        self.fig.tight_layout(pad=3.0)
        self.fig.subplots_adjust(bottom=0.10, left=0.10, right=0.90, top=0.90)

        # Save the image.
        if ChartName is not None:
            self.fig.savefig(ChartName, format='png', metadata={'Software': 'JackrabbitRelay'})

        # Save the MP4 frame
        if writer is not None:
            self.fig.canvas.draw()
            writer.grab_frame()

        self.ImageNumber+=1

        # Clean the house
        if (self.ImageNumber%723)==0:
            gc.collect()

    # Reload the matrix

    def Load(self,fn=None,verbose=True):
        filename=None

        if fn and os.path.exists(fn):
            filenane=fn
        elif self.logname and os.path.exists(self.logname):
            filename=self.logname

        if filename:
            if verbose:
                print("Reloading matrix")

            fh=open(self.logname,'r')
            for line in fh.readlines():
                slice=line.strip().split(',')
                self.Rolling(slice)
            fh.close()

        return self.window

    # Rolling window

    def Rolling(self,slice=None):
        self.Duplicate=False

        # If the window is None, initialize it with a list of `None` values of the specified size
        if self.window is None or self.window==[]:
            self.window=[[None]*6 for _ in range(self.count)]

        # Append the new data slice to the window
        last=None
        if len(self.window)>0:
            last=self.window[-1]

        if slice is not None:
            for i in range(len(slice)):
                if type(slice[i]) is str:
                    if slice[i].lower()!="none":
                        slice[i]=float(slice[i])
                    else:
                        slice[i]=None
            if last is None or last[0] is None or (last is not None and slice[0]>last[0]):
                self.window.append(slice)
            else:
                self.Duplicate=True

        # Ensure the window only contains the last 'size' elements
        if len(self.window)>self.count:
            self.window=self.window[-self.count:]  # Keep only the last `size` elements

        return self.window

    # Update the window with the last two OHLCV values. This replaces the
    # incomplete candle from the previous call. If a LIVE market, the previous
    # PARTIAL candle MUST be removed from the window and replaced the new
    # CLOSED candle.

    def UpdateOHLCVRolling(self,live=True):
        try:
            ohlcv=self.relay.GetOHLCV(symbol=self.asset, timeframe=self.tf, limit=2)
        except Exception:
            ohlcv=[]

        # If no data is returned, append two None entries at the bottom
        if not ohlcv or len(ohlcv)<2 or len(ohlcv[0])<6 or len(ohlcv[1])<6:
            self.window.append([None, None, None, None, None, None])
            if live:
                self.window.append([None, None, None, None, None, None])
            # Enforce fixed window size
            if len(self.window) > self.count:
                self.window = self.window[-self.count:]
            return self.window

        if live:
            # Replace the last candle with the first fetched slice
                if self.window and len(self.window)>0:
                    if ohlcv[0][0]>self.window[-1][0]:
                        self.window[-1] = list(ohlcv[0])
                else:
                    self.Rolling(ohlcv[0])

        # Add the new candle

        self.Rolling(ohlcv[1])

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
    # Return the RAW ohlcv data. Do NOT add it to the rolling window.

    def GetOHLCV(self):
        try:
            count = self.count+1 if self.count<5000 else 5000
            ohlcv=self.relay.GetOHLCV(symbol=self.asset,timeframe=self.tf, limit=count)
        except Exception as err:
            print(err)
            # Return a blank padded window if fetch fails
            ohlcv=None

        return ohlcv

    # Get the ticker

    def GetTicker(self):
        return self.relay.GetTicker(symbol=self.asset)

    def GetSyntheticTicker(self,previous_ticker,deviation=0.0005):
        """
        Generate a synthetic OANDA-style forex ticker.

        Parameters:
            previous_ticker (dict): Previous ticker with keys 'Bid', 'Ask', 'Spread'.
            deviation (float): Maximum allowed deviation for price movement.

        Returns:
            dict: New ticker with keys 'Bid', 'Ask', 'Spread'.
        """
        # Extract previous values
        prev_ask = float(previous_ticker.get('Ask', 1.0))
        prev_spread = abs(previous_ticker.get('Spread', 0.0001))

        # Random movement up or down within deviation
        direction = random.choice([-1, 1])
        change = random.uniform(0, deviation) * direction
        new_ask = prev_ask + change

        # Slight randomization of spread (within 10% of previous)
        spread_change = random.uniform(-prev_spread * 0.1, prev_spread * 0.1)
        new_spread = max(0.00001, prev_spread + spread_change)

        # OANDA relationship: Bid = Ask - Spread
        new_bid = new_ask - new_spread

        ticker={}
        ticker['DateTime']=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        ticker['Ask']=round(new_ask,8)
        ticker['Bid']=round(new_bid,8)
        ticker['Spread']=round(new_spread,8)

        return ticker

    # Make an OHLCV record. No partial records generated.

    def MakeOHLCV(self,days=0,hours=0,minutes=0,seconds=60,synthetic=False):
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
        o=h=l=c=v=None

        start_time = time.time()
        epoch = int(start_time)
        previous_ticker=None

        count=0
        while (time.time() - start_time) < duration:
            if synthetic and previous_ticker:
                ticker=self.GetSyntheticTicker(previous_ticker)
            else:
                ticker=self.relay.GetTicker(symbol=self.asset)
            if previous_ticker is None:
                previous_ticker=ticker
            price=(float(ticker['Bid'])+float(ticker['Ask']))/2  # midpoint

            if o is None:
                o=h=l=c=price
            else:
                h = max(h, price)
                l = min(l, price)
                c = price

            time.sleep(0.1)  # Prevent hammering Relay
            count+=1

        # Volume definition per your spec
        v=abs(c - o)*duration*count

        return [epoch, o, h, l, c, v]

    ##
    ## Technical Indicators
    ##

    # CandleCounter - keeps track of an event for X candles after it occurs.
    # This can be used to hold a signal for X candles, ie a crossing.

    def CandleCounter(self, idx, target_value, reset_count):
        # Require at least one row
        if len(self.window) < 1:
            self.AddColumn(None)
            return self.window

        last_row = self.LastRow()

        # Safe access to the watched column
        try:
            current_value = last_row[idx]
        except Exception:
            self.AddColumn(None)
            return self.window

        # Determine previous counter (last column of previous row)
        prev_count = 0
        pIDX=len(last_row)   # current index in the matrix
        if len(self.window) > 1:
            prev_row = self.window[-2]
            if prev_row and len(prev_row)>=len(last_row):
                prev_count = prev_row[pIDX]
            else:
                prev_count = 0

        # If the watched column equals the target, reset to reset_count
        if current_value == target_value:
            counter = int(reset_count)
        else:
            # Otherwise count down from the previous counter, floor at 0
            counter = prev_count - 1 if prev_count and prev_count > 0 else 0

        self.AddColumn(counter)
        return self.window

    # Calculate difference between two moving averages and where or not they
    # crossed over/user each other

    def Cross(self,idx1,idx2):
        # Ensure there are at least two data points to compare
        if len(self.window) < 2:
            self.AddColumn(None)  # Not enough data to calculate difference or crossing
            self.AddColumn(None)
            return self.window

        try:
            # Get the previous and current values for idx1 and idx2
            prev_idx1 = self.window[-2][idx1]  # Previous value of idx1
            prev_idx2 = self.window[-2][idx2]  # Previous value of idx2
            curr_idx1 = self.window[-1][idx1]  # Current value of idx1
            curr_idx2 = self.window[-1][idx2]  # Current value of idx2
        except Exception as err:
            self.AddColumn(None)  # Not enough data to calculate difference or crossing
            self.AddColumn(None)
            return self.window

        # Check if all values are valid for detecting difference and crossing
        if prev_idx1 is None or prev_idx2 is None or curr_idx1 is None or curr_idx2 is None:
            self.AddColumn(None)  # Not enough data to calculate difference or crossing
            self.AddColumn(None)
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
        self.AddColumn(difference)   # Append the difference
        self.AddColumn(cross_value)  # Append the crossing result

        return self.window

    # Calculate a simple moving average

    def SMA(self,idx,period=17):
        if len(self.window)<period+1:
            self.AddColumn(None) # Update the last slice with None
            return self.window  # Not enough valid closing prices to calculate SMA

        # Get the last 'period' closing prices (index 4), extract closing price
        idxptr = [row[idx] for row in self.window[-period:] if len(row)>idx and row[idx] is not None]

        # Check if we have exactly the required number of closing prices
        if len(idxptr) < period:
            self.AddColumn(None) # Update the last slice with None
            return self.window  # Not enough valid closing prices to calculate SMA

        # Calculate the SMA of the last `period` closing prices
        sma = sum(idxptr) / period

        self.AddColumn(sma)  # Update the last slice with the SMA

        return self.window

    # Calculate an exponential moving average

    def EMA(self, idx, period=17):
        # Get the last 'period' closing prices
        idxptr = [row[idx] for row in self.window[-period:] if len(row)>idx and row[idx] is not None]

        # Check if we have exactly the required number of closing prices
        if len(idxptr) < period:
            self.AddColumn(None)  # Update the last slice with None
            return self.window  # Not enough valid closing prices to calculate EMA

        # Smoothing factor
        k = 2 / (period + 1)

        # Start EMA with the SMA of the first 'period' values
        ema = sum(idxptr) / period

        # Apply EMA formula for remaining values
        for price in idxptr[1:]:
            ema = (price * k) + (ema * (1 - k))

        # Append EMA to the last slice
        self.AddColumn(ema)

        return self.window

    # Calculate a weighted moving average

    def WMA(self, idx, period=17):
        # Get the last 'period' closing prices
        idxptr = [row[idx] for row in self.window[-period:] if len(row)>idx and row[idx] is not None]

        # Check if we have exactly the required number of closing prices
        if len(idxptr) < period:
            self.AddColumn(None)  # Update the last slice with None
            return self.window  # Not enough valid closing prices to calculate WMA

        # Standard WMA weights: 1, 2, ..., period
        weights = list(range(1, period + 1))

        # Weighted sum
        weighted_sum = sum(price * weight for price, weight in zip(idxptr, weights))

        # Normalize by total weight
        wma = weighted_sum / sum(weights)

        # Append WMA to the last slice
        self.AddColumn(wma)

        return self.window

    # Calculate a Hull Moving Average (HMA) using the existing WMA

    # The default is WMA, but by using a column, I can give ANY moving average
    # to HMA or even change the WMA parameters externally.

    def HMA(self, wmaIDX, wma2IDX, period=21):
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
        """

        # Step 0: Ensure enough historical data
        if len(self.window)<period+1:
            self.AddColumn(None)
            self.AddColumn(None)
            return self.window

        if len(self.window[-1])<wmaIDX+1 or len(self.window[-1])<wma2IDX+1:
            self.AddColumn(None)
            self.AddColumn(None)
            return self.window

        # Step 1: WMA(period)
        wma_full = self.window[-1][wmaIDX]

        # Step 2: WMA(period/2)
        wma_half = self.window[-1][wma2IDX]

        # Check validity
        if wma_half is None or wma_full is None:
            self.AddColumn(None)
            self.AddColumn(None)
            return self.window

        # Step 3: Synthetic = 2*WMA(p/2) - WMA(p)
        synthetic_value = (2 * wma_half) - wma_full
        self.AddColumn(synthetic_value)

        # Step 4: WMA(synthetic, sqrt(period))
        sqrt_period = max(1, int(period ** 0.5))
        self.AddColumn(sqrt_period)

        return self.window

    # Calculate a volume weighted moving average

    def VWMA(self, idx, vol_idx=5, period=20):
        # Collect the last 'period' closing prices and volumes
        prices = [row[idx] for row in self.window[-period:] if len(row)>idx and row[idx] is not None and row[vol_idx] is not None]
        volumes = [row[vol_idx] for row in self.window[-period:] if len(row)>idx and row[idx] is not None and row[vol_idx] is not None]

        # Ensure we have enough data
        if len(prices) < period or len(volumes) < period:
            self.AddColumn(None)  # Append None if not enough data
            return self.window

        # Calculate VWMA = sum(price * volume) / sum(volume)
        weighted_sum = sum(p * v for p, v in zip(prices, volumes))
        total_volume = sum(volumes)

        if total_volume == 0:
            vwma = None
        else:
            vwma = weighted_sum / total_volume

        # Append VWMA to the last slice
        self.AddColumn(vwma)

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
            self.AddColumn(None)
            return self.window

        # If this is the first RMA (less than period candles), use simple average
        if len(history) < period:
            rma = sum(history) / len(history)
        else:
            # Wilder's smoothing: RMA_today = (prev_RMA*(period-1) + current_value)/period
            prev_rma = history[-2] if len(history) > 1 else history[0]
            rma = (prev_rma * (period - 1) + history[-1]) / period

        self.AddColumn(rma)
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
            self.AddColumn(None)
            return self.window

        lag = (period - 1) // 2

        # Ensure sufficient history
        if len(self.window) <= lag or self.window[-1][idx] is None or self.window[-lag-1][idx] is None:
            # Append None for zero-lag column
            self.AddColumn(None)
            return self.window

        # Compute zero-lag value
        current_value = self.window[-1][idx]
        lagged_value = self.window[-lag-1][idx]
        zero_lag_value = current_value + (current_value - lagged_value)

        # Append the zero-lag value to the last row
        self.AddColumn(zero_lag_value)

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
            self.AddColumn(None)
            return self.window

        # Extract last 'period' values from the selected column
        series = [row[idx] for row in self.window[-period:] if len(row)>idx and row[idx] is not None]

        # Ensure sufficient history
        if len(series) < period:
            self.AddColumn(None)
            return self.window

        # If any value is None, return None
        if any(v is None for v in series):
            self.AddColumn(None)
            return self.window

        # Generate sine weights (0 -> pi)
        weights = [math.sin((i + 1) * math.pi / period) for i in range(period)]

        # Weighted sum / normalize
        weighted_sum = sum(val * w for val, w in zip(series, weights))
        sine_weighted_value = weighted_sum / sum(weights)

        # Append sine-weighted value to the last row
        self.AddColumn(sine_weighted_value)

        return self.window

    # Jurik moving average

    # The phase parameter in the JMA controls the relative shift of the smoothed
    # line with respect to the source price. Essentially, it allows the moving
    # average to be slightly advanced or delayed** in time. A negative phase**
    # moves the JMA slightly forward, which can reduce lag and make the
    # indicator respond faster to recent price changes, but it may also
    # introduce some overshoot. A positive phase** shifts the line backward,
    # increasing stability but also increasing lag. The phase value is scaled
    # and applied in the second stage of the JMA calculation, where it
    # multiplies the intermediate difference (`det0`) between the smoothed
    # EMA-like stage and the raw price, effectively adjusting the output along
    # the time axis.

    # The factor parameter, sometimes called the smoothing factor or “power,”
    # determines how strongly the JMA responds to changes in the input price. A
    # lower factor produces a smoother curve by reducing the weight of new
    # price movements, which filters out short-term noise but increases lag. A
    # higher factor increases sensitivity, allowing the JMA to follow price
    # more closely, but at the cost of more potential noise in the signal. In
    # the algorithm, the factor is used to compute the adaptive smoothing
    # coefficient (beta), which controls the recursive weighting of the
    # previous smoothed value versus the new input. This coefficient directly
    # influences the three-stage calculation that defines the JMA.

    # Together, the phase and factor parameters allow the JMA to balance
    # responsiveness and smoothness. Phase controls the horizontal alignment
    # of the moving average relative to price changes, while factor adjusts the
    # vertical responsiveness or sensitivity. By tuning these two parameters,
    # traders can achieve a moving average that is smoother than a standard EMA
    # or SMA while also reacting faster to trends, making the JMA a versatile
    # tool for trend detection and noise filtering.

    def JMA(self, idx=4, period=14, phase=0, factor=0.45):
        """
        Robust Jurik Moving Average (JMA) for rolling window.
        Works with any number of existing columns in the window.
        Automatically detects its own 4 state columns (ma1, det0, det1, jma).

        Appends 4 columns per row:
            [ma1, det0, det1, jma]
        """

        # Current source (default: close)

        source = self.window[-1][idx] if len(self.window) > 0 else None
        if source is None:
            self.AddColumn(None)
            self.AddColumn(None)
            self.AddColumn(None)
            self.AddColumn(None)
            return self.window

        # Determine start of JMA columns in previous row
        # If previous row exists and has >= 4 columns for JMA, use last 4 columns
        last_row = self.window[-2] if len(self.window) > 1 else None
        if last_row is None or last_row[0] is None:
            # First call: initialize previous JMA state
            last_ma1 = source
            last_det0 = 0.0
            last_det1 = 0.0
            last_jma = source
        else:
            # Always take the **last 4 columns of the previous row** as prior JMA state
            last_ma1, last_det0, last_det1, last_jma = last_row[-4:]

        # Pre-calculate constants
        phase_value = min(max((phase * 0.01) + 1.5, 0.5), 2.5)
        beta = factor * (period - 1) / ((factor * (period - 1)) + 2)
        len1 = max((math.log(math.sqrt(0.5 * (period - 1))) / math.log(2.0)) + 2.0, 0)
        pow1 = max(len1 - 2.0, 0.5)
        pow1Reciprocal = 1.0 / pow1

        # Adaptive smoothing parameters
        rvolty = 1.0  # fixed for strict JMA
        pow2 = rvolty ** pow1
        alpha = beta ** pow2
        alphaSquared = alpha ** 2
        oneMinusAlpha = 1.0 - alpha
        oneMinusAlphaSquared = oneMinusAlpha ** 2

        # Stage 1 - preliminary smoothing (adaptive EMA)
        ma1 = source + (alpha * (last_ma1 - source))

        # Stage 2 - Kalman-style adjustment
        det0 = (source - ma1) * (1 - beta) + beta * last_det0
        ma2 = ma1 + (phase_value * det0)

        # Stage 3 - final smoothing
        det1 = ((ma2 - last_jma) * oneMinusAlphaSquared) + (alphaSquared * last_det1)
        jma = last_jma + det1

        # Append new JMA columns to the current row
        self.AddColumn(ma1)
        self.AddColumn(det0)
        self.AddColumn(det1)
        self.AddColumn(jma)

        return self.window

    # Calculate Relative Strength Index (RSI) for the last candle in the window.

    def RSI(self, idx, period=14):
        # Collect the last 'period + 1' closing prices
        prices = [row[idx] for row in self.window[-(period+1):] if len(row)>idx and row[idx] is not None]

        if len(prices) < period + 1:
            # Not enough data to calculate RSI
            self.AddColumn(None)
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
        self.AddColumn(rsi)

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
            self.AddColumn(None)
            self.AddColumn(None)
            self.AddColumn(None)
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
                self.AddColumn(None)
                self.AddColumn(None)
                self.AddColumn(None)
                return self.window

            if None in [high, low, prev_high, prev_low, prev_close]:
                self.AddColumn(None)
                self.AddColumn(None)
                self.AddColumn(None)
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

        self.AddColumn(plus_di)
        self.AddColumn(minus_di)

        # DX = abs(+DI - -DI) / (+DI + -DI) * 100
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di) if (plus_di + minus_di) != 0 else 0

        # Calculate ADX recursively if previous ADX exists
        if len(self.window[-2]) >= 3 and self.window[-2][-1] is not None:
            prev_adx = self.window[-2][-1]
            adx = (prev_adx * (period - 1) + dx) / period
        else:
            adx = dx  # first ADX = first DX

        self.AddColumn(adx)

        return self.window

    def BollingerBands(self, idx, period=20, stddev_mult=2):
        """
        Calculate Bollinger Bands using an existing moving average column (idx).

        Appends to self.window[-1]:
            Mean, Variance, STD, Upper Band, Lower Band
        """

        n = len(self.window)

        if n < period:
            self.AddColumn(None)    # mean
            self.AddColumn(None)    # variance
            self.AddColumn(None)    # standard deviation
            self.AddColumn(None)    # upper band
            self.AddColumn(None)    # lower band
            return self.window

        series = [row[idx] for row in self.window[-period:] if len(row) > idx and row[idx] is not None]

        if len(series) < period:
            self.AddColumn(None)
            self.AddColumn(None)
            self.AddColumn(None)
            self.AddColumn(None)
            self.AddColumn(None)
            return self.window

        middle_band = self.window[-1][idx]  # existing MA
        mean = sum(series) / period
        variance = sum((x - mean) ** 2 for x in series) / period
        stddev = math.sqrt(variance)

        upper_band = middle_band + stddev_mult * stddev
        lower_band = middle_band - stddev_mult * stddev

        self.AddColumn(mean)
        self.AddColumn(variance)
        self.AddColumn(stddev)
        self.AddColumn(upper_band)
        self.AddColumn(lower_band)

        return self.window

    # Bollinger Bands %B

    def BollingerBandsB(self, CloseIDX, UpperBandIDX, LowerBandIDX):
        """
        Calculate Bollinger Bands %B (Percent B).
        %B = (Price - Lower Band) / (Upper Band - Lower Band)

        This indicator quantifies a security's price relative to the upper and lower
        Bollinger Bands. A value of 0.5 means the price is at the middle band, > 1 is
        above the upper band, and < 0 is below the lower band.

        Parameters:
            CloseIDX (int): The column index for the closing price.
            UpperBandIDX (int): The column index for the Upper Bollinger Band.
            LowerBandIDX (int): The column index for the Lower Bollinger Band.

        Appends to self.window[-1]:
            %B value
        """

        # Ensure there is at least one row to work with
        if not self.window:
            self.AddColumn(None)
            return self.window

        last_row = self.LastRow()

        # Check if all required column indices are valid for the last row
        required_indices = [CloseIDX, UpperBandIDX, LowerBandIDX]
        if len(last_row) <= max(required_indices):
            self.AddColumn(None)
            return self.window

        # Extract values from the last row
        close_price = last_row[CloseIDX]
        upper_band = last_row[UpperBandIDX]
        lower_band = last_row[LowerBandIDX]

        # Check if any of the necessary values are None
        if any(v is None for v in [close_price, upper_band, lower_band]):
            self.AddColumn(None)
            return self.window

        # Calculate the denominator (the range between the bands)
        band_range = upper_band - lower_band

        # Avoid division by zero if the bands have converged to the same value
        if band_range == 0:
            # If range is 0, %B is undefined. Can be set to 0.5 if price is on the band.
            # Appending None is safer to indicate an undefined state.
            pctb = 0
        else:
            # Calculate %B using the formula
            pctb = (close_price - lower_band) / band_range

        # Add the calculated %B value as a new column to the last row
        self.AddColumn(pctb)

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
            self.AddColumn(None)
            self.AddColumn(None)
            self.AddColumn(None)
            return self.window

        fast = self.window[-1][idxFAST]
        slow = self.window[-1][idxSLOW]

        if fast is None or slow is None:
            self.AddColumn(None)
            self.AddColumn(None)
            self.AddColumn(None)
            return self.window

        # MACD line
        macd_value = fast - slow
        self.AddColumn(macd_value)

        # If no custom signal_func is provided, use EMA as default
        if signal_func is None:
            signal_func = self.EMA

        # Prepare a synthetic column for MACD line temporarily
        temp_idx = len(self.window[-1]) - 1  # MACD column index
        # Apply the moving average function to get the signal line
        signal_func(temp_idx, period)

        # The signal line is appended at the last column
        signal_idx = len(self.window[-1]) - 1
        signal_value = self.window[-1][signal_idx]

        # Histogram = MACD - Signal
        histogram = macd_value - signal_value if signal_value is not None else None
        self.AddColumn(histogram)

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
            self.AddColumn(None)
            self.AddColumn(None)
            return self.window

        row = self.window[-1]
        prev_row = self.window[-2]

        # Check for missing data
        if (len(row) <= max(high_idx, low_idx, close_idx)
        or len(prev_row) <= close_idx or row[high_idx] is None
        or row[low_idx] is None or row[close_idx] is None
        or prev_row[close_idx] is None):
            self.AddColumn(None)
            self.AddColumn(None)
            return self.window

        # Calculate True Range (TR)
        high = row[high_idx]
        low = row[low_idx]
        prev_close = prev_row[close_idx]

        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        self.AddColumn(tr)
        tr_idx = len(self.window[-1]) - 1  # index of TR in row

        # Collect TR values for initial ATR calculation
        TRs = []
        for r in self.window[-period:]:
            if len(r) > tr_idx and r[tr_idx] is not None:
                TRs.append(r[tr_idx])

        # If we have exactly 'period' TRs, set initial ATR as simple average
        if len(TRs) == period:
            initial_atr = sum(TRs) / period
            self.AddColumn(initial_atr)
        else:
            # Apply chosen smoothing function to TR
            smooth_func(tr_idx, malen)

        return self.window

    # Stochastic indicator

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
            self.AddColumn(None)
            self.AddColumn(None)
            self.AddColumn(None)
            return self.window

        # Extract last k_period highs, lows, closes
        highs = [row[high_idx] for row in self.window[-k_period:] if len(row) > high_idx and row[high_idx] is not None]
        lows = [row[low_idx] for row in self.window[-k_period:] if len(row) > low_idx and row[low_idx] is not None]
        closes = [row[close_idx] for row in self.window[-k_period:] if len(row) > close_idx and row[close_idx] is not None]

        if len(highs) < k_period or len(lows) < k_period or len(closes) < k_period:
            self.AddColumn(None)
            self.AddColumn(None)
            self.AddColumn(None)
            return self.window

        high_max = max(highs)
        low_min = min(lows)
        close_last = closes[-1]

        if high_max == low_min:
            raw_k = 0.0
        else:
            raw_k = 100 * (close_last - low_min) / (high_max - low_min)

        # Append raw %K first
        self.AddColumn(raw_k)
        k_idx = len(self.window[-1]) - 1

        # Smooth %K using moving average (k_smooth)
        if ma_func is None:
            ma_func = self.EMA
        ma_func(k_idx, k_smooth)
        smoothed_k = self.window[-1][-1]  # %K smoothed

        # Append smoothed %K
        d_idx = len(self.window[-1]) - 1

        # Smooth %D using moving average (d_smooth) of smoothed %K
        ma_func(d_idx, d_smooth)

        return self.window

    # Williams %R

    def WilliamsR(self, high_idx, low_idx, close_idx, period=14):
        """
        Calculate Williams %R for the last candle in the window.

        Parameters:
            high_idx (int): Column index for high prices
            low_idx (int): Column index for low prices
            close_idx (int): Column index for close prices
            period (int): Lookback period (default 14)

        Appends to self.window[-1]:
            Williams %R
        """

        n = len(self.window)
        if n < period:
            self.AddColumn(None)
            return self.window

        highs = [row[high_idx] for row in self.window[-period:] if len(row) > high_idx and row[high_idx] is not None]
        lows = [row[low_idx] for row in self.window[-period:] if len(row) > low_idx and row[low_idx] is not None]
        closes = [row[close_idx] for row in self.window[-period:] if len(row) > close_idx and row[close_idx] is not None]

        if len(highs) < period or len(lows) < period or len(closes) < period:
            self.AddColumn(None)
            return self.window

        high_max = max(highs)
        low_min = min(lows)
        close_last = closes[-1]

        if high_max == low_min:
            wr = 0.0
        else:
            wr = -100 * (high_max - close_last) / (high_max - low_min)

        self.AddColumn(wr)
        return self.window

    # Calculate the volatility, stand interpretation

    def Volatility(self, CloseIDX=4, periods=19):
        # Ensure there are enough data points
        if len(self.window) < periods:
            self.AddColumn(None)
            return self.window

        # Extract the last 'period' closing prices
        close_prices = [row[CloseIDX] for row in self.window[-periods:] if row[CloseIDX] is not None]

        # Require at least two valid prices
        if len(close_prices) < periods:
            self.AddColumn(None)
            return self.window

        # Calculate daily returns
        returns = []
        for i in range(1, len(close_prices)):
            prev_close = close_prices[i - 1]
            curr_close = close_prices[i]
            if prev_close != 0:
                daily_return = (curr_close - prev_close) / prev_close
                returns.append(daily_return)

        if len(returns) < 2:
            self.AddColumn(None)
            return self.window

        # Calculate the standard deviation of returns
        n = len(returns)
        mean_return = sum(returns) / n
        sum_squared_diff = sum((r - mean_return) ** 2 for r in returns)
        volatility = (sum_squared_diff / (n - 1)) ** 0.5

        self.AddColumn(volatility)

        return self.window

    # MY custom verion of volatility

    # This function is intentionally not a statistical volatility estimator but a
    # grid spacing control derived from return dispersion, where the standard
    # deviation of simple returns is converted into an absolute price distance by
    # multiplying by the current price and then deliberately damped by dividing by
    # the lookback period. In unstable markets, increased return variance causes
    # RDVolatility() to grow, which widens the distance between successive grid
    # levels and automatically slows inventory accumulation, while sustained
    # instability does not cause unbounded expansion because the division by
    # periods suppresses time based amplification. Direction is irrelevant in this
    # architecture because each new order is placed relative to the last filled
    # position rather than a fixed anchor, so price drift is absorbed sequentially
    # instead of predicted or opposed. This makes the RDVolatility function as a
    # bounded volatility aware throttle that controls how aggressively the grid
    # adds exposure under dispersion, rather than as a measure of uncertainty or
    # forecasted movement. The result is a spacing mechanism that widens during
    # volatility shocks, stabilizes during prolonged regimes, and remains effective
    # in slow carry driven markets as well as unstable mean reverting conditions,
    # which is why it is suitable for long running live grid systems even though it
    # should not be interpreted or reused as conventional volatility.

    # periods of 13 for Forex, 19 for crypto work best.

    def RDVolatility(self, CloseIDX=4, periods=19):
        # Ensure there are enough data points
        if len(self.window) < periods:
            self.AddColumn(None)
            return self.window

        # Extract the last 'period' closing prices
        close_prices = [row[CloseIDX] for row in self.window[-periods:] if row[CloseIDX] is not None]

        # Require at least two valid prices
        if len(close_prices) < periods:
            self.AddColumn(None)
            return self.window

        # Calculate returns

        returns=[]
        for i in range(1,len(close_prices)):
            daily_return=(close_prices[i]-close_prices[i-1])/close_prices[i-1]
            returns.append(daily_return)

        # Calculate the standard deviation of returns as volatility

        n=len(returns)
        mean_return=sum(returns)/n
        sum_squared_diff=sum((r-mean_return)**2 for r in returns)
        volatility=(sum_squared_diff/(n-1))**0.5

        self.AddColumn((volatility*close_prices[-1])/periods)

        return self.window

    # Calculate the Avellaneda Stoikov volatility based on the OHLCV data versus
    # bid/ask ticker.

    def ASVolatility(self, CloseIDX=4, periods=19):
        # Not enough data
        if len(self.window) < periods:
            self.AddColumn(None)   # log return
            self.AddColumn(None)   # mean
            self.AddColumn(None)   # variance
            self.AddColumn(None)   # sigma
            return self.window

        # Extract last-period closes
        closes = [row[CloseIDX] for row in self.window[-periods:] if row[CloseIDX] is not None]

        # Require full period of valid closes
        if len(closes) < periods:
            self.AddColumn(None)   # log return
            self.AddColumn(None)   # mean
            self.AddColumn(None)   # variance
            self.AddColumn(None)   # sigma
            return self.window

        # Compute log returns
        log_returns = []
        for i in range(1, len(closes)):
            c1 = closes[i - 1]
            c2 = closes[i]
            if c1 != 0:
                lr = math.log(c2 / c1)
                log_returns.append(lr)

        # Store last log return (intermediate)
        self.AddColumn(log_returns[-1] if log_returns else None)

        if len(log_returns) < 2:
            self.AddColumn(None)   # mean
            self.AddColumn(None)   # variance
            self.AddColumn(None)   # sigma
            return self.window

        # Mean of log returns
        n = len(log_returns)
        mean_r = sum(log_returns) / n
        self.AddColumn(mean_r)

        # Compute variance
        var_sum = sum((r - mean_r) ** 2 for r in log_returns)
        variance = var_sum / (n - 1)
        self.AddColumn(variance)

        # Sigma
        sigma = variance ** 0.5
        self.AddColumn(sigma)

        return self.window

    # Calculate the Black Scholes volatility

    def BSVolatility(self, CloseIDX=4, periods=19):
        # Not enough rows
        if len(self.window) < periods:
            self.AddColumn(None)   # last return
            self.AddColumn(None)   # mean
            self.AddColumn(None)   # variance
            self.AddColumn(None)   # sigma
            return self.window

        # Extract recent closes
        closes = [row[CloseIDX] for row in self.window[-periods:] if row[CloseIDX] is not None]

        # Require full period
        if len(closes) < periods:
            self.AddColumn(None)
            self.AddColumn(None)
            self.AddColumn(None)
            self.AddColumn(None)
            return self.window

        # Compute simple returns
        returns = []
        for i in range(1, len(closes)):
            p1 = closes[i - 1]
            p2 = closes[i]
            if p1 != 0:
                r = (p2 - p1) / p1
                returns.append(r)

        # Store last return
        self.AddColumn(returns[-1] if returns else None)

        # Need at least two
        if len(returns) < 2:
            self.AddColumn(None)
            self.AddColumn(None)
            self.AddColumn(None)
            return self.window

        # Mean return
        n = len(returns)
        mean_r = sum(returns) / n
        self.AddColumn(mean_r)

        # Variance
        var_sum = 0.0
        for r in returns:
            diff = r - mean_r
            var_sum += diff * diff

        variance = var_sum / (n - 1)
        self.AddColumn(variance)

        # Historical sigma
        sigma = variance ** 0.5
        self.AddColumn(sigma)

        return self.window

    # Find the current support level

    def Support(self, low_idx=3, period=14):
        """
        Calculate support levels for a specified column over a rolling window.

        Parameters:
            low_idx (int): Index of the column representing lows (e.g., low prices)
            period (int): Number of candles to consider for support (default 14)

        Returns:
            self.window: The rolling window updated with a support level appended
                         to the last row.
        """
        # Ensure enough history exists
        if len(self.window) < period:
            self.AddColumn(None)
            return self.window

        # Extract lows from the last 'period' candles
        lows = [row[low_idx] for row in self.window[-period:] if len(row) > low_idx and row[low_idx] is not None]

        if len(lows)<period:
            self.AddColumn(None)
            return self.window

        # Support level = minimum low in the period
        support_level = min(lows)

        # Append to the last row of the rolling window
        self.AddColumn(support_level)
        return self.window

    # Find resistance levels

    def Resistance(self, high_idx=2, period=14):
        """
        Calculate resistance levels for a specified column over a rolling window.

        Parameters:
            high_idx (int): Index of the column representing highs (e.g., high prices)
            period (int): Number of candles to consider for resistance (default 14)

        Returns:
            self.window: The rolling window updated with a resistance level appended
                         to the last row.
        """
        # Ensure enough history exists
        if len(self.window) < period:
            self.AddColumn(None)
            return self.window

        # Extract highs from the last 'period' candles
        highs = [row[high_idx] for row in self.window[-period:] if len(row) > high_idx and row[high_idx] is not None]

        if len(highs)<period:
            self.AddColumn(None)
            return self.window

        # Resistance level = maximum high in the period
        resistance_level = max(highs)

        # Append to the last row of the rolling window
        self.AddColumn(resistance_level)
        return self.window

    # Parabolic SAR

    def PSAR(self, HighIDX=2, LowIDX=3, startAF=0.02, stepAF=0.02, maxAF=0.2):
        """
        Compute Parabolic SAR for the current window, fully transparent,
        and append all intermediate values as new columns:
        SAR, Trend (1=up, -1=down), Extreme Point (EP), Acceleration Factor (AF)
        """
        n = len(self.window)

        # Ensure enough data to compute
        if n < 2 or self.window[-2][HighIDX] is None or self.window[-2][LowIDX] is None:
            self.AddColumn(None)  # SAR
            self.AddColumn(None)  # Trend
            self.AddColumn(None)  # EP
            self.AddColumn(None)  # AF
            return self.window

        prev_row = self.window[-2]
        curr_row = self.window[-1]

        sarIDX=len(prev_row)-4

        # Read previous SAR, trend, EP, AF if they exist
        prev_sar = prev_row[sarIDX] if prev_row[sarIDX] is not None else prev_row[LowIDX]  # initial guess
        prev_trend = prev_row[sarIDX+1] if len(prev_row) > sarIDX+1 and prev_row[sarIDX+1] is not None else 1               # assume uptrend
        prev_ep = prev_row[sarIDX+2] if len(prev_row) > sarIDX+2 and prev_row[sarIDX+2] is not None else prev_row[HighIDX]
        prev_af = prev_row[sarIDX+3] if len(prev_row) > sarIDX+3 and prev_row[sarIDX+3] is not None else startAF

        # Determine current trend
        trend = prev_trend
        ep = prev_ep
        af = prev_af
        sar = prev_sar

        # Update SAR
        sar = sar + af * (ep - sar)

        # Check for trend reversal
        if trend == 1:  # Uptrend
            if curr_row[LowIDX] < sar:
                trend = -1
                sar = ep
                ep = curr_row[LowIDX]
                af = startAF
            else:
                if curr_row[HighIDX] > ep:
                    ep = curr_row[HighIDX]
                    af = min(af + stepAF, maxAF)
        else:  # Downtrend
            if curr_row[HighIDX] > sar:
                trend = 1
                sar = ep
                ep = curr_row[HighIDX]
                af = startAF
            else:
                if curr_row[LowIDX] < ep:
                    ep = curr_row[LowIDX]
                    af = min(af + stepAF, maxAF)

        # Append results as new columns
        self.AddColumn(sar)     # SAR
        self.AddColumn(trend)   # Trend: 1=up, -1=down
        self.AddColumn(ep)      # Extreme Point
        self.AddColumn(af)      # Acceleration Factor

        return self.window

    # Momentum indicator

    def Momentum(self, colIDX, period=10):
        """
        Calculate momentum for a given column index and period.
        Momentum = Current value - value N periods ago
        Appends the result as a new column in the rolling window.

        :param colIDX: int, the column index in the rolling window to calculate momentum on
        :param period: int, number of periods to look back
        """

        # Get the last row
        last_row = self.LastRow()

        # Ensure there is enough history
        if len(self.window) < period+1:
            self.AddColumn(None)
            return self.window

        # Calculate momentum
        if len(self.window[-(period + 1)])<colIDX+1:
            self.AddColumn(None)
            return self.window

        past_value = self.window[-(period + 1)][colIDX]
        if past_value is None:
            self.AddColumn(None)
            return self.window

        current_value = last_row[colIDX]

        if past_value is not None and current_value is not None:
            momentum = current_value - past_value
        else:
            momentum = None

        # Add momentum as new column
        self.AddColumn(momentum)
        return self.window

    def RateOfChange(self, colIDX, period=10,absolute=False):
        """
        Calculate the Rate of Change (ROC) for a given column index over a specified period.
        ROC = ((current value - value N periods ago) / value N periods ago) * 100
        The result is appended as a new column to the rolling window.

        Parameters:
            colIDX (int): Column index to calculate ROC from
            period (int): Number of periods for the ROC calculation
        """
        last_row = self.LastRow()

        # Check if enough rows exist
        if len(self.window) > period:
            past_row = self.window[-period-1]  # Row N periods ago
            if len(past_row)<colIDX+1:
                roc = None
            else:
                current_value = last_row[colIDX]
                past_value = past_row[colIDX]

                if current_value is not None and past_value is not None:
                    if past_value==0:
                        roc=0
                    else:
                        if absolute:
                            roc=(abs((current_value-past_value))/(current_value+past_value)) * 100
                        else:
                            roc=((current_value-past_value)/(current_value+past_value)) * 100
                else:
                    roc = None
        else:
            roc = None

        # Add ROC as a new column
        self.AddColumn(roc)
        return self.window

    # On Balance Volume

    def OBV(self, closeIDX=4, volumeIDX=5):
        """
        Calculate On-Balance Volume (OBV) based on closing prices and volume.
        OBV increases by volume when the closing price rises,
        decreases by volume when the closing price falls,
        remains unchanged if the price is the same.

        Parameters:
            closeIDX (int): Column index of the closing price
            volumeIDX (int): Column index of the volume
        """
        if len(self.window)<1:
            self.AddColumn(None)
            return self.window

        last_row = self.LastRow()
        prevIDX=len(last_row)   # Get the right idx for the OBV
        prev_row = self.window[-2]  # Previous row

        close_now = last_row[closeIDX]
        close_prev = prev_row[closeIDX]
        vol_now = last_row[volumeIDX]
        if len(prev_row)<prevIDX+1:
            self.AddColumn(vol_now)
            return self.window

        obv_prev = prev_row[prevIDX] if prev_row[prevIDX] is not None else vol_now  # Use last column as previous OBV

        if close_now is not None and close_prev is not None and vol_now is not None:
            if close_now > close_prev:
                obv = obv_prev + vol_now
            elif close_now < close_prev:
                obv = obv_prev - vol_now
            else:
                obv = obv_prev
        else:
            obv = vol_now

        # Add OBV as a new column
        self.AddColumn(obv)
        return self.window

    # Volume Price Trend (VPT) indicator

    def VolumePriceTrend(self, OpenIDX=1, HighIDX=2, LowIDX=3, CloseIDX=4, VolIDX=5):
        if len(self.window) < 2 or self.window[-2][0] is None:
            self.AddColumn(0.0)   # Initialize VPT at 0 for the first row
            return self.window

        prev_row = self.GetRow(-2)
        last_row = self.LastRow()

        c1 = prev_row[CloseIDX]
        c2 = last_row[CloseIDX]
        v2 = last_row[VolIDX]

        # Retrieve last VPT (already stored in column), if available
        prev_vpt = self.window[-2][-1] if self.window[-2][-1] is not None else 0.0

        vpt = prev_vpt

        if c1 != 0:  # avoid division by zero
            vpt = prev_vpt + v2 * ((c2 - c1) / c1)

        self.AddColumn(vpt)
        return self.window

    # Volume Weighted Average Price (VWAP) indicator

    def VWAP(self, OpenIDX=1, HighIDX=2, LowIDX=3, CloseIDX=4, VolIDX=5):
        if len(self.window) < 2 or self.window[-1][0] is None:
            # Add 3 columns: TP*V cumulative, Volume cumulative, VWAP
            self.AddColumn(None)  # cum TP*V
            self.AddColumn(None)  # cum Vol
            self.AddColumn(None)  # VWAP
            return self.window

        if len(self.window)==1:
            prev_cum_pv = 0.0
            prev_cum_vol = 0.0
        else:
            prev_cum_pv = self.window[-2][-3] if self.window[-2][-3] is not None else 0.0
            prev_cum_vol = self.window[-2][-2] if self.window[-2][-2] is not None else 0.0

        last_row = self.LastRow()

        h = last_row[HighIDX]
        l = last_row[LowIDX]
        c = last_row[CloseIDX]
        v = last_row[VolIDX]

        tp = (h + l + c) / 3.0   # Typical Price

        cum_pv = prev_cum_pv + tp * v
        cum_vol = prev_cum_vol + v

        vwap = None
        if cum_vol != 0:
            vwap = cum_pv / cum_vol

        # Add 3 transparent columns
        self.AddColumn(cum_pv)
        self.AddColumn(cum_vol)
        self.AddColumn(vwap)

        return self.window

    # Vortex Indicator (VI) implementation
    # Based on Etienne Botes and Douglas Siepman's formula

    # Detects positive (VI+) and negative (VI-) trend movement using high, low,
    # close values.

    def Vortex(self, OpenIDX=1, HighIDX=2, LowIDX=3, CloseIDX=4, period=14):
        """
        Calculate the Vortex Indicator (VI) over a rolling window.

        Parameters:
            period (int): Period for the calculation (default = 14).
            OpenIDX (int): Index of Open in the OHLCV row.
            HighIDX (int): Index of High in the OHLCV row.
            LowIDX (int): Index of Low in the OHLCV row.
            CloseIDX (int): Index of Close in the OHLCV row.

        Adds 3 columns per row:
            - VI+ : Positive Vortex line (bullish strength).
            - VI- : Negative Vortex line (bearish strength).
            - TR  : True Range of the current bar (for traceability).

        Formula:
            VM+ = |H_t - L_{t-1}|
            VM- = |L_t - H_{t-1}|
            TR  = max(H_t - L_t, |H_t - C_{t-1}|, |L_t - C_{t-1}|)

            VI+ = sum(VM+ over N) / sum(TR over N)
            VI- = sum(VM- over N) / sum(TR over N)

        Interpretation:
            - VI+ rising above VI- suggests bullish trend continuation.
            - VI- rising above VI+ suggests bearish trend continuation.
        """

        if len(self.window)<period or self.window[-2][0] is None:
            self.AddColumn(None)  # VI+
            self.AddColumn(None)  # VI-
            self.AddColumn(None)  # TR
            return self.window

        prev_row = self.GetRow(-2)
        last_row = self.LastRow()

        h1, l1, c1 = prev_row[HighIDX], prev_row[LowIDX], prev_row[CloseIDX]
        h2, l2, c2 = last_row[HighIDX], last_row[LowIDX], last_row[CloseIDX]

        # True Range of the current bar
        tr = max(h2 - l2, abs(h2 - c1), abs(l2 - c1))

        # Initialize series for last N values
        vm_plus_series = []
        vm_minus_series = []
        tr_series = []

        count = 0
        # Walk back N periods to compute rolling sums
        for i in range(-period+1, 1):
            if -i <= len(self.window):
                row = self.GetRow(i)
                if row is not None and row[0] is not None:
                    prow=self.GetRow(i-1)
                    ph, pl, pc = prow[HighIDX], prow[LowIDX], prow[CloseIDX]
                    ch, cl, cc = row[HighIDX], row[LowIDX], row[CloseIDX]

                    if None in [ch, cl, cc, ph, pl, pc]:
                        continue

                    # TR for this bar
                    t = max(ch - cl, abs(ch - pc), abs(cl - pc))
                    # Upward movement
                    vp = abs(ch - pl)
                    # Downward movement
                    vm = abs(cl - ph)

                    vm_plus_series.append(vp)
                    vm_minus_series.append(vm)
                    tr_series.append(t)
                    count += 1

        # Compute VI+ and VI- if enough data
        if count < period-1:
            vi_plus, vi_minus = None, None
        else:
            sum_vm_plus = sum(vm_plus_series)
            sum_vm_minus = sum(vm_minus_series)
            sum_tr = sum(tr_series)
            vi_plus = sum_vm_plus / sum_tr if sum_tr != 0 else None
            vi_minus = sum_vm_minus / sum_tr if sum_tr != 0 else None

        # Add results as new columns
        self.AddColumn(vi_plus)
        self.AddColumn(vi_minus)
        self.AddColumn(tr)

        return self.window

    # Aroon Indicator
    # Returns Aroon Up and Aroon Down as two new columns
    # period: lookback length for high/low

    # The Aroon indicator is primarily used to identify trends and trend
    # strength in a market. The Aroon Up measures the time since the most
    # recent high within a lookback period, while the Aroon Down measures the
    # time since the most recent low. Values near 100 indicate a strong trend
    # in that direction, and values near 0 indicate a weak trend or potential
    # consolidation. A common approach is to look for crossovers: when Aroon Up
    # crosses above Aroon Down, it signals a possible bullish trend, and when
    # Aroon Down crosses above Aroon Up, it signals a potential bearish trend.
    # Traders often combine Aroon with other indicators, such as moving
    # averages or volume analysis, to confirm trends and avoid false signals.
    # It is also useful to monitor divergences between price and the Aroon
    # values to detect weakening momentum before a reversal occurs.

    def Aroon(self, HighIDX=2, LowIDX=3, period=14):
        if len(self.window) < period:
            self.AddColumn(None)   # Aroon Up
            self.AddColumn(None)   # Aroon Down
            return self.window

        highs = [row[HighIDX] for row in self.window[-period:]]
        lows = [row[LowIDX] for row in self.window[-period:]]

        highest_idx = highs.index(max(highs))
        lowest_idx = lows.index(min(lows))

        aroon_up = ((period - highest_idx - 1) / (period - 1)) * 100
        aroon_down = ((period - lowest_idx - 1) / (period - 1)) * 100

        self.AddColumn(aroon_up)
        self.AddColumn(aroon_down)

        return self.window

    # Ichimoku Cloud signal function
    def IchimokuCloud(self, tenkan_idx, kijun_idx, senkouA_idx, senkouB_idx, chikou_idx, close_idx=4):
        # Not enough data yet
        if len(self.window) < 2:
            # Cross already adds two columns (diff, cross)
            self.AddColumn(None)  # Cloud signal
            self.AddColumn(None)  # Chikou signal
            return self.window

        last_row = self.LastRow()
        if any(last_row[i] is None for i in [tenkan_idx, kijun_idx, senkouA_idx, senkouB_idx, chikou_idx, close_idx]):
            self.AddColumn(None)  # Cloud signal
            self.AddColumn(None)  # Chikou signal
            self.AddColumn(None)
            self.AddColumn(None)
            self.AddColumn(None)
            self.AddColumn(None)
            return self.window

        # 1. TK Cross using your Cross function (this appends 2 columns automatically)
        self.Cross(tenkan_idx, kijun_idx)

        # 2. Cloud signal (price vs cloud)
        price = last_row[close_idx]
        senkouA = last_row[senkouA_idx]
        senkouB = last_row[senkouB_idx]

        upper = max(senkouA, senkouB)
        lower = min(senkouA, senkouB)

        if price > upper:
            cloud_signal = 1   # bullish
        elif price < lower:
            cloud_signal = -1  # bearish
        else:
            cloud_signal = 0   # neutral (inside the cloud)

        self.AddColumn(cloud_signal)

        # 3. Chikou confirmation (lagging span vs price)
        chikou = last_row[chikou_idx]
        if chikou > price:
            chikou_signal = 1
        elif chikou < price:
            chikou_signal = -1
        else:
            chikou_signal = 0

        self.AddColumn(chikou_signal)

        return self.window

    ## Gann section

    # How to use these in a Strategy

    # Gann Fan: Tells you the strength of the trend (is it above the 1x1 line?).
    #
    # Gann HiLo Activator: Tells you the entry/exit trigger. Buy when Trend
    # flips to 1. Sell when it flips to -1.
    #
    # Square of 9: Tells you the Take Profit. If you buy at
    #   $100 and the Next Resistance column says $108, that is your geometric
    #   exit target.

    # Gann Fan
    #   Long Strategy: Anchor to Low. Lines slope Up. Price staying above
    #   1x1 is bullish.
    #   Short Strategy: Anchor to High. Lines slope Down. Price staying
    #   below 1x1 is bearish.
    #
    # Gann HiLo
    #   Long Strategy: Automatic. If Price > SMA(High), the Activator line
    #   is Support.
    #   Short Strategy: Automatic. If Price < SMA(Low), the Activator line
    #   is Resistance.
    #
    # Square of 9
    #   Long Strategy: Anchor to Low. Calculate targets by adding to the
    #   square root.
    #   Short Strategy: Anchor to High. Calculate targets by subtracting
    #   from the square root.

    # WD Gann Fan Indicator
    # Turns the geometric drawing tool into a numerical indicator.
    #
    # This implementation automatically finds the anchor point (Lowest Low
    # for Long, Highest High for Short) within the lookback period.
    #
    # Columns added to the window:
    # 1. Anchor Price: The price point used as the origin (0,0) of the fan.
    # 2. Time Delta: The number of bars (x-axis) since the anchor occurred.
    # 3. 2x1 Angle: The fast/aggressive trend line (2 units price per 1
    #               unit time).
    # 4. 1x1 Angle: The "Balance" line (1 unit price per 1 unit time).
    # 5. 1x2 Angle: The slow/support trend line (1 unit price per 2 units time).
    #
    # Parameters:
    # scale: The "Price Units per Bar". CRITICAL. If None, it auto-calculates
    #        based on the average range of the lookback period (Scale =
    #        Range / Time). For manual tuning: Crypto (~10-100), Forex
    #        (~0.0001).
    # direction: 'long' (anchors to Lows, projects up) or 'short' (anchors
    #             to Highs, projects down).

    def GannFan(self, HighIDX=2, LowIDX=3, lookback=50, scale=None, direction='long'):
        # Ensure enough history exists
        if len(self.window) < lookback:
            self.AddColumn(None) # Anchor Price
            self.AddColumn(None) # Time Delta
            self.AddColumn(None) # 2x1
            self.AddColumn(None) # 1x1
            self.AddColumn(None) # 1x2
            return self.window

        # Extract the relevant slice for analysis
        # We need to find the anchor within the lookback window
        window_slice = self.window[-lookback:]

        # 1. FIND THE ANCHOR
        anchor_price = None
        time_delta = 0

        if direction.lower() == 'short':
            # Find Highest High
            highs = [row[HighIDX] for row in window_slice if row[HighIDX] is not None]
            if not highs:
                for _ in range(5): self.AddColumn(None)
                return self.window

            anchor_price = max(highs)

            # Find the relative index of that high (0 is the oldest in
            # slice, -1 is current) We reverse list to find the *most
            # recent* occurrence if there are duplicates relative_idx from
            # the end

            rev_highs = highs[::-1]
            idx_from_end = rev_highs.index(anchor_price)
            time_delta = idx_from_end # 0 means the anchor is the current bar
        else:
            # Default 'long': Find Lowest Low
            lows = [row[LowIDX] for row in window_slice if row[LowIDX] is not None]
            if not lows:
                for _ in range(5): self.AddColumn(None)
                return self.window

            anchor_price = min(lows)
            rev_lows = lows[::-1]
            idx_from_end = rev_lows.index(anchor_price)
            time_delta = idx_from_end

        # 2. DETERMINE SCALE (The Geometric Aspect) If scale is not
        # provided, we auto-fit it to the box size to ensure 45-degree
        # visually represents the trend of the lookback period.

        calc_scale = scale
        if calc_scale is None or calc_scale == 'auto':

            # Simple heuristic: Average Range / Lookback
            # This prevents the fan from being vertical or flat on untuned assets
            range_max = float("-inf")
            range_min = float("inf")
            for row in window_slice:
                 if row[HighIDX] is not None: range_max = max(range_max, row[HighIDX])
                 if row[LowIDX] is not None: range_min = min(range_min, row[LowIDX])

            if range_max > range_min:
                calc_scale = (range_max - range_min) / lookback
            else:
                calc_scale = 1.0

        # 3. CALCULATE GANN ANGLES (y = mx + b)
        # For 'long', lines go UP (+). For 'short', lines go DOWN (-).

        factor = 1 if direction.lower() == 'long' else -1

        # 1x1 is the balance line
        gann_1x1 = anchor_price + (factor * calc_scale * time_delta)

        # 2x1 is the fast line (Steeper)
        # Price moves 2 units for every 1 unit of time
        gann_2x1 = anchor_price + (factor * (calc_scale * 2) * time_delta)

        # 1x2 is the slow line (Flatter)
        # Price moves 0.5 units for every 1 unit of time
        gann_1x2 = anchor_price + (factor * (calc_scale * 0.5) * time_delta)

        # 4. APPEND COLUMNS (Transparency)
        self.AddColumn(anchor_price)
        self.AddColumn(time_delta)
        self.AddColumn(gann_2x1)
        self.AddColumn(gann_1x1)
        self.AddColumn(gann_1x2)

        return self.window

    # Gann High-Low Activator (GHLA)
    # A trend-following indicator that acts as a trailing stop/reversal signal.

    def GannHiLoActivator(self, HighIDX=2, LowIDX=3, CloseIDX=4, period=3):
        # Need enough history for the MA
        if len(self.window) < period + 1:
            self.AddColumn(None) # SMA High
            self.AddColumn(None) # SMA Low
            self.AddColumn(None) # Trend
            self.AddColumn(None) # Activator Line
            return self.window

        # 1. Calculate Simple Moving Averages of Highs and Lows
        highs = [row[HighIDX] for row in self.window[-period:] if row[HighIDX] is not None]
        lows = [row[LowIDX] for row in self.window[-period:] if row[LowIDX] is not None]

        if len(highs) < period or len(lows) < period:
            self.AddColumn(None)
            self.AddColumn(None)
            self.AddColumn(None)
            self.AddColumn(None)
            return self.window

        sma_high = sum(highs) / period
        sma_low = sum(lows) / period

        # 2. Determine Trend based on previous state
        # Get previous row
        prev_row = self.window[-2]
        curr_row = self.window[-1]
        close = curr_row[CloseIDX]

        # We need to find the previous trend state.
        # Since this adds 4 columns, we look back 4 columns in the previous row.
        # If it's the first run, default to trend based on current close vs SMA.
        prev_trend_idx = len(prev_row) - 2 # Trend is the 3rd column added

#        if len(prev_row) > prev_trend_idx and prev_row[prev_trend_idx] is not None:
#            trend = prev_row[prev_trend_idx]
#        else:
        # Initialize: If close > SMA_High, Bullish (1), else Bearish (-1)
        trend=0
        if close>sma_high:
            trend=1
        if close<sma_low:
            trend=-1

        """
        # 3. Update Trend Logic
        # If we were Bullish (1) and Close breaks below SMA_Low -> Flip to Bearish
        if trend == 1:
            if close < sma_low:
                trend = -1
        # If we were Bearish (-1) and Close breaks above SMA_High -> Flip to Bullish
        else:
            if close > sma_high:
                trend = 1
        """
        # 4. Determine the Activator Value (The line to plot)
        # If Bullish, the stop is the Low MA. If Bearish, the stop is the High MA.
        activator = sma_low if trend == 1 else sma_high

        # 5. Append Columns
        self.AddColumn(sma_high)
        self.AddColumn(sma_low)
        self.AddColumn(trend)
        self.AddColumn(activator)

        return self.window

    # Gann Square of 9 (Bidirectional)
    # Calculates dynamic support/resistance levels.
    #
    # Parameters:
    # direction: 'long' (Anchors to Low, targets Higher) 
    #            'short' (Anchors to High, targets Lower)

    def GannSquareOfNine(self, HighIDX=2, LowIDX=3, CloseIDX=4, period=100, direction='long'):
        if len(self.window) < period:
            self.AddColumn(None) # Anchor
            self.AddColumn(None) # Degrees
            self.AddColumn(None) # Next Level (Target)
            self.AddColumn(None) # Major Level (Trailing Stop)
            return self.window

        current_price = self.window[-1][CloseIDX]
        if current_price is None:
            self.AddColumn(None)
            self.AddColumn(None)
            self.AddColumn(None)
            self.AddColumn(None)
            return self.window

        # 1. FIND ANCHOR and DEFINE MATH
        if direction.lower() == 'short':
            # Find Highest High
            slice_vals = [row[HighIDX] for row in self.window[-period:] if row[HighIDX] is not None]
            if not slice_vals:
                self.AddColumn(None)
                self.AddColumn(None)
                self.AddColumn(None)
                self.AddColumn(None)
                return self.window

            anchor = max(slice_vals)

            # Math: Shorting means Price < Anchor.
            # We measure how much we have fallen (Contracting spiral).
            # Diff is positive representing distance traveled downwards.
            sqrt_anchor = math.sqrt(anchor)
            sqrt_price = math.sqrt(current_price)
            diff = sqrt_anchor - sqrt_price

            # Logic: We are subtracting from the Anchor's root
            math_op = -1
        else:
            # Default Long: Find Lowest Low
            slice_vals = [row[LowIDX] for row in self.window[-period:] if row[LowIDX] is not None]
            if not slice_vals:
                self.AddColumn(None)
                self.AddColumn(None)
                self.AddColumn(None)
                self.AddColumn(None)
                return self.window

            anchor = min(slice_vals)

            # Math: Long means Price > Anchor
            sqrt_anchor = math.sqrt(anchor)
            sqrt_price = math.sqrt(current_price)
            diff = sqrt_price - sqrt_anchor

            # Logic: We are adding to the Anchor's root
            math_op = 1

        # 2. CALCULATE DEGREES
        # 1.0 diff in Sqrt = 180 degrees
        degrees_rotation = diff * 180.0

        # 3. CALCULATE LEVELS
        # Note: If diff is negative (Price broke below anchor for Long, or
        # above anchor for Short), the math still holds but indicates
        # trend failure.

        # TARGET (Next 90 degrees)
        # We look for the next 0.5 increment
        turns = math.floor(diff / 0.5)
        next_step_factor = (turns + 1) * 0.5

        # Calculate Target Price
        # Long: (SqrtAnchor + Factor)^2
        # Short: (SqrtAnchor - Factor)^2
        val_next = sqrt_anchor + (math_op * next_step_factor)
        # Prevent math domain error (negative numbers) for shorts going to 0
        if val_next < 0: val_next = 0
        next_target = val_next ** 2

        # TRAILING STOP (Major 180 degrees)
        # We look for the completed 1.0 increment
        support_step_factor = math.floor(diff / 1.0) * 1.0
        val_support = sqrt_anchor + (math_op * support_step_factor)
        if val_support < 0: val_support = 0
        major_level = val_support ** 2

        # 4. APPEND
        self.AddColumn(anchor)
        self.AddColumn(degrees_rotation)
        self.AddColumn(next_target)
        self.AddColumn(major_level)

        return self.window

    ## Future indicator additions (No particular order)

    # Super Trend

    ## Volume-based

    # Chaikin Money Flow (CMF)
    # Accumulation/Distribution Line (A/D)
    # Money Flow Index (MFI)

    ## Volatility / Band-based

    # Keltner Channels
    # Donchian Channels

    ## Trend / Moving Average Variants

    ## Oscillators

    # CCI (Commodity Channel Index)
    # Ultimate Oscillator
    # Chaikin Oscillator

    ## Other

    # Pivot Points
    # Fibonacci Retracements / Extensions

    ##
    ## Candlestick patterns
    ##

    # Detect a Doji candlestick pattern
    # o=h=l=c Four Price Doji

    def Doji(self,OpenIDX=1,HighIDX=2,LowIDX=3,CloseIDX=4,threshold=0.1):
        if len(self.window)<1:
            self.AddColumn(None)    # body
            self.AddColumn(None)    # range
            self.AddColumn(None)    # ratio
            self.AddColumn(None)    # upper wick/shadow
            self.AddColumn(None)    # lowwer wick/shadow
            self.AddColumn(None)    # is doji (1=yes)
            return self.window

        last_row=self.LastRow()

        o=last_row[OpenIDX]
        h=last_row[HighIDX]
        l=last_row[LowIDX]
        c=last_row[CloseIDX]

        isDoji=0
        b=abs(o-c)                  # Body of candle
        r=h-l                       # Range of candle
        ratio=b/r if r!=0 else 0    # body to range ratio

        us=h-max(o,c)   # length of upper wick/shadow
        ls=max(o,c)-l   # length of lower wick/shadow

        self.AddColumn(b)
        self.AddColumn(r)
        self.AddColumn(ratio)
        self.AddColumn(us)
        self.AddColumn(ls)

        if ratio<=threshold:
            isDoji=1

        self.AddColumn(isDoji)

        return self.window

    # Tri-Star Doji (Three Dojis in a row)

    def TriStarDoji(self,OpenIDX=1,HighIDX=2,LowIDX=3,CloseIDX=4,threshold1=0.1,threshold2=0.1,threshold3=0.1):
        # If not enough candles, fill with None
        if len(self.window) < 3:
            self.AddColumn(None)    # doji 1
            self.AddColumn(None)    # doji 2
            self.AddColumn(None)    # doji 3
            self.AddColumn(None)    # is tri-star doji (1=yes)
            return self.window

        # The current index of the list, each doji is 6 columns
        # Get the three dojis

        self.Doji(OpenIDX,HighIDX,LowIDX,CloseIDX,threshold1)
        self.Doji(OpenIDX,HighIDX,LowIDX,CloseIDX,threshold2)
        self.Doji(OpenIDX,HighIDX,LowIDX,CloseIDX,threshold3)

        lIDX=len(self.window[-1])-1

        if len(self.window[-3])-12<=0:
            self.AddColumn(None)    # is tri-star doji (1=yes)
            return self.window

        # Get last 3 rows
        row1 = self.window[-1]
        row2 = self.window[-2]
        row3 = self.window[-3]

        doji1=row1[lIDX-12]     # Candle row 1
        doji2=row2[lIDX-6]      # Candle row 2
        doji3=row3[lIDX]        # Candle row 3

        # Tri-Star requires all 3 to be Doji
        isTriStar = 1 if (doji1==1 and doji2==1 and doji3==1) else 0

        # Add results to output
        self.AddColumn(isTriStar)

        return self.window

    # Hammer candlestick pattern

    def Hammer(self,OpenIDX=1,HighIDX=2,LowIDX=3,CloseIDX=4):
        if len(self.window)<1:
            self.AddColumn(None)    # is hammer (1=yes)
            return self.window

        last_row=self.LastRow()

        o=last_row[OpenIDX]
        h=last_row[HighIDX]
        l=last_row[LowIDX]
        c=last_row[CloseIDX]

        isHammer=0

        b=abs(o-c)                  # Body of candle

        us=h-max(o,c)   # length of upper wick/shadow
        ls=max(o,c)-l   # length of lower wick/shadow

        if b==0 or (ls>2*b and us>2*b): # spinning top
            isHammer=0
        if ls>2*b and us<b:
            isHammer=1

        self.AddColumn(isHammer)

        return self.window

    # Inverted Hammer candlestick pattern

    def InvertedHammer(self,OpenIDX=1,HighIDX=2,LowIDX=3,CloseIDX=4):
        if len(self.window)<1:
            self.AddColumn(None)    # is inverted hammer (1=yes)
            return self.window

        last_row=self.LastRow()

        o=last_row[OpenIDX]
        h=last_row[HighIDX]
        l=last_row[LowIDX]
        c=last_row[CloseIDX]

        isInvHammer=0

        b=abs(o-c)                  # Body of candle

        us=h-max(o,c)   # length of upper wick/shadow
        ls=max(o,c)-l   # length of lower wick/shadow

        if b==0 or (ls>2*b and us>2*b): # spinning top
            isInvHammer=0
        if us>2*b and ls<b:
            isInvHammer=1

        self.AddColumn(isInvHammer)

        return self.window

    # Spinning Top candlestick pattern

    def SpinningTop(self,OpenIDX=1,HighIDX=2,LowIDX=3,CloseIDX=4):
        if len(self.window)<1:
            self.AddColumn(None)    # is spinning top (1=yes)
            return self.window

        last_row=self.LastRow()

        o=last_row[OpenIDX]
        h=last_row[HighIDX]
        l=last_row[LowIDX]
        c=last_row[CloseIDX]

        isSpinTop=0

        b=abs(o-c)                  # Body of candle

        us=h-max(o,c)   # length of upper wick/shadow
        ls=max(o,c)-l   # length of lower wick/shadow

        if ls>2*b and us>2*b: # spinning top
            isSpinTop=1

        self.AddColumn(isSpinTop)

        return self.window

    # Hanging Man candlestick pattern

    def HangingMan(self,OpenIDX=1,HighIDX=2,LowIDX=3,CloseIDX=4):
        if len(self.window)<1:
            self.AddColumn(None)    # is hammer (1=yes)
            return self.window

        last_row=self.LastRow()

        o=last_row[OpenIDX]
        h=last_row[HighIDX]
        l=last_row[LowIDX]
        c=last_row[CloseIDX]

        isHang=0

        b=abs(o-c)                  # Body of candle

        us=h-max(o,c)   # length of upper wick/shadow
        ls=max(o,c)-l   # length of lower wick/shadow

        if ls>2*b and us<2*b:
            isHang=1

        self.AddColumn(isHang)

        return self.window

    # Shooting Star candlestick pattern

    def ShootingStar(self,OpenIDX=1,HighIDX=2,LowIDX=3,CloseIDX=4):
        if len(self.window)<1:
            self.AddColumn(None)    # is hammer (1=yes)
            return self.window

        last_row=self.LastRow()

        o=last_row[OpenIDX]
        h=last_row[HighIDX]
        l=last_row[LowIDX]
        c=last_row[CloseIDX]

        isShootStar=0

        b=abs(o-c)                  # Body of candle

        us=h-max(o,c)   # length of upper wick/shadow
        ls=max(o,c)-l   # length of lower wick/shadow

        if ls<2*b and us>2*b: # spinning top
            isShootStar=1

        self.AddColumn(isShootStar)

        return self.window

    # Detect a Bullish Marubozu candlestick pattern

    def BullishMarubozu(self,OpenIDX=1,HighIDX=2,LowIDX=3,CloseIDX=4,threshold=0.1):
        if len(self.window)<1:
            self.AddColumn(None)
            return self.window

        last_row=self.LastRow()

        o=last_row[OpenIDX]
        h=last_row[HighIDX]
        l=last_row[LowIDX]
        c=last_row[CloseIDX]

        isBM=0
        b=c-o

        us=h-c
        ls=o-l

        if b>0 and us<threshold*b and ls<threshold*b:
            isBM=1

        self.AddColumn(isBM)

        return self.window

    # Detect a Bearish Marubozu candlestick pattern

    def BearishMarubozu(self,OpenIDX=1,HighIDX=2,LowIDX=3,CloseIDX=4,threshold=0.1):
        if len(self.window)<1:
            self.AddColumn(None)
            return self.window

        last_row=self.LastRow()

        o=last_row[OpenIDX]
        h=last_row[HighIDX]
        l=last_row[LowIDX]
        c=last_row[CloseIDX]

        isBM=0
        b=c-o

        us=h-o
        ls=c-l

        if b<0 and us<threshold*abs(b) and ls<threshold*abs(b):
            isBM=1

        self.AddColumn(isBM)

        return self.window

    # Highwave candlestick pattern

    def HighWave(self,OpenIDX=1,HighIDX=2,LowIDX=3,CloseIDX=4,threshold=2):
        if len(self.window)<1:
            self.AddColumn(None)    # is hammer (1=yes)
            return self.window

        last_row=self.LastRow()

        o=last_row[OpenIDX]
        h=last_row[HighIDX]
        l=last_row[LowIDX]
        c=last_row[CloseIDX]

        isHW=0

        b=abs(o-c)                  # Body of candle

        us=h-max(o,c)   # length of upper wick/shadow
        ls=max(o,c)-l   # length of lower wick/shadow

        if ls>threshold*b and us>threshold*b: # spinning top
            isHW=1

        self.AddColumn(isHW)

        return self.window

    # Bullish Belt Hold

    def BullishBeltHold(self,OpenIDX=1,HighIDX=2,LowIDX=3,CloseIDX=4,threshold=0.1):
        if len(self.window)<1:
            self.AddColumn(None)    # is hammer (1=yes)
            return self.window

        last_row=self.LastRow()

        o=last_row[OpenIDX]
        h=last_row[HighIDX]
        l=last_row[LowIDX]
        c=last_row[CloseIDX]

        isBeltHold=0

        b=c-o

        if b>0:
            us=h-c
            ls=o-l

            if ls<=(threshold*b) and b>0 and c>o:
                isBeltHold=1

        self.AddColumn(isBeltHold)

        return self.window

    # Bearish Belt Hold

    def BearishBeltHold(self,OpenIDX=1,HighIDX=2,LowIDX=3,CloseIDX=4,threshold=0.1):
        if len(self.window)<1:
            self.AddColumn(None)    # is hammer (1=yes)
            return self.window

        last_row=self.LastRow()

        o=last_row[OpenIDX]
        h=last_row[HighIDX]
        l=last_row[LowIDX]
        c=last_row[CloseIDX]

        isBeltHold=0

        b=o-c

        if b>0:
            us=h-o
            ls=c-l

            if us<=(threshold*b) and b>0 and o>c:
                isBeltHold=1

        self.AddColumn(isBeltHold)

        return self.window

    # Bullish Engulfing candlestick pattern

    def BullishEngulfing(self, OpenIDX=1, HighIDX=2, LowIDX=3, CloseIDX=4):
        if len(self.window) < 2 or self.window[-2][0] is None:
            self.AddColumn(None)    # is bullish engulfing (1=yes)
            return self.window

        prev_row = self.GetRow(-2)
        last_row = self.LastRow()

        o1 = prev_row[OpenIDX]
        h1 = prev_row[HighIDX]
        l1 = prev_row[LowIDX]
        c1 = prev_row[CloseIDX]

        o2 = last_row[OpenIDX]
        h2 = last_row[HighIDX]
        l2 = last_row[LowIDX]
        c2 = last_row[CloseIDX]

        isBullEngulf = 0

        # First candle bearish
        if c1 < o1:
            # Second candle bullish
            if c2 > o2:
                # Engulfing condition
                if o2 <= c1 and c2 >= o1:
                    isBullEngulf = 1

        self.AddColumn(isBullEngulf)
        return self.window

    # Bearish Engulfing candlestick pattern

    def BearishEngulfing(self, OpenIDX=1, HighIDX=2, LowIDX=3, CloseIDX=4):
        if len(self.window) < 2 or self.window[-2][0] is None:
            self.AddColumn(None)    # is bearish engulfing (1=yes)
            return self.window

        prev_row = self.GetRow(-2)
        last_row = self.LastRow()

        o1 = prev_row[OpenIDX]
        h1 = prev_row[HighIDX]
        l1 = prev_row[LowIDX]
        c1 = prev_row[CloseIDX]

        o2 = last_row[OpenIDX]
        h2 = last_row[HighIDX]
        l2 = last_row[LowIDX]
        c2 = last_row[CloseIDX]

        isBearEngulf = 0

        # First candle bullish
        if c1 > o1:
            # Second candle bearish
            if c2 < o2:
                # Engulfing condition
                if o2 >= c1 and c2 <= o1:
                    isBearEngulf = 1

        self.AddColumn(isBearEngulf)
        return self.window

    # Tweezer Tops candlestick pattern

    def TweezerTops(self, OpenIDX=1, HighIDX=2, LowIDX=3, CloseIDX=4, tol=0.001):
        if len(self.window) < 2 or self.window[-2][0] is None:
            self.AddColumn(None)    # is tweezer tops (1=yes)
            return self.window

        prev_row = self.GetRow(-2)
        last_row = self.LastRow()

        o1 = prev_row[OpenIDX]
        h1 = prev_row[HighIDX]
        l1 = prev_row[LowIDX]
        c1 = prev_row[CloseIDX]

        o2 = last_row[OpenIDX]
        h2 = last_row[HighIDX]
        l2 = last_row[LowIDX]
        c2 = last_row[CloseIDX]

        isTweezerTop = 0

        # First candle bullish, second bearish
        if c1 > o1 and c2 < o2:
            # Highs nearly equal (within tolerance)
            # tol = tolerance factor (e.g., 0.001 = 0.1%), allows small differences
            if abs(h1 - h2) <= tol * max(h1, h2):
                isTweezerTop = 1

        self.AddColumn(isTweezerTop)
        return self.window

    # Tweezer Bottoms candlestick pattern

    def TweezerBottoms(self, OpenIDX=1, HighIDX=2, LowIDX=3, CloseIDX=4, tol=0.001):
        if len(self.window) < 2 or self.window[-2][0] is None:
            self.AddColumn(None)    # is tweezer bottoms (1=yes)
            return self.window

        prev_row = self.GetRow(-2)
        last_row = self.LastRow()

        o1 = prev_row[OpenIDX]
        h1 = prev_row[HighIDX]
        l1 = prev_row[LowIDX]
        c1 = prev_row[CloseIDX]

        o2 = last_row[OpenIDX]
        h2 = last_row[HighIDX]
        l2 = last_row[LowIDX]
        c2 = last_row[CloseIDX]

        isTweezerBottom = 0

        # First candle bearish, second bullish
        if c1 < o1 and c2 > o2:
            # Lows nearly equal (within tolerance)
            # tol = tolerance factor (e.g., 0.001 = 0.1%), allows small differences
            if abs(l1 - l2) <= tol * min(l1, l2):
                isTweezerBottom = 1

        self.AddColumn(isTweezerBottom)
        return self.window

    # Piercing Line candlestick pattern

    def PiercingLine(self, OpenIDX=1, HighIDX=2, LowIDX=3, CloseIDX=4):
        if len(self.window) < 2 or self.window[-2][0] is None:
            self.AddColumn(None)    # is piercing line (1=yes)
            return self.window

        prev_row = self.GetRow(-2)
        last_row = self.LastRow()

        o1 = prev_row[OpenIDX]
        h1 = prev_row[HighIDX]
        l1 = prev_row[LowIDX]
        c1 = prev_row[CloseIDX]

        o2 = last_row[OpenIDX]
        h2 = last_row[HighIDX]
        l2 = last_row[LowIDX]
        c2 = last_row[CloseIDX]

        isPiercing = 0

        # First candle bearish, second bullish
        if c1 < o1 and c2 > o2:
            # Second opens below first close and closes above midpoint of first body
            if o2 < c1 and c2 > (o1 + c1) / 2:
                isPiercing = 1

        self.AddColumn(isPiercing)
        return self.window

    # Dark Cloud Cover candlestick pattern

    def DarkCloudCover(self, OpenIDX=1, HighIDX=2, LowIDX=3, CloseIDX=4):
        if len(self.window) < 2 or self.window[-2][0] is None:
            self.AddColumn(None)    # is dark cloud cover (1=yes)
            return self.window

        prev_row = self.GetRow(-2)
        last_row = self.LastRow()

        o1 = prev_row[OpenIDX]
        h1 = prev_row[HighIDX]
        l1 = prev_row[LowIDX]
        c1 = prev_row[CloseIDX]

        o2 = last_row[OpenIDX]
        h2 = last_row[HighIDX]
        l2 = last_row[LowIDX]
        c2 = last_row[CloseIDX]

        isDarkCloud = 0

        # First candle bullish, second bearish
        if c1 > o1 and c2 < o2:
            # Second opens above first close and closes below midpoint of first body
            if o2 > c1 and c2 < (o1 + c1) / 2:
                isDarkCloud = 1

        self.AddColumn(isDarkCloud)
        return self.window

    # Bullish Harami candlestick pattern

    def BullishHarami(self, OpenIDX=1, HighIDX=2, LowIDX=3, CloseIDX=4):
        if len(self.window) < 2 or self.window[-2][0] is None:
            self.AddColumn(None)    # is bullish harami (1=yes)
            return self.window

        prev_row = self.GetRow(-2)
        last_row = self.LastRow()

        o1 = prev_row[OpenIDX]
        h1 = prev_row[HighIDX]
        l1 = prev_row[LowIDX]
        c1 = prev_row[CloseIDX]

        o2 = last_row[OpenIDX]
        h2 = last_row[HighIDX]
        l2 = last_row[LowIDX]
        c2 = last_row[CloseIDX]

        isBullHarami = 0

        # First candle bearish, second bullish
        if c1 < o1 and c2 > o2:
            # Second body completely inside first body
            if o2 > c1 and c2 < o1:
                isBullHarami = 1

        self.AddColumn(isBullHarami)
        return self.window

    # Bearish Harami candlestick pattern

    def BearishHarami(self, OpenIDX=1, HighIDX=2, LowIDX=3, CloseIDX=4):
        if len(self.window) < 2 or self.window[-2][0] is None:
            self.AddColumn(None)    # is bearish harami (1=yes)
            return self.window

        prev_row = self.GetRow(-2)
        last_row = self.LastRow()

        o1 = prev_row[OpenIDX]
        h1 = prev_row[HighIDX]
        l1 = prev_row[LowIDX]
        c1 = prev_row[CloseIDX]

        o2 = last_row[OpenIDX]
        h2 = last_row[HighIDX]
        l2 = last_row[LowIDX]
        c2 = last_row[CloseIDX]

        isBearHarami = 0

        # First candle bullish, second bearish
        if c1 > o1 and c2 < o2:
            # Second body completely inside first body
            if o2 < c1 and c2 > o1:
                isBearHarami = 1

        self.AddColumn(isBearHarami)
        return self.window

    # Bullish Harami Cross candlestick pattern

    def BullishHaramiCross(self, OpenIDX=1, HighIDX=2, LowIDX=3, CloseIDX=4, tol=0.001):
        if len(self.window) < 2 or self.window[-2][0] is None:
            self.AddColumn(None)    # is bullish harami cross (1=yes)
            return self.window

        prev_row = self.GetRow(-2)
        last_row = self.LastRow()

        o1 = prev_row[OpenIDX]
        h1 = prev_row[HighIDX]
        l1 = prev_row[LowIDX]
        c1 = prev_row[CloseIDX]

        o2 = last_row[OpenIDX]
        h2 = last_row[HighIDX]
        l2 = last_row[LowIDX]
        c2 = last_row[CloseIDX]

        isBullHaramiCross = 0

        # First candle bearish, second is Doji
        if c1 < o1 and abs(c2 - o2) <= tol:
            # Second candle inside first candle's body
            if o2 > c1 and c2 < o1:
                isBullHaramiCross = 1

        self.AddColumn(isBullHaramiCross)
        return self.window

    # Bearish Harami Cross candlestick pattern

    def BearishHaramiCross(self, OpenIDX=1, HighIDX=2, LowIDX=3, CloseIDX=4, tol=0.001):
        if len(self.window) < 2 or self.window[-2][0] is None:
            self.AddColumn(None)    # is bearish harami cross (1=yes)
            return self.window

        prev_row = self.GetRow(-2)
        last_row = self.LastRow()

        o1 = prev_row[OpenIDX]
        h1 = prev_row[HighIDX]
        l1 = prev_row[LowIDX]
        c1 = prev_row[CloseIDX]

        o2 = last_row[OpenIDX]
        h2 = last_row[HighIDX]
        l2 = last_row[LowIDX]
        c2 = last_row[CloseIDX]

        isBearHaramiCross = 0

        # First candle bullish, second is Doji
        if c1 > o1 and abs(c2 - o2) <= tol:
            # Second candle inside first candle's body
            if o2 < c1 and c2 > o1:
                isBearHaramiCross = 1

        self.AddColumn(isBearHaramiCross)
        return self.window

    # Matching Low candlestick pattern

    def MatchingLow(self, OpenIDX=1, HighIDX=2, LowIDX=3, CloseIDX=4, tol=0.001):
        if len(self.window) < 2 or self.window[-2][0] is None:
            self.AddColumn(None)    # is matching low (1=yes)
            return self.window

        prev_row = self.GetRow(-2)
        last_row = self.LastRow()

        o1 = prev_row[OpenIDX]
        h1 = prev_row[HighIDX]
        l1 = prev_row[LowIDX]
        c1 = prev_row[CloseIDX]

        o2 = last_row[OpenIDX]
        h2 = last_row[HighIDX]
        l2 = last_row[LowIDX]
        c2 = last_row[CloseIDX]

        isMatchingLow = 0

        # Both candles bearish
        if c1 < o1 and c2 < o2:
            # Lows nearly equal (within tolerance)
            if abs(l1 - l2) <= tol * min(l1, l2):
                isMatchingLow = 1

        self.AddColumn(isMatchingLow)
        return self.window

    # Bullish Mat Hold (3) candlestick pattern (simplified, bullish)

    def BullishMatHold3(self, OpenIDX=1, HighIDX=2, LowIDX=3, CloseIDX=4, tol=0.001):
        if len(self.window) < 3 or self.window[-2][0] is None or self.window[-3][0] is None:
            self.AddColumn(None)    # is Mat Hold (1=yes)
            return self.window

        first = self.GetRow(-3)
        middle = self.GetRow(-2)
        last = self.LastRow()

        o1, h1, l1, c1 = first[OpenIDX], first[HighIDX], first[LowIDX], first[CloseIDX]
        o2, h2, l2, c2 = middle[OpenIDX], middle[HighIDX], middle[LowIDX], middle[CloseIDX]
        o3, h3, l3, c3 = last[OpenIDX], last[HighIDX], last[LowIDX], last[CloseIDX]

        isMatHold = 0

        # First candle bullish
        if c1 > o1:
            # Middle candle body contained within first candle
            if o2 >= o1 and c2 <= c1:
                # Last candle bullish and closes above first candle
                if c3 > o3 and c3 > c1:
                    isMatHold = 1

        self.AddColumn(isMatHold)
        return self.window

    # Bearish Mat Hold candlestick pattern (simplified)

    def BearishMatHold(self, OpenIDX=1, HighIDX=2, LowIDX=3, CloseIDX=4, tol=0.001):
        if len(self.window) < 3 or self.window[-2][0] is None or self.window[-3][0] is None:
            self.AddColumn(None)    # is bearish Mat Hold (1=yes)
            return self.window

        first = self.GetRow(-3)
        middle = self.GetRow(-2)
        last = self.LastRow()

        o1, h1, l1, c1 = first[OpenIDX], first[HighIDX], first[LowIDX], first[CloseIDX]
        o2, h2, l2, c2 = middle[OpenIDX], middle[HighIDX], middle[LowIDX], middle[CloseIDX]
        o3, h3, l3, c3 = last[OpenIDX], last[HighIDX], last[LowIDX], last[CloseIDX]

        isBearMatHold = 0

        # First candle bearish
        if c1 < o1:
            # Middle candle body contained within first candle
            if o2 <= o1 and c2 >= c1:
                # Last candle bearish and closes below first candle
                if c3 < o3 and c3 < c1:
                    isBearMatHold = 1

        self.AddColumn(isBearMatHold)
        return self.window

    # 5-candle Bullish Mat Hold candlestick pattern

    def BullishMatHold5(self, OpenIDX=1, HighIDX=2, LowIDX=3, CloseIDX=4, tol=0.001):
        if len(self.window) < 5 \
        or self.window[-2][0] is None or self.window[-3][0] is None \
        or self.window[-4][0] is None or self.window[-5][0] is None:
            self.AddColumn(None)    # is Mat Hold 5-candle (1=yes)
            return self.window

        # Extract the 5 candles
        first   = self.GetRow(-5)
        second  = self.GetRow(-4)
        third   = self.GetRow(-3)
        fourth  = self.GetRow(-2)
        fifth   = self.LastRow()

        candles = [first, second, third, fourth, fifth]

        o1, h1, l1, c1 = first[OpenIDX], first[HighIDX], first[LowIDX], first[CloseIDX]
        o5, h5, l5, c5 = fifth[OpenIDX], fifth[HighIDX], fifth[LowIDX], fifth[CloseIDX]

        isMatHold = 0

        # First candle bullish
        if c1 > o1:
            # Middle three candles body contained within first candle's body
            contained = True
            for mid in candles[1:4]:
                o, c = mid[OpenIDX], mid[CloseIDX]
                if o < o1 - tol * o1 or c > c1 + tol * c1:
                    contained = False
                    break

            # Fifth candle bullish and closes above first candle's close
            if contained and c5 > o5 and c5 > c1:
                isMatHold = 1

        self.AddColumn(isMatHold)
        return self.window

    # 5-candle Bearish Mat Hold candlestick pattern

    def BearishMatHold5(self, OpenIDX=1, HighIDX=2, LowIDX=3, CloseIDX=4, tol=0.001):
        if len(self.window) < 5 \
        or self.window[-2][0] is None or self.window[-3][0] is None \
        or self.window[-4][0] is None or self.window[-5][0] is None:
            self.AddColumn(None)    # is Bearish Mat Hold 5-candle (1=yes)
            return self.window

        # Extract the 5 candles
        first   = self.GetRow(-5)
        second  = self.GetRow(-4)
        third   = self.GetRow(-3)
        fourth  = self.GetRow(-2)
        fifth   = self.LastRow()

        candles = [first, second, third, fourth, fifth]

        o1, h1, l1, c1 = first[OpenIDX], first[HighIDX], first[LowIDX], first[CloseIDX]
        o5, h5, l5, c5 = fifth[OpenIDX], fifth[HighIDX], fifth[LowIDX], fifth[CloseIDX]

        isMatHoldBearish = 0

        # First candle bearish
        if c1 < o1:
            # Middle three candles body contained within first candle's body
            contained = True
            for mid in candles[1:4]:
                o, c = mid[OpenIDX], mid[CloseIDX]
                if o > o1 + tol * o1 or c < c1 - tol * c1:
                    contained = False
                    break

            # Fifth candle bearish and closes below first candle's close
            if contained and c5 < o5 and c5 < c1:
                isMatHoldBearish = 1

        self.AddColumn(isMatHoldBearish)
        return self.window

    # Bullish Kicking by Length candlestick pattern

    def BullishKickingByLength(self, OpenIDX=1, HighIDX=2, LowIDX=3, CloseIDX=4, tol=0.001):
        if len(self.window) < 2 or self.window[-2][0] is None:
            self.AddColumn(None)    # is Kicking by Length (1=yes)
            return self.window

        first = self.GetRow(-2)
        second = self.LastRow()

        o1, h1, l1, c1 = first[OpenIDX], first[HighIDX], first[LowIDX], first[CloseIDX]
        o2, h2, l2, c2 = second[OpenIDX], second[HighIDX], second[LowIDX], second[CloseIDX]

        isKicking = 0

        # Bullish Kicking: first bearish Marubozu, second bullish Marubozu with gap up
        if abs(c1 - o1) > tol * o1 and abs(c2 - o2) > tol * o2:
            if c1 < o1 and c2 > o2 and o2 > c1:
                isKicking = 1

        self.AddColumn(isKicking)
        return self.window

    # Bearish Kicking by Length candlestick pattern

    def BearishKickingByLength(self, OpenIDX=1, HighIDX=2, LowIDX=3, CloseIDX=4, tol=0.001):
        if len(self.window) < 2 or self.window[-2][0] is None:
            self.AddColumn(None)    # is Kicking by Length (1=yes)
            return self.window

        first = self.GetRow(-2)
        second = self.LastRow()

        o1, h1, l1, c1 = first[OpenIDX], first[HighIDX], first[LowIDX], first[CloseIDX]
        o2, h2, l2, c2 = second[OpenIDX], second[HighIDX], second[LowIDX], second[CloseIDX]

        isKicking = 0

        # Bearish Kicking: first bullish Marubozu, second bearish Marubozu with gap down
        if abs(c1 - o1) > tol * o1 and abs(c2 - o2) > tol * o2:
            if c1 > o1 and c2 < o2 and o2 < c1:
                isKicking = 1

        self.AddColumn(isKicking)
        return self.window

    # Bullish Separating Lines candlestick pattern

    def BullishSeparatingLines(self, OpenIDX=1, HighIDX=2, LowIDX=3, CloseIDX=4, tol=0.001):
        if len(self.window) < 2 or self.window[-2][0] is None:
            self.AddColumn(None)    # is bullish separating lines (1=yes)
            return self.window

        prev_row = self.GetRow(-2)
        last_row = self.LastRow()

        o1, h1, l1, c1 = prev_row[OpenIDX], prev_row[HighIDX], prev_row[LowIDX], prev_row[CloseIDX]
        o2, h2, l2, c2 = last_row[OpenIDX], last_row[HighIDX], last_row[LowIDX], last_row[CloseIDX]

        isBullSep = 0

        # First candle bearish
        if c1 < o1:
            # Second candle bullish
            if c2 > o2:
                # Opens at (or very near) same level as first candle's open
                if abs(o2 - o1) <= tol:
                    isBullSep = 1

        self.AddColumn(isBullSep)
        return self.window

    # Bearish Separating Lines candlestick pattern

    def BearishSeparatingLines(self, OpenIDX=1, HighIDX=2, LowIDX=3, CloseIDX=4, tol=0.001):
        if len(self.window) < 2 or self.window[-2][0] is None:
            self.AddColumn(None)    # is bearish separating lines (1=yes)
            return self.window

        prev_row = self.GetRow(-2)
        last_row = self.LastRow()

        o1, h1, l1, c1 = prev_row[OpenIDX], prev_row[HighIDX], prev_row[LowIDX], prev_row[CloseIDX]
        o2, h2, l2, c2 = last_row[OpenIDX], last_row[HighIDX], last_row[LowIDX], last_row[CloseIDX]

        isBearSep = 0

        # First candle bullish
        if c1 > o1:
            # Second candle bearish
            if c2 < o2:
                # Opens at (or very near) same level as first candle's open
                if abs(o2 - o1) <= tol:
                    isBearSep = 1

        self.AddColumn(isBearSep)
        return self.window

    # Bullish Kicker candlestick pattern

    def BullishKicker(self, OpenIDX=1, HighIDX=2, LowIDX=3, CloseIDX=4):
        if len(self.window) < 2 or self.window[-2][0] is None:
            self.AddColumn(None)    # is bullish kicker (1=yes)
            return self.window

        prev_row = self.GetRow(-2)
        last_row = self.LastRow()

        o1, h1, l1, c1 = prev_row[OpenIDX], prev_row[HighIDX], prev_row[LowIDX], prev_row[CloseIDX]
        o2, h2, l2, c2 = last_row[OpenIDX], last_row[HighIDX], last_row[LowIDX], last_row[CloseIDX]

        isBullKicker = 0

        # First candle bearish
        if c1 < o1:
            # Second candle bullish
            if c2 > o2:
                # Open of second candle gaps above high of first candle
                if o2 > h1:
                    isBullKicker = 1

        self.AddColumn(isBullKicker)
        return self.window

    # Bearish Kicker candlestick pattern

    def BearishKicker(self, OpenIDX=1, HighIDX=2, LowIDX=3, CloseIDX=4):
        if len(self.window) < 2 or self.window[-2][0] is None:
            self.AddColumn(None)    # is bearish kicker (1=yes)
            return self.window

        prev_row = self.GetRow(-2)
        last_row = self.LastRow()

        o1, h1, l1, c1 = prev_row[OpenIDX], prev_row[HighIDX], prev_row[LowIDX], prev_row[CloseIDX]
        o2, h2, l2, c2 = last_row[OpenIDX], last_row[HighIDX], last_row[LowIDX], last_row[CloseIDX]

        isBearKicker = 0

        # First candle bullish
        if c1 > o1:
            # Second candle bearish
            if c2 < o2:
                # Open of second candle gaps below low of first candle
                if o2 < l1:
                    isBearKicker = 1

        self.AddColumn(isBearKicker)
        return self.window

    ## Triple Candlestick Patterns

    # Morning Star
    # Evening Star
    # Morning Doji Star
    # Evening Doji Star
    # Three White Soldiers
    # Three Black Crows
    # Three Inside Up
    # Three Inside Down
    # Three Outside Up
    # Three Outside Down
    # Three Line Strike (Bullish, Bearish)
    # Three Stars in the South
    # Three Advancing White Soldiers (variation of White Soldiers)

    ## Extended / Rare Multi-Candle Patterns

    # Abandoned Baby (Bullish & Bearish)
    # Rising Three Methods
    # Falling Three Methods
    # Upside Gap Two Crows
    # Downside Gap Two Rabbits (variation name)
    # Two Crows
    # Concealing Baby Swallow
    # Deliberation Pattern (Stalled Pattern)
    # Advance Block
    # Ladder Bottom
    # Ladder Top
    # On Neck Pattern
    # In Neck Pattern
    # Thrusting Pattern
    # Counterattack Lines (Bullish Counterattack, Bearish Counterattack)
    # Meeting Lines
    # Homing Pigeon
    # Stick Sandwich
    # Side-by-Side White Lines
    # Unique Three River Bottom
    # Tower Top
    # Tower Bottom
    # Rickshaw Man (variation of Long-Legged Doji)
    # Tasuki Gap (Upward Tasuki Gap, Downward Tasuki Gap)
    # Side-by-Side Black Lines
    # Doji Star (Bullish & Bearish)
    # Long Line Candle (variation of Marubozu)
    # Advance Block Soldiers
    # Strong Line Patterns

###
### END of code
###

