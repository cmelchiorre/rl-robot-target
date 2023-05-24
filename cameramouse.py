from panda3d.core import Point2, Vec3, Mat4
import math

class CameraMouseHandler:

    def __init__(self, world):

        self.world = world
        self.registerMouseEvents()

    def registerMouseEvents(self):

        self.cum_zoom = 0
        self.rotate_mode = False

        # mid mouse > rotate
        self.world.accept('mouse2', self.on_mouse2)
        self.world.accept('mouse2-up', self.on_mouse2_up)
        # wheel > rotate
        self.world.accept('wheel_up', self.on_wheel_up)
        self.world.accept('wheel_down', self.on_wheel_down)

        taskMgr.add(self.update, "CameraMouseHandlerUpdate")


    def on_mouse2(self):
        self.rotate_mode = True
        if base.mouseWatcherNode.hasMouse():
            self.pan_start_pos = Point2(base.mouseWatcherNode.getMouse())

    def on_mouse2_up(self):
        self.rotate_mode = False

    def on_wheel_up(self):
        # Handle the mouse wheel up event
        self.cum_zoom += 5

    def on_wheel_down(self):
        # Handle the mouse wheel down event
        self.cum_zoom -= 5


    def update(self, task):

        # Check if the mouse is available before accessing the position
        if base.mouseWatcherNode.hasMouse():

            mouse_pos = Point2(base.mouseWatcherNode.getMouse())

            # ROTATE
            # if self.keyMap['mouse2']:
            if self.rotate_mode:
                
                camera_pos = self.world.camera.getPos()
                
                heading_diff = (mouse_pos[0] - self.pan_start_pos[0])
                pitch_diff = (mouse_pos[1] - self.pan_start_pos[1])

                new_pos = self.rotate_point_3d( camera_pos, heading_diff, pitch_diff )
                self.world.camera.setPos(new_pos)
                self.world.camera.lookAt( 0, 0, 0 )

            # ZOOM 
            elif self.cum_zoom != 0:
                    
                camera_pos = self.world.camera.getPos()
                new_pos = self.zoom_point_3d( camera_pos, self.cum_zoom )
                self.world.camera.setPos(new_pos)
                self.world.camera.lookAt( 0, 0, 0 )

        self.cum_zoom = 0
        return task.cont


    def rotate_point_3d(self, point, thetaH, thetaV):
        # Convert angles to radians
        thetaH = -math.radians(thetaH*40)
        thetaV = math.radians(thetaV*80)

        # Create rotation matrices
        rot_h = Mat4.rotateMat(thetaH, Vec3(0, 0, 1))
        rot_v = Mat4.rotateMat(thetaV, Vec3(1, 0, 0))

        p = Vec3(*point)
        
        # Combine matrices
        rot = rot_h * rot_v
        p = rot.xformPoint(p)

        # Return new coordinates
        return p.x, p.y, p.z
    
    
    def zoom_point_3d(self, point, zoom):

        # Extract coordinates of point
        x, y, z = point

        # Compute vector from (x, y, z) to (0, 0, 0)
        v = (-x, -y, -z)

        # Normalize vector to get direction to move in
        norm = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
        if norm == 0:
            return point
        else:
            direction = (v[0]/norm, v[1]/norm, v[2]/norm)

        # Scale direction by absolute value of cum_zoom
        dx, dy, dz = (zoom * d for d in direction)

        # Add scaled direction to original point to get new point
        x1, y1, z1 = x + dx, y + dy, z + dz

        # Return new point
        return (x1, y1, z1)