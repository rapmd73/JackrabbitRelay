## Section 1 - Non-Technical Description

This program reads a transaction history for a named account, counts how many times a specific asset was bought and sold on each date, and produces a daily activity chart for that asset and account, saving the chart either as an image or as an HTML file.

## Section 2 - Technical Analysis

The script expects three command-line arguments: an output type indicator (either "I" or "H", case-insensitive), an account name, and an asset identifier. It enforces that the first argument is present and equals "i" or "h" after lowercasing; otherwise it prints an error message and exits. It sets fixed filesystem paths for chart output and for Mimic account data, and it sets the variable exchange to the literal string "mimic".

The account argument is used to build a filename for the account history file by appending ".history" to the account name and prepending the MimicData directory. If that file does not exist on disk, the script prints a message asking the user to verify the wallet name and exits.

The account history file is read via a ReadFile function from an imported JRRsupport module. The returned text is stripped and split on newline into lines. Two dictionaries, bl and sl, are created to accumulate counts of buys and sells per date. Three lists, xps, buy, and sell, are prepared to hold the sorted dates and corresponding counts for plotting.

Each non-empty line from the history file is parsed as JSON. If a line fails JSON parsing, the script prints the damaged line and exits. For each parsed JSON object, the code reads the 'Asset' field and skips the entry unless it exactly matches the asset argument (the supplied asset argument is uppercased, and the JSON 'Asset' value is compared directly to that). For matching entries it extracts the date part from the 'DateTime' field by splitting on a space and taking the first token (so only the calendar date is used). It also reads the 'Action' field, uppercases it, and takes only its first character; that first character is used to determine whether the action is treated as a buy ('B') or a sell ('S').

For every date encountered the code ensures there are entries in both bl and sl dictionaries; missing keys are initialized to zero. If the action character is 'B', the code increments bl[date] by 1; if it is 'S', it increments sl[date] by 1. No other actions change the counts. After processing all lines, the code iterates over the sorted keys of the bl dictionary (dates in lexicographic order), appending each date to xps and the corresponding bl and sl counts to buy and sell lists respectively. The comment in the code indicates this approach presumes the sl dictionary has corresponding keys for each date (because both dictionaries were initialized when a date was first seen).

For plotting, the asset string is sanitized into pfn by removing forward slashes, colons, and hyphens. Depending on the initial output-type argument, the script constructs an output filename fn in the chartDir directory with a pattern like DailyActivity.mimic.<account>.<pfn>.html or .png.

A title string ts is built to include the account and asset. Two Plotly Bar traces are created: one for buy counts (colored red, labeled "Buy") and one for sell counts (colored green, labeled "Sell"), each assigned to a different offset group so they appear side-by-side per date. A Figure is constructed containing these two bars.

The figure receives a background layout image: if the output is HTML, the image source is a remote HTTPS URL; otherwise the source is a local file URL. The image is placed using paper coordinates, centered, sized to cover the whole plotting area, and given low opacity (0.1).

The y-axis label is set to "Daily Trading Activity" and the layout title is set using the ts string, centered horizontally. The plotly white template is applied.

Finally, if the initial argument asked for HTML output ('h'), the figure is written to the constructed .html filename using fig1.write_html(fn). If the initial argument asked for an image ('i'), the figure is written to the constructed .png filename using fig1.write_image(fn) with a width of 1920 and height of 1024. The script then ends.
