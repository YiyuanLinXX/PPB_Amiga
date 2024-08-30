import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
import serial


class CANBusHandler(Node):

    def __init__(self):
        super().__init__('canbus_handler')
        self.subscription = self.create_subscription(
            Twist,
            'cmd_vel_nav',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning

        self.ser = serial.Serial('/dev/serial/by-id/usb-Adafruit_Industries_LLC_Feather_M4_CAN_9378F5F848364C53202020540C2A0DFF-if00', 115200)

    def listener_callback(self, msg):
        #twist_str = str(msg.linear.x) + "," + str(msg.angular.z)
        #self.ser.write(twist_str.encode('ascii'))
        twi = (str(msg.linear.x) + "," + str(msg.angular.z)).encode()
        self.ser.write(twi)
        self.get_logger().info('Sending: "%s"' % twi)

def main(args=None):
    rclpy.init(args=args)

    handler = CANBusHandler()

    rclpy.spin(handler)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    handler.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()