## Section 1 - Non-Technical Description

This program reads a specific log file, extracts profit and loss events with timestamps, accumulates those amounts over time to form an equity value, and then creates a time-series chart of that equity curve saved either as an image or as an HTML file in a charts directory.

## Section 2 - Technical Analysis

The script expects at least two command-line arguments: an output type indicator and a path/filename for an "Oliver Twist" log file. The first argument is treated case-insensitively and must be either "I" (image) or "H" (HTML). If the first argument is invalid or missing, the program prints an error and exits. The second argument is parsed by splitting on periods to extract tokens that the program uses as identifiers: exchange (token index 1), account (token index 2), and pair (token index 3). Those tokens are used to construct the output filename.

The script adds a hardcoded library path to sys.path and imports a helper module named JRRsupport. It reads the entire contents of the specified log file using JRRsupport.ReadFile, strips surrounding whitespace, and splits into lines. It initializes an empty list of timestamps (xps), an empty list for equity values (equity), and a running P&L accumulator (pnl) starting at 0.

For each line in the file (converted to lowercase), the program skips blank lines and any line that does not contain the substrings "prft", "loss", or "rduc". It also skips any line containing the substring "broke". For remaining lines it splits the line on spaces and takes the first two tokens to form a datetime string (dt = first token + ' ' + second token). It also extracts a numeric piece by splitting the original line on '/' and taking the part after the first '/', then trimming and splitting that on ',' and using the first element; this extracted string (pdata) is converted to a float.

If the line contains "prft" (case-insensitive), the program increases the running pnl by the absolute value of that float. If the line contains "loss" or "rduc", it decreases the running pnl by the absolute value of that float. After updating pnl, the program appends the datetime string to xps and the current pnl to equity. This results in two parallel lists: timestamps and the accumulated equity value at each recorded event.

After processing all lines, the script constructs an output filename in the chartDir directory using the exchange, account, and pair tokens and either the .html or .png extension depending on the first argument. It sets a title string that includes the account and pair.

Using Plotly, the program creates a single subplot figure and adds a Scatter trace plotting equity (y) against timestamps (x) with the name "Equity" and a blue marker color. It then checks for the existence of a logo file at /home/JackrabbitRelay2/Data/logo.png. If that file exists, it adds the logo as a layout image to the figure; for HTML output it sets the source to '/logo.png' and for image output it sets the source to the file URI 'file:///home/JackrabbitRelay2/Data/logo.png'. The logo is positioned centered in paper coordinates and rendered with opacity 0.1 and size 1x1.

The figure's y-axis is labeled "Equity Curve" and the layout is updated with the title centered and the 'plotly_white' template. Finally, if the requested output type was HTML the script writes the figure to the constructed .html file; otherwise it writes an image file (.png) with resolution 1920x1024. The program performs no other output.
