# Lidar_SLAM_ws

基于 ROS 2 的 3D LiDAR SLAM 工作空间：**Livox MID-360 + FAST-LIO + KISS-Matcher-SAM(回环检测 + 位姿图)**，不含 Nav2。

[![ROS2](https://img.shields.io/badge/ROS2-Humble-22313F?logo=ros)](https://docs.ros.org/en/humble/)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-22.04-E95420?logo=ubuntu)](https://releases.ubuntu.com/22.04/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)

本仓库是从 [Ikunio/Lidar_nav2_ws](https://github.com/Ikunio/Lidar_nav2_ws) 精简而来，**只保留** LiDAR 驱动、LIO 里程计、回环检测 / 重定位与桥接节点，**移除了 Nav2、SLAM Toolbox、Gazebo 仿真、URDF 描述、遥控等导航相关部分**。

## 核心管线

```
Livox MID-360 驱动 (livox_ros_driver2)
        │  /livox/lidar (PointCloud2) + /livox/imu
        ▼
FAST-LIO (fast_lio)
        │  /cloud_registered (PointCloud2) + /Odometry (Odometry)
        ├──────────────────────────────┐
        ▼                              ▼
lio_interface (TF 桥接)          KISS-Matcher-SAM (global_relocalization_kiss_matcher)
        │  /registered_scan              回环检测 + 位姿图优化 → map 帧
        │  /registered_odometry
        ▼
sensor_scan_generation (桥接)
        │  /odom + /lidar_frame_pcd + odom→base_footprint TF
```

TF 坐标树：`map → odom → base_footprint → chassis → livox_frame`

> 走点（`goto_point`）走更短的链路：`camera_init → body`（FAST-LIO 直接发布），不依赖 `map/odom/base_footprint`。

## 包含的功能包

| 分类 | 包 | 说明 |
|------|-----|------|
| 传感器驱动 | `livox_ros_driver2` | Livox MID-360 驱动，发布 PointCloud2 / CustomMsg + IMU（已内置预编译 Livox-SDK2） |
| LIO 里程计 | `localization/FAST_LIO` | FAST-LIO2，基于 ikd-Tree 的紧耦合 LiDAR-IMU 里程计 |
| 回环检测 / 位姿图 | `registration/global_relocalization_kiss_matcher` | **KISS-Matcher-SAM**：`kiss_matcher_sam` 节点实现回环检测(`loop_detector`)+ 回环约束(`loop_closure`)+ 位姿图优化(`pose_graph_manager`)，并含全局重定位节点 |
| 配准 / 重定位 | `registration/small_gicp_relocalization` | 已知大致初值的 small_gicp 连续重定位跟踪 |
| 配准 / 重定位 | `registration/global_small_gicp_relocalization` | small_gicp 全局重定位 |
| 配准 / 重定位 | `registration/global_relocalization` | 全局重定位（small_gicp 版） |
| 配准 / 重定位 | `registration/icp_registration` | 基于 PCL ICP 的重定位 |
| 全局定位（独立库） | `registration/3d_bbs` | 3D-BBS 全局定位（**非 colcon 包**，已加 `COLCON_IGNORE`，可选手动构建） |
| 桥接节点 | `lio_interface` | LIO 内部坐标系 → 标准 odom 的 TF 桥接，转发 `/registered_scan` `/registered_odometry` |
| 桥接节点 | `sensor_scan_generation` | 发布 `/odom` `/lidar_frame_pcd` 及 `odom→base_footprint` TF |
| 走点导航 | `goto_point` | 极简点到点控制器：订阅 `/goal_pose`，输出 `/cmd_vel`（不用 Nav2） |

## 环境要求

- **操作系统**：Ubuntu 22.04
- **ROS 2**：Humble Hawksbill
- **Livox-SDK2**：已内置（`src/livox_ros_driver2/Livox-SDK2/`，amd64/arm64 预编译 `.so`）

### 第三方依赖

| 依赖 | 获取方式 | 用途 |
|------|----------|------|
| PCL / Eigen / OpenMP / TBB | `apt`（`libpcl-dev` `libeigen3-dev` `libtbb-dev`） | 点云、数学、并行 |
| `small_gicp` | CMake `FetchContent` 自动拉取（需联网） | GICP 配准 |
| `kiss_matcher`（`kiss_matcher::kiss_matcher_core`） | 需手动安装，见 [MIT-SPARK/KISS-Matcher](https://github.com/MIT-SPARK/KISS-Matcher) | 全局点云配准 |
| `robin`（robin_hood） | 需手动安装 | 哈希表 |
| `GTSAM`（`libgtsam`） | `apt install libgtsam-dev` 或源码安装 | 位姿图优化 |

> `kiss_matcher`、`robin`、`GTSAM` 是 `global_relocalization_kiss_matcher`（回环检测）的硬依赖；若暂时只跑「驱动 + FAST-LIO + 桥接」，可先跳过该包的构建（`colcon build --packages-skip global_relocalization_kiss_matcher`）。
>
> 完整安装步骤见 **[docs/dependencies.md](docs/dependencies.md)**（注意 kiss_matcher 静态库必须加 `-fPIC` 编译）。

## 构建

```bash
source /opt/ros/humble/setup.bash
cd scripts
./build.sh
```

或等价地：

```bash
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
```

> 如需跳过回环检测包：`colcon build --symlink-install --packages-skip global_relocalization_kiss_matcher --cmake-args -DCMAKE_BUILD_TYPE=Release`

## 快速开始（实机）

### 1. 启动驱动 + LIO 里程计 + 桥接

```bash
source install/setup.bash
cd scripts
./mapping_real.sh
```

该脚本依次启动：

0. `robot_tf` → `scripts/robot_tf.sh`（静态 TF `base_footprint → livox_frame`，**请先改成你的雷达安装外参**）
1. `livox_ros_driver2` → `fast_lio_msg_MID360_launch.py`（MID-360 驱动，PointCloud2 格式）
2. `fast_lio` → `mapping.launch.py`（FAST-LIO 里程计）
3. `lio_interface` → `fastlio_lio_interface_launch.py`（TF 桥接）
4. `sensor_scan_generation` → `sensor_scan_generation_launch.py`（odom / 扫描转发）

> ⚠️ 原仓库的 `base_footprint → livox_frame` 静态 TF 由 URDF（`robot_state_publisher`）发布，本仓库已移除 URDF，故桥接节点会查不到该 TF。请先编辑 `scripts/robot_tf.sh`，把雷达相对 `base_footprint` 的安装外参（x/y/z/yaw/pitch/roll）填进去。

### 2. 启动回环检测 + 位姿图（KISS-Matcher-SAM）

另开一个终端：

```bash
source install/setup.bash
cd scripts
./slam.sh
```

等价命令：

```bash
ros2 launch global_relocalization_kiss_matcher run_kiss_matcher_sam.launch.yaml \
    odom_topic:=/Odometry scan_topic:=/cloud_registered
```

回环检测参数在 `src/registration/global_relocalization_kiss_matcher/config/slam_config.yaml`（`loop_detection_radius`、`keyframe_threshold`、`voxel_resolution` 等，按环境调整）。

### 3. 点到点走位（从启动区到目标点）

`goto_point` 用 LiDAR 定位做闭环，输出 `/cmd_vel` 走到目标点，**不依赖 Nav2，也不依赖桥接节点**。

**极简走位（推荐，一条命令）**：只跑「驱动 + FAST-LIO + goto_point」，目标点给在 FAST-LIO 的世界帧 `camera_init`（启动点 ≈ 原点，+X ≈ 初始朝向）：

```bash
cd scripts
./goto.sh
```

然后给目标点（二选一）：

- **RViz**：Fixed Frame 选 `camera_init`，用工具栏 **"2D Goal Pose"** 点一下；
- **命令行**：

```bash
ros2 topic pub /goal_pose geometry_msgs/msg/PoseStamped \
  "{header: {frame_id: 'camera_init'}, pose: {position: {x: 3.0, y: 0.0}}}" --once
```

`goto_point` 用 FAST-LIO 发布的 TF `camera_init → body` 拿当前位姿，算误差后发 `/cmd_vel`。速度、容差等参数在 `src/goto_point/config/goto_point.yaml`。

> 想用完整桥接路径（`odom` / `base_footprint` 帧）？先跑 `./mapping_real.sh`（含静态 TF），再把 `goto_point.yaml` 的 `default_goal_frame` 改成 `odom`、`base_frame` 改成 `base_footprint`，目标点 `frame_id` 也填 `odom`。

> `goto_point` 输出 `/cmd_vel`（Twist）；若你的底盘走串口下位机，需把 `/cmd_vel` 接到一个串口桥（可参考 robocon-fsm 的 `robot_serial` 思路）。

### 3. 全局重定位 / 重定位

使用前先把先验 PCD 地图放到 `pcd/` 目录，并在对应 launch 文件里把 `prior_pcd_file` 设为实际路径（默认值为占位符 `/path/to/your/prior_map.pcd`）。

- 已知大致初值：`ros2 launch small_gicp_relocalization small_gicp_relocalization_launch.py`
- 无初值全局重定位：`ros2 launch global_relocalization_kiss_matcher global_kiss_matcher_relocalization_launch.py`

> 同一时刻只能有一个节点发布 `map → odom`，请勿同时启动多个重定位节点。

## ROS 2 话题

| 话题 | 类型 | 发布者 |
|------|------|--------|
| `/livox/lidar` | PointCloud2 / CustomMsg | livox_ros_driver2 |
| `/livox/imu` | sensor_msgs/Imu | livox_ros_driver2 |
| `/cloud_registered` | PointCloud2 | fast_lio |
| `/Odometry` | nav_msgs/Odometry | fast_lio |
| `/registered_scan` | PointCloud2 | lio_interface |
| `/registered_odometry` | nav_msgs/Odometry | lio_interface |
| `/odom` | nav_msgs/Odometry | sensor_scan_generation |
| `/lidar_frame_pcd` | PointCloud2 | sensor_scan_generation |

## 与原仓库 `Lidar_nav2_ws` 的差异

- ✅ 保留：`livox_ros_driver2`、`FAST_LIO`、`lio_interface`、`sensor_scan_generation`、整个 `registration/` 目录
- ❌ 移除：`me_nav2_bringup`（Nav2）、`point_lio`、`Sophus`（point_lio 依赖）、`rtabmap`/`rtabmap_ros`、`pcd2pgm-master`、`gui_teleop`、`get_urdf`、`gld_robot_description`、`livox_laser_simulation_RO2`、`ign_sim_pointcloud_tool`、空的 `registration/KISS-Matcher` 占位目录
- 🔧 修复：把指向 `me_nav2_bringup/pcd` 的硬编码 `prior_pcd_file` 改成占位符；把 `run_kiss_matcher_sam.launch.yaml` 等启动文件里指向外部包 `kiss_matcher_ros` 的引用改回本地包 `global_relocalization_kiss_matcher`
- 🚫 `registration/3d_bbs` 为独立 C++ 库（非 colcon 包），已加 `COLCON_IGNORE` 不参与构建

## 致谢

- [FAST-LIO2](https://github.com/hku-mars/FAST_LIO)
- [KISS-Matcher](https://github.com/MIT-SPARK/KISS-Matcher) / KISS-Matcher-SAM
- [small_gicp](https://github.com/koide3/small_gicp)
- [3D-BBS](https://arxiv.org/abs/2310.10023)
- [Livox-SDK2](https://github.com/Livox-SDK/Livox-SDK2)

## 许可证

[MIT License](./LICENSE)
