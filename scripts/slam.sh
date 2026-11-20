#!/usr/bin/env bash

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(dirname -- "$SCRIPT_DIR")"
cd "$WORKSPACE_ROOT" || exit 1

# KISS-Matcher-SAM：回环检测 + 位姿图优化（订阅 FAST-LIO 的 /Odometry 与 /cloud_registered）
source install/setup.bash

ros2 launch global_relocalization_kiss_matcher run_kiss_matcher_sam.launch.yaml \
    odom_topic:=/Odometry \
    scan_topic:=/cloud_registered
