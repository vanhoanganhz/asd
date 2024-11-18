import os
import sys
import urllib3
from art import tprint
from loguru import logger

def setup():
    # Disables urllib3 warnings for cleaner logging output
    urllib3.disable_warnings()

    # Clears previous logger configurations
    logger.remove()

    # Adds a logger configuration to output logs to the console
    logger.add(
        sys.stdout,
        colorize=True,
        format="<light-cyan>{time:HH:mm:ss}</light-cyan> | <level>{level:<8}</level> | - <white>{message}</white>"
    )

    # Adds a logger configuration to output logs to a file with rotation and retention
    logger.add(
        "./logs/logs.log",
        rotation="1 day",
        retention="7 days"
    )

def show_dev_info():
    # Clears the console screen
    os.system("cls" if os.name == "nt" else "clear")

    # Prints ASCII art for "JamBit"
    tprint("JamBit")

    # Prints additional information
    print("\x1b[36mChannel: \x1b[34mhttps://t.me/JamBitPY\x1b[34m")
    print("\x1b[36mGitHub: \x1b[34mhttps://github.com/Jaammerr\x1b[34m")
    print()  # Prints a blank line

# Example usage:
# Uncomment the following lines to test the functions
# setup()
# show_dev_info()
