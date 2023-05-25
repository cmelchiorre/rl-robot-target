import gym
import numpy as np
import random

from config import *

ACTION_FORWARD = 0
ACTION_TURN_LEFT = 1
ACTION_TURN_RIGHT = 2

# @TODO choose values for these
# these values are different from those defined in Bot.py
# for MOVE_STEP and ROTATE_STEP
AGENT_MOVE_STEP = 1
AGENT_ROTATE_STEP = 10

# cost of each step to prioritize faster solutions
REWARD_STEP_PENALTY = 0.1
INVALID_ACTION_PENALTY = 1.0
REWARD_TARGET_REACHED = 1000.0

# terminate when bot-target distance is lower than this threshold
COLLISION_THRESHOLD = 1

class BotWorldEnv(gym.Env):

    metadata = {'render.modes': ['infoframe'] }

    def __init__(self, world):
        self.world = world

        self.observation_space = gym.spaces.Box(
            low=0, high=255, shape=(60, 80, 3), dtype=np.uint8)

        self.action_space = gym.spaces.Discrete(3)
    
    def get_obs(self):

        obs = self.world.getBotCameraBuffer().copy()

        if not self.observation_space.contains(obs):
            # should never happen
            print(obs)
            raise ValueError("Observation is not within the observation space bounds.")

        return obs


    def reset(self, reset_positions = True):

        if reset_positions:
            bot_x = random.uniform(-10.0, 10.0)
            bot_y = random.uniform(-10.0, 10.0)
            self.world.bot.setPos(bot_x, bot_y, 0.0)

            tgt_x = random.uniform(-10.0, 10.0)
            tgt_y = random.uniform(-10.0, 10.0)
            self.world.target.setPos(tgt_x, tgt_y, 0.0)

        return self.get_obs()
    
    def valid_move(self, pos):
        return pos.x >= -10 and pos.x <= 10 and \
               pos.y >= -10 and pos.y <= 10

    def step(self, action):

        # print(f"env.step: action={action}")
        base.graphicsEngine.renderFrame()

        #debug
        old_obs = self.get_obs()
        old_dist = self.world.getBotTargetDistance()
        old_angle = self.world.getBotTargetAngle()
        #~debug

        valid_action = True

        if action == ACTION_FORWARD:
            
            old_pos = self.world.bot.getPos( )
            old_dst = self.world.getBotTargetDistance()
            
            self.world.bot.moveForward(step=AGENT_MOVE_STEP)
            new_pos = self.world.bot.getPos()
            new_dst = self.world.getBotTargetDistance()
            
            if not self.valid_move(new_pos):
                self.world.bot.moveBackward(step=AGENT_MOVE_STEP)
                valid_action = False
                reward = -INVALID_ACTION_PENALTY
            else:
                reward = (old_dst - new_dst)
                # print(f"old: {old_dst} -> new: {new_dst} | reward {reward}")

        if action == ACTION_TURN_LEFT:
            old_angle = self.world.getBotTargetAngle()
            self.world.bot.rotateLeft(angle=AGENT_ROTATE_STEP)
            new_angle = self.world.getBotTargetAngle()
            reward = (old_angle - new_angle)

        if action == ACTION_TURN_RIGHT:
            old_angle = self.world.getBotTargetAngle()
            self.world.bot.rotateRight(angle=AGENT_ROTATE_STEP)
            new_angle = self.world.getBotTargetAngle()
            reward = (old_angle - new_angle)

        reward -= REWARD_STEP_PENALTY

        if self.world.getBotTargetDistance() < COLLISION_THRESHOLD:
            reward += REWARD_TARGET_REACHED
            
        done = self.world.collisionDetected()

        info = {}
        obs = self.get_obs()
       
        debug(f"action: {action}, valid: {1 if valid_action else 0} reward: {reward:.3f}")
        
        return obs, reward, done, info
     
    def render(self, mode='infoframe'):
        self.world.updateInfoFrame()

    def close(self):
        pass