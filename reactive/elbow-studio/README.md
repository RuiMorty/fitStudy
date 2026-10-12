# ELBOW / 02 — Atlas Studio

精细版右侧肘部交互样板。4 块骨与 6 个肌头采用 **BodyParts3D 3.0 的独立解剖网格**，经过表面清理、适度降面、层次配准、肌腱区域分离与可编辑动画适配。6 个肌腱对象从相关原始网格分区，另有 1 层示意筋膜。网页为真实 WebGL 交互，包含实际 GLB 与纤维材质，不依赖视频或图片热点。

## 打开

```bash
cd /Users/agiuser/Documents/fit/reactive/elbow-studio
python3 -m http.server 8767 --bind 127.0.0.1
```

访问 <http://127.0.0.1:8767>。也可运行 `npm start`，无需安装 npm 依赖。资源全部本地化；需要支持 WebGL 2 的现代浏览器。不能直接用 `file://` 打开模型。

- 首先用「近」进入肘部特写，观察骨端、肌腹轮廓、纤维材质与肌腱过渡。
- 点击「看见深层肱肌」，再直接点击三维表面；起止点说明在右侧。
- 播放 0–120° 屈伸，或手动调节角度。肌肉形变为教学适配，不是肌力计算。
- 展开结构、单块隔离、开关筋膜；点击「准确复位」恢复同一角度下的原始间距。
- 鼠标拖动/滚轮与手机单指旋转/双指缩放均支持。

旧版保持原样：`../elbow-lab`，原预览端口 8766。没有部署网站或改动已有课程。

## 这轮的实际变化

- 骨骼由数据库骨面构成，保留肩胛骨凹面、冈与突起、肱骨端和尺桡骨的真实形态特征。
- 六个肌头保留源网格的宽扁、包覆、不对称轮廓，不再用统一纺锤体代替。
- 肌腹、近端腱与远端腱独立可选；肌纤维/胶原材质含纹理、法线与粗糙度变化。
- 深色观察台、冷暖补光和实时接触阴影呈现体积；增加「近」按钮。
- 保留可编辑形态键与附着标记。播放时降低渲染采样、间隔更新阴影以减少开销，暂停后恢复观察精度。

## 文件

| 内容 | 路径 |
|---|---|
| 可编辑 Blender 模型、材质、形态键与动画 | `assets/elbow-right.blend` |
| 网页实际使用的精细模型 | `assets/elbow-right.glb` |
| 结构、起止点、层级、稳定 ID、来源 | `data/structures.json` |
| 原始十个解剖网格及其校验值 | `sources/`、`sources/provenance.json` |
| 纤维/胶原纹理 | `assets/*-color.png`、`assets/*-normal.png`、`assets/*-roughness.png` |
| 网页源码 | `index.html`、`src/`、`vendor/` |
| 建模复现 | `blender/build_studio.py` |
| 验收与截图 | `qa/verification.json`、`docs/VALIDATION.md` |
| 来源与许可 | `docs/SOURCES.md` |
| 已知限制及待审核点 | `docs/MODEL-REVIEW.md` |

## 重新生成与验证

本次使用 Blender 5.2.1。重建会覆盖本目录生成的模型和材质，请先另存人工编辑的版本。

```bash
blender -b --python blender/build_studio.py
blender -b --python blender/audit_studio.py
PLAYWRIGHT_MODULE=/path/to/node_modules/playwright node qa/verify.cjs
```

Blender 时间线 1–121 帧对应 0–120°。骨骼使用 `joint_elbow_R` 刚体层级，肌肉/肌腱使用 `Flex_005` 至 `Flex_120` 形态键。来源与许可也写入 Blender 文本块和 GLB 元数据。

## 精度与权利

源模型来自可追溯的解剖数据库；本次的肌腱分区、细小配准位移、轴定位、肌肉形变和筋膜仍未经过专业解剖审核，不能称为医学测量模型。纤维纹理属于可视化细节，不代表真实肌束追踪结果。

**BodyParts3D, (c) The Database Center for Life Science licensed under CC Attribution-Share Alike 2.1 Japan.** 本样板派生几何遵循同一 [CC BY-SA 2.1 Japan 许可](https://creativecommons.org/licenses/by-sa/2.1/jp/)。网页运行库 Three.js 为 MIT，见 `vendor/THREE-LICENSE.txt`。没有把数据库模型声明为从零原创模型。
