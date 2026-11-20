# 先验点云地图目录

把用于全局重定位 / 重定位的先验 PCD 地图放到本目录，例如：

```
pcd/
└── prior_map.pcd
```

然后在对应 launch 文件中把 `prior_pcd_file` 设为实际路径，例如：

- `src/registration/small_gicp_relocalization/launch/small_gicp_relocalization_launch.py`
- `src/registration/global_relocalization_kiss_matcher/launch/global_kiss_matcher_relocalization_launch.py`

默认值为占位符 `/path/to/your/prior_map.pcd`，使用前必须改成你实际保存的 PCD 文件路径。

保存 PCD 点云可用 PCL 工具，例如：

```bash
ros2 run pcl_ros pointcloud_to_pcd /input:=/cloud_registered
```

（`.pcd` 文件较大，`*.pcd` 已加入 `.gitignore`，不会提交到仓库。）
