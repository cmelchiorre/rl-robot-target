# from direct.actor.Actor import Actor
from panda3d.core import NodePath

from agent import *
from config import *

# 
ROTATE_STEP = 45
MOVE_STEP = 10

class Bot(NodePath):

    def __init__(self, world):

        self.world = world
        NodePath.__init__(self, 'Bot')

        self.model = self.world.loader.loadModel("assets/models/bot-arrow.egg")
        self.model.reparentTo(self)
        self.registerKeyboardEvents()

        self.agent = BotAgent(world=self.world, 
                              model_path=config['model_path'], 
                              model_prefix=config['model_prefix'], 
                              best_model=config.get('best_model', None),
                              log_path=config['log_path']
                              )
        

    def registerKeyboardEvents(self):

        # setup arrow movements

        self.keyMap = {
            "arrow_up": False,
            "arrow_down": False,
            "arrow_left": False,
            "arrow_right": False
        }

        self.world.accept('arrow_up', self.updateKeyMap, ['arrow_up', True] )
        self.world.accept('arrow_up-up', self.updateKeyMap, ['arrow_up', False] )
        self.world.accept('arrow_down', self.updateKeyMap, ['arrow_down', True] )
        self.world.accept('arrow_down-up', self.updateKeyMap, ['arrow_down', False] )
        self.world.accept('arrow_left', self.updateKeyMap, ['arrow_left', True] )
        self.world.accept('arrow_left-up', self.updateKeyMap, ['arrow_left', False] )
        self.world.accept('arrow_right', self.updateKeyMap, ['arrow_right', True] )
        self.world.accept('arrow_right-up', self.updateKeyMap, ['arrow_right', False] )

        taskMgr.add(self.update, 'MovementKeyHandlerUpdate')


    def updateKeyMap(self, key, value):
        self.keyMap[key] = value

    def update(self, task):
        dt = globalClock.getDt()

        if self.keyMap['arrow_up']:
            self.moveForward(dt*MOVE_STEP)
        if self.keyMap['arrow_down']:
            self.moveBackward(dt*MOVE_STEP)
        if self.keyMap['arrow_left']:
            self.rotateLeft(dt*ROTATE_STEP)
        if self.keyMap['arrow_right']:
            self.rotateRight(dt*ROTATE_STEP)
        
        return task.cont


    def moveForward(self, step=MOVE_STEP):
        quat = self.getQuat(render)
        fwd = quat.getForward()
        self.setPos(self.getPos(render) + fwd*step)

    def moveBackward(self, step=MOVE_STEP):
        quat = self.getQuat(render)
        fwd = quat.getForward()
        self.setPos(self.getPos(render) - fwd*step)

    def rotateLeft(self, angle=ROTATE_STEP ):
        heading = self.getH()
        self.setH( heading + angle )

    def rotateRight(self, angle=ROTATE_STEP ):
        heading = self.getH()
        self.setH( heading - angle )


