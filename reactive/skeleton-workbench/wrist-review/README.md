# 腕部韧带审核工作台

本地入口 http://127.0.0.1:8771/wrist-review/ ，从 skeleton-workbench 沿用 npm start，无部署。

本轮接入已有 v2 模型：31 个源名称类别、61 个韧带对象，加双侧桡骨、尺骨、8 块腕骨和5块掌骨，共91个网页对象。源模型来自同一 Z-Anatomy 数据，不混用不同骨架。原模型不删除、不改写。

## 当前阶段

完成清点、分组、已有附着资料映射、审核页接入；没有宣称完成腕部附着修形。仍有19个对象缺少已关联的附着资料。尺豌豆韧带仅有左侧，命名重叠与TFCC相关部分见 AUDIT-CHECKLIST.md。左侧独有对象切换到右侧时会选择同组可用对象，不生成镜像。

骨性标志6类11个，来自源引线：桡骨茎突、尺骨茎突、尺切迹、舟骨结节、大多角骨结节、钩骨钩。左大多角骨结节没有原生引线，未自动补点。源引线端点最多约0.179mm投影到对应骨面，原偏移记于 landmarks.json。颜色是柔边定位范围，不是精确附着区域，使用骨面归属遮罩防止颜色透过韧带。

## 文件与重建

- build_catalog.py：读取已有腕部清单与附着资料，生成 catalog.json、source-inventory.json 和 inventory-summary.json。
- build_models.py：从 wrist-ligaments-refined-v2.blend 提取同源参考骨和已有韧带，生成独立 wrist-review.blend / .glb；不改几何形状。
- build_landmarks.py：读取源引线；随后设置 REVIEW_SCOPES=wrist 运行 ../joint-review-common/build_regions.py。
- geometry-audit.json：标明为继承的静态抽样结果，不冒充本轮完整碰撞复核。
- AUDIT-CHECKLIST.md：逐类清单和下一步处理次序。

当前保留旋转、缩放、单条/分组显示、移出复位、颜色开关及本机审核记录。点击目录不自动放大，近看为显式操作。网页使用共用审核脚本，不提供未经校准的腕关节动画。
