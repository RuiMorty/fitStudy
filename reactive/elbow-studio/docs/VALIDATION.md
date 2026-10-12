# 精细版实际运行验收

2026-10-10：最终精细版 **71 项通过**，浏览器运行/资源加载错误为 0。没有部署。

## 验证环境

本机 Chrome headless；桌面 1440 × 1050，移动 390 × 844、2 倍设备像素比及 Chrome 触控事件管线。移动端是视口/触控仿真，未完成实体手机和移动 Safari 验收。

## 实際通过的交互

- 17 个独立结构全部加载；逐项隔离后，真实画布网格都有命中区域且点击身份正确。
- 隐藏浅层后，桌面鼠标与手机触屏可以直接选择肱肌；隐藏对象不拦截射线。
- 展开至多个间距后复位，所有对象局部变换逐值恢复；保留当前角度。
- 0–120° 屈伸、端点反向播放、暂停、肌肉顶点形变、主动/被动角色文字通过。
- 角度滑块在 0 / 60 / 120° 的状态与截图一致。
- 筋膜独立显隐；单指旋转、双指缩放、鼠标旋转/滚轮均通过。
- 薄骨面使用双面显示，避免肩胛骨从特定方向看不见/不可点。
- 桌面、手机无水平溢出；包含「近」视角的肌肉/肌腱细节截图。

## 几何内部一致性

Blender 检查 0 / 30 / 60 / 90 / 120°。三组远端肌腱到所选骨性足印的最大距离为 **0.046 mm**；骨面起止点标记在采样角度均贴合对应模型骨面。该结果只表示模型内部一致性，不能视作真实人体的精度。

源数据库及派生模型仍存在局部交叠，主要涉及肌头汇合、深层接触和高角度运动区域。完整数值保留在 `qa/geometry-audit.json`，没有把样板标为全角度无碰撞或医学级准确。

## 性能与体量

GLB **23.3 MiB**，17 个网格，43 个节点；保留源网格细节、纹理与可编辑形态键。

| 本次无头浏览器短时播放 | 平均 FPS | 可见三角形 | Draw calls |
|---|---:|---:|---:|
| 桌面 | 25.2 | 99019 | 18 |
| 移动尺寸仿真 | 26.4 | 99019 | 18 |

这是本次机器和自动化环境的采样，不能推广到其他设备。暂停观察保留较高采样，播放降低像素采样并间隔更新阴影；仍需低端实体手机、长期运行和移动 Safari 性能验证。本轮优先保证精细模型的可行效果，没有用低模或静态视频代替交互。

## 演示截图

- [desktop-overview.png](../qa/desktop-overview.png)
- [desktop-brachialis.png](../qa/desktop-brachialis.png)
- [desktop-exploded.png](../qa/desktop-exploded.png)
- [desktop-detail.png](../qa/desktop-detail.png)
- [motion-0.png](../qa/motion-0.png)
- [motion-60.png](../qa/motion-60.png)
- [motion-120.png](../qa/motion-120.png)
- [mobile-brachialis.png](../qa/mobile-brachialis.png)
- [mobile-exploded.png](../qa/mobile-exploded.png)
- [mobile-overview.png](../qa/mobile-overview.png)
- [before-after.png](../qa/before-after.png)
