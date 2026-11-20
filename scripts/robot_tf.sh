#!/usr/bin/env bash

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(dirname -- "$SCRIPT_DIR")"
cd "$WORKSPACE_ROOT" || exit 1

# 桥接节点(lio_interface / sensor_scan_generation)所需的静态 TF:
#   base_footprint → livox_frame(雷达在车体上的安装外参)
# 原仓库由 URDF(robot_state_publisher)发布,本仓库已移除 URDF,故用 static_transform_publisher 补齐。
#
# ⚠️ 把下面 6 个数改成你实际的外参(单位:m / rad):
#   X Y Z          雷达(Mid360)相对 base_footprint 的位置
#   YAW PITCH ROLL 雷达相对 base_footprint 的姿态(欧拉角 yaw-pitch-roll,rad)
#
# 下面是占位值(全 0,表示雷达就装在 base_footprint 原点),请按实车改:
X=0.0
Y=0.0
Z=0.0
YAW=0.0
PITCH=0.0
ROLL=0.0

source install/setup.bash
ros2 run tf2_ros static_transform_publisher \
    "$X" "$Y" "$Z" "$YAW" "$PITCH" "$ROLL" \
    base_footprint livox_frame
