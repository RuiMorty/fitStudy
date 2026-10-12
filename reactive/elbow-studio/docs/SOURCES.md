# 模型来源、署名与许可

BodyParts3D, (c) The Database Center for Life Science licensed under CC Attribution-Share Alike 2.1 Japan

- 数据库：BodyParts3D / Anatomography, version 3.0 (20110915)。
- 分发仓库：[https://github.com/Kevin-Mattheus-Moerman/BodyParts3D](https://github.com/Kevin-Mattheus-Moerman/BodyParts3D)。
- 本次获取的固定提交：`f0eeb6e843380cfe6b83797cf8c3e1af74de5e61`。
- 获取日期：2026-10-10。
- 许可：[CC BY-SA 2.1 Japan](https://creativecommons.org/licenses/by-sa/2.1/jp/)；原文副本见 `sources/LICENSE-BodyParts3D.txt`。
- 数据集引用文献（上游提供）：[https://doi.org/10.1093/nar/gkn613](https://doi.org/10.1093/nar/gkn613)。

本次派生模型及其渲染图片保留署名与相同方式共享要求。源 STL、每个文件的 SHA-256、坐标说明均随交付提供。模型没有被声明为从零原创或已通过临床验证。

| 网页稳定 ID | 数据库 FMA | 源文件 |
|---|---|---|
| `bone_scapula_R` | FMA13395 | `FMA13395.stl` |
| `bone_humerus_R` | FMA23130 | `FMA23130.stl` |
| `bone_radius_R` | FMA23464 | `FMA23464.stl` |
| `bone_ulna_R` | FMA23467 | `FMA23467.stl` |
| `muscle_brachialis_R` | FMA37668 | `FMA37668.stl` |
| `muscle_biceps_short_R` | FMA37684 | `FMA37684.stl` |
| `muscle_biceps_long_R` | FMA37686 | `FMA37686.stl` |
| `muscle_triceps_medial_R` | FMA37695 | `FMA37695.stl` |
| `muscle_triceps_lateral_R` | FMA37697 | `FMA37697.stl` |
| `muscle_triceps_long_R` | FMA37699 | `FMA37699.stl` |

## 修改记录

统一单位与坐标；清理重复顶点和法线；轻度平滑及降面；从相关网格分离肌腱区域；毫米级浅深层配准调整；骨面足印与动画端点标记；可编辑笼形变与 5° 间隔形态键；程序化纤维/胶原材质；独立示意筋膜包络。

肌腱分区与运动适配不是源数据库原有的验证结果。详细边界见 `MODEL-REVIEW.md`。网页运行库 Three.js 的 MIT 许可见 `vendor/THREE-LICENSE.txt`。
