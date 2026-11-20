#!/usr/bin/env bash

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(dirname -- "$SCRIPT_DIR")"
cd "$WORKSPACE_ROOT" || exit 1

# 实机：驱动 + FAST-LIO + 桥接（里程计/建图）
# 回环检测请另开终端运行 ./slam.sh

# 1. Livox MID-360 驱动（PointCloud2 格式，供 FAST-LIO 使用）
gnome-terminal --title="Livox MID-360 驱动" -- bash -c "
source install/setup.bash;
ros2 launch livox_ros_driver2 fast_lio_msg_MID360_launch.py"

# 2. FAST-LIO 里程计
gnome-terminal --title="FAST-LIO 里程计" -- bash -c "
source install/setup.bash;
ros2 launch fast_lio mapping.launch.py"

# 3. lio_interface：LIO 内参坐标系 → 标准 odom（转发 /registered_scan /registered_odometry）
gnome-terminal --title="lio_interface 桥接" -- bash -c "
source install/setup.bash;
ros2 launch lio_interface fastlio_lio_interface_launch.py"

# 4. sensor_scan_generation：发布 /odom /lidar_frame_pcd 与 odom→base_footprint TF
gnome-terminal --title="sensor_scan_generation 桥接" -- bash -c "
source install/setup.bash;
ros2 launch sensor_scan_generation sensor_scan_generation_launch.py"
