# 第三方依赖安装指南（新设备）

`global_relocalization_kiss_matcher`（回环检测 / KISS-Matcher-SAM）需要三个**硬依赖**：`kiss_matcher`、`robin`、`GTSAM`。`small_gicp` 由 CMake `FetchContent` 自动拉取（需联网）。本文按顺序给出 Ubuntu 22.04 的完整安装步骤。

> 若暂时只跑「驱动 + FAST-LIO + 桥接」，可跳过本页，用
> `colcon build --packages-skip global_relocalization_kiss_matcher` 即可。

## 1. 系统依赖（apt）

```bash
sudo apt update
sudo apt install -y gcc g++ build-essential cmake git ninja-build \
    libeigen3-dev libflann-dev liblz4-dev libtbb-dev
```

- `libeigen3-dev` / `libflann-dev`：kiss_matcher 构建必需
- `liblz4-dev`：kiss_matcher 的 `find_library(lz4 REQUIRED)` 需要（官方 `make deps` 未包含，容易漏）
- `libtbb-dev`：本仓库 `global_relocalization_kiss_matcher` 的 `find_package(TBB REQUIRED)` 需要

## 2. GTSAM（位姿图优化）

GTSAM 不在 Ubuntu 默认源，用官方 PPA：

```bash
sudo add-apt-repository ppa:borglab/gtsam-release -y
sudo apt update
sudo apt install -y libgtsam-dev libgtsam-unstable-dev
```

> 若目标设备是 **arm64（如 Jetson Orin Nano / JetPack6）** 且 PPA 无对应架构的包，
> 需从源码编译 GTSAM（`git clone https://github.com/borglab/gtsam.git`，`cmake .. && make -j && sudo make install`）。

## 3. kiss_matcher + robin（关键：必须加 `-fPIC`）

```bash
git clone https://github.com/MIT-SPARK/KISS-Matcher.git
cd KISS-Matcher
cmake -B cpp/kiss_matcher/build cpp/kiss_matcher \
    -DCMAKE_BUILD_TYPE=Release \
    -DUSE_SYSTEM_ROBIN=OFF \
    -DCMAKE_POSITION_INDEPENDENT_CODE=ON
cmake --build cpp/kiss_matcher/build -j$(nproc)
sudo cmake --install cpp/kiss_matcher/build
sudo cmake --install cpp/kiss_matcher/build/_deps/robin-build   # 顺带安装 robin
```

**为什么必须加 `-DCMAKE_POSITION_INDEPENDENT_CODE=ON`**：

`kiss_matcher_core` 是**静态库**（`libkiss_matcher_core.a`），而本仓库的
`global_relocalization_kiss_matcher` 把它链接进 `SHARED` 动态库（`rclcpp_components` 组件）。
静态库不带 `-fPIC` 就会报：

```
relocation R_X86_64_PC32 against symbol ... can not be used when making a shared object; recompile with -fPIC
```

官方 `make cppinstall` 不会加这个标志，所以**不要直接用它**，用上面的 `cmake` 命令。

## 4. 代理（国内 / 走 Clash）

`FetchContent` 拉取 `small_gicp`（以及 robin/TBB 若走 FetchContent）需访问 GitHub。WSL2 下指向宿主机 Clash 网关：

```bash
export https_proxy=http://$(ip route show default | awk '{print $3}'):7897
export http_proxy=http://$(ip route show default | awk '{print $3}'):7897
```

（Clash 端口 7897。）

## 5. 验证

```bash
ls /usr/local/lib/libkiss_matcher_core.a        # kiss_matcher 核心库
ls /usr/local/lib/cmake/robin/ 2>/dev/null       # robin 的 CMake 配置
dpkg -l | grep -E "gtsam|tbb|lz4|flann"          # 确认 apt 库已装
```

## 6. 回到工作空间构建

```bash
cd Lidar_SLAM_ws
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
```
