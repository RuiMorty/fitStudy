# ELBOW / 01 — 肘部运动解剖实验室

一个真实可操作的右侧肘部 WebGL 样板。17 个独立对象来自同一份可编辑 Blender 模型；网页加载本地 GLB，并使用其中的动画曲线与形态键。不依赖在线 CDN、不调用生成服务、不部署。

## 启动

需要 Python 3 与支持 WebGL 2 的现代浏览器。进入本目录：

```bash
cd /Users/agiuser/Documents/fit/reactive/elbow-lab
python3 -m http.server 8766 --bind 127.0.0.1
```

打开 <http://127.0.0.1:8766>。也可以运行 `npm start`（无需安装 npm 依赖）。若端口被占用，改用其他空闲端口。不要直接双击 HTML 使用 `file://`；浏览器会阻止本地模型读取。服务仅绑定本机，没有公网发布。

## 三条验收路径

1. 点击「看见深层肱肌」，浅层与筋膜会隐藏。直接点击画布中的肱肌，查看起止点。也可在索引中选择或搜索任何结构，按「单块隔离」观察。
2. 拖动「结构间距」到 100%，查看结构与附着关系虚线。点击「准确复位」，所有网格回到同一关节角度下的原始变换。复位只恢复间距，保留角度、视角与显隐选择。
3. 点击播放，或拖动角度到 0–120°。观察尺桡骨刚性绕轴运动，以及二头肌、肱肌和三头肌的长度与外形变化。播放时颜色与文字按指定情境区分主动参与与被动拉长。

鼠标拖动旋转、滚轮缩放；手机触控使用单指旋转、双指缩放。前 / 侧 / 后提供固定观察方向。筋膜是单独可选择、可隐藏的透明示意对象。开启筋膜时可点中其外壳；查看内部结构时先关闭筋膜。

## 文件

- `assets/elbow-right.blend`：可编辑源文件，Blender 5.2.1 创建；含集合、17 个结构对象、12 个骨性起止点标记、肘轴控制对象、形态键和时间线动画。
- `assets/elbow-right.glb`：网页实际加载的模型，标准 glTF 2.0 / Y-up / 米，包含刚性旋转与肌肉、肌腱形变动画。
- `data/structures.json`：稳定 ID、中英文名、层次、所属骨骼、起止点、参考来源、展开偏移、已知精度边界及投影后的附着坐标。
- `data/geometry-stats.json`：肌肉与肌腱的样板路径长度；不能当作真实人体测量。
- `docs/STRUCTURES.md`：建模前建立的结构清单、范围与参考资料。
- `docs/MODEL-REVIEW.md`：解剖审核待确认项、实现限制与扩展工作量。
- `docs/VALIDATION.md`：本次实际运行验证、截图索引和性能测量边界。
- `index.html`、`src/`：独立网页源码。`vendor/`：Three.js 0.180.0 与 MIT 许可副本。
- `blender/define_structures.py`、`blender/build_elbow.py`、`blender/audit_geometry.py`：可复现的清单、建模与表面检查脚本。
- `qa/verify.cjs`、`qa/verification.json`：浏览器交互检查及实测结果。

## 编辑 / 重建模型

在 Blender 打开 `.blend` 后，时间线 **1–121 帧对应 0–120°**。`joint_elbow_R` 控制尺桡骨运动，肌肉和肌腱通过 `Flex_005` 至 `Flex_120` 的形态键变化。所有形状可编辑。对象 ID 与 JSON 对应，不要随意重命名。

从源码重建：

```bash
python3 blender/define_structures.py
blender -b --python blender/build_elbow.py
blender -b --python blender/audit_geometry.py
```

这会覆盖**本样板目录中的**生成模型及数据；先另存人工修改过的 `.blend`。Blender 不同版本的节点和 glTF 导出行为可能不同，本次实际使用 5.2.1。

浏览器测试需要 Node.js、Playwright 和本机 Chrome：

```bash
PLAYWRIGHT_MODULE=/path/to/node_modules/playwright node qa/verify.cjs
```

测试默认连接 `127.0.0.1:8766`。报告中手机是 Chrome 的移动尺寸及触控事件仿真，并非实机 Safari/Android 验收。

## 精度与动画含义

起止点**文字**、骨名、关节配对及浅深层关系按公开解剖资料核对。**所有网格几何仍是程序化示意，未被标记为解剖准确。** 附着点投影到本模型的骨面，只证明模型内部连接连续，不能证明它位于真实人体的精确足印。

动作假设是无外部负荷的交替主动屈伸、拮抗肌放松。实际人体可能存在离心收缩、共同收缩及不同负荷策略，所以不能仅按运动方向推断真实肌肉激活。本样板没有计算肌力、力矩、肌电、肌束应变或组织碰撞响应。

本次仅创建 `reactive/elbow-lab`，没有修改已有课程、验收素材或发布状态，没有部署网站。
