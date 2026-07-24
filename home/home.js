/* FitnessStudy home — DNA helix hero animation */
(() => {
  const canvas = document.getElementById("dna-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const ORANGE = [239, 102, 53];
  const MINT = [62, 208, 165];

  let w = 0;
  let h = 0;
  let t = Math.random() * Math.PI * 2;
  let mouseX = 0.5;
  let rafId = null;

  // Ambient particles, regenerated on resize.
  let particles = [];

  function resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    w = canvas.clientWidth;
    h = canvas.clientHeight;
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    particles = Array.from({ length: Math.round(w / 22) }, () => ({
      x: Math.random() * w,
      y: Math.random() * h,
      r: 0.6 + Math.random() * 1.6,
      s: 0.08 + Math.random() * 0.25,
      a: 0.05 + Math.random() * 0.16,
    }));
  }

  function rgba(rgb, a) {
    return `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${a})`;
  }

  function drawParticles() {
    for (const p of particles) {
      p.y -= p.s;
      if (p.y < -4) {
        p.y = h + 4;
        p.x = Math.random() * w;
      }
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = rgba(MINT, p.a);
      ctx.fill();
    }
  }

  function drawHelix() {
    const cx = w * 0.5 + (mouseX - 0.5) * 26;
    const top = h * 0.07;
    const span = h * 0.86;
    const amp = Math.min(w * 0.3, 168);
    const turns = 3.1;
    const rungs = 42;
    const pts = [];

    for (let i = 0; i <= rungs; i += 1) {
      const p = i / rungs;
      const y = top + p * span;
      const a = t + p * Math.PI * turns * 2;
      const s = Math.sin(a);
      const c = Math.cos(a); // depth of strand A, -1..1
      pts.push({ x: cx + s * amp, y, z: c, rgb: ORANGE, strand: "A" });
      pts.push({ x: cx - s * amp, y, z: -c, rgb: MINT, strand: "B" });
      pts.push({ rung: true, x1: cx + s * amp, x2: cx - s * amp, y, z: c });
    }

    // Painter's order: far points first.
    pts.sort((m, n) => m.z - n.z);

    for (const pt of pts) {
      const depth = (pt.z + 1) / 2; // 0 far, 1 near
      if (pt.rung) {
        const grad = ctx.createLinearGradient(pt.x1, pt.y, pt.x2, pt.y);
        grad.addColorStop(0, rgba(ORANGE, 0.05 + depth * 0.28));
        grad.addColorStop(0.5, rgba([255, 255, 255], 0.03 + depth * 0.1));
        grad.addColorStop(1, rgba(MINT, 0.05 + depth * 0.28));
        ctx.strokeStyle = grad;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(pt.x1, pt.y);
        ctx.lineTo(pt.x2, pt.y);
        ctx.stroke();
      } else {
        const r = 1.6 + depth * 3.4;
        ctx.shadowColor = rgba(pt.rgb, 0.9);
        ctx.shadowBlur = 6 + depth * 14;
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, r, 0, Math.PI * 2);
        ctx.fillStyle = rgba(pt.rgb, 0.35 + depth * 0.65);
        ctx.fill();
        ctx.shadowBlur = 0;
      }
    }
  }

  function frame() {
    ctx.clearRect(0, 0, w, h);
    drawParticles();
    drawHelix();
    t += 0.014;
    rafId = requestAnimationFrame(frame);
  }

  function still() {
    ctx.clearRect(0, 0, w, h);
    drawParticles();
    drawHelix();
  }

  resize();
  if (reduceMotion) {
    still();
  } else {
    frame();
    window.addEventListener("pointermove", (e) => {
      mouseX = e.clientX / window.innerWidth;
    }, { passive: true });
    // Pause when hero is off-screen.
    const io = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        if (rafId === null) rafId = requestAnimationFrame(frame);
      } else if (rafId !== null) {
        cancelAnimationFrame(rafId);
        rafId = null;
      }
    });
    io.observe(canvas);
  }
  window.addEventListener("resize", () => {
    resize();
    if (reduceMotion) still();
  });
})();
