# test reddit bot to message me things

import ast
import praw
import random
import threading
import time


r = praw.Reddit(user_agent="test")
d = ast.literal_eval(open("_secret_TestBotInfo.txt").read().strip())
r.login(d["bot"], d["password"])

r.send_message(
    d["user"], 
    "Test Message at {0}".format(time.strftime("%y-%m-%d-%H:%M:%S")),
    "Here's a random number from 1 to 100: {0}.\n- your test bot".format(random.randrange(1,101))
)