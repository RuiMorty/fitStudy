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
  selectedMuscle: "pectoralis",
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
]);

const categories = ["全部", "骨关节", "肌肉", "生物力学", "能量系统", "训练技术", "评估纠正", "营养", "模考"];
const $ = (id) => document.getElementById(id);

const atlasImages = {
  front: "html/assets/muscle-atlas-front.png",
  back: "html/assets/muscle-atlas-back.png",
};

const muscles = [
  {
    id: "front-shoulder",
    view: "front",
    name: "肩部",
    region: "上肢",
    x: 38,
    y: 24,
    function: "肩关节外展、屈曲、水平推拉和上肢稳定。",
    children: ["三角肌前束", "三角肌中束", "胸大肌锁骨部", "肩袖肌群"],
    training: ["肩推", "侧平举", "上斜推"],
    signs: "观察肩胛是否耸肩、肱骨头是否前移，推举类动作先看肩胛上回旋。",
    lessons: ["Day 4 关节运动学", "Day 8 本体感觉"],
  },
  {
    id: "front-chest",
    view: "front",
    name: "胸部",
    region: "躯干前侧",
    x: 50,
    y: 29,
    function: "肩水平内收、肩内旋、推类动作主要发力。",
    children: ["胸大肌锁骨部", "胸大肌胸肋部", "胸小肌", "前锯肌"],
    training: ["卧推", "俯卧撑", "哑铃飞鸟"],
    signs: "胸小肌紧张可能限制肩胛后倾和上回旋，影响上举和推举。",
    lessons: ["Day 4 关节运动学", "Day 5 动作平面"],
  },
  {
    id: "front-upper-arm",
    view: "front",
    name: "大臂",
    region: "上肢",
    x: 36,
    y: 40,
    function: "肘屈伸和肩关节辅助稳定。",
    children: ["肱二头肌", "肱肌", "肱桡肌", "肱三头肌内侧头"],
    training: ["弯举", "引体向上", "臂屈伸"],
    signs: "弯举时避免肩前移和躯干后仰，用肘关节主导动作。",
    lessons: ["Day 5 运动轴", "Day 6 肌丝滑行"],
  },
  {
    id: "front-forearm",
    view: "front",
    name: "小臂",
    region: "上肢",
    x: 32,
    y: 54,
    function: "腕屈伸、旋前旋后、握力和器械控制。",
    children: ["旋前圆肌", "腕屈肌群", "肱桡肌", "掌长肌"],
    training: ["农夫走", "腕弯举", "反握弯举"],
    signs: "握力不足会限制拉类动作表现，前臂过紧也会影响肘腕舒适度。",
    lessons: ["Day 4 关节运动学", "Day 8 感觉反馈"],
  },
  {
    id: "front-abdomen",
    view: "front",
    name: "腹部",
    region: "核心",
    x: 50,
    y: 45,
    function: "躯干抗伸展、抗旋转、腹压维持和骨盆位置控制。",
    children: ["腹直肌", "腹外斜肌", "腹内斜肌", "腹横肌"],
    training: ["死虫", "平板支撑", "Pallof Press"],
    signs: "核心训练重点不是只卷腹，而是让肋骨、骨盆和腰椎保持可控。",
    lessons: ["Day 5 动作平面", "Day 6 肌肉收缩"],
  },
  {
    id: "front-thigh",
    view: "front",
    name: "大腿前侧",
    region: "下肢",
    x: 48,
    y: 67,
    function: "膝伸展、髋屈曲辅助，下蹲和起身主要输出区。",
    children: ["股直肌", "股外侧肌", "股内侧肌", "缝匠肌", "内收肌群"],
    training: ["深蹲", "腿举", "腿屈伸"],
    signs: "膝内扣或下蹲不稳时，同时看股四头肌、髋控制和足踝活动度。",
    lessons: ["Day 3 关节分类", "Day 5 运动轴"],
  },
  {
    id: "front-calf",
    view: "front",
    name: "小腿前外侧",
    region: "下肢",
    x: 48,
    y: 84,
    function: "踝背屈、足弓控制、落地缓冲和步态稳定。",
    children: ["胫骨前肌", "腓骨长肌", "趾长伸肌", "拇长伸肌"],
    training: ["提踵", "胫骨前肌抬脚", "跳绳"],
    signs: "踝背屈不足会影响深蹲深度、跑步落地和膝盖轨迹。",
    lessons: ["Day 4 运动学", "Day 8 本体感觉"],
  },
  {
    id: "back-back",
    view: "back",
    name: "背部",
    region: "躯干后侧",
    x: 50,
    y: 33,
    function: "肩胛稳定、肩伸展内收、脊柱伸展和抗屈曲。",
    children: ["斜方肌", "菱形肌", "背阔肌", "竖脊肌", "冈下肌", "大圆肌"],
    training: ["引体向上", "划船", "面拉"],
    signs: "背部训练不只看拉起重量，还要看肩胛后缩、下压和胸椎伸展。",
    lessons: ["Day 4 关节运动学", "Day 6 肌肉收缩"],
  },
  {
    id: "back-glutes",
    view: "back",
    name: "臀部",
    region: "髋部",
    x: 46,
    y: 57,
    function: "髋伸展、外旋、骨盆稳定和下肢发力传递。",
    children: ["臀大肌", "臀中肌", "梨状肌", "深层外旋肌群"],
    training: ["硬拉", "臀桥", "保加利亚分腿蹲"],
    signs: "臀部发力差时，腰椎和腘绳肌常会代偿，髋伸展动作尤其明显。",
    lessons: ["Day 4 髋关节运动", "Day 5 矢状面"],
  },
  {
    id: "back-thigh",
    view: "back",
    name: "大腿后侧",
    region: "下肢",
    x: 50,
    y: 70,
    function: "膝屈曲、髋伸展、跑跳减速和骨盆控制。",
    children: ["股二头肌", "半腱肌", "半膜肌", "髂胫束"],
    training: ["罗马尼亚硬拉", "腿弯举", "北欧腿弯举"],
    signs: "后侧链紧张感不一定等于短缩，也可能和骨盆位置、神经张力有关。",
    lessons: ["Day 5 动作轴", "Day 8 本体感觉"],
  },
  {
    id: "back-calf",
    view: "back",
    name: "小腿后侧",
    region: "下肢",
    x: 50,
    y: 84,
    function: "踝跖屈、弹跳、跑步推进和落地控制。",
    children: ["腓肠肌", "比目鱼肌", "腓骨短肌", "跟腱"],
    training: ["站姿提踵", "坐姿提踵", "跳绳"],
    signs: "腓肠肌跨膝，比目鱼肌不跨膝，膝伸直和屈曲提踵刺激不同。",
    lessons: ["Day 3 滑膜关节", "Day 6 收缩机制"],
  },
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
    .map((phase) => `<option value="${phase}">${phase}</option>`)
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

  const visibleMuscles = muscles.filter((muscle) => muscle.view === state.atlasView);
  if (!visibleMuscles.some((muscle) => muscle.id === state.selectedMuscle)) {
    state.selectedMuscle = visibleMuscles[0]?.id || state.selectedMuscle;
  }

  $("hotspotLayer").innerHTML = visibleMuscles
    .map(
      (muscle) => `
        <button
          class="muscle-hotspot ${muscle.id === state.selectedMuscle ? "active" : ""}"
          type="button"
          style="left:${muscle.x}%;top:${muscle.y}%"
          data-muscle="${muscle.id}"
          aria-label="${muscle.name}"
        >
          <span></span>
        </button>
      `,
    )
    .join("");

  $("hotspotLayer").onclick = (event) => {
    const button = event.target.closest("[data-muscle]");
    if (!button) return;
    state.selectedMuscle = button.dataset.muscle;
    renderMuscleAtlas();
  };

  const selected = muscles.find((muscle) => muscle.id === state.selectedMuscle) || visibleMuscles[0];
  $("muscleDetail").innerHTML = selected
    ? `
      <div class="detail-head">
        <span class="tag tag-blue">${selected.region}</span>
        <span class="tag tag-green">${state.atlasView === "front" ? "正面" : "背面"}</span>
      </div>
      <h2>${selected.name}</h2>
      <section>
        <h3>主要功能</h3>
        <p>${selected.function}</p>
      </section>
      <section>
        <h3>小肌肉细分</h3>
        <div class="submuscle-list">${selected.children.map((item) => `<span>${item}</span>`).join("")}</div>
      </section>
      <section>
        <h3>常见训练</h3>
        <div class="action-list">${selected.training.map((item) => `<span>${item}</span>`).join("")}</div>
      </section>
      <section>
        <h3>训练观察</h3>
        <p>${selected.signs}</p>
      </section>
      <section>
        <h3>相关理论</h3>
        <div class="lesson-links">${selected.lessons.map((item) => `<span>${item}</span>`).join("")}</div>
      </section>
    `
    : "";
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
