# Section 1 - Non-Technical Description

This program measures and prints how long several different ways of reading, copying, filtering, and deleting lines from a text file take; it reads data from a file named "testData", writes and rewrites an output file "opData" in a few different ways, and runs repeated removals from in-memory lists and a custom doubly linked list while timing each operation and reporting the elapsed seconds and the number of items processed.

# Section 2 - Technical Analysis

- Module imports and setup:
  - The script appends '/home/GitHub/JackrabbitRelay/Base/Library' to sys.path, then imports os, json, time and a module named JRRsupport from that location.
  - It uses time.time() to record start times and compute elapsed times.

- First timed block (file copy using JRRsupport):
  - s = time.time() captures the start.
  - buffer = JRRsupport.ReadFile('testData') reads the entire contents of 'testData' into the variable buffer (as a single string).
  - JRRsupport.WriteFile('opData', buffer) writes that buffer to 'opData'.
  - e = time.time() - s computes elapsed time.
  - It prints "Copy file took {e} seconds for {len(buffer)} bytes", where len(buffer) is the number of characters (bytes) in the buffer string.

- Second timed block (read, split, strip, write line-by-line with single writes):
  - s = time.time() sets the timer.
  - lines = JRRsupport.ReadFile('testData').split('\n') reads the file and splits into a list of lines using the newline character.
  - It opens 'opData' for writing with fh = open('opData', 'w').
  - It iterates over each line in lines, strips whitespace from both ends with line.strip(), and if the stripped line is neither None nor empty string, writes that line plus a newline to the file using fh.write(line+'\n').
  - fh.close() closes the file.
  - e = time.time() - s calculates elapsed time.
  - It prints "Buffer splice/1x1Write took {e} seconds for {len(lines)} lines", where len(lines) is the count of elements produced by split.

- Third timed block (read, split, strip, build a single buffer string, bulk write):
  - s = time.time() starts timing.
  - lines = JRRsupport.ReadFile('testData').split('\n') again gets a list of lines.
  - buffer = '' initializes an empty string.
  - It iterates lines, strips each, and if the stripped line is neither None nor empty string it appends line+'\n' to the buffer string.
  - JRRsupport.WriteFile('opData', buffer) writes the accumulated buffer to 'opData' in one operation.
  - e = time.time() - s computes elapsed time.
  - It prints "Buffer splice/Build Buffer/Bulk Write took {e} seconds for {len(lines)} lines".

- Fourth timed block (read 'opData', parse and repeatedly drop first element via slicing):
  - s = time.time() starts timing.
  - lines = JRRsupport.ReadFile('opData').split('\n') reads the output file and splits into a list of lines.
  - A loop runs 9000 times; each iteration reassigns lines = lines[1:], effectively creating a new list that excludes the first element (drops the head).
  - e = time.time() - s measures elapsed time.
  - It prints "ReadFile/parse/list delete took {e} seconds over {len(lines)} lines", where len(lines) is the final length after the repeated slices.

- Fifth timed block (open file, readlines, repeatedly drop first element via slicing):
  - s = time.time() records start time.
  - fh = open('opData', 'r') opens the file.
  - lines = fh.readlines() reads all lines into a list where each element includes its trailing newline.
  - fh.close() closes the file.
  - A loop runs 9000 times, each time reassigning lines = lines[1:], dropping the first element.
  - e = time.time() - s computes elapsed time.
  - It prints "bulk readlines/delete took {e} seconds over {len(lines)} lines" with the resultant list length.

- Sixth timed block (read lines, strip into list, repeated delete via slicing):
  - s = time.time().
  - fh = open('opData', 'r'); then lines = [].
  - For each line in fh.readlines(), it appends line.strip() to lines. fh.close().
  - A loop runs 9000 times dropping the first element with lines = lines[1:].
  - e = time.time() - s.
  - It prints "1by1 readline()/delete took {e} seconds over {len(lines)} lines".

- Seventh timed block (use JRRsupport.DList to insert unique-filtered items, then delete head data repeatedly):
  - s = time.time().
  - dList = JRRsupport.DList() constructs an instance of DList from JRRsupport.
  - Opens 'opData' and reads all lines into lines = fh.readlines().
  - For each line in lines: line.strip() is called and, if the stripped line is neither None nor empty string, dList.insert(line) is called. This populates dList; the naming suggests DList provides an insert operation that likely filters duplicates but the code only calls insert.
  - fh.close().
  - A loop runs 9000 times calling dList.delete(dList.GetHead().GetData()). Each iteration obtains the head node via GetHead(), gets its data via GetData(), and passes that to dList.delete(...) to remove that data from the list.
  - e = time.time() - s.
  - It prints "dList(dup filter)/1by1 took {e} seconds over {dList.Length()} lines", where dList.Length() is queried after the deletions to report the final length.

- Eighth timed block (repeat DList population using ReadFile then repeated deletes):
  - s = time.time().
  - dList = JRRsupport.DList() creates a fresh DList.
  - lines = JRRsupport.ReadFile('opData').split('\n') reads the file and splits lines.
  - For each line, after stripping and checking for non-empty, it inserts into dList via dList.insert(line).
  - A loop of 9000 iterations deletes the current head's data each time by calling dList.delete(dList.GetHead().GetData()).
  - e = time.time() - s.
  - It prints "dList(dup filter)/ReadFile took {e} seconds over {dList.Length()} lines".

- Overall behavior:
  - The script performs a sequence of file I/O and in-memory operations, each wrapped in timing measurement and followed by a status print describing the elapsed time and counts (bytes or lines).
  - It relies on JRRsupport for ReadFile, WriteFile, and a DList class and uses list slicing, file read methods, string strip and concatenation, and repeated deletion of head elements from lists and the DList to produce measurable timings for different approaches.
