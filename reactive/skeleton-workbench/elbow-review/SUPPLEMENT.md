> 纤维体重建（elbow-fiber-v1）：`build_fiber_ligaments.py` 用共用模块 `../joint-review-common/fiber_shell.py` 把 16 个肘部薄壳（原 0.17–0.5 mm 等厚）重建为纤维体：逐顶点配对对侧层，保留中面，按距边缘距离做椭圆收边，端部渐薄，加纤维束起伏；增厚进入骨内时二分收缩并在邻域扩散，中面已在骨内处不加深。拓扑、`_motion_weight` 不变，24 帧屈伸形态按同一配对逐帧重建并对已转动的前臂骨做避让，`elbow-motion.js` 未改。峰值厚度见脚本 `DISPLAY_THICKNESS_MM`（1.0–2.6 mm），为显示参数。新产物：`elbow-review-fiber.glb`、`elbow-fiber-ligaments.blend`、`geometry-audit-fiber.json`、`../z-anatomy-candidate/elbow-ligaments-fiber.{json,glb}`、`../motion/elbow-ligaments-fiber.glb`；旧产物保留。斜索为开放网格，仅约 58% 顶点可配对，仍偏片状。

> 接缝与附着（同一修订）：桡侧副韧带源对象由上下两块网格组成，两块彼此贴近的边缘现识别为内部接缝，不收边并在膨胀后对合，消除中间分割线。距骨面 2.5 mm 内的韧带端部（末 25% 长度）展宽为圆舌形足印、深面贴骨、浅面渐薄至零，末端沉入骨面 0.08 mm，颜色渐变为骨色；运动帧对转动后的骨面同样处理。足印形状是显示处理，不是文献足印。对比图：`../qa/elbow-fiber-rcl-seam-fixed.png`、`../qa/elbow-fiber-lucl-enthesis.png`。

# 肘部韧带补充候选 · 2026-10-14

当前主页面与肘部审核页均使用此补充版本。每侧 8 项，双侧 16 项；其中 8 个对象沿用同源网格或其已有显示派生，8 个对象为文献关系指导的重建候选。不是解剖验收完成。

| 每侧结构 | 来源与变化 | 纯屈伸显示 |
|---|---|---|
| 尺侧副韧带前束 | 替换旧整体候选；依据前下方起侧、崇高结节和尺骨嵴的附着关系重建 | 两端绑定，主体变形 |
| 尺侧副韧带后束 | 独立重建；内上髁至鹰嘴内侧的扇形候选 | 两端绑定，主体变形 |
| 尺侧副韧带横束 | 独立重建；冠突内侧至鹰嘴内侧，两端均在尺骨 | 随尺骨移动 |
| 尺侧外侧副韧带（LUCL） | 独立重建；外上髁经桡骨头后外侧至旋后肌嵴 | 两端绑定，主体变形 |
| 桡侧副韧带 | 沿用上一版肱骨—环状韧带显示模型与变形数据 | 两端绑定，主体变形 |
| 桡骨环状韧带 | 沿用上一版 | 随前臂移动；旋转间隙未动态验收 |
| 方形韧带 | 沿用上一版 | 随前臂移动 |
| 斜索 | 从 Z-Anatomy Startup.blend 的左右 Oblique cord 原配网格提取并细分 | 随前臂移动 |

## 附着依据与限制

- Cinque ME et al. 2020, *Review of Anatomy of the Medial Ulnar Collateral Ligament Complex of the Elbow*. DOI: 10.1007/s12178-020-09609-z。已阅读公开全文，保存相关正文至 `references/ucl-review-2020.txt`。支持三束结构、前束肱骨起侧及远端延长足印；文献平均尺寸不作为该骨架的实测尺寸。
- *Applied anatomy of the elbow*, Clinical Gate。已阅读韧带段落，摘录保存至 `references/applied-elbow-excerpts.json`。支持后束朝向鹰嘴、Cooper 纤维位于尺骨远侧连接、LUCL 至旋后肌嵴和斜索连接关系。该页内侧分部用词与现代三束综述不同，未将其“前部朝环状韧带”的表述用于前束建模。
- 同源骨性标志来自 Z-Anatomy 标签引线最近骨面端；这些是定位点，不能当成已划定的韧带足印。补充了双侧旋后肌嵴标签与贴骨颜色定位范围。
- 前、后、横束与 LUCL 的宽度、厚度、骨面足印和纤维分布均为候选。源外侧组合网格未证明包含完整独立 LUCL，当前独立模型也未通过专家核对。
- 副外侧副韧带有变异，本轮未在缺乏可靠同源独立模型与足印证据时强行添加。
- 关节囊仍未绑定变形；未增加肌腱、肌肉、旋前旋后或真实组织应力计算。

## 模型与接入

- 可编辑源：`elbow-review-supplement.blend`。独立形态键、端部候选顶点组、匹配骨的屈伸关键帧；旧源文件未删除。
- 审核静态装配：`elbow-review-supplement.glb`，含 6 块骨和 16 个韧带对象。
- 主页面补充资源：`../z-anatomy-candidate/assets/elbow-supplement.glb`；清单 `../z-anatomy-candidate/elbow-supplement.json`。新增 10 个对象，替换旧双侧整体尺侧副韧带对象，净增 8 项。
- 运动资源：`../motion/elbow-ligaments-complete.glb`，8 个可变形对象，0°原形与 24 个 5°间隔形态。其余肘部韧带使用静态网格随前臂移动。
- 审核入口 `review-config.json` 指向 `supplement-catalog.json`，未修改其他部位的审核数据。
- `build_supplement.py` 从上一版装配、运动源和原始斜索重建上述文件；附着候选坐标、端宽与浅嵌入测量保存在补充清单内的 `attachment_candidates` 字段。

## 验证

`node qa/check_elbow_supplement.mjs`：实际 GLB 加载、双侧 0/2.5/30/62.5/90/117.5/120°端部随动、非刚性变化、开关、视图切换和退出恢复。报告：`../qa/elbow-supplement-validation.json`。这些误差只验证程序绑定，不等于解剖定位精度。

新建三种跨关节束（双侧 6 个网格）每 5°抽样至120°，144 个姿态中的自由段顶点最近法线筛查未提示大于0.5 mm的深部穿入；结果在 `supplement-deformation-audit.json`。这不是完整三角面、自相交、韧带互相重叠或所有连续帧的碰撞验收。原配斜索仍需要用户与解剖人员检查足印。

本地运行：在工作台目录运行 `python3 -m http.server 8771`，访问 `/elbow-review/` 或主页「进入肘部运动」。不部署。

## 三束纤维与修形（ucl-fiber2）

前、后、横束采用平滑附着曲线之间的连续曲面，取消逐顶点推离骨面造成的锯齿折叠。横束两端仍随同一尺骨移动，不添加虚假的跨关节拉伸。端部宽度和曲面均为显示候选，不是文献实测足印。

新增顺走行的颜色、法线和粗糙度纹理，弱化塑料高光；主页面与审核页面通过 `src/ucl-material.js` 共用材质。选中时保留纤维。纹理生成源为 `build_fiber_material.py`，PNG 位于 `textures/`，已经打包进可编辑 `.blend`。GLB 只导出几何与形态数据，网页材质依赖上述模块及 PNG，单独在其他查看器打开 GLB 不会自动获得本页效果。

材质与网格外观不是组织力学参数，静态贴合及抽样运动筛查不代表解剖审核或完整碰撞验收。

## 当前版本：还原带状模型（ucl-restored9）

按用户要求，尺侧副韧带前、后、横束已还原到实体细束实验前的连续带状模型及其材质、运动形态。主页面、审核页和可编辑源同步。其他韧带构建规则未变。

`resolve_ucl_contacts.py`、`ucl-interbundle-audit.json`、`ucl-attachment-transition-check.json` 为已撤回实验的文件，不描述当前模型；保留文件但不再运行或作为当前验证依据。
