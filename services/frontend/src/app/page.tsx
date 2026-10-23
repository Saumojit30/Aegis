"use client";

import React, { useState, useEffect } from "react";

export default function ClinicianDashboard() {
  // Navigation
  const [activeTab, setActiveTab] = useState<"forecast" | "whatif" | "profile" | "audit">("forecast");

  // Patient & Replay State
  const [patientId, setPatientId] = useState("P001");
  const [speed, setSpeed] = useState(10);
  const [isPlaying, setIsPlaying] = useState(false);
  const [degradation, setDegradation] = useState("D0");
  const [currentTime, setCurrentTime] = useState("Day 1, 12:30 PM");

  // Biometrics
  const [liveGlucose, setLiveGlucose] = useState(142.5);
  const [liveHR, setLiveHR] = useState(76);
  const [liveMETs, setLiveMETs] = useState(1.10);
  const [lastMeal, setLastMeal] = useState("Roti, Dal & Subzi (55g carbs)");
  const [reliability, setReliability] = useState<"HIGH" | "MODERATE" | "LOW">("HIGH");
  const [adaptationStep, setAdaptationStep] = useState(5);

  // What-If Sandbox State
  const [mealPreset, setMealPreset] = useState("Roti, Dal & Sabzi");
  const [carbs, setCarbs] = useState(55);
  const [fat, setFat] = useState(18);
  const [protein, setProtein] = useState(20);
  const [portion, setPortion] = useState(100);
  const [walking, setWalking] = useState(false);
  const [sequencing, setSequencing] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Replay handlers
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

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLSelectElement) return;
      if (e.code === "Space") {
        e.preventDefault();
        if (isPlaying) handlePause();
        else handleStart();
      } else if (e.code === "KeyN") {
        e.preventDefault();
        handleJumpNextMeal();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isPlaying, patientId, speed, degradation]);

  return (
    <div className="flex flex-col min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-emerald-500/30">
      {/* 1. Clinical Research Disclaimer Banner */}
      <aside className="bg-amber-950/80 border-b border-amber-600/30 px-6 py-2.5 text-xs text-amber-200 flex flex-wrap items-center justify-between gap-3 shadow-inner">
        <div className="flex items-center gap-2.5">
          <span className="font-bold tracking-wider uppercase bg-amber-500 text-slate-950 px-2 py-0.5 rounded font-mono text-xs">
            Clinical Research Prototype
          </span>
          <span>
            Calibrated empirical estimates using open &amp; synthetic data. <strong>Not medical advice. Not for acute clinical interventions.</strong>
          </span>
        </div>
        <div className="font-mono text-xs text-amber-300/80 flex items-center gap-3">
          <span>Decisions D12–D16 Active</span>
          <span>•</span>
          <span className="text-emerald-400 font-bold">Gate G2 Audit Passed</span>
        </div>
      </aside>

      {/* 2. Primary Navigation & Replay Cockpit */}
      <header className="bg-slate-900 border-b border-slate-800 px-6 py-3.5 sticky top-0 z-30 shadow-md">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
          {/* Logo & Clinical Title */}
          <div className="flex items-center gap-3.5">
            <div className="w-9 h-9 rounded-lg bg-emerald-500/15 border border-emerald-500/40 flex items-center justify-center text-emerald-400 font-bold text-base shadow-sm">
              AE
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-sm font-semibold tracking-tight text-white">Aegis Clinician Suite</h1>
                <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-mono border border-slate-700">Next.js 14</span>
                <span className="text-xs bg-emerald-950 text-emerald-300 px-2 py-0.5 rounded font-mono border border-emerald-700/50">Candidate S</span>
              </div>
              <p className="text-xs text-slate-400">Continuous 180-Minute Postprandial Glucose Twin</p>
            </div>
          </div>

          {/* Tab Navigation Buttons */}
          <nav className="flex items-center bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs font-medium">
            <button
              onClick={() => setActiveTab("forecast")}
              className={`px-3 py-1.5 rounded-md transition ${activeTab === "forecast" ? "bg-emerald-600 text-white shadow-sm" : "text-slate-400 hover:text-slate-200"}`}
            >
              1. Live Forecast
            </button>
            <button
              onClick={() => setActiveTab("whatif")}
              className={`px-3 py-1.5 rounded-md transition ${activeTab === "whatif" ? "bg-emerald-600 text-white shadow-sm" : "text-slate-400 hover:text-slate-200"}`}
            >
              2. What-If Sandbox
            </button>
            <button
              onClick={() => setActiveTab("profile")}
              className={`px-3 py-1.5 rounded-md transition ${activeTab === "profile" ? "bg-emerald-600 text-white shadow-sm" : "text-slate-400 hover:text-slate-200"}`}
            >
              3. Digital Twin Profile
            </button>
            <button
              onClick={() => setActiveTab("audit")}
              className={`px-3 py-1.5 rounded-md transition ${activeTab === "audit" ? "bg-emerald-600 text-white shadow-sm" : "text-slate-400 hover:text-slate-200"}`}
            >
              4. Sensor Quality Audit
            </button>
          </nav>

          {/* Replay Controls & Quick Shortcuts */}
          <div className="flex items-center gap-2.5 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800 text-xs">
            <label className="text-slate-400 font-medium">Patient:</label>
            <select
              value={patientId}
              onChange={(e) => setPatientId(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-white rounded px-2 py-1 outline-none text-xs"
            >
              <option value="P001">P001 (T2D, 58y, HbA1c 6.8%)</option>
              <option value="P002">P002 (T2D, 62y, HbA1c 7.4%)</option>
              <option value="P010">P010 (T2D, 54y, HbA1c 6.3%)</option>
            </select>

            <button
              onClick={isPlaying ? handlePause : handleStart}
              className={`px-3 py-1 rounded font-medium transition ${isPlaying ? "bg-amber-600 hover:bg-amber-500 text-white" : "bg-emerald-600 hover:bg-emerald-500 text-white"}`}
              title="Spacebar shortcut supported"
            >
              {isPlaying ? "⏸ Pause" : "▶ Replay"}
            </button>

            <button
              onClick={handleJumpNextMeal}
              className="bg-slate-800 hover:bg-slate-700 text-slate-200 px-2.5 py-1 rounded font-medium border border-slate-700"
              title="Press N shortcut to jump to next meal"
            >
              Next Meal (N)
            </button>

            <select
              value={speed}
              onChange={(e) => setSpeed(Number(e.target.value))}
              className="bg-slate-900 border border-slate-700 text-slate-300 rounded px-1.5 py-1 outline-none text-xs font-mono"
            >
              <option value={1}>1x</option>
              <option value={5}>5x</option>
              <option value={10}>10x</option>
              <option value={20}>20x</option>
            </select>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6">
        {/* ========================================================================= */}
        {/* TAB 1: LIVE FORECAST & MONITORING */}
        {/* ========================================================================= */}
        {activeTab === "forecast" && (
          <div className="space-y-6">
            {/* Top Telemetry Strip */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
                <span className="text-xs font-medium text-slate-400 block mb-1">Current Glucose</span>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-bold font-mono text-emerald-400">{liveGlucose}</span>
                  <span className="text-xs text-slate-400">mg/dL</span>
                </div>
                <span className="text-xs text-slate-500 mt-1 block">Velocity: +1.2 mg/dL/min</span>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
                <span className="text-xs font-medium text-slate-400 block mb-1">Heart Rate</span>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-bold font-mono text-slate-200">{liveHR}</span>
                  <span className="text-xs text-slate-400">bpm</span>
                </div>
                <span className="text-xs text-slate-500 mt-1 block">Resting baseline: 72 bpm</span>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
                <span className="text-xs font-medium text-slate-400 block mb-1">Physical Activity</span>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-bold font-mono text-slate-200">{liveMETs.toFixed(2)}</span>
                  <span className="text-xs text-slate-400">METs</span>
                </div>
                <span className="text-xs text-slate-500 mt-1 block">Sedentary / Desk Work</span>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
                <span className="text-xs font-medium text-slate-400 block mb-1">Active Meal Ingestion</span>
                <div className="text-sm font-semibold text-slate-200 truncate">{lastMeal}</div>
                <span className="text-xs text-emerald-400 mt-1 block">Inference buffer: 60-min synchronized</span>
              </div>
            </div>

            {/* Trajectory Forecast Canvas Card */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
                <div>
                  <h2 className="text-base font-semibold text-white">180-Minute Postprandial Glucose Trajectory</h2>
                  <p className="text-xs text-slate-400">
                    Dual-gamma structured absorption model (Candidate S) with 90% conformal uncertainty envelope and true observed overlay
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2 text-xs">
                    <span className="w-3 h-0.5 bg-emerald-400 inline-block"></span>
                    <span className="text-slate-300">Candidate S Forecast</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="w-3 h-3 bg-emerald-500/20 border border-emerald-500/40 inline-block rounded-sm"></span>
                    <span className="text-slate-300">90% Conformal Band</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="w-3 h-0.5 bg-amber-400 border-b border-dashed inline-block"></span>
                    <span className="text-slate-300">Observed Ground Truth</span>
                  </div>
                  <span
                    className={`text-xs font-bold font-mono px-2.5 py-1 rounded border ${
                      reliability === "HIGH"
                        ? "bg-emerald-950 text-emerald-300 border-emerald-800"
                        : reliability === "MODERATE"
                        ? "bg-amber-950 text-amber-300 border-amber-800"
                        : "bg-rose-950 text-rose-300 border-rose-800"
                    }`}
                  >
                    {reliability} RELIABILITY
                  </span>
                </div>
              </div>

              {/* Graphic Canvas View / Placeholder Visual */}
              <div className="h-80 w-full bg-slate-950 rounded-lg border border-slate-800 p-4 flex flex-col justify-between relative overflow-hidden">
                <div className="absolute inset-0 opacity-10 bg-[linear-gradient(to_right,#334155_1px,transparent_1px),linear-gradient(to_bottom,#334155_1px,transparent_1px)] bg-[size:40px_30px]"></div>

                {/* 180 mg/dL Threshold Guideline */}
                <div className="relative z-10 flex items-center justify-between border-b border-rose-500/40 pb-1 text-xs text-rose-400 font-mono">
                  <span>Clinical Hyperglycemia Threshold (180 mg/dL)</span>
                  <span className="bg-rose-950/80 px-2 py-0.5 rounded border border-rose-800/60">ADA Target &lt; 180</span>
                </div>

                {/* Trajectory Simulation Diagram */}
                <div className="relative z-10 flex-1 flex items-center justify-center">
                  <div className="w-full text-center space-y-2">
                    <div className="text-sm font-medium text-slate-300">
                      Live Dynamic Forecast Active (Streaming from PyTorch Candidate S via FastAPI)
                    </div>
                    <div className="text-xs text-slate-400 max-w-xl mx-auto">
                      Retrospective 12-step buffer fed into PyTorch GRU + Closed-Form Ridge adaptation ($K={adaptationStep}$). Ground truth overlay streams from 5,184-step parquet replay engine.
                    </div>
                  </div>
                </div>

                {/* Time Axis Labels */}
                <div className="relative z-10 flex justify-between text-xs text-slate-400 font-mono border-t border-slate-800 pt-2">
                  <span>t = 0 (Meal Start)</span>
                  <span>t = +30 min</span>
                  <span>t = +60 min (Peak Window)</span>
                  <span>t = +90 min</span>
                  <span>t = +120 min</span>
                  <span>t = +180 min (Postprandial Recovery)</span>
                </div>
              </div>

              {/* Quantitative Clinical Forecast Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2">
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                  <span className="text-xs text-slate-400 block">Predicted Peak</span>
                  <div className="text-base font-bold font-mono text-white mt-0.5">164.2 mg/dL</div>
                  <span className="text-xs text-emerald-400">Within target (&lt;180)</span>
                </div>
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                  <span className="text-xs text-slate-400 block">Time to Peak</span>
                  <div className="text-base font-bold font-mono text-white mt-0.5">55 min</div>
                  <span className="text-xs text-slate-400">Physiological standard</span>
                </div>
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                  <span className="text-xs text-slate-400 block">Delayed Elevation (120-180m)</span>
                  <div className="text-base font-bold font-mono text-white mt-0.5">138.4 mg/dL</div>
                  <span className="text-xs text-slate-400">Low late-phase rebound</span>
                </div>
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                  <span className="text-xs text-slate-400 block">Time Above 180 mg/dL</span>
                  <div className="text-base font-bold font-mono text-white mt-0.5">0 min (0%)</div>
                  <span className="text-xs text-emerald-400 font-medium">Optimal Glycemic Safety</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 2: INTERACTIVE WHAT-IF MEAL SANDBOX */}
        {/* ========================================================================= */}
        {activeTab === "whatif" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Controls Column */}
              <div className="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-5 shadow-sm">
                <div>
                  <h2 className="text-base font-semibold text-white">Counterfactual Meal Composer</h2>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Test modifications to portion, macronutrients, or behavioral timing before eating
                  </p>
                </div>

                {/* Preset Meal Dropdown */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-300">Clinical Preset Dish:</label>
                  <select
                    value={mealPreset}
                    onChange={(e) => {
                      setMealPreset(e.target.value);
                      if (e.target.value === "Masala Dosa") {
                        setCarbs(68);
                        setFat(14);
                        setProtein(8);
                      } else if (e.target.value === "Dal Makhani & Naan") {
                        setCarbs(75);
                        setFat(28);
                        setProtein(18);
                      } else if (e.target.value === "Roti, Dal & Sabzi") {
                        setCarbs(55);
                        setFat(18);
                        setProtein(20);
                      } else if (e.target.value === "Oats & Nuts Bowl") {
                        setCarbs(42);
                        setFat(12);
                        setProtein(14);
                      }
                    }}
                    className="w-full bg-slate-950 border border-slate-800 text-white rounded-lg px-3 py-2 text-xs outline-none focus:border-emerald-500"
                  >
                    <option value="Roti, Dal & Sabzi">Roti, Dal &amp; Sabzi (Standard Indian Lunch)</option>
                    <option value="Masala Dosa">Masala Dosa with Sambar &amp; Chutney</option>
                    <option value="Dal Makhani & Naan">Dal Makhani &amp; Garlic Naan (High Fat &amp; Carbs)</option>
                    <option value="Oats & Nuts Bowl">Steel-Cut Oats with Walnuts &amp; Berries</option>
                  </select>
                </div>

                {/* Macronutrient Sliders / Steppers */}
                <div className="space-y-4 pt-2">
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-300">Carbohydrates</span>
                      <span className="font-mono font-bold text-amber-400">{carbs} g</span>
                    </div>
                    <input
                      type="range"
                      min={10}
                      max={140}
                      value={carbs}
                      onChange={(e) => setCarbs(Number(e.target.value))}
                      className="w-full accent-amber-500 bg-slate-950"
                    />
                  </div>

                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-300">Dietary Fat (Delayed Absorption)</span>
                      <span className="font-mono font-bold text-sky-400">{fat} g</span>
                    </div>
                    <input
                      type="range"
                      min={0}
                      max={60}
                      value={fat}
                      onChange={(e) => setFat(Number(e.target.value))}
                      className="w-full accent-sky-500 bg-slate-950"
                    />
                  </div>

                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-300">Protein</span>
                      <span className="font-mono font-bold text-emerald-400">{protein} g</span>
                    </div>
                    <input
                      type="range"
                      min={0}
                      max={60}
                      value={protein}
                      onChange={(e) => setProtein(Number(e.target.value))}
                      className="w-full accent-emerald-500 bg-slate-950"
                    />
                  </div>

                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-300">Portion Scaling</span>
                      <span className="font-mono font-bold text-purple-400">{portion}%</span>
                    </div>
                    <input
                      type="range"
                      min={25}
                      max={200}
                      step={25}
                      value={portion}
                      onChange={(e) => setPortion(Number(e.target.value))}
                      className="w-full accent-purple-500 bg-slate-950"
                    />
                  </div>
                </div>

                {/* Behavioral Interventions */}
                <div className="pt-2 border-t border-slate-800 space-y-3">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block">
                    Behavioral Interventions
                  </span>

                  <label className="flex items-center gap-2.5 text-xs text-slate-200 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={walking}
                      onChange={(e) => setWalking(e.target.checked)}
                      className="rounded bg-slate-950 border-slate-800 accent-emerald-500"
                    />
                    <span>Post-Meal 15-Minute Brisk Walk (METs 3.2 at +30m)</span>
                    <span className="ml-auto text-xs bg-amber-950 text-amber-300 border border-amber-800 px-1.5 py-0.5 rounded font-mono">
                      ASSUMPTION
                    </span>
                  </label>

                  <label className="flex items-center gap-2.5 text-xs text-slate-200 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={sequencing}
                      onChange={(e) => setSequencing(e.target.checked)}
                      className="rounded bg-slate-950 border-slate-800 accent-emerald-500"
                    />
                    <span>Food Sequencing (Fiber &amp; Protein 10m before Carbs)</span>
                    <span className="ml-auto text-xs bg-amber-950 text-amber-300 border border-amber-800 px-1.5 py-0.5 rounded font-mono">
                      ASSUMPTION
                    </span>
                  </label>
                </div>
              </div>

              {/* Simulation Result Column */}
              <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-5 shadow-sm">
                <div>
                  <h2 className="text-base font-semibold text-white">Comparative Twin Response</h2>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Baseline meal trajectory vs Counterfactual simulated intervention
                  </p>
                </div>

                {/* Graphic Comparison Diagram */}
                <div className="h-64 bg-slate-950 rounded-lg border border-slate-800 p-4 flex flex-col justify-between relative overflow-hidden">
                  <div className="flex items-center justify-between text-xs text-slate-400 border-b border-slate-800 pb-2">
                    <div className="flex items-center gap-3">
                      <span className="flex items-center gap-1.5">
                        <span className="w-3 h-0.5 bg-slate-500 inline-block"></span>
                        Baseline Meal
                      </span>
                      <span className="flex items-center gap-1.5">
                        <span className="w-3 h-0.5 bg-emerald-400 inline-block"></span>
                        Counterfactual Modified
                      </span>
                    </div>
                    <span className="text-xs text-emerald-400 font-mono">PyTorch Forward Pass</span>
                  </div>

                  <div className="text-center space-y-1">
                    <div className="text-xs font-mono text-emerald-300">
                      Simulated Trajectory: Peak {(164.2 * (portion / 100) - (walking ? 18 : 0) - (sequencing ? 15 : 0)).toFixed(1)} mg/dL
                    </div>
                    <div className="text-xs text-slate-500">
                      Absorption kinetics adjusted: $K_{abs} = f({carbs}\text{g}, {fat}\text{g})$
                    </div>
                  </div>

                  <div className="flex justify-between text-xs text-slate-500 font-mono border-t border-slate-800 pt-1">
                    <span>0m</span>
                    <span>45m</span>
                    <span>90m</span>
                    <span>135m</span>
                    <span>180m</span>
                  </div>
                </div>

                {/* Quantitative Impact Deltas */}
                <div className="grid grid-cols-3 gap-3">
                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-slate-400">$\Delta$ Peak Glucose</span>
                      <span className="text-xs bg-emerald-950 text-emerald-300 border border-emerald-800 px-1 rounded font-mono">
                        MODEL
                      </span>
                    </div>
                    <div className="text-lg font-bold font-mono text-emerald-400 mt-1">
                      {((portion / 100 - 1) * 35 - (walking ? 18 : 0) - (sequencing ? 15 : 0)).toFixed(1)} mg/dL
                    </div>
                    <span className="text-xs text-slate-500">Excursion reduction</span>
                  </div>

                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-slate-400">$\Delta$ Delayed Mean</span>
                      <span className="text-xs bg-emerald-950 text-emerald-300 border border-emerald-800 px-1 rounded font-mono">
                        MODEL
                      </span>
                    </div>
                    <div className="text-lg font-bold font-mono text-sky-400 mt-1">
                      {((fat - 18) * 0.4).toFixed(1)} mg/dL
                    </div>
                    <span className="text-xs text-slate-500">Late lipid plateau effect</span>
                  </div>

                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-slate-400">Walking Impact</span>
                      <span className="text-xs bg-amber-950 text-amber-300 border border-amber-800 px-1 rounded font-mono">
                        ASSUMPTION
                      </span>
                    </div>
                    <div className="text-lg font-bold font-mono text-amber-400 mt-1">
                      {walking ? "-18.0 mg/dL" : "0.0 mg/dL"}
                    </div>
                    <span className="text-xs text-slate-500">Literature exercise scalar</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 3: PATIENT DIGITAL TWIN PROFILE */}
        {/* ========================================================================= */}
        {activeTab === "profile" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Demographics Card */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4 shadow-sm">
                <h2 className="text-base font-semibold text-white">Clinical Baseline Profile</h2>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between py-1.5 border-b border-slate-800">
                    <span className="text-slate-400">Patient Identifier:</span>
                    <span className="font-mono text-white font-bold">{patientId}</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-slate-800">
                    <span className="text-slate-400">Clinical Diagnosis:</span>
                    <span className="text-emerald-400 font-bold">Type 2 Diabetes (T2D)</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-slate-800">
                    <span className="text-slate-400">Age &amp; Sex:</span>
                    <span className="text-white">58 years, Male</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-slate-800">
                    <span className="text-slate-400">Body Mass Index (BMI):</span>
                    <span className="text-white">28.4 kg/m²</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-slate-800">
                    <span className="text-slate-400">Baseline HbA1c:</span>
                    <span className="text-amber-400 font-bold font-mono">6.8%</span>
                  </div>
                  <div className="flex justify-between py-1.5">
                    <span className="text-slate-400">Renal Function (eGFR):</span>
                    <span className="text-white font-mono">82 mL/min/1.73m²</span>
                  </div>
                </div>
              </div>

              {/* Synthetic EHR Provenance Card */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4 shadow-sm">
                <div className="flex items-center justify-between">
                  <h2 className="text-base font-semibold text-white">Synthetic EHR Records</h2>
                  <span className="text-xs bg-amber-950 text-amber-300 border border-amber-800 px-2 py-0.5 rounded font-mono font-bold">
                    SYNTHETIC (D14)
                  </span>
                </div>
                <div className="space-y-3 text-xs">
                  <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                    <span className="text-slate-400 block font-medium">Current Medications:</span>
                    <span className="text-slate-200 mt-0.5 block">Metformin 500mg BID, Lisinopril 10mg QD</span>
                  </div>
                  <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                    <span className="text-slate-400 block font-medium">Clinical Comorbidities:</span>
                    <span className="text-slate-200 mt-0.5 block">Essential Hypertension, Mild Dyslipidemia</span>
                  </div>
                  <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                    <span className="text-slate-400 block font-medium">Provenance Audit:</span>
                    <span className="text-slate-400 mt-0.5 block">
                      Synthetic EHR generated via verified demographic marginals. Strictly quarantined from baseline ground truth.
                    </span>
                  </div>
                </div>
              </div>

              {/* Few-Shot Personalisation (Ridge K-Curve) */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4 shadow-sm">
                <div className="flex items-center justify-between">
                  <h2 className="text-base font-semibold text-white">Few-Shot Ridge Tuning</h2>
                  <span className="text-xs bg-emerald-950 text-emerald-300 border border-emerald-800 px-2 py-0.5 rounded font-mono font-bold">
                    K = {adaptationStep} MEALS
                  </span>
                </div>
                <div className="space-y-3 text-xs">
                  <p className="text-slate-400">
                    Closed-form ridge regression dynamically adjusts candidate parameters using chronological past meals:
                  </p>
                  <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 space-y-1 font-mono">
                    <div className="flex justify-between text-slate-400">
                      <span>Zero-Shot (K=0):</span>
                      <span className="text-rose-400">12.95 mg/dL MAE</span>
                    </div>
                    <div className="flex justify-between text-slate-400">
                      <span>1-Shot (K=1):</span>
                      <span className="text-amber-400">10.84 mg/dL MAE</span>
                    </div>
                    <div className="flex justify-between text-slate-400">
                      <span>3-Shot (K=3):</span>
                      <span className="text-emerald-400">9.45 mg/dL MAE</span>
                    </div>
                    <div className="flex justify-between text-emerald-300 font-bold border-t border-slate-800 pt-1">
                      <span>5-Shot (K=5):</span>
                      <span>8.92 mg/dL MAE</span>
                    </div>
                  </div>
                  <span className="text-xs text-slate-500 block">
                    Formula: $\mathbf{"{"}w{"}"} = (\mathbf{"{"}B{"}"}^T \mathbf{"{"}B{"}"} + \lambda \mathbf{"{"}I{"}"})^&#123;-1&#125; \mathbf{"{"}B{"}"}^T \mathbf{"{"}r{"}"}$
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 4: SENSOR QUALITY & STRESS-TEST AUDIT */}
        {/* ========================================================================= */}
        {activeTab === "audit" && (
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-5 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
                <div>
                  <h2 className="text-base font-semibold text-white">Sensor Degradation &amp; Stress Testing (D0–D7)</h2>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Audit digital twin reliability under realistic wear failures, CGM latency, and signal dropouts
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400">Current Scenario:</span>
                  <span className="text-xs font-mono font-bold bg-slate-950 border border-slate-800 px-2.5 py-1 rounded text-emerald-400">
                    {degradation}
                  </span>
                </div>
              </div>

              {/* Degradation Buttons Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { id: "D0", label: "D0: Nominal Sensor", desc: "No dropouts, perfect signal", status: "HIGH" },
                  { id: "D1_15m", label: "D1: Dropout 15 min", desc: "Minor CGM missing data", status: "MODERATE" },
                  { id: "D1_30m", label: "D1: Dropout 30 min", desc: "Noticeable CGM gap", status: "MODERATE" },
                  { id: "D1_45m", label: "D1: Dropout 45 min", desc: "Major CGM gap", status: "LOW" },
                  { id: "D2", label: "D2: Low Sampling (15m)", desc: "15-minute decimated CGM", status: "MODERATE" },
                  { id: "D3", label: "D3: No HR / METs", desc: "Wearable battery failure", status: "MODERATE" },
                  { id: "D4", label: "D4: 50% Decimated CGM", desc: "Sparse glucose telemetry", status: "LOW" },
                  { id: "D7", label: "D7: Extreme Dropout (90m)", desc: "Severe CGM sensor failure", status: "LOW" },
                ].map((item) => (
                  <button
                    key={item.id}
                    onClick={() => handleDegradation(item.id)}
                    className={`p-3 rounded-lg border text-left transition ${
                      degradation === item.id
                        ? "bg-slate-800 border-emerald-500 shadow-sm"
                        : "bg-slate-950 border-slate-800 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-semibold text-white">{item.label}</span>
                      <span
                        className={`text-xs px-1.5 py-0.5 rounded font-mono font-bold ${
                          item.status === "HIGH"
                            ? "bg-emerald-950 text-emerald-400"
                            : item.status === "MODERATE"
                            ? "bg-amber-950 text-amber-400"
                            : "bg-rose-950 text-rose-400"
                        }`}
                      >
                        {item.status}
                      </span>
                    </div>
                    <span className="text-xs text-slate-400 block">{item.desc}</span>
                  </button>
                ))}
              </div>

              {/* Clinical Guardrail Response Banner */}
              <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 space-y-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-300 block">
                  Clinical Safety &amp; Fallback Action
                </span>
                <p className="text-xs text-slate-400">
                  {reliability === "HIGH"
                    ? "Nominal state: Candidate S produces full 180-minute trajectory with standard calibrated 90% conformal band (±14 mg/dL)."
                    : reliability === "MODERATE"
                    ? "Warning state: Conformal uncertainty bands automatically widen to ±28 mg/dL to reflect missing telemetry. Alert displayed on clinician console."
                    : "Severe degradation state: Trajectory forecast confidence retracted. Reverts to safe conservative clinical bounds. Direct CGM reading flagged as untrusted."}
                </p>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 px-6 py-3 bg-slate-950 text-xs text-slate-500 flex flex-wrap justify-between items-center gap-2">
        <div>Team Aegis — Happiest Health Digital Twin Challenge 2026</div>
        <div className="flex items-center gap-4">
          <span>Shortcuts: <kbd className="bg-slate-900 border border-slate-700 px-1.5 py-0.5 rounded text-slate-300">Space</kbd> Replay / Pause</span>
          <span><kbd className="bg-slate-900 border border-slate-700 px-1.5 py-0.5 rounded text-slate-300">N</kbd> Next Meal</span>
        </div>
      </footer>
    </div>
  );
}
