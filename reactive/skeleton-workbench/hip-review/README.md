# 髋部审核候选

从父目录本机 HTTP 服务打开 hip-review/。保留 Z-Anatomy 同源原配坐标；.blend 含源对象场景及网页网格场景。

- 所有源模型仍待逐项核对附着足印、侧别、厚度和穿插；本版无关节运动。
- 骨性标志和颜色范围尚未建立；不会用骨中心或随意点位代替。
- 未关联文献的条目在详情中标为待补齐，不据名称编写附着。

公开参考： https://teachmeanatomy.info/lower-limb/joints/hip-joint/ （2026-10-13 读取；只支持标明的区域概述。）

复建：先运行 joint-review-common/build_lower_reviews.py，再用 Blender 执行 package_lower_reviews.py。

审查统一：运行 build_lower_landmarks.py 和 REVIEW_SCOPES=hip,knee 的 build_regions.py，最后运行 unify_lower_reviews.py。原生定位标志并不代表完整足印。

当前网页模型：hip-review-unified.glb；可编辑文件：hip-review-unified.blend。几何初筛：geometry-audit-unified.json；逐条核对清单：AUDIT-CHECKLIST.md。
复建最后依次运行 refine_lower_reviews.py 和 supplement_lower_evidence.py（需先准备 references 中的已核对资料）。
