"use client";

import React, { useState, useEffect, useMemo } from "react";

interface CommandAction {
  id: string;
  title: string;
  cat: string;
  key: string;
  run: () => void;
}

export default function ClinicianDashboard() {
  // Navigation & View State
  const [activeTab, setActiveTab] = useState<"forecast" | "whatif" | "profile" | "audit">("forecast");

  // Theme State (Dark / Light)
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  // Patient & Replay Cockpit State
  const [patientId, setPatientId] = useState("P020");
  const [speed, setSpeed] = useState(10);
  const [isPlaying, setIsPlaying] = useState(false);
  const [degradation, setDegradation] = useState("D0");

  // Command Palette State
  const [isPaletteOpen, setIsPaletteOpen] = useState(false);
  const [paletteQuery, setPaletteQuery] = useState("");
  const [paletteIndex, setPaletteIndex] = useState(0);

  // Custom Meal Modal State
  const [isCustomMealOpen, setIsCustomMealOpen] = useState(false);
  const [customName, setCustomName] = useState("Paneer Butter Masala & Roti");
  const [customCarbs, setCustomCarbs] = useState(52);
  const [customFat, setCustomFat] = useState(24);
  const [customProtein, setCustomProtein] = useState(18);

  // Biometrics Telemetry
  const liveGlucose = 136.6;
  const liveHR = 71;
  const liveMETs = 1.0;
  const lastMeal = "Roti, Dal & Sabzi";
  const lastMealMacros = "48g Carbs • 12g Fat";
  const [reliability, setReliability] = useState<"HIGH" | "MODERATE" | "LOW">("HIGH");

  // What-If Sandbox State
  const [activeDishName, setActiveDishName] = useState("Roti, Dal & Sabzi");
  const [carbs, setCarbs] = useState(48);
  const [fat, setFat] = useState(12);
  const [protein, setProtein] = useState(16);
  const [portion, setPortion] = useState(100);
  const [walking, setWalking] = useState(false);
  const [sequencing, setSequencing] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Total Calories & Macro Percentages
  const totalKcal = carbs * 4 + protein * 4 + fat * 9;
  const totalGrams = carbs + protein + fat || 1;
  const cPct = Math.round((carbs / totalGrams) * 100);
  const pPct = Math.round((protein / totalGrams) * 100);
  const fPct = 100 - cPct - pPct;

  // Initialize and synchronize theme
  useEffect(() => {
    const saved = localStorage.getItem("aegis_theme") as "dark" | "light" | null;
    if (saved === "light" || saved === "dark") {
      setTheme(saved);
      document.documentElement.classList.toggle("dark", saved === "dark");
    } else {
      const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      const initial = prefersDark ? "dark" : "light";
      setTheme(initial);
      document.documentElement.classList.toggle("dark", initial === "dark");
    }
  }, []);

  const handleSetTheme = (newTheme: "dark" | "light") => {
    setTheme(newTheme);
    localStorage.setItem("aegis_theme", newTheme);
    document.documentElement.classList.toggle("dark", newTheme === "dark");
  };

  // Replay Handlers
  const handleStart = async () => {
    try {
      await fetch(`${API_URL}/replay/start?session_id=nextjs_ui&patient_id=${patientId}&speed=${speed}&degradation=${degradation}`, { method: "POST" });
      setIsPlaying(true);
    } catch {
      setIsPlaying(true);
    }
  };

  const handlePause = async () => {
    try {
      await fetch(`${API_URL}/replay/pause?session_id=nextjs_ui`, { method: "POST" });
      setIsPlaying(false);
    } catch {
      setIsPlaying(false);
    }
  };

  const handleJumpNextMeal = async () => {
    try {
      await fetch(`${API_URL}/replay/jump?session_id=nextjs_ui&direction=next_meal`, { method: "POST" });
      setIsPlaying(true);
    } catch (e) {
      console.warn("Replay jump call:", e);
    }
  };

  const handleDegradation = async (deg: string) => {
    setDegradation(deg);
    try {
      await fetch(`${API_URL}/replay/degrade?session_id=nextjs_ui&degradation=${deg}`, { method: "POST" });
    } catch (e) {
      console.warn("Degradation update call:", e);
    }
    if (deg === "D4" || deg === "D7") setReliability("LOW");
    else if (deg.startsWith("D1") || deg === "D3") setReliability("MODERATE");
    else setReliability("HIGH");
  };

  const selectDish = (dish: string) => {
    if (dish === "masala_dosa") {
      setActiveDishName("Masala Dosa + Sambar");
      setCarbs(62); setFat(18); setProtein(10);
    } else if (dish === "chicken_biryani") {
      setActiveDishName("Chicken Biryani Plate");
      setCarbs(68); setFat(22); setProtein(32);
    } else if (dish === "rajma_chawal") {
      setActiveDishName("Rajma Chawal");
      setCarbs(72); setFat(14); setProtein(20);
    } else {
      setActiveDishName("Roti, Dal & Sabzi");
      setCarbs(48); setFat(12); setProtein(16);
    }
  };

  const applyCustomMeal = () => {
    setActiveDishName(customName);
    setCarbs(customCarbs);
    setFat(customFat);
    setProtein(customProtein);
    setIsCustomMealOpen(false);
    setActiveTab("whatif");
  };

  // Command Palette Actions
  const actions: CommandAction[] = useMemo(() => [
    { id: "play", title: "Replay: Toggle Play / Pause Stream", cat: "Replay", key: "Space", run: () => (isPlaying ? handlePause() : handleStart()) },
    { id: "jump", title: "Replay: Jump to Next Clinical Meal", cat: "Replay", key: "N", run: handleJumpNextMeal },
    { id: "p020", title: "Twin: Switch to P020 (Type 2 Diabetes, 58y)", cat: "Twin", key: "P20", run: () => setPatientId("P020") },
    { id: "p021", title: "Twin: Switch to P021 (Type 2 Diabetes, 61y)", cat: "Twin", key: "P21", run: () => setPatientId("P021") },
    { id: "p010", title: "Twin: Switch to P010 (Prediabetes, 48y)", cat: "Twin", key: "P10", run: () => setPatientId("P010") },
    { id: "p001", title: "Twin: Switch to P001 (Healthy Control, 28y)", cat: "Twin", key: "P01", run: () => setPatientId("P001") },
    { id: "preset_roti", title: "What-If: Roti, Dal & Sabzi", cat: "What-If", key: "R", run: () => { setActiveTab("whatif"); selectDish("roti_dal_sabzi"); } },
    { id: "preset_dosa", title: "What-If: Masala Dosa + Sambar", cat: "What-If", key: "D", run: () => { setActiveTab("whatif"); selectDish("masala_dosa"); } },
    { id: "preset_biryani", title: "What-If: Chicken Biryani", cat: "What-If", key: "B", run: () => { setActiveTab("whatif"); selectDish("chicken_biryani"); } },
    { id: "custom_modal", title: "What-If: Open Custom Meal Builder Modal", cat: "What-If", key: "+", run: () => setIsCustomMealOpen(true) },
    { id: "theme_light", title: "Theme: Switch to Light Theme", cat: "Theme", key: "L", run: () => handleSetTheme("light") },
    { id: "theme_dark", title: "Theme: Switch to Dark Theme", cat: "Theme", key: "D", run: () => handleSetTheme("dark") },
    { id: "deg_d0", title: "Stress: Nominal 5-Min Telemetry (D0)", cat: "Stress", key: "D0", run: () => handleDegradation("D0") },
    { id: "deg_d1", title: "Stress: 30m Signal Dropout (D1)", cat: "Stress", key: "D1", run: () => handleDegradation("D1_30m") },
    { id: "deg_d3", title: "Stress: No Wearable HR/METs (D3)", cat: "Stress", key: "D3", run: () => handleDegradation("D3") },
    { id: "tab_1", title: "View: 1. Live Forecast & Monitoring", cat: "View", key: "1", run: () => setActiveTab("forecast") },
    { id: "tab_2", title: "View: 2. What-If Meal Sandbox", cat: "View", key: "2", run: () => setActiveTab("whatif") },
    { id: "tab_3", title: "View: 3. Patient Digital Twin Phenotype", cat: "View", key: "3", run: () => setActiveTab("profile") },
    { id: "tab_4", title: "View: 4. Sensor Stress-Test Studio", cat: "View", key: "4", run: () => setActiveTab("audit") },
  ], [isPlaying, patientId]);

  const filteredActions = useMemo(() => {
    return actions.filter((a) =>
      a.title.toLowerCase().includes(paletteQuery.toLowerCase()) ||
      a.cat.toLowerCase().includes(paletteQuery.toLowerCase())
    );
  }, [actions, paletteQuery]);

  // Keyboard Shortcuts (Cmd+K, Space, N, 1-4)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setIsPaletteOpen((prev) => !prev);
        setPaletteQuery("");
        setPaletteIndex(0);
        return;
      }

      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLSelectElement) {
        if (e.key === "Escape") {
          setIsPaletteOpen(false);
          setIsCustomMealOpen(false);
        }
        return;
      }

      if (isPaletteOpen) {
        if (e.key === "ArrowDown") {
          e.preventDefault();
          setPaletteIndex((prev) => (prev + 1) % (filteredActions.length || 1));
        } else if (e.key === "ArrowUp") {
          e.preventDefault();
          setPaletteIndex((prev) => (prev - 1 + (filteredActions.length || 1)) % (filteredActions.length || 1));
        } else if (e.key === "Enter") {
          e.preventDefault();
          if (filteredActions[paletteIndex]) {
            filteredActions[paletteIndex].run();
            setIsPaletteOpen(false);
          }
        } else if (e.key === "Escape") {
          setIsPaletteOpen(false);
        }
        return;
      }

      if (e.code === "Space") {
        e.preventDefault();
        if (isPlaying) handlePause();
        else handleStart();
      } else if (e.code === "KeyN") {
        e.preventDefault();
        handleJumpNextMeal();
      } else if (e.key === "1") {
        setActiveTab("forecast");
      } else if (e.key === "2") {
        setActiveTab("whatif");
      } else if (e.key === "3") {
        setActiveTab("profile");
      } else if (e.key === "4") {
        setActiveTab("audit");
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isPlaying, isPaletteOpen, filteredActions, paletteIndex]);

  return (
    <div className="min-h-screen flex flex-col font-sans bg-[var(--bg-canvas)] text-[var(--text-main)] transition-colors duration-200">
      
      {/* 1. Clinical Research & Governance Bar */}
      <aside aria-label="Clinical Disclaimer" className="bg-amber-500/10 border-b border-amber-500/20 text-amber-800 dark:text-amber-300 px-6 py-2 text-xs flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <span className="inline-flex items-center gap-1 font-semibold uppercase tracking-wider bg-amber-500 text-slate-950 px-2 py-0.5 rounded text-[11px] font-mono">
            Research Prototype
          </span>
          <span>
            Candidate S Digital Twin (Dual-Gamma Structured Absorption). <strong>Not medical advice. Not for acute clinical interventions or insulin titration.</strong>
          </span>
        </div>
        <div className="flex items-center gap-4 text-xs font-mono text-[var(--text-secondary)]">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span> Split-Conformal 90%
          </span>
          <span>•</span>
          <span>Gate G2 Audit Passed</span>
        </div>
      </aside>

      {/* 2. Top Header Navigation (Figma / OpenRouter Clean Style) */}
      <header className="sticky top-0 z-40 bg-[var(--bg-card)] border-b border-[var(--border-main)] px-6 py-3 transition-colors duration-200">
        <div className="max-w-[1720px] mx-auto flex flex-wrap items-center justify-between gap-4">
          
          {/* Logo & Product Identity */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center font-bold text-white text-sm shadow-sm">
              AE
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-sm tracking-tight text-[var(--text-main)]">Aegis</span>
                <span className="text-xs px-2 py-0.5 rounded font-mono font-medium bg-[var(--bg-card-subtle)] text-[var(--text-secondary)] border border-[var(--border-main)]">
                  v2026.4
                </span>
              </div>
              <p className="text-xs text-[var(--text-secondary)]">Postprandial Digital Twin Platform</p>
            </div>
          </div>

          {/* Segmented View Tabs (Figma UI3 Style) */}
          <nav aria-label="Views" className="flex items-center p-1 rounded-xl bg-[var(--bg-card-subtle)] border border-[var(--border-main)] text-xs font-medium">
            <button
              onClick={() => setActiveTab("forecast")}
              className={`px-3.5 py-1.5 rounded-lg transition ${
                activeTab === "forecast" ? "bg-[var(--nav-active-bg)] text-[var(--nav-active-text)] font-semibold shadow-sm" : "text-[var(--text-secondary)] hover:text-[var(--text-main)]"
              }`}
            >
              Forecast
            </button>
            <button
              onClick={() => setActiveTab("whatif")}
              className={`px-3.5 py-1.5 rounded-lg transition ${
                activeTab === "whatif" ? "bg-[var(--nav-active-bg)] text-[var(--nav-active-text)] font-semibold shadow-sm" : "text-[var(--text-secondary)] hover:text-[var(--text-main)]"
              }`}
            >
              What-If Sandbox
            </button>
            <button
              onClick={() => setActiveTab("profile")}
              className={`px-3.5 py-1.5 rounded-lg transition ${
                activeTab === "profile" ? "bg-[var(--nav-active-bg)] text-[var(--nav-active-text)] font-semibold shadow-sm" : "text-[var(--text-secondary)] hover:text-[var(--text-main)]"
              }`}
            >
              Patient Profile
            </button>
            <button
              onClick={() => setActiveTab("audit")}
              className={`px-3.5 py-1.5 rounded-lg transition ${
                activeTab === "audit" ? "bg-[var(--nav-active-bg)] text-[var(--nav-active-text)] font-semibold shadow-sm" : "text-[var(--text-secondary)] hover:text-[var(--text-main)]"
              }`}
            >
              Sensor Quality
            </button>
          </nav>

          {/* Controls & Dark / Light Switch */}
          <div className="flex items-center gap-3">
            {/* Command Palette Button */}
            <button
              onClick={() => setIsPaletteOpen(true)}
              className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg border border-[var(--border-main)] bg-[var(--bg-card-subtle)] text-[var(--text-secondary)] hover:text-[var(--text-main)] text-xs transition"
            >
              <span>Search actions</span>
              <kbd className="font-mono text-[11px] px-1.5 py-0.5 rounded bg-[var(--bg-card)] border border-[var(--border-main)]">⌘K</kbd>
            </button>

            {/* Dark & Light Segmented Switch */}
            <div className="flex items-center p-0.5 rounded-lg border border-[var(--border-main)] bg-[var(--bg-canvas)]">
              <button
                onClick={() => handleSetTheme("light")}
                className={`px-2.5 py-1 rounded-md text-xs font-medium flex items-center gap-1.5 transition ${
                  theme === "light" ? "bg-[var(--bg-card)] text-[var(--text-main)] shadow-sm font-semibold" : "text-[var(--text-secondary)] hover:text-[var(--text-main)]"
                }`}
                title="Switch to Light mode"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
                <span>Light</span>
              </button>
              <button
                onClick={() => handleSetTheme("dark")}
                className={`px-2.5 py-1 rounded-md text-xs font-medium flex items-center gap-1.5 transition ${
                  theme === "dark" ? "bg-[var(--bg-card)] text-[var(--text-main)] shadow-sm font-semibold" : "text-[var(--text-secondary)] hover:text-[var(--text-main)]"
                }`}
                title="Switch to Dark mode"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
                <span>Dark</span>
              </button>
            </div>
          </div>

        </div>
      </header>

      {/* 3. Sub-toolbar: Patient Selector & Stream Controls */}
      <section className="bg-[var(--bg-card)] border-b border-[var(--border-main)] px-6 py-2.5 transition-colors duration-200">
        <div className="max-w-[1720px] mx-auto flex flex-wrap items-center justify-between gap-3 text-xs">
          
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="text-[var(--text-secondary)] font-medium">Digital Twin:</span>
              <select
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                className="bg-[var(--bg-card-subtle)] border border-[var(--border-main)] text-[var(--text-main)] rounded-lg px-2.5 py-1 font-medium outline-none focus:border-emerald-500 cursor-pointer"
              >
                <option value="P020">P020 — T2D (58y, HbA1c 7.4%)</option>
                <option value="P021">P021 — T2D (61y, HbA1c 7.8%)</option>
                <option value="P010">P010 — Prediabetes (48y, HbA1c 6.0%)</option>
                <option value="P001">P001 — Healthy Control (28y, HbA1c 5.2%)</option>
              </select>
            </div>

            <div className="h-4 w-px bg-[var(--border-main)] hidden sm:block"></div>

            {/* Playback Controls */}
            <div className="flex items-center gap-1.5">
              <button
                onClick={isPlaying ? handlePause : handleStart}
                className="px-3 py-1 rounded-lg border border-[var(--border-main)] bg-[var(--bg-card-subtle)] hover:border-[var(--border-subtle)] font-medium text-[var(--text-main)] flex items-center gap-1.5 transition"
              >
                <span>{isPlaying ? "⏸ Pause" : "▶ Play"}</span>
                <kbd className="font-mono text-[10px] text-[var(--text-secondary)]">Space</kbd>
              </button>
              <button
                onClick={handleJumpNextMeal}
                className="px-3 py-1 rounded-lg border border-[var(--border-main)] bg-[var(--bg-card-subtle)] hover:border-[var(--border-subtle)] font-medium text-[var(--text-main)] flex items-center gap-1.5 transition"
              >
                <span>Next Meal</span>
                <kbd className="font-mono text-[10px] text-[var(--text-secondary)]">N</kbd>
              </button>
            </div>

            <div className="h-4 w-px bg-[var(--border-main)] hidden sm:block"></div>

            <div className="flex items-center gap-1.5">
              <span className="text-[var(--text-secondary)]">Speed:</span>
              <select
                value={speed}
                onChange={(e) => setSpeed(Number(e.target.value))}
                className="bg-[var(--bg-card-subtle)] border border-[var(--border-main)] text-[var(--text-main)] rounded-lg px-2 py-1 font-mono outline-none cursor-pointer"
              >
                <option value={1}>1x</option>
                <option value={5}>5x</option>
                <option value={10}>10x</option>
                <option value={20}>20x</option>
              </select>
            </div>
          </div>

          <div className="flex items-center gap-3 font-mono text-[var(--text-secondary)]">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span> Sensor Replay Synchronized
            </span>
            <span>•</span>
            <span>5-Min Cadence</span>
          </div>

        </div>
      </section>

      {/* 4. Main View Body */}
      <main className="flex-1 p-6 max-w-[1720px] w-full mx-auto">
        
        {/* TAB 1: LIVE FORECAST & MONITORING */}
        {activeTab === "forecast" && (
          <div className="space-y-6">
            
            {/* Bento KPI Summary Row */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              
              {/* CGM Glucose Card with ATTD/ADA TIR Segmented Bar */}
              <div className="clean-card p-5 space-y-2">
                <div className="flex items-center justify-between text-xs text-[var(--text-secondary)]">
                  <span>Current Glycemia (CGM)</span>
                  <span className="px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                    IN RANGE
                  </span>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-bold font-mono tracking-tight text-[var(--text-main)]">{liveGlucose}</span>
                  <span className="text-xs text-[var(--text-secondary)]">mg/dL</span>
                </div>
                {/* ADA TIR 3-Segment Bar */}
                <div className="pt-2 space-y-1">
                  <div className="flex justify-between text-[11px] font-mono text-[var(--text-secondary)]">
                    <span className="text-emerald-600 dark:text-emerald-400 font-semibold">TIR: 78% (&ge;70%)</span>
                    <span>GMI: 6.8%</span>
                  </div>
                  <div className="w-full h-1.5 rounded-full overflow-hidden flex bg-[var(--border-main)]">
                    <div className="bg-emerald-500 h-full" style={{ width: "78%" }} title="Time In Range (70-180 mg/dL): 78%"></div>
                    <div className="bg-rose-500 h-full" style={{ width: "18%" }} title="Time Above Range (>180 mg/dL): 18%"></div>
                    <div className="bg-amber-400 h-full" style={{ width: "4%" }} title="Time Below Range (<70 mg/dL): 4%"></div>
                  </div>
                </div>
                <div className="flex items-center justify-between text-[11px] text-[var(--text-muted)] pt-2 border-t border-[var(--border-main)]">
                  <span className="text-emerald-600 dark:text-emerald-400 font-mono">↗ +1.2 mg/dL/min</span>
                  <span>Dexcom G6 5-min</span>
                </div>
              </div>

              {/* Heart Rate Card */}
              <div className="clean-card p-5 space-y-2">
                <div className="flex items-center justify-between text-xs text-[var(--text-secondary)]">
                  <span>Resting &amp; Active HR</span>
                  <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-[var(--bg-card-subtle)] text-[var(--text-secondary)] border border-[var(--border-main)]">
                    NORMAL
                  </span>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-bold font-mono tracking-tight text-[var(--text-main)]">{liveHR}</span>
                  <span className="text-xs text-[var(--text-secondary)]">bpm</span>
                </div>
                <div className="flex items-center justify-between text-[11px] text-[var(--text-muted)] pt-6 border-t border-[var(--border-main)]">
                  <span>Baseline: 68 bpm</span>
                  <span>Optical PPG Wearable</span>
                </div>
              </div>

              {/* Physical Activity (METs) Card */}
              <div className="clean-card p-5 space-y-2">
                <div className="flex items-center justify-between text-xs text-[var(--text-secondary)]">
                  <span>Physical Activity</span>
                  <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-[var(--bg-card-subtle)] text-[var(--text-secondary)] border border-[var(--border-main)]">
                    SEDENTARY
                  </span>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-bold font-mono tracking-tight text-[var(--text-main)]">{liveMETs.toFixed(2)}</span>
                  <span className="text-xs text-[var(--text-secondary)]">METs</span>
                </div>
                <div className="flex items-center justify-between text-[11px] text-[var(--text-muted)] pt-6 border-t border-[var(--border-main)]">
                  <span>Desk Activity</span>
                  <span>Accelerometry Fusion</span>
                </div>
              </div>

              {/* Active Meal Profile Card */}
              <div className="clean-card p-5 space-y-2">
                <div className="flex items-center justify-between text-xs text-[var(--text-secondary)]">
                  <span>Active Clinical Meal</span>
                  <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                    RECORDED
                  </span>
                </div>
                <div className="truncate font-semibold text-[var(--text-main)] text-sm">
                  {lastMeal}
                </div>
                <div className="text-xs font-mono text-[var(--text-secondary)]">
                  {lastMealMacros}
                </div>
                <div className="flex items-center justify-between text-[11px] text-[var(--text-muted)] pt-2 border-t border-[var(--border-main)]">
                  <span className="text-emerald-600 dark:text-emerald-400">12-Step Buffer Ready</span>
                  <span>Parquet Ingest</span>
                </div>
              </div>

            </div>

            {/* Trajectory Canvas Card */}
            <div className="clean-card p-6 space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[var(--border-main)] pb-3">
                <div>
                  <div className="flex items-center gap-3">
                    <h2 className="text-base font-semibold text-[var(--text-main)] tracking-tight">
                      180-Minute Postprandial Glycemic Forecast
                    </h2>
                    <span className="px-2.5 py-0.5 rounded text-[11px] font-mono font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                      {reliability} CONFIDENCE
                    </span>
                  </div>
                  <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                    Candidate S dual-gamma absorption model with 90% conformal uncertainty intervals and ground truth overlay
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-3 text-xs">
                  <span className="flex items-center gap-1.5 text-[var(--text-secondary)]">
                    <span className="w-3 h-0.5 bg-emerald-500 inline-block"></span> Candidate S Prediction
                  </span>
                  <span className="flex items-center gap-1.5 text-[var(--text-secondary)]">
                    <span className="w-3 h-0.5 border-b-2 border-dashed border-amber-500 inline-block"></span> Recorded CGM Truth
                  </span>
                  <span className="flex items-center gap-1.5 text-[var(--text-secondary)]">
                    <span className="w-3 h-2 bg-emerald-500/15 border border-emerald-500/30 rounded-sm inline-block"></span> 90% Conformal Interval
                  </span>
                </div>
              </div>

              {/* Scrubber HUD Bar */}
              <div className="flex flex-wrap items-center justify-between px-3.5 py-1.5 rounded-lg bg-[var(--bg-card-subtle)] border border-[var(--border-main)] text-xs font-mono text-[var(--text-secondary)]">
                <div className="flex items-center gap-3">
                  <span>Scrubber HUD:</span>
                  <span className="font-semibold text-[var(--text-main)]">+55 min</span>
                  <span className="text-[var(--border-subtle)]">|</span>
                  <span className="text-emerald-600 dark:text-emerald-400 font-semibold">Pred: 164.2 mg/dL</span>
                  <span className="text-[var(--border-subtle)]">|</span>
                  <span>90% Bounds: [150.2 – 178.2]</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-amber-600 dark:text-amber-400 font-semibold">Truth: 162.0 mg/dL</span>
                  <span className="text-[var(--text-muted)]">(Δ -2.2)</span>
                </div>
              </div>

              {/* Visual Curve Area */}
              <div className="h-80 w-full bg-[var(--bg-canvas)] rounded-xl border border-[var(--border-main)] p-4 flex flex-col justify-between">
                <div className="flex justify-between items-center text-xs text-rose-600 dark:text-rose-400 font-mono border-b border-rose-500/20 pb-1">
                  <span>Hyperglycemia Threshold (180 mg/dL)</span>
                  <span className="px-1.5 py-0.5 rounded bg-rose-500/10 border border-rose-500/20 text-[10px]">ADA Target &lt; 180</span>
                </div>

                <div className="flex-1 flex items-center justify-center text-center">
                  <div className="space-y-1">
                    <span className="text-sm font-semibold text-[var(--text-main)] block">Candidate S PyTorch Streaming Active</span>
                    <span className="text-xs text-[var(--text-secondary)] block max-w-lg mx-auto">
                      Streaming calibrated 5-min post-meal telemetry and personalized Ridge weights.
                    </span>
                  </div>
                </div>

                <div className="flex justify-between text-xs text-[var(--text-muted)] font-mono border-t border-[var(--border-main)] pt-2">
                  <span>0m</span>
                  <span>30m</span>
                  <span>60m (Peak)</span>
                  <span>90m</span>
                  <span>120m</span>
                  <span>180m</span>
                </div>
              </div>

              {/* 4 Quantitative Metric Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2 border-t border-[var(--border-main)]">
                <div className="bg-[var(--bg-card-subtle)] p-3 rounded-lg border border-[var(--border-main)] text-center">
                  <span className="text-xs text-[var(--text-secondary)] block mb-0.5">Predicted Peak</span>
                  <span className="text-xl font-bold font-mono text-[var(--text-main)]">164.2 mg/dL</span>
                  <span className="text-[11px] text-emerald-600 dark:text-emerald-400 block mt-0.5">Within Target</span>
                </div>
                <div className="bg-[var(--bg-card-subtle)] p-3 rounded-lg border border-[var(--border-main)] text-center">
                  <span className="text-xs text-[var(--text-secondary)] block mb-0.5">Time to Peak</span>
                  <span className="text-xl font-bold font-mono text-[var(--text-main)]">55 min</span>
                  <span className="text-[11px] text-[var(--text-muted)] block mt-0.5">Absorption Window</span>
                </div>
                <div className="bg-[var(--bg-card-subtle)] p-3 rounded-lg border border-[var(--border-main)] text-center">
                  <span className="text-xs text-[var(--text-secondary)] block mb-0.5">Delayed Mean (120-180m)</span>
                  <span className="text-xl font-bold font-mono text-sky-600 dark:text-sky-400">138.4 mg/dL</span>
                  <span className="text-[11px] text-[var(--text-muted)] block mt-0.5">Late Lipid Plateau</span>
                </div>
                <div className="bg-[var(--bg-card-subtle)] p-3 rounded-lg border border-[var(--border-main)] text-center">
                  <span className="text-xs text-[var(--text-secondary)] block mb-0.5">Time Above 180</span>
                  <span className="text-xl font-bold font-mono text-emerald-600 dark:text-emerald-400">0 min (0%)</span>
                  <span className="text-[11px] text-emerald-600 dark:text-emerald-400 block mt-0.5">Optimal Safety</span>
                </div>
              </div>

            </div>

          </div>
        )}

        {/* TAB 2: INTERACTIVE WHAT-IF MEAL SANDBOX */}
        {activeTab === "whatif" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              
              <div className="lg:col-span-5 clean-card p-6 space-y-5">
                <div className="border-b border-[var(--border-main)] pb-3 flex items-center justify-between">
                  <div>
                    <h2 className="text-base font-semibold text-[var(--text-main)]">What-If Counterfactual Sandbox</h2>
                    <p className="text-xs text-[var(--text-secondary)] mt-0.5">Modify macronutrients, portion scaling, or physical exercise timing</p>
                  </div>

                  <button
                    onClick={() => setIsCustomMealOpen(true)}
                    className="px-2.5 py-1.5 rounded-lg border border-[var(--border-main)] bg-[var(--bg-card-subtle)] hover:border-[var(--border-subtle)] text-xs font-medium text-[var(--text-main)] flex items-center gap-1 transition"
                  >
                    <span>+ Custom Meal</span>
                  </button>
                </div>

                {/* Preset Meal Quick Cards */}
                <div className="space-y-2">
                  <label className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] block">
                    Regional Indian Presets:
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      onClick={() => selectDish("roti_dal_sabzi")}
                      className={`text-left p-3 rounded-lg border transition ${
                        activeDishName.includes("Roti") ? "border-emerald-500 bg-emerald-500/5" : "border-[var(--border-main)] bg-[var(--bg-card-subtle)] hover:border-[var(--border-subtle)]"
                      }`}
                    >
                      <div className="text-xs font-medium text-[var(--text-main)]">Roti, Dal &amp; Sabzi</div>
                      <div className="text-[11px] text-[var(--text-secondary)] mt-0.5">48g C • 12g F • 16g P</div>
                    </button>
                    <button
                      onClick={() => selectDish("masala_dosa")}
                      className={`text-left p-3 rounded-lg border transition ${
                        activeDishName.includes("Dosa") ? "border-emerald-500 bg-emerald-500/5" : "border-[var(--border-main)] bg-[var(--bg-card-subtle)] hover:border-[var(--border-subtle)]"
                      }`}
                    >
                      <div className="text-xs font-medium text-[var(--text-main)]">Masala Dosa + Sambar</div>
                      <div className="text-[11px] text-[var(--text-secondary)] mt-0.5">62g C • 18g F • 10g P</div>
                    </button>
                    <button
                      onClick={() => selectDish("chicken_biryani")}
                      className={`text-left p-3 rounded-lg border transition ${
                        activeDishName.includes("Biryani") ? "border-emerald-500 bg-emerald-500/5" : "border-[var(--border-main)] bg-[var(--bg-card-subtle)] hover:border-[var(--border-subtle)]"
                      }`}
                    >
                      <div className="text-xs font-medium text-[var(--text-main)]">Chicken Biryani</div>
                      <div className="text-[11px] text-[var(--text-secondary)] mt-0.5">68g C • 22g F • 32g P</div>
                    </button>
                    <button
                      onClick={() => selectDish("rajma_chawal")}
                      className={`text-left p-3 rounded-lg border transition ${
                        activeDishName.includes("Rajma") ? "border-emerald-500 bg-emerald-500/5" : "border-[var(--border-main)] bg-[var(--bg-card-subtle)] hover:border-[var(--border-subtle)]"
                      }`}
                    >
                      <div className="text-xs font-medium text-[var(--text-main)]">Rajma Chawal</div>
                      <div className="text-[11px] text-[var(--text-secondary)] mt-0.5">72g C • 14g F • 20g P</div>
                    </button>
                  </div>
                </div>

                {/* Dynamic Macro Visualizer */}
                <div className="bg-[var(--bg-card-subtle)] p-3 rounded-lg border border-[var(--border-main)] space-y-2">
                  <div className="flex justify-between text-xs text-[var(--text-main)]">
                    <span className="font-semibold">{activeDishName}</span>
                    <span className="font-mono font-semibold">{totalKcal} kcal</span>
                  </div>
                  <div className="w-full h-2.5 rounded-full overflow-hidden flex bg-[var(--border-main)]">
                    <div className="bg-amber-500 h-full transition-all duration-300" style={{ width: `${cPct}%` }}></div>
                    <div className="bg-emerald-500 h-full transition-all duration-300" style={{ width: `${pPct}%` }}></div>
                    <div className="bg-sky-500 h-full transition-all duration-300" style={{ width: `${fPct}%` }}></div>
                  </div>
                  <div className="flex justify-between text-[11px] font-mono text-[var(--text-secondary)]">
                    <span>Carbs ({cPct}%)</span>
                    <span>Protein ({pPct}%)</span>
                    <span>Fat ({fPct}%)</span>
                  </div>
                </div>

                {/* Range Sliders */}
                <div className="space-y-4 pt-1">
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-[var(--text-secondary)] font-medium">Carbohydrates</span>
                      <span className="font-mono font-semibold text-amber-600 dark:text-amber-400">{carbs} g</span>
                    </div>
                    <input type="range" min={10} max={140} value={carbs} onChange={(e) => setCarbs(Number(e.target.value))} className="w-full accent-emerald-500" />
                  </div>

                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-[var(--text-secondary)] font-medium">Dietary Fat</span>
                      <span className="font-mono font-semibold text-sky-600 dark:text-sky-400">{fat} g</span>
                    </div>
                    <input type="range" min={0} max={60} value={fat} onChange={(e) => setFat(Number(e.target.value))} className="w-full accent-emerald-500" />
                  </div>

                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-[var(--text-secondary)] font-medium">Protein</span>
                      <span className="font-mono font-semibold text-emerald-600 dark:text-emerald-400">{protein} g</span>
                    </div>
                    <input type="range" min={0} max={60} value={protein} onChange={(e) => setProtein(Number(e.target.value))} className="w-full accent-emerald-500" />
                  </div>

                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-[var(--text-secondary)] font-medium">Portion Scaling</span>
                      <span className="font-mono font-semibold text-[var(--text-main)]">{portion}%</span>
                    </div>
                    <input type="range" min={25} max={200} step={25} value={portion} onChange={(e) => setPortion(Number(e.target.value))} className="w-full accent-emerald-500" />
                  </div>
                </div>

                {/* Behavioral Interventions */}
                <div className="pt-3 border-t border-[var(--border-main)] space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)]">Behavioral Interventions</span>
                    <span className="text-[11px] px-2 py-0.5 rounded font-mono font-semibold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                      ASSUMPTION
                    </span>
                  </div>

                  <label className="flex items-center justify-between p-3 rounded-lg border border-[var(--border-main)] bg-[var(--bg-card-subtle)] cursor-pointer hover:border-[var(--border-subtle)] transition">
                    <div className="space-y-0.5">
                      <div className="text-xs font-medium text-[var(--text-main)] flex items-center gap-1.5">
                        <span>Post-Meal 15-Minute Brisk Walk</span>
                        <span className="text-emerald-600 dark:text-emerald-400 font-mono font-semibold">-18 mg/dL</span>
                      </div>
                      <div className="text-[11px] text-[var(--text-secondary)]">Elevates METs to 3.2 at +30m postprandial</div>
                    </div>
                    <input type="checkbox" checked={walking} onChange={(e) => setWalking(e.target.checked)} className="w-4 h-4 rounded accent-emerald-500" />
                  </label>

                  <label className="flex items-center justify-between p-3 rounded-lg border border-[var(--border-main)] bg-[var(--bg-card-subtle)] cursor-pointer hover:border-[var(--border-subtle)] transition">
                    <div className="space-y-0.5">
                      <div className="text-xs font-medium text-[var(--text-main)] flex items-center gap-1.5">
                        <span>Food Sequencing (Protein/Veg First)</span>
                        <span className="text-emerald-600 dark:text-emerald-400 font-mono font-semibold">-15 mg/dL</span>
                      </div>
                      <div className="text-[11px] text-[var(--text-secondary)]">Delays gastric emptying rate via GLP-1</div>
                    </div>
                    <input type="checkbox" checked={sequencing} onChange={(e) => setSequencing(e.target.checked)} className="w-4 h-4 rounded accent-emerald-500" />
                  </label>
                </div>
              </div>

              {/* Simulation Comparison Column */}
              <div className="lg:col-span-7 clean-card p-6 space-y-5">
                <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[var(--border-main)] pb-3">
                  <div>
                    <h2 className="text-base font-semibold text-[var(--text-main)]">Comparative Digital Twin Response</h2>
                    <p className="text-xs text-[var(--text-secondary)] mt-0.5">Baseline excursion vs counterfactual modified scenario</p>
                  </div>
                  <div className="flex items-center gap-3 text-xs">
                    <span className="flex items-center gap-1.5 text-[var(--text-secondary)]">
                      <span className="w-3 h-0.5 bg-emerald-500 inline-block"></span> Baseline
                    </span>
                    <span className="flex items-center gap-1.5 text-[var(--text-secondary)]">
                      <span className="w-3 h-0.5 bg-purple-500 inline-block"></span> Counterfactual
                    </span>
                  </div>
                </div>

                <div className="h-80 bg-[var(--bg-canvas)] rounded-xl border border-[var(--border-main)] p-4 flex flex-col justify-between">
                  <div className="flex justify-between text-xs text-[var(--text-muted)] font-mono">
                    <span>Simulation: Candidate S Neural Absorption Model</span>
                    <span className="text-emerald-600 dark:text-emerald-400">Portion: {portion}%</span>
                  </div>
                  <div className="text-center space-y-1">
                    <div className="text-2xl font-bold font-mono text-purple-600 dark:text-purple-400">
                      Peak Estimate: {(164.2 * (portion / 100) - (walking ? 18 : 0) - (sequencing ? 15 : 0)).toFixed(1)} mg/dL
                    </div>
                    <div className="text-xs text-[var(--text-secondary)]">
                      Adjusted for {carbs}g Carbs, {fat}g Fat, {protein}g Protein
                    </div>
                  </div>
                  <div className="flex justify-between text-xs text-[var(--text-muted)] font-mono border-t border-[var(--border-main)] pt-1">
                    <span>0m</span>
                    <span>45m</span>
                    <span>90m</span>
                    <span>135m</span>
                    <span>180m</span>
                  </div>
                </div>

                {/* Deltas */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div className="bg-[var(--bg-card-subtle)] p-3.5 rounded-lg border border-[var(--border-main)]">
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-[var(--text-secondary)]">Δ Peak Glycemia</span>
                      <span className="text-[10px] font-mono font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 px-1.5 py-0.2 rounded">
                        MODEL
                      </span>
                    </div>
                    <div className="text-xl font-bold font-mono text-emerald-600 dark:text-emerald-400">
                      {((portion / 100 - 1) * 35 - (walking ? 18 : 0) - (sequencing ? 15 : 0)).toFixed(1)} mg/dL
                    </div>
                    <span className="text-[11px] text-[var(--text-muted)] mt-1 block">Excursion maximum delta</span>
                  </div>

                  <div className="bg-[var(--bg-card-subtle)] p-3.5 rounded-lg border border-[var(--border-main)]">
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-[var(--text-secondary)]">Δ Delayed Mean</span>
                      <span className="text-[10px] font-mono font-semibold bg-sky-500/10 text-sky-600 dark:text-sky-400 px-1.5 py-0.2 rounded">
                        MODEL
                      </span>
                    </div>
                    <div className="text-xl font-bold font-mono text-sky-600 dark:text-sky-400">
                      {((fat - 12) * 0.3).toFixed(1)} mg/dL
                    </div>
                    <span className="text-[11px] text-[var(--text-muted)] mt-1 block">Late lipid plateau effect</span>
                  </div>

                  <div className="bg-[var(--bg-card-subtle)] p-3.5 rounded-lg border border-[var(--border-main)]">
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-[var(--text-secondary)]">Behavioral Impact</span>
                      <span className="text-[10px] font-mono font-semibold bg-amber-500/10 text-amber-600 dark:text-amber-400 px-1.5 py-0.2 rounded">
                        ASSUMPTION
                      </span>
                    </div>
                    <div className="text-xl font-bold font-mono text-amber-600 dark:text-amber-400">
                      {(walking ? -18 : 0) + (sequencing ? -15 : 0)} mg/dL
                    </div>
                    <span className="text-[11px] text-[var(--text-muted)] mt-1 block">Literature exercise scalar</span>
                  </div>
                </div>

              </div>

            </div>
          </div>
        )}

        {/* TAB 3: PATIENT PROFILE */}
        {activeTab === "profile" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              
              <div className="clean-card p-6 space-y-4">
                <h2 className="text-base font-semibold text-[var(--text-main)]">Clinical Baseline Profile</h2>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between py-2 border-b border-[var(--border-main)]"><span className="text-[var(--text-secondary)]">Patient:</span> <span className="font-mono text-[var(--text-main)] font-semibold">{patientId}</span></div>
                  <div className="flex justify-between py-2 border-b border-[var(--border-main)]"><span className="text-[var(--text-secondary)]">Diagnosis:</span> <span className="text-emerald-600 dark:text-emerald-400 font-semibold">Type 2 Diabetes</span></div>
                  <div className="flex justify-between py-2 border-b border-[var(--border-main)]"><span className="text-[var(--text-secondary)]">Age &amp; Sex:</span> <span className="text-[var(--text-main)]">58y / Male</span></div>
                  <div className="flex justify-between py-2 border-b border-[var(--border-main)]"><span className="text-[var(--text-secondary)]">BMI:</span> <span className="text-[var(--text-main)] font-mono">28.4 kg/m²</span></div>
                  <div className="flex justify-between py-2 border-b border-[var(--border-main)]"><span className="text-[var(--text-secondary)]">Baseline HbA1c:</span> <span className="text-amber-600 dark:text-amber-400 font-semibold font-mono">7.4%</span></div>
                  <div className="flex justify-between py-2"><span className="text-[var(--text-secondary)]">Fasting Glucose:</span> <span className="text-[var(--text-main)] font-mono">138 mg/dL</span></div>
                </div>
              </div>

              <div className="clean-card p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-base font-semibold text-[var(--text-main)]">Synthetic EHR Records</h2>
                  <span className="text-[11px] px-2 py-0.5 rounded font-mono font-semibold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                    SYNTHETIC (D14)
                  </span>
                </div>
                <div className="space-y-3 text-xs">
                  <div className="p-3 bg-[var(--bg-card-subtle)] rounded-lg border border-[var(--border-main)]">
                    <span className="text-[var(--text-secondary)] block font-medium">Prescribed Medications:</span>
                    <span className="text-[var(--text-main)] mt-0.5 block">Metformin 500mg BID, Lisinopril 10mg QD</span>
                  </div>
                  <div className="p-3 bg-[var(--bg-card-subtle)] rounded-lg border border-[var(--border-main)]">
                    <span className="text-[var(--text-secondary)] block font-medium">Diagnosed Comorbidities:</span>
                    <span className="text-[var(--text-main)] mt-0.5 block">Essential Hypertension, Dyslipidemia</span>
                  </div>
                </div>
              </div>

              <div className="clean-card p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-base font-semibold text-[var(--text-main)]">Few-Shot Personalization</h2>
                  <span className="text-[11px] px-2 py-0.5 rounded font-mono font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                    K = 5 MEALS
                  </span>
                </div>
                <div className="space-y-2 text-xs font-mono">
                  <div className="p-3 bg-[var(--bg-card-subtle)] rounded-lg border border-[var(--border-main)] space-y-1.5">
                    <div className="flex justify-between text-[var(--text-secondary)]"><span>Zero-Shot (K=0):</span> <span className="text-rose-500">12.95 mg/dL</span></div>
                    <div className="flex justify-between text-[var(--text-secondary)]"><span>1-Shot (K=1):</span> <span className="text-amber-500">10.84 mg/dL</span></div>
                    <div className="flex justify-between text-[var(--text-secondary)]"><span>3-Shot (K=3):</span> <span className="text-emerald-500">9.45 mg/dL</span></div>
                    <div className="flex justify-between text-emerald-600 dark:text-emerald-400 font-bold border-t border-[var(--border-main)] pt-1.5">
                      <span>5-Shot Adapted (K=5):</span> <span>8.92 mg/dL</span>
                    </div>
                  </div>
                </div>
              </div>

            </div>
          </div>
        )}

        {/* TAB 4: SENSOR QUALITY & STRESS-TEST */}
        {activeTab === "audit" && (
          <div className="space-y-6">
            <div className="clean-card p-6 space-y-5">
              <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[var(--border-main)] pb-3">
                <div>
                  <h2 className="text-base font-semibold text-[var(--text-main)]">Sensor Degradation &amp; Stress Testing (D0–D7)</h2>
                  <p className="text-xs text-[var(--text-secondary)] mt-0.5">Audit digital twin reliability under realistic wear failures and signal dropouts</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-[var(--text-secondary)]">Active Scenario:</span>
                  <span className="text-xs font-mono font-semibold bg-[var(--bg-card-subtle)] border border-emerald-500/40 text-emerald-600 dark:text-emerald-400 px-3 py-1 rounded-lg">
                    {degradation}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                {[
                  { id: "D0", label: "D0: Nominal Stream", desc: "No dropouts, continuous 5-min telemetry", status: "HIGH" },
                  { id: "D1_15m", label: "D1: Dropout 15m", desc: "Minor CGM retrospective gap", status: "MODERATE" },
                  { id: "D1_30m", label: "D1: Dropout 30m", desc: "Noticeable 30-min CGM gap", status: "MODERATE" },
                  { id: "D1_45m", label: "D1: Dropout 45m", desc: "Major CGM sensor silence", status: "LOW" },
                  { id: "D2", label: "D2: Low Sampling (15m)", desc: "Decimated to 15-min cadence", status: "MODERATE" },
                  { id: "D3", label: "D3: No HR / METs", desc: "Wearable battery failure", status: "MODERATE" },
                  { id: "D4", label: "D4: 50% Decimated CGM", desc: "Sparse glucose telemetry", status: "LOW" },
                  { id: "D7", label: "D7: Extreme Dropout (90m)", desc: "Severe CGM sensor failure", status: "LOW" },
                ].map((item) => (
                  <button
                    key={item.id}
                    onClick={() => handleDegradation(item.id)}
                    className={`p-4 rounded-lg border text-left transition ${
                      degradation === item.id
                        ? "bg-[var(--bg-card)] border-emerald-500 shadow-sm"
                        : "bg-[var(--bg-card-subtle)] border-[var(--border-main)] hover:border-[var(--border-subtle)]"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-semibold text-[var(--text-main)]">{item.label}</span>
                      <span className={`text-[10px] px-1.5 py-0.2 rounded font-mono font-semibold ${
                        item.status === "HIGH" ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400" : item.status === "MODERATE" ? "bg-amber-500/10 text-amber-600 dark:text-amber-400" : "bg-rose-500/10 text-rose-600 dark:text-rose-400"
                      }`}>
                        {item.status}
                      </span>
                    </div>
                    <span className="text-[11px] text-[var(--text-secondary)] block">{item.desc}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

      </main>

      {/* 5. Command Palette Modal */}
      {isPaletteOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-start justify-center pt-24 px-4">
          <div className="w-full max-w-xl bg-[var(--bg-card)] rounded-xl border border-[var(--border-main)] shadow-2xl overflow-hidden">
            <div className="p-3.5 border-b border-[var(--border-main)] flex items-center gap-3 bg-[var(--bg-card-subtle)]">
              <input
                type="text"
                autoFocus
                value={paletteQuery}
                onChange={(e) => { setPaletteQuery(e.target.value); setPaletteIndex(0); }}
                placeholder="Search actions, patients, presets, or theme..."
                className="bg-transparent text-[var(--text-main)] placeholder-[var(--text-muted)] text-xs outline-none flex-1 font-sans"
              />
              <kbd className="text-[11px] font-mono bg-[var(--bg-card)] text-[var(--text-secondary)] px-2 py-0.5 rounded border border-[var(--border-main)]">ESC</kbd>
            </div>
            <div className="max-h-80 overflow-y-auto p-2 space-y-1">
              {filteredActions.length === 0 ? (
                <div className="text-xs text-[var(--text-muted)] text-center py-6">No matching actions</div>
              ) : (
                filteredActions.map((item, idx) => (
                  <div
                    key={item.id}
                    onClick={() => { item.run(); setIsPaletteOpen(false); }}
                    className={`flex items-center justify-between p-2.5 rounded-lg cursor-pointer transition text-xs ${
                      idx === paletteIndex ? "bg-emerald-500/10 border border-emerald-500/40 text-[var(--text-main)]" : "bg-[var(--bg-card-subtle)] border border-transparent text-[var(--text-secondary)] hover:text-[var(--text-main)] hover:border-[var(--border-main)]"
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                      <span>{item.title}</span>
                    </div>
                    <span className="font-mono text-[11px] bg-[var(--bg-card)] px-2 py-0.5 rounded text-[var(--text-secondary)] border border-[var(--border-main)]">{item.key}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* 6. Custom Meal Modal */}
      {isCustomMealOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-[var(--bg-card)] rounded-xl border border-[var(--border-main)] shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-[var(--border-main)] pb-3">
              <h3 className="text-sm font-semibold text-[var(--text-main)]">Create Custom Meal Input</h3>
              <button onClick={() => setIsCustomMealOpen(false)} className="text-[var(--text-secondary)] hover:text-[var(--text-main)] text-xs">✕</button>
            </div>
            <div className="space-y-3 text-xs">
              <div>
                <label className="text-[var(--text-secondary)] font-medium block mb-1">Dish Name:</label>
                <input
                  type="text"
                  value={customName}
                  onChange={(e) => setCustomName(e.target.value)}
                  className="w-full bg-[var(--bg-card-subtle)] border border-[var(--border-main)] text-[var(--text-main)] rounded-lg p-2.5 outline-none focus:border-emerald-500"
                />
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-amber-600 dark:text-amber-400 font-medium block mb-1">Carbs (g):</label>
                  <input
                    type="number"
                    value={customCarbs}
                    onChange={(e) => setCustomCarbs(Number(e.target.value))}
                    className="w-full bg-[var(--bg-card-subtle)] border border-[var(--border-main)] text-[var(--text-main)] rounded-lg p-2 font-mono outline-none focus:border-amber-500"
                  />
                </div>
                <div>
                  <label className="text-sky-600 dark:text-sky-400 font-medium block mb-1">Fat (g):</label>
                  <input
                    type="number"
                    value={customFat}
                    onChange={(e) => setCustomFat(Number(e.target.value))}
                    className="w-full bg-[var(--bg-card-subtle)] border border-[var(--border-main)] text-[var(--text-main)] rounded-lg p-2 font-mono outline-none focus:border-sky-500"
                  />
                </div>
                <div>
                  <label className="text-emerald-600 dark:text-emerald-400 font-medium block mb-1">Protein (g):</label>
                  <input
                    type="number"
                    value={customProtein}
                    onChange={(e) => setCustomProtein(Number(e.target.value))}
                    className="w-full bg-[var(--bg-card-subtle)] border border-[var(--border-main)] text-[var(--text-main)] rounded-lg p-2 font-mono outline-none focus:border-emerald-500"
                  />
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2.5 pt-3 border-t border-[var(--border-main)]">
              <button
                onClick={() => setIsCustomMealOpen(false)}
                className="px-3.5 py-1.5 rounded-lg border border-[var(--border-main)] bg-[var(--bg-card-subtle)] text-[var(--text-secondary)] hover:text-[var(--text-main)] text-xs font-medium"
              >
                Cancel
              </button>
              <button
                onClick={applyCustomMeal}
                className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-sm transition"
              >
                Apply to Sandbox
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 7. Footer */}
      <footer className="border-t border-[var(--border-main)] px-6 py-3 bg-[var(--bg-card)] text-xs text-[var(--text-secondary)] flex flex-wrap justify-between items-center gap-3 transition-colors duration-200">
        <div>Team Aegis — Happiest Health Digital Twin Challenge 2026</div>
        <div className="flex items-center gap-4">
          <span><kbd className="bg-[var(--bg-card-subtle)] border border-[var(--border-main)] px-1.5 py-0.5 rounded text-[var(--text-main)]">Cmd+K</kbd> Command</span>
          <span><kbd className="bg-[var(--bg-card-subtle)] border border-[var(--border-main)] px-1.5 py-0.5 rounded text-[var(--text-main)]">Space</kbd> Play / Pause</span>
          <span><kbd className="bg-[var(--bg-card-subtle)] border border-[var(--border-main)] px-1.5 py-0.5 rounded text-[var(--text-main)]">N</kbd> Next Meal</span>
        </div>
      </footer>

    </div>
  );
}
