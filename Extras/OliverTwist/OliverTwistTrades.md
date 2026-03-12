# Section 1 - Non-Technical Description

This program reads a trading log and any currently open orders, then produces a visual chart of recent market price candles together with lines showing open orders and completed trade entries and exits; it saves that chart as either an image or an HTML file depending on the user's choice.

# Section 2 - Technical Analysis

- Startup and configuration:
  - The script imports modules and extends sys.path to include a specific library directory. It creates a logging object and a signal interceptor using objects from imported modules JRR and JRRsupport. It defines fixed directory paths for data, charts, and a subdirectory named OliverTwist where open-order storehouse files live. A Locker object named OliverTwistLock is created for synchronized access to that storehouse.

- ReadStorehouse(exchange, account, asset):
  - This function composes a file path for a Storehouse file using the provided exchange, account, and asset.
  - It acquires the OliverTwistLock (spinning with ElasticSleep(1) until the lock status equals 'locked').
  - If the Storehouse file exists, the file is read and split into lines. Each non-empty line is stripped and parsed from JSON into a Python object (it loops while the object is still a string doing json.loads until the entry is a parsed structure).
  - If the parsed object contains 'Order' or 'Detail' entries that are still strings, those strings are json.loads() parsed, then any 'Identity' fields are removed from those parsed sub-objects, and the cleaned sub-objects are reattached to the parent object.
  - Each resulting object is appended to a list OrphanList.
  - The lock is released and OrphanList is returned. This returns a list of open-order entries tracked in the storehouse file.

- FindStartDateTime(end_date_str, duration_str):
  - Parses an end-date string with the format '%Y-%m-%d %H:%M:%S.%f' into a datetime.
  - Parses a duration string that is expected to be like "X days, HH:MM:SS.sss" (splitting by ', '), extracts integer days and hours/minutes/seconds, builds a timedelta, subtracts it from the end date, formats the start datetime back to the same string format, and returns that formatted start date string.

- Command-line argument handling:
  - The program requires at least two command-line arguments. The first arg must indicate output type: 'i' (image) or 'h' (html). The second arg must be a grid-bot log filename (gblog). If these are not supplied, the script prints usage messages and exits.
  - The script copies the first arg lowercased into ih and validates it. The second arg is stored as gblog.
  - It then removes additional sys.argv elements in a loop so that sys.argv is shortened (the code removes elements starting at index 1 repeatedly).

- Parsing gblog and preparing pair/exchange/account:
  - The script prints a Phase 1 message, splits the gblog filename on '.' into data.
  - It sets exchange = data[1] and account = data[2].
  - It computes asset and pair depending on number of fields: if len(data) == 5 it uses data[3] as asset; otherwise it uses data[4] as asset. pair is constructed by taking the asset string and inserting '/' before the last three characters (asset[:-3] + '/' + asset[-3:]).

- Reading open orders and determining time bounds:
  - The script calls ReadStorehouse(exchange, account, asset) to get OpenOrders.
  - If OpenOrders is non-empty:
    - Parses the 'DateTime' of the first open order into OpenOrderDT and its epoch OpenEpoch.
    - Overrides pair with OpenOrders[0]['Order']['Asset'].
    - Sets EndOrderDate to the current datetime string, and EndOrderDT to that parsed datetime.
  - If OpenOrders is empty:
    - Sets OpenOrderDT to now and OpenEpoch to now's epoch. (This ensures a bound for further comparisons.)

- Reading the log file:
  - The entire log file named by gblog is read and split into lines; lines are stored in variable lines.
  - The script determines StartDate from the first token of the first line (splitting on space) and converts it to StartDT and StartEpoch.
  - OldestEpoch is set to the minimum of OpenEpoch and StartEpoch.

- Obtaining OHLCV candle data:
  - A JackrabbitRelay object is instantiated as relay with framework='oanda', plus the exchange, account, and asset pair.
  - For each timeframe in relay.Timeframes, it calls relay.GetOHLCV(symbol=pair, timeframe=tf, limit=5000), takes the timestamp of the first returned candle (firstCandle = ohlcv[0][0]/1000) and checks whether that timestamp is older (less) than OldestEpoch. It breaks out of the timeframe loop when it finds a timeframe whose first candle is earlier than the oldest epoch. The corresponding timeframe is stored in ChartTF. The last ohlcv dataset assigned before the break is used.

- Preparing output filename and chart title:
  - Based on ih the output filename fn is set to either a .html or .png file located under chartDir with naming Trades.{exchange}.{account}.{asset}.(html|png).
  - A title string ts is constructed that includes account, pair, and ChartTF.

- Creating the Plotly figure:
  - A subplot figure fig1 is created with a single subplot (secondary_y False).
  - Phase 2 message is printed.

- Determining the first candle to display:
  - The first non-empty token on the first log line is parsed to get a field fid. The code attempts to get order details via relay.GetOrderDetails(OrderID=fid)[0], parse its 'time' field splitting at 'T' and take the date part to compute sdt = timestamp of that date. If this lookup fails, sdt defaults to StartEpoch.

- Plotting candles:
  - Iterates through the previously obtained ohlcv list. For each candle slice, computes candle time cdt = slice[0]/1000. Candles with cdt < sdt are skipped. For remaining candles, it appends datetime.fromtimestamp(slice[0]/1000) to dt and the open/high/low/close values to do, dh, dl, dc lists respectively.
  - Adds a Candlestick trace to fig1 using those collected lists. The increasing and decreasing candle line colors are set to specific hex colors.

- Plotting open orders as horizontal lines:
  - Iterates through OpenOrders and for each:
    - If exchange is 'oanda', it tries to fetch the latest order details via relay.GetOrderDetails(OrderID=order['ID'])[-1] and extract price and units; on exception it prints an error and continues to the next open order.
    - If exchange is 'mimic', it reads amount and price from order['Response']['Details'] fields named 'Amount' and 'Price'.
    - Otherwise (fall-through, e.g., CCXT), it reads amount and price from 'amount' and 'price' keys in order['Response']['Details'].
    - It constructs a hover text showing ID, amount, and price and plots a Scatter trace containing a horizontal line from the order DateTime to EndOrderDate at the order price, colored with a fixed RGBA color. The plotted mode is 'lines'.

- Parsing trade lines and plotting trade entry/exit segments:
  - Iterates over each line from the log (lines). For each line:
    - Lowercases the line and skips empty lines or lines that do not contain any of the substrings 'prft', 'loss', or 'rduc'. Lines containing 'broke' are skipped.
    - Splits the line on spaces, removes empty tokens, and extracts date/time and duration. If the line contains 'days,' or 'day,' it builds a duration string from tokens at positions 12-14; otherwise it builds a duration string of '0 days, <token 12>'.
    - Calls FindStartDateTime with the full date/time string and the constructed duration to compute bTime (the calculated start time string).
    - Extracts action (token 6), direction (token 7 before a comma), amount as the absolute value of token 8 up to a colon, bPrice as token 9, sPrice as the numeric part of token 11 before a '/' and sTime as dt (the exit datetime).
    - Computes rpl (realized profit/loss) as (sPrice - bPrice) * amount for 'long' or the reverse for non-long.
    - Chooses a color based on action and rpl:
      - action == 'prft' and rpl>0 => green
      - action == 'prft' and rpl==0 => yellow-ish
      - action == 'prft' and rpl<0 => orange with 0.5 alpha
      - action == 'rduc' => almost transparent cyan
      - action == 'loss' => dark red with 0.5 alpha
      - Otherwise prints the line and continues to next line.
    - Adds a Scatter trace to fig1 drawing a line from the computed bTime to sTime with y values bPrice to sPrice, using the selected color.

- Adding an optional background logo:
  - If a logo file exists at /home/JackrabbitRelay2/Data/logo.png, it adds a layout image to the figure. If output is HTML, it sets the image source to '/logo.png'; if image output, it uses the file:/// path to the logo file. The image is centered and semi-transparent (opacity 0.1).

- Final layout updates and writing the output:
  - The Y-axis is labeled 'Price', the title and layout template are set (Plotly white template), legend is turned off, and the range slider is disabled.
  - If ih == 'h', fig1.write_html(fn) is called to write a standalone HTML file containing the chart.
  - Otherwise fig1.write_image(fn, width=1920, height=1024) writes a PNG image at 1920x1024 pixels.

Observed behavior summary:
- The program reads a grid-bot log filename and an output type argument, reads open orders from a storehouse file, reads historical candle data from a relay object, builds a candlestick chart covering from the first relevant candle through recent time, overlays horizontal lines for currently open orders, overlays line segments for trades marked as profit/loss/reduce in the log with color-coding by outcome, optionally adds a semi-transparent logo, and saves the result as either an HTML file or a PNG image in the Charts directory.
