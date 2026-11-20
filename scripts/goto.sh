#!/usr/bin/env bash

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(dirname -- "$SCRIPT_DIR")"
cd "$WORKSPACE_ROOT" || exit 1

# 极简走点控制器(订阅 /goal_pose,输出 /cmd_vel)
# 目标点用 RViz 的 "2D Goal Pose"(Fix Frame 选 odom)点一下,或用命令行发布:
#   ros2 topic pub /goal_pose geometry_msgs/msg/PoseStamped "{header: {frame_id: 'odom'}, pose: {position: {x: 3.0, y: 0.0}}}" --once

source install/setup.bash
ros2 launch goto_point goto_point.launch.py
