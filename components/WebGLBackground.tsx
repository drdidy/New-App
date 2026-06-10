"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

// A slow, flowing warm gradient rendered in WebGL — a living "paper" behind the
// whole app. Kept soft and low-contrast so white cards stay readable. Caps
// pixel ratio, pauses when the tab is hidden, and renders a single static frame
// when the user prefers reduced motion.
const FRAG = `
precision mediump float;
varying vec2 vUv;
uniform float uTime;
uniform vec2 uRes;

void main() {
  vec2 st = vUv;
  float a = uRes.x / uRes.y;
  vec2 p = vec2(st.x * a, st.y);
  float t = uTime * 0.05;

  // gentle domain warp for an organic flow
  p += 0.35 * vec2(sin(p.y * 2.6 + t), cos(p.x * 2.4 - t * 1.1));
  float n  = 0.5 + 0.5 * sin(p.x * 2.0 + t) * cos(p.y * 2.0 - t * 0.8);
  float n2 = 0.5 + 0.5 * sin((p.x + p.y) * 1.6 - t * 1.2);

  vec3 cream = vec3(0.957, 0.945, 0.925);
  vec3 terra = vec3(0.823, 0.447, 0.247);
  vec3 amber = vec3(0.909, 0.635, 0.290);
  vec3 coral = vec3(0.878, 0.541, 0.420);
  vec3 teal  = vec3(0.180, 0.545, 0.447);

  vec3 col = cream;
  col = mix(col, terra, smoothstep(0.40, 0.95, n) * 0.50);
  col = mix(col, amber, smoothstep(0.30, 0.85, n2) * 0.42);
  col = mix(col, coral, smoothstep(0.55, 1.00, n * n2) * 0.38);
  col = mix(col, teal,  smoothstep(0.88, 1.00, n2) * 0.10);

  // keep it soft so content stays legible
  col = mix(cream, col, 0.78);
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
      renderer = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: false, powerPreference: "low-power" });
    } catch {
      return; // no WebGL — the CSS fallback background stays
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));

    const scene = new THREE.Scene();
    const camera = new THREE.Camera();
    const uniforms = {
      uTime: { value: 0 },
      uRes: { value: new THREE.Vector2(1, 1) },
    };
    const mat = new THREE.ShaderMaterial({ vertexShader: VERT, fragmentShader: FRAG, uniforms });
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), mat);
    scene.add(mesh);

    function resize() {
      const w = window.innerWidth;
      const h = window.innerHeight;
      renderer.setSize(w, h, false);
      uniforms.uRes.value.set(w, h);
    }
    resize();
    window.addEventListener("resize", resize);

    const reduce =
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    let raf = 0;
    const start = performance.now();
    function loop(now: number) {
      uniforms.uTime.value = (now - start) / 1000;
      renderer.render(scene, camera);
      if (!document.hidden) raf = requestAnimationFrame(loop);
    }
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
