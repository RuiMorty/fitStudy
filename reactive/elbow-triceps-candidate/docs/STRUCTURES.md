# 起点校准版结构清单

17 个独立解剖结构保持原稳定 ID。新增 6 个候选附着区是辅助标注，不是额外的肌肉或组织。具体位置与状态见 `data/attachment-landmarks.json`。

| 名称 / ID | 层次 | 起点 → 止点 | 几何来源 |
|---|---|---|---|
| 肩胛骨<br>`bone_scapula_R` | skeleton | 不适用 → 不适用 | FMA13395 |
| 肱骨<br>`bone_humerus_R` | skeleton | 不适用 → 不适用 | FMA23130 |
| 尺骨<br>`bone_ulna_R` | skeleton | 不适用 → 不适用 | FMA23467 |
| 桡骨<br>`bone_radius_R` | skeleton | 不适用 → 不适用 | FMA23464 |
| 肱二头肌·长头<br>`muscle_biceps_long_R` | superficial | 肩胛骨盂上结节及上盂唇；本样板仅显示骨性候选附着区，上盂唇未建模 → 桡骨粗隆（经共同远端肌腱）；另有肱二头肌腱膜连至前臂筋膜，本样板未建此腱膜 | FMA37686 |
| 肱二头肌·短头<br>`muscle_biceps_short_R` | superficial | 肩胛骨喙突 → 桡骨粗隆（经共同远端肌腱）；另有肱二头肌腱膜连至前臂筋膜，本样板未建此腱膜 | FMA37684 |
| 肱肌<br>`muscle_brachialis_R` | deep | 肱骨前面远侧半及相邻肌间隔；色块为骨面宽起点的代表区，肌间隔未建模 → 尺骨粗隆；冠突附着细分待审核 | FMA37668 |
| 肱三头肌·长头<br>`muscle_triceps_long_R` | superficial | 肩胛骨盂下结节 → 尺骨鹰嘴（经共同肱三头肌腱） | FMA37699 |
| 肱三头肌·外侧头<br>`muscle_triceps_lateral_R` | superficial | 肱骨后面，桡神经沟上方 → 尺骨鹰嘴（经共同肱三头肌腱） | FMA37697 |
| 肱三头肌·内侧头<br>`muscle_triceps_medial_R` | deep | 肱骨后面，桡神经沟下方 → 尺骨鹰嘴（经共同肱三头肌腱） | FMA37695 |
| 肱二头肌长头·近端腱<br>`tendon_biceps_long_prox_R` | superficial | 肩胛骨盂上结节及上盂唇；本样板仅显示骨性候选附着区，上盂唇未建模 → 长头肌腹近端 | 相关网格分区 / 示意 |
| 肱二头肌短头·近端腱<br>`tendon_biceps_short_prox_R` | superficial | 肩胛骨喙突 → 短头肌腹近端 | 相关网格分区 / 示意 |
| 肱二头肌·共同远端腱<br>`tendon_biceps_distal_R` | superficial | 长头与短头肌腹汇合处 → 桡骨粗隆 | 相关网格分区 / 示意 |
| 肱肌·远端腱<br>`tendon_brachialis_distal_R` | deep | 肱肌肌腹远端 → 尺骨粗隆 | 相关网格分区 / 示意 |
| 肱三头肌长头·近端腱<br>`tendon_triceps_long_prox_R` | superficial | 肩胛骨盂下结节 → 三头肌长头肌腹近端 | 相关网格分区 / 示意 |
| 肱三头肌·共同远端腱<br>`tendon_triceps_distal_R` | superficial | 肱三头肌三头汇合处 → 尺骨鹰嘴 | 相关网格分区 / 示意 |
| 臂筋膜·示意层<br>`fascia_brachial_R` | fascia | 连续筋膜，不以肌肉起止点描述 → 本样板覆盖上臂；不含肌间隔与前臂筋膜 | 相关网格分区 / 示意 |

## 解剖文字参考与几何状态

- [TeachMeAnatomy — Muscles of the Upper Arm](https://teachmeanatomy.info/upper-limb/muscles/upper-arm/)
- [TeachMeAnatomy — The Elbow Joint](https://teachmeanatomy.info/upper-limb/joints/elbow-joint/)
- [Kenhub — Brachialis muscle](https://www.kenhub.com/en/library/anatomy/brachialis-muscle)

沿用上一版的文字参考。本轮没有专家解剖签核，候选区的具体骨面位置、完整附着边界和近端腱分区均为待审核状态。二头肌长头上盂唇附着仅作文字补充，模型未包含上盂唇。不得将候选区面积或内部几何误差解释为真实人体测量。

骨骼与六个肌头的原始数据为 BodyParts3D，相关来源、许可与校验信息见 `SOURCES.md`。变化细节见 [起点校准记录](ATTACHMENT-CALIBRATION.md)。
