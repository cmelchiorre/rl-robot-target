from direct.showbase.ShowBase import ShowBase

from panda3d.core import *

from direct.task import Task
from direct.gui.OnscreenImage import OnscreenImage

from cameramouse import CameraMouseHandler
from infoframe import InfoFrame
from bot import Bot
from config import *

import numpy as np
import random
import math
from PIL import Image
import datetime

# small size for performance reasons
BOT_CAMERA_FILM_WIDTH = 80 
BOT_CAMERA_FILM_HEIGHT = 60

class RobotTargetWorld(ShowBase):

    # Class init method

    def __init__(self):

        super().__init__()

        wp = WindowProperties()
        wp.setSize(1200, 720)
        self.win.requestProperties(wp)

        # load models from the environment default folder Lib\site-packages\panda3d\models
        self.loadGround()        
        self.loadBot()
        self.loadTarget()

        # self.pligth_np = self.createPointLight()
        self.dlight_np = self.createDirectionalLight()
        self.alight_np = self.createAmbientLight()
        
        self.render.setShaderAuto()

        # set viewport stuff
        self.setupCamera()
        self.setupCrosshair()
        self.setupSkybox()
        self.setupMouseWatcher()

        # set collision system
        self.setupCollisions()

        # setup bot camera
        self.setupBotCamera()

        # create frame for status messages
        self.info_frame = InfoFrame()

        taskMgr.add(self.updateInfoFrame, "updateInfoFrameTask" )

        self.learning = False
        self.accept('control-t', self.startLearn )
        self.accept('control-p', self.startPlay )
        self.accept('control-o', self.targetRandomMove )
        self.accept('control-s', self.saveBotCameraScreenshot)

        

    # 3D Model loading functions

    def loadGround(self):
        """
        Load the 3d model for the ground plane
        """
        self.ground = self.loader.loadModel("assets/models/ground.egg")
        self.ground.reparentTo(self.render)

    def loadBot(self):
        """
        Loads 3d model for the bot (blue ball with camera)
        """
        self.bot = Bot(self)
        # self.bot = self.loader.loadModel("assets/models/bot.egg")
        self.bot.reparentTo(self.render)
        self.bot.setPos(5, -5, 0)

    def loadTarget(self):
        """
        Loads 3d model for target (green box)
        """
        self.target = self.loader.loadModel("assets/models/target.egg")
        self.target.setPos(-5, 5, 0)
        self.target.reparentTo(self.render)

    def createAmbientLight(self):
        """
        Creates ambient light
        """
        print("creating ambient")
        ambientLight = AmbientLight('ambientLight')
        ambientLight.setColor(Vec4(0.8, 0.8, 0.9, 1))
        ambientLight_node_path = self.render.attachNewNode(ambientLight)

        self.render.setLight(ambientLight_node_path)
        
        return ambientLight_node_path
    
    def createDirectionalLight(self):
        """
        Create directional light
        """
        print("creating directional")

        dir_light = DirectionalLight('directionalLight')
        dir_light.setColor((1, 1, 1, 1))
        dir_light.setShadowCaster(True, 512, 512)

        dir_light_node_path = render.attachNewNode(dir_light)
        dir_light_node_path.setHpr(45, -45, 0)
        
        self.render.setLight(dir_light_node_path)

        return dir_light_node_path
    
    def createPointLight(self):
        """
        Creates point light
        """
        print("creating point")

        self.light_speed = 2
        self.light_x = 10

        ptlight = PointLight("ptlight")
        ptlight.setColor((1,1,1,1))
        
        ptlight_node_path = self.render.attachNewNode(ptlight)
        ptlight_node_path.setPos(-6, 20, 3)

        ptlight_attr = LightAttrib.make()
        ptlight_attr = ptlight_attr.addOnLight(ptlight_node_path)
        
        self.render.setLight(ptlight_node_path)
        self.render.setAttrib(ptlight_attr)

        # self.taskMgr.add( self.move_point_light, "move-light")
        return ptlight_node_path
    

    # 3D World seutup functions

    def setupCamera(self):
        """
        Main camera setup
        """

        base.disableMouse( )
        #self.camera.setPos(0, -30, 20)
        self.camera.setPos(0, 0, 40)
        self.camera.lookAt(0,0,0)

        # Create an instance of CameraMouseHandler and pass self as an argument
        self.mouseHandler = CameraMouseHandler(self)

    def setupCrosshair(self):
        """
        Used only for debugging, positions a crosshairs marker
        at the center of the (-10.0, 10.0) plane.
        """
        # set transparent crosshair
        crosshairs = OnscreenImage(
            image = 'assets/images/crosshairs.png',
            pos = (0, 0, 0),
            scale = 0.05
        )
        crosshairs.setTransparency(TransparencyAttrib.MAlpha)

    def setupSkybox(self):
        """
        Sets the sky box background
        """
        skybox = loader.loadModel('assets/skybox/skybox-circular.egg')
        skybox.setScale(500)
        skybox.setBin('background', 1)
        skybox.setDepthWrite(0)
        skybox.setLightOff()
        skybox.reparentTo(self.render)

        # see: https://discourse.panda3d.org/t/changing-the-background-image-work-at-random-times-only/28594/1
        # self.background = OnscreenImage(parent=render2dp, 
        #                         image="./assets/skybox/blueprint-background.jpg") 
        # base.cam2dp.node().getDisplayRegion(0).setSort(-99) 
        # cannot make the bot camera display region not transparent in sky regions


    def setupMouseWatcher(self):
        """
        Initialize MouseWatcher to caputre mouse click events.
        """
        self.mouse_watcher = MouseWatcher('mouseWatcher')
        base.mouseWatcher.attachNewNode(self.mouse_watcher)

        # setup jump to mouse click
        self.accept('mouse1', self.jumpToMouse, [ self.bot ])
        self.accept('shift-mouse1', self.jumpToMouse, [ self.target ])
        self.plane = Plane(Vec3(0, 0, 1), Point3(0, 0, 0))

    def setupCollisions(self):
        """
        Setup collision system to capture collisions between
        the bot and the target
        """
        self.cTrav = CollisionTraverser()  # Collision traverser for handling collisions
        self.cHandler = CollisionHandlerQueue()  # Collision handler to store collision results

        # Create collision nodes for bot and target
        botCollisionNode = CollisionNode("bot")
        botCollisionNode.addSolid(CollisionSphere(0, 0, 0, 0.5))  # Adjust the sphere radius according to your bot's size
        botCollisionNP = self.bot.attachNewNode(botCollisionNode)

        targetCollisionNode = CollisionNode("target")
        targetCollisionNode.addSolid(CollisionSphere(0, 0, 0, 0.5))  # Adjust the sphere radius according to your target's size
        targetCollisionNP = self.target.attachNewNode(targetCollisionNode)

        self.cTrav.addCollider(botCollisionNP, self.cHandler)  # Add bot's collision node to the traverser

    def setupBotCamera(self):
        """
        Setup the bot camera. 
        This is a secondary camera attached to the bot, provides its PoV.
        see: self.getBotCameraBufferImage
        """

        # self.botCam  = self.bot.attachNewNode(Camera("botCam"))
        self.botCamBuffer = base.win.makeTextureBuffer(f'botCam', BOT_CAMERA_FILM_WIDTH, BOT_CAMERA_FILM_HEIGHT )
        
        self.botCamTexture = Texture()
        self.botCamBuffer.addRenderTexture(self.botCamTexture, 
                                           GraphicsOutput.RTM_copy_ram
                                           )

        # self.botCamBuffer.setSort(-99)
        self.botCam  = base.makeCamera( self.botCamBuffer )

        self.botCam.reparentTo(self.bot)
        self.botCam.setPos(0, 0.15, 0.5) 

        # Get the current lens of the botCam
        self.botCam.node().getLens().setFilmSize(BOT_CAMERA_FILM_WIDTH, BOT_CAMERA_FILM_HEIGHT)

        botCamDispRegion = base.win.makeDisplayRegion(0.75, 0.95, 0.05, 0.3 )
        botCamDispRegion.setCamera(self.botCam)
        botCamDispRegion.setClearDepthActive(True)


    # Action functions

    def targetRandomMove(self):
        """
        Randomly positions the target (green box) on the (-10.0, 10.0) plane.
        Called when the user presses 'control-o'
        """
        tgt_x = random.uniform(-10.0, 10.0)
        tgt_y = random.uniform(-10.0, 10.0)
        self.target.setPos(tgt_x, tgt_y, 0.0)

    def jumpToMouse(self, object):
        """
        Called when the user left-clicks the mouse.
        Positions the bot on the (-10.0, 10.0) plane corresponding to the 
        clicked location on the plane.
        """
        if self.mouse_watcher.hasMouse():
            
            mouse_pos = self.mouse_watcher.getMouse()
            near_point = Point3()
            far_point = Point3()
            self.camLens.extrude(mouse_pos, near_point, far_point)
            
            mouse_pos_3d = Point3()
            
            if self.plane.intersectsLine(mouse_pos_3d,
                render.getRelativePoint(self.camera, near_point),
                render.getRelativePoint(self.camera, far_point)):

                x = mouse_pos_3d.getX()
                y = mouse_pos_3d.getY()
        
                if  x>=-10.0 and x<=10 and y>=-10.0 and y<=10:
                    # Only if valid position...
                    # Move the object to the mouse position on the z=0 plane
                    object.setPos(x, y, 0)

    def collisionDetected(self):
        """
        Called to check wether a collision between the bot
        and the target occurred. Signals successfull end of episode.
        """
        # Check if any collisions occurred
        self.cTrav.traverse(self.render)
        return self.cHandler.getNumEntries() > 0
        
    def startLearn(self):
        """
        Triggers learning for the bot's agent, with parameters as specified by configuration
        Called when the user pressed 'control-t'
        """
        print("learning...")
        self.learning = True
        self.bot.agent.learn(config['n_episodes'], config['n_max_steps_per_episode'])
        
    def startPlay(self):
        """
        Starts playing an episode
        Called when the user pressed 'control-p'
        """
        self.playing = True
        self.bot.agent.play(n_max_steps_per_episode=config['n_max_steps_per_episode'])

    # Utility functions

    def getBotTargetDistance(self):
        """
        Calculates current distance between the bot and the target.
        Useful for reward evaluation.
        """
        return self.bot.getDistance(self.target)
    
    def getBotTargetAngle(self):
        """
        calculate angle between the bot's y axis and the 
        line that connects its position to the target
        see: https://math.stackexchange.com/questions/878785/how-to-find-an-angle-in-range0-360-between-2-vectors
        Useful for reward evaluation.
        """

        bot_pos = self.bot.getPos()
        target_pos = self.target.getPos()
        
        u = self.bot.getRelativeVector(render, (0, 1, 0)) # bot_y_axis
        u = Vec2(-u.x, u.y) # don't know why but I have to invert x coord

        v = target_pos - bot_pos # dir_vec
        v = Vec2(v.x, v.y)
        v.normalize()
        
        dot = u.x*v.x + u.y*v.y      # dot product
        det = u.x*v.y - u.y*v.x      # determinant

        return abs(math.atan2(det, dot))  

    def updateInfoFrame(self, task):
        """
        Updates debugging information on the top-left InfoFrame UI
        """

        # distance
        distance = self.bot.getDistance(self.target)
        
        # angle
        angle = self.getBotTargetAngle()

        # bot pos
        pos = self.bot.getPos()

        # current bot agent's cum_reward
        reward = self.bot.agent.cumulative_reward 
        steps = self.bot.agent.playing_steps

        u = self.bot.getRelativeVector(render, (0, 1, 0))
        u = Vec2(-u.x, u.y) # bot_y_axis

        newtext = f" pos {pos.x:.2f} {pos.y:.2f} \
                    \n distance: {distance:.2f} \
                    \n angle:  {angle:.2f} \
                    \n bot y axis: {u.x:.2f}, {u.y:.2f} \
                    \n ------------- \
                    \n cumulative reward {reward:.3f} \
                    \n remaining steps {steps}"
        
        self.info_frame.setText(newtext)
        return Task.again

    def getBotCameraBuffer(self):
        """
        Returns the RAM image corresponding to the current bot camera view
        as an np.array
        """
        buffer = self.botCamTexture.getRamImageAs("RGB")
        buffer = np.asarray(memoryview(buffer))
        # for some reason the image is stored as (rows, cols, colors), with
        # rows inveerted upside down
        buffer = buffer.reshape(BOT_CAMERA_FILM_HEIGHT, BOT_CAMERA_FILM_WIDTH, 3)
        buffer = buffer[::-1, :, :] 

        return buffer

    def saveBotCameraScreenshot(self):
        """
        saves the current bot camera view as png file
        """
        buffer = self.getBotCameraBuffer()
        image = Image.fromarray(np.uint8(buffer))

        current_datetime = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"output/{current_datetime}.png"
        image.save(filename)
