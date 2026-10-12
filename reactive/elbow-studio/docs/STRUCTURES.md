# 精细版结构清单

保持 17 个独立对象与原有稳定 ID：4 骨、6 肌头、6 腱、1 筋膜。原始几何来源与本次适配明确区分。

| 名称 / ID | 层次 | 起点 → 止点 | 几何来源 / 状态 |
|---|---|---|---|
| 肩胛骨<br>`bone_scapula_R` | skeleton | 不适用 → 不适用 | FMA13395<br>atlas-derived |
| 肱骨<br>`bone_humerus_R` | skeleton | 不适用 → 不适用 | FMA23130<br>atlas-derived |
| 尺骨<br>`bone_ulna_R` | skeleton | 不适用 → 不适用 | FMA23467<br>atlas-derived |
| 桡骨<br>`bone_radius_R` | skeleton | 不适用 → 不适用 | FMA23464<br>atlas-derived |
| 肱二头肌·长头<br>`muscle_biceps_long_R` | superficial | 肩胛骨盂上结节 → 桡骨粗隆（经共同远端肌腱）；另有肱二头肌腱膜连至前臂筋膜，本样板未建此腱膜 | FMA37686<br>atlas-derived |
| 肱二头肌·短头<br>`muscle_biceps_short_R` | superficial | 肩胛骨喙突 → 桡骨粗隆（经共同远端肌腱）；另有肱二头肌腱膜连至前臂筋膜，本样板未建此腱膜 | FMA37684<br>atlas-derived |
| 肱肌<br>`muscle_brachialis_R` | deep | 肱骨干前面远侧区域（起点广面压缩为标记点） → 尺骨粗隆；冠突附着细分待审核 | FMA37668<br>atlas-derived |
| 肱三头肌·长头<br>`muscle_triceps_long_R` | superficial | 肩胛骨盂下结节 → 尺骨鹰嘴（经共同肱三头肌腱） | FMA37699<br>atlas-derived |
| 肱三头肌·外侧头<br>`muscle_triceps_lateral_R` | superficial | 肱骨后面，桡神经沟上方 → 尺骨鹰嘴（经共同肱三头肌腱） | FMA37697<br>atlas-derived |
| 肱三头肌·内侧头<br>`muscle_triceps_medial_R` | deep | 肱骨后面，桡神经沟下方 → 尺骨鹰嘴（经共同肱三头肌腱） | FMA37695<br>atlas-derived |
| 肱二头肌长头·近端腱<br>`tendon_biceps_long_prox_R` | superficial | 肩胛骨盂上结节 → 长头肌腹近端 | 相关肌头网格分区<br>atlas-region-separated |
| 肱二头肌短头·近端腱<br>`tendon_biceps_short_prox_R` | superficial | 肩胛骨喙突 → 短头肌腹近端 | 相关肌头网格分区<br>atlas-region-separated |
| 肱二头肌·共同远端腱<br>`tendon_biceps_distal_R` | superficial | 长头与短头肌腹汇合处 → 桡骨粗隆 | 相关肌头网格分区<br>atlas-region-separated |
| 肱肌·远端腱<br>`tendon_brachialis_distal_R` | deep | 肱肌肌腹远端 → 尺骨粗隆 | 相关肌头网格分区<br>atlas-region-separated |
| 肱三头肌长头·近端腱<br>`tendon_triceps_long_prox_R` | superficial | 肩胛骨盂下结节 → 三头肌长头肌腹近端 | 相关肌头网格分区<br>atlas-region-separated |
| 肱三头肌·共同远端腱<br>`tendon_triceps_distal_R` | superficial | 肱三头肌三头汇合处 → 尺骨鹰嘴 | 相关肌头网格分区<br>atlas-region-separated |
| 臂筋膜·示意层<br>`fascia_brachial_R` | fascia | 连续筋膜，不以肌肉起止点描述 → 本样板覆盖上臂；不含肌间隔与前臂筋膜 | 本次包络示意<br>schematic |

## 解剖文字依据

- [TeachMeAnatomy — Muscles of the Upper Arm](https://teachmeanatomy.info/upper-limb/muscles/upper-arm/)，核对日期 2026-10-10。
- [TeachMeAnatomy — The Elbow Joint](https://teachmeanatomy.info/upper-limb/joints/elbow-joint/)，核对日期 2026-10-10。
- [Kenhub — Brachialis muscle](https://www.kenhub.com/en/library/anatomy/brachialis-muscle)，核对日期 2026-10-10。

肌肉起止点文字与几何审核分开。具体足印面积、腱区分段、动态形变与肌束走向未获得专业签核。原始网格、许可与校验信息见 `SOURCES.md`。
