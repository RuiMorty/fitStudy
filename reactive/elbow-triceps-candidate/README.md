# 三头肌整段形变实验 · 尚未验收

这是 `elbow-attachments` 的独立实验副本，不能代替已交付版本。正式页面 8768 和原始模型未改动。本副本仅在 8770 本机预览。

原先把弯折集中到下端的方案已被用户否定，不应复用。当前改用各肌头自己的路径弧长分配肌腹伸长，并作横截面缩减；共同远端路径沿肘后方走行。远端腱源网格中嵌入尺骨的体积已裁除。三头肌源网格的长三角面作了细分。

这些是几何近似，没有依据患者数据或生物力学参数验证肌纤维应变、腱刚度、组织体积守恒及接触滑动。当前仍有局部骨面穿入，整体外形未获验收，不应称为“已修复”或“解剖准确”。

- 可编辑候选：`assets/elbow-right.blend`
- 网页候选：`assets/elbow-right.glb`
- 新路径方法：`blender/triceps_path.py`
- 完整检查：`blender/audit_triceps.py`、`qa/triceps-verification.json`
- 整段屈伸演示：`qa/triceps-whole-candidate.gif`

`docs/` 其余历史记录和继承的 QA 结果不代表本候选已通过。当前结果以 `qa/triceps-verification.json` 为准。

启动：`python3 -m http.server 8770 --bind 127.0.0.1`

BodyParts3D © DBCLS，派生几何遵循 CC BY-SA 2.1 Japan；参见 `docs/SOURCES.md`。
