const state = {
  lessons: [],
  reviews: [],
  phases: [],
  tab: "theory",
  cert: "全部",
  phase: "全部",
  category: "全部",
  query: "",
  exerciseView: "atlas",
  atlasView: "front",
  selectedMuscle: "front-left-deltoid",
};

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
]);

const categories = ["全部", "骨关节", "肌肉", "生物力学", "能量系统", "训练技术", "评估纠正", "营养", "模考"];
const $ = (id) => document.getElementById(id);

const atlasImages = {
  front: "html/assets/muscle-atlas-front.png",
  back: "html/assets/muscle-atlas-back.png",
};

const atlasLessons = ["Day 4 关节运动学", "Day 5 动作平面", "Day 6 肌肉收缩"];

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
  const [markdown, reviews] = await Promise.all([
    fetch("fitness_syllabus.md").then((response) => response.text()),
    fetch("reviews.json")
      .then((response) => (response.ok ? response.json() : []))
      .catch(() => []),
  ]);
  state.reviews = reviews;
  parseSyllabus(markdown);
  bindUI();
  render();
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
  $("reviewTab").addEventListener("click", () => setTab("review"));
  $("exerciseTab").addEventListener("click", () => setTab("exercise"));
  document.querySelectorAll("[data-exercise-view]").forEach((button) => {
    button.addEventListener("click", () => {
      state.exerciseView = button.dataset.exerciseView;
      render();
    });
  });
  document.querySelectorAll("[data-atlas-view]").forEach((button) => {
    button.addEventListener("click", () => {
      state.atlasView = button.dataset.atlasView;
      const firstMuscle = muscles.find((muscle) => muscle.view === state.atlasView);
      state.selectedMuscle = firstMuscle?.id || state.selectedMuscle;
      render();
    });
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
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeModal();
  });

  renderFilterControls();
}

function setTab(tab) {
  state.tab = tab;
  $("theoryTab").classList.toggle("active", tab === "theory");
  $("reviewTab").classList.toggle("active", tab === "review");
  $("exerciseTab").classList.toggle("active", tab === "exercise");
  render();
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
  });
  $("categoryFilters").addEventListener("click", (event) => {
    const button = event.target.closest("[data-category]");
    if (!button) return;
    state.category = button.dataset.category;
    render();
  });
}

function chip(kind, value, active) {
  return `<button class="chip ${value === active ? "active" : ""}" type="button" data-${kind}="${value}">${value}</button>`;
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
  });
}

function render() {
  const lessons = filteredLessons();
  const reviews = filteredReviews();
  renderFilterState();

  const theoryMode = state.tab === "theory";
  const reviewMode = state.tab === "review";
  const exerciseMode = state.tab === "exercise";
  $("cardGrid").hidden = !theoryMode;
  $("reviewGrid").hidden = !reviewMode;
  $("exercisePanel").hidden = !exerciseMode;
  renderMainHeader();

  if (theoryMode) renderCards(lessons);
  if (reviewMode) renderReviews(reviews);
  if (exerciseMode) renderExercise();
  $("resultText").textContent = theoryMode
    ? `找到 ${lessons.length} 个理论主题`
    : reviewMode
      ? `找到 ${reviews.length} 个复习包`
      : state.exerciseView === "atlas"
        ? `肌肉图谱 · ${state.atlasView === "front" ? "正面" : "背面"}`
        : "健身动作库待补";
}

function renderMainHeader() {
  const header = {
    theory: {
      kicker: "112 Day Library",
      title: "健身知识库",
      description: "按理论、证书、阶段和主题检索；已有详情页可直接弹窗阅读。",
      action: "最新复习",
      href: "html/review-day20-运动损伤的力学机制.html",
    },
    review: {
      kicker: "Weekly Review",
      title: "复习资料",
      description: "按周回顾核心概念、错题要点和训练实践。",
      action: "查看理论",
      href: "#cardGrid",
    },
    exercise: {
      kicker: "Training Lab",
      title: "健身动作",
      description: "通过肌肉图谱和动作库，建立训练动作与解剖知识的连接。",
      action: "肌肉图谱",
      href: "#muscleAtlas",
    },
  }[state.tab];

  $("headerKicker").textContent = header.kicker;
  $("headerTitle").textContent = header.title;
  $("headerDescription").textContent = header.description;
  $("headerAction").textContent = header.action;
  $("headerAction").href = header.href;
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
  });
  $("muscleAtlas").hidden = state.exerciseView !== "atlas";
  $("exerciseLibrary").hidden = state.exerciseView !== "library";

  if (state.exerciseView === "atlas") renderMuscleAtlas();
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
