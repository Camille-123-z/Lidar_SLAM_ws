import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('goto_point')
    params = os.path.join(pkg_share, 'config', 'goto_point.yaml')

    node = Node(
        package='goto_point',
        executable='goto_point_node',
        name='goto_point',
        output='screen',
        parameters=[params],
    )

    return LaunchDescription([node])
