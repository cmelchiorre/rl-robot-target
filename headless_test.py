
# WORK IN PROGRESS:

# experimenting to make the application runnable on a headless remote linux server
# currently not working

from panda3d.core import loadPrcFileData
from direct.showbase.ShowBase import ShowBase


loadPrcFileData("", "window-type none")

from world import RobotTargetWorld

world = RobotTargetWorld(headless=True)
# it doesn't work since i couldn't find a way to make the bot camera buffer render when 
# `window-type none` is active.
# I had defined the headless param in the constructor so as to allow RobotTargetWorld to
# tell the case when it was run in headless mode; now I removed this for 
# the mentioned problem.

# Give feedback on command prompt log that the Panda3D program is active 
# 3 seconds after launch
base.task_mgr.do_method_later(3, print, "Panda3D is still running", ["foo"])

world.run()

