"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

// A slow, living dark gradient rendered in WebGL — replaces the app's static
// navy backdrop with a flowing navy/teal/emerald field. Tuned dark so the UI
// stays readable. Pixel-ratio capped, pauses when hidden, renders one static
// frame under prefers-reduced-motion, and the CSS dark fallback covers it if
// WebGL is unavailable.
const FRAG = `
precision mediump float;
varying vec2 vUv;
uniform float uTime;
uniform vec2 uRes;

float blob(vec2 p, vec2 c, float r) {
  float d = length(p - c);
  return smoothstep(r, 0.0, d);
}

void main() {
  vec2 st = vUv;
  float a = uRes.x / uRes.y;
  vec2 p = vec2(st.x * a, st.y);
  float t = uTime * 0.045;

  vec3 navy1 = vec3(0.027, 0.043, 0.071);
  vec3 navy3 = vec3(0.063, 0.098, 0.157);
  vec3 teal  = vec3(0.055, 0.300, 0.262);
  vec3 emer  = vec3(0.110, 0.460, 0.350);
  vec3 gold  = vec3(0.886, 0.710, 0.322);

  // base vertical navy gradient
  vec3 col = mix(navy1, navy3, smoothstep(0.0, 1.0, st.y));

  // drifting light fields
  vec2 c1 = vec2(0.30 * a + 0.18 * a * sin(t * 0.9), 0.32 + 0.12 * cos(t));
  vec2 c2 = vec2(0.78 * a + 0.14 * a * cos(t * 0.7), 0.74 + 0.12 * sin(t * 1.1));
  vec2 c3 = vec2(0.55 * a + 0.20 * a * sin(t * 0.5 + 1.0), 0.10 + 0.10 * cos(t * 0.8));

  col += teal * blob(p, c1, 0.55 * a) * 0.55;
  col += emer * blob(p, c2, 0.50 * a) * 0.40;
  col += gold * blob(p, c3, 0.30 * a) * 0.05;

  // gentle top sheen
  col += vec3(0.04, 0.06, 0.09) * smoothstep(0.7, 0.0, st.y);

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
      return; // no WebGL — the CSS dark fallback stays
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
