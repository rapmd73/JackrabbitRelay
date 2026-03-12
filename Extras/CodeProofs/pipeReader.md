## Section 1 - Non-Technical Description

This program generates up to a set number of short tasks, gives each task a random identifier, runs an external helper program for each task twice to produce two separate pieces of information, stores those pieces of information alongside each task, and then prints the full list of tasks with their associated data.

## Section 2 - Technical Analysis

The script begins by importing standard modules and a local support module named JRRsupport. It reads a file called "wordlist" through JRRsupport.ReadFile and splits its contents into a list named words. It also constructs a path to an external executable (pipeWriter) that the program will invoke repeatedly. A global locker object gLock is created by calling JRRsupport.Locker('pipeReader'), and a doubly linked list pList is created later using JRRsupport.DList with a provided compare function.

GetID()
- Generates a 20-character identifier string.
- For each of 20 positions it repeatedly picks a random index into a string of allowed characters (letters and digits). It repeats random index selection a random number of times (random.randrange(73,237)) before settling on one value, then ensures the chosen character is not identical to the previous character before appending it to the identifier.
- Returns the assembled 20-character string.

compareCounter(node, dz)
- Expects node to be an object with GetData() returning a JSON string and dz to be a JSON string.
- Loads JSON from both, extracts the 'ID' fields, converts them to strings, and compares them lexicographically.
- Returns -1 if dz's ID is less than node's ID, 1 if greater, or 0 if equal.
- This function is passed to pList as the comparison function for ordering/searching.

ProcessData(data, id)
- Starts the external program at the path pipeWriter via subprocess.Popen with pipes for stdin/stdout/stderr.
- Writes the provided data (encoded) to the subprocess stdin, then calls communicate() to read its output.
- Decodes and strips whitespace from the subprocess output and stores it as res.
- Constructs and returns a dictionary with keys 'ID' (set to the provided id) and 'Result' (set to the subprocess output).

ProcessResults(result)
- Acquires the global lock gLock.
- Calls pList.find(json.dumps(result)) to locate a node whose stored JSON string matches the provided result JSON string (as a string).
- If a node is found, it reads that node's stored JSON data, parses it into a dict pd, sets pd['Result'] to result['Result'], then writes the updated JSON string back into the node via SetData.
- Releases the lock.

ProcessWords(result)
- Picks a random index into the preloaded words list.
- Acquires the global lock gLock.
- Calls pList.find(json.dumps(result)) to find a matching node by serialized JSON.
- If found, loads that node's JSON, sets pd['Word'] to the randomly chosen word, and writes the updated JSON back to the node.
- Releases the lock.

Global list pList
- Created after the compareCounter function with JRRsupport.DList(Compare=compareCounter), so the list uses compareCounter for comparisons and searches.

main()
- Determines cMax as 10 by default or from the first command-line argument when present.
- Creates a multiprocessing.Pool with number of processes equal to 2 * CPU count and maxtasksperchild set to 237.
- In a loop from counter 0 up to (but not including) cMax:
  - Converts the counter to a string and creates a dictionary pData with keys 'Counter' (the string) and 'ID' (a new ID from GetID()).
  - Acquires gLock, inserts json.dumps(pData) into pList, and releases the lock.
  - Submits two asynchronous tasks to the ProcessPool:
    - One that runs ProcessData(data, id) and uses ProcessResults as the callback.
    - A second that runs ProcessData(data, id) and uses ProcessWords as the callback.
  - Increments counter and repeats until cMax tasks have been queued.
- If an exception occurs within the try block, it closes and joins the ProcessPool.
- After task submission completes, it iterates the list pList from head to tail, printing each node's stored JSON string via GetData().

Program runtime behavior summary
- For each loop iteration a new entry is inserted into the global list as a JSON string containing 'Counter' and 'ID'.
- Two subprocess-based tasks are started per entry. Each task runs the external pipeWriter program providing the counter string on stdin and collects its stdout. Each task returns a dict with the same ID and the subprocess output under 'Result'.
- The first task's callback, ProcessResults, finds the list entry matching the returned serialized JSON and sets that entry's 'Result' field to the returned subprocess output.
- The second task's callback, ProcessWords, finds the same entry (matching by serialized JSON) and sets that entry's 'Word' field to a randomly chosen word from the loaded wordlist.
- After all submissions, the program prints the final JSON stored in each list node, which will include the original 'Counter' and 'ID', and - depending on timing and successful callback execution - may include 'Result' and 'Word' fields populated by the callbacks.
