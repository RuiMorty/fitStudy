# 实现与复现

本目录是在检查 FitStudy 根目录说明、package.json、现有文件及本机 Blender 后新建的独立样板，原先没有 `reactive`。原仓库用于课程渲染，存在其他未提交工作，均未覆盖。

数据流程：`define_structures.py → structures.json / STRUCTURES.md → build_elbow.py → .blend / .glb / geometry-stats.json → GLTFLoader → AnimationMixer → WebGLRenderer`。

Blender 的 17 个对象分入骨骼、浅肌、深肌、肌腱、筋膜集合，12 个骨性标记和关节控制放在单独集合。导出包含 31 个节点。GLB 中可能每个对象输出一条独立动画，网页通过同一个角度采样骨骼曲线与导出的形态键。为降低 GPU 开销，每个变形网格只使用当前角度相邻的两组 GLB 形态键；几何数据仍来自导出文件。播放回程不依赖一次性动画的终止状态。

单位为米。Blender `[x,y,z]` 对应 glTF `[x,z,-y]`，网页采用标准 Y-up，不附加不明确的模型旋转补丁。`structures.json` 的坐标仍显式记录为 Blender 空间。

图形依赖固定为 Three.js 0.180.0，本地包含 core/module、OrbitControls、GLTFLoader 和 BufferGeometryUtils，许可见 vendor/THREE-LICENSE.txt。没有外部字体、运行时 CDN、API 或遥测请求。

交互检查使用真实 DOM 事件、鼠标画布点击与 Chrome 触控事件；数值断言另外检查刚体旋转、变形顶点、远端肌腱连续性与精确复位。截图仅为证据，用户交付的网页本身为三维交互。
