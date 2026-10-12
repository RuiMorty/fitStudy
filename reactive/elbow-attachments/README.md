# 肘关节运动解剖样板 · 0.3.3

这是 `elbow-studio` 的独立修正版，原版文件及课程未改动，没有部署。保留 17 个独立解剖结构，新增 6 个骨面候选附着区作为可编辑标注。**候选区域尚未通过专业解剖审核，不能称为已确认的完整足印。**

## 0.3.3 观察与照明

默认与复位相机从正前方观察。主光随相机转动，保留表面明暗，关闭投射阴影以消除原有的隔帧阴影滞后。播放不再改变组织颜色，也不再切换画布分辨率；主动与被动角色仍通过文字说明。模型几何与贴图未改动，已有穿插问题仍待处理。

## 界面更新

按最终选择恢复原来的暖白页面、灰绿色控件与深色模型背景。保留中文无衬线字体和中文界面文案，英文名称在详情中展开查看。模型、结构数据及建模脚本保持不变。

## 本轮贴合优化

针对侧面观察中二头肌、肱肌之间被放大的长缝，减少二头肌向前的人工分离偏移，统一两层屈肌的主体运动趋势；肱肌朝骨面的表面在候选区域内保持贴骨，二头肌内侧表面按深层肱肌外形做局部避让。没有增加填洞模型，也未启用筋膜遮挡间隙。

局部余量和表面修形是样板几何参数，不能当作真实筋膜厚度。前后使用相同侧面视角、角度和比例比较。新的接触检查仍发现高角度局部约 1 mm 的方向性面中心内穿，完整肌间接触尚待审核。详见 [贴合检查](docs/LAYER-FIT.md)。

上一版完整包保留为 `../elbow-attachments-v03-before-fit.zip`，本次更新当前目录和 `elbow-attachments-delivery.zip`。

## 启动与查看

```bash
cd /Users/agiuser/Documents/fit/reactive/elbow-attachments
python3 -m http.server 8768 --bind 127.0.0.1
```

打开 <http://127.0.0.1:8768>，或使用 `npm start`。运行库和模型均在本地，无需安装网页依赖。

1. 选择「肱二头肌·长头」，点击「查看起点」。肱骨等遮挡结构临时隐藏，肌腱变为半透明，可以看到关节盂上缘附近的候选附着区。
2. 橙色区域是候选骨面，圆点是代表位置。上盂唇未建模，不应把色块理解为完整长头起点。标记遵循深度遮挡，不会穿透前方骨骼显示。
3. 切换到其余五个肌头。肱肌及三头肌的宽起点显示为代表性骨面区域。
4. 点击「返回整体观察」恢复进入前的视角、展开间距和显隐设置。手机点击按钮会自动回到模型视窗。
5. 隐藏浅层查看肱肌，播放屈伸，展开和准确复位，保留原交互。

## 这一轮修正

旧版取网格最高处，再投影到最近骨面，导致二头肌长头起点落到肩峰。新的起点由 `data/attachment-landmarks.json` 中显式指定的候选区域控制，不再使用最高点算法。保留原始长头腱到达关节盂上缘的走行，没有把肌腱错误拉到旧标记上。

相关肌肉、肌腱的局部骨面接触顶点受到固定约束，邻近表面平滑过渡到原屈伸形变。宽起点仅校准源组织与指定区域相接的部分，完整附着面积、肌间隔与桡神经沟界限仍待审核。远端止点沿用前版，未在本轮完成新的解剖定位审核。

## 交付文件

| 内容 | 文件 |
|---|---|
| 可编辑几何、形态键、绑定顶点组、候选区域 | `assets/elbow-right.blend` |
| 网页实际加载的模型 | `assets/elbow-right.glb` |
| 结构与起止点 | `data/structures.json` |
| 可复核的区域坐标与状态 | `data/attachment-landmarks.json` |
| 区域生成结果 | `data/attachment-regions.json` |
| 网页源码 | `index.html`、`src/`、`vendor/` |
| 建模与局部约束 | `blender/build_studio.py`、`blender/attachment_geometry.py` |
| 成品几何检查 | `blender/audit_attachments.py`、`qa/attachment-audit.json` |
| 浏览器回归 | `qa/verify.cjs`、`qa/verify-attachments.cjs` |
| 六个起点与手机演示 | `qa/origin-*.png`、`qa/mobile-origin-long-head.png` |
| 旧版问题与新方法、审核边界 | `docs/ATTACHMENT-CALIBRATION.md` |
| 实际验证结果 | `docs/VALIDATION.md` |

## 复现

Blender 5.2.1；重建会覆盖本目录生成的模型，请先另存人工修改的源文件。

```bash
blender -b --python-exit-code 1 --python blender/build_studio.py
blender -b --python-exit-code 1 --python blender/audit_attachments.py
blender -b --python-exit-code 1 --python blender/audit_studio.py
PLAYWRIGHT_MODULE=/path/to/node_modules/playwright node qa/verify.cjs
PLAYWRIGHT_MODULE=/path/to/node_modules/playwright node qa/verify-attachments.cjs
```

浏览器检查需要本地服务器已启动和 Chrome。解剖位置的确认不能由这些检查替代。几何检查若找不到相邻的旧版目录，会使用随包保存的历史测量结果作回归对照。

## 来源与范围

4 骨、6 肌头基于 BodyParts3D 3.0；6 腱由相关网格分区，1 层筋膜为包络示意。新增 6 个色块是辅助标注，不增加解剖结构计数；GLB 共 23 个网格。起点区域、肌腱分区、关节轴和运动仍待专业审核。形变不是肌力或有限元计算，高角度仍可能存在局部交叠和非生理形变。

**BodyParts3D, (c) The Database Center for Life Science licensed under CC Attribution-Share Alike 2.1 Japan.** 派生几何遵循同一许可，来源、原始 STL 和校验值随包保留；Three.js 运行库为 MIT。详见 `docs/SOURCES.md`。
