import React, { useState, useEffect } from "react";
import { motion as Motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Layers, Zap, Terminal } from "lucide-react";
import Magnetic from "../components/ui/Magnetic";

import { Skeleton } from "boneyard-js/react";

const stats = [
  { label: "Curated Tracks", value: "12+", sub: "professional paths" },
  { label: "Coding Sprints", value: "150+", sub: "technical challenges" },
  { label: "Performance", value: "Instant", sub: "validation feedback" },
];

const features = [
  {
    icon: Terminal,
    title: "Live Runtime",
    desc: "Execute Python code in a high-performance sandbox with instant telemetry and rich error analysis.",
  },
  {
    icon: Layers,
    title: "Curated Tracks",
    desc: "Master Python through industrially-aligned paths, from fundamental logic to advanced architecture.",
  },
  {
    icon: Zap,
    title: "Reward Protocol",
    desc: "Gain XP, unlock premium content, and visualize your professional evolution with every milestone.",
  },
];

const floatingCode = `# Python Mastery Track
def solve(nums: list[int]) -> int:
    seen = set()
    for n in nums:
        if n in seen:
            return n
        seen.add(n)
    return -1

# ✓ Test passed — 12ms`;

const LandingPage = () => {
  const navigate = useNavigate();
  const [typed, setTyped] = useState("");
  const [mousePos, setMousePos] = useState({ x: 50, y: 50 });

  const handleMouseMove = (e) => {
    const { clientX, clientY } = e;
    const { innerWidth, innerHeight } = window;
    const x = (clientX / innerWidth) * 100;
    const y = (clientY / innerHeight) * 100;
    setMousePos({ x, y });
  };

  useEffect(() => {
    let i = 0;
    const timer = setInterval(() => {
      if (i <= floatingCode.length) {
        setTyped(floatingCode.slice(0, i));
        i++;
      } else {
        clearInterval(timer);
      }
    }, 18);
    return () => clearInterval(timer);
  }, []);

  return (
    <Skeleton name="landing-page">
      <div
        className="relative w-full overflow-hidden bg-black ds-spotlight"
        onMouseMove={handleMouseMove}
        style={{
          "--mouse-x": `${mousePos.x}%`,
          "--mouse-y": `${mousePos.y}%`,
        }}
      >
        {/* BACKGROUND TEXTURE */}
        <div className="absolute inset-0 z-0 app-grid-overlay opacity-40 pointer-events-none" />
        {/* HERO */}
        <section className="relative z-10 app-page-width flex min-h-[calc(100vh-9rem)] flex-col items-center justify-center px-5 py-12 sm:px-8">
          <Motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, ease: [0.16, 1, 0.3, 1] }}
            className="mx-auto w-full max-w-4xl"
          >
            {/* Main heading */}
            <h1 className="ds-heading text-center text-4xl text-white sm:text-6xl lg:text-7xl">
              Master the Art of Python
              <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-white via-neutral-300 to-neutral-500">
                One Clash at a Time
              </span>
            </h1>

            <p className="mx-auto mt-6 max-w-2xl text-center text-base leading-relaxed text-neutral-300 sm:text-lg">
              CLASHCODE is the precision-built arena for developers who demand
              structured growth, instant feedback, and verifiable expertise.
            </p>

            {/* CTA */}
            <div className="mt-10 flex justify-center">
              <Magnetic strength={0.3}>
                <button
                  onClick={() => navigate("/login")}
                  className="ds-btn ds-btn-primary h-12 px-10 text-base font-bold rounded-xl group relative overflow-hidden transition-all hover:scale-[1.02] active:scale-[0.98] shadow-[0_0_20px_rgba(255,255,255,0.1)]"
                  id="hero-cta-start"
                >
                  <span className="relative z-10 flex items-center gap-2">
                    Start Learning Free
                    <ArrowRight
                      size={18}
                      className="group-hover:translate-x-1 transition-transform"
                    />
                  </span>
                  {/* Subtle shine effect */}
                  <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/10 to-transparent" />
                </button>
              </Magnetic>
            </div>

            {/* LIVE PULSE TICKER */}
            <div className="mt-12 w-full max-w-lg mx-auto overflow-hidden relative">
              <div className="absolute inset-y-0 left-0 w-12 bg-gradient-to-r from-black to-transparent z-10" />
              <div className="absolute inset-y-0 right-0 w-12 bg-gradient-to-l from-black to-transparent z-10" />
              <Motion.div
                animate={{ x: [0, -1000] }}
                transition={{
                  repeat: Infinity,
                  duration: 40,
                  ease: "linear",
                }}
                className="flex whitespace-nowrap gap-12 items-center"
              >
                {[...Array(2)].map((_, i) => (
                  <div key={i} className="flex gap-12 items-center">
                    <span className="flex items-center gap-2 text-[10px] font-['Geist_Mono'] text-neutral-600 uppercase tracking-widest">
                      <span className="w-1 h-1 rounded-full bg-emerald-500 animate-pulse" />
                      jithin just completed Python Basics III
                    </span>
                    <span className="flex items-center gap-2 text-[10px] font-['Geist_Mono'] text-neutral-600 uppercase tracking-widest">
                      <span className="w-1 h-1 rounded-full bg-blue-500 animate-pulse" />
                      Global XP Earned: 142,850
                    </span>
                    <span className="flex items-center gap-2 text-[10px] font-['Geist_Mono'] text-neutral-600 uppercase tracking-widest">
                      <span className="w-1 h-1 rounded-full bg-purple-500 animate-pulse" />
                      New Challenge: Async IO Mastery
                    </span>
                    <span className="flex items-center gap-2 text-[10px] font-['Geist_Mono'] text-neutral-600 uppercase tracking-widest">
                      <span className="w-1 h-1 rounded-full bg-orange-500 animate-pulse" />
                      User_42 unlocked level 12
                    </span>
                  </div>
                ))}
              </Motion.div>
            </div>

            {/* Stats bar */}
            <div className="mx-auto mt-14 grid max-w-3xl grid-cols-1 sm:grid-cols-3 gap-4">
              {stats.map((item, i) => (
                <Motion.div
                  key={item.label}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 + i * 0.07, duration: 0.4 }}
                  className="relative group"
                >
                  <div className="absolute -inset-px bg-gradient-to-b from-white/10 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                  <div className="relative ds-card p-6 text-center bg-[#050505]/60 backdrop-blur-md border-white/[0.03] overflow-hidden">
                    <p className="ds-eyebrow mb-2 text-neutral-500 group-hover:text-neutral-300 transition-colors">
                      {item.label}
                    </p>
                    <p className="text-3xl font-bold text-white font-['Space_Grotesk'] tracking-tight mb-1">
                      {item.value}
                    </p>
                    <p className="text-[10px] font-bold text-neutral-700 font-['Geist_Mono'] uppercase tracking-[0.1em] group-hover:text-neutral-500 transition-colors">
                      {item.sub}
                    </p>
                    {/* Subtle ambient glow */}
                    <div className="absolute -bottom-4 -right-4 w-12 h-12 bg-white/5 blur-2xl rounded-full opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                </Motion.div>
              ))}
            </div>
          </Motion.div>
        </section>

        {/* FEATURES + CODE PREVIEW */}
        <section className="relative z-10 app-page-width px-5 pb-24 sm:px-8">
          <div className="grid gap-8 lg:grid-cols-2 lg:gap-12 items-start">
            {/* Features list */}
            <Motion.div
              initial={{ opacity: 0, x: -16 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.5, duration: 0.5 }}
              className="space-y-4"
            >
              <p className="font-['Geist_Mono'] text-[10px] font-bold tracking-[0.2em] text-neutral-500 uppercase mb-6">
                Why CLASHCODE
              </p>
              {features.map((f, i) => {
                const Icon = f.icon;
                return (
                  <Motion.div
                    key={f.title}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.6 + i * 0.08 }}
                    className="ds-card-hover p-5 flex gap-4 bg-black border-white/5"
                  >
                    <div className="h-9 w-9 rounded-lg bg-black border border-white/10 flex items-center justify-center shrink-0">
                      <Icon size={17} className="text-neutral-400" />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-white mb-1">
                        {f.title}
                      </h3>
                      <p className="text-[13px] text-neutral-500 leading-relaxed">
                        {f.desc}
                      </p>
                    </div>
                  </Motion.div>
                );
              })}
            </Motion.div>

            {/* Code preview terminal */}
            <Motion.div
              initial={{ opacity: 0, x: 16 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.55, duration: 0.55 }}
              className="sticky top-20"
            >
              <div className="ds-card overflow-hidden bg-black border-white/5 shadow-2xl">
                {/* Terminal header */}
                <div className="flex items-center gap-2 border-b border-white/5 px-4 py-3 bg-black">
                  <div className="flex gap-1.5">
                    <div className="h-3 w-3 rounded-full bg-white/10" />
                    <div className="h-3 w-3 rounded-full bg-white/10" />
                    <div className="h-3 w-3 rounded-full bg-white/10" />
                  </div>
                  <span className="ml-2 text-[11px] font-mono text-neutral-600 font-['Geist_Mono']">
                    challenge_workspace.py
                  </span>
                </div>
                {/* Code content */}
                <div className="p-5">
                  <pre className="font-['Geist_Mono',monospace] text-[12.5px] leading-[1.7] text-neutral-300 whitespace-pre-wrap min-h-[180px]">
                    <code>
                      {typed}
                      <span className="border-r-2 border-neutral-400 animate-pulse ml-0.5" />
                    </code>
                  </pre>
                </div>
                {/* Status bar */}
                <div className="border-t border-white/5 px-4 py-2 flex items-center justify-between bg-black">
                  <span className="font-['Geist_Mono'] text-[9px] font-bold text-neutral-700 uppercase tracking-widest">
                    Python 3.11
                  </span>
                </div>
              </div>
            </Motion.div>
          </div>
        </section>
      </div>
    </Skeleton>
  );
};

export default LandingPage;
