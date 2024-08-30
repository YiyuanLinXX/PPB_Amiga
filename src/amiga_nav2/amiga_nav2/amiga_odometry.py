import rclpy
from rclpy.node import Node

from nav_msgs.msg import Odometry
import serial
from geometry_msgs.msg import Twist

class OdometryPublisher(Node):

    def __init__(self):
        super().__init__('odometry')
        self.publisher_ = self.create_publisher(Odometry, 'odom', 10)
        timer_period = 0.1  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.i = 0
        self.ser = serial.Serial('/dev/serial/by-id/usb-Adafruit_Industries_LLC_Feather_M4_CAN_F6FF0DE648364C53202020542C1B0DFF-if00')
        self.subscription = self.create_subscription(
            Twist,
            'cmd_vel_out',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning
    
    def listener_callback(self, msg):
        #twist_str = str(msg.linear.x) + "," + str(msg.angular.z)
        #self.ser.write(twist_str.encode('ascii'))
        twi = (str(msg.linear.x) + "," + str(msg.angular.z)).encode()
        self.ser.write(twi)
        self.get_logger().info('Sending: "%s"' % twi)
        
    def timer_callback(self):
        latest_line = None

        # Read all available data from the serial port
        try:
            while self.ser.in_waiting > 0:
                latest_line = self.ser.readline().decode().strip()

            # If we got some data, publish it
            if latest_line:
                msg = Odometry()
                twi = list(map(float, latest_line.strip('"').split()))
                msg.twist.twist.linear.x = twi[0]
                msg.twist.twist.angular.z = twi[1]
                msg.child_frame_id = 'base_link'

                msg.header.frame_id = 'odom'
                msg.header.stamp = self.get_clock().now().to_msg()

                msg.pose.pose.position.x = 0.0
                msg.pose.pose.position.y = 0.0
                msg.pose.pose.position.z = 0.0
                msg.pose.pose.orientation.x = 0.0
                msg.pose.pose.orientation.y = 0.0
                msg.pose.pose.orientation.z = 0.0

                self.publisher_.publish(msg)
                self.get_logger().info(f'Published Odom: {twi}')
        except Exception as e:

            self.get_logger().info('Bad Line: ' + str(e))
            pass

def main(args=None):
    rclpy.init(args=args)

    odom_publisher = OdometryPublisher()

    rclpy.spin(odom_publisher)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    odom_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
