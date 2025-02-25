#!/usr/bin/env python3

# ROS python API
import rospy
# Joy message structure
#from sensor_msgs.msg import Joy
# 3D point & Stamped Pose msgs
from geometry_msgs.msg import Point, PoseStamped
# import all mavros messages and services
from mavros_msgs.msg import State, PositionTarget
from mavros_msgs.srv import CommandBool, SetMode

# Flight modes class
# Flight modes are activated using ROS services


class fcuModes:
    def __init__(self):
        pass

    def setArm(self):
        rospy.wait_for_service('mavros/cmd/arming')
        try:
            armService = rospy.ServiceProxy('mavros/cmd/arming', CommandBool)
            armService(True)
        except rospy.ServiceException as e:
            print("Service arming call failed: %s" % e)

    def setDisarm(self):
        rospy.wait_for_service('mavros/cmd/arming')
        try:
            armService = rospy.ServiceProxy('mavros/cmd/arming', CommandBool)
            armService(False)
        except rospy.ServiceException as e:
            print("Service disarming call failed: %s" % e)

    def setStabilizedMode(self):
        rospy.wait_for_service('mavros/set_mode')
        try:
            flightModeService = rospy.ServiceProxy('mavros/set_mode', SetMode)
            flightModeService(custom_mode='STABILIZED')
        except rospy.ServiceException as e:
            print("service set_mode call failed: %s. Stabilized Mode could not be set." % e)

    def setOffboardMode(self):
        rospy.wait_for_service('mavros/set_mode')
        try:
            flightModeService = rospy.ServiceProxy('mavros/set_mode', SetMode)
            flightModeService(custom_mode='OFFBOARD')
        except rospy.ServiceException as e:
            print("service set_mode call failed: %s. Offboard Mode could not be set." % e)

    def setAltitudeMode(self):
        rospy.wait_for_service('mavros/set_mode')
        try:
            flightModeService = rospy.ServiceProxy('mavros/set_mode', SetMode)
            flightModeService(custom_mode='ALTCTL')
        except rospy.ServiceException as e:
            print("service set_mode call failed: %s. Altitude Mode could not be set." % e)

    def setPositionMode(self):
        rospy.wait_for_service('mavros/set_mode')
        try:
            flightModeService = rospy.ServiceProxy('mavros/set_mode', SetMode)
            flightModeService(custom_mode='POSCTL')
        except rospy.ServiceException as e:
            print("service set_mode call failed: %s. Position Mode could not be set." % e)

    def setAutoLandMode(self):
        rospy.wait_for_service('mavros/set_mode')
        try:
            flightModeService = rospy.ServiceProxy('mavros/set_mode', SetMode)
            flightModeService(custom_mode='AUTO.LAND')
        except rospy.ServiceException as e:
            print("service set_mode call failed: %s. Autoland Mode could not be set." % e)


class Controller:
    ''' Main class: Converts joystick commands to position setpoints '''
    # initialization method

    def __init__(self):
        # Drone state
        self.state = State()
        # Instantiate a setpoints message
        self.setpoint_target = PositionTarget()
        # set the flag to use position setpoints and yaw angle
        self.setpoint_target.type_mask = int('010111111000', 2)
        # LOCAL_NED
        self.setpoint_target.coordinate_frame = 1

        # We will fly at a fixed altitude for now
        # Altitude setpoint, [meters]
        self.ALT_SP = rospy.get_param('alt_sp', 1.0)
        # update the setpoint message with the required altitude
        self.setpoint_target.position.z = self.ALT_SP

        # Instantiate a joystick message
        #self.joy_msg        = Joy()
        # initialize
        #self.joy_msg.axes=[0.0, 0.0, 0.0]

        # Step size for position update
        #self.STEP_SIZE = rospy.get_param('joy_step_scale',2.0)

        # Fence. We will assume a square fence for now
        #self.FENCE_LIMIT = 5.0

        # A Message for the current local position of the drone
        self.local_pos = Point(0.0, 0.0, 0.0)

    # Callbacks

    # local position callback
    def posCb(self, msg):
        self.local_pos.x = msg.pose.position.x
        self.local_pos.y = msg.pose.position.y
        self.local_pos.z = msg.pose.position.z

    # joystick callback
    # def joyCb(self, msg):
    #     self.joy_msg = msg

    # Drone State callback
    def stateCb(self, msg):
        self.state = msg

    # Update setpoint message
#    def updateSp(self):
#        x = -1.0*self.joy_msg.axes[0]
#        y = self.joy_msg.axes[1]

#        self.sp.position.x = self.local_pos.x + self.STEP_SIZE*x
#        self.sp.position.y = self.local_pos.y + self.STEP_SIZE*y

# Main function
# takes of in offboard mode at current positin to  self.ALT_SP altitude, specified in the takeoff_test_params.yaml


def start():

    # initiate node
    rospy.init_node('takeoff_offboard_test_node', anonymous=True)
    rospy.logindo("init node created")

    modes = fcuModes()
    # flight mode object
    #modes = fcuModes()
    # controller object
    cnt = Controller()

    # ROS loop rate, [Hz]
    rate = rospy.Rate(20.0)

    # Subscribe to drone state
    rospy.Subscriber('mavros/state', State, cnt.stateCb)
    rospy.loginfo("subscribed to state")

    # Subscribe to drone's local position
    rospy.Subscriber('mavros/local_position/pose', PoseStamped, cnt.posCb)
    rospy.loginfo("subscribed to local_position/pose")
    # subscribe to joystick topic
    #rospy.Subscriber('joy', Joy, cnt.joyCb)

    # Setpoint publisher
    sp_pub = rospy.Publisher('mavros/setpoint_raw/local', PositionTarget, queue_size=1)

    # Make sure the drone is armed
    while not cnt.state.armed:
        modes.setArm()
        rate.sleep()

    # collect few measurements of the current position
    # will be used to determine the x,y home position, assuming that drone is not airborn
    k = 0
    while k < 10:
        cnt.setpoint_target.position.x = cnt.local_pos.x
        cnt.setpoint_target.position.y = cnt.local_pos.y
        cnt.setpoint_target.position.z = cnt.ALT_SP
        rate.sleep()
        k += 1

    # ROS main loop
    while not rospy.is_shutdown():
        sp_pub.publish(cnt.setpoint_target)
        rate.sleep()


if __name__ == '__main__':
    print("entering main")
    start()
    # try:
    #     main()
    # except rospy.ROSInterruptException:
    #     pass
