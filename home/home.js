(() => {
  const canvas = document.getElementById('mouse-canvas');
  if (!canvas) return;

  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const paper = [243 / 255, 239 / 255, 236 / 255];
  const pointer = { id: null, x: 0, y: 0, targetX: 0, targetY: 0, ready: false, moved: false };
  const strokes = [];
  let fluid;
  let frameId = 0;
  let previousTime = 0;
  let lastInput = -Infinity;
  let width = 1;
  let height = 1;

  // A thin-film fluid cursor, matched to https://reapi.ai/models/face-swap.
  // Thickness controls interference colour; only the fluid's changing edges
  // catch light. Gravity carries the wisps down after the pointer passes.
  function createFluid() {
    const gl = canvas.getContext('webgl2', {
      alpha: false, antialias: false, depth: false, stencil: false,
      powerPreference: 'low-power',
    });
    if (!gl || !gl.getExtension('EXT_color_buffer_float')) return null;

    const linear = Boolean(gl.getExtension('OES_texture_float_linear'));
    const programs = [];
    let targets = [];
    let velocity;
    let ink;
    let pressure;
    let divergence;
    let curl;

    const vertexSource = `#version 300 es
      precision highp float;
      out vec2 uv;
      void main() {
        vec2 p = vec2(float((gl_VertexID << 1) & 2), float(gl_VertexID & 2));
        uv = p;
        gl_Position = vec4(p * 2.0 - 1.0, 0.0, 1.0);
      }
    `;

    function compile(type, source) {
      const shader = gl.createShader(type);
      gl.shaderSource(shader, source);
      gl.compileShader(shader);
      if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
        const message = gl.getShaderInfoLog(shader);
        gl.deleteShader(shader);
        throw new Error(message);
      }
      return shader;
    }

    const vertex = compile(gl.VERTEX_SHADER, vertexSource);

    function program(source, precision = 'highp') {
      const fragment = compile(gl.FRAGMENT_SHADER, `#version 300 es
        precision ${precision} float;
        precision ${precision} sampler2D;
        in highp vec2 uv;
        out vec4 result;
      ` + source);
      const handle = gl.createProgram();
      gl.attachShader(handle, vertex);
      gl.attachShader(handle, fragment);
      gl.linkProgram(handle);
      gl.deleteShader(fragment);
      if (!gl.getProgramParameter(handle, gl.LINK_STATUS)) {
        const message = gl.getProgramInfoLog(handle);
        gl.deleteProgram(handle);
        throw new Error(message);
      }
      const uniforms = {};
      const count = gl.getProgramParameter(handle, gl.ACTIVE_UNIFORMS);
      for (let i = 0; i < count; i += 1) {
        const name = gl.getActiveUniform(handle, i).name;
        uniforms[name] = gl.getUniformLocation(handle, name);
      }
      const item = { handle, uniforms };
      programs.push(item);
      return item;
    }

    const advect = program(`
      uniform sampler2D source;
      uniform sampler2D velocity;
      uniform vec2 velocityTexel;
      uniform vec2 sourceTexel;
      uniform float dt;
      uniform float decay;
      vec4 sampleField(sampler2D field, vec2 p, vec2 texel) {
        ${linear ? 'return texture(field, p);' : `
          vec2 grid = p / texel - 0.5;
          vec2 base = (floor(grid) + 0.5) * texel;
          vec2 f = fract(grid);
          return mix(mix(texture(field, base), texture(field, base + vec2(texel.x, 0.0)), f.x),
                     mix(texture(field, base + vec2(0.0, texel.y)), texture(field, base + texel), f.x), f.y);
        `}
      }
      void main() {
        vec2 flow = sampleField(velocity, uv, velocityTexel).xy;
        vec2 p = uv - dt * flow * velocityTexel;
        result = sampleField(source, p, sourceTexel) / (1.0 + decay * dt);
      }
    `);

    const splat = program(`
      uniform sampler2D source;
      uniform vec2 point;
      uniform vec2 aspect;
      uniform vec3 value;
      uniform float radius;
      void main() {
        vec2 p = (uv - point) * aspect;
        float drop = exp(-dot(p, p) / radius);
        vec3 field = texture(source, uv).xyz + drop * value;
        result = vec4(field, 1.0);
      }
    `);

    const curlProgram = program(`
      uniform sampler2D velocity;
      uniform vec2 texel;
      void main() {
        float l = texture(velocity, uv - vec2(texel.x, 0.0)).y;
        float r = texture(velocity, uv + vec2(texel.x, 0.0)).y;
        float b = texture(velocity, uv - vec2(0.0, texel.y)).x;
        float t = texture(velocity, uv + vec2(0.0, texel.y)).x;
        result = vec4(0.5 * (r - l - t + b), 0.0, 0.0, 1.0);
      }
    `, 'mediump');

    const vorticity = program(`
      uniform sampler2D velocity;
      uniform sampler2D curl;
      uniform vec2 texel;
      uniform float dt;
      void main() {
        float l = texture(curl, uv - vec2(texel.x, 0.0)).r;
        float r = texture(curl, uv + vec2(texel.x, 0.0)).r;
        float b = texture(curl, uv - vec2(0.0, texel.y)).r;
        float t = texture(curl, uv + vec2(0.0, texel.y)).r;
        float c = texture(curl, uv).r;
        vec2 force = 0.5 * vec2(abs(t) - abs(b), abs(l) - abs(r));
        force /= length(force) + 0.0001;
        force *= 8.0 * c;
        vec2 flow = texture(velocity, uv).xy + force * dt;
        result = vec4(clamp(flow, vec2(-1000.0), vec2(1000.0)), 0.0, 1.0);
      }
    `);

    const gravity = program(`
      uniform sampler2D velocity;
      uniform sampler2D ink;
      uniform float dt;
      void main() {
        vec2 flow = texture(velocity, uv).xy;
        flow.y -= 220.0 * min(texture(ink, uv).r, 1.5) * dt;
        result = vec4(flow, 0.0, 1.0);
      }
    `);

    const relaxPressure = program(`
      uniform sampler2D pressure;
      void main() {
        result = texture(pressure, uv) * 0.8;
      }
    `);

    const divergenceProgram = program(`
      uniform sampler2D velocity;
      uniform vec2 texel;
      void main() {
        vec2 c = texture(velocity, uv).xy;
        float l = texture(velocity, uv - vec2(texel.x, 0.0)).x;
        float r = texture(velocity, uv + vec2(texel.x, 0.0)).x;
        float b = texture(velocity, uv - vec2(0.0, texel.y)).y;
        float t = texture(velocity, uv + vec2(0.0, texel.y)).y;
        if (uv.x < texel.x) l = -c.x;
        if (uv.x > 1.0 - texel.x) r = -c.x;
        if (uv.y < texel.y) b = -c.y;
        if (uv.y > 1.0 - texel.y) t = -c.y;
        result = vec4(0.5 * (r - l + t - b), 0.0, 0.0, 1.0);
      }
    `, 'mediump');

    const pressureProgram = program(`
      uniform sampler2D pressure;
      uniform sampler2D divergence;
      uniform vec2 texel;
      void main() {
        float l = texture(pressure, uv - vec2(texel.x, 0.0)).r;
        float r = texture(pressure, uv + vec2(texel.x, 0.0)).r;
        float b = texture(pressure, uv - vec2(0.0, texel.y)).r;
        float t = texture(pressure, uv + vec2(0.0, texel.y)).r;
        float d = texture(divergence, uv).r;
        result = vec4((l + r + b + t - d) * 0.25, 0.0, 0.0, 1.0);
      }
    `, 'mediump');

    const gradient = program(`
      uniform sampler2D pressure;
      uniform sampler2D velocity;
      uniform vec2 texel;
      void main() {
        float l = texture(pressure, uv - vec2(texel.x, 0.0)).r;
        float r = texture(pressure, uv + vec2(texel.x, 0.0)).r;
        float b = texture(pressure, uv - vec2(0.0, texel.y)).r;
        float t = texture(pressure, uv + vec2(0.0, texel.y)).r;
        vec2 flow = texture(velocity, uv).xy - vec2(r - l, t - b);
        result = vec4(flow, 0.0, 1.0);
      }
    `, 'mediump');

    const display = program(`
      uniform sampler2D ink;
      uniform vec2 texel;
      uniform vec3 paper;
      void main() {
        float density = texture(ink, uv).r;
        float l = texture(ink, uv - vec2(texel.x, 0.0)).r;
        float r = texture(ink, uv + vec2(texel.x, 0.0)).r;
        float b = texture(ink, uv - vec2(0.0, texel.y)).r;
        float t = texture(ink, uv + vec2(0.0, texel.y)).r;
        float edge = length(vec2(r - l, t - b));
        float rim = pow(min(edge * 2.5, 1.0), 1.25);
        vec3 fringe = 0.5 + 0.5 * cos(6.2832 * density * 2.6 + vec3(0.0, 2.1, 4.2));
        fringe = pow(fringe, vec3(1.4));
        vec3 light = fringe * rim * 0.38 + vec3(pow(rim, 3.0) * 0.06)
                   + vec3(clamp(density, 0.0, 1.0) * 0.03);
        light = min(light, vec3(1.0));
        float alpha = clamp(max(light.r, max(light.g, light.b)), 0.0, 1.0);
        result = vec4(light + paper * (1.0 - alpha), 1.0);
      }
    `);
    gl.deleteShader(vertex);
    gl.disable(gl.BLEND);
    gl.disable(gl.DEPTH_TEST);

    function target(w, h, channels, filtered = false) {
      const texture = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, texture);
      const filter = filtered && linear ? gl.LINEAR : gl.NEAREST;
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, filter);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, filter);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.texImage2D(gl.TEXTURE_2D, 0, channels === 2 ? gl.RG16F : gl.R16F,
        w, h, 0, channels === 2 ? gl.RG : gl.RED, gl.HALF_FLOAT, null);
      const framebuffer = gl.createFramebuffer();
      gl.bindFramebuffer(gl.FRAMEBUFFER, framebuffer);
      gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, texture, 0);
      const item = { texture, framebuffer, width: w, height: h };
      targets.push(item);
      if (gl.checkFramebufferStatus(gl.FRAMEBUFFER) !== gl.FRAMEBUFFER_COMPLETE) {
        throw new Error('Floating-point fluid framebuffer is unavailable.');
      }
      gl.clearColor(0, 0, 0, 0);
      gl.clear(gl.COLOR_BUFFER_BIT);
      return item;
    }

    function pair(w, h, channels, filtered = true) {
      return {
        read: target(w, h, channels, filtered),
        write: target(w, h, channels, filtered),
        swap() { [this.read, this.write] = [this.write, this.read]; },
      };
    }

    function use(item, values) {
      gl.useProgram(item.handle);
      let unit = 0;
      for (const [name, value] of Object.entries(values)) {
        const location = item.uniforms[name];
        if (location == null) continue;
        if (value && value.texture) {
          gl.activeTexture(gl.TEXTURE0 + unit);
          gl.bindTexture(gl.TEXTURE_2D, value.texture);
          gl.uniform1i(location, unit++);
        } else if (Array.isArray(value)) {
          if (value.length === 2) gl.uniform2f(location, ...value);
          else gl.uniform3f(location, ...value);
        } else {
          gl.uniform1f(location, value);
        }
      }
    }

    function draw(destination) {
      gl.bindFramebuffer(gl.FRAMEBUFFER, destination ? destination.framebuffer : null);
      gl.viewport(0, 0, destination ? destination.width : canvas.width,
        destination ? destination.height : canvas.height);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
    }

    function releaseTargets() {
      for (const item of targets) {
        gl.deleteTexture(item.texture);
        gl.deleteFramebuffer(item.framebuffer);
      }
      targets = [];
    }

    function resolution(shortSide, limit) {
      const scale = Math.min(shortSide / Math.min(width, height), limit / Math.max(width, height));
      return [Math.max(2, Math.round(width * scale)), Math.max(2, Math.round(height * scale))];
    }

    return {
      resize() {
        releaseTargets();
        const [sw, sh] = resolution(128, 512);
        const [iw, ih] = resolution(1024, 4096);
        velocity = pair(sw, sh, 2);
        ink = pair(iw, ih, 1);
        pressure = pair(sw, sh, 1, false);
        divergence = target(sw, sh, 1);
        curl = target(sw, sh, 1);
      },
      splat(stroke) {
        const common = {
          point: [stroke.x, stroke.y],
          aspect: [width / height, 1],
          radius: 0.0014,
        };
        use(splat, {
          ...common, source: velocity.read,
          value: [stroke.dx, stroke.dy, 0],
        });
        draw(velocity.write);
        velocity.swap();
        use(splat, { ...common, radius: 0.00014,
          source: ink.read, value: [stroke.amount, 0, 0] });
        draw(ink.write);
        ink.swap();
      },
      step(dt) {
        const texel = [1 / velocity.read.width, 1 / velocity.read.height];
        use(curlProgram, { velocity: velocity.read, texel });
        draw(curl);
        use(vorticity, { velocity: velocity.read, curl, texel, dt });
        draw(velocity.write);
        velocity.swap();
        use(gravity, { velocity: velocity.read, ink: ink.read, dt });
        draw(velocity.write);
        velocity.swap();
        use(divergenceProgram, { velocity: velocity.read, texel });
        draw(divergence);
        use(relaxPressure, { pressure: pressure.read });
        draw(pressure.write);
        pressure.swap();
        for (let i = 0; i < 20; i += 1) {
          use(pressureProgram, { pressure: pressure.read, divergence, texel });
          draw(pressure.write);
          pressure.swap();
        }
        use(gradient, { pressure: pressure.read, velocity: velocity.read, texel });
        draw(velocity.write);
        velocity.swap();
        use(advect, { source: velocity.read, velocity: velocity.read,
          velocityTexel: texel, sourceTexel: texel, dt, decay: 1.2 });
        draw(velocity.write);
        velocity.swap();
        use(advect, { source: ink.read, velocity: velocity.read,
          velocityTexel: texel, sourceTexel: [1 / ink.read.width, 1 / ink.read.height],
          dt, decay: 4 });
        draw(ink.write);
        ink.swap();
      },
      render() {
        use(display, { ink: ink.read, texel: [1.5 / ink.read.width, 1.5 / ink.read.height], paper });
        draw(null);
      },
      clear() {
        for (const item of targets) {
          gl.bindFramebuffer(gl.FRAMEBUFFER, item.framebuffer);
          gl.clearColor(0, 0, 0, 0);
          gl.clear(gl.COLOR_BUFFER_BIT);
        }
        this.render();
      },
      dispose() {
        releaseTargets();
        for (const item of programs) gl.deleteProgram(item.handle);
      },
    };
  }

  function stop() {
    cancelAnimationFrame(frameId);
    frameId = 0;
    previousTime = 0;
    pointer.ready = false;
    pointer.moved = false;
    pointer.id = null;
    strokes.length = 0;
  }

  function resize() {
    const nextWidth = Math.max(1, canvas.clientWidth);
    const nextHeight = Math.max(1, canvas.clientHeight);
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    if (width === nextWidth && height === nextHeight
      && canvas.width === Math.round(nextWidth * dpr)
      && canvas.height === Math.round(nextHeight * dpr)) return;
    stop();
    width = nextWidth;
    height = nextHeight;
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    if (fluid) {
      fluid.resize();
      fluid.render();
    }
  }

  function frame(now) {
    frameId = 0;
    if (!fluid || document.hidden || motion.matches) return;
    const dt = Math.min((now - (previousTime || now - 16.67)) / 1000, 1 / 60);
    previousTime = now;
    if (pointer.ready && pointer.moved) {
      pointer.moved = false;
      trace(pointer.targetX - pointer.x, pointer.targetY - pointer.y);
    }
    for (const stroke of strokes) fluid.splat(stroke);
    strokes.length = 0;
    fluid.step(dt);
    const idle = (now - lastInput) / 1000;
    fluid.render();
    if (idle < 10) frameId = requestAnimationFrame(frame);
    else {
      fluid.clear();
      previousTime = 0;
    }
  }

  function trace(dx, dy) {
    const distance = Math.hypot(dx, dy);
    if (distance === 0) return;
    // Resample by distance so a fast sweep is a continuous ribbon, even
    // when the browser delivers only a few pointer events per frame.
    const steps = Math.min(24, Math.ceil(distance / 0.004));
    for (let i = 1; i <= steps; i += 1) {
      strokes.push({
        x: pointer.x + dx * i / steps,
        y: pointer.y + dy * i / steps,
        dx: dx * 600, dy: dy * 600,
        amount: Math.min(0.18 + distance * 4, 0.55),
      });
    }
    pointer.x += dx;
    pointer.y += dy;
  }

  function move(event) {
    if (!fluid || motion.matches || document.hidden || !event.isPrimary) return;
    const rect = canvas.getBoundingClientRect();
    pointer.targetX = (event.clientX - rect.left) / width;
    pointer.targetY = 1 - (event.clientY - rect.top) / height;
    if (!pointer.ready || pointer.id !== event.pointerId) {
      pointer.x = pointer.targetX;
      pointer.y = pointer.targetY;
      pointer.id = event.pointerId;
      pointer.ready = true;
      return;
    }
    pointer.moved = true;
    wake();
  }

  function wake() {
    lastInput = performance.now();
    if (!frameId) {
      previousTime = 0;
      frameId = requestAnimationFrame(frame);
    }
  }

  function press(event) {
    if (!fluid || motion.matches || document.hidden || !event.isPrimary) return;
    move(event);
    // The reference adds a short swirling bloom on click.
    for (let i = 0; i < 10; i += 1) {
      const angle = Math.random() * Math.PI * 2;
      const speed = 400 + Math.random() * 500;
      strokes.push({ x: pointer.targetX, y: pointer.targetY,
        dx: Math.cos(angle) * speed, dy: Math.sin(angle) * speed, amount: 0.5 });
    }
    wake();
  }

  function initialize() {
    try {
      fluid = createFluid();
      width = 0;
      resize();
      // Keep the paper background if this device cannot render the field.
      canvas.hidden = !fluid;
    } catch (error) {
      console.warn('Mouse fluid could not initialize:', error);
      fluid?.dispose();
      fluid = null;
      canvas.hidden = true;
    }
  }

  canvas.addEventListener('pointermove', move, { passive: true });
  canvas.addEventListener('pointerdown', press, { passive: true });
  canvas.addEventListener('pointerleave', () => { pointer.ready = false; });
  canvas.addEventListener('pointercancel', () => { pointer.ready = false; });
  canvas.addEventListener('pointerup', (event) => {
    if (event.pointerType !== 'mouse') pointer.ready = false;
  });
  canvas.addEventListener('webglcontextlost', (event) => {
    event.preventDefault();
    stop();
    fluid = null;
    canvas.hidden = true;
  });
  canvas.addEventListener('webglcontextrestored', () => {
    canvas.hidden = false;
    initialize();
  });
  window.addEventListener('resize', resize);
  window.addEventListener('blur', () => { pointer.ready = false; });
  document.addEventListener('visibilitychange', () => {
    stop();
    fluid?.clear();
  });
  motion.addEventListener('change', () => {
    stop();
    fluid?.clear();
  });
  initialize();
})();
