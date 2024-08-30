cmake_minimum_required(VERSION 3.8)
project(amiga_mux)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(twist_mux REQUIRED)



install(
  DIRECTORY launch config
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
