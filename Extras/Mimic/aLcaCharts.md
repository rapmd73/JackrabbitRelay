Section 1 - Non-Technical Description

This program reads a named history file for a trading wallet, groups the recorded trades by asset, and for each asset produces a set of six charts (balances, transaction amounts, prices, fees, and action counts) saved as a PNG image file in a charts folder.

Section 2 - Technical Analysis

- Startup and configuration: the script adjusts the Python path to include /home/JackrabbitRelay2/Base/Library, imports standard modules (os, time, json), pandas, and matplotlib, and imports a custom module JRRsupport. It defines two directory path variables: chartDir for saved chart images and MimicData for locating account history files.

- Command-line argument handling: the script requires at least one command-line argument. If none is provided it prints "A Mimic account is required." and exits with status 1. The first argument is taken as account.

- History file lookup: it composes a filename acn by joining the MimicData directory with the account name and adding the ".history" extension. If that file path does not exist, the script prints "Please verify wallet name and case" and exits with status 1.

- Reading the history file: the script uses JRRsupport.ReadFile(acn) to read the entire file contents into TradeData. It strips leading/trailing whitespace and splits the contents into lines on newline characters.

- Parsing lines into JSON objects and grouping by asset: the script initializes an empty dictionary Wallet. It iterates over each non-empty line from the history file, attempts to parse the line as JSON using json.loads. If parsing fails it prints "Line damaged:", prints the offending line, and exits with status 1. For each successfully parsed JSON object (named data), it uses the value of data['Asset'] as a key in Wallet; if that key is not present, it creates an empty list. It then appends the parsed data dictionary to the list for that asset. After this loop, Wallet maps asset name strings (like "PEPE/USDT") to lists of data dictionaries read from the history file, preserving the order those lines appeared.

- Iterating assets and deriving base/quote: the script iterates the keys of Wallet in sorted order. For each asset string it normally splits the string on '/' into base and quote. It also contains extra parsing: if the asset contains a colon ':' it instead sets quote to the substring after the colon, and if that quote substring contains a hyphen '-' it further truncates quote at the hyphen's first occurrence. These parsed base and quote values are passed to the plotting routine.

- Plotting routine (plot_trading_data): this function receives trading_data (a list of dictionaries), account, base, and quot (quote). It treats trading_data as already parsed JSON and builds a pandas DataFrame from that list. It converts the DataFrame's 'DateTime' column to pandas datetime objects. It then creates a matplotlib figure and arranges six subplots in a 3x2 grid:
  1. Subplot (1): plots DateTime vs the column named by base (e.g., PEPE) with markers, titled "<base> Balance Over Time".
  2. Subplot (2): plots DateTime vs the column named by quote with orange markers, titled "<quote> Balance Over Time".
  3. Subplot (3): plots DateTime vs the 'Amount' column with green markers, titled "Transaction Amount Over Time".
  4. Subplot (4): plots DateTime vs the 'Price' column with red markers, titled "Transaction Price Over Time".
  5. Subplot (5): plots DateTime vs the 'Fee' column with purple markers, titled "Transaction Fee Over Time".
  6. Subplot (6): computes value counts for the 'Action' column and plots them as a bar chart with two colors (blue and red), titled "Action Distribution".

  After laying out the plots, it calls plt.tight_layout(), saves the figure to a PNG file named using the pattern aLcaChart.mimic.{account}.{base}{quote}.png inside chartDir, and then closes the figure. The function does not display the figure interactively.

- Overall behavior: for each asset present in the account history file the program produces one PNG file containing six subplots derived from the list of trade records for that asset. The PNG filenames include the account name and concatenation of base and quote symbols. If any line in the history file is not valid JSON, the program prints that line and exits; if the account file is missing it prints a message and exits; if no account argument is given it prints a message and exits.
