from panda3d.core import TextNode

from direct.gui.DirectGui import *
from direct.gui.OnscreenText import OnscreenText

class InfoFrame:

    def __init__(self):

        # Create a semi-transparent DirectFrame
        # frame_pos = (0.1, 0, -0.4)
        # frame_size = (0, 1, -0.25, 0.3)
        frame_pos = (0.1, 0, -0.1)
        frame_size = (0, 1, 0, -.55)
        
        text_pos = (0.05, 0, -0.1) # text position relative to frame

        self.frame = DirectFrame(frameColor=(0, 0, 0, .5),
                    frameSize=frame_size, 
                    pos=frame_pos,
                )
        
        self.textLabel = DirectLabel(
                text= f'frame: {frame_pos}\nsize:{frame_size}\ntext_pos: {text_pos}',
                # text_font = ...,
                pos=text_pos,
                text_fg = (1,1,1,.75), 
                relief = None,
                text_align = TextNode.ALeft,
                text_scale = .06, 
                parent = self.frame)

        # Attach the new NodePath to the aspect2d node
        self.frame.reparentTo(base.a2dTopLeft)
        self.textLabel.reparentTo(self.frame)

    def setText(self, text):
        self.textLabel.setText(text)

        