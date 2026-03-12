# Section 1 - Non-Technical Description

This small program continuously runs a specific trading-related application located in a folder, restarting it every three minutes so it keeps running indefinitely, and it passes along any input given when the program is started.

# Section 2 - Technical Analysis

The script is a shell (bash) script that begins by changing the current working directory to /home/Oanda using the cd command. This sets the environment for subsequent commands to execute from that directory.

After changing directory, the script enters an infinite loop constructed with while true; do ... done. Inside the loop it runs the executable /home/Oanda/oandaGridBot and supplies all positional arguments that were passed to the script when it was invoked; this is achieved by using $@, which expands to the complete list of original command-line arguments. Immediately after launching the executable, the script issues a sleep 180 command that pauses execution for 180 seconds (three minutes). When the sleep completes, the loop repeats: it invokes /home/Oanda/oandaGridBot again with the same arguments, then sleeps again, and so on forever.

Because the executable is called directly (without backgrounding), the script will wait for /home/Oanda/oandaGridBot to exit before executing the sleep and starting the next iteration. Each iteration therefore consists of: run /home/Oanda/oandaGridBot with the original script arguments, wait until that process finishes, then sleep for 180 seconds, then start it again. The initial comment indicates that the first argument is intended to be a configuration file, and that argument (along with any others) is forwarded to the executable unchanged. The script does not set shell options, handle signals, or perform any logging; its observable behavior is limited to repeatedly invoking the specified executable from /home/Oanda and pausing for three minutes between each invocation.
