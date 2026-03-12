Section 1 - Non-Technical Description

This program checks a historical price data file for repeated records and reports how many duplicate entries it finds after feeding each record into a technical-analysis component. It requires command-line inputs specifying an exchange, account, asset, and time frame; it looks for a text file named after the asset, reads its lines, processes each line through a technical-analysis object, counts any records the object flags as duplicates, and prints the duplicate count.

Section 2 - Technical Analysis

The script begins by extending the Python module search path and importing several standard modules (sys, os, json, datetime, time) plus two application-specific modules: JackrabbitRelay (aliased JRR) and JRRtechnical (aliased jrTA). It defines a main() function that first checks command-line arguments: if more than four arguments are provided, it assigns the first four to variables exchangeName, account, asset, and tf; otherwise it prints a brief usage message and exits with status 1.

Next, main() constructs a TechnicalAnalysis object by calling jrTA.TechnicalAnalysis(exchangeName, account, asset, tf, 5000) and storing it in the variable ta. The code builds a filename by removing any forward slashes from the asset string (asset.replace('/','')) and appending the ".txt" extension; it then checks for the existence of that file in the current working directory. If the file is not present, it prints a message indicating the missing candle file and exits with status 1.

The program then intends to iterate over the lines of the OHLCV (open-high-low-close-volume) dataset to search for duplicates. It initializes a duplicate counter dc to zero. For each line returned by fh.readlines(), it splits the line on commas into a list named slice, converts the first element of slice to an integer, converts the remaining elements to floats, and passes the resulting list to ta.Rolling(slice). After calling ta.Rolling, it checks ta.Duplicate; if ta.Duplicate evaluates as true, it increments the duplicate counter dc and continues to the next line. After the loop, it closes fh and prints the total number of duplicates found with the message "Duplicates: {dc}".

Finally, the script runs main() when executed as the main program by checking if __name__ == '__main__'.

Variable and operation details:
- exchangeName, account, asset, tf: strings obtained from command-line arguments.
- ta: an instance of TechnicalAnalysis created with the provided arguments plus the integer 5000.
- fn: the filename base derived from asset with slashes removed.
- dc: integer counter tracking how many records were flagged as duplicates by ta.
- The loop processes each line from a file handle fh (expected to be the opened candle file), splitting comma-separated values into a list; it converts the timestamp/time field to int and the numerical fields to float before passing the list to ta.Rolling.
- ta.Rolling(slice) is invoked for each parsed record; ta.Duplicate is inspected after each call to decide whether to increment dc.
- The final output is a single printed line showing the count of duplicates.

Note: the program's runtime behavior depends on the TechnicalAnalysis class and its Rolling method and Duplicate attribute supplied by the imported jrTA module, and on the presence and contents of the asset-based ".txt" file in the current directory.
