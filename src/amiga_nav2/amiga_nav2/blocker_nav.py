import rclpy
import os
import math
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool
from std_srvs.srv import Trigger, SetBool
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix
from geopy.distance import geodesic as GD

class BlockerNav(Node):
    def __init__(self):
        super().__init__('blocker_nav')
        self.get_logger().info("started blocker nav")

        
        #SUBSCRIBERS
        self.fix_sub = self.create_subscription(NavSatFix, '/gps/odin', self.fix_callback, 1)
        self.amiga_sub = self.create_subscription(NavSatFix, '/gps/fix', self.amiga_callback, 1)

        #PUBLISHERS
        self.twist_pub = self.create_publisher(Twist, 'cmd_vel_blocker', 1)

        self.amiga_location = 0.0
        self.thorvald_location = 0.0

        self.thorvald_lat = 0.0
        self.thorvald_long = 0.0

        self.amiga_lat = 0.0
        self.amiga_long = 0.0

        self.next = False
        self.next2 = False
        # while rclpy.ok():
        #     self.measure()
        #     rclpy.spin()
    

    
    def fix_callback(self, msg):
        self.thorvald_lat = msg.latitude
        self.thorvald_long = msg.longitude
        self.next = True
        self.measure()
        # thorvald_long = thorvald_long * 111.32 * 1000
        # thorvald_lat = thorvald_lat *  111.32 * 1000
        # self.thorvald_location = math.sqrt(pow(thorvald_lat,2) + pow(thorvald_long,2))

    def amiga_callback(self, msg):
        self.amiga_lat = msg.latitude
        self.amiga_long = msg.longitude
        self.next2 = True
        self.measure()
        # amiga_long = amiga_long * 111.32 * 1000
        # amiga_lat = amiga_lat *  111.32 * 1000
        # self.amiga_location = math.sqrt(pow(amiga_lat,2) + pow(amiga_long,2))

    def measure(self):
        if self.next and self.next2:
            distance = GD((self.amiga_lat, self.amiga_long), (self.thorvald_lat, self.thorvald_long)).meters
            self.get_logger().info(f"{distance}")
            if distance < 5:
                twist_msg = Twist()

                twist_msg.linear.x = 0.0
                twist_msg.linear.y = 0.0
                twist_msg.linear.z = 0.0
            
                twist_msg.angular.x = 0.0
                twist_msg.angular.y = 0.0
                twist_msg.angular.z = 0.0

                self.twist_pub.publish(twist_msg)
                self.next = False
                self.next2 = False






        
def main(args=None):
    rclpy.init(args=args)
    node = BlockerNav()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()