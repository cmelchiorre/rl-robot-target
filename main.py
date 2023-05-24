from world import RobotTargetWorld

world = RobotTargetWorld()

# debug
action_space = world.bot.agent.environment.action_space

world.run()
