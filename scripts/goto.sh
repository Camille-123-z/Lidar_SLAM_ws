#!/usr/bin/env bash

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(dirname -- "$SCRIPT_DIR")"
cd "$WORKSPACE_ROOT" || exit 1

# 极简走点(从启动区到目标点):驱动 + FAST-LIO + goto_point,不用 Nav2、不用桥接。
# 目标点给在 FAST-LIO 世界帧 camera_init(启动点≈原点,+X≈初始朝向):
#   ros2 topic pub /goal_pose geometry_msgs/msg/PoseStamped \
#     "{header: {frame_id: 'camera_init'}, pose: {position: {x: 3.0, y: 0.0}}}" --once
# 或用 RViz(Fixed Frame 选 camera_init)"2D Goal Pose"点一下。

# 1. Livox MID-360 驱动(PointCloud2 格式)
gnome-terminal --title="Livox MID-360 驱动" -- bash -c "
source install/setup.bash;
ros2 launch livox_ros_driver2 fast_lio_msg_MID360_launch.py"

# 2. FAST-LIO 里程计(发布 /Odometry + camera_init→body TF)
gnome-terminal --title="FAST-LIO 里程计" -- bash -c "
source install/setup.bash;
ros2 launch fast_lio mapping.launch.py"

# 3. 走点控制器(订阅 /goal_pose,输出 /cmd_vel)
gnome-terminal --title="goto_point 走点" -- bash -c "
source install/setup.bash;
ros2 launch goto_point goto_point.launch.py"
