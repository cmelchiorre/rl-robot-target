from world import *
from environment import *
from config import *

from stable_baselines3 import PPO, A2C
from stable_baselines3.common.monitor import Monitor
from gym.wrappers import TimeLimit

from stable_baselines3.common.callbacks import BaseCallback, CheckpointCallback, EvalCallback

import os

MAX_STEPS_PER_EPISODE = config['n_max_steps_per_episode']

class BotAgent:

    def __init__(self, world, model_path, model_prefix, best_model=None, log_path="./logs"):

        self.world = world
        env = BotWorldEnv(world)
        env = TimeLimit( env, max_episode_steps=config['n_max_steps_per_episode'] )
        # env = Monitor(env, filename=f"/logs/{config['model_prefix']}/stats_{config.get('best_model', 'new')}.log")
        self.environment = env
        self.agent = None

        self.model_path = model_path
        self.model_prefix = model_prefix
        self.best_model = best_model
        self.log_path = log_path
        self.load()

        self.playing_steps = 0
        self.current_obs = None
        self.cumulative_reward = 0

    def load(self):

        if self.model_path == None or self.model_prefix == None:
            raise

        from typing import Callable
        def linear_schedule(initial_value: float) -> Callable[[float], float]:
            def func(progress_remaining: float) -> float:
                lr = progress_remaining * initial_value
                if lr < 0.0003: lr = 0.0003
                return lr
            return func
        
        initial_learning_rate = config.get('initial_learning_rate', 0.0003)
        debug(f"settining initial_learning_rate={initial_learning_rate}")

        if self.best_model == None:
            print("creating new agent")
            # no previously loaded agent, instantiate new one
            self.agent = PPO("CnnPolicy", self.environment, verbose=1 
                             , learning_rate=linear_schedule(initial_learning_rate))
        else:
            try:
                print(f"loading agent: {self.best_model}")
                model_fname = f"{self.model_path}/{self.model_prefix}/{self.best_model}.zip"
                self.agent = PPO.load( model_fname, self.environment 
                                    , learning_rate=linear_schedule(initial_learning_rate))
            except Exception as e:
                print(f"ERROR: cannot load {model_path}")
                self.agent = None
                raise e


    def learn(self, n_episodes, n_max_steps_per_episode=MAX_STEPS_PER_EPISODE):
        
        if self.agent == None or self.environment == None:
            raise

        base.win.setActive(False)
            
        custom_callback = CustomSaveBestCallback(self.model_path, self.model_prefix)
        eval_callback = EvalCallback(eval_env=self.environment,
                                     best_model_save_path=f"{self.model_path}/{self.model_prefix}",
                                    log_path="./logs/", 
                                    eval_freq=config['eval_freq'],
                                    deterministic=True, 
                                    render=False, 
                                    callback_on_new_best=custom_callback
                                    )

        checkpoint_callback = CheckpointCallback( \
            save_freq=config['checkpoint_save_freq'], 
            save_path=f"{self.model_path}/{self.model_prefix}", 
            name_prefix=f"{self.model_prefix}_checkpoint"
            )

        debug_state = config['debug']
        config['debug'] = False

        model_history = self.agent.learn( 
            total_timesteps=n_episodes*n_max_steps_per_episode,
            reset_num_timesteps=False,  
            callback=[eval_callback, checkpoint_callback],
            log_interval=1
        )
        config['debug'] = debug_state

        base.win.setActive(True)
        
        print("learning terminated...")
    

    def play(self, n_max_steps_per_episode=MAX_STEPS_PER_EPISODE ):
        
        if self.agent == None or self.environment == None:
            raise

        self.playing_steps = n_max_steps_per_episode
        self.current_obs = self.environment.reset(reset_positions=False)
        self.cumulative_reward = 0

        taskMgr.add(self.playStep, 'AgentPlayUpdate')


    def playStep(self, task):

        dt = globalClock.getDt()

        action = self.agent.predict(self.current_obs)[0]
        
        self.current_obs, reward, done, info = self.environment.step(action)
 
        self.cumulative_reward += reward

        if done: # episode ended
            return task.done

        self.playing_steps -= 1     
        if self.playing_steps <= 0:
            print("max play step reached")
            return task.done
        
        return task.cont


class CustomSaveBestCallback(BaseCallback):

    def __init__(self, model_path, model_prefix):
        self.model_path = model_path
        self.model_prefix = model_prefix
        super(CustomSaveBestCallback, self).__init__()

    def _on_step(self) -> bool:
        print(f"eval callback steps: {self.num_timesteps}")

        file_path = f"{self.model_path}/{self.model_prefix}/best_model.zip"
        new_file_path = f"{self.model_path}/{self.model_prefix}/{self.model_prefix}_{self.num_timesteps}_steps.zip"
        if os.path.exists(f"agents"):
            directory = os.path.dirname(file_path)
            os.rename(file_path, new_file_path)
            print(f"File '{file_path}' renamed to '{new_file_path}'")
        else:
            print(f"File '{file_path}' does not exist.")
        return True
