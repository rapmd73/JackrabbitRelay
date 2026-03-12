# Section 1 - Non-Technical Description

This program reads a transaction history for a specific account and asset, calculates how the account's exposure in base and quote currencies and the overall exposure balance change over time, and then produces a time-series chart of those exposures as either an image or an HTML file.

# Section 2 - Technical Analysis

The script begins by importing modules and appending a specific directory to Python's module search path so it can import a local support module named JRRsupport. It defines filesystem paths for where charts and Mimic account data are stored, and creates a list of token symbols considered "stablecoin/US D"-like identifiers (StableCoinUSD).

The program expects three command-line arguments: an output type flag (first argument, either "I" or "H" case-insensitive), an account name (second argument), and an asset pair identifier (third argument). If fewer than three arguments are supplied or the first argument is not i/I or h/H, the script prints an error and exits.

It constructs the filename of the account history by joining the MimicData directory path with the account name plus ".history". If that file does not exist, the program prints a message and exits. It reads the entire file using JRRsupport.ReadFile(acn), strips whitespace, and splits by newline to get individual lines. It initializes lists for timestamps (xps), base exposures (bExposure), quote exposures (qExposure), and a running exposure measure (cnr). It also initializes two numeric accumulators: pnl and balance, both starting at 0.

The script iterates over each non-empty line of the account history. For each line it attempts to parse the line as JSON; if parsing fails the script prints the offending line and exits. For each parsed record it extracts the 'Asset' field as pair. It derives base and quote variables from the provided asset argument (sys.argv[3]). If the asset argument contains a colon, the right side of the colon is used as the quote; if that quote contains a hyphen, the portion before the hyphen is kept. If the record's pair does not exactly match the asset argument, that record is skipped.

For matching records it extracts:
- dt from data['DateTime'] (timestamp string),
- act as the first character (uppercased) of data['Action'],
- bw as the float value of data[base],
- qw as the float value of data[quote],
- a as float(data['Amount']),
- p as float(data['Price']),
- f as float(data['Fee']).

If balance is still zero (first processed matching record), it sets balance to qw + f + (abs(bw) * p), and sets pnl equal to that balance. For each record thereafter, it updates pnl depending on act: if act is 'B' (buy), it subtracts (abs(a) * p) + f from pnl; otherwise it adds (abs(a) * p) - f to pnl. After that update it appends dt to xps.

For the base exposure list, it appends bw * p unless the base symbol appears in StableCoinUSD, in which case it appends bw (no price conversion). For the quote exposure list, it appends qw * p unless the quote symbol appears in StableCoinUSD, in which case it appends qw. It appends the current pnl value to cnr.

After processing all records, the script builds an output filename. It removes any slash from the asset argument and then splits on ':' keeping the first portion as pair; it combines chartDir, a prefix "Exposure", the exchange name ("mimic"), the account name, and that pair to form either an .html or .png filename depending on the requested output type flag.

It creates a Plotly figure with a single subplot. It adds three traces as line charts sharing the same y-axis: the exposure curve (cnr) plotted in blue labeled "Exposure", the base exposure (bExposure) labeled "Base", and the quote exposure (qExposure) labeled "Quote". It sets the y-axis title to "Exposure Curve" and sets a centered title that includes the account and asset.

The script then overlays a semi-transparent logo image centered in the plot. If the requested output is HTML, the logo is referenced by a remote URL; for image output the logo is referenced by a local file URL. Finally, if HTML output was requested the figure is written to the HTML filename; otherwise the figure is written as an image (PNG) at 1920×1024 to the PNG filename.

Summary of runtime behavior:
- Loads an account history file containing JSON lines.
- Filters lines for the specified asset.
- Computes running exposure (pnl) from amounts, prices, and fees using a specific initialization and per-action update rule.
- Converts base and quote holdings into exposure values, applying price conversion except for tokens in StableCoinUSD.
- Produces a time-series plot of exposure, base, and quote, and saves it as either an HTML file or a PNG image with a background logo.
