# 结构清单与精度边界

建模前清单；右侧，4 骨 + 6 肌头 + 6 腱 + 1 筋膜 = 17 个可选对象。左右侧、肌头和肌腱分别计数。所有网格均为原创程序化示意几何，无外部人体模型。

仅下列资料核对过的名称、骨性连接、肌肉起止点文字及浅深层关系可称为「已核对」。没有任何骨面或肌肉表面被标为解剖准确。坐标是设计值，并非测量值。

| ID / 名称 | 层级 / 所属骨 | 起点 → 止点 | 依据 / 建模边界 |
|---|---|---|---|
| `bone_scapula_R`<br>肩胛骨 / Scapula | skeleton.upper / skeleton<br>bone_scapula_R | 不适用 → 不适用 | TMA-ELBOW<br>肩胛体、肩胛冈、肩峰、喙突、盂上与盂下区域的程序化示意；无扫描数据。 |
| `bone_humerus_R`<br>肱骨 / Humerus | skeleton.upper / skeleton<br>bone_humerus_R | 不适用 → 不适用 | TMA-ELBOW<br>肱骨头、骨干、滑车与小头轮廓示意；双髁中心定义近似屈伸轴。 |
| `bone_ulna_R`<br>尺骨 / Ulna | skeleton.forearm / skeleton<br>bone_ulna_R | 不适用 → 不适用 | TMA-ELBOW<br>鹰嘴、滑车切迹、尺骨粗隆与尺骨干示意；尺骨远端不含腕关节。 |
| `bone_radius_R`<br>桡骨 / Radius | skeleton.forearm / skeleton<br>bone_radius_R | 不适用 → 不适用 | TMA-ELBOW<br>桡骨头、桡骨颈、桡骨粗隆与桡骨干示意；固定旋后位。 |
| `muscle_biceps_long_R`<br>肱二头肌·长头 / Biceps brachii · long head | muscles.flexor / superficial<br>bone_scapula_R, bone_radius_R | 肩胛骨盂上结节 → 桡骨粗隆（经共同远端肌腱）；另有肱二头肌腱膜连至前臂筋膜，本样板未建此腱膜 | TMA-ARM<br>肌腹体积随路径长度近似补偿，起止区域用单点表示；无肌力、肌电或有限元计算。 |
| `muscle_biceps_short_R`<br>肱二头肌·短头 / Biceps brachii · short head | muscles.flexor / superficial<br>bone_scapula_R, bone_radius_R | 肩胛骨喙突 → 桡骨粗隆（经共同远端肌腱）；另有肱二头肌腱膜连至前臂筋膜，本样板未建此腱膜 | TMA-ARM<br>肌腹体积随路径长度近似补偿，起止区域用单点表示；无肌力、肌电或有限元计算。 |
| `muscle_brachialis_R`<br>肱肌 / Brachialis | muscles.flexor / deep<br>bone_humerus_R, bone_ulna_R | 肱骨干前面远侧区域（起点广面压缩为标记点） → 尺骨粗隆；冠突附着细分待审核 | TMA-ARM<br>肌腹体积随路径长度近似补偿，起止区域用单点表示；无肌力、肌电或有限元计算。 |
| `muscle_triceps_long_R`<br>肱三头肌·长头 / Triceps brachii · long head | muscles.extensor / superficial<br>bone_scapula_R, bone_ulna_R | 肩胛骨盂下结节 → 尺骨鹰嘴（经共同肱三头肌腱） | TMA-ARM<br>肌腹体积随路径长度近似补偿，起止区域用单点表示；无肌力、肌电或有限元计算。 |
| `muscle_triceps_lateral_R`<br>肱三头肌·外侧头 / Triceps brachii · lateral head | muscles.extensor / superficial<br>bone_humerus_R, bone_ulna_R | 肱骨后面，桡神经沟上方 → 尺骨鹰嘴（经共同肱三头肌腱） | TMA-ARM<br>肌腹体积随路径长度近似补偿，起止区域用单点表示；无肌力、肌电或有限元计算。 |
| `muscle_triceps_medial_R`<br>肱三头肌·内侧头 / Triceps brachii · medial head | muscles.extensor / deep<br>bone_humerus_R, bone_ulna_R | 肱骨后面，桡神经沟下方 → 尺骨鹰嘴（经共同肱三头肌腱） | TMA-ARM<br>肌腹体积随路径长度近似补偿，起止区域用单点表示；无肌力、肌电或有限元计算。 |
| `tendon_biceps_long_prox_R`<br>肱二头肌长头·近端腱 / Biceps long head proximal tendon | tendons.flexor / superficial<br>bone_scapula_R | 肩胛骨盂上结节 → 长头肌腹近端 | TMA-ARM<br>长头肌腱越过肱骨头前上方并进入结节间沟的路径仅为示意，关节囊内部分未分段。 |
| `tendon_biceps_short_prox_R`<br>肱二头肌短头·近端腱 / Biceps short head proximal tendon | tendons.flexor / superficial<br>bone_scapula_R | 肩胛骨喙突 → 短头肌腹近端 | TMA-ARM<br>喙突共同腱未纳入喙肱肌。 |
| `tendon_biceps_distal_R`<br>肱二头肌·共同远端腱 / Distal biceps tendon | tendons.flexor / superficial<br>bone_radius_R | 长头与短头肌腹汇合处 → 桡骨粗隆 | TMA-ARM<br>简化为共同腱；未表示扭转、双头足印差异及肱二头肌腱膜。 |
| `tendon_brachialis_distal_R`<br>肱肌·远端腱 / Brachialis distal tendon | tendons.flexor / deep<br>bone_ulna_R | 肱肌肌腹远端 → 尺骨粗隆 | TMA-ARM<br>附着面积、冠突分支及腱膜结构待审核。 |
| `tendon_triceps_long_prox_R`<br>肱三头肌长头·近端腱 / Triceps long head proximal tendon | tendons.extensor / superficial<br>bone_scapula_R | 肩胛骨盂下结节 → 三头肌长头肌腹近端 | TMA-ARM<br>起点宽度与腱膜简化。 |
| `tendon_triceps_distal_R`<br>肱三头肌·共同远端腱 / Distal triceps tendon | tendons.extensor / superficial<br>bone_ulna_R | 肱三头肌三头汇合处 → 尺骨鹰嘴 | TMA-ARM<br>三层腱膜与内侧头独立深部插入细节未区分；绕鹰嘴的滑移为路径示意。 |
| `fascia_brachial_R`<br>臂筋膜·示意层 / Brachial fascia · schematic shell | fascia / fascia<br>bone_humerus_R | 连续筋膜，不以肌肉起止点描述 → 本样板覆盖上臂；不含肌间隔与前臂筋膜 | TMA-ARM<br>单层半透明外包络，仅用于交互验证；不是按组织厚度或真实筋膜平面重建。 |

## 坐标与运动约束

+X 外侧 / +Y 前方 / +Z 近端；肘轴中心原点
+X 外侧 / +Y 近端 / -Z 前方（标准 Y-up）

肱骨长度约 0.32 m，前臂约 0.26 m；是统一单位的成人比例示意，未作个体测量。肘关节轴通过近似滑车/小头中心。肩胛骨与肱骨固定；尺桡骨作为同一前臂运动组绕 X 轴屈伸。

每块肌肉保留 `origin__<id>`、`insertion__<id>` 空对象。插入标记跟随前臂旋转。肌腹通过近端腱/共同远端腱与骨性标记保持连通；不把肌腹端点误当骨性起止点。

## 参考资料（2026-10-10 实际读取）

- [TMA-ARM — TeachMeAnatomy — Muscles of the Upper Arm](https://teachmeanatomy.info/upper-limb/muscles/upper-arm/)：肱二头肌两头起点、桡骨粗隆及腱膜止点；肱肌在二头肌深层，肱骨干起、尺骨粗隆止；三头肌三头起点、鹰嘴共同止点、内侧头深层。
- [TMA-ELBOW — TeachMeAnatomy — The Elbow Joint](https://teachmeanatomy.info/upper-limb/joints/elbow-joint/)：肱尺、肱桡关节的骨性配对；肘关节铰链式屈伸；旋前旋后属于不同自由度。

资料只作为事实核对依据，不复制网页插图、网格或整篇正文。模型几何需要后续解剖专业审核；未表示的结构包括关节软骨、韧带、关节囊、神经、血管、喙肱肌、肘肌及旋后肌。

## 补充事实核对

2026-10-10 另读取 [Kenhub — Brachialis muscle](https://www.kenhub.com/en/library/anatomy/brachialis-muscle)，核对肱肌起于肱骨前面远侧半、止于尺骨粗隆及冠突。冠突的具体足印分区仍未在样板几何中准确重建。结构数据中记为 `KH-BRACHIALIS`。
