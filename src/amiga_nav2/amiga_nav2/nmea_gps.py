import amiga_nav2.utils.gps_utils as gps_utils

import serial
import pynmea2

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import NavSatFix
from sensor_msgs.msg import Imu

GPS_PORT = '/dev/serial/by-id/usb-Emlid_ReachRS3_8243ABB34D7B2976-if02'



def read_gps_data(serial_port):
    with serial.Serial(serial_port, 38400, timeout=1) as ser:
        line = ser.readline().decode('utf-8').strip()
        if line.startswith('$GP') or line.startswith('$GN'):
            try:
                msg = pynmea2.parse(line)
                if isinstance(msg, pynmea2.types.talker.GGA):
                    latitude = msg.latitude
                    longitude = msg.longitude
                    heading = 0.0
                elif isinstance(msg, pynmea2.types.talker.VTG):
                    heading = msg.true_track
                elif isinstance(msg, pynmea2.types.talker.GLL):
                    latitude = msg.latitude
                    longitude = msg.longitude
                    heading = 0.0
                elif isinstance(msg, pynmea2.types.talker.RMC):
                    latitude = msg.latitude
                    longitude = msg.longitude
                    heading = msg.true_course
                elif isinstance(msg, pynmea2.types.talker.GNS):
                    latitude = msg.latitude
                    longitude = msg.longitude
                    heading = msg.true_track
                return [latitude, longitude, heading]
            except pynmea2.ParseError as e:
                print(f"Parse error: {e}")
            except:
                print(f'GPS: Bad line')

class GPS(Node):

    def __init__(self):
        super().__init__('gps')
        self.get_logger().info('Launching GPS Module')

        self.publisher_gps = self.create_publisher(NavSatFix, 'gps/fix', 10)
        self.publisher_imu = self.create_publisher(Imu, 'imu', 10)

        # try:
        #     self.gps_port = serial.Serial('/dev/ttyACM0', 38400, timeout=1)
        # except:
        #     self.gps_port = serial.Serial('/dev/ttyACM1', 38400, timeout=1)
        self.gps_port = serial.Serial(GPS_PORT, 38400, timeout=1)
        self.latitude = None
        self.longitude = None
        self.heading = 0.0

        timer_period = 0.5  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)

    def get_gps(self):
        line = self.gps_port.readline().decode('utf-8').strip()
        if line.startswith('$GPGGA'):
            try:
                msg = pynmea2.parse(line)
                if isinstance(msg, pynmea2.types.talker.GGA):
                    self.latitude = msg.latitude
                    self.longitude = msg.longitude
            except pynmea2.ParseError as e:
                print(f"Parse error: {e}")
        elif line.startswith('$GPETC'):
            try:
                msg = line.split(',')
                self.heading = float(msg[4])
            except pynmea2.ParseError as e:
                print(f"Parse error: {e}")
            except:
                print(f"Empty Value")


    def timer_callback(self):
        gps_msg = NavSatFix()
        imu_msg = Imu()

        gps_msg.header.frame_id = 'gps'
        gps_msg.header.stamp = self.get_clock().now().to_msg()

        imu_msg.header.frame_id = 'imu'
        imu_msg.header.stamp = self.get_clock().now().to_msg()
   

        self.get_gps()
        gp = [self.latitude, self.longitude, self.heading]
        gps_msg.position_covariance_type = 0
       # latitude,longitude,heading = gp[0], gp[1], gp[2]
        gps_msg.latitude = gp[0]
        gps_msg.longitude = gp[1]

        imu_msg.orientation = gps_utils.quaternion_from_euler(gp[2], 0 ,0)
        
        self.publisher_gps.publish(gps_msg)
        self.publisher_imu.publish(imu_msg)
        self.get_logger().info('Publishing: "%s"' % str(gp[0]) + ',' + str(gp[1]) + ',' + str(gp[2]))

    # #Convert current gps data to meters relative to the origin
    # def convert_to_meters(self,gps):
    #     # Define the projection (WGS84 to UTM)
    #     wgs84 = pyproj.Proj(proj='latlong', datum='WGS84')
    #     utm = pyproj.Proj(proj='utm', zone=18, datum='WGS84')  # Change zone according to your location
        
    #     # Convert the first waypoint to UTM and set as origin
    #     origin_x, origin_y = self.origin.pose.position.x, self.origin.pose.position.y
        
    #     x,y = gps.pose.position.x, gps.pose.position.y
    #     x_m, y_m = pyproj.transform(wgs84, utm, x, y)
    #     relative_x = x_m - origin_x
    #     relative_y = y_m - origin_y
    #     relative_pos = (relative_x, relative_y)        
    #     return relative_pos


def main(args=None):
    rclpy.init(args=args)
    gps = GPS()
    rclpy.spin(gps)
    gps.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()