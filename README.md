# JackrabbitRelay
Jackrabbit Relay is an API endpoint for cryptocurrency exchange.

## Disclaimer

Use this Software at your own risk. The author(s) accept no
responsibility for losses incurred through using this software. While we
have gone to great lengths to test the software, if you do find any bugs,
please report them to us in the [Jackrabbit Support
Server](https://discord.gg/g93TpbV) or on Github, and we will sort them
out. Remember that risk management is your responsibility. If you lose
your account, that's entirely on you.

## Requirements

This software requiresa VPS with one core, one gig of RAM, 2 gigs of
swap, 40 gigs of excess storage. This software was developed for the
intention of using a VPS to its fullest extent. If you wish to use a
virtual environment, please consult your VPS documentation.

## Securoty and firewall

Whitelisting IP addresses and setting up restrictions is solely to the
the responsibility of your native firewall. There is absolutely no way I
can provide any level of security that is even remotely comparable to the
firewall your VPS already comes with. Suggesting such is a severe
misnomer to you and the security of your VPS. Please consult the
documentation of your VPS for establishing your firewall rules.

## Installation

Start with these shell commands

    mkdir -p /home/GitHub
    cd /home/GitHub
    git clone https://github.com/rapmd73/JackrabbitRelay

You now have a copy of the Jackrabbit repository. Now its time to install
everything.

    cd /home/GitHub/JackrabbitRelay
    ./install

At this point the files are inatalled, but more setup is required before
Relay is ready to run. Configuring the exchanges and crontab need to be
completed next.

## Configuration

The Jackrabbit Relay file structure and folder layout is very simple:

    /home/JackrabbitRelay/

        This is the main folder

    /home/JackrabbitRelay/Config

        This is where all configuration files are stored

    /home/JackrabbitRelay/Base

        All program files go here

    /home/JackrabbitRelay/Logs

        All log files go here

In the base directory (/home/JackrabbitRelay/Base), there are several
files:

    CCXT-PlaceOrder

        This is the Order Processor. You actually wont use this file
        directly, but rather copy it to the actual exchange designated
        order transactor, for example PlaceOrder.ftxus

    PlaceOrder.tester

        This is just a dummy test module that you can use to test the
        connection with TradingView. It too, gets copied to the exchange
        designator, for example, PlaceOrder.kraken

    JackrabbitRelay

        This is the actual server program that waits for a connewction.
        It should NOT be ran directly, but rather through the
        RelayLauncher shell script.

    RelayLauncher

        This shell script sets the port and launches the server. It is
        the harness that keeps everything running and is what you place
        in your CronTab.

The Jackrabbit Relay files are ver sime JSON based text.  Here is an example:

    { "Account":"MAIN","API":"YourAPI","SECRET":"YourSecret","RateLimit":"200" }

This would be placed in a folder called /home/JackrabbitRelay/Config and
named something like ftxus.cfg

This file would be the configuration for the FTX.US exchange.

Now for the details:

    Account: this MUST be MAIN, case sensitive, for the main account of
    every exchange.

    API: your API key exactly as your exchange gives it to you.

    SECRET: your SECRET exactly as your exchange gives it to you.

    RateLimit: This is the amount Relay waits between each exchange API
    call.

        ALL EXCHANGES HAVE RATE LIMIT REQUIREMENTS.

        This value represent milliseconds. 1000 is one second. If you
        leave this out, chances are you will be banned from your
        exchange, most likely temporarily. You will have to tweak this
        number based upon your exchange.

Jackrabbit support multiple API per exchange (sub)account. This is
accomplished by this format:

    { "Account":"MAIN","API 1":"YourAPI","SECRET 1":"YourSecret","RateLimit":"200" }
    { "Account":"MAIN","API 2":"YourAPI","SECRET 2":"YourSecret","RateLimit":"200" }

The above means the your MAIN account has two API/SECRET combinations the
Relay will rotate between. Each (sub)account can hace as many as your
exchange will allow.
