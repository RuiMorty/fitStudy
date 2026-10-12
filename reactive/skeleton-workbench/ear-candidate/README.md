# 听骨链候选研究

打开 http://127.0.0.1:8771/ear-candidate/ 。沿用主骨架本地服务器；无需部署。

本页加载六块独立听小骨及两块候选来源的颞骨，提供左右切换、选择、半透明颞骨上下文和 0–4 mm 示意展开，准确复位。保留来源装配，不把它们写入当前主骨架，也不将主骨架计数改为206。

## 已确认的资源事实

- 固定源仓库：https://github.com/Z-Anatomy/Models-of-human-anatomy/tree/2b6cf98a8ca012571ecb252e5c077b42a21b3b61
- 模型包 Z-Anatomy.zip，86,734,957 字节；SHA-256：e029688545627bd0214b269e1063143abb580aad72b2c2445d6d8a9a0d9da736。
- 从 Startup.blend 读取 Malleus.r/.l、Incus.r/.l、Stapes.r/.l、Temporal bone.r/.l 八个实际网格。没有运行源包插件或自动脚本。
- 六块听小骨均有可编辑几何；左侧对象世界变换含负行列式，且左右对应顶点数相同，必须披露其上游镜像设置，不能说是左右独立扫描。
- 颞骨与当前 BodyParts3D 3.0 网格顶点数、世界坐标和左右形态不同，仅同属 BodyParts3D 派生谱系不证明同一配准。
- 源对象世界变换烘焙进导出几何，重新居中原点并保持装配。法线重算、三角化、展示材质替换；没有改变听骨链形状或逐骨摆放。
- 按源世界坐标作为米展示，三骨尺寸为毫米级；原始比例及临床尺寸仍需审核，不能用于测量结论。

## 许可与配准待办

Z-Anatomy 总许可为 CC BY-SA 4.0，但它的 Readme 与 License 同时列出 “Anatomy of the Inner Ear — University of Dundee School of Medicine — CC BY-NC-SA 4.0” 作为参考/纳入素材。对象属性未给出每块听小骨的具体创作来源，因此不能仅凭总许可宣称这六块适用商业用途。该来源冲突尚未解决，本页为本地研究候选，不是正式再分发交付素材。

后续必须逐块核实素材归属；若需商业使用，选择许可明确的其他来源或在取得授权后处理。接入现有骨架时，以颞骨鼓室区域、镫骨底板/前庭窗和鼓膜连接关系共同核对整条链的配准；不能逐骨缩放凑齐，也不能仅对齐颞骨包围盒。

## 文件

- assets/ear-candidate.blend：可编辑的8对象研究场景。
- assets/ear-candidate.glb：网页实际加载的模型。
- data.json：逐对象、原始坐标、镜像状态、版本和审核记录。
- ../research/ossicles/：原包、官方索引检索记录、许可与检查脚本。
- ../qa/ear-candidate-report.json：浏览器验证；实体手机和解剖审核不在通过范围。

BodyParts3D — DBCLS — CC BY-SA 2.1 Japan；Z-Anatomy — The libre 3D atlas of anatomy — CC BY-SA 4.0；耳部参考：University of Dundee School of Medicine — CC BY-NC-SA 4.0。
