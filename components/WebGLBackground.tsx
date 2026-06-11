"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

// A soft, airy animated gradient — pale mint / sky / cream drifting over an
// off-white base. Tuned very light so white cards and ink text stay crisp.
// Pixel-ratio capped, pauses when hidden, single static frame under
// prefers-reduced-motion; the CSS off-white fallback covers it if WebGL fails.
const FRAG = `
precision mediump float;
varying vec2 vUv;
uniform float uTime;
uniform vec2 uRes;

float blob(vec2 p, vec2 c, float r) {
  return smoothstep(r, 0.0, length(p - c));
}

void main() {
  vec2 st = vUv;
  float a = uRes.x / uRes.y;
  vec2 p = vec2(st.x * a, st.y);
  float t = uTime * 0.04;

  // Colours are designed for CSS mix-blend-mode screen over a light page base:
  // a black base leaves the page light, and saturated blobs become soft airy
  // colour washes that can only LIGHTEN, never darken text.
  vec3 base = vec3(0.0);
  vec3 mint = vec3(0.10, 0.52, 0.40);
  vec3 sky  = vec3(0.22, 0.42, 0.85);
  vec3 cream= vec3(0.80, 0.58, 0.26);
  vec3 lilac= vec3(0.48, 0.38, 0.86);

  vec2 c1 = vec2(0.26 * a + 0.18 * a * sin(t * 0.9), 0.30 + 0.12 * cos(t));
  vec2 c2 = vec2(0.80 * a + 0.14 * a * cos(t * 0.7), 0.72 + 0.12 * sin(t * 1.1));
  vec2 c3 = vec2(0.58 * a + 0.20 * a * sin(t * 0.5 + 1.0), 0.12 + 0.10 * cos(t * 0.8));
  vec2 c4 = vec2(0.12 * a + 0.12 * a * cos(t * 0.6 + 2.0), 0.86 + 0.08 * sin(t));

  vec3 col = base;
  col += mint  * blob(p, c1, 0.60 * a) * 0.55;
  col += sky   * blob(p, c2, 0.58 * a) * 0.45;
  col += cream * blob(p, c3, 0.44 * a) * 0.40;
  col += lilac * blob(p, c4, 0.42 * a) * 0.40;

  gl_FragColor = vec4(col, 1.0);
}`;

const VERT = `
varying vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = vec4(position.xy, 0.0, 1.0);
}`;

export default function WebGLBackground() {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        canvas,
        antialias: false,
        alpha: false,
        powerPreference: "low-power",
      });
    } catch {
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));

    const scene = new THREE.Scene();
    const camera = new THREE.Camera();
    const uniforms = {
      uTime: { value: 0 },
      uRes: { value: new THREE.Vector2(1, 1) },
    };
    const mat = new THREE.ShaderMaterial({
      vertexShader: VERT,
      fragmentShader: FRAG,
      uniforms,
    });
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), mat);
    scene.add(mesh);

    const resize = () => {
      const w = window.innerWidth;
      const h = window.innerHeight;
      renderer.setSize(w, h, false);
      uniforms.uRes.value.set(w, h);
    };
    resize();
    window.addEventListener("resize", resize);

    const reduce =
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    let raf = 0;
    const start = performance.now();
    const loop = (now: number) => {
      uniforms.uTime.value = (now - start) / 1000;
      renderer.render(scene, camera);
      if (!document.hidden) raf = requestAnimationFrame(loop);
    };
    if (reduce) {
      renderer.render(scene, camera);
    } else {
      raf = requestAnimationFrame(loop);
    }

    const onVis = () => {
      if (!document.hidden && !reduce) raf = requestAnimationFrame(loop);
    };
    document.addEventListener("visibilitychange", onVis);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      document.removeEventListener("visibilitychange", onVis);
      mesh.geometry.dispose();
      mat.dispose();
      renderer.dispose();
    };
  }, []);

  return <canvas ref={ref} className="webgl-bg" aria-hidden="true" />;
}
