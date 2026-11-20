#!/usr/bin/env bash

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(dirname -- "$SCRIPT_DIR")"
cd "$WORKSPACE_ROOT" || exit 1

# 常规构建（3d_bbs 已加 COLCON_IGNORE，不参与构建，无需 CUDA/g++-10）
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release

# 若回环检测包(global_relocalization_kiss_matcher)的 kiss_matcher/robin/GTSAM 依赖未装好，可改为：
# colcon build --symlink-install --packages-skip global_relocalization_kiss_matcher --cmake-args -DCMAKE_BUILD_TYPE=Release
