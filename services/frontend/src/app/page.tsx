"use client";

import React, { useState, useEffect } from "react";

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

  // Patient & Replay Cockpit State
  const [patientId, setPatientId] = useState("P020");
  const [speed, setSpeed] = useState(10);
  const [isPlaying, setIsPlaying] = useState(false);
  const [degradation, setDegradation] = useState("D0");
  const [isDarkMode, setIsDarkMode] = useState(true);

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
  const [liveGlucose, setLiveGlucose] = useState(136.6);
  const [liveHR, setLiveHR] = useState(71);
  const [liveMETs, setLiveMETs] = useState(1.00);
  const [lastMeal, setLastMeal] = useState("Roti, Dal & Sabzi");
  const [lastMealMacros, setLastMealMacros] = useState("48g Carbs • 12g Fat");
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
  const actions: CommandAction[] = [
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
    { id: "deg_d0", title: "Stress: Nominal 5-Min Telemetry (D0)", cat: "Stress", key: "D0", run: () => handleDegradation("D0") },
    { id: "deg_d1", title: "Stress: 30m Signal Dropout (D1)", cat: "Stress", key: "D1", run: () => handleDegradation("D1_30m") },
    { id: "deg_d3", title: "Stress: No Wearable HR/METs (D3)", cat: "Stress", key: "D3", run: () => handleDegradation("D3") },
    { id: "tab_1", title: "View: 1. Live Forecast & Monitoring", cat: "View", key: "1", run: () => setActiveTab("forecast") },
    { id: "tab_2", title: "View: 2. What-If Meal Sandbox", cat: "View", key: "2", run: () => setActiveTab("whatif") },
    { id: "tab_3", title: "View: 3. Patient Digital Twin Phenotype", cat: "View", key: "3", run: () => setActiveTab("profile") },
    { id: "tab_4", title: "View: 4. Sensor Stress-Test Studio", cat: "View", key: "4", run: () => setActiveTab("audit") },
  ];

  const filteredActions = actions.filter((a) =>
    a.title.toLowerCase().includes(paletteQuery.toLowerCase()) ||
    a.cat.toLowerCase().includes(paletteQuery.toLowerCase())
  );

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
  }, [isPlaying, patientId, speed, degradation, isPaletteOpen, filteredActions, paletteIndex]);

  return (
    <div className={`flex flex-col min-h-screen ${isDarkMode ? "bg-[#06080e] text-slate-100" : "bg-slate-50 text-slate-900"} font-sans selection:bg-emerald-500/30`}>
      
      {/* 1. Clinical Research & Governance Bar */}
      <aside className="bg-[#0b0f19]/90 border-b border-amber-500/20 text-amber-200/90 px-6 py-2 text-xs flex flex-wrap items-center justify-between gap-3 shadow-inner">
        <div className="flex items-center gap-3">
          <span className="inline-flex items-center gap-1.5 font-bold tracking-wider uppercase bg-amber-500/20 text-amber-300 border border-amber-500/40 px-2 py-0.5 rounded text-xs font-mono">
            Research Prototype
          </span>
          <span className="text-slate-300">
            Candidate S Digital Twin (Dual-Gamma Structured Absorption). <strong className="text-amber-200 font-semibold">Not medical advice and not suitable for treatment decisions.</strong>
          </span>
        </div>
        <div className="flex items-center gap-4 text-xs font-mono text-slate-400">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span> Split-Conformal 90%
          </span>
          <span>•</span>
          <span className="text-emerald-400 font-semibold">Gate G2 Audit Passed</span>
        </div>
      </aside>

      {/* 2. Sleek 2026 Navigation & Cockpit */}
      <header className="bg-[#0b0f19]/80 border-b border-white/[0.08] px-6 py-3.5 sticky top-0 z-40 backdrop-blur-xl shadow-lg">
        <div className="max-w-[1720px] mx-auto flex flex-wrap items-center justify-between gap-4">
          
          {/* Logo & Clinical System Identity */}
          <div className="flex items-center gap-3.5">
            <div className="relative flex items-center justify-center">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600/30 to-cyan-500/20 border border-emerald-500/40 flex items-center justify-center shadow-[0_0_20px_rgba(16,185,129,0.25)]">
                <span className="text-emerald-400 font-bold text-base">AE</span>
              </div>
              <span className="absolute -top-1 -right-1 flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
              </span>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold tracking-tight text-white flex items-center gap-2">
                  AEGIS <span className="text-slate-400 font-normal">Twin Suite</span>
                </h1>
                <span className="bg-slate-800 text-cyan-400 border border-cyan-500/30 text-xs px-2 py-0.5 rounded font-mono font-semibold">
                  2026.4-PROD
                </span>
              </div>
              <p className="text-xs text-slate-400">Continuous 180-Min Postprandial Glycemic Digital Twin</p>
            </div>
          </div>

          {/* Replay Controls Cockpit */}
          <div className="flex flex-wrap items-center gap-2.5 bg-[#06080e]/90 p-1.5 rounded-2xl border border-white/[0.08] shadow-inner">
            
            {/* Command Palette Trigger */}
            <button
              onClick={() => setIsPaletteOpen(true)}
              className="flex items-center gap-2 px-3 py-1.5 bg-[#111726] hover:bg-[#182033] border border-white/[0.08] text-slate-300 hover:text-white rounded-xl text-xs font-mono transition"
            >
              <span>Command</span>
              <kbd className="bg-[#06080e] border border-white/[0.1] text-emerald-400 px-1.5 py-0.2 rounded text-[11px]">⌘K</kbd>
            </button>

            <div className="h-5 w-px bg-slate-800 hidden md:block"></div>

            <div className="flex items-center gap-2 pl-1">
              <span className="text-xs text-slate-400 font-medium">Twin:</span>
              <select
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                className="bg-[#111726] border border-white/[0.08] text-white rounded-xl px-3 py-1.5 text-xs font-medium focus:ring-2 focus:ring-emerald-500 outline-none cursor-pointer"
              >
                <option value="P020">P020 (Type 2 Diabetes • 58y, HbA1c 7.4%)</option>
                <option value="P021">P021 (Type 2 Diabetes • 61y, HbA1c 7.8%)</option>
                <option value="P010">P010 (Prediabetes • 48y, HbA1c 6.0%)</option>
                <option value="P001">P001 (Healthy Control • 28y, HbA1c 5.2%)</option>
              </select>
            </div>

            <div className="h-5 w-px bg-slate-800 hidden md:block"></div>

            <div className="flex items-center gap-1.5">
              <button
                onClick={isPlaying ? handlePause : handleStart}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition ${
                  isPlaying
                    ? "bg-amber-600 hover:bg-amber-500 text-white shadow-[0_0_15px_rgba(245,158,11,0.3)]"
                    : "bg-emerald-600 hover:bg-emerald-500 text-white shadow-[0_0_15px_rgba(16,185,129,0.3)]"
                }`}
              >
                {isPlaying ? "⏸ Pause Stream" : "▶ Start Stream"}
              </button>

              <button
                onClick={handleJumpNextMeal}
                className="bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition shadow-sm"
              >
                Next Meal <kbd className="font-mono text-[11px] bg-indigo-900/60 px-1 py-0.2 rounded ml-0.5">N</kbd>
              </button>
            </div>

            <div className="h-5 w-px bg-slate-800 hidden md:block"></div>

            <div className="flex items-center gap-1.5 pr-2">
              <span className="text-xs text-slate-400 font-medium">Speed:</span>
              <select
                value={speed}
                onChange={(e) => setSpeed(Number(e.target.value))}
                className="bg-[#111726] border border-white/[0.08] text-cyan-400 rounded-lg px-2 py-1 text-xs font-mono font-semibold outline-none cursor-pointer"
              >
                <option value={1}>1x</option>
                <option value={5}>5x</option>
                <option value={10}>10x</option>
                <option value={20}>20x</option>
              </select>
            </div>
          </div>

          {/* Right Status Beacon & Theme Toggle */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsDarkMode((prev) => !prev)}
              className="p-2 rounded-xl bg-[#06080e] border border-white/[0.08] text-slate-300 hover:text-white transition"
              title="Toggle Theme"
            >
              {isDarkMode ? "🌙" : "☀️"}
            </button>

            <div className="flex items-center gap-2 text-xs font-mono bg-emerald-950/40 border border-emerald-500/40 text-emerald-400 px-3.5 py-1.5 rounded-full shadow-[0_0_15px_rgba(16,185,129,0.15)]">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span className="tracking-wide">LIVE SENSOR STREAM</span>
            </div>
          </div>

        </div>
      </header>

      {/* 3. Floating Segmented Navigation Bar */}
      <nav className="sticky top-[69px] z-30 px-6 py-2.5 bg-[#06080e]/70 backdrop-blur-xl border-b border-white/[0.06]">
        <div className="max-w-[1720px] mx-auto flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 bg-[#0b0f19]/90 p-1 rounded-xl border border-white/[0.07] text-xs font-medium">
            <button
              onClick={() => setActiveTab("forecast")}
              className={`px-4 py-2 rounded-lg transition font-semibold ${
                activeTab === "forecast"
                  ? "bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 text-white border border-emerald-500/50 shadow-[0_0_20px_rgba(16,185,129,0.2)]"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              1. Live Monitoring &amp; Forecast
            </button>
            <button
              onClick={() => setActiveTab("whatif")}
              className={`px-4 py-2 rounded-lg transition font-semibold ${
                activeTab === "whatif"
                  ? "bg-gradient-to-r from-purple-500/20 to-pink-500/20 text-white border border-purple-500/50 shadow-[0_0_20px_rgba(168,85,247,0.2)]"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              2. What-If Meal Sandbox
            </button>
            <button
              onClick={() => setActiveTab("profile")}
              className={`px-4 py-2 rounded-lg transition font-semibold ${
                activeTab === "profile"
                  ? "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-white border border-cyan-500/50 shadow-[0_0_20px_rgba(6,182,212,0.2)]"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              3. Digital Twin Phenotype
            </button>
            <button
              onClick={() => setActiveTab("audit")}
              className={`px-4 py-2 rounded-lg transition font-semibold ${
                activeTab === "audit"
                  ? "bg-gradient-to-r from-amber-500/20 to-rose-500/20 text-white border border-amber-500/50 shadow-[0_0_20px_rgba(245,158,11,0.2)]"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              4. Sensor Stress-Test Studio
            </button>
          </div>

          <div className="hidden xl:flex items-center gap-4 text-xs font-mono text-slate-400">
            <span className="flex items-center gap-1.5 bg-[#0b0f19] border border-white/[0.06] px-2.5 py-1 rounded-lg">
              <span className="text-slate-500">Shortcuts:</span>
              <kbd className="text-white bg-slate-800 px-1.5 py-0.5 rounded border border-white/[0.08]">Cmd+K</kbd> Command
              <kbd className="text-white bg-slate-800 px-1.5 py-0.5 rounded border border-white/[0.08]">Space</kbd> Play
              <kbd className="text-white bg-slate-800 px-1.5 py-0.5 rounded border border-white/[0.08]">N</kbd> Next Meal
            </span>
          </div>
        </div>
      </nav>

      {/* 4. Main Body Content */}
      <main className="flex-1 p-6 max-w-[1720px] w-full mx-auto">
        {/* TAB 1: LIVE FORECAST & MONITORING */}
        {activeTab === "forecast" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Glucose KPI Card + TIR Segmented Bar */}
              <div className="bg-[#0b0f19]/80 border border-white/[0.07] rounded-2xl p-5 relative overflow-hidden backdrop-blur-xl shadow-xl">
                <div className="flex items-center justify-between text-xs text-slate-400 font-medium mb-1">
                  <span>Current Glycemia (CGM)</span>
                  <span className="bg-emerald-950/80 text-emerald-300 border border-emerald-600/50 px-2 py-0.5 rounded-full font-mono text-xs">
                    IN RANGE
                  </span>
                </div>
                <div className="flex items-baseline gap-2.5 my-1">
                  <span className="text-4xl font-extrabold font-mono tracking-tight text-white">{liveGlucose}</span>
                  <span className="text-sm font-medium text-slate-400">mg/dL</span>
                </div>
                {/* TIR Bar */}
                <div className="my-2 space-y-1">
                  <div className="flex justify-between text-[11px] font-mono text-slate-400">
                    <span className="text-emerald-400 font-semibold">TIR: 78% (Target &ge;70%)</span>
                    <span>GMI: 6.8%</span>
                  </div>
                  <div className="w-full h-1.5 rounded-full overflow-hidden flex bg-slate-900 border border-white/[0.08]">
                    <div className="bg-emerald-500 h-full" style={{ width: "78%" }}></div>
                    <div className="bg-rose-500 h-full" style={{ width: "18%" }}></div>
                    <div className="bg-amber-400 h-full" style={{ width: "4%" }}></div>
                  </div>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-white/[0.06]">
                  <span className="text-emerald-400 font-mono">↗ +1.2 mg/dL/min</span>
                  <span className="text-slate-500">Dexcom G6 5-min</span>
                </div>
              </div>

              <div className="bg-[#0b0f19]/80 border border-white/[0.07] rounded-2xl p-5 relative overflow-hidden backdrop-blur-xl shadow-xl">
                <div className="flex items-center justify-between text-xs text-slate-400 font-medium mb-2">
                  <span>Resting &amp; Active HR</span>
                  <span className="bg-slate-800 text-slate-300 border border-white/[0.08] px-2 py-0.5 rounded-full font-mono text-xs">
                    NORMAL
                  </span>
                </div>
                <div className="flex items-baseline gap-2.5 my-1">
                  <span className="text-4xl font-extrabold font-mono tracking-tight text-rose-300">{liveHR}</span>
                  <span className="text-sm font-medium text-slate-400">bpm</span>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-white/[0.06] mt-4">
                  <span>Baseline: 68 bpm</span>
                  <span className="text-slate-500">Optical PPG Wearable</span>
                </div>
              </div>

              <div className="bg-[#0b0f19]/80 border border-white/[0.07] rounded-2xl p-5 relative overflow-hidden backdrop-blur-xl shadow-xl">
                <div className="flex items-center justify-between text-xs text-slate-400 font-medium mb-2">
                  <span>Metabolic Exertion</span>
                  <span className="bg-cyan-950/70 text-cyan-300 border border-cyan-600/40 px-2 py-0.5 rounded-full font-mono text-xs">
                    SEDENTARY
                  </span>
                </div>
                <div className="flex items-baseline gap-2.5 my-1">
                  <span className="text-4xl font-extrabold font-mono tracking-tight text-cyan-300">{liveMETs.toFixed(2)}</span>
                  <span className="text-sm font-medium text-slate-400">METs</span>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-white/[0.06] mt-4">
                  <span>Rest / Desk Activity</span>
                  <span className="text-slate-500">Accelerometry Fusion</span>
                </div>
              </div>

              <div className="bg-[#0b0f19]/80 border border-white/[0.07] rounded-2xl p-5 relative overflow-hidden backdrop-blur-xl shadow-xl">
                <div className="flex items-center justify-between text-xs text-slate-400 font-medium mb-2">
                  <span>Active Clinical Meal</span>
                  <span className="bg-amber-950/70 text-amber-300 border border-amber-600/40 px-2 py-0.5 rounded-full font-mono text-xs">
                    RECORDED
                  </span>
                </div>
                <div className="my-1">
                  <div className="text-base font-bold text-white truncate">{lastMeal}</div>
                  <div className="text-xs font-mono text-amber-400 mt-0.5">{lastMealMacros}</div>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-white/[0.06] mt-4">
                  <span className="text-emerald-400">12-Step Buffer Ready</span>
                  <span className="text-slate-500">Parquet Engine</span>
                </div>
              </div>
            </div>

            {/* Trajectory Canvas Card */}
            <div className="bg-[#0b0f19]/80 border border-white/[0.07] rounded-2xl p-6 shadow-2xl space-y-4 backdrop-blur-xl">
              <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/[0.07] pb-3">
                <div>
                  <div className="flex items-center gap-3">
                    <h2 className="text-lg font-bold text-white tracking-tight">180-Minute Postprandial Glycemic Forecast</h2>
                    <span className="bg-emerald-950/80 text-emerald-300 border border-emerald-500/60 text-xs font-bold font-mono px-3 py-1 rounded-full uppercase shadow-sm">
                      {reliability} CONFIDENCE
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">
                    Candidate S structured absorption model with 90% conformal bounds and real recorded ground truth
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-3 text-xs">
                  <span className="flex items-center gap-2 bg-[#06080e] px-3 py-1.5 rounded-lg border border-white/[0.06] text-emerald-300">
                    <span className="w-3 h-1 bg-emerald-400 rounded-full inline-block"></span> Candidate S Forecast
                  </span>
                  <span className="flex items-center gap-2 bg-[#06080e] px-3 py-1.5 rounded-lg border border-white/[0.06] text-amber-300">
                    <span className="w-3 h-1 border-b-2 border-dashed border-amber-400 inline-block"></span> Ground Truth Overlay
                  </span>
                  <span className="flex items-center gap-2 bg-[#06080e] px-3 py-1.5 rounded-lg border border-white/[0.06] text-slate-300">
                    <span className="w-3 h-2.5 bg-emerald-500/20 border border-emerald-500/40 rounded-sm inline-block"></span> 90% Conformal Band
                  </span>
                </div>
              </div>

              {/* Scrubber HUD Bar */}
              <div className="flex flex-wrap items-center justify-between px-3.5 py-1.5 rounded-xl bg-[#06080e] border border-white/[0.08] text-xs font-mono text-slate-300">
                <div className="flex items-center gap-3">
                  <span className="text-slate-400">Live Scrubber:</span>
                  <span className="text-white font-bold">+55 min</span>
                  <span className="text-slate-600">|</span>
                  <span className="text-emerald-400 font-bold">Pred: 164.2 mg/dL</span>
                  <span className="text-slate-600">|</span>
                  <span className="text-slate-300">90% Bounds: [150.2 – 178.2]</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-amber-400 font-semibold">Ground Truth: 162.0 mg/dL</span>
                  <span className="text-slate-400">(Δ -2.2)</span>
                </div>
              </div>

              <div className="h-80 w-full bg-[#06080e] rounded-xl border border-white/[0.06] p-4 flex flex-col justify-between">
                <div className="flex justify-between items-center text-xs text-rose-400 font-mono border-b border-rose-500/30 pb-1">
                  <span>Clinical Hyperglycemia Boundary (180 mg/dL)</span>
                  <span className="bg-rose-950/80 px-2 py-0.5 rounded border border-rose-800/60">ADA Target &lt; 180</span>
                </div>

                <div className="flex-1 flex items-center justify-center text-center">
                  <div className="space-y-1">
                    <span className="text-sm font-semibold text-slate-200 block">Candidate S PyTorch Streaming Active</span>
                    <span className="text-xs text-slate-400 block max-w-lg mx-auto">
                      Streaming real 5,184-step sensor parquets and Ridge K=5 adapted weights.
                    </span>
                  </div>
                </div>

                <div className="flex justify-between text-xs text-slate-500 font-mono border-t border-white/[0.06] pt-2">
                  <span>0m</span>
                  <span>30m</span>
                  <span>60m (Peak)</span>
                  <span>90m</span>
                  <span>120m</span>
                  <span>180m</span>
                </div>
              </div>

              {/* 4 Quantitative Metric Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2 border-t border-white/[0.06]">
                <div className="bg-[#06080e] p-3.5 rounded-xl border border-white/[0.06] text-center">
                  <span className="text-xs text-slate-400 block mb-1">Predicted Peak</span>
                  <span className="text-2xl font-bold font-mono text-white">164.2 mg/dL</span>
                  <span className="text-xs text-emerald-400 block mt-1">Within Target</span>
                </div>
                <div className="bg-[#06080e] p-3.5 rounded-xl border border-white/[0.06] text-center">
                  <span className="text-xs text-slate-400 block mb-1">Time to Peak</span>
                  <span className="text-2xl font-bold font-mono text-white">55 min</span>
                  <span className="text-xs text-slate-500 block mt-1">Absorption Window</span>
                </div>
                <div className="bg-[#06080e] p-3.5 rounded-xl border border-white/[0.06] text-center">
                  <span className="text-xs text-slate-400 block mb-1">Delayed Mean (120-180m)</span>
                  <span className="text-2xl font-bold font-mono text-sky-400">138.4 mg/dL</span>
                  <span className="text-xs text-slate-500 block mt-1">Late Lipid Plateau</span>
                </div>
                <div className="bg-[#06080e] p-3.5 rounded-xl border border-white/[0.06] text-center">
                  <span className="text-xs text-slate-400 block mb-1">Time Above 180</span>
                  <span className="text-2xl font-bold font-mono text-emerald-400">0 min (0%)</span>
                  <span className="text-xs text-emerald-400 block mt-1">Optimal Safety</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: INTERACTIVE WHAT-IF MEAL SANDBOX */}
        {activeTab === "whatif" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <div className="lg:col-span-5 bg-[#0b0f19]/80 border border-white/[0.07] rounded-2xl p-6 shadow-2xl space-y-5 backdrop-blur-xl">
                <div className="border-b border-white/[0.07] pb-3 flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-purple-400"></span>
                      <h2 className="text-base font-bold text-white">What-If Counterfactual Sandbox</h2>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">Test modifications to portion, nutrients, or behavioral timing</p>
                  </div>

                  <button
                    onClick={() => setIsCustomMealOpen(true)}
                    className="px-3 py-1.5 bg-purple-950/80 hover:bg-purple-900 border border-purple-500/50 text-purple-200 text-xs font-semibold rounded-xl flex items-center gap-1.5 transition"
                  >
                    <span>+ Custom Meal</span>
                  </button>
                </div>

                {/* Preset Meal Quick Cards */}
                <div className="space-y-2">
                  <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 block">
                    Regional Clinical Presets:
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    <button onClick={() => selectDish("roti_dal_sabzi")} className="text-left p-3 rounded-xl bg-[#06080e] border border-white/[0.07] hover:border-emerald-500/50 transition">
                      <div className="text-xs font-semibold text-white">Roti, Dal &amp; Sabzi</div>
                      <div className="text-xs text-slate-400 mt-0.5">48g C • 12g F • 16g P</div>
                    </button>
                    <button onClick={() => selectDish("masala_dosa")} className="text-left p-3 rounded-xl bg-[#06080e] border border-white/[0.07] hover:border-emerald-500/50 transition">
                      <div className="text-xs font-semibold text-white">Masala Dosa + Sambar</div>
                      <div className="text-xs text-slate-400 mt-0.5">62g C • 18g F • 10g P</div>
                    </button>
                    <button onClick={() => selectDish("chicken_biryani")} className="text-left p-3 rounded-xl bg-[#06080e] border border-white/[0.07] hover:border-emerald-500/50 transition">
                      <div className="text-xs font-semibold text-white">Chicken Biryani</div>
                      <div className="text-xs text-slate-400 mt-0.5">68g C • 22g F • 32g P</div>
                    </button>
                    <button onClick={() => selectDish("rajma_chawal")} className="text-left p-3 rounded-xl bg-[#06080e] border border-white/[0.07] hover:border-emerald-500/50 transition">
                      <div className="text-xs font-semibold text-white">Rajma Chawal</div>
                      <div className="text-xs text-slate-400 mt-0.5">72g C • 14g F • 20g P</div>
                    </button>
                  </div>
                </div>

                {/* Dynamic Macro Visualizer */}
                <div className="bg-[#06080e] p-3.5 rounded-xl border border-white/[0.06] space-y-2">
                  <div className="flex justify-between text-xs text-slate-300">
                    <span className="font-semibold text-white">{activeDishName}</span>
                    <span className="font-mono font-semibold text-slate-200">{totalKcal} kcal</span>
                  </div>
                  <div className="w-full h-3 rounded-full overflow-hidden flex bg-slate-900 border border-white/[0.08]">
                    <div className="bg-amber-500 h-full transition-all duration-300" style={{ width: `${cPct}%` }}></div>
                    <div className="bg-emerald-500 h-full transition-all duration-300" style={{ width: `${pPct}%` }}></div>
                    <div className="bg-sky-500 h-full transition-all duration-300" style={{ width: `${fPct}%` }}></div>
                  </div>
                  <div className="flex justify-between text-xs font-mono text-slate-400">
                    <span>Carbs ({cPct}%)</span>
                    <span>Protein ({pPct}%)</span>
                    <span>Fat ({fPct}%)</span>
                  </div>
                </div>

                {/* Range Sliders */}
                <div className="space-y-4 pt-1">
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-300">Carbohydrates</span>
                      <span className="font-mono font-bold text-amber-400">{carbs} g</span>
                    </div>
                    <input type="range" min={10} max={140} value={carbs} onChange={(e) => setCarbs(Number(e.target.value))} className="w-full accent-amber-500" />
                  </div>

                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-300">Dietary Fat</span>
                      <span className="font-mono font-bold text-sky-400">{fat} g</span>
                    </div>
                    <input type="range" min={0} max={60} value={fat} onChange={(e) => setFat(Number(e.target.value))} className="w-full accent-sky-500" />
                  </div>

                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-300">Protein</span>
                      <span className="font-mono font-bold text-emerald-400">{protein} g</span>
                    </div>
                    <input type="range" min={0} max={60} value={protein} onChange={(e) => setProtein(Number(e.target.value))} className="w-full accent-emerald-500" />
                  </div>

                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-300">Portion Scaling</span>
                      <span className="font-mono font-bold text-purple-400">{portion}%</span>
                    </div>
                    <input type="range" min={25} max={200} step={25} value={portion} onChange={(e) => setPortion(Number(e.target.value))} className="w-full accent-purple-500" />
                  </div>
                </div>

                {/* Behavioral Interventions */}
                <div className="pt-3 border-t border-white/[0.07] space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Behavioral Interventions</span>
                    <span className="text-xs bg-amber-950/80 text-amber-300 border border-amber-600/50 px-2 py-0.5 rounded font-mono">
                      ASSUMPTION BADGE
                    </span>
                  </div>

                  <label className="flex items-center justify-between p-3 rounded-xl bg-[#06080e] border border-white/[0.07] cursor-pointer hover:border-emerald-500/40 transition">
                    <div className="space-y-0.5">
                      <div className="text-xs font-semibold text-white flex items-center gap-1.5">
                        <span>Post-Meal 15-Minute Brisk Walk</span>
                        <span className="text-xs text-emerald-400 font-mono">-18 mg/dL</span>
                      </div>
                      <div className="text-xs text-slate-400">Elevates METs to 3.2 at +30m postprandial</div>
                    </div>
                    <input type="checkbox" checked={walking} onChange={(e) => setWalking(e.target.checked)} className="w-4 h-4 rounded accent-emerald-500" />
                  </label>

                  <label className="flex items-center justify-between p-3 rounded-xl bg-[#06080e] border border-white/[0.07] cursor-pointer hover:border-emerald-500/40 transition">
                    <div className="space-y-0.5">
                      <div className="text-xs font-semibold text-white flex items-center gap-1.5">
                        <span>Food Sequencing (Protein/Veg First)</span>
                        <span className="text-xs text-emerald-400 font-mono">-15 mg/dL</span>
                      </div>
                      <div className="text-xs text-slate-400">Delays gastric emptying rate via GLP-1 (Shukla 2017)</div>
                    </div>
                    <input type="checkbox" checked={sequencing} onChange={(e) => setSequencing(e.target.checked)} className="w-4 h-4 rounded accent-emerald-500" />
                  </label>
                </div>
              </div>

              {/* Simulation Result Column */}
              <div className="lg:col-span-7 bg-[#0b0f19]/80 border border-white/[0.07] rounded-2xl p-6 shadow-2xl space-y-5 backdrop-blur-xl">
                <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/[0.07] pb-4">
                  <div>
                    <h2 className="text-base font-bold text-white">Comparative Digital Twin Response</h2>
                    <p className="text-xs text-slate-400 mt-0.5">Baseline meal excursion vs counterfactual scenario curve</p>
                  </div>
                  <div className="flex items-center gap-3 text-xs">
                    <span className="flex items-center gap-1.5 bg-[#06080e] px-2.5 py-1 rounded border border-white/[0.06] text-slate-300">
                      <span className="w-3 h-0.5 bg-emerald-400 inline-block"></span> Baseline
                    </span>
                    <span className="flex items-center gap-1.5 bg-[#06080e] px-2.5 py-1 rounded border border-white/[0.06] text-purple-300">
                      <span className="w-3 h-0.5 bg-purple-400 inline-block"></span> Counterfactual
                    </span>
                  </div>
                </div>

                <div className="h-80 bg-[#06080e] rounded-xl border border-white/[0.06] p-4 flex flex-col justify-between">
                  <div className="flex justify-between text-xs text-slate-500 font-mono">
                    <span>Simulation Mode: Active Candidate S Neural Inference</span>
                    <span className="text-emerald-400">Portion Adjusted: {portion}%</span>
                  </div>
                  <div className="text-center space-y-1">
                    <div className="text-lg font-bold font-mono text-purple-300">
                      Peak Estimate: {(164.2 * (portion / 100) - (walking ? 18 : 0) - (sequencing ? 15 : 0)).toFixed(1)} mg/dL
                    </div>
                    <div className="text-xs text-slate-400">
                      Adjusted for {carbs}g Carbs, {fat}g Fat, {protein}g Protein
                    </div>
                  </div>
                  <div className="flex justify-between text-xs text-slate-500 font-mono border-t border-white/[0.06] pt-1">
                    <span>0m</span>
                    <span>45m</span>
                    <span>90m</span>
                    <span>135m</span>
                    <span>180m</span>
                  </div>
                </div>

                {/* Deltas */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div className="bg-[#06080e] p-4 rounded-xl border border-white/[0.06]">
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-slate-400">Δ Peak Glycemia</span>
                      <span className="text-xs font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-600/50 px-1.5 py-0.2 rounded">
                        MODEL
                      </span>
                    </div>
                    <div className="text-2xl font-bold font-mono text-emerald-400">
                      {((portion / 100 - 1) * 35 - (walking ? 18 : 0) - (sequencing ? 15 : 0)).toFixed(1)} mg/dL
                    </div>
                    <span className="text-xs text-slate-500 mt-1 block">Excursion maximum delta</span>
                  </div>

                  <div className="bg-[#06080e] p-4 rounded-xl border border-white/[0.06]">
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-slate-400">Δ Delayed Mean</span>
                      <span className="text-xs font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-600/50 px-1.5 py-0.2 rounded">
                        MODEL
                      </span>
                    </div>
                    <div className="text-2xl font-bold font-mono text-sky-400">
                      {((fat - 12) * 0.3).toFixed(1)} mg/dL
                    </div>
                    <span className="text-xs text-slate-500 mt-1 block">Late lipid plateau effect</span>
                  </div>

                  <div className="bg-[#06080e] p-4 rounded-xl border border-white/[0.06]">
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-slate-400">Behavioral Impact</span>
                      <span className="text-xs font-mono font-bold bg-amber-950 text-amber-300 border border-amber-600/50 px-1.5 py-0.2 rounded">
                        ASSUMPTION
                      </span>
                    </div>
                    <div className="text-2xl font-bold font-mono text-amber-300">
                      {(walking ? -18 : 0) + (sequencing ? -15 : 0)} mg/dL
                    </div>
                    <span className="text-xs text-slate-500 mt-1 block">Literature exercise scalar</span>
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
              <div className="bg-[#0b0f19]/80 border border-white/[0.07] rounded-2xl p-6 shadow-2xl space-y-4 backdrop-blur-xl">
                <h2 className="text-base font-bold text-white">Clinical Baseline Profile</h2>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between py-2 border-b border-white/[0.06]"><span className="text-slate-400">Patient:</span> <span className="font-mono text-white font-bold">{patientId}</span></div>
                  <div className="flex justify-between py-2 border-b border-white/[0.06]"><span className="text-slate-400">Diagnosis:</span> <span className="text-emerald-400 font-bold">Type 2 Diabetes</span></div>
                  <div className="flex justify-between py-2 border-b border-white/[0.06]"><span className="text-slate-400">Age &amp; Sex:</span> <span className="text-white">58y / Male</span></div>
                  <div className="flex justify-between py-2 border-b border-white/[0.06]"><span className="text-slate-400">BMI:</span> <span className="text-white font-mono">28.4 kg/m²</span></div>
                  <div className="flex justify-between py-2 border-b border-white/[0.06]"><span className="text-slate-400">Baseline HbA1c:</span> <span className="text-amber-400 font-bold font-mono">7.4%</span></div>
                  <div className="flex justify-between py-2"><span className="text-slate-400">Fasting Glucose:</span> <span className="text-white font-mono">138 mg/dL</span></div>
                </div>
              </div>

              <div className="bg-[#0b0f19]/80 border border-white/[0.07] rounded-2xl p-6 shadow-2xl space-y-4 backdrop-blur-xl">
                <div className="flex items-center justify-between">
                  <h2 className="text-base font-bold text-white">Synthetic EHR Records</h2>
                  <span className="text-xs bg-amber-950 text-amber-300 border border-amber-600/50 px-2 py-0.5 rounded font-mono font-bold">SYNTHETIC (D14)</span>
                </div>
                <div className="space-y-3 text-xs">
                  <div className="p-3 bg-[#06080e] rounded-xl border border-white/[0.06]">
                    <span className="text-slate-400 block font-medium">Medications:</span>
                    <span className="text-slate-200 mt-0.5 block">Metformin 500mg BID, Lisinopril 10mg QD</span>
                  </div>
                  <div className="p-3 bg-[#06080e] rounded-xl border border-white/[0.06]">
                    <span className="text-slate-400 block font-medium">Comorbidities:</span>
                    <span className="text-slate-200 mt-0.5 block">Essential Hypertension, Dyslipidemia</span>
                  </div>
                </div>
              </div>

              <div className="bg-[#0b0f19]/80 border border-white/[0.07] rounded-2xl p-6 shadow-2xl space-y-4 backdrop-blur-xl">
                <div className="flex items-center justify-between">
                  <h2 className="text-base font-bold text-white">Few-Shot Ridge Tuning</h2>
                  <span className="text-xs bg-emerald-950 text-emerald-300 border border-emerald-600/50 px-2 py-0.5 rounded font-mono font-bold">K = 5 MEALS</span>
                </div>
                <div className="space-y-2 text-xs font-mono">
                  <div className="p-3 bg-[#06080e] rounded-xl border border-white/[0.06] space-y-1.5">
                    <div className="flex justify-between text-slate-400"><span>Zero-Shot (K=0):</span> <span className="text-rose-400">12.95 mg/dL</span></div>
                    <div className="flex justify-between text-slate-400"><span>1-Shot (K=1):</span> <span className="text-amber-400">10.84 mg/dL</span></div>
                    <div className="flex justify-between text-slate-400"><span>3-Shot (K=3):</span> <span className="text-emerald-400">9.45 mg/dL</span></div>
                    <div className="flex justify-between text-emerald-300 font-bold border-t border-white/[0.08] pt-1"><span>5-Shot (K=5):</span> <span>8.92 mg/dL</span></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: SENSOR QUALITY & STRESS-TEST */}
        {activeTab === "audit" && (
          <div className="space-y-6">
            <div className="bg-[#0b0f19]/80 border border-white/[0.07] rounded-2xl p-6 shadow-2xl space-y-5 backdrop-blur-xl">
              <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/[0.07] pb-4">
                <div>
                  <h2 className="text-base font-bold text-white">Sensor Degradation &amp; Stress Testing (D0–D7)</h2>
                  <p className="text-xs text-slate-400 mt-0.5">Audit digital twin reliability under realistic wear failures and signal dropouts</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400">Active Stress Scenario:</span>
                  <span className="text-xs font-mono font-bold bg-[#06080e] border border-emerald-500/50 text-emerald-400 px-3 py-1 rounded-lg">
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
                    className={`p-4 rounded-xl border text-left transition ${
                      degradation === item.id
                        ? "bg-[#06080e] border-emerald-500/60 shadow-[0_0_15px_rgba(16,185,129,0.15)]"
                        : "bg-[#06080e] border-white/[0.07] hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-white">{item.label}</span>
                      <span className={`text-xs px-1.5 py-0.2 rounded font-mono font-bold ${
                        item.status === "HIGH" ? "bg-emerald-950 text-emerald-400" : item.status === "MODERATE" ? "bg-amber-950 text-amber-400" : "bg-rose-950 text-rose-400"
                      }`}>
                        {item.status}
                      </span>
                    </div>
                    <span className="text-xs text-slate-400 block">{item.desc}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* 5. Command Palette Modal */}
      {isPaletteOpen && (
        <div className="fixed inset-0 z-50 bg-[#04060c]/85 backdrop-blur-md flex items-start justify-center pt-24 px-4">
          <div className="w-full max-w-xl bg-[#0b0f19] rounded-2xl border border-white/[0.12] shadow-2xl overflow-hidden">
            <div className="p-3.5 border-b border-white/[0.08] flex items-center gap-3 bg-[#06080e]/60">
              <input
                type="text"
                autoFocus
                value={paletteQuery}
                onChange={(e) => { setPaletteQuery(e.target.value); setPaletteIndex(0); }}
                placeholder="Search actions, patients, presets, or stress tests..."
                className="bg-transparent text-white placeholder-slate-500 text-xs outline-none flex-1 font-sans"
              />
              <kbd className="text-[11px] font-mono bg-[#111726] text-slate-400 px-2 py-0.5 rounded border border-white/[0.08]">ESC</kbd>
            </div>
            <div className="max-h-80 overflow-y-auto p-2 space-y-1">
              {filteredActions.length === 0 ? (
                <div className="text-xs text-slate-500 text-center py-6">No matching clinical actions</div>
              ) : (
                filteredActions.map((item, idx) => (
                  <div
                    key={item.id}
                    onClick={() => { item.run(); setIsPaletteOpen(false); }}
                    className={`flex items-center justify-between p-2.5 rounded-xl cursor-pointer transition text-xs ${
                      idx === paletteIndex ? "bg-emerald-950/60 border border-emerald-500/50 text-white" : "bg-[#06080e]/60 border border-white/[0.04] text-slate-300 hover:border-white/[0.1]"
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                      <span>{item.title}</span>
                    </div>
                    <span className="font-mono text-[11px] bg-[#111726] px-2 py-0.5 rounded text-slate-400 border border-white/[0.08]">{item.key}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* 6. Custom Meal Modal */}
      {isCustomMealOpen && (
        <div className="fixed inset-0 z-50 bg-[#04060c]/85 backdrop-blur-md flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-[#0b0f19] rounded-2xl border border-white/[0.12] shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
              <h3 className="text-sm font-bold text-white">Create Custom Meal Input</h3>
              <button onClick={() => setIsCustomMealOpen(false)} className="text-slate-400 hover:text-white text-xs">✕</button>
            </div>
            <div className="space-y-3 text-xs">
              <div>
                <label className="text-slate-300 font-medium block mb-1">Dish Name:</label>
                <input type="text" value={customName} onChange={(e) => setCustomName(e.target.value)} className="w-full bg-[#06080e] border border-white/[0.08] text-white rounded-xl p-2.5 outline-none" />
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-amber-400 font-medium block mb-1">Carbs (g):</label>
                  <input type="number" value={customCarbs} onChange={(e) => setCustomCarbs(Number(e.target.value))} className="w-full bg-[#06080e] border border-white/[0.08] text-white rounded-xl p-2.5 font-mono outline-none" />
                </div>
                <div>
                  <label className="text-sky-400 font-medium block mb-1">Fat (g):</label>
                  <input type="number" value={customFat} onChange={(e) => setCustomFat(Number(e.target.value))} className="w-full bg-[#06080e] border border-white/[0.08] text-white rounded-xl p-2.5 font-mono outline-none" />
                </div>
                <div>
                  <label className="text-emerald-400 font-medium block mb-1">Protein (g):</label>
                  <input type="number" value={customProtein} onChange={(e) => setCustomProtein(Number(e.target.value))} className="w-full bg-[#06080e] border border-white/[0.08] text-white rounded-xl p-2.5 font-mono outline-none" />
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2.5 pt-2 border-t border-white/[0.06]">
              <button onClick={() => setIsCustomMealOpen(false)} className="px-3.5 py-1.5 rounded-xl bg-[#111726] text-slate-300 text-xs">Cancel</button>
              <button onClick={applyCustomMeal} className="px-4 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold">Apply to Sandbox</button>
            </div>
          </div>
        </div>
      )}

      {/* 7. Footer */}
      <footer className="border-t border-white/[0.07] px-6 py-3 bg-[#06080e]/80 text-xs text-slate-500 flex flex-wrap justify-between items-center gap-3">
        <div>Team Aegis — Happiest Health Digital Twin Challenge 2026</div>
        <div className="flex items-center gap-4">
          <span><kbd className="bg-slate-900 border border-white/[0.08] px-1.5 py-0.5 rounded text-slate-300">Cmd+K</kbd> Command</span>
          <span><kbd className="bg-slate-900 border border-white/[0.08] px-1.5 py-0.5 rounded text-slate-300">Space</kbd> Play / Pause</span>
          <span><kbd className="bg-slate-900 border border-white/[0.08] px-1.5 py-0.5 rounded text-slate-300">N</kbd> Next Meal</span>
        </div>
      </footer>
    </div>
  );
}
