const state = {
  lessons: [],
  reviews: [],
  phases: [],
  currentDay: null,
  tab: "theory",
  visibleTab: "theory",
  tabTransitionTimer: null,
  cert: "全部",
  phase: "全部",
  category: "全部",
  query: "",
  exerciseView: "library",
  exercisePattern: "全部",
  exerciseMuscle: "全部",
  exerciseEquipment: "全部",
  exerciseQuery: "",
  selectedExercise: "lat-pulldown",
  atlasView: "front",
  selectedMuscle: "front-left-deltoid",
};

const navigationStorageKey = "fitness-study.navigation.v1";
let reviewsRequest = null;

const publishedPages = new Map([
  [1, "html/day01-骨学基础-骨骼系统总览.html"],
  [2, "html/day02-主要骨性标志与骨骼辨识.html"],
  [3, "html/day03-关节分类-纤维软骨滑膜关节.html"],
  [4, "html/day04-关节面形状与运动学.html"],
  [5, "html/day05-动作平面与运动轴.html"],
  [6, "html/day06-肌肉微观结构-肌丝滑行理论.html"],
  [7, "html/day07-研究方法与统计学循证基础.html"],
  [8, "html/day08-本体感觉与前庭系统.html"],
  [9, "html/day09-肌纤维类型与特性.html"],
  [10, "html/day10-骨骼肌起止点与命名规则.html"],
  [11, "html/day11-主要肌群-上肢肌功能分群.html"],
  [12, "html/day12-主要肌群-核心肌群与McGill核心功能分类.html"],
  [13, "html/day13-肌肉收缩类型.html"],
  [14, "html/day14-第2周复盘-本体感觉肌纤维肌群收缩.html"],
  [15, "html/day15-生物力学基本概念与力.html"],
  [16, "html/day16-杠杆系统与力矩.html"],
  [17, "html/day17-动作的生物力学分析-动作模式.html"],
  [18, "html/day18-脊柱与核心生物力学.html"],
  [19, "html/day19-肌力与肌耐力的力学决定因素.html"],
  [20, "html/day20-运动损伤的力学机制.html"],
  [21, "html/day21-第3周复盘-生物力学.html"],
  [22, "html/day22-能量系统-ATP-PCr系统.html"],
  [23, "html/day23-能量系统-糖酵解系统.html"],
  [24, "html/day24-能量系统-氧化系统.html"],
  [25, "html/day25-能量系统交互与运动强度关系.html"],
  [26, "html/day26-神经肌肉接头与兴奋-收缩耦联完整钙链条.html"],
  [27, "html/day27-运动单位募集与神经肌肉控制深化.html"],
  [28, "html/day28-第4周复盘-能量系统与神经肌肉.html"],
  [29, "html/day29-训练适应基本原则.html"],
  [30, "html/day30-FITT-VP训练变量与ACSM身体活动指南.html"],
  [31, "html/day31-PAR-Q+与医学筛查.html"],
]);

const generatedThumbs = new Map([
  [1, "html/thumbs/day01-skeletal-system-thumbnail.png"],
  [2, "html/thumbs/day02-bony-landmarks-thumbnail.png"],
  [3, "html/thumbs/day03-joint-types-thumbnail.png"],
  [4, "html/thumbs/day04-joint-arthrokinematics-thumbnail.png"],
  [5, "html/thumbs/day05-motion-planes-axes-thumbnail.png"],
  [6, "html/thumbs/day06-muscle-sliding-filament-thumbnail.png"],
  [7, "html/thumbs/day07-evidence-research-methods-thumbnail.png"],
  [8, "html/thumbs/day08-proprioception-vestibular-thumbnail.png"],
  [9, "html/thumbs/day09-muscle-fiber-types-thumbnail.png"],
  [10, "html/thumbs/day10-muscle-origin-insertion-thumbnail.png"],
  [11, "html/thumbs/day11-upper-limb-muscle-groups-thumbnail.png"],
  [12, "html/thumbs/day12-core-mcgill-functions-thumbnail.png"],
  [13, "html/thumbs/day13-muscle-contraction-types-thumbnail.png"],
  [14, "html/thumbs/day14-week2-recap-thumbnail.png"],
  [15, "html/thumbs/day15-biomechanics-force-basics-thumbnail.png"],
  [16, "html/thumbs/day16-lever-torque-system-thumbnail.png"],
  [17, "html/thumbs/day17-biomechanical-movement-patterns-thumbnail.png"],
  [18, "html/thumbs/day18-spine-core-biomechanics-thumbnail.png"],
  [19, "html/thumbs/day19-strength-endurance-determinants-thumbnail.png"],
  [20, "html/thumbs/day20-injury-biomechanics-thumbnail.png"],
  [21, "html/thumbs/day21-week3-biomechanics-review-thumbnail.png"],
  [22, "html/thumbs/day22-atp-pcr-energy-system-thumbnail.png"],
  [23, "html/thumbs/day23-glycolytic-energy-system-thumbnail.png"],
  [24, "html/thumbs/day24-oxidative-energy-system-thumbnail.png"],
  [25, "html/thumbs/day25-energy-system-interaction-intensity-thumbnail.png"],
  [26, "html/thumbs/day26-neuromuscular-coupling-thumbnail.png"],
  [27, "html/thumbs/day27-motor-unit-recruitment-control-thumbnail.png"],
  [28, "html/thumbs/day28-fourth-week-review-energy-systems-neuromuscular-thumbnail.png"],
  [29, "html/thumbs/day29-training-adaptation-principles-thumbnail.png"],
  [30, "html/thumbs/day30-fitt-vp-acsm-guidelines-thumbnail.png"],
  [31, "html/thumbs/day31-par-q-medical-screening-thumbnail.png"],
]);

const categories = ["全部", "骨关节", "肌肉", "生物力学", "能量系统", "训练技术", "评估纠正", "营养", "模考"];
const $ = (id) => document.getElementById(id);

const atlasImages = {
  front: "html/assets/muscle-atlas-front.png",
  back: "html/assets/muscle-atlas-back.png",
};

const atlasLessons = ["Day 4 关节运动学", "Day 5 动作平面", "Day 6 肌肉收缩"];

const exercises = [
  {
    id: "barbell-back-squat",
    name: "杠铃深蹲",
    english: "Barbell Back Squat",
    pattern: "深蹲",
    equipment: "杠铃",
    level: "中级",
    muscles: ["股四头肌", "臀大肌"],
    support: ["核心", "竖脊肌"],
    media: "html/assets/action-library/barbell-back-squat/barbell-back-squat.gif?v=3",
    frames: [
      "html/assets/action-library/barbell-back-squat/frame-01-standing.png?v=3",
      "html/assets/action-library/barbell-back-squat/frame-02-shallow.png?v=3",
      "html/assets/action-library/barbell-back-squat/frame-03-half.png?v=3",
      "html/assets/action-library/barbell-back-squat/frame-04-bottom.png?v=3",
    ],
    phases: ["站立", "浅蹲", "半蹲", "最低点"],
    cues: ["足底三点稳定接触地面", "膝盖沿脚尖方向追踪", "下放时保持躯干刚性"],
    mistakes: ["膝内扣", "足弓塌陷", "腰椎失去中立"],
    coachingVisuals: {
      mistakes: [
        {
          title: "膝内扣",
          description: "膝盖落在脚尖内侧时，主动向外推膝。",
          src: "html/assets/action-library/barbell-back-squat/error-knee-valgus.png",
          alt: "杠铃深蹲膝内扣错误示意图",
        },
        {
          title: "足弓塌陷",
          description: "下蹲时内侧足弓明显下沉，足舟骨（脚内侧突出的骨头）下移、跟骨（脚后跟的骨头）外翻；距下关节过度旋前使脚掌内侧承重增加，并可能连锁膝盖内扣。",
          src: "html/assets/action-library/barbell-back-squat/error-arch-collapse.png",
          alt: "杠铃深蹲足弓塌陷与跟骨外翻错误示意图",
        },
        {
          title: "腰椎失去中立",
          description: "最低点出现骨盆后卷、腰椎圆背时，缩小下蹲深度并保持躯干刚性。",
          src: "html/assets/action-library/barbell-back-squat/error-lumbar-neutral-loss.png",
          alt: "杠铃深蹲腰椎失去中立错误示意图",
        },
      ],
    },
  },
  {
    id: "romanian-deadlift",
    name: "罗马尼亚硬拉",
    english: "Romanian Deadlift",
    pattern: "髋铰链",
    equipment: "杠铃",
    level: "中级",
    muscles: ["腘绳肌", "臀大肌"],
    support: ["竖脊肌", "背阔肌"],
    cues: ["髋向后移，不是屈膝下蹲", "杠铃贴近腿部", "保持脊柱中立"],
    mistakes: ["腰背圆曲", "杠铃离身体过远", "把髋铰链做成深蹲"],
  },
  {
    id: "push-up",
    name: "俯卧撑",
    english: "Push-up",
    pattern: "水平推",
    equipment: "自重",
    level: "初级",
    muscles: ["胸大肌", "肱三头肌"],
    support: ["前三角肌", "前锯肌"],
    cues: ["身体维持一条直线", "肘部略向后打开", "推起时主动推远地面"],
    mistakes: ["腰部塌陷", "耸肩", "头部前伸"],
  },
  {
    id: "lat-pulldown",
    name: "高位下拉",
    english: "Lat Pulldown",
    pattern: "垂直拉",
    equipment: "器械",
    level: "初级",
    muscles: ["背阔肌", "大圆肌"],
    support: ["肱二头肌", "下斜方肌"],
    media: "html/assets/action-library/lat-pulldown-rear/lat-pulldown-rear.gif?v=2",
    frames: [
      "html/assets/action-library/lat-pulldown-rear/frame-01-start.png?v=2",
      "html/assets/action-library/lat-pulldown-rear/frame-02-pull.png?v=2",
      "html/assets/action-library/lat-pulldown-rear/frame-03-contracted.png?v=2",
    ],
    phases: ["起始位", "下拉中段", "收缩位"],
    cues: ["先做肩胛下压", "肘部向下向后", "避免靠后仰借力"],
    mistakes: ["颈后下拉", "身体大幅后仰", "耸肩拉动"],
  },
  {
    id: "pallof-press",
    name: "Pallof Press",
    english: "Pallof Press",
    pattern: "抗旋转",
    equipment: "绳索",
    level: "初级",
    muscles: ["腹斜肌", "腹横肌"],
    support: ["臀中肌", "肩胛稳定肌"],
    cues: ["肋骨对齐骨盆", "推出时抵抗躯干旋转", "均匀呼吸"],
    mistakes: ["骨盆旋转", "耸肩", "憋气"],
  },
  {
    id: "split-squat",
    name: "保加利亚分腿蹲",
    english: "Bulgarian Split Squat",
    pattern: "单腿深蹲",
    equipment: "哑铃",
    level: "中级",
    muscles: ["股四头肌", "臀大肌"],
    support: ["臀中肌", "核心"],
    cues: ["前脚完整踩实", "骨盆保持水平", "前膝稳定追踪"],
    mistakes: ["前膝内扣", "后脚过度发力", "骨盆下沉"],
  },
];

function atlasMuscle(id, view, name, region, x, y, functionText, children, training, signs) {
  return { id, view, name, region, x, y, function: functionText, children, training, signs, lessons: atlasLessons };
}

const muscles = [
  // 正面：头颈、肩臂、胸腹、髋腿与足踝。
  atlasMuscle("front-neck", "front", "颈部前侧", "头颈", 50, 15, "颈椎屈曲、侧屈和头颈姿势控制。", ["胸锁乳突肌", "舌骨下肌群", "斜角肌"], ["颈部等长收缩", "下巴回收"], "训练时维持颈椎中立，避免用颈部代偿推拉动作。"),
  atlasMuscle("front-left-deltoid", "front", "左三角肌", "上肢", 61, 25, "肩关节屈曲、外展和水平内收。", ["三角肌前束", "三角肌中束"], ["肩推", "侧平举", "前平举"], "上举时配合肩胛上回旋，避免耸肩。"),
  atlasMuscle("front-right-deltoid", "front", "右三角肌", "上肢", 39, 25, "肩关节屈曲、外展和水平内收。", ["三角肌前束", "三角肌中束"], ["肩推", "侧平举", "前平举"], "上举时配合肩胛上回旋，避免耸肩。"),
  atlasMuscle("front-left-pectoralis", "front", "左胸大肌", "躯干前侧", 57, 29, "肩水平内收、内旋和屈曲辅助。", ["胸大肌锁骨部", "胸大肌胸肋部"], ["卧推", "俯卧撑", "哑铃飞鸟"], "推举保持肩胛稳定，避免肘部过度外展。"),
  atlasMuscle("front-right-pectoralis", "front", "右胸大肌", "躯干前侧", 43, 29, "肩水平内收、内旋和屈曲辅助。", ["胸大肌锁骨部", "胸大肌胸肋部"], ["卧推", "俯卧撑", "哑铃飞鸟"], "推举保持肩胛稳定，避免肘部过度外展。"),
  atlasMuscle("front-left-biceps", "front", "左肱二头肌", "上肢", 66, 37, "肘屈曲、前臂旋后和肩屈曲辅助。", ["肱二头肌长头", "肱二头肌短头", "肱肌"], ["哑铃弯举", "杠铃弯举", "反握划船"], "弯举固定上臂，避免躯干摆动借力。"),
  atlasMuscle("front-right-biceps", "front", "右肱二头肌", "上肢", 34, 37, "肘屈曲、前臂旋后和肩屈曲辅助。", ["肱二头肌长头", "肱二头肌短头", "肱肌"], ["哑铃弯举", "杠铃弯举", "反握划船"], "弯举固定上臂，避免躯干摆动借力。"),
  atlasMuscle("front-left-forearm", "front", "左前臂屈肌群", "上肢", 71, 49, "腕屈曲、旋前和握力控制。", ["旋前圆肌", "桡侧腕屈肌", "尺侧腕屈肌"], ["农夫走", "腕弯举", "悬垂"], "握力不足会限制拉类动作；手腕保持中立。"),
  atlasMuscle("front-right-forearm", "front", "右前臂屈肌群", "上肢", 29, 49, "腕屈曲、旋前和握力控制。", ["旋前圆肌", "桡侧腕屈肌", "尺侧腕屈肌"], ["农夫走", "腕弯举", "悬垂"], "握力不足会限制拉类动作；手腕保持中立。"),
  atlasMuscle("front-left-serratus", "front", "左前锯肌", "躯干前侧", 60, 38, "肩胛前伸、上回旋和贴附胸廓。", ["前锯肌"], ["俯卧撑加", "墙滑", "熊爬"], "肩胛翼状时，先检查前锯肌控制和胸廓位置。"),
  atlasMuscle("front-right-serratus", "front", "右前锯肌", "躯干前侧", 40, 38, "肩胛前伸、上回旋和贴附胸廓。", ["前锯肌"], ["俯卧撑加", "墙滑", "熊爬"], "肩胛翼状时，先检查前锯肌控制和胸廓位置。"),
  atlasMuscle("front-rectus-abdominis", "front", "腹直肌", "核心", 50, 43, "躯干屈曲、骨盆后倾和腹压协同。", ["腹直肌上段", "腹直肌下段"], ["卷腹", "悬垂举腿", "死虫"], "肋骨与骨盆保持可控，避免腰椎代偿伸展。"),
  atlasMuscle("front-left-oblique", "front", "左腹斜肌", "核心", 57, 47, "躯干旋转、侧屈和抗旋转。", ["腹外斜肌", "腹内斜肌", "腹横肌"], ["Pallof Press", "侧桥", "伐木"], "优先练抗旋转和呼吸配合，不只追求躯干扭转幅度。"),
  atlasMuscle("front-right-oblique", "front", "右腹斜肌", "核心", 43, 47, "躯干旋转、侧屈和抗旋转。", ["腹外斜肌", "腹内斜肌", "腹横肌"], ["Pallof Press", "侧桥", "伐木"], "优先练抗旋转和呼吸配合，不只追求躯干扭转幅度。"),
  atlasMuscle("front-left-hip-flexor", "front", "左髋屈肌群", "髋部", 56, 55, "髋屈曲和骨盆前侧稳定。", ["髂腰肌", "阔筋膜张肌", "股直肌"], ["悬垂抬膝", "直腿抬高", "行进"], "髋屈训练避免腰椎前凸代偿，保持骨盆稳定。"),
  atlasMuscle("front-right-hip-flexor", "front", "右髋屈肌群", "髋部", 44, 55, "髋屈曲和骨盆前侧稳定。", ["髂腰肌", "阔筋膜张肌", "股直肌"], ["悬垂抬膝", "直腿抬高", "行进"], "髋屈训练避免腰椎前凸代偿，保持骨盆稳定。"),
  atlasMuscle("front-left-quadriceps", "front", "左股四头肌", "下肢", 57, 65, "膝伸展；股直肌也辅助髋屈曲。", ["股直肌", "股外侧肌", "股内侧肌", "股中间肌"], ["深蹲", "腿举", "腿屈伸"], "下蹲时追踪膝盖方向，保持足部三点支撑。"),
  atlasMuscle("front-right-quadriceps", "front", "右股四头肌", "下肢", 43, 65, "膝伸展；股直肌也辅助髋屈曲。", ["股直肌", "股外侧肌", "股内侧肌", "股中间肌"], ["深蹲", "腿举", "腿屈伸"], "下蹲时追踪膝盖方向，保持足部三点支撑。"),
  atlasMuscle("front-left-adductor", "front", "左内收肌群", "下肢", 53, 69, "髋内收、屈伸辅助和骨盆稳定。", ["长收肌", "短收肌", "大收肌", "股薄肌"], ["相扑深蹲", "哥本哈根侧桥", "夹球桥"], "内收肌需要力量与长度兼顾，单腿动作可观察骨盆控制。"),
  atlasMuscle("front-right-adductor", "front", "右内收肌群", "下肢", 47, 69, "髋内收、屈伸辅助和骨盆稳定。", ["长收肌", "短收肌", "大收肌", "股薄肌"], ["相扑深蹲", "哥本哈根侧桥", "夹球桥"], "内收肌需要力量与长度兼顾，单腿动作可观察骨盆控制。"),
  atlasMuscle("front-left-tibialis", "front", "左胫骨前肌", "下肢", 55, 82, "踝背屈、足弓控制和落地缓冲。", ["胫骨前肌", "趾长伸肌"], ["胫骨前肌抬脚", "坡走", "跳绳"], "踝背屈不足会影响深蹲深度和膝盖轨迹。"),
  atlasMuscle("front-right-tibialis", "front", "右胫骨前肌", "下肢", 45, 82, "踝背屈、足弓控制和落地缓冲。", ["胫骨前肌", "趾长伸肌"], ["胫骨前肌抬脚", "坡走", "跳绳"], "踝背屈不足会影响深蹲深度和膝盖轨迹。"),

  // 背面：肩胛稳定、后侧链、臀腿与足踝。
  atlasMuscle("back-neck", "back", "颈部后侧", "头颈", 50, 15, "颈椎伸展和头颈姿势控制。", ["头夹肌", "颈夹肌", "上斜方肌"], ["下巴回收", "颈部等长收缩"], "长时间低头后，先恢复颈椎中立和胸椎活动度。"),
  atlasMuscle("back-left-trapezius", "back", "左斜方肌", "上背", 43, 24, "肩胛上提、后缩、下压与上回旋。", ["上斜方肌", "中斜方肌", "下斜方肌"], ["面拉", "俯身 Y 举", "耸肩"], "拉类动作避免只耸肩，分清肩胛上提和后缩。"),
  atlasMuscle("back-right-trapezius", "back", "右斜方肌", "上背", 57, 24, "肩胛上提、后缩、下压与上回旋。", ["上斜方肌", "中斜方肌", "下斜方肌"], ["面拉", "俯身 Y 举", "耸肩"], "拉类动作避免只耸肩，分清肩胛上提和后缩。"),
  atlasMuscle("back-left-deltoid", "back", "左三角肌后束", "上肢", 37, 25, "肩水平外展、伸展和外旋辅助。", ["三角肌后束"], ["反向飞鸟", "面拉", "俯身划船"], "反向飞鸟避免腰椎摆动，让肩胛稳定后再带动上臂。"),
  atlasMuscle("back-right-deltoid", "back", "右三角肌后束", "上肢", 63, 25, "肩水平外展、伸展和外旋辅助。", ["三角肌后束"], ["反向飞鸟", "面拉", "俯身划船"], "反向飞鸟避免腰椎摆动，让肩胛稳定后再带动上臂。"),
  atlasMuscle("back-left-triceps", "back", "左肱三头肌", "上肢", 33, 36, "肘伸展；长头也辅助肩伸展。", ["肱三头肌长头", "外侧头", "内侧头"], ["下压", "窄距卧推", "臂屈伸"], "推类训练肘部轨迹稳定，避免肩前侧不适。"),
  atlasMuscle("back-right-triceps", "back", "右肱三头肌", "上肢", 67, 36, "肘伸展；长头也辅助肩伸展。", ["肱三头肌长头", "外侧头", "内侧头"], ["下压", "窄距卧推", "臂屈伸"], "推类训练肘部轨迹稳定，避免肩前侧不适。"),
  atlasMuscle("back-left-latissimus", "back", "左背阔肌", "背部", 41, 36, "肩伸展、内收、内旋和躯干稳定。", ["背阔肌", "大圆肌"], ["引体向上", "高位下拉", "划船"], "先建立肩胛下压，再完成肘部向下或向后运动。"),
  atlasMuscle("back-right-latissimus", "back", "右背阔肌", "背部", 59, 36, "肩伸展、内收、内旋和躯干稳定。", ["背阔肌", "大圆肌"], ["引体向上", "高位下拉", "划船"], "先建立肩胛下压，再完成肘部向下或向后运动。"),
  atlasMuscle("back-left-forearm", "back", "左前臂伸肌群", "上肢", 28, 48, "腕伸展、手指伸展和握力稳定。", ["桡侧腕长伸肌", "尺侧腕伸肌", "指伸肌"], ["反握弯举", "农夫走", "悬垂"], "腕伸肌耐力不足常使抓握动作出现手腕塌陷。"),
  atlasMuscle("back-right-forearm", "back", "右前臂伸肌群", "上肢", 72, 48, "腕伸展、手指伸展和握力稳定。", ["桡侧腕长伸肌", "尺侧腕伸肌", "指伸肌"], ["反握弯举", "农夫走", "悬垂"], "腕伸肌耐力不足常使抓握动作出现手腕塌陷。"),
  atlasMuscle("back-left-erector", "back", "左竖脊肌", "核心", 46, 42, "脊柱伸展、抗屈曲和躯干刚性维持。", ["竖脊肌", "多裂肌", "腰方肌"], ["罗马尼亚硬拉", "鸟狗", "背伸"], "髋铰链中保持脊柱中立，腰背不做主动折叠。"),
  atlasMuscle("back-right-erector", "back", "右竖脊肌", "核心", 54, 42, "脊柱伸展、抗屈曲和躯干刚性维持。", ["竖脊肌", "多裂肌", "腰方肌"], ["罗马尼亚硬拉", "鸟狗", "背伸"], "髋铰链中保持脊柱中立，腰背不做主动折叠。"),
  atlasMuscle("back-left-glute", "back", "左臀大肌", "髋部", 43, 51, "髋伸展、外旋和骨盆稳定。", ["臀大肌", "臀中肌", "深层外旋肌群"], ["臀桥", "硬拉", "保加利亚分腿蹲"], "髋伸展优先由髋完成，避免腰椎过伸抢代偿。"),
  atlasMuscle("back-right-glute", "back", "右臀大肌", "髋部", 57, 51, "髋伸展、外旋和骨盆稳定。", ["臀大肌", "臀中肌", "深层外旋肌群"], ["臀桥", "硬拉", "保加利亚分腿蹲"], "髋伸展优先由髋完成，避免腰椎过伸抢代偿。"),
  atlasMuscle("back-left-hamstrings", "back", "左腘绳肌", "下肢", 44, 64, "膝屈曲、髋伸展和跑跳减速。", ["股二头肌", "半腱肌", "半膜肌"], ["罗马尼亚硬拉", "腿弯举", "北欧腿弯举"], "后侧紧张不必然代表短缩；检查骨盆位置和神经张力。"),
  atlasMuscle("back-right-hamstrings", "back", "右腘绳肌", "下肢", 56, 64, "膝屈曲、髋伸展和跑跳减速。", ["股二头肌", "半腱肌", "半膜肌"], ["罗马尼亚硬拉", "腿弯举", "北欧腿弯举"], "后侧紧张不必然代表短缩；检查骨盆位置和神经张力。"),
  atlasMuscle("back-left-gastrocnemius", "back", "左腓肠肌", "下肢", 44, 81, "踝跖屈、跑跳推进；跨越膝关节。", ["腓肠肌内侧头", "腓肠肌外侧头", "比目鱼肌"], ["站姿提踵", "跳绳", "冲刺"], "膝伸直提踵更强调腓肠肌，控制全程踝关节活动。"),
  atlasMuscle("back-right-gastrocnemius", "back", "右腓肠肌", "下肢", 56, 81, "踝跖屈、跑跳推进；跨越膝关节。", ["腓肠肌内侧头", "腓肠肌外侧头", "比目鱼肌"], ["站姿提踵", "跳绳", "冲刺"], "膝伸直提踵更强调腓肠肌，控制全程踝关节活动。"),
];

async function init() {
  const [markdown, progress] = await Promise.all([
    fetch("fitness_syllabus.md").then((response) => response.text()),
    fetch("progress.json", { cache: "no-store" })
      .then((response) => (response.ok ? response.json() : null))
      .catch(() => null),
  ]);
  if (Number.isInteger(progress?.day)) state.currentDay = progress.day;
  parseSyllabus(markdown);
  restoreNavigation();
  bindUI();
  render();
  state.visibleTab = state.tab;
  if (state.tab === "review") loadReviews();
}

function loadReviews() {
  if (reviewsRequest) return reviewsRequest;
  reviewsRequest = fetch("reviews.json")
    .then((response) => (response.ok ? response.json() : []))
    .catch(() => [])
    .then((reviews) => {
      state.reviews = reviews;
      if (state.tab === "review" && state.visibleTab === "review") render();
      return reviews;
    });
  return reviewsRequest;
}

function restoreNavigation() {
  try {
    const saved = JSON.parse(localStorage.getItem(navigationStorageKey));
    if (!saved || typeof saved !== "object") return;

    if (["theory", "review", "exercise", "nutrition"].includes(saved.tab)) state.tab = saved.tab;
    if (["library", "atlas"].includes(saved.exerciseView)) state.exerciseView = saved.exerciseView;
    if (["front", "back"].includes(saved.atlasView)) state.atlasView = saved.atlasView;
    if (exercises.some((exercise) => exercise.id === saved.selectedExercise)) state.selectedExercise = saved.selectedExercise;
  } catch {
    // Invalid or unavailable browser storage should not block app startup.
  }
}

function saveNavigation() {
  try {
    localStorage.setItem(navigationStorageKey, JSON.stringify({
      tab: state.tab,
      exerciseView: state.exerciseView,
      atlasView: state.atlasView,
      selectedExercise: state.selectedExercise,
    }));
  } catch {
    // Private browsing or storage policies can disable localStorage.
  }
}

function parseSyllabus(markdown) {
  const lines = markdown.split(/\r?\n/);
  let currentPhase = "";
  let currentGoal = "";
  let lesson = null;

  for (const rawLine of lines) {
    const line = rawLine.trim();
    const phaseMatch = line.match(/^## 第\s*(\d+)\s*周\s*·\s*(.+)$/);
    if (phaseMatch) {
      currentPhase = `第${phaseMatch[1]}周 · ${phaseMatch[2]}`;
      currentGoal = "";
      state.phases.push({ name: currentPhase, count: 0 });
      continue;
    }

    const goalMatch = line.match(/^\*目标:\s*(.+)\*$/);
    if (goalMatch) {
      currentGoal = goalMatch[1];
      continue;
    }

    const lessonMatch = line.match(/^### Day\s+(\d+)\s*·\s*(.+?)\s*【(.+?)】$/);
    if (lessonMatch) {
      lesson = {
        day: Number(lessonMatch[1]),
        title: lessonMatch[2],
        cert: lessonMatch[3],
        phase: currentPhase,
        goal: currentGoal,
        points: [],
        practice: "",
      };
      lesson.category = getCategory(lesson.title);
      lesson.image = getLessonImage(lesson);
      state.lessons.push(lesson);
      state.phases[state.phases.length - 1].count += 1;
      continue;
    }

    if (!lesson) continue;
    if (line.startsWith("- ")) lesson.points.push(line.slice(2));
    if (line.startsWith(">")) lesson.practice = line.replace(/^>\s*/, "").replace(/^🌙\s*/, "");
  }
}

function getLessonImage(lesson) {
  if (generatedThumbs.has(lesson.day)) return generatedThumbs.get(lesson.day);
  if (lesson.day > 6) return "";
  const safeTitle = lesson.title.replace(/\//g, "");
  return `html/assets/阶段1基础科学/day${String(lesson.day).padStart(2, "0")}-${safeTitle}.png`;
}

function getCategory(title) {
  if (/骨骼肌|肌|本体感觉|收缩|GTO|肌梭/.test(title)) return "肌肉";
  if (/骨|关节|动作平面|运动轴/.test(title)) return "骨关节";
  if (/力|杠杆|脊柱|损伤|动作模式/.test(title)) return "生物力学";
  if (/能量|心肺|神经肌肉|兴奋/.test(title)) return "能量系统";
  if (/训练|热身|柔韧|速度|敏捷|爆发|核心|平衡|周期/.test(title)) return "训练技术";
  if (/评估|筛查|姿势|纠正|综合征|CES/.test(title)) return "评估纠正";
  if (/营养|碳水|蛋白|脂肪|维生素|水合|补剂|体重/.test(title)) return "营养";
  if (/模考|考试|错题|冲刺|收官/.test(title)) return "模考";
  return "训练技术";
}

function bindUI() {
  $("atlasImage").addEventListener("load", syncHotspotLayer);
  window.addEventListener("resize", syncHotspotLayer);
  $("theoryTab").addEventListener("click", () => setTab("theory"));
  $("exerciseTab").addEventListener("click", () => setTab("exercise"));
  $("nutritionTab").addEventListener("click", () => setTab("nutrition"));
  $("headerAction").addEventListener("click", (event) => {
    if ($("headerAction").dataset.view !== "review") return;
    event.preventDefault();
    setTab("review");
  });
  document.querySelectorAll("[data-exercise-view]").forEach((button) => {
    button.addEventListener("click", () => {
      state.exerciseView = button.dataset.exerciseView;
      saveNavigation();
      render();
      pulseSelection(button);
    });
  });
  document.querySelectorAll("[data-atlas-view]").forEach((button) => {
    button.addEventListener("click", () => {
      state.atlasView = button.dataset.atlasView;
      const firstMuscle = muscles.find((muscle) => muscle.view === state.atlasView);
      state.selectedMuscle = firstMuscle?.id || state.selectedMuscle;
      saveNavigation();
      render();
      pulseSelection(button);
    });
  });
  $("exerciseSearch").addEventListener("input", (event) => {
    state.exerciseQuery = event.target.value.trim();
    renderExerciseLibrary();
  });
  $("exercisePatternFilters").addEventListener("click", (event) => {
    const button = event.target.closest("[data-exercise-pattern]");
    if (!button) return;
    state.exercisePattern = button.dataset.exercisePattern;
    renderExerciseLibrary();
    pulseSelection(document.querySelector(`[data-exercise-pattern="${state.exercisePattern}"]`));
  });
  $("exerciseMuscleFilters").addEventListener("click", (event) => {
    const button = event.target.closest("[data-exercise-muscle]");
    if (!button) return;
    state.exerciseMuscle = button.dataset.exerciseMuscle;
    renderExerciseLibrary();
    pulseSelection(document.querySelector(`[data-exercise-muscle="${state.exerciseMuscle}"]`));
  });
  $("exerciseEquipmentFilters").addEventListener("click", (event) => {
    const button = event.target.closest("[data-exercise-equipment]");
    if (!button) return;
    state.exerciseEquipment = button.dataset.exerciseEquipment;
    renderExerciseLibrary();
    pulseSelection(document.querySelector(`[data-exercise-equipment="${state.exerciseEquipment}"]`));
  });
  $("exerciseCards").addEventListener("click", (event) => {
    const card = event.target.closest("[data-exercise-id]");
    if (!card) return;
    state.selectedExercise = card.dataset.exerciseId;
    saveNavigation();
    renderExerciseLibrary();
    jellySelection(document.querySelector(`[data-exercise-id="${state.selectedExercise}"]`));
  });
  $("searchInput").addEventListener("input", (event) => {
    state.query = event.target.value.trim();
    $("clearSearch").classList.toggle("visible", Boolean(state.query));
    render();
  });
  $("clearSearch").addEventListener("click", () => {
    state.query = "";
    $("searchInput").value = "";
    $("clearSearch").classList.remove("visible");
    render();
  });
  $("phaseFilter").addEventListener("change", (event) => {
    state.phase = event.target.value;
    render();
  });
  $("resetFilters").addEventListener("click", resetFilters);
  document.querySelectorAll("[data-close-modal]").forEach((node) => node.addEventListener("click", closeModal));
  document.querySelectorAll("[data-close-coaching-visual]").forEach((node) => node.addEventListener("click", closeCoachingVisual));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeModal();
      closeCoachingVisual();
    }
  });

  renderFilterControls();
}

function setTab(tab) {
  const fromTab = state.visibleTab;
  if (tab === state.tab && !state.tabTransitionTimer) return;

  if (state.tabTransitionTimer) window.clearTimeout(state.tabTransitionTimer);
  state.tab = tab;
  if (tab === "review") loadReviews();
  saveNavigation();
  updateTabSelection(tab, tab !== fromTab);

  if (tab === fromTab) {
    const panel = panelForTab(fromTab);
    panel.classList.remove("tab-panel-leave-forward", "tab-panel-leave-backward");
    state.tabTransitionTimer = null;
    render();
    return;
  }

  const direction = tabDirection(fromTab, tab);
  const outgoingPanel = panelForTab(fromTab);
  outgoingPanel.classList.remove("tab-panel-enter-forward", "tab-panel-enter-backward", "tab-panel-leave-forward", "tab-panel-leave-backward");
  outgoingPanel.classList.add(`tab-panel-leave-${direction}`);
  state.tabTransitionTimer = window.setTimeout(() => {
    outgoingPanel.classList.remove(`tab-panel-leave-${direction}`);
    state.tabTransitionTimer = null;
    render(direction);
    state.visibleTab = state.tab;
  }, 170);
}

function panelForTab(tab) {
  return $(tab === "theory" ? "cardGrid" : tab === "review" ? "reviewGrid" : tab === "nutrition" ? "nutritionPanel" : "exercisePanel");
}

function tabDirection(fromTab, toTab) {
  const tabOrder = { theory: 0, review: 0, exercise: 1, nutrition: 2 };
  return tabOrder[toTab] >= tabOrder[fromTab] ? "forward" : "backward";
}

function updateTabSelection(tab, animate = false) {
  const tabs = document.querySelector(".tabs");
  $("theoryTab").classList.toggle("active", tab === "theory");
  $("exerciseTab").classList.toggle("active", tab === "exercise");
  $("nutritionTab").classList.toggle("active", tab === "nutrition");
  tabs.dataset.active = tab;

  if (animate && tab !== "review") {
    tabs.classList.remove("is-jelly");
    void tabs.offsetWidth;
    tabs.classList.add("is-jelly");
  }
}

function renderFilterControls() {
  $("certFilters").innerHTML = ["全部", "双证", "NSCA", "NASM"].map((cert) => chip("cert", cert, state.cert)).join("");
  $("categoryFilters").innerHTML = categories.map((category) => chip("category", category, state.category)).join("");
  $("phaseFilter").innerHTML = ["全部", ...state.phases.map((phase) => phase.name)]
    .map((phase) => `<option value="${phase}">${phase === "全部" ? "全部阶段" : phase}</option>`)
    .join("");

  $("certFilters").addEventListener("click", (event) => {
    const button = event.target.closest("[data-cert]");
    if (!button) return;
    state.cert = button.dataset.cert;
    render();
    pulseSelection(button);
  });
  $("categoryFilters").addEventListener("click", (event) => {
    const button = event.target.closest("[data-category]");
    if (!button) return;
    state.category = button.dataset.category;
    render();
    pulseSelection(button);
  });
}

function chip(kind, value, active) {
  return `<button class="chip ${value === active ? "active" : ""}" type="button" data-${kind}="${value}">${value}</button>`;
}

function pulseSelection(control) {
  if (!control) return;
  control.classList.remove("selection-pop");
  void control.offsetWidth;
  control.classList.add("selection-pop");
}

function jellySelection(control) {
  if (!control) return;
  control.classList.remove("is-jelly");
  void control.offsetWidth;
  control.classList.add("is-jelly");
}

function resetFilters() {
  state.cert = "全部";
  state.phase = "全部";
  state.category = "全部";
  state.query = "";
  $("searchInput").value = "";
  $("clearSearch").classList.remove("visible");
  render();
}

function filteredLessons() {
  const query = state.query.toLowerCase();
  return state.lessons.filter((lesson) => {
    const certOk = state.cert === "全部" || lesson.cert.includes(state.cert);
    const phaseOk = state.phase === "全部" || lesson.phase === state.phase;
    const categoryOk = state.category === "全部" || lesson.category === state.category;
    const text = [lesson.day, lesson.title, lesson.cert, lesson.phase, lesson.category, lesson.goal, ...lesson.points].join(" ").toLowerCase();
    const queryOk = !query || text.includes(query);
    return certOk && phaseOk && categoryOk && queryOk;
  }).sort((a, b) => {
    if (a.day === state.currentDay) return -1;
    if (b.day === state.currentDay) return 1;
    return a.day - b.day;
  });
}

function render(enterDirection = "") {
  const lessons = filteredLessons();
  const reviews = filteredReviews();
  renderFilterState();

  const theoryMode = state.tab === "theory";
  const reviewMode = state.tab === "review";
  const nutritionMode = state.tab === "nutrition";
  const exerciseMode = state.tab === "exercise";
  updateTabSelection(state.tab);
  $("cardGrid").hidden = !theoryMode;
  $("reviewGrid").hidden = !reviewMode;
  $("nutritionPanel").hidden = !nutritionMode;
  $("exercisePanel").hidden = !exerciseMode;
  $("resultBar").hidden = !theoryMode;
  $("resetFilters").hidden = !theoryMode;
  renderMainHeader();
  renderSidebarContext();

  if (theoryMode) renderCards(lessons);
  if (reviewMode) renderReviews(reviews);
  if (exerciseMode) renderExercise();
  if (theoryMode) $("resultText").textContent = `找到 ${lessons.length} 个理论主题`;

  if (enterDirection) {
    const activePanel = theoryMode ? $("cardGrid") : reviewMode ? $("reviewGrid") : nutritionMode ? $("nutritionPanel") : $("exercisePanel");
    const enterClass = `tab-panel-enter-${enterDirection}`;
    activePanel.classList.remove("tab-panel-enter-forward", "tab-panel-enter-backward");
    requestAnimationFrame(() => activePanel.classList.add(enterClass));
  }
}

function renderSidebarContext() {
  const theoryMode = state.tab === "theory";
  $("theorySidebarControls").hidden = !theoryMode;
  $("pendingSidebarControls").hidden = theoryMode;
  if (theoryMode) return;

  const pendingCopy = {
    exercise: ["功能待开发", "更多动作学习功能正在开发中。"],
    nutrition: ["功能待开发", "更多营养工具正在开发中。"],
    review: ["功能待开发", "更多复习工具正在开发中。"],
  }[state.tab];
  $("pendingSidebarTitle").textContent = pendingCopy[0];
  $("pendingSidebarDescription").textContent = pendingCopy[1];
}

function renderMainHeader() {
  const header = {
    theory: {
      kicker: "112 Day Library",
      title: "健身知识库",
      description: "按理论、证书、阶段和主题检索；已有详情页可直接弹窗阅读。",
      action: "复习",
      href: "#reviewGrid",
      view: "review",
      insight: `<span>课程总览</span><strong>${state.lessons.length} <small>主题</small></strong>`,
    },
    review: {
      kicker: "Review Library",
      title: "复习",
      description: "全部复习页，按学习节奏回顾核心知识。",
      insight: `<span>已生成</span><strong>${state.reviews.length} <small>复习页</small></strong>`,
    },
    exercise: {
      kicker: "Training Lab",
      title: "健身动作",
      description: "通过肌肉图谱和动作库，建立训练动作与解剖知识的连接。",
      insight: state.exerciseView === "atlas"
        ? `<span>当前浏览</span><strong>肌肉 <small>${state.atlasView === "front" ? "正面" : "背面"}</small></strong>`
        : (() => {
            const exercise = exercises.find((item) => item.id === state.selectedExercise);
            return exercise
              ? `<span>当前查看</span><strong>${exercise.name}<small>${exercise.pattern} · ${exercise.level}</small></strong>`
              : `<span>当前查看</span><strong>动作库</strong>`;
          })(),
    },
    nutrition: {
      kicker: "Nutrition Library",
      title: "营养学",
      description: "",
      insight: `<span>能量速查</span><strong>4 · 4 · 9 <small>kcal/g</small></strong>`,
    },
  }[state.tab];

  $("headerKicker").textContent = header.kicker;
  $("headerTitle").textContent = header.title;
  $("headerDescription").textContent = header.description;
  $("headerDescription").hidden = !header.description;
  $("headerInsight").innerHTML = header.insight;
  $("headerAction").hidden = !header.action;
  if (header.action) {
    $("headerAction").textContent = header.action;
    $("headerAction").href = header.href;
    $("headerAction").dataset.view = header.view || "";
  } else {
    delete $("headerAction").dataset.view;
  }
}

function renderFilterState() {
  $("phaseFilter").value = state.phase;
  $("certFilters").innerHTML = ["全部", "双证", "NSCA", "NASM"].map((cert) => chip("cert", cert, state.cert)).join("");
  $("categoryFilters").innerHTML = categories.map((category) => chip("category", category, state.category)).join("");
}

function renderCards(lessons) {
  $("cardGrid").innerHTML = lessons
    .map((lesson) => {
      const hasPage = publishedPages.has(lesson.day);
      return `
        <article class="lesson-card" data-day="${lesson.day}">
          <div class="thumb ${lesson.image ? "has-image" : "no-image"}">
            ${
              lesson.image
                ? `<img src="${lesson.image}" alt="${lesson.title}缩略图" loading="lazy">`
                : `<div class="thumb-placeholder"><span>Day ${lesson.day}</span><b>${lesson.category}</b></div>`
            }
          </div>
          <div class="card-top">
            <span class="day-pill">Day ${lesson.day}</span>
            <span class="cert-badge cert-${lesson.cert === "NSCA" ? "blue" : lesson.cert === "NASM" ? "green" : "orange"}">${lesson.cert}</span>
          </div>
          <h2>${lesson.title}</h2>
          <div class="phase-line">${lesson.phase}</div>
          <div class="card-footer">
            <span class="tag tag-green">${lesson.category}</span>
            <span class="tag ${hasPage ? "tag-blue" : "tag-muted"}">${hasPage ? "详情" : "摘要"}</span>
            <button class="card-action" type="button">查看</button>
          </div>
        </article>
      `;
    })
    .join("");

  $("cardGrid").onclick = (event) => {
    const card = event.target.closest(".lesson-card");
    if (!card) return;
    openLesson(Number(card.dataset.day));
  };
}

function filteredReviews() {
  const query = state.query.toLowerCase();
  return state.reviews.filter((review) => {
    const text = [
      review.day,
      review.title,
      review.summary,
      review.path,
      ...(review.items || []).flatMap((item) => [item.type, item.day, item.label]),
    ]
      .join(" ")
      .toLowerCase();
    return !query || text.includes(query);
  });
}

function renderReviews(reviews) {
  $("reviewGrid").innerHTML = reviews
    .map((review) => {
      const items = review.items || [];
      return `
        <article class="review-card" data-day="${review.day}">
          <div class="review-card-head">
            <span class="day-pill">Day ${review.day}</span>
            <span class="cert-badge cert-blue">${items.length} 组复习</span>
          </div>
          <h2>${review.title}</h2>
          <p>${review.summary || "按艾宾浩斯节奏回忆当天与历史知识点。"}</p>
          <div class="review-slots">
            ${items
              .map(
                (item) => `
                  <span>
                    <b>${item.type}</b>
                    ${item.label} · Day ${item.day}
                  </span>
                `,
              )
              .join("")}
          </div>
          <div class="card-footer">
            <span class="tag tag-blue">复习</span>
            <span class="tag tag-green">艾宾浩斯</span>
            <button class="card-action" type="button">查看</button>
          </div>
        </article>
      `;
    })
    .join("");

  $("reviewGrid").onclick = (event) => {
    const card = event.target.closest(".review-card");
    if (!card) return;
    openReview(Number(card.dataset.day));
  };
}

function renderExercise() {
  document.querySelectorAll("[data-exercise-view]").forEach((button) => {
    button.classList.toggle("active", button.dataset.exerciseView === state.exerciseView);
    button.setAttribute("aria-selected", String(button.dataset.exerciseView === state.exerciseView));
  });
  $("muscleAtlas").hidden = state.exerciseView !== "atlas";
  $("exerciseLibrary").hidden = state.exerciseView !== "library";

  if (state.exerciseView === "atlas") renderMuscleAtlas();
  if (state.exerciseView === "library") renderExerciseLibrary();
}

function libraryChip(kind, value, active) {
  const attr = `exercise-${kind}`;
  return `<button class="library-chip ${value === active ? "active" : ""}" type="button" data-${attr}="${value}">${value}</button>`;
}

function filteredExercises() {
  const query = state.exerciseQuery.toLowerCase();
  return exercises.filter((exercise) => {
    const patternOk = state.exercisePattern === "全部" || exercise.pattern === state.exercisePattern;
    const muscleOk = state.exerciseMuscle === "全部" || [...exercise.muscles, ...exercise.support].includes(state.exerciseMuscle);
    const equipmentOk = state.exerciseEquipment === "全部" || exercise.equipment === state.exerciseEquipment;
    const text = [exercise.name, exercise.english, exercise.pattern, exercise.equipment, exercise.level, ...exercise.muscles, ...exercise.support].join(" ").toLowerCase();
    return patternOk && muscleOk && equipmentOk && (!query || text.includes(query));
  });
}

function renderExerciseLibrary() {
  const patterns = ["全部", ...new Set(exercises.map((exercise) => exercise.pattern))];
  const exerciseMuscles = ["全部", ...new Set(exercises.flatMap((exercise) => [...exercise.muscles, ...exercise.support]))];
  const equipment = ["全部", ...new Set(exercises.map((exercise) => exercise.equipment))];
  const filtered = filteredExercises();
  if (!filtered.some((exercise) => exercise.id === state.selectedExercise)) {
    state.selectedExercise = filtered[0]?.id || exercises[0].id;
  }
  const selected = exercises.find((exercise) => exercise.id === state.selectedExercise) || exercises[0];
  $("exercisePatternFilters").innerHTML = patterns.map((pattern) => libraryChip("pattern", pattern, state.exercisePattern)).join("");
  $("exerciseMuscleFilters").innerHTML = exerciseMuscles.map((muscle) => libraryChip("muscle", muscle, state.exerciseMuscle)).join("");
  $("exerciseEquipmentFilters").innerHTML = equipment.map((item) => libraryChip("equipment", item, state.exerciseEquipment)).join("");
  $("exerciseCount").textContent = `${filtered.length} 个动作`;
  $("exerciseCards").innerHTML = filtered.map((exercise) => `
    <button class="exercise-card ${exercise.id === selected.id ? "active" : ""}" type="button" data-exercise-id="${exercise.id}" aria-pressed="${exercise.id === selected.id}">
      <span class="exercise-card-mark">${exercise.pattern.slice(0, 2)}</span>
      <span class="exercise-card-copy"><strong>${exercise.name}</strong><small>${exercise.pattern} · ${exercise.equipment}</small></span>
      <span class="exercise-card-level">${exercise.level}</span>
    </button>
  `).join("") || `<div class="exercise-empty">没有匹配动作</div>`;
  const hasMedia = Boolean(selected.media);
  $("exerciseDetail").innerHTML = `
    <div class="detail-media ${hasMedia ? "has-media" : ""} ${selected.media?.endsWith(".gif") ? "is-animation" : ""}">
      ${hasMedia ? `<img id="exerciseMedia" src="${selected.media}" alt="${selected.name}动作演示" />` : `<div class="detail-media-placeholder"><span>${selected.pattern}</span><strong>${selected.name}</strong><small>演示素材待接入</small></div>`}
      <span class="detail-level">${selected.level}</span>
    </div>
    <div class="exercise-detail-body">
      <div class="exercise-title-row"><div><div class="detail-overline">${selected.pattern} · ${selected.equipment}</div><h2>${selected.name}</h2><p>${selected.english}</p></div></div>
      <section class="muscle-summary"><div><span>主练</span><strong>${selected.muscles.join(" · ")}</strong></div><div><span>协同</span><strong>${selected.support.join(" · ")}</strong></div></section>
      ${hasMedia ? `<section class="phase-section"><div class="section-label">动作阶段</div><div class="phase-row" id="phaseRow">${selected.phases.map((phase, index) => `<button class="phase-button ${index === 0 ? "active" : ""}" type="button" data-frame-index="${index}"><span>${String(index + 1).padStart(2, "0")}</span>${phase}</button>`).join("")}</div></section>` : ""}
      <div class="coaching-grid"><section><div class="section-label">关键提示</div><ul>${selected.cues.map((cue) => `<li>${cue}</li>`).join("")}</ul></section><section><div class="section-label">常见错误</div>${renderMistakes(selected.mistakes, selected.coachingVisuals?.mistakes)}</section></div>
    </div>
  `;
  if (hasMedia) {
    $("phaseRow").onclick = (event) => {
      const button = event.target.closest("[data-frame-index]");
      if (!button) return;
      const index = Number(button.dataset.frameIndex);
      $("exerciseMedia").src = selected.frames[index];
      document.querySelectorAll(".phase-button").forEach((item) => item.classList.toggle("active", item === button));
      pulseSelection(button);
    };
  }
  $("exerciseDetail").onclick = (event) => {
    const visual = event.target.closest("[data-coaching-visual]");
    if (!visual) return;
    openCoachingVisual(visual.dataset.coachingVisual, visual.dataset.coachingTitle, visual.dataset.coachingAlt);
  };
  renderMainHeader();
}

function renderMistakes(mistakes, visuals = []) {
  return `<ul class="mistake-list">${mistakes.map((mistake) => {
    const visual = visuals.find((item) => item.title === mistake);
    if (!visual) return `<li>${mistake}</li>`;
    return `<li class="mistake-item"><button type="button" data-coaching-visual="${visual.src}" data-coaching-title="${visual.title}" data-coaching-alt="${visual.alt}" aria-label="查看${visual.title}错误示意图"><span>${mistake}</span><b aria-hidden="true">↗</b><span class="mistake-preview"><img src="${visual.src}" alt="" /><span><strong>${visual.title}</strong><small>${visual.description}</small></span></span></button></li>`;
  }).join("")}</ul>`;
}

function openCoachingVisual(src, title, alt) {
  $("coachingVisualTitle").textContent = title;
  $("coachingVisualImage").src = src;
  $("coachingVisualImage").alt = alt;
  $("coachingVisualModal").classList.add("open");
  $("coachingVisualModal").setAttribute("aria-hidden", "false");
}

function closeCoachingVisual() {
  $("coachingVisualModal").classList.remove("open");
  $("coachingVisualModal").setAttribute("aria-hidden", "true");
  $("coachingVisualImage").removeAttribute("src");
}

function renderMuscleAtlas() {
  document.querySelectorAll("[data-atlas-view]").forEach((button) => {
    button.classList.toggle("active", button.dataset.atlasView === state.atlasView);
  });
  $("atlasImage").src = atlasImages[state.atlasView];
  $("atlasImage").alt = `全身肌肉${state.atlasView === "front" ? "正面" : "背面"}图谱`;

  // 图谱只作视觉参考，暂不显示未经逐点校准的交互热点。
  $("hotspotLayer").replaceChildren();
  $("hotspotLayer").onclick = null;
  $("muscleDetail").hidden = true;
  document.querySelector(".atlas-layout").classList.add("atlas-static");
  syncHotspotLayer();
}

function syncHotspotLayer() {
  const figure = $("atlasFigure");
  const image = $("atlasImage");
  const layer = $("hotspotLayer");
  if (!figure || !image.complete || !image.naturalWidth) return;

  const figureBox = figure.getBoundingClientRect();
  const imageBox = image.getBoundingClientRect();
  layer.style.inset = "auto";
  layer.style.left = `${imageBox.left - figureBox.left - figure.clientLeft}px`;
  layer.style.top = `${imageBox.top - figureBox.top - figure.clientTop}px`;
  layer.style.width = `${imageBox.width}px`;
  layer.style.height = `${imageBox.height}px`;
}

function openReview(day) {
  const review = state.reviews.find((item) => item.day === day);
  if (!review) return;

  $("modalMeta").textContent = `Day ${review.day} · 艾宾浩斯复习区`;
  $("modalTitle").textContent = review.title;
  $("openPage").style.display = "inline-flex";
  $("openPage").href = review.path;
  $("modalBody").innerHTML = `<iframe src="${review.path}" title="${review.title}复习"></iframe>`;
  $("lessonModal").classList.add("open");
  $("lessonModal").setAttribute("aria-hidden", "false");
}

function openLesson(day) {
  const lesson = state.lessons.find((item) => item.day === day);
  if (!lesson) return;
  const page = publishedPages.get(day);

  $("modalMeta").textContent = `Day ${lesson.day} · ${lesson.phase} · ${lesson.cert}`;
  $("modalTitle").textContent = lesson.title;
  $("openPage").style.display = page ? "inline-flex" : "none";
  $("openPage").href = page || "#";

  if (page) {
    $("modalBody").innerHTML = `<iframe src="${page}" title="${lesson.title}"></iframe>`;
  } else {
    $("modalBody").innerHTML = `
      <div class="summary-view">
        <h3>阶段目标</h3>
        <p>${lesson.goal || "按总纲推进本主题。"}</p>
        <h3>核心要点</h3>
        <ul>${lesson.points.map((point) => `<li>${point}</li>`).join("")}</ul>
        <h3>晚间应用</h3>
        <div class="practice-box">${lesson.practice || "用一个训练动作解释本主题。"}</div>
      </div>
    `;
  }

  $("lessonModal").classList.add("open");
  $("lessonModal").setAttribute("aria-hidden", "false");
}

function closeModal() {
  $("lessonModal").classList.remove("open");
  $("lessonModal").setAttribute("aria-hidden", "true");
  $("modalBody").innerHTML = "";
}

init().catch((error) => {
  console.error(error);
  $("resultText").textContent = "载入失败。请通过本地服务打开项目。";
});
