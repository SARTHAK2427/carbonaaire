import { useState, useEffect, useRef } from "react";
import MLDashboard from "./frontend_mldashboard";
import SimulationDashboard from "./frontend_simulation";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const TOKEN_KEY = "carbonaire_token";
const USER_KEY = "carbonaire_user";

function getStoredToken() {
  try {
    return localStorage.getItem(TOKEN_KEY) || "";
  } catch {
    return "";
  }
}

function getStoredUser() {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function storeAuthSession({ token, user }) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
  } catch {}
}

function authJsonHeaders() {
  const token = getStoredToken();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

/* ── GLOBAL STYLES ──────────────────────────────────────────────────────────── */
const GLOBAL_CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&family=Syne:wght@400;500;600;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --g50:  #F0FAF7;
    --g100: #DCF5EC;
    --g200: #B5E8D4;
    --g300: #80D4B4;
    --g400: #4EBFA0;
    --g500: #2DA888;
    --g600: #228F72;
    --g700: #1A7059;
    --g800: #0F4D3D;
    --g900: #0A3329;
    --white: #FFFFFF;
    --off:  #F5FAF8;
    --ink:  #0E1A16;
    --ink2: #1E3329;
    --muted:#4D6B61;
    --line: #C8E8DF;
    --warn: #C05A2C;
    --amber:#B08020;
    --blue: #2E5A8A;
    --r: 4px;
    --rl: 10px;
    --sh: 0 2px 12px rgba(20,26,16,.07), 0 1px 3px rgba(20,26,16,.05);
    --shm: 0 6px 28px rgba(20,26,16,.10), 0 2px 6px rgba(20,26,16,.06);
    --shl: 0 16px 56px rgba(20,26,16,.12), 0 4px 12px rgba(20,26,16,.07);
  }

  html { scroll-behavior: smooth; font-size: 15px; }
  body {
    background: var(--white);
    color: var(--ink);
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-weight: 400;
    line-height: 1.7;
    -webkit-font-smoothing: antialiased;
    overflow-x: hidden;
  }

  ::-webkit-scrollbar { width: 5px; }
  ::-webkit-scrollbar-track { background: var(--g50); }
  ::-webkit-scrollbar-thumb { background: var(--g300); border-radius: 99px; }

  .syne    { font-family: 'Syne', sans-serif; }
  .mono    { font-family: 'JetBrains Mono', monospace; }
  .corm    { font-family: 'Cormorant Garamond', serif; }

  /* NAV */
  .nav-bar {
    position: fixed; top: 0; left: 0; right: 0; z-index: 1000;
    height: 68px;
    display: flex; align-items: center;
    padding: 0 48px;
    justify-content: space-between;
    transition: background .3s, box-shadow .3s, border-color .3s;
    background: #071a14;
    border-bottom: 1px solid rgba(255,255,255,.05);
  }
  .nav-bar.scrolled {
    background: #ffffff;
    border-bottom: 1px solid var(--line);
    box-shadow: var(--sh);
  }
  .nav-left { display: flex; align-items: center; flex: 1; }
  .nav-center { display: flex; align-items: center; justify-content: center; flex: 2; }
  .nav-right { display: flex; align-items: center; justify-content: flex-end; gap: 12px; flex: 1; }

  .nav-logo {
    font-family: 'Syne', sans-serif;
    font-size: 18px; font-weight: 700;
    color: #fff; letter-spacing: -.02em;
    display: flex; align-items: center; gap: 10px;
    cursor: pointer;
  }
  .nav-bar.scrolled .nav-logo { color: var(--ink); }
  .nav-hex {
    width: 32px; height: 32px;
    background: var(--g500);
    clip-path: polygon(50% 0%,93% 25%,93% 75%,50% 100%,7% 75%,7% 25%);
    display: flex; align-items: center; justify-content: center;
  }
  .nav-hex span { font-family: 'JetBrains Mono',monospace; font-size: 12px; color: #fff; font-weight: 500; }
  
  .nav-links { display: flex; align-items: center; gap: 2px; }
  .nav-link {
    font-family: 'Syne', sans-serif;
    font-size: 12px; font-weight: 500;
    letter-spacing: .05em; text-transform: uppercase;
    color: rgba(255,255,255,.85); background: none; border: none;
    padding: 8px 14px; cursor: pointer;
    border-radius: var(--r);
    transition: color .15s, background .15s;
  }
  .nav-link:hover { background: rgba(255,255,255,.12); color: #fff; }
  .nav-bar.scrolled .nav-link { color: var(--ink2); }
  .nav-bar.scrolled .nav-link:hover { background: var(--g50); color: var(--g600); }
  
  .nav-actions { display: flex; align-items: center; gap: 8px; }
  
  .nav-signup {
    font-family: 'Syne', sans-serif;
    font-size: 12px; font-weight: 600;
    letter-spacing: .06em; text-transform: uppercase;
    background: transparent; color: rgba(255,255,255,.9);
    border: 1px solid rgba(255,255,255,.35); padding: 8px 18px;
    border-radius: var(--r); cursor: pointer;
    transition: all .15s;
    margin-left: 0;
  }
  .nav-signup:hover { background: rgba(255,255,255,.12); border-color: rgba(255,255,255,.65); color: #fff; }
  .nav-bar.scrolled .nav-signup { color: var(--g600); border-color: var(--g400); }
  .nav-bar.scrolled .nav-signup:hover { background: var(--g50); }
  .nav-cta {
    font-family: 'Syne', sans-serif;
    font-size: 11px; font-weight: 600;
    letter-spacing: .06em; text-transform: uppercase;
    background: var(--g500); color: #fff;
    border: none; padding: 10px 20px;
    border-radius: var(--r); cursor: pointer;
    transition: background .15s, transform .1s;
    white-space: nowrap;
  }
  .nav-cta:hover { background: var(--g600); }
  .nav-cta:active { transform: translateY(1px); }


  /* PROFILE DROPDOWN */
  .profile-trigger-wrap { position: relative; display: flex; align-items: center; }
  .profile-trigger {
    display: flex; align-items: center; gap: 10px;
    padding: 6px 14px; cursor: pointer; border-radius: 99px;
    transition: all .2s; border: 1px solid transparent;
  }
  .profile-trigger:hover { background: rgba(255,255,255,.1); }
  .nav-bar.scrolled .profile-trigger:hover { background: var(--g50); }
  
  .profile-avatar {
    width: 28px; height: 28px; background: var(--g500);
    border-radius: 50%; display: flex; align-items: center; justify-content: center;
    font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #fff; font-weight: 700;
  }
  .profile-name {
    font-family: 'Syne', sans-serif; font-size: 13px; font-weight: 600; color: #fff;
  }
  .nav-bar.scrolled .profile-name { color: var(--ink); }

  .profile-dropdown {
    position: absolute; top: 110%; right: 0; width: 220px;
    background: rgba(255,255,255,.98); backdrop-filter: blur(16px);
    border: 1px solid var(--line); border-radius: 12px;
    box-shadow: var(--shl); padding: 8px;
    display: none; flex-direction: column; opacity: 0; transform: translateY(10px);
    transition: all .2s cubic-bezier(0.16, 1, 0.3, 1);
    z-index: 1001;
  }
  .profile-trigger-wrap:hover .profile-dropdown { display: flex; opacity: 1; transform: translateY(0); }

  .dropdown-header { padding: 12px 14px; border-bottom: 1px solid var(--line); margin-bottom: 6px; }
  .dropdown-email { font-size: 11px; color: var(--muted); font-family: 'JetBrains Mono', monospace; }

  .dropdown-item {
    font-family: 'Syne', sans-serif; font-size: 13px; font-weight: 500;
    color: var(--ink2); padding: 10px 14px; border-radius: 8px;
    background: none; border: none; text-align: left; cursor: pointer;
    transition: all .15s; display: flex; align-items: center; gap: 10px;
  }
  .dropdown-item:hover { background: var(--g50); color: var(--g600); }
  .dropdown-item.logout { color: #A04040; }
  .dropdown-item.logout:hover { background: #FFF5F5; color: #D04040; }

  /* DASHBOARD LAYOUT */
  .dash-layout { display: flex; gap: 60px; }
  .dash-sidebar { width: 280px; flex-shrink: 0; display: flex; flex-direction: column; gap: 4px; }
  .dash-side-btn {
    font-family: 'Syne', sans-serif; font-size: 13px; font-weight: 600;
    color: var(--muted); padding: 12px 16px; border-radius: 8px;
    background: none; border: none; text-align: left; cursor: pointer;
    transition: all .2s; display: flex; align-items: center; gap: 12px;
  }
  .dash-side-btn:hover { background: var(--g100); color: var(--g700); }
  .dash-side-btn.active { background: var(--g500); color: #fff; }
  .dash-main { flex: 1; min-width: 0; }

  .fake-card {
    background: #fff; border: 1px solid var(--line); border-radius: 16px;
    padding: 32px; box-shadow: var(--sh);
  }
  .fake-title { font-family: 'Cormorant Garamond', serif; font-size: 32px; font-weight: 300; color: var(--ink); margin-bottom: 24px; }
  .fake-label { font-family: 'JetBrains Mono', monospace; font-size: 11px; text-transform: uppercase; color: var(--muted); margin-bottom: 8px; }
  
  .api-key-wrap {
    background: var(--off); border: 1px solid var(--line); border-radius: 8px;
    padding: 16px; font-family: 'JetBrains Mono', monospace; font-size: 13px;
    color: var(--ink2); display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 20px;
  }
  .gen-anim { animation: pulse-green 1.5s infinite; }
  @keyframes pulse-green {
    0% { opacity: 1; }
    50% { opacity: 0.4; }
    100% { opacity: 1; }
  }

  .residency-toggle {
    display: flex; gap: 1px; background: var(--line); border-radius: 8px; overflow: hidden;
    width: fit-content; margin-bottom: 24px;
  }
  .res-opt {
    padding: 10px 20px; font-family: 'Syne', sans-serif; font-size: 12px; font-weight: 600;
    background: #fff; border: none; cursor: pointer; color: var(--muted);
  }
  .res-opt.active { background: var(--g500); color: #fff; }

  .goal-progress {
    height: 12px; background: var(--g100); border-radius: 99px; overflow: hidden; margin: 20px 0;
  }
  .goal-fill { height: 100%; background: var(--g500); transition: width 1s ease-out; }

  /* DASHBOARD */
  .dash-page { min-height: 100vh; background: var(--off); padding-top: 100px; }
  .dash-container { max-width: 1600px; margin: 0 auto; padding: 40px 60px; }
  .dash-header { margin-bottom: 40px; }
  .dash-title {
    font-family: 'Cormorant Garamond', serif; font-size: 48px;
    font-weight: 300; color: var(--ink); line-height: 1.1; margin-bottom: 12px;
  }
  .dash-sub { font-size: 16px; color: var(--muted); }

  .dash-grid { display: grid; grid-template-columns: 1fr; gap: 24px; }
  .history-table-wrap {
    background: #fff; border: 1px solid var(--line); border-radius: 16px;
    overflow: hidden; box-shadow: var(--sh);
  }
  .history-table { width: 100%; border-collapse: collapse; text-align: left; }
  .history-table th {
    padding: 18px 24px; font-family: 'Syne', sans-serif; font-size: 11px;
    text-transform: uppercase; letter-spacing: .1em; color: var(--muted);
    background: var(--g50); border-bottom: 1px solid var(--line);
  }
  .history-table td {
    padding: 20px 24px; border-bottom: 1px solid var(--off);
    font-size: 14px; vertical-align: middle;
  }
  .history-table tr:hover td { background: var(--g50); }

  .row-title { font-family: 'Syne', sans-serif; font-weight: 700; color: var(--ink); margin-bottom: 4px; }
  .row-meta { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: var(--muted); }

  .badge-intensity {
    padding: 4px 10px; border-radius: 6px; font-family: 'JetBrains Mono', monospace;
    font-size: 11px; font-weight: 600;
  }

  .action-btns { display: flex; gap: 8px; }
  .btn-icon {
    width: 34px; height: 34px; border-radius: 8px; border: 1px solid var(--line);
    background: #fff; cursor: pointer; display: flex; align-items: center; justify-content: center;
    transition: all .2s; font-size: 12px; color: var(--ink2);
  }
  .btn-icon:hover { border-color: var(--g400); background: var(--g50); color: var(--g600); }
  .btn-icon.delete:hover { border-color: #E07878; background: #FFF5F5; color: #D04040; }
  
  .empty-state {
    padding: 80px 40px; text-align: center; color: var(--muted);
  }

  /* SECTIONS */
  section { position: relative; }

  /* HERO */
  .hero {
    min-height: 100vh;
    background: linear-gradient(155deg, #071a14 0%, #0d2a20 40%, #061510 100%);
    display: flex; align-items: center;
    padding: 120px 80px 80px;
    overflow: hidden;
  }
  .hero-inner {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 72px;
    align-items: center;
    width: 100%;
    position: relative; z-index: 1;
  }
  .hero-bg-grid {
    position: absolute; inset: 0; pointer-events: none;
    background-image:
      linear-gradient(rgba(46,168,136,.07) 1px, transparent 1px),
      linear-gradient(90deg, rgba(46,168,136,.07) 1px, transparent 1px);
    background-size: 60px 60px;
  }
  .hero-bg-glow {
    position: absolute; pointer-events: none;
    width: 800px; height: 800px;
    background: radial-gradient(circle, rgba(45,168,136,.2) 0%, transparent 65%);
    top: -250px; right: -150px;
    border-radius: 50%;
  }
  .hero-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: clamp(36px, 4.5vw, 68px);
    font-weight: 300; line-height: 1.05;
    color: #E8F7F3; letter-spacing: -.02em;
    margin-bottom: 20px;
  }
  .hero-motto-sub {
    font-family: 'Cormorant Garamond', serif;
    font-size: 18px; font-weight: 300;
    color: rgba(232,247,243,.55);
    max-width: 480px; line-height: 1.65;
    margin-bottom: 40px;
    letter-spacing: .01em;
  }
  .hero-actions { display: flex; align-items: center; gap: 16px; }

  /* HERO SLIDESHOW */
  .hero-slideshow {
    position: relative;
    width: 100%;
    aspect-ratio: 16 / 10;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 32px 80px rgba(0,0,0,.55), 0 0 0 1px rgba(255,255,255,.08);
  }
  .hero-slide {
    position: absolute; inset: 0;
    opacity: 0;
    transition: opacity 1s cubic-bezier(.4,0,.2,1);
  }
  .hero-slide.active { opacity: 1; }
  .hero-slide img {
    width: 100%; height: 100%;
    object-fit: cover; object-position: top left;
    display: block;
  }
  .hero-slide-overlay {
    position: absolute; inset: 0;
    background: linear-gradient(180deg, transparent 55%, rgba(7,26,20,.7) 100%);
    pointer-events: none;
  }
  .hero-slide-caption {
    position: absolute; bottom: 14px; left: 14px;
    background: rgba(10,51,41,.8);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255,255,255,.1);
    border-radius: 6px;
    padding: 6px 12px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px; letter-spacing: .1em; text-transform: uppercase;
    color: rgba(255,255,255,.55);
  }
  .hero-slide-dots {
    position: absolute; bottom: 16px; right: 16px;
    display: flex; gap: 6px; align-items: center;
  }
  .hero-slide-dot {
    height: 4px; border-radius: 99px;
    width: 18px;
    background: rgba(255,255,255,.2);
    transition: width .4s ease, background .4s ease;
    cursor: pointer;
  }
  .hero-slide-dot.active {
    width: 28px;
    background: var(--g400);
  }
  .hero-slide-progress {
    position: absolute; top: 0; left: 0; right: 0;
    height: 2px;
    background: rgba(255,255,255,.06);
  }
  .hero-slide-progress-fill {
    height: 100%;
    background: var(--g500);
    transition: width .08s linear;
  }
  .btn-hero {
    font-family: 'Syne', sans-serif;
    font-size: 12px; font-weight: 600;
    letter-spacing: .08em; text-transform: uppercase;
    background: var(--g500); color: #fff;
    border: none; padding: 14px 32px;
    border-radius: var(--r); cursor: pointer;
    transition: background .15s, transform .1s, box-shadow .15s;
  }
  .btn-hero:hover { background: var(--g600); box-shadow: 0 8px 24px rgba(45,168,136,.4); }
  .btn-hero:active { transform: translateY(1px); }
  .btn-hero-ghost {
    font-family: 'Syne', sans-serif;
    font-size: 12px; font-weight: 600;
    letter-spacing: .08em; text-transform: uppercase;
    background: transparent; color: rgba(232,247,243,.75);
    border: 1px solid rgba(232,247,243,.25); padding: 14px 32px;
    border-radius: var(--r); cursor: pointer;
    transition: all .15s;
  }
  .btn-hero-ghost:hover { border-color: rgba(232,247,243,.55); color: #E8F7F3; }

  /* GENERIC SECTION */
  .section-pad { padding: 100px 80px; }
  .section-pad-sm { padding: 72px 80px; }
  .section-tag {
    font-family: 'Syne', sans-serif;
    font-size: 13px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase;
    color: var(--g500); margin-bottom: 16px;
    display: flex; align-items: center; gap: 12px;
  }
  .section-tag::before { display:none; }
  .section-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: clamp(34px, 4vw, 56px);
    font-weight: 300; line-height: 1.1;
    color: var(--ink); letter-spacing: -.02em;
  }
  .section-title em { font-style: italic; color: var(--g500); }
  .section-body {
    font-size: 17px; color: var(--muted);
    line-height: 1.75; font-weight: 300;
    max-width: 560px;
  }

  /* ABOUT */
  .about-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 80px; align-items: center; }
  .about-visual {
    position: relative; height: 480px;
    background: var(--g50); border-radius: var(--rl);
    border: 1px solid var(--line);
    overflow: hidden;
    display: flex; align-items: center; justify-content: center;
  }
  .about-circles {
    position: absolute; inset: 0;
    display: flex; align-items: center; justify-content: center;
  }
  .acirc {
    position: absolute; border-radius: 50%;
    border: 1px solid;
    display: flex; align-items: center; justify-content: center;
  }
  .about-center-text {
    position: relative; text-align: center; z-index:10;
  }
  .about-center-num {
    font-family: 'Cormorant Garamond', serif;
    font-size: 72px; font-weight: 300;
    color: var(--g600); line-height: 1;
  }
  .about-center-sub { font-family: 'JetBrains Mono', monospace; font-size: 10px; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); margin-top: 6px; }
  .about-pillars { margin-top: 40px; display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

  /* PROFESSIONAL FEATURE CARDS */
  .pillar {
    padding: 24px 22px;
    background: var(--white);
    border: 1px solid var(--line);
    border-radius: var(--r);
    border-top: 3px solid var(--g400);
    transition: box-shadow .2s, transform .2s;
  }
  .pillar:hover { box-shadow: var(--shm); transform: translateY(-2px); }
  .pillar-indicator {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px; letter-spacing: .14em; text-transform: uppercase;
    color: var(--g500); margin-bottom: 12px;
    display: flex; align-items: center; gap: 8px;
  }
  .pillar-indicator::before { display:none; }
  .pillar-title { font-family: 'Syne', sans-serif; font-size: 14px; font-weight: 700; color: var(--ink); margin-bottom: 8px; letter-spacing: -.01em; }
  .pillar-text  { font-size: 13px; color: var(--muted); line-height: 1.6; }

  /* HOW IT WORKS */
  .hiw-bg { background: var(--g900); }
  .hiw-steps { display: grid; grid-template-columns: repeat(3, 1fr); gap: 2px; margin-top: 60px; }
  .hiw-step {
    background: rgba(255,255,255,.04);
    border: 1px solid rgba(255,255,255,.07);
    padding: 36px 32px;
    position: relative; overflow: hidden;
    transition: background .2s;
  }
  .hiw-step:hover { background: rgba(255,255,255,.07); }
  .hiw-step-num {
    font-family: 'Cormorant Garamond', serif;
    font-size: 64px; font-weight: 300;
    color: rgba(78,138,58,.25); line-height: 1;
    position: absolute; top: 16px; right: 20px;
  }
  .hiw-step-icon { font-size: 28px; margin-bottom: 16px; }
  .hiw-step-title { font-family: 'Syne', sans-serif; font-size: 16px; font-weight: 600; color: #fff; margin-bottom: 10px; }
  .hiw-step-text  { font-size: 15px; color: rgba(255,255,255,.5); line-height: 1.6; }

  /* CAPABILITIES */
  .cap-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; margin-top: 56px; }
  .cap-card {
    background: var(--white);
    border: 1px solid var(--line);
    border-radius: var(--rl);
    padding: 32px; box-shadow: var(--sh);
    transition: box-shadow .2s, transform .2s;
  }
  .cap-card:hover { box-shadow: var(--shm); transform: translateY(-3px); }
  .cap-icon { width: 48px; height: 48px; background: var(--g50); border-radius: var(--r); display: flex; align-items: center; justify-content: center; font-size: 22px; margin-bottom: 20px; border: 1px solid var(--g100); }
  .cap-title { font-family: 'Syne', sans-serif; font-size: 16px; font-weight: 600; color: var(--ink); margin-bottom: 10px; }
  .cap-text  { font-size: 14.5px; color: var(--muted); line-height: 1.65; }

  /* CALCULATOR PAGE */
  .calc-page { min-height: 100vh; background: var(--off); padding-top: 80px; }
  .calc-header {
    background: var(--g800);
    padding: 56px 80px 48px;
  }
  .calc-header-inner { max-width: 1100px; margin: 0 auto; }
  .calc-title { font-family: 'Cormorant Garamond', serif; font-size: 44px; font-weight: 300; color: #fff; letter-spacing: -.02em; }
  .calc-sub { font-size: 16px; color: rgba(255,255,255,.5); margin-top: 8px; }

  /* Progress */
  .progress-wrap { background: var(--white); border-bottom: 1px solid var(--line); padding: 0 80px; }
  .progress-inner { max-width: 1100px; margin: 0 auto; display: flex; }
  .prog-step {
    flex: 1; padding: 20px 0 18px;
    display: flex; align-items: center; gap: 12px;
    border-bottom: 3px solid transparent;
    cursor: pointer; transition: all .15s;
  }
  .prog-step.active { border-bottom-color: var(--g500); }
  .prog-step.done   { border-bottom-color: var(--g300); }
  .prog-dot {
    width: 28px; height: 28px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
    background: var(--g50); color: var(--muted);
    border: 1.5px solid var(--line); flex-shrink: 0;
    transition: all .15s;
  }
  .prog-step.active .prog-dot { background: var(--g500); color: #fff; border-color: var(--g500); }
  .prog-step.done   .prog-dot { background: var(--g100); color: var(--g600); border-color: var(--g300); }
  .prog-label { font-family: 'Syne', sans-serif; font-size: 11px; font-weight: 500; letter-spacing: .05em; text-transform: uppercase; color: var(--muted); }
  .prog-step.active .prog-label { color: var(--g600); }

  /* Calc body */
  .calc-body { max-width: 1100px; margin: 0 auto; padding: 40px 80px 80px; }

  /* Step form */
  .step-card {
    background: var(--white); border: 1px solid var(--line);
    border-radius: var(--rl); box-shadow: var(--sh);
    overflow: hidden; margin-bottom: 24px;
  }
  .step-card-header {
    padding: 24px 32px 22px;
    border-bottom: 1px solid var(--line);
    display: flex; align-items: center; gap: 16px;
    background: var(--g50);
  }
  .step-card-num {
    width: 36px; height: 36px; border-radius: 50%;
    background: var(--g600); color: #fff;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px; display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
  }
  .step-card-title { font-family: 'Syne', sans-serif; font-size: 17px; font-weight: 600; color: var(--ink); }
  .step-card-sub   { font-size: 13px; color: var(--muted); margin-top: 2px; }
  .step-card-body  { padding: 32px; }

  .fgrid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
  .fgrid-2 { grid-template-columns: repeat(2, 1fr); }
  .fgrid-4 { grid-template-columns: repeat(4, 1fr); }
  .fg-span2 { grid-column: span 2; }
  .fg-span3 { grid-column: span 3; }

  .fl { display: flex; flex-direction: column; gap: 5px; }
  .fl label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; letter-spacing: .08em; text-transform: uppercase;
    color: var(--muted);
  }
  .fl input, .fl select, .fl textarea {
    background: var(--off);
    border: 1px solid var(--line);
    border-radius: var(--r);
    padding: 10px 13px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12.5px; color: var(--ink); width: 100%;
    transition: border-color .15s, box-shadow .15s;
    -webkit-appearance: none;
  }
  .fl input:focus, .fl select:focus {
    outline: none; border-color: var(--g400);
    background: var(--white);
    box-shadow: 0 0 0 3px rgba(78,138,58,.10);
  }
  .fl input::placeholder { color: var(--line); }
  .unit-input { position: relative; }
  .unit-input input { padding-right: 52px; }
  .unit-tag {
    position: absolute; right: 12px; top: 50%; transform: translateY(-50%);
    font-family: 'JetBrains Mono', monospace; font-size: 10px;
    color: var(--muted); pointer-events: none;
  }

  .btn-next {
    font-family: 'Syne', sans-serif;
    font-size: 12px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase;
    background: var(--g600); color: #fff;
    border: none; padding: 12px 28px; border-radius: var(--r);
    cursor: pointer; transition: background .15s;
  }
  .btn-next:hover { background: var(--g700); transform: translateY(-1px); }
  .btn-next:active { transform: translateY(0); }

  /* RESULTS TABS */
  .res-tabs {
    display: flex; gap: 4px; margin-bottom: 24px;
    background: var(--off); padding: 5px; border-radius: 99px;
    border: 1px solid var(--line); width: fit-content;
  }
  .res-tab-btn {
    padding: 10px 24px; border-radius: 99px; border: none;
    font-family: 'Syne', sans-serif; font-size: 13px; font-weight: 600;
    color: var(--muted); cursor: pointer; transition: all .2s;
    background: transparent; letter-spacing: .02em;
  }
  .res-tab-btn:hover { color: var(--g600); background: rgba(34,143,114,.05); }
  .res-tab-btn.active { background: var(--white); color: var(--g600); box-shadow: var(--sh); }

  .fade-in { animation: fadeIn .4s ease-out forwards; }
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .btn-back {
    font-family: 'Syne', sans-serif;
    font-size: 12px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase;
    background: transparent; color: var(--muted);
    border: 1px solid var(--line); padding: 12px 24px; border-radius: var(--r);
    cursor: pointer; transition: all .15s;
  }
  .btn-back:hover { border-color: var(--g300); color: var(--ink); }
  .btn-calculate {
    font-family: 'Syne', sans-serif;
    font-size: 13px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase;
    background: var(--g500); color: #fff;
    border: none; padding: 14px 40px; border-radius: var(--r);
    cursor: pointer; transition: background .15s, box-shadow .15s;
    box-shadow: 0 4px 16px rgba(78,138,58,.3);
  }
  .btn-calculate:hover { background: var(--g600); }

  /* Results */
  .results-section { background: var(--white); min-height: 100vh; padding-top: 80px; }
  .results-header { background: var(--g800); padding: 56px 80px 48px; }
  .results-header-inner { max-width: 1200px; margin: 0 auto; display: flex; align-items: flex-end; justify-content: space-between; }
  .result-band-pill {
    display: inline-block;
    padding: 6px 18px; border-radius: 99px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px; letter-spacing: .06em; text-transform: uppercase;
    font-weight: 500; margin-bottom: 14px;
  }
  .results-body { max-width: 1200px; margin: 0 auto; padding: 48px 80px 80px; }
  .results-grid { display: grid; grid-template-columns: 1fr 380px; gap: 28px; margin-bottom: 28px; }

  .res-card { background: var(--white); border: 1px solid var(--line); border-radius: var(--rl); box-shadow: var(--sh); overflow: hidden; }
  .res-card-header { padding: 16px 24px; border-bottom: 1px solid var(--line); background: var(--g50); }
  .res-card-title { font-family: 'Syne', sans-serif; font-size: 11px; font-weight: 600; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); }
  .res-card-body { padding: 28px 24px; }

  .kpi-strip { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1px; background: var(--line); border: 1px solid var(--line); border-radius: var(--rl); overflow: hidden; margin-bottom: 28px; }
  .kpi-cell { background: var(--white); padding: 22px 24px; }
  .kpi-label { font-family: 'JetBrains Mono', monospace; font-size: 9px; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); margin-bottom: 8px; }
  .kpi-val   { font-family: 'Cormorant Garamond', serif; font-size: 34px; font-weight: 300; color: var(--ink); line-height: 1; }
  .kpi-unit  { font-family: 'JetBrains Mono', monospace; font-size: 9px; color: var(--muted); margin-top: 4px; }

  /* Bar chart custom */
  .bar-chart-wrap { display: flex; flex-direction: column; gap: 14px; }
  .brow { display: flex; align-items: center; gap: 12px; }
  .brow-label { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: var(--muted); width: 90px; flex-shrink: 0; text-align: right; }
  .brow-track { flex: 1; height: 22px; background: var(--g50); border-radius: 2px; position: relative; overflow: hidden; }
  .brow-fill  { height: 100%; border-radius: 2px; transition: width 1.2s cubic-bezier(.22,1,.36,1); display: flex; align-items: center; justify-content: flex-end; padding-right: 8px; }
  .brow-fill span { font-family: 'JetBrains Mono', monospace; font-size: 9px; color: rgba(255,255,255,.9); white-space: nowrap; }
  .brow-ref { position: absolute; top: 0; bottom: 0; width: 2px; background: var(--warn); opacity: .6; }
  .brow-val  { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: var(--ink2); width: 70px; text-align: right; }

  /* Gauge */
  .gauge-wrap { display: flex; flex-direction: column; align-items: center; padding: 16px 0; }
  .gauge-svg { width: 200px; height: 120px; }
  .gauge-value { font-family: 'Cormorant Garamond', serif; font-size: 42px; font-weight: 300; text-align: center; line-height: 1; margin-top: -8px; }
  .gauge-unit  { font-family: 'JetBrains Mono', monospace; font-size: 9px; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); text-align: center; margin-top: 4px; }

  /* Donut */
  .donut-legend { display: flex; flex-direction: column; gap: 10px; margin-top: 16px; }
  .dleg { display: flex; align-items: center; gap: 10px; }
  .dleg-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
  .dleg-label { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: var(--muted); flex: 1; }
  .dleg-val   { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: var(--ink2); font-weight: 500; }

  /* Finding cards */
  .finding { border-radius: var(--r); padding: 20px 24px; margin-bottom: 12px; border-left: 4px solid; }
  .f-CRITICAL { background: #FEF4F0; border-left-color: #C05A2C; }
  .f-HIGH     { background: #FDFBF0; border-left-color: #B08020; }
  .f-MEDIUM   { background: #F0F5FF; border-left-color: #2E5A8A; }
  .f-INFO     { background: var(--g50); border-left-color: var(--g400); }
  .f-badge { display: inline-block; font-family: 'JetBrains Mono', monospace; font-size: 9px; letter-spacing: .1em; text-transform: uppercase; padding: 3px 9px; border-radius: 2px; margin-bottom: 8px; font-weight: 500; }
  .fb-CRITICAL { background: #C05A2C; color: #fff; }
  .fb-HIGH     { background: #B08020; color: #fff; }
  .fb-MEDIUM   { background: #2E5A8A; color: #fff; }
  .fb-INFO     { background: var(--g500); color: #fff; }
  .f-scope { font-family: 'JetBrains Mono', monospace; font-size: 9px; color: var(--muted); margin-left: 8px; }
  .f-cat   { font-family: 'JetBrains Mono', monospace; font-size: 9px; color: var(--muted); border-left: 1px solid var(--line); padding-left: 8px; margin-left: 6px; }
  .f-msg   { font-size: 15px; color: var(--ink); margin-bottom: 7px; line-height: 1.5; }
  .f-rec   { font-size: 13.5px; color: var(--ink2); font-style: italic; line-height: 1.6; }
  .f-rec::before { content: 'Recommendation: '; font-style: normal; color: var(--g500); font-family: 'JetBrains Mono', monospace; font-size: 10px; letter-spacing: .06em; }

  /* AI Chat */
  .ai-section { background: linear-gradient(155deg, #071a14 0%, #0d2a20 50%, #061510 100%); min-height: 100vh; padding-top: 80px; }
  .ai-header  { padding: 56px 80px 48px; max-width: 1100px; margin: 0 auto; }
  .ai-body    { max-width: 1100px; margin: 0 auto; padding: 0 80px 80px; display: grid; grid-template-columns: 1fr 340px; gap: 28px; }
  .chat-container { background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.08); border-radius: var(--rl); overflow: hidden; }
  .chat-top { padding: 16px 24px; border-bottom: 1px solid rgba(255,255,255,.08); display: flex; align-items: center; gap: 10px; }
  .chat-top-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--g400); animation: pulse 2s infinite; }
  @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: .4; } }
  .chat-top-label { font-family: 'JetBrains Mono', monospace; font-size: 10px; letter-spacing: .1em; text-transform: uppercase; color: rgba(255,255,255,.4); }
  .chat-messages { height: 420px; overflow-y: auto; padding: 24px; display: flex; flex-direction: column; gap: 18px; }
  .cmsg { max-width: 78%; }
  .cmsg.user { align-self: flex-end; }
  .cmsg.ai   { align-self: flex-start; }
  .cmsg-who  { font-family: 'JetBrains Mono', monospace; font-size: 9px; letter-spacing: .08em; text-transform: uppercase; color: rgba(255,255,255,.3); margin-bottom: 5px; }
  .cmsg.user .cmsg-who { text-align: right; }
  .cmsg-bubble { padding: 13px 16px; font-size: 14px; line-height: 1.6; border-radius: 2px; }
  .cmsg.user .cmsg-bubble { background: var(--g600); color: #fff; border-radius: 8px 8px 2px 8px; }
  .cmsg.ai   .cmsg-bubble { background: rgba(255,255,255,.07); color: rgba(255,255,255,.85); border: 1px solid rgba(255,255,255,.08); border-radius: 8px 8px 8px 2px; }
  .chat-input-bar { border-top: 1px solid rgba(255,255,255,.08); padding: 16px 20px; display: flex; gap: 10px; }
  .chat-input {
    flex: 1; background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.1);
    border-radius: var(--r); padding: 10px 15px;
    font-family: 'Cormorant Garamond', serif; font-size: 15px;
    color: rgba(255,255,255,.85);
    transition: border-color .15s;
  }
  .chat-input:focus { outline: none; border-color: var(--g400); }
  .chat-input::placeholder { color: rgba(255,255,255,.25); }
  .chat-send { background: var(--g500); color: #fff; border: none; padding: 10px 22px; font-family: 'Syne', sans-serif; font-size: 11px; letter-spacing: .08em; text-transform: uppercase; font-weight: 600; border-radius: var(--r); cursor: pointer; transition: background .15s; }
  .chat-send:hover { background: var(--g400); }

  .ai-side-card { background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.08); border-radius: var(--rl); padding: 24px; }
  .ai-side-title { font-family: 'Syne', sans-serif; font-size: 11px; font-weight: 600; letter-spacing: .1em; text-transform: uppercase; color: rgba(255,255,255,.4); margin-bottom: 16px; }
  .ai-chip { display: block; width: 100%; text-align: left; background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.08); border-radius: var(--r); padding: 11px 14px; margin-bottom: 8px; font-family: 'Cormorant Garamond', serif; font-size: 14px; color: rgba(255,255,255,.65); cursor: pointer; transition: all .15s; }
  .ai-chip:hover { background: rgba(255,255,255,.09); color: #fff; border-color: var(--g400); }

  /* Typing dots */
  .typing { display: flex; gap: 5px; align-items: center; padding: 4px 0; }
  .tdot { width: 6px; height: 6px; border-radius: 50%; background: rgba(255,255,255,.4); animation: tdot 1.3s infinite; }
  .tdot:nth-child(2) { animation-delay: .2s; }
  .tdot:nth-child(3) { animation-delay: .4s; }
  @keyframes tdot { 0%,80%,100% { transform:translateY(0); opacity:.4; } 40% { transform:translateY(-7px); opacity:1; } }

  /* DOCUMENT UPLOAD SCREEN */
  .upload-screen { max-width: 860px; margin: 0 auto; padding: 40px 80px 80px; }
  .upload-hero-card {
    background: linear-gradient(135deg, var(--g800) 0%, var(--g700) 100%);
    border-radius: var(--rl); padding: 40px 44px; margin-bottom: 24px;
    position: relative; overflow: hidden;
  }
  .upload-hero-card::before {
    content: ''; position: absolute; inset: 0; pointer-events: none;
    background-image: linear-gradient(rgba(78,191,160,.06) 1px, transparent 1px),
      linear-gradient(90deg, rgba(78,191,160,.06) 1px, transparent 1px);
    background-size: 40px 40px;
  }
  .upload-hero-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 34px; font-weight: 300; color: #E8F7F3;
    letter-spacing: -.02em; margin-bottom: 10px;
  }
  .upload-hero-sub {
    font-size: 15px; color: rgba(232,247,243,.55); line-height: 1.65; max-width: 520px;
  }
  .upload-badge {
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(78,191,160,.15); border: 1px solid rgba(78,191,160,.3);
    border-radius: 99px; padding: 5px 14px;
    font-family: 'JetBrains Mono', monospace; font-size: 10px;
    color: var(--g300); letter-spacing: .1em; text-transform: uppercase;
    margin-bottom: 20px;
  }
  .upload-card {
    background: var(--white); border: 1px solid var(--line);
    border-radius: var(--rl); box-shadow: var(--sh);
    overflow: hidden; margin-bottom: 16px;
  }
  .upload-card-header {
    padding: 20px 28px 18px; border-bottom: 1px solid var(--line);
    background: var(--g50); display: flex; align-items: center; gap: 14px;
  }
  .upload-card-icon {
    width: 38px; height: 38px; border-radius: var(--r);
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; flex-shrink: 0;
  }
  .upload-card-title { font-family: 'Syne', sans-serif; font-size: 15px; font-weight: 600; color: var(--ink); }
  .upload-card-desc  { font-size: 12.5px; color: var(--muted); margin-top: 2px; }
  .upload-card-body  { padding: 28px; }

  .upload-drop-zone {
    border: 2px dashed var(--line);
    border-radius: var(--r); padding: 36px 24px;
    text-align: center; cursor: pointer;
    transition: border-color .2s, background .2s;
    background: var(--off);
  }
  .upload-drop-zone:hover, .upload-drop-zone.drag-over {
    border-color: var(--g400); background: var(--g50);
  }
  .upload-drop-zone.has-file {
    border-color: var(--g400); border-style: solid;
    background: var(--g50);
  }
  .upload-drop-icon { font-size: 32px; margin-bottom: 10px; }
  .upload-drop-text {
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
    color: var(--muted); letter-spacing: .05em;
  }
  .upload-drop-sub { font-size: 11px; color: var(--line); margin-top: 4px; }
  .upload-file-chip {
    display: inline-flex; align-items: center; gap: 8px;
    background: var(--g100); border: 1px solid var(--g300);
    border-radius: 99px; padding: 6px 14px;
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
    color: var(--g700); margin-top: 10px;
  }
  .upload-file-chip-remove {
    cursor: pointer; color: var(--muted); font-size: 14px; line-height: 1;
    margin-left: 2px; background: none; border: none; padding: 0;
  }
  .upload-file-chip-remove:hover { color: var(--warn); }

  .doc-upload-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
  .doc-upload-row {
    display: flex; align-items: center; gap: 12px;
    border: 1px solid var(--line); border-radius: var(--r);
    padding: 14px 16px; cursor: pointer;
    transition: border-color .15s, background .15s;
    background: var(--off);
  }
  .doc-upload-row:hover { border-color: var(--g400); background: var(--g50); }
  .doc-upload-row.uploaded { border-color: var(--g400); border-style: solid; background: var(--g50); }
  .doc-upload-row-icon { font-size: 20px; flex-shrink: 0; }
  .doc-upload-row-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; color: var(--muted); letter-spacing: .06em;
    text-transform: uppercase; margin-bottom: 2px;
  }
  .doc-upload-row-status { font-size: 12px; color: var(--ink2); }
  .doc-upload-row-check { margin-left: auto; color: var(--g500); font-size: 16px; }

  .template-note {
    background: linear-gradient(135deg, #EFF9F5 0%, #F5FAF8 100%);
    border: 1px solid var(--g200); border-left: 3px solid var(--g500);
    border-radius: var(--r); padding: 16px 20px;
    margin-bottom: 20px;
  }
  .template-note-title {
    font-family: 'Syne', sans-serif; font-size: 12px; font-weight: 600;
    color: var(--g700); margin-bottom: 6px; display: flex; align-items: center; gap: 8px;
  }
  .template-note-text { font-size: 13px; color: var(--muted); line-height: 1.6; }
  .template-download-btn {
    display: inline-flex; align-items: center; gap: 6px;
    background: var(--g600); color: #fff;
    font-family: 'Syne', sans-serif; font-size: 11px; font-weight: 600;
    letter-spacing: .06em; text-transform: uppercase;
    border: none; border-radius: var(--r); padding: 8px 16px;
    cursor: pointer; transition: background .15s; margin-top: 12px;
  }
  .template-download-btn:hover { background: var(--g700); }

  .upload-skip-bar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 20px 0; margin-top: 8px;
  }
  .upload-skip-text { font-size: 13.5px; color: var(--muted); }
  .upload-proceed-btn {
    font-family: 'Syne', sans-serif; font-size: 12px; font-weight: 600;
    letter-spacing: .08em; text-transform: uppercase;
    background: var(--g600); color: #fff;
    border: none; padding: 12px 32px; border-radius: var(--r);
    cursor: pointer; transition: background .15s;
  }
  .upload-proceed-btn:hover { background: var(--g700); }
  .upload-proceed-btn:disabled { background: var(--g200); cursor: not-allowed; }
  .upload-manual-btn {
    font-family: 'Syne', sans-serif; font-size: 12px; font-weight: 600;
    letter-spacing: .08em; text-transform: uppercase;
    background: transparent; color: var(--muted);
    border: 1px solid var(--line); padding: 12px 24px; border-radius: var(--r);
    cursor: pointer; transition: all .15s;
  }
  .upload-manual-btn:hover { border-color: var(--g300); color: var(--ink); }

  /* MISSION SECTION */
  .mission-section {
    background: var(--white);
    padding: 100px 80px;
    border-bottom: 1px solid var(--line);
  }
  .mission-inner {
    max-width: 900px; margin: 0 auto; text-align: center;
  }
  .mission-tag {
    font-family: 'Syne', sans-serif;
    font-size: 13px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase;
    color: var(--g500); margin-bottom: 24px;
    display: inline-flex; align-items: center; gap: 12px;
  }
  .mission-headline {
    font-family: 'Cormorant Garamond', serif;
    font-size: clamp(36px, 5vw, 64px);
    font-weight: 300; line-height: 1.1;
    color: var(--ink); letter-spacing: -.02em;
    margin-bottom: 28px;
  }
  .mission-body {
    font-size: 18px; color: var(--muted);
    line-height: 1.8; font-weight: 300;
    max-width: 680px; margin: 0 auto 48px;
  }
  .mission-pillars {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 1px;
    background: var(--line); border-radius: var(--rl);
    overflow: hidden; margin-top: 48px;
  }
  .mission-pillar {
    background: var(--white); padding: 36px 32px;
    text-align: left;
  }
  .mission-pillar-num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px; color: var(--g500); letter-spacing: .1em;
    text-transform: uppercase; margin-bottom: 14px;
  }
  .mission-pillar-title {
    font-family: 'Syne', sans-serif;
    font-size: 17px; font-weight: 700; color: var(--ink);
    margin-bottom: 10px;
  }
  .mission-pillar-text {
    font-size: 14px; color: var(--muted); line-height: 1.65;
  }

  /* JOURNEY / 3-STEP ANIMATED SECTION */
  .journey-section {
    background: linear-gradient(155deg, #071a14 0%, #0d2a20 50%, #061510 100%);
    padding: 100px 80px;
    overflow: hidden;
  }
  .journey-header { margin-bottom: 72px; }
  .journey-tag {
    font-family: 'Syne', sans-serif;
    font-size: 13px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase;
    color: var(--g300); margin-bottom: 16px;
    display: flex; align-items: center; gap: 12px;
  }
  .journey-tag::before { display:none; }
  .journey-headline {
    font-family: 'Cormorant Garamond', serif;
    font-size: clamp(34px, 4vw, 54px);
    font-weight: 300; line-height: 1.1;
    color: #fff; letter-spacing: -.02em;
  }
  .journey-layout {
    display: grid;
    grid-template-columns: 320px 1fr;
    gap: 60px;
    align-items: start;
  }
  .journey-steps { display: flex; flex-direction: column; gap: 0; }
  .journey-step {
    padding: 28px 0;
    border-bottom: 1px solid rgba(255,255,255,.06);
    cursor: pointer;
    transition: all .3s;
    position: relative;
  }
  .journey-step:first-child { padding-top: 0; }
  .journey-step-num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; letter-spacing: .12em; text-transform: uppercase;
    color: rgba(255,255,255,.25); margin-bottom: 8px;
    transition: color .3s;
  }
  .journey-step-title {
    font-family: 'Syne', sans-serif;
    font-size: 18px; font-weight: 700;
    color: rgba(255,255,255,.4);
    transition: color .3s, font-size .4s cubic-bezier(.22,1,.36,1);
    line-height: 1.2;
  }
  .journey-step-sub {
    font-size: 13px; color: rgba(255,255,255,.3);
    line-height: 1.5; margin-top: 8px;
    max-height: 0; overflow: hidden;
    transition: max-height .4s cubic-bezier(.22,1,.36,1), opacity .3s, color .3s;
    opacity: 0;
  }
  .journey-step.active .journey-step-num { color: var(--g400); }
  .journey-step.active .journey-step-title { color: #fff; font-size: 22px; }
  .journey-step.active .journey-step-sub { max-height: 80px; opacity: 1; color: rgba(255,255,255,.55); }
  .journey-step-bar {
    position: absolute; left: -20px; top: 28px; bottom: 0;
    width: 3px; background: var(--g500); border-radius: 2px;
    transform: scaleY(0); transform-origin: top;
    transition: transform 4s linear;
  }
  .journey-step:first-child .journey-step-bar { top: 0; }
  .journey-step.active .journey-step-bar { transform: scaleY(1); }
  .journey-preview {
    position: relative;
    background: rgba(255,255,255,.04);
    border: 1px solid rgba(255,255,255,.1);
    border-radius: 12px;
    overflow: hidden;
    min-height: 420px;
    display: flex; flex-direction: column;
  }
  .journey-preview-bar {
    height: 36px;
    background: rgba(255,255,255,.06);
    border-bottom: 1px solid rgba(255,255,255,.08);
    display: flex; align-items: center; padding: 0 16px; gap: 8px; flex-shrink: 0;
  }
  .jp-dot { width: 10px; height: 10px; border-radius: 50%; }
  .journey-preview-content {
    flex: 1; padding: 28px 28px; display: flex; flex-direction: column; gap: 14px;
    transition: opacity .4s;
  }
  .jp-field {
    background: rgba(255,255,255,.06);
    border: 1px solid rgba(255,255,255,.1);
    border-radius: 6px; padding: 12px 16px;
  }
  .jp-field-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px; color: rgba(255,255,255,.35); letter-spacing: .1em; text-transform: uppercase; margin-bottom: 5px;
  }
  .jp-field-val {
    font-family: 'Cormorant Garamond', serif;
    font-size: 16px; color: rgba(255,255,255,.75);
  }
  .jp-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .jp-chart-bar { height: 8px; background: var(--g600); border-radius: 4px; margin-top: 6px; }
  .jp-badge {
    display: inline-block; padding: 4px 10px;
    background: rgba(107,179,107,.2); border: 1px solid rgba(107,179,107,.4);
    border-radius: 4px; font-family: 'JetBrains Mono', monospace;
    font-size: 10px; color: var(--g300); letter-spacing: .06em;
  }
  .jp-rec {
    background: rgba(255,255,255,.04);
    border: 1px solid rgba(255,255,255,.08);
    border-left: 3px solid var(--g500);
    border-radius: 4px; padding: 12px 16px;
  }
  .jp-rec-title {
    font-family: 'Syne', sans-serif; font-size: 12px; font-weight: 600;
    color: rgba(255,255,255,.7); margin-bottom: 4px;
  }
  .jp-rec-text { font-size: 12px; color: rgba(255,255,255,.4); line-height: 1.5; }
  .jp-ai-bubble {
    background: rgba(107,179,107,.1); border: 1px solid rgba(107,179,107,.2);
    border-radius: 8px 8px 8px 2px; padding: 12px 16px;
    font-size: 13px; color: rgba(255,255,255,.7); line-height: 1.5;
  }
  .jp-user-bubble {
    align-self: flex-end;
    background: var(--g700); border-radius: 8px 8px 2px 8px; padding: 10px 16px;
    font-size: 13px; color: rgba(255,255,255,.8); line-height: 1.5;
    max-width: 75%;
  }
  .jp-timer {
    display: flex; gap: 3px; padding: 8px 28px 0;
  }
  .jp-timer-dot {
    height: 3px; flex: 1; border-radius: 2px;
    background: rgba(255,255,255,.12);
    overflow: hidden;
  }
  .jp-timer-fill {
    height: 100%; background: var(--g500); border-radius: 2px;
    transition: width 0.1s linear;
  }

  /* SIGN UP MODAL */
  .modal-overlay {
    position: fixed; inset: 0; z-index: 2000;
    background: rgba(10,51,41,.75);
    backdrop-filter: blur(6px);
    display: flex; align-items: center; justify-content: center;
    padding: 24px;
    animation: fadeIn .2s ease;
  }
  @keyframes fadeIn { from { opacity:0; } to { opacity:1; } }
  .modal-box {
    background: var(--white);
    border-radius: 12px;
    box-shadow: 0 24px 64px rgba(10,51,41,.3);
    width: 100%; max-width: 460px;
    overflow: hidden;
    animation: slideUp .25s cubic-bezier(.22,1,.36,1);
  }
  @keyframes slideUp { from { opacity:0; transform:translateY(24px); } to { opacity:1; transform:translateY(0); } }
  .modal-header {
    background: linear-gradient(135deg, #0A3329 0%, #1A7059 100%);
    padding: 32px 36px 28px;
  }
  .modal-logo {
    display: flex; align-items: center; gap: 10px; margin-bottom: 20px;
  }
  .modal-logo-hex {
    width: 28px; height: 28px;
    background: var(--g500);
    clip-path: polygon(50% 0%,93% 25%,93% 75%,50% 100%,7% 75%,7% 25%);
    display: flex; align-items: center; justify-content: center;
  }
  .modal-logo-text { font-family:'Syne',sans-serif; font-size:16px; font-weight:700; color:#E8F7F3; }
  .modal-title { font-family:'Cormorant Garamond',serif; font-size:30px; font-weight:300; color:#E8F7F3; line-height:1.1; margin-bottom:8px; }
  .modal-sub { font-size:14px; color:rgba(240,237,214,.55); line-height:1.5; }
  .modal-body { padding: 32px 36px 36px; }
  .modal-tabs {
    display: flex; gap: 0; margin-bottom: 28px;
    border-bottom: 1px solid var(--line);
  }
  .modal-tab {
    font-family:'Syne',sans-serif; font-size:12px; font-weight:600;
    letter-spacing:.06em; text-transform:uppercase;
    color:var(--muted); background:none; border:none;
    padding:10px 0; margin-right:28px; cursor:pointer;
    border-bottom:2px solid transparent; margin-bottom:-1px;
    transition: color .15s, border-color .15s;
  }
  .modal-tab.active { color:var(--g600); border-bottom-color:var(--g500); }
  .modal-field { margin-bottom: 18px; }
  .modal-label { font-family:'JetBrains Mono',monospace; font-size:10px; letter-spacing:.12em; text-transform:uppercase; color:var(--muted); margin-bottom:7px; display:block; }
  .modal-input {
    width:100%; padding:11px 14px;
    font-family:'Cormorant Garamond',serif; font-size:16px; color:var(--ink);
    background:var(--off); border:1px solid var(--line); border-radius:var(--r);
    transition: border-color .15s, box-shadow .15s;
    outline:none;
  }
  .modal-input:focus { border-color:var(--g500); box-shadow:0 0 0 3px rgba(125,122,71,.12); }
  .modal-btn {
    width:100%; padding:13px;
    font-family:'Syne',sans-serif; font-size:12px; font-weight:600;
    letter-spacing:.08em; text-transform:uppercase;
    background:var(--g500); color:#fff; border:none;
    border-radius:var(--r); cursor:pointer;
    transition: background .15s;
    margin-top:8px;
  }
  .modal-btn:hover { background:var(--g600); }
  .modal-divider { text-align:center; font-family:'JetBrains Mono',monospace; font-size:10px; color:var(--muted); margin:20px 0; position:relative; }
  .modal-divider::before,.modal-divider::after { content:''; position:absolute; top:50%; width:42%; height:1px; background:var(--line); }
  .modal-divider::before { left:0; } .modal-divider::after { right:0; }
  .modal-note { font-size:12px; color:var(--muted); text-align:center; margin-top:16px; line-height:1.5; }
  .modal-close {
    position:absolute; top:16px; right:16px;
    width:32px; height:32px; border-radius:50%;
    background:rgba(255,255,255,.12); border:none; cursor:pointer;
    color:rgba(240,237,214,.7); font-size:16px;
    display:flex; align-items:center; justify-content:center;
    transition: background .15s;
  }
  .modal-close:hover { background:rgba(255,255,255,.22); }
  .modal-success {
    text-align:center; padding:40px 36px;
  }
  .modal-success-icon {
    width:56px; height:56px; border-radius:50%;
    background:var(--g50); border:2px solid var(--g300);
    display:flex; align-items:center; justify-content:center;
    font-size:24px; margin:0 auto 20px;
  }
  .modal-success-title { font-family:'Cormorant Garamond',serif; font-size:28px; font-weight:300; color:var(--ink); margin-bottom:10px; }
  .modal-success-sub { font-size:15px; color:var(--muted); line-height:1.6; }

  /* Enhanced Footer Style */
  .footer {
    background: #061510;
    padding: 120px 80px 60px;
    color: #fff;
    border-top: 1px solid rgba(255,255,255,.06);
    position: relative;
    overflow: hidden;
  }
  .footer::before {
    content: ''; position: absolute; inset: 0; pointer-events: none;
    background-image: radial-gradient(circle at 10% 20%, rgba(46,168,136,.08) 0%, transparent 40%);
  }
  .footer-grid {
    display: grid;
    grid-template-columns: 1.6fr 1fr 1fr 1fr 1fr;
    gap: 48px;
    margin-bottom: 100px;
    position: relative; z-index: 1;
  }
  .footer-brand { display: flex; flex-direction: column; gap: 28px; }
  .footer-logo {
    display: flex; align-items: center; gap: 12px;
    font-family: 'Syne', sans-serif;
    font-size: 26px; font-weight: 700; color: #fff;
    letter-spacing: -.03em;
  }
  .footer-motto {
    font-family: 'Cormorant Garamond', serif;
    font-size: 24px; font-weight: 400; font-style: italic;
    color: #E8F7F3; line-height: 1.3;
    max-width: 360px;
  }
  .footer-mission {
    font-size: 14.5px; color: rgba(255,255,255,.5);
    line-height: 1.8; max-width: 400px;
    font-weight: 300;
  }
  .footer-contact { margin-top: 10px; }
  .footer-col-title {
    font-family: 'Syne', sans-serif;
    font-size: 11px; font-weight: 700; letter-spacing: .15em;
    text-transform: uppercase; color: var(--g400);
    margin-bottom: 32px;
  }
  .footer-link-list { display: flex; flex-direction: column; gap: 16px; align-items: flex-start; }
  .footer-link {
    font-family: inherit;
    font-size: 14.5px; color: rgba(255,255,255,.5);
    background: none; border: none; padding: 0;
    text-decoration: none; cursor: pointer;
    transition: all .2s;
    border-bottom: 1px solid transparent;
    width: fit-content;
    text-align: left;
    font-weight: 300;
  }
  .footer-link:hover { color: var(--g300); transform: translateX(6px); }
  
  .footer-bottom {
    border-top: 1px solid rgba(255,255,255,.08);
    padding-top: 48px;
    display: flex; justify-content: space-between; align-items: center;
    position: relative; z-index: 1;
  }
  .footer-copy {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; color: rgba(255,255,255,.2);
    letter-spacing: .05em;
  }
  .footer-legal { display: flex; gap: 32px; }
  .footer-legal-link {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; color: rgba(255,255,255,.2);
    background: none; border: none; padding: 0;
    text-decoration: none; transition: color .15s;
    text-transform: uppercase; letter-spacing: .1em;
    cursor: pointer;
  }
  .footer-legal-link:hover { color: var(--g300); }

  .footer-socials { display: flex; gap: 14px; margin-top: 10px; }
  .footer-social-icon {
    width: 36px; height: 36px; border-radius: 50%;
    background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.08);
    display: flex; align-items: center; justify-content: center;
    color: rgba(255,255,255,.4); cursor: pointer; transition: all .3s cubic-bezier(0.16, 1, 0.3, 1);
    font-size: 13px; font-family: 'Syne', sans-serif; font-weight: 600;
  }
  .footer-social-icon:hover { background: var(--g600); color: #fff; transform: translateY(-4px); border-color: var(--g400); }

  /* Transparency Page Styles */

  /* Transparency Page Theme Alignment */
  .trans-page { background: var(--white); min-height: 100vh; padding-top: 68px; }
  .trans-hero {
    background: #061510; padding: 140px 80px 100px; position: relative; overflow: hidden;
    border-bottom: 1px solid rgba(255,255,255,.05);
  }
  .trans-hero::before {
    content: ''; position: absolute; inset: 0;
    background: 
      radial-gradient(circle at 80% 20%, rgba(46,168,136,.15) 0%, transparent 50%),
      radial-gradient(circle at 20% 80%, rgba(46,168,136,.05) 0%, transparent 50%);
  }
  .trans-hero-tag {
    font-family: 'JetBrains Mono', monospace; font-size: 10px; color: var(--g400);
    letter-spacing: .25em; text-transform: uppercase; margin-bottom: 24px; display: block;
  }
  .trans-hero-title {
    font-family: 'Cormorant Garamond', serif; font-size: clamp(48px, 6vw, 84px);
    font-weight: 300; color: #E8F7F3; line-height: .95; letter-spacing: -.03em;
    max-width: 900px;
  }
  .trans-container {
    max-width: 1440px; margin: 0 auto; display: grid;
    grid-template-columns: 320px 1fr; gap: 100px; padding: 100px 80px;
  }
  .trans-sidebar { position: sticky; top: 120px; height: fit-content; }
  .trans-nav-title {
    font-family: 'Syne', sans-serif; font-size: 11px; font-weight: 800;
    text-transform: uppercase; letter-spacing: .15em; color: var(--g600);
    margin-bottom: 32px; padding-bottom: 12px; border-bottom: 1px solid var(--line);
  }
  .trans-nav-item {
    display: block; width: 100%; text-align: left; background: none; border: none;
    padding: 14px 20px; font-size: 14px; color: var(--muted); cursor: pointer;
    border-radius: 6px; transition: all .2s cubic-bezier(.4, 0, .2, 1); margin-bottom: 6px;
    font-family: 'Syne', sans-serif; font-weight: 500;
  }
  .trans-nav-item:hover { background: var(--g50); color: var(--g800); padding-left: 24px; }
  .trans-nav-item.active { background: var(--g600); color: #fff; font-weight: 600; box-shadow: 0 4px 12px rgba(34,143,114,.2); }

  .trans-section { margin-bottom: 120px; scroll-margin-top: 140px; animation: fadeUp .6s ease forwards; }
  .trans-section-tag {
    font-family: 'Syne', sans-serif; font-size: 12px; font-weight: 700; color: var(--g500);
    letter-spacing: .1em; text-transform: uppercase; margin-bottom: 20px; display: flex; align-items: center; gap:12px;
  }
  .trans-section-tag::before { content: ""; width: 24px; height: 1px; background: var(--g300); }
  .trans-section-title {
    font-family: 'Cormorant Garamond', serif; font-size: 48px; font-weight: 300;
    color: var(--ink); margin-bottom: 32px; letter-spacing: -.02em; line-height: 1.1;
  }
  .trans-text { 
    font-family: 'Cormorant Garamond', serif; font-size: 19px; color: var(--muted); 
    line-height: 1.7; margin-bottom: 32px; max-width: 760px; font-weight: 400;
  }
  
  .data-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 32px; margin-bottom: 48px; }
  .data-card {
    background: var(--white); border: 1px solid var(--line); border-radius: 8px; padding: 40px;
    box-shadow: var(--sh); transition: all .3s;
  }
  .data-card:hover { transform: translateY(-4px); box-shadow: var(--shm); border-color: var(--g300); }
  .data-card-title {
    font-family: 'Syne', sans-serif; font-size: 18px; font-weight: 700;
    color: var(--ink2); margin-bottom: 14px;
  }
  .data-card-text { font-family: 'Cormorant Garamond', serif; font-size: 16px; color: var(--muted); line-height: 1.6; font-weight: 400; }

  .method-table-wrap { border: 1px solid var(--line); border-radius: 8px; overflow: hidden; margin: 32px 0 48px; }
  .method-table {
    width: 100%; border-collapse: collapse;
    font-family: 'JetBrains Mono', monospace; font-size: 12px;
  }
  .method-table th {
    text-align: left; padding: 20px; background: var(--g50);
    border-bottom: 1px solid var(--line); color: var(--g700); text-transform: uppercase; letter-spacing: .08em;
    font-size: 11px; font-weight: 600;
  }
  .method-table td { padding: 18px 20px; border-bottom: 1px solid var(--line); color: var(--ink2); }
  .method-table tr:last-child td { border-bottom: none; }
  .method-table tr:hover { background: #fcfdfc; }
  
  .formula-box {
    background: #061510; border-radius: 12px; padding: 48px;
    margin-bottom: 48px; position: relative; overflow: hidden;
    box-shadow: 0 16px 40px rgba(0,0,0,.15);
  }
  .formula-box::after {
    content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: var(--g400);
  }
  .formula-label {
    font-family: 'JetBrains Mono', monospace; font-size: 10px; color: var(--g400);
    text-transform: uppercase; margin-bottom: 16px; letter-spacing: .15em;
  }
  .formula-text {
    font-family: 'JetBrains Mono', monospace; font-size: 22px; color: #E8F7F3;
    letter-spacing: .05em; font-weight: 400;
  }
  .formula-sub { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: rgba(255,255,255,.35); margin-top: 16px; }

  .research-item {
    background: var(--off); padding: 48px; border-radius: 12px; border: 1px solid var(--line);
    display: grid; grid-template-columns: 1fr 1fr; gap: 48px; align-items: start;
    transition: all .3s;
  }
  .research-item:hover { border-color: var(--g300); background: var(--white); box-shadow: var(--shm); }
  .blog-card {
    background: var(--white); border: 1px solid var(--line); border-radius: 8px; padding: 24px;
    display: flex; flex-direction: column; gap: 12px;
  }
  .blog-tag { font-family: 'JetBrains Mono', monospace; font-size: 9px; color: var(--g500); text-transform: uppercase; letter-spacing: .1em; }
  .blog-title { font-family: 'Syne', sans-serif; font-size: 16px; font-weight: 700; color: var(--ink); }
  .blog-excerpt { font-family: 'Cormorant Garamond', serif; font-size: 15px; color: var(--muted); line-height: 1.5; }

  /* Utility */
  .flex { display: flex; }
  .items-center { align-items: center; }
  .justify-between { justify-content: space-between; }
  .gap16 { gap: 16px; }
  .mt8 { margin-top: 8px; }
  .mt16 { margin-top: 16px; }
  .mt24 { margin-top: 24px; }
  .mt32 { margin-top: 32px; }
  .mt48 { margin-top: 48px; }
  .mb8  { margin-bottom: 8px; }
  .mb16 { margin-bottom: 16px; }
  .mb24 { margin-bottom: 24px; }
  .hr   { border: none; border-top: 1px solid var(--line); margin: 28px 0; }

  @keyframes fadeUp { from { opacity:0; transform:translateY(16px); } to { opacity:1; transform:translateY(0); } }
  .fade-up  { animation: fadeUp .4s ease forwards; }
  .fade-up2 { animation: fadeUp .4s ease .1s forwards; opacity:0; }
  .fade-up3 { animation: fadeUp .4s ease .2s forwards; opacity:0; }

  .w-full { width: 100%; }
  .text-right { text-align: right; }
  .text-center { text-align: center; }

  @keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
  }
  .processing-shimmer {
    background: linear-gradient(90deg, var(--muted) 25%, var(--g300) 50%, var(--muted) 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 600;
  }

  /* Verification Component */
  .verify-block {
    background: #F8F9FA; border: 1px solid var(--line); border-radius: 8px;
    padding: 20px; margin-bottom: 24px; display: flex; gap: 24px;
  }
  .verify-preview {
    width: 120px; height: 160px; background: var(--white); border: 1px solid var(--line);
    border-radius: 4px; display: flex; flex-direction: column; align-items: center; justify-content: center;
    overflow: hidden; flex-shrink: 0; position: relative;
  }
  .verify-preview img { width: 100%; height: 100%; object-fit: cover; }
  .verify-preview-icon { font-size: 32px; margin-bottom: 8px; }
  .verify-preview-label { font-size: 10px; color: var(--muted); text-align: center; padding: 0 8px; word-break: break-all; }
  
  .verify-content { flex: 1; }
  .verify-title { font-family: 'Syne', sans-serif; font-size: 15px; font-weight: 600; color: var(--ink); margin-bottom: 4px; }
  .verify-sub { font-size: 13px; color: var(--muted); margin-bottom: 16px; }
  
  .verify-data-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; margin-bottom: 20px; }
  .verify-data-item { background: var(--white); border: 1px solid var(--line); border-radius: 4px; padding: 10px 12px; }
  .verify-data-label { font-family: 'JetBrains Mono', monospace; font-size: 9px; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; margin-bottom: 4px; }
  .verify-data-val { font-size: 14px; color: var(--ink2); font-weight: 500; }

  .verify-question { border-top: 1px solid var(--line); padding-top: 16px; font-size: 14px; color: var(--ink); }
  .verify-actions { display: flex; gap: 12px; margin-top: 12px; }
  .btn-verify { 
    padding: 8px 16px; border-radius: 4px; font-size: 13px; cursor: pointer; border: 1px solid var(--line);
    background: var(--white); color: var(--ink); transition: all .15s;
  }
  .btn-verify.active { background: var(--ink); color: #fff; border-color: var(--ink); }
  .btn-verify:hover:not(.active) { background: #f0f0f0; }
`;

/* ── CALCULATION ENGINE ──────────────────────────────────────────────────────── */
const GEF = { default: 0.82, karnataka: 0.82, maharashtra: 0.79, delhi: 0.78, gujarat: 0.86, tamil_nadu: 0.76 };
const BENCHMARK = 3.1;
const BANDS = [
  { band: "Excellent", min: 0, max: 2.4, col: "#28541C", bg: "#EEF5EB" },
  { band: "Good", min: 2.4, max: 3.0, col: "#4E8A3A", bg: "#F2F8EE" },
  { band: "Industry Normal", min: 3.0, max: 3.6, col: "#B08020", bg: "#FDF8EC" },
  { band: "High Emitter", min: 3.6, max: Infinity, col: "#C05A2C", bg: "#FEF4F0" },
];

function calc(d) {
  const gef = GEF[d.state] || GEF.default;
  const ren = (d.renewable || 0) / 100;
  const dh = (d.hours || 8) * 22;
  const s1d = (d.diesel || 0) * 2.68;
  const s1p = (d.petrol || 0) * 2.31;
  const s1g = (d.natgas || 0) * 2.04;
  const s1l = (d.lpg || 0) * 1.51;
  const s1 = s1d + s1p + s1g + s1l;
  const s2e = (d.elec || 0) * (1 - ren) * gef;
  const s2la = (d.laptops || 0) * .065 * dh * gef / 1000;
  const s2de = (d.desktops || 0) * .2 * dh * gef / 1000;
  const s2mo = (d.monitors || 0) * .03 * dh * gef / 1000;
  const skw = (d.racks || 0) * 5 * .42 + (d.servers || 0) * .4;
  const s2sr = skw * (d.srvhrs || 24) * 30 * gef / 1000;
  const s2 = s2e + s2la + s2de + s2mo + s2sr;
  const s3c = (d.cloudbill || 0) / 8 * 0.00017 * 1000;
  const s3s = (d.services || 0) * 0.00015;
  const s3 = s3c + s3s;
  const tot = s1 + s2 + s3;
  const ann = tot * 12;
  const intensity = ann / Math.max(d.revenue || 1, .01);
  const band = BANDS.find(b => intensity >= b.min && intensity < b.max) || BANDS[3];
  return {
    s1, s2, s3, tot, ann, intensity, band,
    monthly: { s1, s2, s3, tot },
    annual: { s1: s1 * 12, s2: s2 * 12, s3: s3 * 12, tot: ann },
    bdown: {
      Diesel: s1d, Petrol: s1p, "Natural Gas": s1g, LPG: s1l,
      Electricity: s2e, Laptops: s2la, Desktops: s2de, Monitors: s2mo, Servers: s2sr,
      Cloud: s3c, Services: s3s
    },
  };
}

function findings(r, d) {
  const f = [];
  const add = (sev, scope, cat, msg, rec) => f.push({ sev, scope, cat, msg, rec });
  if ((d.diesel || 0) >= 1000) add("CRITICAL", "Scope 1", "Diesel Generator", `Critical diesel use: ${d.diesel} L/month = ${r.bdown.Diesel.toFixed(2)} tCO2e/month.`, "Switch to solar with battery backup. Audit all generator idle runtimes.");
  else if ((d.diesel || 0) >= 500) add("HIGH", "Scope 1", "Diesel Generator", `Elevated diesel at ${d.diesel} L/month.`, "Add battery backup systems to reduce generator dependency. Track runtime hours and cut non-essential loads during outages.");
  if ((d.renewable || 0) < 10) add("HIGH", "Scope 2", "Renewable Energy", "Renewable share under 10%. Electricity is your highest-leverage reduction lever.", "Switch some or all of your electricity to renewables. Rooftop solar or green energy tariffs from your provider can cut this directly. Even 25% renewable reduces your electricity footprint by 25%.");
  else if ((d.renewable || 0) >= 50) add("INFO", "Scope 2", "Renewable Energy", `Strong renewable mix at ${d.renewable}%. Above sector average.`, "Good work. Target 100% renewable as the next milestone.");
  if (r.tot > 0 && r.s2 / r.tot > 0.6) add("HIGH", "Scope 2", "Electricity", `Electricity is ${(r.s2 / r.tot * 100).toFixed(1)}% of your total. The dominant source.`, "Commission an energy audit. Upgrade to energy-efficient servers, enforce device sleep policies, and check your cooling setup.");
  if ((d.desktops || 0) > (d.laptops || 0) * .5 && (d.desktops || 0) > 10) add("MEDIUM", "Scope 2", "Device Fleet", `${d.desktops} desktops consume roughly 3x more power than equivalent laptops.`, "Replace desktops with laptops in your next hardware refresh. Estimated reduction: 20 to 30% on device-related emissions.");
  if ((!d.cloud || d.cloud === "none") && (d.servers || 0) > 5) add("MEDIUM", "Scope 3", "Cloud Migration", `${d.servers} on-premise servers with no cloud workloads.`, "Consider migrating some workloads to cloud. Large cloud providers run their infrastructure more efficiently than typical company server rooms.");
  if (r.intensity > BENCHMARK * 1.5) add("CRITICAL", "Overall", "Benchmark", `Your emission intensity of ${r.intensity.toFixed(2)} tCO2e/Rs Cr is ${((r.intensity / BENCHMARK - 1) * 100).toFixed(0)}% above the sector average.`, "Set a clear reduction target and focus on your two biggest emission sources first.");
  else if (r.intensity > BENCHMARK) add("HIGH", "Overall", "Benchmark", `Your intensity of ${r.intensity.toFixed(2)} tCO2e/Rs Cr is above the Indian IT sector average of ${BENCHMARK}.`, "Set annual reduction targets. Electricity-related actions tend to deliver the fastest results.");
  else if (r.intensity <= 2.4) add("INFO", "Overall", "Benchmark", `Excellent: ${r.intensity.toFixed(2)} tCO2e/Rs Cr. You are in the top quartile for Indian IT companies.`, "Maintain this trajectory. Consider making your results public as a differentiator with clients.");
  return f.sort((a, b) => ({ CRITICAL: 0, HIGH: 1, MEDIUM: 2, INFO: 3 }[a.sev] - { CRITICAL: 0, HIGH: 1, MEDIUM: 2, INFO: 3 }[b.sev]));
}

/* ── AI KNOWLEDGE ───────────────────────────────────────────────────────────── */
const KB = {
  greet: "Hi. I'm Carbonaire's assistant. Ask me anything about carbon emissions, what your results mean, or how to reduce your footprint.",
  renewable: "Renewable energy is the fastest way to cut electricity-related emissions. Options include rooftop solar (typically pays back in 4 to 6 years), purchasing renewable energy credits to offset your grid usage, or group power arrangements for larger organisations. Even switching 25% of your electricity to renewables cuts that portion of your footprint by 25%.",
  benchmark: `The Indian IT sector average is 3.1 tCO2e per Rs Crore of revenue. If you're below that, you're doing better than most. The top-performing companies come in below 2.4. These figures come from industry disclosure data across Indian IT and technology companies.`,
  scope: "Emissions are split into three categories. Direct (Scope 1) covers fuel you burn on-site: generators, vehicles, gas. Electricity (Scope 2) covers your grid power bill, the biggest source for most IT companies. Indirect (Scope 3) covers everything else: cloud computing, outsourced services, device manufacturing. Most IT companies have Scope 2 as 55 to 70% of their total.",
  cloud: "Migrating workloads to cloud typically reduces server-related emissions by 20 to 40% compared to running your own servers. Large cloud providers run their data centres more efficiently and use more renewable energy than a typical company server room. Google Cloud currently has the lowest carbon intensity, followed by Azure and AWS.",
  default: "The three highest-impact steps for most IT companies are: (1) Switch some or all of your electricity to renewables, which cuts the biggest slice of your footprint; (2) Improve server room efficiency, as better cooling arrangements reduce energy waste; (3) Move some workloads to cloud, since large providers are more energy-efficient than typical on-premise setups. Would you like to know more about any of these?",
};
function aiReply(m) {
  const l = m.toLowerCase();
  if (/\bhello\b|\bhi\b|\bhey\b/.test(l)) return KB.greet;
  if (/renewable|solar|wind|energy/.test(l)) return KB.renewable;
  if (/benchmark|average|median|industry|compare/.test(l)) return KB.benchmark;
  if (/\bscope\b|what is|how does|explain|definition/.test(l)) return KB.scope;
  if (/cloud|aws|azure|gcp|server|migration/.test(l)) return KB.cloud;
  return KB.default;
}

/* ── DONUT CHART ──────────────────────────────────────────────────────────── */
function DonutChart({ data, size = 160 }) {
  const total = data.reduce((s, d) => s + d.value, 0);
  if (total === 0) return null;
  const r = 58, cx = 80, cy = 80, circ = 2 * Math.PI * r;
  let offset = 0;
  const slices = data.map(d => {
    const pct = d.value / total;
    const dash = pct * circ;
    const slice = { ...d, dash, offset, pct };
    offset += dash;
    return slice;
  });
  return (
    <svg viewBox="0 0 160 160" width={size} height={size}>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--g50)" strokeWidth="20" />
      {slices.map((s, i) => (
        <circle key={i} cx={cx} cy={cy} r={r} fill="none"
          stroke={s.color} strokeWidth="20"
          strokeDasharray={`${s.dash} ${circ - s.dash}`}
          strokeDashoffset={-s.offset + circ * .25}
          style={{ transition: `stroke-dasharray 1s cubic-bezier(.22,1,.36,1) ${i * .15}s` }}
        />
      ))}
      <text x={cx} y={cy - 4} textAnchor="middle" fontSize="11" fill="var(--muted)" fontFamily="JetBrains Mono, monospace">tCO2e</text>
      <text x={cx} y={cy + 14} textAnchor="middle" fontSize="13" fill="var(--ink)" fontFamily="JetBrains Mono, monospace" fontWeight="500">
        {total.toFixed(2)}
      </text>
    </svg>
  );
}

/* ── GAUGE CHART ──────────────────────────────────────────────────────────── */
function GaugeSVG({ value, max = 9, color }) {
  const pct = Math.min(value / max, 1);
  const r = 80, cx = 100, cy = 100;
  const toXY = (deg) => {
    const rad = (deg - 90) * Math.PI / 180;
    return [cx + r * Math.cos(rad), cy + r * Math.sin(rad)];
  };
  const arcPath = (from, to, col, sw = 16) => {
    const [x1, y1] = toXY(from); const [x2, y2] = toXY(to);
    const large = (to - from) > 180 ? 1 : 0;
    return <path d={`M${x1},${y1} A${r},${r} 0 ${large},1 ${x2},${y2}`} fill="none" stroke={col} strokeWidth={sw} strokeLinecap="round" />;
  };
  const [nx, ny] = toXY(-90 + pct * 180);
  return (
    <svg viewBox="0 0 200 110" className="gauge-svg">
      {arcPath(-90, 90, "var(--g50)")}
      {arcPath(-90, -90 + pct * 180, color)}
      <circle cx={nx} cy={ny} r="6" fill="var(--white)" stroke={color} strokeWidth="2" />
      {[-90, -45, 0, 45, 90].map((a, i) => {
        const [x, y] = toXY(a);
        return <circle key={i} cx={x} cy={y} r="2" fill="var(--line)" />;
      })}
    </svg>
  );
}



/* ── PROFILE DROPDOWN COMPONENT ─────────────────────────────────────────── */
const ProfileDropdown = ({ user, onLogout, onDashboard }) => {
  return (
    <div className="profile-trigger-wrap">
      <div className="profile-trigger">
        <div className="profile-avatar">{user.name.charAt(0).toUpperCase()}</div>
        <div className="profile-name">{user.name}</div>
      </div>
      <div className="profile-dropdown">
        <div className="dropdown-header">
          <div className="profile-name" style={{ color: "var(--ink2)", fontSize: 14 }}>{user.name}</div>
          <div className="dropdown-email">{user.email}</div>
        </div>
        <button className="dropdown-item" onClick={() => onDashboard("assessments")}>
          User Dashboard
        </button>
        <button className="dropdown-item" onClick={() => onDashboard("api_keys")}>
          API Access & Keys
        </button>
        <button className="dropdown-item" onClick={() => onDashboard("data_residency")}>
          Data Residency Settings
        </button>
        <button className="dropdown-item" style={{ borderTop: "1px solid var(--off)" }} onClick={() => onDashboard("account")}>
          Account Settings
        </button>
        <button className="dropdown-item logout" onClick={onLogout}>
          Log Out
        </button>
      </div>
    </div>
  );
};

/* ── UNIFIED NAVBAR COMPONENT ─────────────────────────────────────────── */
const Navbar = ({ page, user, setUser, setPage, scrolled, setShowSignup, goCalculator, result, setStep }) => {
  const isScrolled = scrolled || (page !== "home" && page !== "transparency");

  const onLogout = () => {
    localStorage.removeItem("carbonaire_token");
    localStorage.setItem("carbonaire_user", "");
    setUser(null);
    setPage("home");
  };

  const scrollTo = (sectionId) => {
    if (page !== "home") {
      setPage("home");
      setTimeout(() => {
        document.getElementById(sectionId)?.scrollIntoView({ behavior: "smooth" });
      }, 300);
    } else {
      document.getElementById(sectionId)?.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <nav className={`nav-bar${isScrolled ? " scrolled" : ""}`} style={page === "ai" ? { background: "#071a14", borderBottom: "1px solid rgba(255,255,255,.06)" } : {}}>
      <div className="nav-left">
        <div className="nav-logo" onClick={() => setPage("home")}>
          <div className="nav-hex"><span>C</span></div>
          <span style={page === "ai" ? { color: "#E8F7F3" } : {}}>Carbonaire</span>
        </div>
      </div>

      <div className="nav-center">
        <div className="nav-links">
          <button className="nav-link" onClick={() => setPage("home")}>Home</button>
          <button className="nav-link" onClick={() => scrollTo("mission")}>Mission</button>
          <button className="nav-link" onClick={() => scrollTo("journey")}>Journey</button>
          <button className="nav-link" onClick={() => scrollTo("what-we-do")}>Solutions</button>
          {page === "results" ? (
             <button className="nav-link" onClick={() => { setStep(0); goCalculator(); }}>Recalculate</button>
          ) : (
             <button className="nav-link" onClick={goCalculator}>Calculator</button>
          )}
          {result && page !== "results" && <button className="nav-link" onClick={() => setPage("results")}>Results</button>}
        </div>
      </div>

      <div className="nav-right">
        <div className="nav-actions">
           {page === "results" && (
             <button className="nav-cta" onClick={() => setPage("ai")}>AI Advisor</button>
           )}
           {user ? (
             <ProfileDropdown 
               user={user} 
               onDashboard={(tab) => {
                 setPage("dashboard");
                 // We'll need a way to pass the tab to the dashboard. 
                 // Since Dashboard is a child of App, we can use a state.
                 setDashTab(tab || "assessments");
               }}
               onLogout={onLogout} 
             />
           ) : (
             <>
               <button className="nav-link" onClick={() => setShowSignup(true)}>Sign In</button>
               <button className="nav-signup" onClick={() => setShowSignup(true)}>Sign Up</button>
             </>
           )}
        </div>
      </div>
    </nav>
  );
};


/* ── TRANSPARENCY PAGE ───────────────────────────────────────────────────── */
function TransparencyPage({ setPage, goCalculator, user, setUser, setShowSignup, page, scrolled, result, setStep }) {
  const [activeSec, setActiveSec] = useState("methodology");
  const sections = [
    { id: "methodology", label: "Core Methodology" },
    { id: "sources", label: "Authoritative Sources" },
    { id: "research", label: "Research & Blogs" },
    { id: "governance", label: "Security & Governance" },
    { id: "platform", label: "Architecture" },
  ];

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveSec(entry.target.id);
          }
        });
      },
      { threshold: 0.2, rootMargin: "-10% 0px -60% 0px" }
    );

    sections.forEach((s) => {
      const el = document.getElementById(s.id);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  const scrollToAnchor = (sectionId) => {
    setActiveSec(sectionId);
    document.getElementById(sectionId)?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="trans-page">
      <style>{GLOBAL_CSS}</style>

      <Navbar 
        page={page} 
        user={user} 
        setUser={setUser} 
        setPage={setPage} 
        scrolled={scrolled} 
        setShowSignup={setShowSignup} 
        goCalculator={goCalculator} 
        result={result}
        setStep={setStep}
      />

      <div className="trans-hero">
        <span className="trans-hero-tag">Transparency & Methodology Documentation</span>
        <h1 className="trans-hero-title">Engineering Carbon Accountability with Data Rigor</h1>
      </div>

      <div className="trans-container">
        <aside className="trans-sidebar">
          <div className="trans-nav-title">Documentation Hub</div>
          {sections.map(s => (
            <button key={s.id} 
              className={`trans-nav-item${activeSec === s.id ? " active" : ""}`}
              onClick={() => {
                setActiveSec(s.id);
                document.getElementById(s.id)?.scrollIntoView({ behavior: "smooth" });
              }}
            >
              {s.label}
            </button>
          ))}
          <div style={{ marginTop: 40, padding: 24, background: "var(--g50)", borderRadius: 12, border: "1px solid var(--line)" }}>
            <div style={{ fontFamily: "Syne,sans-serif", fontSize: 13, fontWeight: 700, color: "var(--g800)", marginBottom: 8 }}>Auditor Access</div>
            <div style={{ fontFamily: "Cormorant Garamond,serif", fontSize: 14, color: "var(--muted)", lineHeight: 1.5, marginBottom: 16 }}>Enterprise clients can request detailed audit trails for every calculation performed.</div>
            <button className="nav-cta" style={{ width: "100%", marginLeft: 0 }}>Request Data Export</button>
          </div>
        </aside>

        <main className="trans-content">
          <section id="methodology" className="trans-section">
            <div className="trans-section-tag">Methodology 01</div>
            <h2 className="trans-section-title">GHG Protocol Alignment</h2>
            <p className="trans-text">Carbonaire utilizes the <strong>GHG Protocol Corporate Accounting and Reporting Standard</strong>. We categorize emissions into three distinct scopes to provide a comprehensive view of your environmental impact.</p>
            
            <div className="data-grid">
              <div className="data-card">
                <div className="data-card-title">Scope 1: Direct</div>
                <p className="data-card-text">Emissions from sources owned or controlled by the company, such as diesel generators and company-owned vehicle fleets.</p>
              </div>
              <div className="data-card">
                <div className="data-card-title">Scope 2: Energy</div>
                <p className="data-card-text">Indirect emissions from the generation of purchased electricity consumed by the company. This is the primary driver for IT firms.</p>
              </div>
              <div className="data-card" style={{ gridColumn: "span 2" }}>
                <div className="data-card-title">Scope 3: Value Chain</div>
                <p className="data-card-text">All other indirect emissions that occur in the company's value chain, including cloud infrastructure (AWS/Azure/GCP), hardware manufacturing, and business travel.</p>
              </div>
            </div>

            <div className="formula-box">
              <div className="formula-label">Core Calculation Engine</div>
              <div className="formula-text">Emission = Activity Data × Emission Factor (EF)</div>
              <div className="formula-sub">Example: kWh × (kg CO2e / kWh) = total CO2e. We use GWP100 constants from IPCC AR6.</div>
            </div>
          </section>

          <section id="sources" className="trans-section">
            <div className="trans-section-tag">Sources 02</div>
            <h2 className="trans-section-title">Peer-Reviewed Data & Citations</h2>
            <p className="trans-text">Our engine is built upon authoritative datasets to ensure scientific validity and regulatory compliance.</p>
            <ul style={{ listStyle: "none", padding: 0 }}>
              {[
                { name: "IPCC Sixth Assessment Report (AR6)", data: "The global gold standard for Global Warming Potential (GWP) values. We utilize AR6 GWP100 constants for all greenhouse gas conversions." },
                { name: "CEA India User Guide V19.0", data: "Primary source for All India Grid Emission Factors. Includes regional intensity variations for Maharashtra, Karnataka, and Gujarat." },
                { name: "GHG Protocol Tech Guidance", data: "Standardized procedures for calculating Scope 3 emissions from purchased goods and services." },
                { name: "IEA World Energy Outlook", data: "Global benchmarks for data center energy intensity and renewable transition paths." }
              ].map(s => (
                <li key={s.name} style={{ padding: "24px 0", borderBottom: "1px solid var(--line)" }}>
                  <div style={{ fontFamily: "Syne,sans-serif", fontWeight: 700, fontSize: 16, color: "var(--ink)", marginBottom: 8 }}>{s.name}</div>
                  <div className="data-card-text">{s.data}</div>
                </li>
              ))}
            </ul>
          </section>

          <section id="research" className="trans-section">
            <div className="trans-section-tag">Insights 03</div>
            <h2 className="trans-section-title">Current Research & Blogs</h2>
            <p className="trans-text">Explore our latest findings on sustainable technology and sector-specific carbon benchmarking.</p>
            
            <div className="research-item" style={{ marginBottom: 40 }}>
               <div className="blog-card">
                  <span className="blog-tag">Whitepaper</span>
                  <h3 className="blog-title">OCR-Based Utility Audit</h3>
                  <p className="blog-excerpt">Exploring how Tesseract-based ML models can verify utility bill data to eliminate "green-guessing" in corporate disclosures.</p>
                  <button className="footer-link" style={{ marginTop: "auto", color: "var(--g600)" }}>Read Paper →</button>
               </div>
               <div className="blog-card">
                  <span className="blog-tag">Benchmark</span>
                  <h3 className="blog-title">India Tech Outlook 2026</h3>
                  <p className="blog-excerpt">A longitudinal study of 400+ Indian IT firms shows a 14% drop in Scope 2 intensity due to grid decarbonization.</p>
                  <button className="footer-link" style={{ marginTop: "auto", color: "var(--g600)" }}>View Data →</button>
               </div>
            </div>

            <div className="research-item">
               <div className="blog-card">
                  <span className="blog-tag">Blog</span>
                  <h3 className="blog-title">The Cloud Efficiency Gap</h3>
                  <p className="blog-excerpt">Why moving to serverless can reduce your compute footprint by up to 60% compared to legacy EC2 instances.</p>
                  <button className="footer-link" style={{ marginTop: "auto", color: "var(--g600)" }}>Read More →</button>
               </div>
               <div className="blog-card">
                  <span className="blog-tag">Blog</span>
                  <h3 className="blog-title">Green Coding Principles</h3>
                  <p className="blog-excerpt">Practical steps for engineers to reduce energy consumption through algorithmic efficiency and payload optimization.</p>
                  <button className="footer-link" style={{ marginTop: "auto", color: "var(--g600)" }}>Read More →</button>
               </div>
            </div>
          </section>

          <section id="governance" className="trans-section">
            <div className="trans-section-tag">Security 04</div>
            <h2 className="trans-section-title">Data Security & Compliance</h2>
            <p className="trans-text">Carbonaire follows strict data residency and security protocols to protect sensitive corporate operational data.</p>
            <div className="data-grid">
              <div className="data-card" style={{ borderTop: "4px solid var(--g500)" }}>
                <div className="data-card-title">AES-256 Encryption</div>
                <p className="data-card-text">All organizational inputs and calculated results are encrypted at rest and in transit using military-grade AES-256 protocols.</p>
              </div>
              <div className="data-card" style={{ borderTop: "4px solid var(--g500)" }}>
                <div className="data-card-title">SOC 2 Alignment</div>
                <p className="data-card-text">Our data handling processes are designed to align with AICPA SOC 2 Type II trust principles for security and confidentiality.</p>
              </div>
              <div className="data-card" style={{ gridColumn: "span 2" }}>
                <div className="data-card-title">Data Anonymization</div>
                <p className="data-card-text">Sector benchmarking data is strictly anonymized. Individual company metrics are never shared with third parties without explicit consent.</p>
              </div>
            </div>
          </section>

          <section id="platform" className="trans-section">
            <div className="trans-section-tag">Architecture 05</div>
            <h2 className="trans-section-title">Platform Infrastructure</h2>
            <p className="trans-text">Carbonaire is a cloud-native platform designed for high availability and verifiable accuracy.</p>
            <div className="data-grid">
              <div className="data-card">
                <div className="data-card-title">Precision Engine</div>
                <p className="data-card-text">Built on Python/FastAPI for high-concurrency calculation requests and sub-millisecond processing.</p>
              </div>
              <div className="data-card">
                <div className="data-card-title">Audit Log</div>
                <p className="data-card-text">Maintains immutable records of calculation versions and emission factor timestamps for audit traceability.</p>
              </div>
            </div>
          </section>

          <section id="simulation-principles" className="trans-section">
            <div className="trans-section-tag">Simulation 06</div>
            <h2 className="trans-section-title">Simulation Principles</h2>
            <p className="trans-text">The Carbonaire Simulation Engine uses dynamic modeling to project long-term environmental and financial outcomes.</p>
            <div className="data-grid">
              <div className="data-card" style={{ background: "var(--g50)", border: "1px solid var(--g200)" }}>
                <div className="data-card-title">Dynamic Modeling</div>
                <p className="data-card-text">Our engine adjusts emissions based on operational levers—modeling how renewable adoption reduces Scope 2 while cloud migration shifts footprints to Scope 3.</p>
              </div>
              <div className="data-card" style={{ background: "var(--g50)", border: "1px solid var(--g200)" }}>
                <div className="data-card-title">50-Year Trajectory</div>
                <p className="data-card-text">Long-term projections utilize a 2% CAGR for business growth, overlaid with strategic interventions to show your net-zero alignment path.</p>
              </div>
              <div className="data-card" style={{ gridColumn: "span 2", background: "var(--g800)", color: "#fff" }}>
                <div className="data-card-title" style={{ color: "var(--g300)" }}>Financial ROI Logic</div>
                <p className="data-card-text" style={{ color: "rgba(255,255,255,0.7)" }}>Operational savings are calculated by multiplying carbon avoidance (tonnes) with local energy pricing and proxy carbon tax rates (approx. ₹12,500/tCO2e).</p>
              </div>
            </div>
          </section>
        </main>
      </div>
      <Footer setPage={setPage} goCalculator={goCalculator} />
    </div>
  );
}

/* ── FOOTER COMPONENT ─────────────────────────────────────────────────────── */
function Footer({ setPage, goCalculator }) {
  const scrollTo = (pageId, sectionId) => {
    setPage(pageId);
    setTimeout(() => {
      document.getElementById(sectionId)?.scrollIntoView({ behavior: "smooth" });
    }, 150);
  };

  const scrollToSection = (sectionId) => {
    setPage("home");
    setTimeout(() => {
      document.getElementById(sectionId)?.scrollIntoView({ behavior: "smooth" });
    }, 300);
  };

  return (
    <footer className="footer">
      <div className="footer-grid">
        <div className="footer-brand">
          <div className="footer-logo">
            <div className="nav-hex" style={{ width: 34, height: 34 }}><span>C</span></div>
            Carbonaire
          </div>
          <div className="footer-mission" style={{ color: "var(--g300)", fontWeight: 500, lineHeight: 1.6 }}>
            Advanced Carbon Intelligence for the Global Technology Sector. Measure, benchmark, and decarbonize your digital infrastructure with precision engineering and authoritative data rigor.
          </div>
          <div className="footer-contact">
            <div className="footer-col-title" style={{ marginBottom: 12 }}>Corporate Inquiry</div>
            <a href="mailto:carbonaire@gmail.com" className="footer-link">carbonaire@gmail.com</a>
          </div>
          <div className="footer-socials">
            {['X', 'LinkedIn', 'Instagram'].map(s => (
              <div key={s} className="footer-social-icon">{s}</div>
            ))}
          </div>
        </div>

        <div>
          <div className="footer-col-title">Transparency</div>
          <div className="footer-link-list">
            <button className="footer-link" onClick={() => scrollTo("transparency", "sources")}>Research Papers</button>
            <button className="footer-link" onClick={() => scrollTo("transparency", "methodology")}>Methodology Hub</button>
            <button className="footer-link" onClick={() => scrollTo("transparency", "research")}>Our Research</button>
            <button className="footer-link" onClick={() => scrollTo("transparency", "methodology")}>GHG Scopes (1, 2, 3)</button>
            <button className="footer-link" onClick={() => scrollTo("transparency", "simulation-principles")}>Simulation Principles</button>
          </div>
        </div>

        <div>
          <div className="footer-col-title">Our Company</div>
          <div className="footer-link-list">
            <button className="footer-link" onClick={() => scrollToSection("mission")}>Corporate Motto</button>
            <button className="footer-link" onClick={() => scrollToSection("mission")}>Our Mission</button>
            <button className="footer-link" onClick={() => scrollTo("transparency", "research")}>Impact Blogs</button>
            <button className="footer-link" onClick={() => scrollTo("transparency", "research")}>Case Studies</button>
          </div>
        </div>

        <div>
          <div className="footer-col-title">Platform Hub</div>
          <div className="footer-link-list">
            <button className="footer-link" onClick={() => setPage("home")}>Home Interface</button>
            <button className="footer-link" onClick={() => scrollToSection("mission")}>Mission Profile</button>
            <button className="footer-link" onClick={() => scrollToSection("journey")}>Operational Journey</button>
            <button className="footer-link" onClick={() => scrollToSection("what-we-do")}>Product Solutions</button>
            <button className="footer-link" onClick={goCalculator}>Carbon Calculator</button>
          </div>
        </div>

        <div>
          <div className="footer-col-title">Security & Trust</div>
          <div className="footer-link-list">
            <button className="footer-link" onClick={() => scrollTo("transparency", "governance")}>Security & Compliance</button>
            <button className="footer-link" onClick={() => scrollTo("transparency", "governance")}>Data Security Rules</button>
            <button className="footer-link" onClick={() => scrollTo("transparency", "governance")}>Encryption Protocols</button>
            <button className="footer-link" onClick={() => scrollTo("transparency", "governance")}>SOC 2 Alignment</button>
            <button className="footer-link" onClick={() => scrollTo("transparency", "governance")}>Compliance Guide</button>
          </div>
        </div>
      </div>

      <div className="footer-bottom">
        <div className="footer-copy">
          © 2026 CARBONAIRE GLOBAL · EMISSION FACTORS SOURCED FROM PEER-REVIEWED DATASETS (CEA, GHG PROTOCOL, IPCC AR6).
        </div>
        <div className="footer-legal">
          <button className="footer-legal-link" onClick={() => scrollTo("transparency", "governance")}>Privacy Policy</button>
          <button className="footer-legal-link" onClick={() => scrollTo("transparency", "governance")}>Terms of Service</button>
          <button className="footer-legal-link" onClick={() => scrollTo("transparency", "governance")}>Security Policy</button>
        </div>
      </div>
    </footer>
  );
}

/* ── SIGN UP MODAL ───────────────────────────────────────────────────────── */
function SignUpModal({ onClose, onAuthSuccess }) {
  const [tab, setTab] = useState("signup");
  const [done, setDone] = useState(false);
  const [formData, setFormData] = useState({ name: "", email: "", company: "", password: "" });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const set = (k, v) => setFormData(p => ({ ...p, [k]: v }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");

    try {
      const res = await fetch(
        `${API_BASE}${tab === "signup" ? "/api/auth/register" : "/api/auth/login"}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(
            tab === "signup"
              ? {
                  email: formData.email,
                  name: formData.name,
                  password: formData.password,
                  company_name: formData.company,
                }
              : {
                  email: formData.email,
                  password: formData.password,
                }
          ),
        }
      );
      const data = await res.json();

      if (!data.ok) {
        setError(data.error || data.detail || "Authentication failed. Please try again.");
        return;
      }

      const user = {
        user_id: data.user_id || null,
        name: data.name || formData.name,
        email: data.email || formData.email,
        company_name: formData.company || "",
      };

      storeAuthSession({ token: data.token, user });
      onAuthSuccess?.(user);
      setDone(true);
    } catch (err) {
      console.error("Authentication failed:", err);
      setError("Could not reach the authentication service. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal-box" style={{ position: "relative" }}>
        <div className="modal-header">
          <div className="modal-logo">
            <div className="modal-logo-hex"><span style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 11, color: "#fff", fontWeight: 500 }}>C</span></div>
            <span className="modal-logo-text">Carbonaire</span>
          </div>
          <div className="modal-title">{done ? "You're in." : tab === "signup" ? "Create your account" : "Welcome back"}</div>
          <div className="modal-sub">{done ? "Your account is ready and your session is active." : tab === "signup" ? "Free forever. No credit card required." : "Sign in to access your assessments."}</div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        {done ? (
          <div className="modal-success">
            <div className="modal-success-icon">✓</div>
            <div className="modal-success-title">{tab === "signup" ? "Account created" : "Signed in"}</div>
            <div className="modal-success-sub">Signed in as <strong>{formData.email}</strong>. Your future assessments can now be saved and personalized.</div>
            <button className="modal-btn" style={{ marginTop: 24 }} onClick={onClose}>Start Your Assessment →</button>
          </div>
        ) : (
          <div className="modal-body">
            <div className="modal-tabs">
              <button className={`modal-tab${tab === "signup" ? " active" : ""}`} onClick={() => setTab("signup")}>Sign Up</button>
              <button className={`modal-tab${tab === "login" ? " active" : ""}`} onClick={() => setTab("login")}>Log In</button>
            </div>

            <form onSubmit={handleSubmit}>
              {tab === "signup" && (
                <>
                  <div className="modal-field">
                    <label className="modal-label">Your Name</label>
                    <input className="modal-input" type="text" placeholder="e.g. Arjun Sharma" value={formData.name} onChange={e => set("name", e.target.value)} required />
                  </div>
                  <div className="modal-field">
                    <label className="modal-label">Company Name</label>
                    <input className="modal-input" type="text" placeholder="e.g. TechNova Solutions" value={formData.company} onChange={e => set("company", e.target.value)} />
                  </div>
                </>
              )}
              <div className="modal-field">
                <label className="modal-label">Work Email</label>
                <input className="modal-input" type="email" placeholder="you@company.com" value={formData.email} onChange={e => set("email", e.target.value)} required />
              </div>
              <div className="modal-field">
                <label className="modal-label">Password</label>
                <input className="modal-input" type="password" placeholder={tab === "signup" ? "Create a password (min. 8 chars)" : "Your password"} value={formData.password} onChange={e => set("password", e.target.value)} required minLength={8} />
              </div>
              {error && <div style={{ marginBottom: 12, color: "#A33C15", fontSize: 13, lineHeight: 1.5 }}>{error}</div>}
              <button className="modal-btn" type="submit" disabled={submitting}>{submitting ? "Please wait..." : tab === "signup" ? "Create Free Account" : "Sign In"}</button>
            </form>

            <div className="modal-note">
              {tab === "signup"
                ? <>Already have an account? <span style={{ color: "var(--g600)", cursor: "pointer", textDecoration: "underline" }} onClick={() => setTab("login")}>Log in</span></>
                : <>No account yet? <span style={{ color: "var(--g600)", cursor: "pointer", textDecoration: "underline" }} onClick={() => setTab("signup")}>Sign up free</span></>
              }
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ── JOURNEY SECTION COMPONENT ───────────────────────────────────────────── */
function JourneySection({ onStart }) {
  const [active, setActive] = useState(0);
  const [progress, setProgress] = useState(0);
  const intervalRef = useRef(null);
  const DURATION = 4000;
  const TICK = 50;

  const steps = [
    {
      num: "01",
      title: "Enter Your Data",
      sub: "Answer a few simple questions about your company, energy use, and devices. No expertise required.",
      preview: "input"
    },
    {
      num: "02",
      title: "Outputs & Reports",
      sub: "Get a full emissions breakdown with visual charts and benchmarking against the Indian IT sector.",
      preview: "output"
    },
    {
      num: "03",
      title: "Recommendations & AI",
      sub: "Receive a personalised action plan and chat with our AI assistant for tailored guidance.",
      preview: "ai"
    }
  ];

  useEffect(() => {
    setProgress(0);
    clearInterval(intervalRef.current);
    intervalRef.current = setInterval(() => {
      setProgress(p => {
        if (p >= 100) {
          setActive(a => (a + 1) % steps.length);
          return 0;
        }
        return p + (TICK / DURATION * 100);
      });
    }, TICK);
    return () => clearInterval(intervalRef.current);
  }, [active]);

  const handleStepClick = (i) => {
    setActive(i);
    setProgress(0);
  };

  const InputPreview = () => (
    <div className="journey-preview-content">
      <div className="jp-row">
        <div className="jp-field">
          <div className="jp-field-label">Company Name</div>
          <div className="jp-field-val">TechNova Solutions</div>
        </div>
        <div className="jp-field">
          <div className="jp-field-label">State</div>
          <div className="jp-field-val">Karnataka</div>
        </div>
      </div>
      <div className="jp-row">
        <div className="jp-field">
          <div className="jp-field-label">Employees</div>
          <div className="jp-field-val">120</div>
        </div>
        <div className="jp-field">
          <div className="jp-field-label">Annual Revenue</div>
          <div className="jp-field-val">Rs 24 Cr</div>
        </div>
      </div>
      <div className="jp-field">
        <div className="jp-field-label">Monthly Electricity</div>
        <div className="jp-field-val">18,500 kWh</div>
        <div className="jp-chart-bar" style={{ width: "72%", background: "var(--g600)" }} />
      </div>
      <div className="jp-row">
        <div className="jp-field">
          <div className="jp-field-label">Laptops</div>
          <div className="jp-field-val">95</div>
        </div>
        <div className="jp-field">
          <div className="jp-field-label">Servers</div>
          <div className="jp-field-val">8</div>
        </div>
      </div>
    </div>
  );

  const OutputPreview = () => (
    <div className="journey-preview-content">
      <div style={{ display: "flex", gap: 8, marginBottom: 4 }}>
        <span className="jp-badge">Good</span>
        <span style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 10, color: "rgba(255,255,255,.4)", alignSelf: "center" }}>Below sector average</span>
      </div>
      <div className="jp-field">
        <div className="jp-field-label">Total Annual Emissions</div>
        <div style={{ fontFamily: "Cormorant Garamond,serif", fontSize: 32, fontWeight: 300, color: "var(--g300)", marginTop: 4 }}>47.2 tCO2e</div>
      </div>
      {[
        { label: "Electricity", pct: 68, col: "var(--g500)" },
        { label: "Devices", pct: 19, col: "var(--g600)" },
        { label: "Cloud", pct: 13, col: "#2E5A8A" },
      ].map(b => (
        <div key={b.label} style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 10, color: "rgba(255,255,255,.4)", width: 70 }}>{b.label}</div>
          <div style={{ flex: 1, height: 16, background: "rgba(255,255,255,.06)", borderRadius: 2, overflow: "hidden" }}>
            <div style={{ height: "100%", width: `${b.pct}%`, background: b.col, borderRadius: 2 }} />
          </div>
          <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 10, color: "rgba(255,255,255,.5)", width: 32 }}>{b.pct}%</div>
        </div>
      ))}
      <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 10, color: "rgba(255,255,255,.3)", marginTop: 4 }}>
        Intensity: 1.97 tCO2e / Rs Cr · Top quartile
      </div>
    </div>
  );

  const AiPreview = () => (
    <div className="journey-preview-content" style={{ gap: 10 }}>
      <div className="jp-rec">
        <div className="jp-rec-title">Switch to renewable energy tariff</div>
        <div className="jp-rec-text">Reduce electricity emissions by up to 40%. Your biggest single action.</div>
      </div>
      <div className="jp-rec">
        <div className="jp-rec-title">Replace desktops with laptops</div>
        <div className="jp-rec-text">Desktops use 3x more power. Swap on next refresh for 20 to 30% device savings.</div>
      </div>
      <div style={{ borderTop: "1px solid rgba(255,255,255,.08)", paddingTop: 10, display: "flex", flexDirection: "column", gap: 8 }}>
        <div className="jp-ai-bubble">Your top priority is electricity. Switching to a green energy tariff could save around 12 tCO2e per year and reduce costs.</div>
        <div className="jp-user-bubble">What about our servers?</div>
      </div>
    </div>
  );

  return (
    <section id="journey" className="journey-section">
      <div className="journey-header">
        <div className="journey-tag">How It Works</div>
        <h2 className="journey-headline">Three layers. One clear picture.</h2>
      </div>
      <div className="journey-layout">
        <div className="journey-steps">
          {steps.map((s, i) => (
            <div key={i} className={`journey-step${active === i ? " active" : ""}`} onClick={() => handleStepClick(i)}>
              {active === i && <div className="journey-step-bar" />}
              <div className="journey-step-num">{s.num}</div>
              <div className="journey-step-title">{s.title}</div>
              <div className="journey-step-sub">{s.sub}</div>
            </div>
          ))}
          <div style={{ marginTop: 36 }}>
            <button className="btn-hero" style={{ background: "var(--g600)" }} onClick={onStart}>Begin Assessment →</button>
          </div>
        </div>
        <div className="journey-preview">
          <div className="journey-preview-bar">
            <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 9, color: "rgba(255,255,255,.25)", letterSpacing: ".08em" }}>
              {steps[active].num} — {steps[active].title}
            </div>
          </div>
          {active === 0 && <InputPreview />}
          {active === 1 && <OutputPreview />}
          {active === 2 && <AiPreview />}
          <div className="jp-timer">
            {steps.map((_, i) => (
              <div key={i} className="jp-timer-dot">
                <div className="jp-timer-fill" style={{ width: active === i ? `${progress}%` : active > i ? "100%" : "0%" }} />
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

/* ── HERO SECTION COMPONENT ──────────────────────────────────────────────────── */
const SLIDES = [
  {
    url: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1200&q=80",
    caption: "Emissions Dashboard"
  },
  {
    url: "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=1200&q=80",
    caption: "Benchmark Analysis"
  },
  {
    url: "https://images.unsplash.com/photo-1504868584819-f8e8b4b6d7e3?w=1200&q=80",
    caption: "Reduction Pathways"
  },
  {
    url: "https://images.unsplash.com/photo-1543286386-713bdd548da4?w=1200&q=80",
    caption: "Scope Breakdown"
  },
];

function HeroSection({ onStart, onLearnMore }) {
  const [slide, setSlide] = useState(0);
  const [progress, setProgress] = useState(0);
  const DURATION = 4000;
  const TICK = 60;
  const timerRef = useRef(null);

  useEffect(() => {
    setProgress(0);
    clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      setProgress(p => {
        if (p >= 100) {
          setSlide(s => (s + 1) % SLIDES.length);
          return 0;
        }
        return p + (TICK / DURATION * 100);
      });
    }, TICK);
    return () => clearInterval(timerRef.current);
  }, [slide]);

  const goTo = (i) => { setSlide(i); setProgress(0); };

  return (
    <section className="hero">
      <div className="hero-bg-grid" />
      <div className="hero-bg-glow" />
      <div className="hero-inner">
        {/* Left: text */}
        <div>
          <h1 className="hero-title fade-up">
            Measure<br />Optimize<br />Decarbonize
          </h1>
          <p className="hero-motto-sub fade-up2">
            A carbon footprint platform built for IT and technology organizations. Understand your emissions, benchmark against your sector, and take targeted action.
          </p>
          <div className="hero-actions fade-up3">
            <button className="btn-hero" onClick={onStart}>Start Calculating</button>
            <button className="btn-hero-ghost" onClick={onLearnMore}>Learn More</button>
          </div>
        </div>

        {/* Right: slideshow — no browser chrome */}
        <div className="fade-up2">
          <div className="hero-slideshow" style={{ borderRadius: "12px" }}>
            <div className="hero-slide-progress">
              <div className="hero-slide-progress-fill" style={{ width: `${progress}%` }} />
            </div>
            {SLIDES.map((s, i) => (
              <div key={i} className={`hero-slide${slide === i ? " active" : ""}`}>
                <img src={s.url} alt={s.caption} loading="lazy" />
                <div className="hero-slide-overlay" />
                {slide === i && (
                  <div className="hero-slide-caption">{s.caption}</div>
                )}
              </div>
            ))}
            <div className="hero-slide-dots">
              {SLIDES.map((_, i) => (
                <div key={i} className={`hero-slide-dot${slide === i ? " active" : ""}`} onClick={() => goTo(i)} />
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ── STEP FORM DATA ──────────────────────────────────────────────────────────── */
const INIT_FORM = {
  company: "", state: "default", industry: "IT", employees: 50, revenue: 10, hours: 8,
  diesel: 0, petrol: 0, natgas: 0, lpg: 0,
  elec: 5000, renewable: 0,
  racks: 0, srvhrs: 24, srvtype: "hot_aisle_cold_aisle", servers: 0,
  laptops: 0, desktops: 0, monitors: 0,
  cloud: "none", cloudbill: 0, services: 0,
};

/* ── MAIN APP ─────────────────────────────────────────────────────────────── */
export default function App() {
  const [page, setPage] = useState("home");
  const [dashTab, setDashTab] = useState("assessments");
  const [simTarget, setSimTarget] = useState(null);
  const [step, setStep] = useState(0);
  const [form, setForm] = useState(INIT_FORM);
  const [result, setResult] = useState(null);
  const [fList, setFList] = useState([]);
  const [apiMessage, setApiMessage] = useState(null);
  const [msgs, setMsgs] = useState([{ role: "ai", text: KB.greet }]);
  const [chatInput, setChatInput] = useState("");
  const [typing, setTyping] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [showSignup, setShowSignup] = useState(false);
  const [isCalculating, setIsCalculating] = useState(false);
  const [resultsTab, setResultsTab] = useState("insights"); // "insights" or "recommendations"
  const [mlData, setMlData] = useState(null);
  const [personalization, setPersonalization] = useState(null);
  const [learningStatus, setLearningStatus] = useState(null);
  const [savedPrefs, setSavedPrefs] = useState(() => {
  try { return JSON.parse(localStorage.getItem("carbonaire_prefs") || "[]"); }
  catch { return []; }
  });
  const [user, setUser] = useState(() => getStoredUser());

  const [inputMode, setInputMode] = useState("upload");
  const [excelFile, setExcelFile] = useState(null);
  const [excelDrag, setExcelDrag] = useState(false);
  const [uploadedDocs, setUploadedDocs] = useState({ electricity: null, hardware: null, cloud: null, fuel: null });
  const [processingDocs, setProcessingDocs] = useState({ electricity: false, hardware: false, cloud: false, fuel: false, template: false });
  const [extractedData, setExtractedData] = useState({ electricity: null, hardware: null, cloud: null, fuel: null });
  const [sectionVerified, setSectionVerified] = useState({ electricity: null, hardware: null, cloud: null, fuel: null }); // null, 'yes', 'no'
  const excelInputRef = useRef(null);
  const chatRef = useRef(null);
  const topRef = useRef(null);

  useEffect(() => {
    setUser(getStoredUser());
  }, []);

  /* ── INTERNAL COMPONENTS ────────────────────────────────────────────────── */
  const VerificationBlock = ({ docKey, title, fields }) => {
  const doc = uploadedDocs[docKey];
  const data = extractedData[docKey];
  if (!doc) return null;

  const isImg = doc.type.startsWith("image/");
  const previewUrl = isImg ? URL.createObjectURL(doc) : null;

  // Figure out what was extracted vs what's missing
  const extracted = {};
  const missing = {};
  if (data) {
    Object.entries(fields).forEach(([label, apiKey]) => {
      if (data[apiKey] !== undefined && data[apiKey] !== null) {
        extracted[label] = data[apiKey];
      } else {
        missing[label] = apiKey;
      }
    });
  }

  const hasExtracted = Object.keys(extracted).length > 0;
  const hasMissing = Object.keys(missing).length > 0;

  return (
    <div className="verify-block fade-up">
      <div className="verify-preview">
        {isImg
          ? <img src={previewUrl} alt="Document Preview" />
          : <div className="verify-preview-icon">[DOC]</div>
        }
        <div className="verify-preview-label">{doc.name}</div>
      </div>
      <div className="verify-content">
        <div className="verify-title">[FILE] {title}</div>

        {/* Show extracted values */}
        {hasExtracted && (
          <div style={{ marginBottom: 14 }}>
            <div style={{
              fontFamily: "JetBrains Mono,monospace", fontSize: 9,
              letterSpacing: ".1em", textTransform: "uppercase",
              color: "var(--g600)", marginBottom: 8,
              display: "flex", alignItems: "center", gap: 6
            }}>
              [VALID] Extracted from document
            </div>
            <div className="verify-data-grid">
              {Object.entries(extracted).map(([label, val]) => (
                <div key={label} className="verify-data-item">
                  <div className="verify-data-label">{label}</div>
                  <div className="verify-data-val" style={{ color: "var(--g700)" }}>
                    {val}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Show missing fields */}
        {hasMissing && (
          <div style={{
            background: "#FFFBEB", border: "1px solid #D97706",
            borderRadius: 6, padding: "10px 14px", marginBottom: 10
          }}>
            <div style={{
              fontFamily: "JetBrains Mono,monospace", fontSize: 9,
              letterSpacing: ".1em", textTransform: "uppercase",
              color: "#B45309", marginBottom: 6
            }}>
              [WARN] Could not find — please enter below
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {Object.keys(missing).map(label => (
                <span key={label} style={{
                  background: "#FEF3C7", border: "1px solid #FCD34D",
                  borderRadius: 4, padding: "2px 8px",
                  fontFamily: "JetBrains Mono,monospace",
                  fontSize: 10, color: "#92400E"
                }}>
                  {label}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* If everything was extracted, show complete message */}
        {hasExtracted && !hasMissing && (
          <div style={{
            background: "var(--g50)", border: "1px solid var(--g300)",
            borderRadius: 6, padding: "8px 14px",
            fontFamily: "JetBrains Mono,monospace", fontSize: 10,
            color: "var(--g700)"
          }}>
            [DONE] All required data extracted — no manual entry needed for this section.
          </div>
        )}
      </div>
    </div>
    );
  };

  const MLInsightsCard = ({ data }) => {
    if (!data || !data.ml_available) return null;
    return (
      <div className="res-card fade-up" style={{ borderTop: "4px solid var(--g500)", marginBottom: 28, background: "linear-gradient(135deg, #fff 0%, #f0faf7 100%)" }}>
        <div className="res-card-header" style={{ background: "transparent", borderBottom: "1px solid rgba(45,168,136,.1)" }}>
          <div className="res-card-title" style={{ color: "var(--g600)", display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 16 }}>[AI]</span> ML-Powered Emission Archetype
          </div>
        </div>
        <div className="res-card-body" style={{ display: "flex", flexDirection: "column", alignItems: "stretch", gap: 24 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 32 }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontFamily: "Cormorant Garamond, serif", fontSize: 24, fontWeight: 500, color: "var(--ink)", marginBottom: 8 }}>
              {data.ml_cluster_description}
            </div>
            <div style={{ fontSize: 13, color: "var(--muted)", lineHeight: 1.6 }}>
              The ML model identified this emission pattern with <strong>{data.ml_confidence} confidence</strong>.
              Priority Score: <strong>{data.ml_priority_score}/10</strong>.
            </div>
            {data.ml_primary_message && (
              <div style={{ marginTop: 14, padding: "14px 16px", background: "rgba(45,168,136,.08)", border: "1px solid rgba(45,168,136,.14)", borderRadius: 4 }}>
                <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, letterSpacing: ".12em", textTransform: "uppercase", color: "var(--g500)", marginBottom: 6 }}>Top ML Recommendation</div>
                <div style={{ fontSize: 15, color: "var(--ink)", lineHeight: 1.6 }}>{data.ml_primary_message}</div>
              </div>
            )}
          </div>
          <div style={{ width: 100, textAlign: "center" }}>
            <div style={{ fontSize: 10, fontFamily: "JetBrains Mono, monospace", color: "var(--g500)", marginBottom: 4, textTransform: "uppercase" }}>Confidence</div>
            <div style={{ fontSize: 28, fontFamily: "Cormorant Garamond, serif", color: "var(--g600)" }}>{data.ml_confidence}</div>
            <div style={{ height: 4, background: "var(--g100)", borderRadius: 99, marginTop: 4, overflow: "hidden" }}>
              <div style={{ width: `${data.ml_confidence}%`, height: "100%", background: "var(--g500)" }} />
            </div>
          </div>
        </div>
          {data.ml_top3_recommendations?.length > 0 && (
            <div>
              <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, letterSpacing: ".12em", textTransform: "uppercase", color: "var(--muted)", marginBottom: 10 }}>Prioritised ML Recommendations</div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 12 }}>
                {data.ml_top3_recommendations.map((rec, idx) => (
                  <div key={`${rec.recommendation}-${idx}`} style={{ padding: "14px 14px 12px", border: "1px solid rgba(45,168,136,.12)", borderRadius: 4, background: "#fff" }}>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
                      <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "var(--g500)", textTransform: "uppercase" }}>Rank {idx + 1}</div>
                      <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "var(--muted)" }}>{rec.confidence}</div>
                    </div>
                    <div style={{ fontSize: 14, color: "var(--ink)", lineHeight: 1.5, marginBottom: 12 }}>{rec.message}</div>
                    <div>
                      <button 
                        className="btn-back" 
                        style={{ padding: "6px 12px", fontSize: "9px", borderColor: "var(--line)", color: "var(--g600)", width: "100%" }}
                        onClick={() => {
                           setSimTarget({ sev: "HIGH", cat: "ML Priority", scope: "Analysis", rec: rec.message });
                           setPage("simulation");
                        }}>
                         Simulate Impact
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 30);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);


  useEffect(() => { window.scrollTo(0, 0); }, [page]);

  useEffect(() => { chatRef.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs, typing]);

  const set = (k, v) => setForm(p => ({ ...p, [k]: v }));
  const num = (k) => (e) => set(k, parseFloat(e.target.value) || 0);
  const str = (k) => (e) => set(k, e.target.value);

  const buildPayload = (sourceForm) => ({
    company_name: sourceForm.company,
    industry_type: sourceForm.industry,
    location_state: sourceForm.state,
    num_employees: parseInt(sourceForm.employees),
    working_hours_per_day: parseFloat(sourceForm.hours),
    annual_revenue_inr_cr: parseFloat(sourceForm.revenue),
    diesel_litres_per_month: parseFloat(sourceForm.diesel),
    petrol_litres_per_month: parseFloat(sourceForm.petrol),
    natural_gas_m3_per_month: parseFloat(sourceForm.natgas),
    lpg_litres_per_month: parseFloat(sourceForm.lpg),
    electricity_kwh_per_month: parseFloat(sourceForm.elec),
    renewable_energy_percent: parseFloat(sourceForm.renewable),
    server_rack_count: parseInt(sourceForm.racks),
    server_operating_hours_per_day: parseFloat(sourceForm.srvhrs),
    server_arrangement: sourceForm.srvtype,
    num_laptops: parseInt(sourceForm.laptops),
    num_desktops: parseInt(sourceForm.desktops),
    num_servers_onprem: parseInt(sourceForm.servers),
    num_monitors: parseInt(sourceForm.monitors),
    cloud_provider: sourceForm.cloud,
    cloud_monthly_bill_inr: parseFloat(sourceForm.cloudbill),
    purchased_services_spend_inr_per_month: parseFloat(sourceForm.services)
  });

  const getBackendIssue = (data) => {
    const issues = [...(data.errors || []), ...(data.warnings || [])].filter(Boolean);
    if (!issues.length) return "The backend rejected this submission. Please review the required inputs and try again.";
    return issues.join(" ");
  };

  const applyAssessmentResult = (data, formCombined, formExtracted, formManual) => {
    const rExt = calc(formExtracted);
    const rMan = calc(formManual);
    const monthly = {
      s1: data.emissions.monthly.scope1_tco2e,
      s2: data.emissions.monthly.scope2_tco2e,
      s3: data.emissions.monthly.scope3_tco2e,
      tot: data.emissions.monthly.total_tco2e,
    };
    const annual = {
      s1: data.emissions.annual.scope1_tco2e,
      s2: data.emissions.annual.scope2_tco2e,
      s3: data.emissions.annual.scope3_tco2e,
      tot: data.emissions.annual.total_tco2e,
    };
    const band = BANDS.find(b => data.intensity.revenue_intensity_tco2e_per_cr >= b.min && data.intensity.revenue_intensity_tco2e_per_cr < b.max) || BANDS[3];
    const bdown = {
      Diesel: data.emissions.scope1.diesel_tco2e,
      Petrol: data.emissions.scope1.petrol_tco2e,
      "Natural Gas": data.emissions.scope1.natural_gas_tco2e,
      LPG: data.emissions.scope1.lpg_tco2e,
      Electricity: data.emissions.scope2.total_tco2e,
      Cloud: data.emissions.scope3.cloud.tco2e,
      Services: data.emissions.scope3.services.tco2e,
      Devices: data.emissions.scope3.devices.total_monthly_tco2e,
    };

    setResult({
      combined: {
        tot: monthly.tot,
        ann: annual.tot,
        s1: monthly.s1,
        s2: monthly.s2,
        s3: monthly.s3,
        intensity: data.intensity.revenue_intensity_tco2e_per_cr,
        band,
        bdown,
      },
      extracted: rExt,
      manual: rMan,
      s1: monthly.s1,
      s2: monthly.s2,
      s3: monthly.s3,
      tot: monthly.tot,
      ann: annual.tot,
      intensity: data.intensity.revenue_intensity_tco2e_per_cr,
      monthly,
      annual,
      band,
      bdown,
    });

    if (data.ml && data.ml.ml_available) {
      setMlData(data.ml);
      if (data.personalization) setPersonalization(data.personalization);
      setFList(data.ml.ml_enhanced_findings.map(f => ({
        sev: f.severity,
        scope: f.scope || (f.source === "ML" ? "AI Suggestion" : "Rule"),
        cat: f.category,
        msg: f.message,
        rec: f.recommendation || f.message,
        source: f.source,
        confidence: f.confidence
      })));
    } else {
      setMlData(null);
      setFList(findings(calc(formCombined), formCombined));
    }

    setApiMessage(null);
    setPage("results");
  };

  const doCalc = async () => {
    setIsCalculating(true);
    setApiMessage(null);
    // Prepare 3 sets of data for the trifold result
    const formExtracted = { ...INIT_FORM };
    const formManual = { ...INIT_FORM };
    const formCombined = { ...form };

    // 1. Combine Doc Data + Manual Addition Data for formCombined
    Object.keys(extractedData).forEach(key => {
      if (!extractedData[key]) return;
      const data = extractedData[key];
      const mapping = {
        electricity: { electricity_kwh_per_month: "elec", location_state: "state" },
        fuel: { diesel_litres_per_month: "diesel", petrol_litres_per_month: "petrol" },
        cloud: { cloud_provider: "cloud", cloud_monthly_bill_inr: "cloudbill" },
        hardware: { num_laptops: "laptops", num_desktops: "desktops", num_servers_onprem: "servers", num_monitors: "monitors" }
      };

      const m = mapping[key];
      Object.entries(m).forEach(([exKey, formKey]) => {
        if (data[exKey] !== undefined) {
          formExtracted[formKey] = data[exKey];
          if (sectionVerified[key] === 'no') {


            formCombined[formKey] = (parseFloat(data[exKey]) || 0) + (parseFloat(form[formKey]) || 0);
            formManual[formKey] = form[formKey];

          } else {
            formCombined[formKey] = data[exKey];
            formManual[formKey] = 0;
          }
        }
      });
    });

    Object.keys(INIT_FORM).forEach(k => {
      if (!formExtracted[k]) formManual[k] = form[k];
    });

    // Call Backend API for ML-powered results
    try {
      const payload = buildPayload(formCombined);

      const resp = await fetch(`${API_BASE}/api/run`, {
        method: "POST",
        headers: authJsonHeaders(),
        body: JSON.stringify(payload)
      });
      const data = await resp.json();

      if (data.ok) {
        applyAssessmentResult(data, formCombined, formExtracted, formManual);
        fetch(`${API_BASE}/api/user/learning-status`)
          .then(r => r.json())
          .then(d => setLearningStatus(d))
          .catch(() => {});
      } else {
        setMlData(null);
        setApiMessage(getBackendIssue(data));
      }
    } catch (err) {
      console.error("API calculation failed:", err);
      // Fallback to local calculation
      const rComp = calc(formCombined);
      const rExt = calc(formExtracted);
      const rMan = calc(formManual);
      setMlData(null);
      setApiMessage("The backend assessment was unavailable, so the dashboard is showing the local rule-based estimate only.");
      setResult({ combined: rComp, extracted: rExt, manual: rMan, ...rComp });
      setFList(findings(rComp, formCombined));
      setPage("results");
    } finally {
      setIsCalculating(false);
    }
  };


  const goCalculator = () => {
    if (!user) {
      setShowSignup(true);
      return;
    }
    setApiMessage(null);
  
    setApiMessage(null);
    setInputMode("upload");
    setExcelFile(null);
    setUploadedDocs({ electricity: null, hardware: null, cloud: null, fuel: null });
    setStep(0);
    setForm({ ...INIT_FORM, elec: 0, diesel: 0, petrol: 0, cloudbill: 0, laptops: 0, desktops: 0, servers: 0, monitors: 0 });
    setPage("calculator");
    setPage("calculator");
  };

  const handleDocUpload = async (key, e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploadedDocs(p => ({ ...p, [key]: file }));
    setProcessingDocs(p => ({ ...p, [key]: true }));

    const fd = new FormData();
    fd.append("file", file);
    fd.append("doc_type", key);

    try {
      const resp = await fetch(`${API_BASE}/api/upload-doc`, {
        method: "POST",
        body: fd
      });
      const data = await resp.json();

      if (data.ok && data.data) {
        setExtractedData(prev => ({ ...prev, [key]: data.data }));
        // Note: We no longer auto-fill the 'form' state directly here.
        // The user will verify the document in the respective manual section.
      }
    } catch (err) {
      console.error("Document extraction failed:", err);
    } finally {
      setProcessingDocs(p => ({ ...p, [key]: false }));
    }
  };

  const handleProcessExcel = async () => {
    if (!excelFile) return;

    setProcessingDocs(p => ({ ...p, template: true }));
    setApiMessage(null);
    const fd = new FormData();
    fd.append("file", excelFile);
    fd.append("doc_type", "template");

    try {
      const resp = await fetch(`${API_BASE}/api/upload-doc`, {
        method: "POST",
        body: fd
      });
      const data = await resp.json();

      if (data.ok && data.data) {
        const raw = data.data;
        const newForm = {
          company: raw.company_name || "",
          state: raw.location_state || "default",
          industry: raw.industry_type || "IT",
          employees: raw.num_employees || 0,
          revenue: raw.annual_revenue_inr_cr || 0,
          hours: raw.working_hours_per_day || 8,
          diesel: raw.diesel_litres_per_month || 0,
          petrol: raw.petrol_litres_per_month || 0,
          natgas: raw.natural_gas_m3_per_month || 0,
          lpg: raw.lpg_litres_per_month || 0,
          elec: raw.electricity_kwh_per_month || 0,
          renewable: raw.renewable_energy_percent || 0,
          racks: raw.server_rack_count || 0,
          srvhrs: raw.server_operating_hours_per_day || 24,
          srvtype: raw.server_arrangement || "default",
          servers: raw.num_servers_onprem || 0,
          laptops: raw.num_laptops || 0,
          desktops: raw.num_desktops || 0,
          monitors: raw.num_monitors || 0,
          cloud: raw.cloud_provider || "none",
          cloudbill: raw.cloud_monthly_bill_inr || 0,
          services: raw.purchased_services_spend_inr_per_month || 0,
        };

        setForm(newForm);
        const runResp = await fetch(`${API_BASE}/api/run`, {
          method: "POST",
          headers: authJsonHeaders(),
          body: JSON.stringify(buildPayload(newForm))
        });
        const runData = await runResp.json();

        if (runData.ok) {
          applyAssessmentResult(runData, newForm, newForm, INIT_FORM);
        } else {
          setMlData(null);
          setInputMode("manual");
          setStep(0);
          setApiMessage(getBackendIssue(runData));
        }
      } else {
        setInputMode("manual");
      }
    } catch (err) {
      console.error("Master template processing failed:", err);
      setMlData(null);
      setApiMessage("The template was parsed, but the backend assessment could not be completed. You can continue from the manual form.");
      setInputMode("manual");
    } finally {
      setProcessingDocs(p => ({ ...p, template: false }));
    }
  };

  const sendChat = async () => {
    if (!chatInput.trim()) return;
    const t = chatInput.trim();
    setMsgs(p => [...p, { role: "user", text: t }]);
    setChatInput("");
    setTyping(true);

    // Build user emission context if a result is available
    const user_data = result ? {
      total:     result.combined?.ann ?? result.ann ?? 0,
      scope1:    result.combined?.s1  ?? result.s1  ?? 0,
      scope2:    result.combined?.s2  ?? result.s2  ?? 0,
      scope3:    result.combined?.s3  ?? result.s3  ?? 0,
      intensity: result.intensity ?? 0,
      band:      result.band?.band ?? "unknown",
      renewable: form.renewablePct ?? 0,
      employees: form.employees ?? 0,
      servers:   form.serversOnprem ?? 0,
    } : null;

    try {
      const res = await fetch(`${API_BASE}/api/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: t, user_data }),
      });
      const data = await res.json();
      setMsgs(p => [...p, { role: "ai", text: data.answer || "Sorry, I couldn't generate a response." }]);
    } catch (err) {
      setMsgs(p => [...p, { role: "ai", text: "Could not reach the AI backend. Make sure the server is running on port 8000." }]);
    } finally {
      setTyping(false);
    }
  };

  const STEPS = ["Company Profile", "Fuel & Generators", "Electricity & Devices", "Cloud & Services"];

  /* ── HOME PAGE ───────────────────────────────────────────────────────────── */
  if (page === "home") {
    return (
      <>
        <style>{GLOBAL_CSS}</style>

        {showSignup && <SignUpModal onClose={() => setShowSignup(false)} onAuthSuccess={setUser} />}

        {/* NAV */}
        <Navbar 
          page={page} 
          user={user} 
          setUser={setUser} 
          setPage={setPage} 
          scrolled={scrolled} 
          setShowSignup={setShowSignup} 
          goCalculator={goCalculator} 
          result={result}
          setStep={setStep}
        />

        {/* HERO */}
        <HeroSection onStart={goCalculator} onLearnMore={() => document.getElementById("about")?.scrollIntoView({ behavior: "smooth" })} />

        {/* ABOUT */}
        <section id="about" className="section-pad" style={{ background: "var(--white)" }}>
          <div className="about-grid">
            <div>
              <div className="section-tag">About Us</div>
              <h2 className="section-title" style={{ fontSize: "clamp(34px, 4vw, 56px)" }}>
                Carbonaire simplifies carbon accounting for technology organizations.
              </h2>
              <p className="section-body mt16">
                Many carbon management platforms are built for large enterprises with dedicated sustainability teams. Carbonaire focuses on providing a practical and accessible solution for organizations that want to understand and reduce their environmental impact without requiring specialized expertise.
              </p>
              <p className="section-body mt16">
                By entering operational data, clients receive a clear assessment of their carbon footprint. The platform analyzes the results, benchmarks performance against relevant industry metrics, and provides prioritized recommendations that help organizations identify the most effective actions for reducing emissions.
              </p>

              {/* Redesigned professional feature cards */}
              <div className="about-pillars">
                {[
                  { tag: "Methodology", title: "Accurate Calculation", text: "Location-adjusted electricity emission factors, real device power consumption, and cloud spend estimation are all built into the platform." },
                  { tag: "Performance", title: "Sector Benchmarking", text: "Compare your emission intensity against the Indian IT industry average to understand where your organization stands." },
                  { tag: "Action", title: "Prioritised Recommendations", text: "Receive specific, ranked actions based on your emission profile, ordered by the highest potential impact for your organization." },
                  { tag: "Advisory", title: "AI-Powered Guidance", text: "Engage with an AI assistant to explore emission sources, reduction pathways, and data-driven strategies for your specific context." },
                ].map(p => (
                  <div key={p.title} className="pillar">
                    <div className="pillar-indicator">{p.tag}</div>
                    <div className="pillar-title">{p.title}</div>
                    <div className="pillar-text">{p.text}</div>
                  </div>
                ))}
              </div>
            </div>
            <div className="about-visual">
              <div className="about-circles">
                <div className="acirc" style={{ width: 360, height: 360, borderColor: "rgba(94,160,94,.08)" }} />
                <div className="acirc" style={{ width: 270, height: 270, borderColor: "rgba(94,160,94,.13)" }} />
                <div className="acirc" style={{ width: 180, height: 180, borderColor: "rgba(94,160,94,.20)" }} />
                <div className="acirc" style={{ width: 90, height: 90, borderColor: "rgba(94,160,94,.32)", background: "rgba(94,160,94,.06)" }} />
              </div>
              <div className="about-center-text">
                <div className="about-center-num">3.1</div>
                <div className="about-center-sub">tCO2e / Rs Crore<br />Indian IT Sector Average</div>
              </div>
              <div style={{ position: "absolute", top: 40, left: 32, background: "var(--white)", border: "1px solid var(--line)", borderRadius: 4, padding: "8px 12px", boxShadow: "var(--sh)" }}>
                <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 9, color: "var(--muted)", letterSpacing: ".1em", textTransform: "uppercase", marginBottom: 2 }}>Direct</div>
                <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 13, color: "var(--g700)" }}>Fuel & Generators</div>
              </div>
              <div style={{ position: "absolute", top: 40, right: 32, background: "var(--white)", border: "1px solid var(--line)", borderRadius: 4, padding: "8px 12px", boxShadow: "var(--sh)" }}>
                <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 9, color: "var(--muted)", letterSpacing: ".1em", textTransform: "uppercase", marginBottom: 2 }}>Electricity</div>
                <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 13, color: "var(--g700)" }}>Devices & Servers</div>
              </div>
              <div style={{ position: "absolute", bottom: 40, left: "50%", transform: "translateX(-50%)", background: "var(--white)", border: "1px solid var(--line)", borderRadius: 4, padding: "8px 12px", boxShadow: "var(--sh)" }}>
                <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 9, color: "var(--muted)", letterSpacing: ".1em", textTransform: "uppercase", marginBottom: 2 }}>Indirect</div>
                <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 13, color: "var(--g700)" }}>Cloud & Services</div>
              </div>
            </div>
          </div>
        </section>

        {/* MISSION SECTION */}
        <section id="mission" className="mission-section">
          <div className="mission-inner">
            <div className="mission-tag">Our Mission</div>
            <h2 className="mission-headline">Making carbon accountability accessible and practical for technology organizations</h2>
            <p className="mission-body">
              Our mission is to make carbon accountability accessible and practical for technology organizations. As digital infrastructure continues to expand, so does the environmental impact associated with it. Many carbon management solutions are expensive, complex, or designed primarily for large enterprises. Carbonaire was created to provide a clear and practical alternative. We aim to give organizations the ability to measure their carbon footprint with confidence and to act on it with informed, data-driven decisions that lead to meaningful emission reductions.
            </p>
            <div className="mission-pillars">
              <div className="mission-pillar">
                <div className="mission-pillar-num">01 — Input</div>
                <div className="mission-pillar-title">Understand what you use</div>
                <div className="mission-pillar-text">Capture your actual energy, fuel, device, and cloud usage data in under five minutes. No specialist knowledge needed.</div>
              </div>
              <div className="mission-pillar">
                <div className="mission-pillar-num">02 — Output</div>
                <div className="mission-pillar-title">See where you stand</div>
                <div className="mission-pillar-text">Get a precise emissions breakdown and benchmark your performance against the Indian IT sector average instantly.</div>
              </div>
              <div className="mission-pillar">
                <div className="mission-pillar-num">03 — Action</div>
                <div className="mission-pillar-title">Know exactly what to do</div>
                <div className="mission-pillar-text">Receive prioritised recommendations and AI-powered guidance tailored to your specific emission profile.</div>
              </div>
            </div>
          </div>
        </section>

        {/* JOURNEY section */}
        <JourneySection onStart={() => setPage("calculator")} />

        {/* WHAT WE DO */}
        <section id="what-we-do" className="section-pad" style={{ background: "var(--g50)" }}>
          <div className="section-tag">What We Do</div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 80 }}>
            <div style={{ flex: 1 }}>
              <h2 className="section-title">Built around three things that matter</h2>
              <p className="section-body mt16">
                We don't overwhelm you with reports or jargon. Carbonaire is focused on three outputs that actually help your business act.
              </p>
            </div>
            <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 20, paddingTop: 8 }}>
              {[
                { num: "01", title: "Your Carbon Footprint", text: "A precise monthly and annual breakdown of your emissions by source: electricity, fuel, cloud, and devices. You know exactly where the number comes from." },
                { num: "02", title: "Benchmark Comparison", text: "Your emission intensity (tCO2e per Rs Crore revenue) plotted against the Indian IT industry average. You will see whether you are above, below, or in the top quartile." },
                { num: "03", title: "Personalised Recommendations", text: "Actions ranked by impact, tailored to your specific emission profile. Not generic advice but specific things your organisation can do to cut emissions and costs." },
              ].map(w => (
                <div key={w.num} style={{ display: "flex", gap: 20, paddingBottom: 20, borderBottom: "1px solid var(--line)" }}>
                  <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 11, color: "var(--g500)", fontWeight: 500, flexShrink: 0, paddingTop: 3 }}>{w.num}</div>
                  <div>
                    <div style={{ fontFamily: "Syne,sans-serif", fontSize: 15, fontWeight: 600, color: "var(--ink)", marginBottom: 6 }}>{w.title}</div>
                    <div style={{ fontSize: 14, color: "var(--muted)", lineHeight: 1.65 }}>{w.text}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA BANNER */}
        <section style={{ background: "var(--g700)", padding: "80px" }}>
          <div style={{ maxWidth: 640, margin: "0 auto", textAlign: "center" }}>
            <h2 style={{ fontFamily: "Cormorant Garamond,serif", fontSize: "clamp(32px,4vw,52px)", fontWeight: 300, color: "#fff", lineHeight: 1.1, marginBottom: 36, letterSpacing: "-.02em" }}>
              Ready to see your carbon footprint?
            </h2>
            <button className="btn-hero" onClick={goCalculator}>Start Your Assessment</button>
          </div>
        </section>

        <Footer setPage={setPage} goCalculator={goCalculator} />
      </>
    );
  }

  /* ── CALCULATOR PAGE ─────────────────────────────────────────────────────── */
  if (page === "calculator") {
    return (
      <div>
        <style>{GLOBAL_CSS}</style>
        <Navbar 
          page={page} 
          user={user} 
          setUser={setUser} 
          setPage={setPage} 
          scrolled={true} 
          setShowSignup={setShowSignup} 
          goCalculator={goCalculator} 
          result={result}
          setStep={setStep}
        />
        {showSignup && <SignUpModal onClose={() => setShowSignup(false)} onAuthSuccess={setUser} />}

        <div className="calc-page">
          <div className="calc-header">
            <div className="calc-header-inner">
              <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 10, letterSpacing: ".16em", textTransform: "uppercase", color: "var(--g300)", marginBottom: 12 }}>Carbon Footprint Assessment</div>
              {inputMode === "upload"
                ? <><div className="calc-title">Upload your documents</div><div className="calc-sub">Upload an Excel template or supporting documents to auto-fill your data, or skip to enter everything manually.</div></>
                : <><div className="calc-title">Let's calculate your footprint</div><div className="calc-sub">Work through each section. Most fields take under a minute. Enter zero for anything that doesn't apply to your company.</div></>
              }
            </div>
          </div>

          {/* DOCUMENT UPLOAD SCREEN */}
          {inputMode === "upload" && (
            <div className="upload-screen fade-up">
              <div className="upload-hero-card">
                <div className="upload-badge">Module 0 of 4 · Documentation Intake</div>
                <div className="upload-hero-title">Data Source Submission</div>
                <div className="upload-hero-sub">
                  To optimize accuracy and minimize manual data entry, please provide the relevant operational documents below. The system will extract the required metrics for your verification in the subsequent steps.
                  <br /><br />
                  {Object.values(uploadedDocs).filter(Boolean).length > 0
                    ? `Assessing ${Object.values(uploadedDocs).filter(Boolean).length} documents. Please provide any remaining records for Fuel, Hardware, or Cloud to ensure a complete automated assessment.`
                    : "No documents provided yet. Submit supporting records to enable automated processing."
                  }
                </div>
              </div>

              <div className="upload-card">
                <div className="upload-card-header">
                  <div className="upload-card-icon" style={{ background: "#EAF5F0", border: "1px solid var(--g200)" }}>📊</div>
                  <div>
                    <div className="upload-card-title">Excel Input Template <span style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 10, color: "var(--g500)", marginLeft: 8, letterSpacing: ".06em" }}>RECOMMENDED</span></div>
                    <div className="upload-card-desc">Fill in our official template and upload it here. All fields will be auto-populated instantly.</div>
                  </div>
                </div>
                <div className="upload-card-body">
                  <div className="template-note">
                    <div className="template-note-title">Use the Carbonaire Input Template</div>
                    <div className="template-note-text">
                      Your Excel file must follow the <strong>Carbonaire Input Template</strong> format exactly, with columns for <code style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 11, background: "var(--g100)", padding: "1px 5px", borderRadius: 2 }}>company_name</code>, <code style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 11, background: "var(--g100)", padding: "1px 5px", borderRadius: 2 }}>industry_type</code>, <code style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 11, background: "var(--g100)", padding: "1px 5px", borderRadius: 2 }}>location_state</code>, <code style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 11, background: "var(--g100)", padding: "1px 5px", borderRadius: 2 }}>num_employees</code>, <code style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 11, background: "var(--g100)", padding: "1px 5px", borderRadius: 2 }}>annual_revenue_inr_cr</code>, and all other required fields. Files in any other format will not be accepted.
                    </div>
                    <a href="/Carbonaire_Input_Template.xlsx" download style={{ textDecoration: "none" }}>
                      <button className="template-download-btn">Download Template (.xlsx)</button>
                    </a>
                  </div>

                  <input type="file" accept=".xlsx,.xls" ref={excelInputRef} style={{ display: "none" }} onChange={e => { const f = e.target.files[0]; if (f) setExcelFile(f); }} />
                  <div
                    className={`upload-drop-zone${excelDrag ? " drag-over" : ""}${excelFile ? " has-file" : ""}`}
                    onClick={() => excelInputRef.current.click()}
                    onDragOver={e => { e.preventDefault(); setExcelDrag(true); }}
                    onDragLeave={() => setExcelDrag(false)}
                    onDrop={e => { e.preventDefault(); setExcelDrag(false); const f = e.dataTransfer.files[0]; if (f && (f.name.endsWith(".xlsx") || f.name.endsWith(".xls"))) setExcelFile(f); }}
                  >
                    <div className="upload-drop-icon">{processingDocs.template ? "⚡" : (excelFile ? "✅" : "📂")}</div>
                    <div className="upload-drop-text">
                      {processingDocs.template
                        ? <span className="processing-shimmer">Processing all documents...</span>
                        : (excelFile ? "Template uploaded" : "Drop your filled Excel template here, or click to browse")
                      }
                    </div>
                    <div className="upload-drop-sub">{excelFile || processingDocs.template ? "" : " .xlsx or .xls · Carbonaire template format only"}</div>
                    {excelFile && !processingDocs.template && (
                      <div className="upload-file-chip">
                        [FILE] {excelFile.name}
                        <button className="upload-file-chip-remove" onClick={e => { e.stopPropagation(); setExcelFile(null); }}>✕</button>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div className="upload-card">
                <div className="upload-card-header">
                  <div className="upload-card-icon" style={{ background: "#F0F5FF", border: "1px solid #C5D8F0" }}>📎</div>
                  <div>
                    <div className="upload-card-title">Supporting Documents <span style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 10, color: "var(--muted)", marginLeft: 8, letterSpacing: ".06em" }}>(Important)</span></div>
                    <div className="upload-card-desc">Attach invoices and bills to improve accuracy and provide audit traceability</div>
                  </div>
                </div>
                <div className="upload-card-body">
                  <div className="doc-upload-grid">
                    {[
                      { key: "electricity", icon: "⚡", label: "Electricity Bill", hint: "PDF or Excel · auto-fills location & kWh" },
                      { key: "hardware", icon: "🖥", label: "Hardware Invoice", hint: "IT equipment, servers, monitors" },
                      { key: "cloud", icon: "☁️", label: "Cloud Services Bill", hint: "AWS, Azure, GCP · auto-fills spend" },
                      { key: "fuel", icon: "⛽", label: "Fuel Purchase Record", hint: "Diesel, petrol, LPG receipts" },
                    ].map(doc => (
                      <label key={doc.key} className={`doc-upload-row${uploadedDocs[doc.key] ? " uploaded" : ""}`} style={{ cursor: "pointer" }}>
                        <input type="file" style={{ display: "none" }} accept=".pdf,.xlsx,.xls,.csv,.png,.jpg" onChange={e => handleDocUpload(doc.key, e)} />
                        <div className="doc-upload-row-icon">{doc.icon}</div>
                        <div style={{ flex: 1 }}>
                          <div className="doc-upload-row-label">{doc.label}</div>
                          <div className="doc-upload-row-status">
                            {processingDocs[doc.key]
                              ? <span className="processing-shimmer">⚡ Reading document...</span>
                              : uploadedDocs[doc.key]
                                ? <span style={{ color: "var(--g600)", fontWeight: 500 }}>📄 {uploadedDocs[doc.key].name}</span>
                                : <span style={{ color: "var(--muted)" }}>{doc.hint}</span>
                            }
                          </div>
                        </div>
                        {uploadedDocs[doc.key] && <div className="doc-upload-row-check">✓</div>}
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              <div className="upload-skip-bar">
                <div className="upload-skip-text">
                  {Object.values(uploadedDocs).filter(Boolean).length > 0
                    ? `${Object.values(uploadedDocs).filter(Boolean).length} supporting document(s) attached · you can still edit all fields manually`
                    : "No documents? No problem. You can enter all data manually in the next steps."}
                </div>
                <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                  <button className="upload-manual-btn" onClick={() => setInputMode("manual")}>
                    Skip — Enter Manually
                  </button>
                  <button
                    className="upload-proceed-btn"
                    onClick={excelFile ? handleProcessExcel : () => setInputMode("manual")}
                  >
                    {excelFile ? "Process & Continue →" : "Continue to Form →"}
                  </button>
                </div>
              </div>
            </div>
          )}

          {inputMode === "manual" && (
            <div className="progress-wrap">
              <div className="progress-inner">
                {STEPS.map((s, i) => (
                  <div key={i} className={`prog-step${step === i ? " active" : i < step ? " done" : ""}`} onClick={() => i <= step && setStep(i)}>
                    <div className="prog-dot">{i < step ? "✓" : i + 1}</div>
                    <div className="prog-label">{s}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {inputMode === "manual" ? (
            <div className="calc-body">
              {apiMessage && (
                <div style={{ marginBottom: 20, background: "#FFF3E7", border: "1px solid rgba(192,90,44,.18)", borderLeft: "4px solid #C05A2C", borderRadius: 4, padding: "14px 16px", color: "#7A3E21", lineHeight: 1.6 }}>
                  {apiMessage}
                </div>
              )}

              {step === 0 && (
                <div className="fade-up">
                  <div className="step-card">
                    <div className="step-card-header">
                      <div className="step-card-num">1</div>
                      <div>
                        <div className="step-card-title">Company Profile</div>
                        <div className="step-card-sub">Basic organisational information used for benchmarking and emission intensity calculation</div>
                      </div>
                    </div>
                    <div className="step-card-body">
                      <div className="fgrid fgrid-2 mb24">
                        <div className="fl fg-span2">
                          <label>Company Name</label>
                          <input type="text" value={form.company} onChange={str("company")} placeholder="e.g. TechNova Solutions Pvt. Ltd." />
                        </div>
                        <div className="fl">
                          <label>State / Region</label>
                          <select value={form.state} onChange={str("state")}>
                            <option value="default">Select State</option>
                            <option value="karnataka">Karnataka</option>
                            <option value="maharashtra">Maharashtra</option>
                            <option value="delhi">Delhi</option>
                            <option value="gujarat">Gujarat</option>
                            <option value="tamil_nadu">Tamil Nadu</option>
                            <option value="default">Other / Default</option>
                          </select>
                        </div>
                        <div className="fl">
                          <label>Industry Type</label>
                          <select value={form.industry} onChange={str("industry")}>
                            <option value="IT">IT </option>
                            <option value="Software">Software Development</option>
                            <option value="BPO">BPO / Call Centre</option>
                            <option value="Data Centre">Data Centre</option>
                            <option value="Startup">Technology Startup</option>
                          </select>
                        </div>
                      </div>
                      <div className="hr" />
                      <div className="fgrid fgrid-2">
                        <div className="fl">
                          <label>Number of Employees</label>
                          <div className="unit-input"><input type="number" value={form.employees} onChange={num("employees")} min="1" /></div>
                        </div>
                        <div className="fl">
                          <label>Annual Revenue</label>
                          <div className="unit-input"><input type="number" value={form.revenue} onChange={num("revenue")} step=".1" /><span className="unit-tag">Rs Cr</span></div>
                        </div>
                        <div className="fl">
                          <label>Working Hours per Day</label>
                          <div className="unit-input"><input type="number" value={form.hours} onChange={num("hours")} step=".5" min="1" max="24" /><span className="unit-tag">hrs</span></div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div style={{ display: "flex", justifyContent: "flex-end" }}>
                    <button className="btn-next" onClick={() => setStep(1)}>Next: Fuel & Generators →</button>
                  </div>
                </div>
              )}

              {step === 1 && (
                <div className="fade-up">
                  <div style={{ background: "var(--white)", border: "1px solid var(--line)", borderRadius: 4, padding: "16px 20px", marginBottom: 20, borderLeft: "4px solid #C05A2C" }}>
                    <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 10, letterSpacing: ".1em", textTransform: "uppercase", color: "var(--warn)", marginBottom: 4 }}>On-Site Fuel Use</div>
                    <div style={{ fontSize: 14, color: "var(--muted)" }}>Tell us about fuel burned at your premises: generators, vehicles, and gas. Most IT companies have very little here. Enter zero for anything that doesn't apply.</div>
                  </div>
                  <div className="step-card">
                    <div className="step-card-header">
                      <div className="step-card-num" style={{ background: "#C05A2C" }}>2</div>
                      <div>
                        <div className="step-card-title">On-Site Fuel & Combustion</div>
                        <div className="step-card-sub">Generator fuel, company vehicles, kitchen gas: any fuel burned at your premises or in company-owned vehicles</div>
                      </div>
                    </div>
                    <div className="step-card-body">
                      <VerificationBlock
                        docKey="fuel"
                        title="Fuel Records"
                        fields={{ "Diesel (L)": "diesel_litres_per_month", "Petrol (L)": "petrol_litres_per_month" }}
                      />
                      {sectionVerified.fuel !== 'yes' && (
                        <div className="fgrid">
                          <div className="fl">
                            <label>{uploadedDocs.fuel ? "Additional Diesel" : "Diesel Consumption"}</label>
                            <div className="unit-input"><input type="number" value={form.diesel} onChange={num("diesel")} min="0" /><span className="unit-tag">L/mo</span></div>
                          </div>
                          <div className="fl">
                            <label>{uploadedDocs.fuel ? "Additional Petrol" : "Petrol Consumption"}</label>
                            <div className="unit-input"><input type="number" value={form.petrol} onChange={num("petrol")} min="0" /><span className="unit-tag">L/mo</span></div>
                          </div>
                          <div className="fl">
                            <label>Natural Gas</label>
                            <div className="unit-input"><input type="number" value={form.natgas} onChange={num("natgas")} min="0" /><span className="unit-tag">m³/mo</span></div>
                          </div>
                          <div className="fl">
                            <label>LPG (Cylinders / Kitchen)</label>
                            <div className="unit-input"><input type="number" value={form.lpg} onChange={num("lpg")} min="0" /><span className="unit-tag">L/mo</span></div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <button className="btn-back" onClick={() => setStep(0)}>Back</button>
                    <button className="btn-next" onClick={() => setStep(2)}>Next: Electricity & Devices →</button>
                  </div>
                </div>
              )}

              {step === 2 && (
                <div className="fade-up">
                  <div style={{ background: "var(--white)", border: "1px solid var(--line)", borderRadius: 4, padding: "16px 20px", marginBottom: 20, borderLeft: "4px solid var(--g500)" }}>
                    <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 10, letterSpacing: ".1em", textTransform: "uppercase", color: "var(--g600)", marginBottom: 4 }}>Electricity & Devices</div>
                    <div style={{ fontSize: 14, color: "var(--muted)" }}>Electricity is typically the biggest part of an IT company's carbon footprint. Enter your monthly usage and we'll handle the rest.</div>
                  </div>
                  <div className="step-card">
                    <div className="step-card-header">
                      <div className="step-card-num">3</div>
                      <div>
                        <div className="step-card-title">Electricity Consumption</div>
                        <div className="step-card-sub">Your total monthly electricity consumption and how much of it comes from renewable sources</div>
                      </div>
                    </div>
                    <div className="step-card-body">
                      <VerificationBlock
                        docKey="electricity"
                        title="Electricity Invoice"
                        fields={{ "Units (kWh)": "electricity_kwh_per_month", "Location": "location_state" }}
                      />
                      {sectionVerified.electricity !== 'yes' && (
                        <div className="fgrid fgrid-2">
                          <div className="fl">
                            <label>{uploadedDocs.electricity ? "Additional kWh" : "Monthly Electricity Consumption"}</label>
                            <div className="unit-input"><input type="number" value={form.elec} onChange={num("elec")} min="0" /><span className="unit-tag">kWh</span></div>
                          </div>
                          <div className="fl">
                            <label>Renewable Energy Share (%)</label>
                            <div className="unit-input"><input type="number" value={form.renewable} onChange={num("renewable")} min="0" max="100" /><span className="unit-tag">%</span></div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="step-card" style={{ marginTop: 16 }}>
                    <div className="step-card-header">
                      <div className="step-card-num">3b</div>
                      <div>
                        <div className="step-card-title">IT Device Fleet</div>
                        <div className="step-card-sub">On-site devices consuming electricity, powered by your organisation's purchased electricity</div>
                      </div>
                    </div>
                    <div className="step-card-body">
                      <VerificationBlock
                        docKey="hardware"
                        title="Hardware Invoice"
                        fields={{ "Laptops": "num_laptops", "Desktops": "num_desktops", "Servers": "num_servers_onprem", "Monitors": "num_monitors" }}
                      />
                      {sectionVerified.hardware !== 'yes' && (
                        <>
                          <div className="fgrid fgrid-4">
                            <div className="fl">
                              <label>{uploadedDocs.hardware ? "Extra Laptops" : "Laptops"}</label>
                              <input type="number" value={form.laptops} onChange={num("laptops")} min="0" />
                            </div>
                            <div className="fl">
                              <label>{uploadedDocs.hardware ? "Extra Desktops" : "Desktops"}</label>
                              <input type="number" value={form.desktops} onChange={num("desktops")} min="0" />
                            </div>
                            <div className="fl">
                              <label>{uploadedDocs.hardware ? "Extra Monitors" : "Monitors"}</label>
                              <input type="number" value={form.monitors} onChange={num("monitors")} min="0" />
                            </div>
                            <div className="fl">
                              <label>{uploadedDocs.hardware ? "Extra Servers" : "On-Premise Servers"}</label>
                              <input type="number" value={form.servers} onChange={num("servers")} min="0" />
                            </div>
                          </div>
                          <div className="hr" />
                          <div className="fgrid fgrid-2">
                            <div className="fl">
                              <label>Server Racks</label>
                              <input type="number" value={form.racks} onChange={num("racks")} min="0" />
                            </div>
                            <div className="fl">
                              <label>Server Operating Hours / Day</label>
                              <div className="unit-input"><input type="number" value={form.srvhrs} onChange={num("srvhrs")} min="0" max="24" /><span className="unit-tag">hrs</span></div>
                            </div>
                            <div className="fl fg-span2">
                              <label>Server Room Arrangement</label>
                              <select value={form.srvtype} onChange={str("srvtype")}>
                                <option value="hot_aisle_cold_aisle">Hot/Cold Aisle Containment</option>
                                <option value="stacked_high_density">Stacked High Density</option>
                                <option value="direct_liquid_cooling">Direct Liquid Cooling</option>
                                <option value="custom">Custom / Unknown</option>
                              </select>
                            </div>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8 }}>
                    <button className="btn-back" onClick={() => setStep(1)}>Back</button>
                    <button className="btn-next" onClick={() => setStep(3)}>Next: Cloud & Services →</button>
                  </div>
                </div>
              )}

              {step === 3 && (
                <div className="fade-up">
                  <div style={{ background: "var(--white)", border: "1px solid var(--line)", borderRadius: 4, padding: "16px 20px", marginBottom: 20, borderLeft: "4px solid var(--blue)" }}>
                    <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 10, letterSpacing: ".1em", textTransform: "uppercase", color: "var(--blue)", marginBottom: 4 }}>Cloud & Purchased Services</div>
                    <div style={{ fontSize: 14, color: "var(--muted)" }}>Emissions from your cloud infrastructure and outsourced services. We estimate this from your provider and monthly spend.</div>
                  </div>
                  <div className="step-card">
                    <div className="step-card-header">
                      <div className="step-card-num" style={{ background: "var(--blue)" }}>4</div>
                      <div>
                        <div className="step-card-title">Cloud Computing</div>
                        <div className="step-card-sub">Emissions from cloud infrastructure are estimated from your provider and monthly spend</div>
                      </div>
                    </div>
                    <div className="step-card-body">
                      <VerificationBlock
                        docKey="cloud"
                        title="Cloud Billing"
                        fields={{ "Provider": "cloud_provider", "Spend (Rs)": "cloud_monthly_bill_inr" }}
                      />
                      {sectionVerified.cloud !== 'yes' && (
                        <div className="fgrid fgrid-2">
                          <div className="fl">
                            <label>Cloud Provider</label>
                            <select value={form.cloud} onChange={str("cloud")}>
                              <option value="none">None — On-Premise Only</option>
                              <option value="aws">Amazon Web Services (AWS)</option>
                              <option value="azure">Microsoft Azure</option>
                              <option value="gcp">Google Cloud Platform (lowest carbon)</option>
                            </select>
                          </div>
                          <div className="fl">
                            <label>{uploadedDocs.cloud ? "Additional Cloud Spend" : "Monthly Cloud Spend"}</label>
                            <div className="unit-input"><input type="number" value={form.cloudbill} onChange={num("cloudbill")} min="0" /><span className="unit-tag">Rs</span></div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="step-card" style={{ marginTop: 16 }}>
                    <div className="step-card-header">
                      <div className="step-card-num" style={{ background: "var(--blue)" }}>4b</div>
                      <div>
                        <div className="step-card-title">Purchased Services</div>
                        <div className="step-card-sub">SaaS subscriptions, outsourced work, professional services. Estimated from your monthly spend.</div>
                      </div>
                    </div>
                    <div className="step-card-body">
                      <div className="fgrid fgrid-2">
                        <div className="fl">
                          <label>Total Purchased Services Spend</label>
                          <div className="unit-input"><input type="number" value={form.services} onChange={num("services")} min="0" /><span className="unit-tag">Rs/mo</span></div>
                        </div>
                      </div>
                      <div style={{ marginTop: 16, padding: "12px 16px", background: "var(--g50)", borderRadius: 4, border: "1px solid var(--g100)" }}>
                        <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 10, color: "var(--muted)" }}>We estimate emissions from purchased services based on spend volume.</div>
                      </div>
                    </div>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8 }}>
                    <button className="btn-back" onClick={() => setStep(2)}>Back</button>
                    <button className="btn-calculate" onClick={doCalc} disabled={isCalculating}>
                      {isCalculating ? <span className="processing-shimmer">Processing ML Audit...</span> : "Compute Footprint & View Results →"}
                    </button>

                  </div>
                </div>
              )}

            </div>
          ) : null}
        </div>
        <Footer setPage={setPage} goCalculator={goCalculator} />
      </div>
    );
  }

  /* ── RESULTS PAGE ────────────────────────────────────────────────────────── */
  if (page === "results" && result) {
    const { s1, s2, s3, tot, ann, intensity, band, bdown, monthly, annual } = result;
    const fndgs = fList;
    const donutData = [
      { label: "Scope 1 — Direct", value: s1, color: "#C05A2C" },
      { label: "Scope 2 — Electricity", value: s2, color: "#228F72" },
      { label: "Scope 3 — Indirect", value: s3, color: "#2E5A8A" },
    ];
    const srcSorted = Object.entries(bdown).filter(([, v]) => v > 0.00005).sort(([, a], [, b]) => b - a);
    const maxSrc = srcSorted[0]?.[1] || 1;

    const bmTotal = BENCHMARK * (form.revenue || 1);
    const bm = { s1: bmTotal * 0.05, s2: bmTotal * 0.65, s3: bmTotal * 0.30, tot: bmTotal };

    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const lineYou = months.map((_, i) => tot * (i + 1));
    const lineBm = months.map((_, i) => (bm.tot / 12) * (i + 1));
    const lineMax = Math.max(...lineYou, ...lineBm, 0.01);

    const srcColors = {
      Diesel: "#C05A2C", Petrol: "#E07840",
      "Natural Gas": "#D4944A", LPG: "#F0B860",
      Electricity: "#228F72", Laptops: "#4EBFA0", Desktops: "#2DA888", Monitors: "#80D4B4", Servers: "#1A7059",
      Cloud: "#2E5A2A", Services: "#5080B8",
    };

    function LineChart({ you, bench, max, w = 520, h = 140 }) {
      const pad = { t: 12, r: 12, b: 28, l: 44 };
      const gw = w - pad.l - pad.r; const gh = h - pad.t - pad.b;
      const px = (i) => pad.l + i / (you.length - 1) * gw;
      const py = (v) => pad.t + gh - (v / max) * gh;
      const toPath = arr => arr.map((v, i) => `${i === 0 ? "M" : "L"}${px(i)},${py(v)}`).join(" ");
      const toArea = arr => `${toPath(arr)} L${px(arr.length - 1)},${pad.t + gh} L${px(0)},${pad.t + gh} Z`;
      return (
        <svg viewBox={`0 0 ${w} ${h}`} style={{ width: "100%", height: h, display: "block" }}>
          <defs>
            <linearGradient id="gyou" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#228F72" stopOpacity=".25" />
              <stop offset="100%" stopColor="#228F72" stopOpacity="0" />
            </linearGradient>
            <linearGradient id="gbm" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#B08020" stopOpacity=".15" />
              <stop offset="100%" stopColor="#B08020" stopOpacity="0" />
            </linearGradient>
          </defs>
          {[0, .25, .5, .75, 1].map(f => {
            const y = pad.t + gh * (1 - f);
            return <g key={f}>
              <line x1={pad.l} y1={y} x2={w - pad.r} y2={y} stroke="var(--line)" strokeWidth={.8} />
              <text x={pad.l - 6} y={y + 4} textAnchor="end" fontSize={8} fontFamily="JetBrains Mono,monospace" fill="var(--muted)">{(max * f).toFixed(1)}</text>
            </g>;
          })}
          {you.map((_, i) => <text key={i} x={px(i)} y={h - 4} textAnchor="middle" fontSize={8} fontFamily="JetBrains Mono,monospace" fill="var(--muted)">{months[i]}</text>)}
          <path d={toArea(bench)} fill="url(#gbm)" />
          <path d={toPath(bench)} fill="none" stroke="#B08020" strokeWidth={1.5} strokeDasharray="4 3" />
          <path d={toArea(you)} fill="url(#gyou)" />
          <path d={toPath(you)} fill="none" stroke="#228F72" strokeWidth={2.5} />
          <circle cx={px(you.length - 1)} cy={py(you[you.length - 1])} r={4} fill="#228F72" stroke="#fff" strokeWidth={1.5} />
          <circle cx={px(bench.length - 1)} cy={py(bench[bench.length - 1])} r={4} fill="#B08020" stroke="#fff" strokeWidth={1.5} />
        </svg>
      );
    }

    function ScopeGroupedBar({ yours, bench, labels, colors, benchColor = "#B08020" }) {
      const W = 480; const H = 180;
      const pad = { t: 10, r: 12, b: 32, l: 44 };
      const gw = W - pad.l - pad.r; const gh = H - pad.t - pad.b;
      const allVals = [...yours, ...bench];
      const maxV = Math.max(...allVals, 0.01);
      const n = yours.length;
      const groupW = gw / n;
      const barW = groupW * .32;
      const gap = groupW * .06;
      return (
        <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", height: H, display: "block" }}>
          {[0, .25, .5, .75, 1].map(f => {
            const y = pad.t + gh * (1 - f);
            return <g key={f}>
              <line x1={pad.l} y1={y} x2={W - pad.r} y2={y} stroke="var(--line)" strokeWidth={.8} />
              <text x={pad.l - 6} y={y + 4} textAnchor="end" fontSize={8} fontFamily="JetBrains Mono,monospace" fill="var(--muted)">{(maxV * f).toFixed(1)}</text>
            </g>;
          })}
          {yours.map((v, i) => {
            const bv = bench[i];
            const gx = pad.l + i * groupW + groupW / 2;
            const bh = (v / maxV) * gh; const bbh = (bv / maxV) * gh;
            const by_ = pad.t + gh - bh; const bby = pad.t + gh - bbh;
            return <g key={i}>
              <rect x={gx - barW - gap / 2} y={bby} width={barW} height={bbh} fill={`${benchColor}40`} rx={2} />
              <text x={gx - barW / 2 - gap / 2} y={bby - 4} textAnchor="middle" fontSize={7.5} fontFamily="JetBrains Mono,monospace" fill={benchColor}>{bv.toFixed(1)}</text>
              <rect x={gx + gap / 2} y={by_} width={barW} height={bh} fill={colors[i]} rx={2} />
              <text x={gx + barW / 2 + gap / 2} y={by_ - 4} textAnchor="middle" fontSize={7.5} fontFamily="JetBrains Mono,monospace" fill={colors[i]}>{v.toFixed(1)}</text>
              <text x={gx} y={H - 4} textAnchor="middle" fontSize={9} fontFamily="Syne,sans-serif" fontWeight={600} fill="var(--ink2)">{labels[i]}</text>
            </g>;
          })}
        </svg>
      );
    }

    return (
      <>
        <style>{GLOBAL_CSS}</style>
        <Navbar 
          page={page} 
          user={user} 
          setUser={setUser} 
          setPage={setPage} 
          scrolled={true} 
          setShowSignup={setShowSignup} 
          goCalculator={goCalculator} 
          result={result}
          setStep={setStep}
        />
        {showSignup && <SignUpModal onClose={() => setShowSignup(false)} onAuthSuccess={setUser} />}

        <div className="results-section">
          <div className="results-header">
            <div className="results-header-inner">
              <div>
                <div className="result-band-pill" style={{ background: band.bg, color: band.col, border: `1px solid ${band.col}40` }}>
                  {band.band}
                </div>
                <div style={{ fontFamily: "Cormorant Garamond,serif", fontSize: 44, fontWeight: 300, color: "#fff", letterSpacing: "-.02em", lineHeight: 1, marginBottom: 8 }}>
                  {form.company || "Your Company"}
                </div>
                <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 11, color: "rgba(255,255,255,.4)", letterSpacing: ".08em", textTransform: "uppercase" }}>
                  {form.industry} · {form.state === "default" ? "India" : form.state.replace("_", " ")} · {form.employees} employees
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 10, letterSpacing: ".12em", textTransform: "uppercase", color: "rgba(255,255,255,.4)", marginBottom: 8 }}>Emission Intensity</div>
                <div style={{ fontFamily: "Cormorant Garamond,serif", fontSize: 68, fontWeight: 300, lineHeight: 1, color: band.col }}>{intensity.toFixed(2)}</div>
                <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 11, color: "rgba(255,255,255,.4)" }}>tCO2e per Rs Crore revenue</div>
                <div style={{ marginTop: 10, fontFamily: "JetBrains Mono,monospace", fontSize: 11, color: intensity <= BENCHMARK ? "var(--g300)" : "#E88A6A" }}>
                  [OK] {intensity <= BENCHMARK ? `${((BENCHMARK - intensity) / BENCHMARK * 100).toFixed(1)}% below industry median` : `${((intensity - BENCHMARK) / BENCHMARK * 100).toFixed(1)}% above industry median`}
                </div>
              </div>
            </div>
          </div>

        <div className="results-body">
            {apiMessage && (
              <div style={{ marginBottom: 20, background: "#FFF3E7", border: "1px solid rgba(192,90,44,.18)", borderLeft: "4px solid #C05A2C", borderRadius: 4, padding: "14px 16px", color: "#7A3E21", lineHeight: 1.6 }}>
                {apiMessage}
              </div>
            )}

            <div style={{ display: "grid", gridTemplateColumns: "repeat(5,1fr)", gap: 1, background: "var(--line)", borderRadius: 8, overflow: "hidden", marginBottom: 28, boxShadow: "var(--sh)" }}>
              {[
                { label: "Combined Total", val: result.combined.tot, fmt: v => v.toFixed(3), unit: "tCO2e / mo", color: "var(--ink)", pct: 100, note: `${(result.combined.tot * 1000).toFixed(1)} kgCO2e` },
                { label: "Annual Estimate", val: result.combined.ann, fmt: v => v.toFixed(1), unit: "tCO2e / yr", color: "var(--ink)", pct: (result.combined.ann / (bm.tot || 1)) * 100, note: `Benchmark: ${bm.tot.toFixed(1)} t` },
                { label: "Scope 1 — Direct", val: result.combined.s1, fmt: v => v.toFixed(3), unit: "tCO2e / mo", color: "#C05A2C", pct: result.combined.tot > 0 ? (result.combined.s1 / result.combined.tot) * 100 : 0, note: `${result.combined.tot > 0 ? (result.combined.s1 / result.combined.tot * 100).toFixed(1) : 0}% of total` },
                { label: "Scope 2 — Electricity", val: result.combined.s2, fmt: v => v.toFixed(3), unit: "tCO2e / mo", color: "#228F72", pct: result.combined.tot > 0 ? (result.combined.s2 / result.combined.tot) * 100 : 0, note: `${result.combined.tot > 0 ? (result.combined.s2 / result.combined.tot * 100).toFixed(1) : 0}% of total` },
                { label: "Scope 3 — Indirect", val: result.combined.s3, fmt: v => v.toFixed(3), unit: "tCO2e / mo", color: "#2E5A8A", pct: result.combined.tot > 0 ? (result.combined.s3 / result.combined.tot) * 100 : 0, note: `${result.combined.tot > 0 ? (result.combined.s3 / result.combined.tot * 100).toFixed(1) : 0}% of total` },
              ].map(k => (
                <div key={k.label} style={{ background: "var(--white)", padding: "20px 20px 16px" }}>
                  <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 9, letterSpacing: ".1em", textTransform: "uppercase", color: "var(--muted)", marginBottom: 8 }}>{k.label}</div>
                  <div style={{ fontFamily: "Cormorant Garamond,serif", fontSize: 30, fontWeight: 300, color: k.color, lineHeight: 1 }}>{k.fmt(k.val)}</div>
                  <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 9, color: "var(--muted)", marginTop: 4 }}>{k.unit}</div>
                  <div style={{ marginTop: 10, height: 5, background: "var(--g100)", borderRadius: 99, overflow: "hidden" }}>
                    <div style={{ height: "100%", width: `${Math.min(k.pct, 100)}%`, background: k.color, borderRadius: 99 }} />
                  </div>
                  <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 9, color: "var(--muted)", marginTop: 5 }}>{k.note}</div>
                </div>
              ))}
            </div>

            <div className="res-tabs">
              <button 
                className={`res-tab-btn${resultsTab === "insights" ? " active" : ""}`}
                onClick={() => setResultsTab("insights")}
              >
                Analysis & Attribution
              </button>
              <button 
                className={`res-tab-btn${resultsTab === "recommendations" ? " active" : ""}`}
                onClick={() => setResultsTab("recommendations")}
              >
                Recommendations & Actions
              </button>
            </div>

            {resultsTab === "insights" && (
              <div className="fade-in">
                <div style={{ marginBottom: 28 }}>
                  <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 10, letterSpacing: ".1em", textTransform: "uppercase", color: "var(--muted)", marginBottom: 12 }}>Data Origin & Attribution Breakdown</div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 20 }}>
                    <div className="res-card" style={{ borderTop: "4px solid #228F72" }}>
                      <div className="res-card-header">
                        <div className="res-card-title">Verified Machine-Extraction</div>
                      </div>
                      <div className="res-card-body">
                        <div style={{ fontSize: 24, fontFamily: "Cormorant Garamond,serif", color: "#228F72", marginBottom: 4 }}>{result.extracted.tot.toFixed(3)} tCO2e/mo</div>
                        <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 16 }}>Calculated purely from provided documents.</div>
                        <div style={{ borderTop: "1px solid var(--line)", paddingTop: 12 }}>
                          {Object.entries(uploadedDocs).filter(([, v]) => v).map(([k]) => (
                            <div key={k} style={{ fontSize: 11, marginVertical: 4, color: "var(--ink)" }}>[VALID] {k.charAt(0).toUpperCase() + k.slice(1)} bill verified</div>
                          ))}
                          {Object.values(uploadedDocs).filter(Boolean).length === 0 && <div style={{ fontSize: 11, color: "var(--muted)" }}>No document data attributed.</div>}
                        </div>
                      </div>
                    </div>
                    <div className="res-card" style={{ borderTop: "4px solid var(--g400)" }}>
                      <div className="res-card-header">
                        <div className="res-card-title">Manual Data Input</div>
                      </div>
                      <div className="res-card-body">
                        <div style={{ fontSize: 24, fontFamily: "Cormorant Garamond,serif", color: "var(--ink)", marginBottom: 4 }}>{result.manual.tot.toFixed(3)} tCO2e/mo</div>
                        <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 16 }}>Calculated from user-entered missing values.</div>
                        <div style={{ borderTop: "1px solid var(--line)", paddingTop: 12 }}>
                          <div style={{ fontSize: 11, color: "var(--muted)" }}>Includes organizational overhead and supplemental records.</div>
                        </div>
                      </div>
                    </div>
                    <div className="res-card" style={{ borderTop: "4px solid var(--ink)" }}>
                      <div className="res-card-header">
                        <div className="res-card-title">Consolidated Footprint</div>
                      </div>
                      <div className="res-card-body">
                        <div style={{ fontSize: 24, fontFamily: "Cormorant Garamond,serif", color: "var(--ink)", marginBottom: 4 }}>{result.combined.tot.toFixed(3)} tCO2e/mo</div>
                        <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 16 }}>Total official organizational impact.</div>
                        <div style={{ borderTop: "1px solid var(--line)", paddingTop: 12, display: "flex", height: 10, borderRadius: 99, overflow: "hidden", marginTop: 10 }}>
                          <div style={{ flex: result.extracted.tot, background: "#228F72" }} title="Extracted" />
                          <div style={{ flex: result.manual.tot, background: "var(--g400)" }} title="Manual" />
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4, fontFamily: "JetBrains Mono,monospace", fontSize: 8 }}>
                          <span>DOC: {(result.combined.tot > 0 ? result.extracted.tot / result.combined.tot * 100 : 0).toFixed(0)}%</span>
                          <span>MAN: {(result.combined.tot > 0 ? result.manual.tot / result.combined.tot * 100 : 0).toFixed(0)}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "220px 220px 1fr", gap: 20, marginBottom: 20 }}>
                  <div className="res-card" style={{ display: "flex", flexDirection: "column" }}>
                    <div className="res-card-header"><div className="res-card-title">Scope Split</div></div>
                    <div className="res-card-body" style={{ display: "flex", flexDirection: "column", alignItems: "center", flex: 1 }}>
                      <DonutChart data={donutData.filter(d => d.value > 0)} size={140} />
                      <div style={{ width: "100%", marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
                        {donutData.map(d => (
                          <div key={d.label}>
                            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                                <div style={{ width: 8, height: 8, borderRadius: "50%", background: d.color, flexShrink: 0 }} />
                                <span style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 9, color: "var(--muted)" }}>{d.label.split("—")[0].trim()}</span>
                              </div>
                              <span style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 9, color: d.color, fontWeight: 600 }}>{tot > 0 ? (d.value / tot * 100).toFixed(1) : 0}%</span>
                            </div>
                            <div style={{ height: 3, background: "var(--g100)", borderRadius: 99, overflow: "hidden" }}>
                              <div style={{ height: "100%", width: `${tot > 0 ? (d.value / tot) * 100 : 0}%`, background: d.color, borderRadius: 99 }} />
                            </div>
                            <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 8, color: "var(--muted)", marginTop: 2 }}>{d.value.toFixed(4)} t/mo</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="res-card" style={{ display: "flex", flexDirection: "column" }}>
                    <div className="res-card-header"><div className="res-card-title">Performance</div></div>
                    <div className="res-card-body" style={{ flex: 1 }}>
                      <div className="gauge-wrap">
                        <GaugeSVG value={intensity} max={9} color={band.col} />
                        <div className="gauge-value" style={{ color: band.col }}>{intensity.toFixed(2)}</div>
                        <div className="gauge-unit">tCO2e / Rs Crore</div>
                        <div style={{ marginTop: 10, padding: "6px 14px", borderRadius: 99, background: band.bg, border: `1px solid ${band.col}30`, fontFamily: "JetBrains Mono,monospace", fontSize: 10, color: band.col, letterSpacing: ".08em", textTransform: "uppercase" }}>
                          {band.band}
                        </div>
                      </div>
                      <div style={{ marginTop: 14 }}>
                        {BANDS.map(b => (
                          <div key={b.band} style={{ display: "flex", alignItems: "center", gap: 6, padding: "5px 0", borderBottom: "1px solid var(--line)" }}>
                            <div style={{ width: 8, height: 8, borderRadius: "50%", background: b.col, flexShrink: 0 }} />
                            <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 9, color: result.band.band === b.band ? "var(--ink)" : "var(--muted)", flex: 1, fontWeight: result.band.band === b.band ? 600 : 400 }}>{b.band}</div>
                            <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 9, color: "var(--muted)" }}>{b.min}–{b.max === Infinity ? "∞" : b.max}</div>
                            {result.band.band === b.band && <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 9, color: b.col }}>◀</div>}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="res-card">
                    <div className="res-card-header">
                      <div className="res-card-title">Your Scopes vs Sector Benchmark (tCO2e / yr)</div>
                    </div>
                    <div className="res-card-body">
                      <ScopeGroupedBar
                        yours={[annual.s1, annual.s2, annual.s3, annual.tot]}
                        bench={[bm.s1, bm.s2, bm.s3, bm.tot]}
                        labels={["Scope 1", "Scope 2", "Scope 3", "Total"]}
                        colors={["#C05A2C", "#228F72", "#2E5A8A", "var(--ink)"]}
                      />
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 1, background: "var(--line)", borderRadius: 4, overflow: "hidden", marginTop: 16 }}>
                        {[
                          { label: "Scope 1", yours: annual.s1, bench: bm.s1, col: "#C05A2C" },
                          { label: "Scope 2", yours: annual.s2, bench: bm.s2, col: "#228F72" },
                          { label: "Scope 3", yours: annual.s3, bench: bm.s3, col: "#2E5A8A" },
                          { label: "Total", yours: annual.tot, bench: bm.tot, col: "var(--ink)" },
                        ].map(c => (
                          <div key={c.label} style={{ background: "var(--white)", padding: "10px 12px" }}>
                            <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 8, letterSpacing: ".08em", textTransform: "uppercase", color: "var(--muted)", marginBottom: 4 }}>{c.label}</div>
                            <div style={{ fontFamily: "Cormorant Garamond,serif", fontSize: 20, fontWeight: 300, color: c.col, lineHeight: 1 }}>{c.yours.toFixed(1)}</div>
                            <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 8, color: "var(--muted)", marginTop: 3 }}>
                              vs {c.bench.toFixed(1)} bm
                              <span style={{ marginLeft: 4, color: c.yours <= c.bench ? "#28541C" : "#C05A2C" }}>
                                {c.yours <= c.bench ? "[OK]" : "[+]"}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                      <div style={{ marginTop: 10, display: "flex", gap: 16, alignItems: "center" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                          <div style={{ width: 18, height: 4, borderRadius: 2, background: "var(--g500)" }} />
                          <span style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 9, color: "var(--muted)" }}>Your company</span>
                        </div>
                        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                          <div style={{ width: 18, height: 4, borderRadius: 2, background: "rgba(176,128,32,.35)" }} />
                          <span style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 9, color: "var(--muted)" }}>Sector benchmark (IT India avg)</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>
                  <div className="res-card">
                    <div className="res-card-header">
                      <div className="res-card-title">12-Month Cumulative Emissions Projection</div>
                    </div>
                    <div className="res-card-body">
                      <LineChart you={lineYou} bench={lineBm} max={lineMax} />
                      <div style={{ display: "flex", gap: 20, marginTop: 10, alignItems: "center" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
                          <svg width={20} height={8}><line x1={0} y1={4} x2={20} y2={4} stroke="#228F72" strokeWidth={2.5} /></svg>
                          <span style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 9, color: "var(--muted)" }}>Your company ({ann.toFixed(1)} t/yr)</span>
                        </div>
                        <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
                          <svg width={20} height={8}><line x1={0} y1={4} x2={20} y2={4} stroke="#B08020" strokeWidth={1.5} strokeDasharray="4 3" /></svg>
                          <span style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 9, color: "var(--muted)" }}>Benchmark ({bm.tot.toFixed(1)} t/yr)</span>
                        </div>
                      </div>
                      <div style={{ marginTop: 12, padding: "10px 14px", background: "var(--g50)", borderRadius: 4, border: "1px solid var(--line)", fontFamily: "JetBrains Mono,monospace", fontSize: 9, color: "var(--muted)" }}>
                        At current rate your annual footprint will be <strong style={{ color: "var(--ink2)" }}>{ann.toFixed(1)} tCO2e</strong> vs the sector benchmark of <strong style={{ color: "#B08020" }}>{bm.tot.toFixed(1)} tCO2e</strong> for a company of your size and revenue.
                      </div>
                    </div>
                  </div>

                  <div className="res-card">
                    <div className="res-card-header">
                      <div className="res-card-title">Scope Proportion — You vs Benchmark</div>
                    </div>
                    <div className="res-card-body">
                      <div style={{ marginBottom: 20 }}>
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                          <span style={{ fontFamily: "Syne,sans-serif", fontSize: 12, fontWeight: 600, color: "var(--ink)" }}>Your Company</span>
                          <span style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 10, color: "var(--muted)" }}>{tot.toFixed(3)} tCO2e/mo</span>
                        </div>
                        <div style={{ display: "flex", height: 28, borderRadius: 4, overflow: "hidden", gap: 1 }}>
                          {donutData.filter(d => d.value > 0).map(d => (
                            <div key={d.label} style={{ flex: d.value, background: d.color, display: "flex", alignItems: "center", justifyContent: "center" }}>
                              {(d.value / tot) > 0.08 && <span style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 8, color: "#fff" }}>{(d.value / tot * 100).toFixed(0)}%</span>}
                            </div>
                          ))}
                        </div>
                        <div style={{ display: "flex", gap: 2, marginTop: 4 }}>
                          {donutData.map(d => (
                            <div key={d.label} style={{ flex: d.value, fontFamily: "JetBrains Mono,monospace", fontSize: 8, color: "var(--muted)", textAlign: "center" }}>{d.value.toFixed(3)}</div>
                          ))}
                        </div>
                      </div>
                      <div style={{ marginBottom: 24 }}>
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                          <span style={{ fontFamily: "Syne,sans-serif", fontSize: 12, fontWeight: 600, color: "var(--muted)" }}>Sector Benchmark</span>
                          <span style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 10, color: "var(--muted)" }}>{(bm.tot / 12).toFixed(3)} tCO2e/mo</span>
                        </div>
                        <div style={{ display: "flex", height: 28, borderRadius: 4, overflow: "hidden", gap: 1 }}>
                          <div style={{ flex: bm.s1, background: "rgba(192,90,44,.4)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                            <span style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 8, color: "#C05A2C" }}>5%</span>
                          </div>
                          <div style={{ flex: bm.s2, background: "rgba(34,143,114,.4)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                            <span style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 8, color: "#228F72" }}>65%</span>
                          </div>
                          <div style={{ flex: bm.s3, background: "rgba(46,90,138,.35)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                            <span style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 8, color: "#2E5A8A" }}>30%</span>
                          </div>
                        </div>
                      </div>
                      <div style={{ display: "flex", gap: 16, flexWrap: "wrap", borderTop: "1px solid var(--line)", paddingTop: 12 }}>
                        {[
                          { label: "Scope 1 — Direct", col: "#C05A2C" },
                          { label: "Scope 2 — Electricity", col: "#228F72" },
                          { label: "Scope 3 — Indirect", col: "#2E5A8A" },
                        ].map(l => (
                          <div key={l.label} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                            <div style={{ width: 10, height: 10, borderRadius: 2, background: l.col, flexShrink: 0 }} />
                            <span style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 9, color: "var(--muted)" }}>{l.label}</span>
                          </div>
                        ))}
                      </div>
                      <div style={{ marginTop: 14, padding: "10px 14px", background: "var(--g50)", borderRadius: 4, border: "1px solid var(--line)", fontFamily: "JetBrains Mono,monospace", fontSize: 9, color: "var(--muted)" }}>
                        Indian IT sector typical split: S1 5% · S2 65% · S3 30%
                      </div>
                    </div>
                  </div>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>
                  <div className="res-card">
                    <div className="res-card-header"><div className="res-card-title">Intensity Benchmark — tCO2e / Rs Crore</div></div>
                    <div className="res-card-body">
                      <div className="bar-chart-wrap">
                        {[
                          { label: "Your Company", val: intensity, color: band.col, isYou: true },
                          { label: "Excellent  2.4", val: 2.4, color: "#28541C", isYou: false },
                          { label: "Good  3.0", val: 3.0, color: "#4E8A3A", isYou: false },
                          { label: "IT Median", val: BENCHMARK, color: "#B08020", isYou: false },
                          { label: "High Emitter  3.6+", val: 4.5, color: "#C05A2C", isYou: false },
                        ].map((b, i) => {
                          const maxVal = Math.max(intensity, 4.5, 1);
                          const pct = (b.val / maxVal) * 100;
                          return (
                            <div key={i} className="brow">
                              <div className="brow-label" style={{ fontWeight: b.isYou ? 700 : 400, color: b.isYou ? b.color : "var(--muted)" }}>{b.label}</div>
                              <div className="brow-track">
                                <div className="brow-fill" style={{ width: `${pct}%`, background: b.isYou ? b.color : `${b.color}50` }}>
                                  {b.isYou && <span>{b.val.toFixed(2)}</span>}
                                </div>
                                {!b.isYou && <div style={{ position: "absolute", top: 0, left: `${pct}%`, bottom: 0, width: 2, background: b.color, opacity: .8 }} />}
                              </div>
                              <div className="brow-val" style={{ color: b.isYou ? b.color : "var(--muted)", fontWeight: b.isYou ? 700 : 400 }}>{b.val.toFixed(2)}</div>
                            </div>
                          );
                        })}
                      </div>
                      <div style={{ marginTop: 16, padding: "10px 14px", background: "var(--g50)", borderRadius: 4, border: "1px solid var(--line)", fontFamily: "JetBrains Mono,monospace", fontSize: 9, color: "var(--muted)" }}>
                        Lower is better. Your intensity vs sector: {intensity <= BENCHMARK ? `${((BENCHMARK - intensity) / BENCHMARK * 100).toFixed(1)}% below` : `${((intensity - BENCHMARK) / BENCHMARK * 100).toFixed(1)}% above`}
                      </div>
                    </div>
                  </div>

                  <div className="res-card">
                    <div className="res-card-header"><div className="res-card-title">Emission Source Breakdown — Monthly</div></div>
                    <div className="res-card-body">
                      <div className="bar-chart-wrap">
                        {srcSorted.map(([k, v], i) => {
                          const pct = tot > 0 ? (v / tot) * 100 : 0;
                          const col = srcColors[k] || "var(--g500)";
                          return (
                            <div key={i} className="brow">
                              <div className="brow-label" style={{ color: col }}>{k}</div>
                              <div className="brow-track">
                                <div className="brow-fill" style={{ width: `${(v / maxSrc) * 100}%`, background: col }}>
                                  {v > maxSrc * .12 && <span>{v.toFixed(3)} t</span>}
                                </div>
                              </div>
                              <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", minWidth: 64 }}>
                                <div className="brow-val" style={{ color: col, fontSize: 10 }}>{v.toFixed(4)}</div>
                                <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 8, color: "var(--muted)" }}>{pct.toFixed(1)}%</div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                      <div style={{ marginTop: 16 }}>
                        <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 9, letterSpacing: ".1em", textTransform: "uppercase", color: "var(--muted)", marginBottom: 8 }}>Share of total monthly emissions</div>
                        <div style={{ display: "flex", height: 20, borderRadius: 3, overflow: "hidden", gap: 1 }}>
                          {srcSorted.map(([k, v], i) => (
                            <div key={i} title={`${k}: ${(v / tot * 100).toFixed(1)}%`} style={{ flex: v, background: srcColors[k] || "var(--g500)", minWidth: 2 }} />
                          ))}
                        </div>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px 12px", marginTop: 8 }}>
                          {srcSorted.slice(0, 6).map(([k, v], i) => (
                            <div key={i} style={{ display: "flex", alignItems: "center", gap: 5 }}>
                              <div style={{ width: 8, height: 8, borderRadius: 1, background: srcColors[k] || "var(--g500)", flexShrink: 0 }} />
                              <span style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 8, color: "var(--muted)" }}>{k} {tot > 0 ? (v / tot * 100).toFixed(1) : 0}%</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="res-card" style={{ marginBottom: 28 }}>
                  <div className="res-card-header"><div className="res-card-title">Annual Scope Emissions vs Benchmark — Detailed Comparison (tCO2e / year)</div></div>
                  <div className="res-card-body">
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 1, background: "var(--line)", borderRadius: 6, overflow: "hidden", marginBottom: 24 }}>
                      {[
                        { label: "Scope 1 — Direct", yours: annual.s1, bench: bm.s1, color: "#C05A2C" },
                        { label: "Scope 2 — Electricity", yours: annual.s2, bench: bm.s2, color: "#228F72" },
                        { label: "Scope 3 — Indirect", yours: annual.s3, bench: bm.s3, color: "#2E5A8A" },
                        { label: "Total Annual", yours: annual.tot, bench: bm.tot, color: "var(--ink)" },
                      ].map(c => {
                        const diff = c.yours - c.bench;
                        const better = diff <= 0;
                        return (
                          <div key={c.label} style={{ background: "var(--white)", padding: "18px 20px" }}>
                            <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 9, letterSpacing: ".1em", textTransform: "uppercase", color: "var(--muted)", marginBottom: 8 }}>{c.label}</div>
                            <div style={{ fontFamily: "Cormorant Garamond,serif", fontSize: 32, fontWeight: 300, color: c.color, lineHeight: 1 }}>{c.yours.toFixed(1)}</div>
                            <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 9, color: "var(--muted)", marginTop: 4 }}>tCO2e / year</div>
                            <div style={{ marginTop: 10 }}>
                              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                                <span style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 8, color: "var(--muted)" }}>You</span>
                                <span style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 8, color: "var(--muted)" }}>Benchmark</span>
                              </div>
                              {[
                                { v: c.yours, col: c.color, max: Math.max(c.yours, c.bench, 0.01) },
                                { v: c.bench, col: "rgba(176,128,32,.5)", max: Math.max(c.yours, c.bench, 0.01) },
                              ].map((b, i) => (
                                <div key={i} style={{ height: 5, background: "var(--g100)", borderRadius: 99, overflow: "hidden", marginBottom: 4 }}>
                                  <div style={{ height: "100%", width: `${(b.v / b.max) * 100}%`, background: b.col, borderRadius: 99 }} />
                                </div>
                              ))}
                              <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 9, color: better ? "#28541C" : "#C05A2C", marginTop: 4 }}>
                                {better ? `${Math.abs(diff).toFixed(1)} t below benchmark` : `${Math.abs(diff).toFixed(1)} t above benchmark`}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                    <div style={{ padding: "10px 14px", background: "var(--g50)", borderRadius: 4, border: "1px solid var(--line)", fontFamily: "JetBrains Mono,monospace", fontSize: 9, color: "var(--muted)" }}>
                      Benchmark assumes Indian IT sector average of {BENCHMARK} tCO2e/Rs Cr · S1: 5% · S2: 65% · S3: 30% for a company with Rs {(form.revenue || 1).toFixed(1)} Cr revenue.
                    </div>
                  </div>
                </div>
              </div>
            )}

            {resultsTab === "recommendations" && (
              <div className="fade-in">
                <div style={{ marginBottom: 32 }}>
                  <MLInsightsCard data={mlData} />
                  <MLDashboard
                    mlData={mlData}
                    personalization={personalization}
                    learningStatus={learningStatus}
                    user={user}
                    onLogin={() => setShowSignup(true)}
                    inputSnapshot={buildPayload(form)}
                  />
                </div>
                <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 10, letterSpacing: ".1em", textTransform: "uppercase", color: "var(--muted)", marginBottom: 12 }}>Rule-based Findings</div>
                {result.findings && result.findings.map((f, i) => (
                  <div key={i} className="res-card" style={{ marginBottom: 20 }}>
                    <div className="res-card-body">
                      <div style={{ marginBottom: 12 }}>
                        <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "var(--g500)", fontWeight: 600 }}>ML-POWERED</span>
                        {f.confidence && <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "var(--muted)", marginLeft: 8 }}>{f.confidence}</span>}
                      </div>
                      <div style={{ display: "flex", alignItems: "center", marginBottom: 9, gap: 8 }}>
                        <span className={`f-badge fb-${f.sev}`}>{f.sev}</span>
                        <span className="f-scope" style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 11, color: "var(--muted)" }}>{f.scope}</span>
                        <span className="f-cat" style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 11, color: "var(--muted)" }}>{f.cat}</span>
                      </div>
                      <div className="f-msg" style={{ fontSize: 16, fontWeight: 500, color: "var(--ink)", marginBottom: 8 }}>{f.msg}</div>
                      <div className="f-rec" style={{ paddingBottom: 16, color: "var(--muted)", fontSize: 14 }}>{f.rec}</div>
                      <div>
                        <button 
                          className="btn-back" 
                          style={{ padding: "8px 16px", fontSize: "10px", borderColor: "var(--g300)", color: "var(--g600)" }}
                          onClick={() => {
                             setSimTarget(f);
                             setPage("simulation");
                          }}>
                           Simulate Impact
                        </button>
                      </div>
                    </div>
                  </div>
                ))}

                <div style={{ marginTop: 32, textAlign: "center" }}>
                  <button className="btn-hero" style={{ background: "var(--g600)" }} onClick={() => setPage("ai")}>
                    Ask the AI Assistant →
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        <Footer setPage={setPage} goCalculator={goCalculator} />
      </>
    );
  }

  /* ── SIMULATION PAGE ─────────────────────────────────────────────── */
  if (page === "simulation") {
    return (
      <SimulationDashboard 
        recommendation={simTarget} 
        onBack={() => setPage("results")} 
        GLOBAL_CSS={GLOBAL_CSS} 
        result={result} 
        user={user}
        setUser={setUser}
        setPage={setPage}
        goCalculator={goCalculator}
        setShowSignup={setShowSignup}
      />
    );
  }

  /* ── AI ADVISOR PAGE ─────────────────────────────────────────────── */
  if (page === "ai") {
    return (
      <>
        <style>{GLOBAL_CSS}</style>
        {showSignup && <SignUpModal onClose={() => setShowSignup(false)} onAuthSuccess={setUser} />}
        <Navbar 
          page={page} 
          user={user} 
          setUser={setUser} 
          setPage={setPage} 
          scrolled={scrolled} 
          setShowSignup={setShowSignup} 
          goCalculator={goCalculator} 
          result={result}
          setStep={setStep}
        />

        <div className="ai-section">
          <div className="ai-header">
            <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 10, letterSpacing: ".18em", textTransform: "uppercase", color: "var(--g300)", marginBottom: 16, display: "flex", alignItems: "center", gap: 12 }}>
              <span style={{ display: "block", width: 28, height: 1, background: "var(--g400)" }} />
              AI Assistant
            </div>
            <div style={{ fontFamily: "Cormorant Garamond,serif", fontSize: 44, fontWeight: 300, color: "#E8F7F3", letterSpacing: "-.02em", marginBottom: 10 }}>
              Ask anything about carbon and emissions
            </div>
            <div style={{ fontSize: 16, color: "rgba(240,237,214,.5)", maxWidth: 560 }}>
              Ask about emission sources, reduction strategies, what your results mean, or anything else sustainability-related.
            </div>
          </div>

          <div className="ai-body">
            <div className="chat-container">
              <div className="chat-top">
                <div className="chat-top-dot" />
                <div className="chat-top-label">Carbonaire Assistant · Active</div>
                {result && <div style={{ marginLeft: "auto", fontFamily: "JetBrains Mono,monospace", fontSize: 9, color: "rgba(255,255,255,.3)", letterSpacing: ".06em", textTransform: "uppercase" }}>
                  Context: {form.company || "Your Co"} · {result.intensity.toFixed(2)} tCO2e/Rs Cr · {result.band.band}
                </div>}
              </div>
              <div className="chat-messages">
                {msgs.map((m, i) => (
                  <div key={i} className={`cmsg ${m.role}`}>
                    <div className="cmsg-who">{m.role === "ai" ? "Carbonaire AI" : "You"}</div>
                    <div className="cmsg-bubble">{m.text}</div>
                  </div>
                ))}
                {typing && (
                  <div className="cmsg ai">
                    <div className="cmsg-who">Carbonaire AI</div>
                    <div className="cmsg-bubble"><div className="typing"><span className="tdot" /><span className="tdot" /><span className="tdot" /></div></div>
                  </div>
                )}
                <div ref={chatRef} />
              </div>
              <div className="chat-input-bar">
                <input className="chat-input" value={chatInput} onChange={e => setChatInput(e.target.value)} onKeyDown={e => e.key === "Enter" && sendChat()} placeholder="Ask about your results, how to reduce emissions, what numbers mean…" />
                <button className="chat-send" onClick={sendChat}>Send</button>
              </div>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <div className="ai-side-card">
                <div className="ai-side-title">Suggested Questions</div>
                {["What does my result mean?", "How do I reduce my electricity emissions?", "What is Scope 1, 2 and 3?", "Should I move to cloud to cut emissions?", "How does renewable energy help?", "What's the industry average for IT companies?", "Which emission source should I tackle first?", "How do servers affect my footprint?"].map(q => (
                  <button key={q} className="ai-chip" onClick={() => setChatInput(q)}>{q}</button>
                ))}
              </div>
              {result && (
                <div className="ai-side-card">
                  <div className="ai-side-title">Your Analysis Summary</div>
                  <div style={{ fontFamily: "JetBrains Mono,monospace", fontSize: 10, color: "rgba(255,255,255,.4)", lineHeight: 2 }}>
                    <div>Intensity: <span style={{ color: result.band.col }}>{result.intensity.toFixed(2)} tCO2e/Rs Cr</span></div>
                    <div>Band: <span style={{ color: result.band.col }}>{result.band.band}</span></div>
                    <div>Annual: <span style={{ color: "rgba(255,255,255,.7)" }}>{result.ann.toFixed(1)} tCO2e</span></div>
                    <div>Findings: <span style={{ color: "rgba(255,255,255,.7)" }}>{fList.length} total, {fList.filter(f => f.sev === "CRITICAL" || f.sev === "HIGH").length} priority</span></div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
        <Footer setPage={setPage} goCalculator={goCalculator} />
      </>
    );
  }

  /* ── TRANSPARENCY PAGE ─────────────────────────────────────────────── */
  /* ── TRANSPARENCY PAGE ───────────────────────────────────────────────────── */
  if (page === "transparency") {
    return (
      <TransparencyPage 
        setPage={setPage} 
        goCalculator={goCalculator} 
        user={user} 
        setUser={setUser} 
        setShowSignup={setShowSignup} 
        page={page}
        scrolled={scrolled}
        result={result}
        setStep={setStep}
      />
    );
  }

  /* ── USER DASHBOARD ──────────────────────────────────────────────────────── */
  if (page === "dashboard") {
    return (
      <UserDashboard 
        user={user} setUser={setUser}
        page={page} setPage={setPage}
        dashTab={dashTab} setDashTab={setDashTab}
        goCalculator={goCalculator}
        result={result} setResult={setResult}
        setStep={setStep}
        onLogout={() => { setUser(null); setPage("home"); }}
        setForm={setForm}
        API_BASE={API_BASE}
        authJsonHeaders={authJsonHeaders}
        INIT_FORM={INIT_FORM}
        BANDS={BANDS}
        GLOBAL_CSS={GLOBAL_CSS}
      />
    );
  }

  return <div><style>{GLOBAL_CSS}</style><button onClick={() => setPage("home")}>Home</button></div>;
}

/* ── USER DASHBOARD ────────────────────────────────────────────────────────── */
const UserDashboard = ({ 
  user, setUser, page, setPage, dashTab, setDashTab,
  goCalculator, result, setStep, onLogout, setForm, API_BASE, authJsonHeaders, INIT_FORM, BANDS, setResult, GLOBAL_CSS
}) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [apiKey, setApiKey] = useState("sk_live_67a2b9..." + Math.random().toString(36).substring(7));
  const [genning, setGenning] = useState(false);
  const [residency, setResidency] = useState("India");

  const tabs = [
    { id: "assessments", label: "Assessments", icon: null },
    { id: "api_keys", label: "API Keys", icon: null },
    { id: "data_residency", label: "Data Residency", icon: null },
    { id: "account", label: "Account Settings", icon: null },
  ];

  const fetchHistory = async () => {
    try {
      const resp = await fetch(`${API_BASE}/api/user/history`, {
        headers: authJsonHeaders()
      });
      const data = await resp.json();
      if (data.ok) setHistory(data.history);
    } catch (err) {
      console.error("Failed to fetch history:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { if (dashTab === "assessments") fetchHistory(); }, [dashTab]);

  const deleteItem = async (id) => {
    if (!window.confirm("Are you sure you want to delete this assessment? This action cannot be undone.")) return;
    try {
      const resp = await fetch(`${API_BASE}/api/assessment/${id}`, {
        method: "DELETE",
        headers: authJsonHeaders()
      });
      const data = await resp.json();
      if (data.ok) fetchHistory();
      else alert(data.error || "Failed to delete.");
    } catch (err) {
      console.error("Delete failed:", err);
    }
  };

  const viewItem = (item) => {
    const res = item.results;
    const inputs = item.inputs;
    setResult({
      combined: {
        tot: res.total_tco2e, ann: res.total_tco2e * 12,
        s1: res.scope1_tco2e, s2: res.scope2_tco2e, s3: res.scope3_tco2e,
        intensity: res.intensity,
        band: BANDS.find(b => res.intensity >= b.min && res.intensity < b.max) || BANDS[3],
        bdown: {} 
      },
      ...res,
      tot: res.total_tco2e, intensity: res.intensity,
      monthly: { total_tco2e: res.total_tco2e, scope1_tco2e: res.scope1_tco2e, scope2_tco2e: res.scope2_tco2e, scope3_tco2e: res.scope3_tco2e },
      annual: { total_tco2e: res.total_tco2e * 12, scope1_tco2e: res.scope1_tco2e * 12, scope2_tco2e: res.scope2_tco2e * 12, scope3_tco2e: res.scope3_tco2e * 12 },
    });
    setForm({ ...INIT_FORM, ...inputs });
    setPage("results");
  };

  const editItem = (item) => {
    setForm({ ...INIT_FORM, ...item.inputs });
    setStep(0);
    setPage("calculator");
  };

  const generateKey = () => {
    setGenning(true);
    setTimeout(() => {
      setApiKey("sk_live_" + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15));
      setGenning(false);
    }, 1200);
  };

  return (
    <div className="dash-page">
      <style>{GLOBAL_CSS}</style>
      <Navbar 
        page={page} user={user} setUser={setUser} setPage={setPage} 
        scrolled={true} setShowSignup={() => {}} goCalculator={goCalculator} 
        result={result} setStep={setStep} 
      />

      <div className="dash-container">
        <div className="dash-header">
          <h1 className="dash-title">ESG Intelligence Hub</h1>
          <p className="dash-sub">Centralized environmental oversight and corporate documentation for {user?.company_name || "your organization"}.</p>
        </div>

        <div className="dash-layout">
          <aside className="dash-sidebar">
            {tabs.map(t => (
              <button key={t.id} className={`dash-side-btn${dashTab === t.id ? " active" : ""}`} onClick={() => setDashTab(t.id)}>
                {t.label}
              </button>
            ))}
            <div style={{ marginTop: "auto", paddingTop: 20 }}>
              <button className="dash-side-btn" onClick={onLogout} style={{ color: "#A04040" }}>
                Log Out
              </button>
            </div>
          </aside>

          <main className="dash-main">
            {dashTab === "assessments" && (
              <div className="history-table-wrap fade-in">
                {loading ? (
                  <div className="empty-state">Loading your audit history...</div>
                ) : history.length === 0 ? (
                  <div className="empty-state">
                    <div style={{ fontSize: 40, color: "var(--line)", marginBottom: 16 }}>[NONE]</div>
                    <div>No previous assessments found. Start your first calculation to see it here.</div>
                    <button className="nav-cta" style={{ marginTop: 20, marginLeft: 0 }} onClick={goCalculator}>Start New Calculation</button>
                  </div>
                ) : (
                  <table className="history-table">
                    <thead>
                      <tr>
                        <th>Date & Details</th>
                        <th>Emissions</th>
                        <th>Intensity</th>
                        <th style={{ textAlign: "right" }}>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {history.map(item => {
                        const band = BANDS.find(b => item.results.intensity >= b.min && item.results.intensity < b.max) || BANDS[3];
                        return (
                          <tr key={item.id}>
                            <td>
                              <div className="row-title">{item.inputs.company_name || "Assessment"}</div>
                              <div className="row-meta">{new Date(item.created_at).toLocaleDateString()} · {item.inputs.location_state || "Unknown"}</div>
                            </td>
                            <td>
                              <div style={{ fontWeight: 600, color: "var(--ink2)" }}>{item.results.total_tco2e.toFixed(3)} tCO2e/mo</div>
                              <div className="row-meta">S1: {item.results.scope1_tco2e.toFixed(2)} · S2: {item.results.scope2_tco2e.toFixed(2)}</div>
                            </td>
                            <td>
                              <span className="badge-intensity" style={{ background: band.bg, color: band.col }}>
                                {item.results.intensity.toFixed(2)}
                              </span>
                            </td>
                            <td>
                              <div className="action-btns" style={{ justifyContent: "flex-end" }}>
                                <button className="btn-icon" onClick={() => viewItem(item)}>View</button>
                                <button className="btn-icon" onClick={() => editItem(item)}>Edit</button>
                                <button className="btn-icon delete" onClick={() => deleteItem(item.id)}>Delete</button>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                )}
              </div>
            )}

            {dashTab === "api_keys" && (
              <div className="fake-card fade-in">
                <h2 className="fake-title">API Access & Automation</h2>
                <p style={{ color: "var(--muted)", marginBottom: 32 }}>Integrate Carbonaire directly into your CI/CD pipelines or cloud billing systems to automate emission tracking.</p>
                
                <div className="fake-label">Active API Key</div>
                <div className="api-key-wrap">
                  <code className={genning ? "gen-anim" : ""}>{apiKey}</code>
                  <button className="btn-icon" style={{ width: "auto", padding: "0 12px", fontSize: 10 }} title="Copy Key" onClick={() => alert("Copied to clipboard!")}>COPY</button>
                </div>

                <div style={{ display: "flex", gap: 12 }}>
                  <button className="nav-cta" style={{ marginLeft: 0 }} onClick={generateKey} disabled={genning}>
                    {genning ? "Generating..." : "Roll Secret Key"}
                  </button>
                  <button className="btn-hero-ghost" style={{ borderColor: "var(--line)", color: "var(--ink2)", padding: "10px 20px" }}>View API Docs</button>
                </div>

                <div style={{ marginTop: 40, borderTop: "1px solid var(--line)", paddingTop: 32 }}>
                  <div className="fake-label">Webhook Endpoints</div>
                  <p style={{ fontSize: 13, color: "var(--muted)" }}>No webhooks configured. Add an endpoint to receive real-time alerts when emission thresholds are exceeded.</p>
                </div>
              </div>
            )}

            {dashTab === "data_residency" && (
              <div className="fake-card fade-in">
                <h2 className="fake-title">Data Sovereignty & Privacy</h2>
                <p style={{ color: "var(--muted)", marginBottom: 32 }}>Configure where your sensitive operational data is stored and processed to meet local regulatory requirements.</p>

                <div className="fake-label">Storage Region</div>
                <div className="residency-toggle">
                  <button className={`res-opt${residency === "India" ? " active" : ""}`} onClick={() => setResidency("India")}>Mumbai (India)</button>
                  <button className={`res-opt${residency === "Global" ? " active" : ""}`} onClick={() => setResidency("Global")}>Global (Standard)</button>
                </div>

                <div className="fake-label">Security Protocols</div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 32 }}>
                  <div style={{ padding: 16, background: "var(--g50)", borderRadius: 8, border: "1px solid var(--line)" }}>
                    <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 4 }}>AES-256-GCM</div>
                    <div style={{ fontSize: 11, color: "var(--muted)" }}>Database-level encryption active for all organizational inputs.</div>
                  </div>
                  <div style={{ padding: 16, background: "var(--g50)", borderRadius: 8, border: "1px solid var(--line)" }}>
                    <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 4 }}>TLS 1.3</div>
                    <div style={{ fontSize: 11, color: "var(--muted)" }}>Secure transport layer active for all API and Browser traffic.</div>
                  </div>
                </div>

                <button className="nav-cta" style={{ marginLeft: 0 }}>Save Governance Settings</button>
              </div>
            )}

            {dashTab === "account" && (
              <div className="fake-card fade-in">
                <h2 className="fake-title">Corporate Account Settings</h2>
                
                <div style={{ display: "flex", flexDirection: "column", gap: 20, maxWidth: 400 }}>
                  <div className="fl">
                    <label>Organization Name</label>
                    <input type="text" defaultValue={user?.company_name} />
                  </div>
                  <div className="fl">
                    <label>Primary Contact Email</label>
                    <input type="email" defaultValue={user?.email} />
                  </div>
                  <div className="fl">
                    <label>Default Currency</label>
                    <select><option>INR (₹)</option><option>USD ($)</option></select>
                  </div>
                  <button className="nav-cta" style={{ marginLeft: 0, marginTop: 12 }}>Update Profile</button>
                </div>
              </div>
            )}
          </main>
        </div>
      </div>
      <Footer setPage={setPage} goCalculator={goCalculator} />
    </div>
  );
};
