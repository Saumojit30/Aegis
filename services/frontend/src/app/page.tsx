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
  const [activeTab, setActiveTab] = useState<"forecast" | "whatif" | "timeline" | "profile" | "audit" | "settings">("forecast");

  // Theme State (Dark / Light)
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  // Patient Twin & Replay Cockpit State
  const [patientId, setPatientId] = useState("P020");
  const [speed, setSpeed] = useState(10);
  const [isPlaying, setIsPlaying] = useState(false);
  const [degradation, setDegradation] = useState("D0");
  const [reliability, setReliability] = useState<"HIGH" | "MODERATE" | "LOW">("HIGH");

  // Command Palette State
  const [isPaletteOpen, setIsPaletteOpen] = useState(false);
  const [paletteQuery, setPaletteQuery] = useState("");
  const [paletteIndex, setPaletteIndex] = useState(0);

  // Custom Meal Modal State
  const [isCustomMealOpen, setIsCustomMealOpen] = useState(false);
  const [customName, setCustomName] = useState("Paneer Butter Masala with Roti");
  const [customCarbs, setCustomCarbs] = useState(52);
  const [customFat, setCustomFat] = useState(24);
  const [customProtein, setCustomProtein] = useState(18);

  // Doctronic AI Doctor Persona State
  const [doctorResponseStyle, setDoctorResponseStyle] = useState("Just the facts");
  const [isStylePopoverOpen, setIsStylePopoverOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Biometrics Telemetry
  const liveGlucose = 136.6;
  const liveHR = 71;
  const liveMETs = 1.0;
  const lastMeal = "Roti, Dal & Sabzi";
  const lastMealMacros = "48g Carbs • 12g Fat";

  // What-If Sandbox State
  const [activeDishName, setActiveDishName] = useState("Roti, Dal & Sabzi");
  const [carbs, setCarbs] = useState(48);
  const [fat, setFat] = useState(12);
  const [protein, setProtein] = useState(16);
  const [portion, setPortion] = useState(100);
  const [walking, setWalking] = useState(false);
  const [sequencing, setSequencing] = useState(false);

  // Patient Twin Phenotypes
  const patientData: Record<string, { age: string; bmi: string; hba1c: string; fasting: string; diagnosis: string; meds: string; comorbidities: string }> = {
    P020: { age: "58y / Male", bmi: "28.4 kg/m²", hba1c: "7.4%", fasting: "138 mg/dL", diagnosis: "Type 2 Diabetes", meds: "Metformin 500mg BID, Lisinopril 10mg QD", comorbidities: "Essential Hypertension, Dyslipidemia" },
    P021: { age: "61y / Female", bmi: "30.1 kg/m²", hba1c: "7.8%", fasting: "146 mg/dL", diagnosis: "Type 2 Diabetes", meds: "Metformin 1000mg BID, Empagliflozin 10mg QD", comorbidities: "Microalbuminuria" },
    P010: { age: "48y / Male", bmi: "26.8 kg/m²", hba1c: "6.0%", fasting: "112 mg/dL", diagnosis: "Prediabetes", meds: "Lifestyle modification, Metformin 250mg QD", comorbidities: "None recorded" },
    P001: { age: "28y / Female", bmi: "21.5 kg/m²", hba1c: "5.2%", fasting: "88 mg/dL", diagnosis: "Healthy Control", meds: "None", comorbidities: "None" }
  };

  const currentPatient = patientData[patientId] || patientData.P020;

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

  const triggerToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  // Preset Selection
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
    triggerToast(`Loaded meal preset: ${activeDishName}`);
  };

  const applyCustomMeal = () => {
    setActiveDishName(customName);
    setCarbs(customCarbs);
    setFat(customFat);
    setProtein(customProtein);
    setIsCustomMealOpen(false);
    setActiveTab("whatif");
    triggerToast(`Applied custom meal: ${customName}`);
  };

  const handleDegradation = (deg: string) => {
    setDegradation(deg);
    if (deg === "D4" || deg === "D7") setReliability("LOW");
    else if (deg.startsWith("D1") || deg === "D3" || deg === "D2") setReliability("MODERATE");
    else setReliability("HIGH");
    triggerToast(`Stress test injected: ${deg}`);
  };

  // Command Palette Actions
  const actions: CommandAction[] = useMemo(() => [
    { id: "play", title: "Replay: Toggle Play / Pause Stream", cat: "Replay", key: "Space", run: () => setIsPlaying((p) => !p) },
    { id: "jump", title: "Replay: Jump to Next Clinical Meal", cat: "Replay", key: "N", run: () => triggerToast("Jumping to next clinical postprandial meal (+180m)") },
    { id: "p020", title: "Twin: Switch to P020 (Type 2 Diabetes, 58y)", cat: "Twin", key: "P20", run: () => { setPatientId("P020"); triggerToast("Switched active twin to P020"); } },
    { id: "p021", title: "Twin: Switch to P021 (Type 2 Diabetes, 61y)", cat: "Twin", key: "P21", run: () => { setPatientId("P021"); triggerToast("Switched active twin to P021"); } },
    { id: "p010", title: "Twin: Switch to P010 (Prediabetes, 48y)", cat: "Twin", key: "P10", run: () => { setPatientId("P010"); triggerToast("Switched active twin to P010"); } },
    { id: "p001", title: "Twin: Switch to P001 (Healthy Control, 28y)", cat: "Twin", key: "P01", run: () => { setPatientId("P001"); triggerToast("Switched active twin to P001"); } },
    { id: "preset_roti", title: "What-If: Roti, Dal & Sabzi", cat: "What-If", key: "R", run: () => { setActiveTab("whatif"); selectDish("roti_dal_sabzi"); } },
    { id: "preset_dosa", title: "What-If: Masala Dosa + Sambar", cat: "What-If", key: "D", run: () => { setActiveTab("whatif"); selectDish("masala_dosa"); } },
    { id: "preset_biryani", title: "What-If: Chicken Biryani", cat: "What-If", key: "B", run: () => { setActiveTab("whatif"); selectDish("chicken_biryani"); } },
    { id: "custom_modal", title: "What-If: Open Custom Meal Builder Modal", cat: "What-If", key: "+", run: () => setIsCustomMealOpen(true) },
    { id: "theme_light", title: "Theme: Switch to Light Theme", cat: "Theme", key: "L", run: () => handleSetTheme("light") },
    { id: "theme_dark", title: "Theme: Switch to Dark Theme", cat: "Theme", key: "D", run: () => handleSetTheme("dark") },
    { id: "deg_d0", title: "Stress: Nominal 5-Min Telemetry (D0)", cat: "Stress", key: "D0", run: () => handleDegradation("D0") },
    { id: "deg_d1", title: "Stress: 30m Signal Dropout (D1)", cat: "Stress", key: "D1", run: () => handleDegradation("D1_30m") },
    { id: "deg_d3", title: "Stress: No Wearable HR/METs (D3)", cat: "Stress", key: "D3", run: () => handleDegradation("D3") },
    { id: "tab_1", title: "View: 1. Overview & Forecast", cat: "View", key: "1", run: () => setActiveTab("forecast") },
    { id: "tab_2", title: "View: 2. What-If Meal Sandbox", cat: "View", key: "2", run: () => setActiveTab("whatif") },
    { id: "tab_3", title: "View: 3. Meal Timeline (Refero)", cat: "View", key: "3", run: () => setActiveTab("timeline") },
    { id: "tab_4", title: "View: 4. Digital Twin Phenotype", cat: "View", key: "4", run: () => setActiveTab("profile") },
    { id: "tab_5", title: "View: 5. Sensor Stress Audit", cat: "View", key: "5", run: () => setActiveTab("audit") },
    { id: "tab_6", title: "View: 6. Doctor AI Persona (Doctronic)", cat: "View", key: "6", run: () => setActiveTab("settings") },
  ], [isPlaying, patientId]);

  const filteredActions = useMemo(() => {
    return actions.filter((a) =>
      a.title.toLowerCase().includes(paletteQuery.toLowerCase()) ||
      a.cat.toLowerCase().includes(paletteQuery.toLowerCase())
    );
  }, [actions, paletteQuery]);

  // Keyboard Shortcuts (Cmd+K, Space, N, 1-6)
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
          setIsStylePopoverOpen(false);
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
        setIsPlaying((prev) => !prev);
      } else if (e.code === "KeyN") {
        e.preventDefault();
        triggerToast("Jumping to next clinical postprandial meal (+180m)");
      } else if (e.key === "1") setActiveTab("forecast");
      else if (e.key === "2") setActiveTab("whatif");
      else if (e.key === "3") setActiveTab("timeline");
      else if (e.key === "4") setActiveTab("profile");
      else if (e.key === "5") setActiveTab("audit");
      else if (e.key === "6") setActiveTab("settings");
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isPlaying, isPaletteOpen, filteredActions, paletteIndex]);

  return (
    <div className="min-h-screen flex overflow-x-hidden font-sans bg-[var(--bg-canvas)] text-[var(--text-main)] transition-colors duration-200">
      
      {/* 1. LEFT MICRO-RAIL (OpenRouter & Doctronic Style, 56px) */}
      <aside aria-label="Micro-Rail" className="w-14 flex-shrink-0 flex flex-col items-center justify-between py-3.5 border-r border-[var(--border-main)] bg-[var(--bg-micro)] z-50">
        <div className="flex flex-col items-center gap-4">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-purple-700 to-indigo-600 flex items-center justify-center text-white font-bold text-sm shadow-sm cursor-pointer" title="Aegis Twin Suite">
            AE
          </div>

          <div className="w-7 h-px bg-[var(--border-main)] my-1"></div>

          <button onClick={() => setActiveTab("forecast")} className={`p-2 rounded-lg transition ${activeTab === "forecast" ? "text-purple-600 bg-[var(--bg-card)] shadow-sm" : "text-[var(--text-secondary)] hover:text-[var(--text-main)]"}`} title="Activity & Trajectory Forecast">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/></svg>
          </button>

          <button onClick={() => setActiveTab("whatif")} className={`p-2 rounded-lg transition ${activeTab === "whatif" ? "text-purple-600 bg-[var(--bg-card)] shadow-sm" : "text-[var(--text-secondary)] hover:text-[var(--text-main)]"}`} title="What-If Counterfactual Sandbox">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/></svg>
          </button>

          <button onClick={() => setActiveTab("timeline")} className={`p-2 rounded-lg transition ${activeTab === "timeline" ? "text-purple-600 bg-[var(--bg-card)] shadow-sm" : "text-[var(--text-secondary)] hover:text-[var(--text-main)]"}`} title="Chronological Meal Timeline (Refero)">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
          </button>

          <button onClick={() => setActiveTab("profile")} className={`p-2 rounded-lg transition ${activeTab === "profile" ? "text-purple-600 bg-[var(--bg-card)] shadow-sm" : "text-[var(--text-secondary)] hover:text-[var(--text-main)]"}`} title="Patient Digital Twin Phenotype">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>
          </button>

          <button onClick={() => setActiveTab("audit")} className={`p-2 rounded-lg transition ${activeTab === "audit" ? "text-purple-600 bg-[var(--bg-card)] shadow-sm" : "text-[var(--text-secondary)] hover:text-[var(--text-main)]"}`} title="Sensor Stress-Test Studio">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
          </button>

          <button onClick={() => setActiveTab("settings")} className={`p-2 rounded-lg transition ${activeTab === "settings" ? "text-purple-600 bg-[var(--bg-card)] shadow-sm" : "text-[var(--text-secondary)] hover:text-[var(--text-main)]"}`} title="AI Doctor Persona & Settings (Doctronic)">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          </button>
        </div>

        <div className="flex flex-col items-center gap-3">
          <button onClick={() => setIsPaletteOpen(true)} className="p-2 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-main)] transition" title="Search Actions (⌘K)">
            <kbd className="font-mono text-[10px] bg-[var(--bg-card)] border border-[var(--border-main)] px-1 py-0.5 rounded">⌘K</kbd>
          </button>
          <div className="w-8 h-8 rounded-full bg-slate-300 dark:bg-slate-700 border border-[var(--border-main)] flex items-center justify-center text-xs font-semibold text-[var(--text-main)]" title="Dr. Connie (Lead Endocrinologist)">
            DC
          </div>
        </div>
      </aside>

      {/* 2. EXPANDED SIDEBAR NAVIGATION (OpenRouter Style, 240px) */}
      <aside aria-label="Sidebar" className="w-60 flex-shrink-0 flex flex-col border-r border-[var(--border-main)] bg-[var(--bg-sidebar)] z-40">
        
        {/* Workspace / Twin Selector */}
        <div className="p-3.5 border-b border-[var(--border-main)]">
          <div className="flex items-center justify-between text-xs font-medium text-[var(--text-secondary)] mb-1.5">
            <div className="flex items-center gap-1.5">
              <span className="w-4 h-4 rounded-full bg-purple-600 text-white flex items-center justify-center text-[10px] font-bold">P</span>
              <span>Twin Workspace</span>
            </div>
            <span className="text-[10px] text-[var(--text-muted)] font-mono">v2026.4</span>
          </div>
          <select
            value={patientId}
            onChange={(e) => { setPatientId(e.target.value); triggerToast(`Switched active twin to ${e.target.value}`); }}
            className="w-full bg-[var(--bg-card-subtle)] border border-[var(--border-main)] text-[var(--text-main)] rounded-lg px-2.5 py-1.5 text-xs font-semibold outline-none focus:border-purple-500 cursor-pointer"
          >
            <option value="P020">P020 — T2D (58y, HbA1c 7.4%)</option>
            <option value="P021">P021 — T2D (61y, HbA1c 7.8%)</option>
            <option value="P010">P010 — Prediabetes (48y, 6.0%)</option>
            <option value="P001">P001 — Healthy Control (28y)</option>
          </select>
        </div>

        {/* Search Bar */}
        <div className="px-3 py-2.5 border-b border-[var(--border-main)]">
          <div onClick={() => setIsPaletteOpen(true)} className="flex items-center justify-between px-2.5 py-1.5 rounded-lg border border-[var(--border-main)] bg-[var(--bg-card-subtle)] text-[var(--text-secondary)] hover:text-[var(--text-main)] text-xs cursor-pointer">
            <div className="flex items-center gap-2">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
              <span>Search telemetry...</span>
            </div>
            <kbd className="font-mono text-[10px] bg-[var(--bg-card)] px-1 rounded border border-[var(--border-main)]">⌘K</kbd>
          </div>
        </div>

        {/* Sidebar Nav Items */}
        <nav className="flex-1 overflow-y-auto px-2.5 py-3 space-y-4 text-xs font-medium">
          
          <div>
            <div className="px-2 py-1 text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
              Clinical Monitoring
            </div>
            <div className="mt-1 space-y-0.5">
              <button
                onClick={() => setActiveTab("forecast")}
                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-left transition ${
                  activeTab === "forecast" ? "bg-[var(--nav-active-bg)] text-[var(--nav-active-text)] font-semibold" : "text-[var(--text-secondary)] hover:text-[var(--text-main)] hover:bg-[var(--bg-card-subtle)]"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/></svg>
                  <span>Activity &amp; Forecast</span>
                </div>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              </button>

              <button
                onClick={() => setActiveTab("timeline")}
                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-left transition ${
                  activeTab === "timeline" ? "bg-[var(--nav-active-bg)] text-[var(--nav-active-text)] font-semibold" : "text-[var(--text-secondary)] hover:text-[var(--text-main)] hover:bg-[var(--bg-card-subtle)]"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
                  <span>Meal Timeline</span>
                </div>
                <span className="text-[10px] text-[var(--text-muted)] font-mono">Refero</span>
              </button>

              <button
                onClick={() => setActiveTab("profile")}
                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-left transition ${
                  activeTab === "profile" ? "bg-[var(--nav-active-bg)] text-[var(--nav-active-text)] font-semibold" : "text-[var(--text-secondary)] hover:text-[var(--text-main)] hover:bg-[var(--bg-card-subtle)]"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>
                  <span>Twin Phenotype</span>
                </div>
                <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-mono">K=5</span>
              </button>
            </div>
          </div>

          <div>
            <div className="px-2 py-1 text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
              Counterfactual Lab
            </div>
            <div className="mt-1 space-y-0.5">
              <button
                onClick={() => setActiveTab("whatif")}
                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-left transition ${
                  activeTab === "whatif" ? "bg-[var(--nav-active-bg)] text-[var(--nav-active-text)] font-semibold" : "text-[var(--text-secondary)] hover:text-[var(--text-main)] hover:bg-[var(--bg-card-subtle)]"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/></svg>
                  <span>What-If Sandbox</span>
                </div>
                <span className="text-[10px] bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20 px-1 rounded">Sim</span>
              </button>

              <button
                onClick={() => setIsCustomMealOpen(true)}
                className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-left transition text-[var(--text-secondary)] hover:text-[var(--text-main)] hover:bg-[var(--bg-card-subtle)]"
              >
                <div className="flex items-center gap-2.5">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"/></svg>
                  <span>Add Custom Meal</span>
                </div>
                <kbd className="font-mono text-[10px] text-[var(--text-muted)]">+</kbd>
              </button>
            </div>
          </div>

          <div>
            <div className="px-2 py-1 text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
              Audit &amp; Intelligence
            </div>
            <div className="mt-1 space-y-0.5">
              <button
                onClick={() => setActiveTab("audit")}
                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-left transition ${
                  activeTab === "audit" ? "bg-[var(--nav-active-bg)] text-[var(--nav-active-text)] font-semibold" : "text-[var(--text-secondary)] hover:text-[var(--text-main)] hover:bg-[var(--bg-card-subtle)]"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
                  <span>Sensor Quality D0–D7</span>
                </div>
                <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-mono">High</span>
              </button>

              <button
                onClick={() => setActiveTab("settings")}
                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-left transition ${
                  activeTab === "settings" ? "bg-[var(--nav-active-bg)] text-[var(--nav-active-text)] font-semibold" : "text-[var(--text-secondary)] hover:text-[var(--text-main)] hover:bg-[var(--bg-card-subtle)]"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                  <span>AI Doctor Persona</span>
                </div>
                <span className="text-[10px] bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 px-1 rounded">Doctronic</span>
              </button>
            </div>
          </div>

        </nav>

        <div className="p-3 border-t border-[var(--border-main)] flex items-center justify-between text-[11px] text-[var(--text-muted)]">
          <span>Candidate S Model</span>
          <span className="font-mono text-emerald-600 dark:text-emerald-400 font-medium">Split-Conformal 90%</span>
        </div>

      </aside>

      {/* 3. MAIN WORKSPACE CANVAS */}
      <div className="flex-1 flex flex-col min-w-0 min-h-screen">
        
        {/* Top Header Bar */}
        <header className="sticky top-0 z-30 bg-[var(--bg-card)] border-b border-[var(--border-main)] px-6 py-2.5 transition-colors duration-200">
          <div className="max-w-[1600px] mx-auto flex flex-wrap items-center justify-between gap-4">
            
            <div className="flex items-center gap-2 text-xs">
              <span className="text-[var(--text-secondary)]">Aegis Twin Suite</span>
              <span className="text-[var(--border-subtle)]">/</span>
              <span className="font-semibold text-[var(--text-main)]">
                {activeTab === "forecast" ? "Activity & Trajectory Forecast" :
                 activeTab === "whatif" ? "Counterfactual Meal Sandbox" :
                 activeTab === "timeline" ? "Chronological Meal Timeline" :
                 activeTab === "profile" ? "Patient Digital Twin Phenotype" :
                 activeTab === "audit" ? "Sensor Quality & Stress Testing" :
                 "Doctor AI Persona & Settings"}
              </span>
              <span className="text-[11px] px-2 py-0.2 rounded font-mono font-medium bg-[var(--bg-card-subtle)] text-[var(--text-secondary)] border border-[var(--border-main)]">
                Candidate S
              </span>
            </div>

            <div className="flex items-center gap-3 text-xs">
              
              {/* Replay Playback Transport */}
              <div className="flex items-center gap-1.5 p-1 rounded-lg border border-[var(--border-main)] bg-[var(--bg-card-subtle)]">
                <button
                  onClick={() => { setIsPlaying((p) => !p); triggerToast(!isPlaying ? "Telemetry stream playback active" : "Telemetry playback paused"); }}
                  className="px-2.5 py-1 rounded-md bg-[var(--bg-card)] text-[var(--text-main)] font-semibold shadow-sm flex items-center gap-1.5 transition"
                >
                  <span>{isPlaying ? "⏸" : "▶"}</span>
                  <span>{isPlaying ? "Pause" : "Play"}</span>
                  <kbd className="font-mono text-[10px] text-[var(--text-muted)]">Space</kbd>
                </button>
                <button
                  onClick={() => triggerToast("Jumping to next clinical postprandial meal (+180m)")}
                  className="px-2.5 py-1 rounded-md hover:bg-[var(--bg-card)] text-[var(--text-secondary)] hover:text-[var(--text-main)] flex items-center gap-1 transition"
                >
                  <span>Next Meal</span>
                  <kbd className="font-mono text-[10px] text-[var(--text-muted)]">N</kbd>
                </button>
                <div className="h-3.5 w-px bg-[var(--border-main)]"></div>
                <select
                  value={speed}
                  onChange={(e) => { setSpeed(Number(e.target.value)); triggerToast(`Replay speed set to ${e.target.value}x`); }}
                  className="bg-transparent text-[var(--text-main)] font-mono font-medium text-xs outline-none cursor-pointer"
                >
                  <option value={1}>1x</option>
                  <option value={5}>5x</option>
                  <option value={10}>10x</option>
                  <option value={20}>20x</option>
                </select>
              </div>

              {/* Dark & Light Segmented Switch */}
              <div className="flex items-center p-0.5 rounded-lg border border-[var(--border-main)] bg-[var(--bg-canvas)]">
                <button
                  onClick={() => handleSetTheme("light")}
                  className={`px-2.5 py-1 rounded-md text-xs font-medium flex items-center gap-1.5 transition ${
                    theme === "light" ? "bg-[var(--bg-card)] text-[var(--text-main)] shadow-sm font-semibold" : "text-[var(--text-secondary)] hover:text-[var(--text-main)]"
                  }`}
                  title="Switch to Light mode"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>
                  <span>Light</span>
                </button>
                <button
                  onClick={() => handleSetTheme("dark")}
                  className={`px-2.5 py-1 rounded-md text-xs font-medium flex items-center gap-1.5 transition ${
                    theme === "dark" ? "bg-[var(--bg-card)] text-[var(--text-main)] shadow-sm font-semibold" : "text-[var(--text-secondary)] hover:text-[var(--text-main)]"
                  }`}
                  title="Switch to Dark mode"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>
                  <span>Dark</span>
                </button>
              </div>

            </div>

          </div>
        </header>

        {/* Floating Doctronic Toast Notification */}
        {toastMessage && (
          <div className="fixed top-14 right-8 z-50 transition-all duration-300">
            <div className="flex items-center gap-2.5 px-4 py-2.5 rounded-full shadow-lg border border-blue-200 dark:border-blue-900 bg-blue-50 dark:bg-blue-950/90 text-blue-800 dark:text-blue-200 text-xs font-medium">
              <svg className="w-4 h-4 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
              <span>{toastMessage}</span>
            </div>
          </div>
        )}

        {/* Main Body */}
        <main className="flex-1 p-6 max-w-[1600px] w-full mx-auto space-y-6">
          
          {/* OpenRouter Dismissible Clinical Banner */}
          <section className="p-4 rounded-xl border border-blue-500/20 bg-blue-500/5 dark:bg-blue-950/20 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-blue-600/10 border border-blue-500/30 flex items-center justify-center text-blue-600 dark:text-blue-400 font-bold text-xs">
                G2
              </div>
              <div>
                <div className="text-xs font-semibold text-[var(--text-main)]">
                  Candidate S Digital Twin Research Prototype (Dual-Gamma Absorption)
                </div>
                <div className="text-[11px] text-[var(--text-secondary)]">
                  Calibrated with 90% Split-Conformal intervals and Ridge K=5 personalization. <strong>Not medical advice and not suitable for treatment decisions.</strong>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={() => setActiveTab("audit")} className="px-3 py-1 rounded-lg bg-[var(--bg-card)] border border-[var(--border-main)] text-xs font-medium text-[var(--text-main)] hover:border-[var(--border-subtle)] transition">
                View Conformal Audit
              </button>
            </div>
          </section>

          {/* OpenRouter Page Title & Underline Tabs */}
          <div className="border-b border-[var(--border-main)] pb-0">
            <div className="flex flex-wrap items-end justify-between gap-4 mb-4">
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-[var(--text-main)]">
                  {activeTab === "forecast" ? "Activity" :
                   activeTab === "whatif" ? "What-If Simulation" :
                   activeTab === "timeline" ? "Meal Excursions Timeline" :
                   activeTab === "profile" ? "Patient Profile" :
                   activeTab === "audit" ? "Resilience Audit" :
                   "AI Doctor Persona"}
                </h1>
                <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                  {activeTab === "forecast" ? "Continuous 180-min postprandial glycemic digital twin telemetry across patient models" :
                   activeTab === "whatif" ? "Test nutritional substitutions, portion scaling, and behavioral exercise timing" :
                   activeTab === "timeline" ? "Historical postprandial sessions with macronutrient ratios and glycemic envelopes" :
                   activeTab === "profile" ? "Clinical baseline, synthetic EHR comorbidities, and few-shot Ridge K=5 adapted weights" :
                   activeTab === "audit" ? "Validate digital twin fidelity across realistic packet dropouts (D0–D7)" :
                   "Customize clinical communication tone, telemetry memory, and physician consent preferences"}
                </p>
              </div>
              
              <div className="flex items-center gap-2 text-xs">
                <span className="px-2.5 py-1 rounded-md border border-[var(--border-main)] bg-[var(--bg-card)] text-[var(--text-secondary)] font-mono">
                  🌐 GMT+5:30
                </span>
                <span className="px-2.5 py-1 rounded-md border border-[var(--border-main)] bg-[var(--bg-card)] text-[var(--text-main)] font-medium">
                  Past 180-Min Excursion ▾
                </span>
              </div>
            </div>

            <div className="flex items-center gap-8 text-xs">
              <button onClick={() => setActiveTab("forecast")} className={`tab-underline ${activeTab === "forecast" ? "active" : ""}`}>
                Overview &amp; Forecast
              </button>
              <button onClick={() => setActiveTab("whatif")} className={`tab-underline ${activeTab === "whatif" ? "active" : ""}`}>
                What-If Sandbox
              </button>
              <button onClick={() => setActiveTab("timeline")} className={`tab-underline ${activeTab === "timeline" ? "active" : ""}`}>
                Meal Timeline (Refero)
              </button>
              <button onClick={() => setActiveTab("profile")} className={`tab-underline ${activeTab === "profile" ? "active" : ""}`}>
                Patient Phenotype
              </button>
              <button onClick={() => setActiveTab("audit")} className={`tab-underline ${activeTab === "audit" ? "active" : ""}`}>
                Sensor Stress Audit
              </button>
              <button onClick={() => setActiveTab("settings")} className={`tab-underline ${activeTab === "settings" ? "active" : ""}`}>
                Doctor AI Persona (Doctronic)
              </button>
            </div>
          </div>

          {/* TAB 1: OVERVIEW & FORECAST */}
          {activeTab === "forecast" && (
            <div className="space-y-6">
              
              {/* 5-Column Bento KPI Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
                <div className="clean-card p-4 space-y-2">
                  <div className="flex items-center justify-between text-xs text-[var(--text-secondary)]">
                    <span>Current CGM</span>
                    <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">IN RANGE</span>
                  </div>
                  <div className="flex items-baseline justify-between">
                    <div>
                      <span className="text-2xl font-bold font-mono tracking-tight text-[var(--text-main)]">{liveGlucose}</span>
                      <span className="text-xs text-[var(--text-secondary)] ml-1">mg/dL</span>
                    </div>
                    <svg className="w-16 h-6 text-emerald-500" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 64 24"><path strokeLinecap="round" strokeLinejoin="round" d="M2 18 L16 14 L30 16 L44 8 L62 4" /></svg>
                  </div>
                  <div className="text-[11px] text-[var(--text-muted)] font-mono flex items-center justify-between pt-1 border-t border-[var(--border-main)]">
                    <span className="text-emerald-600 dark:text-emerald-400">↗ +1.2 mg/dL/min</span>
                    <span>Dexcom G6</span>
                  </div>
                </div>

                <div className="clean-card p-4 space-y-2">
                  <div className="flex items-center justify-between text-xs text-[var(--text-secondary)]">
                    <span>Resting HR</span>
                    <span className="px-1.5 py-0.2 rounded text-[10px] font-mono text-[var(--text-secondary)] bg-[var(--bg-card-subtle)]">NORMAL</span>
                  </div>
                  <div className="flex items-baseline justify-between">
                    <div>
                      <span className="text-2xl font-bold font-mono tracking-tight text-[var(--text-main)]">{liveHR}</span>
                      <span className="text-xs text-[var(--text-secondary)] ml-1">bpm</span>
                    </div>
                    <svg className="w-16 h-6 text-rose-500" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 64 24"><path strokeLinecap="round" strokeLinejoin="round" d="M2 12 L16 12 L22 4 L28 20 L34 8 L40 12 L62 12" /></svg>
                  </div>
                  <div className="text-[11px] text-[var(--text-muted)] flex items-center justify-between pt-1 border-t border-[var(--border-main)]">
                    <span>Baseline: 68 bpm</span>
                    <span>Optical PPG</span>
                  </div>
                </div>

                <div className="clean-card p-4 space-y-2">
                  <div className="flex items-center justify-between text-xs text-[var(--text-secondary)]">
                    <span>Physical Activity</span>
                    <span className="px-1.5 py-0.2 rounded text-[10px] font-mono text-[var(--text-secondary)] bg-[var(--bg-card-subtle)]">SEDENTARY</span>
                  </div>
                  <div className="flex items-baseline justify-between">
                    <div>
                      <span className="text-2xl font-bold font-mono tracking-tight text-[var(--text-main)]">{liveMETs.toFixed(2)}</span>
                      <span className="text-xs text-[var(--text-secondary)] ml-1">METs</span>
                    </div>
                    <svg className="w-16 h-6 text-sky-500" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 64 24"><path strokeLinecap="round" strokeLinejoin="round" d="M2 20 L20 18 L38 20 L50 16 L62 18" /></svg>
                  </div>
                  <div className="text-[11px] text-[var(--text-muted)] flex items-center justify-between pt-1 border-t border-[var(--border-main)]">
                    <span>Desk / Resting</span>
                    <span>Accelerometry</span>
                  </div>
                </div>

                <div className="clean-card p-4 space-y-2">
                  <div className="flex items-center justify-between text-xs text-[var(--text-secondary)]">
                    <span>Time in Range (TIR)</span>
                    <span className="text-[10px] font-mono text-[var(--text-muted)]">GMI: 6.8%</span>
                  </div>
                  <div className="flex items-baseline justify-between">
                    <div>
                      <span className="text-2xl font-bold font-mono tracking-tight text-emerald-600 dark:text-emerald-400">78%</span>
                      <span className="text-xs text-[var(--text-muted)] ml-1">(&ge;70%)</span>
                    </div>
                    <span className="text-[11px] font-mono text-emerald-600 dark:text-emerald-400 font-semibold">OPTIMAL</span>
                  </div>
                  <div className="w-full h-1.5 rounded-full overflow-hidden flex bg-[var(--border-main)] mt-1">
                    <div className="bg-emerald-500 h-full" style={{ width: "78%" }}></div>
                    <div className="bg-rose-500 h-full" style={{ width: "18%" }}></div>
                    <div className="bg-amber-400 h-full" style={{ width: "4%" }}></div>
                  </div>
                </div>

                <div className="clean-card p-4 space-y-2">
                  <div className="flex items-center justify-between text-xs text-[var(--text-secondary)]">
                    <span>Candidate S Peak</span>
                    <span className="px-1.5 py-0.2 rounded text-[10px] font-mono text-purple-600 dark:text-purple-400 bg-purple-500/10">INFERENCE</span>
                  </div>
                  <div className="flex items-baseline justify-between">
                    <div>
                      <span className="text-2xl font-bold font-mono tracking-tight text-[var(--text-main)]">164.2</span>
                      <span className="text-xs text-[var(--text-secondary)] ml-1">mg/dL</span>
                    </div>
                    <span className="text-[11px] font-mono text-slate-500">+55m</span>
                  </div>
                  <div className="text-[11px] text-[var(--text-muted)] flex items-center justify-between pt-1 border-t border-[var(--border-main)]">
                    <span>Target &lt; 180</span>
                    <span className="text-emerald-600 dark:text-emerald-400 font-semibold">PASS</span>
                  </div>
                </div>
              </div>

              {/* Trajectory Display */}
              <div className="clean-card p-6 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[var(--border-main)] pb-3">
                  <div>
                    <div className="flex items-center gap-2.5">
                      <h2 className="text-base font-semibold text-[var(--text-main)]">180-Minute Postprandial Glycemic Forecast</h2>
                      <span className="px-2 py-0.2 rounded text-[11px] font-mono font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                        {reliability} CONFIDENCE
                      </span>
                    </div>
                    <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                      Dual-gamma neural model with 90% split-conformal uncertainty intervals and real recorded sensor ground truth overlay
                    </p>
                  </div>

                  <div className="flex flex-wrap items-center gap-3.5 text-xs">
                    <span className="flex items-center gap-1.5 text-[var(--text-secondary)]">
                      <span className="w-3 h-0.5 bg-emerald-500 inline-block"></span> Candidate S Prediction
                    </span>
                    <span className="flex items-center gap-1.5 text-[var(--text-secondary)]">
                      <span className="w-3 h-0.5 border-b-2 border-dashed border-amber-500 inline-block"></span> Recorded CGM Truth
                    </span>
                    <span className="flex items-center gap-1.5 text-[var(--text-secondary)]">
                      <span className="w-3 h-2 bg-emerald-500/15 border border-emerald-500/30 rounded-sm inline-block"></span> 90% Conformal Band
                    </span>
                  </div>
                </div>

                <div className="flex flex-wrap items-center justify-between px-3.5 py-1.5 rounded-lg bg-[var(--bg-card-subtle)] border border-[var(--border-main)] text-xs font-mono text-[var(--text-secondary)]">
                  <div className="flex items-center gap-3">
                    <span>Scrubber:</span>
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

                <div className="h-80 w-full bg-[var(--bg-canvas)] rounded-xl border border-[var(--border-main)] p-4 flex flex-col justify-between">
                  <div className="flex justify-between items-center text-xs text-rose-600 dark:text-rose-400 font-mono border-b border-rose-500/20 pb-1">
                    <span>Hyperglycemia Threshold (180 mg/dL)</span>
                    <span className="px-1.5 py-0.2 rounded bg-rose-500/10 border border-rose-500/20 text-[10px]">ADA Target &lt; 180</span>
                  </div>
                  <div className="flex-1 flex items-center justify-center text-center">
                    <div className="space-y-1">
                      <span className="text-sm font-semibold text-[var(--text-main)] block">Candidate S PyTorch Streaming Active</span>
                      <span className="text-xs text-[var(--text-secondary)] block max-w-lg mx-auto">
                        5-minute interval streaming from parquet engine with Ridge K=5 adapted weights.
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

                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2 border-t border-[var(--border-main)]">
                  <div className="bg-[var(--bg-card-subtle)] p-3 rounded-lg border border-[var(--border-main)] text-center">
                    <span className="text-xs text-[var(--text-secondary)] block mb-0.5">Predicted Peak Excursion</span>
                    <span className="text-xl font-bold font-mono text-[var(--text-main)]">164.2 mg/dL</span>
                    <span className="text-[11px] text-emerald-600 dark:text-emerald-400 block mt-0.5">Within Target</span>
                  </div>
                  <div className="bg-[var(--bg-card-subtle)] p-3 rounded-lg border border-[var(--border-main)] text-center">
                    <span className="text-xs text-[var(--text-secondary)] block mb-0.5">Time to Peak</span>
                    <span className="text-xl font-bold font-mono text-[var(--text-main)]">55 min</span>
                    <span className="text-[11px] text-[var(--text-muted)] block mt-0.5">Absorption Kinetics</span>
                  </div>
                  <div className="bg-[var(--bg-card-subtle)] p-3 rounded-lg border border-[var(--border-main)] text-center">
                    <span className="text-xs text-[var(--text-secondary)] block mb-0.5">Late Lipid Mean (120–180m)</span>
                    <span className="text-xl font-bold font-mono text-sky-600 dark:text-sky-400">138.4 mg/dL</span>
                    <span className="text-[11px] text-[var(--text-muted)] block mt-0.5">Sustained Plateau</span>
                  </div>
                  <div className="bg-[var(--bg-card-subtle)] p-3 rounded-lg border border-[var(--border-main)] text-center">
                    <span className="text-xs text-[var(--text-secondary)] block mb-0.5">Time Above 180</span>
                    <span className="text-xl font-bold font-mono text-emerald-600 dark:text-emerald-400">0 min (0%)</span>
                    <span className="text-[11px] text-emerald-600 dark:text-emerald-400 block mt-0.5">Clinical Safety</span>
                  </div>
                </div>
              </div>

            </div>
          )}

          {/* TAB 2: WHAT-IF MEAL SANDBOX */}
          {activeTab === "whatif" && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                
                <div className="lg:col-span-5 clean-card p-6 space-y-5">
                  <div className="border-b border-[var(--border-main)] pb-3 flex items-center justify-between">
                    <div>
                      <h2 className="text-base font-semibold text-[var(--text-main)]">What-If Counterfactual Sandbox</h2>
                      <p className="text-xs text-[var(--text-secondary)] mt-0.5">Simulate modified carbohydrate, fat, protein, or exercise interventions</p>
                    </div>
                    <button onClick={() => setIsCustomMealOpen(true)} className="px-2.5 py-1 rounded-lg border border-[var(--border-main)] bg-[var(--bg-card-subtle)] text-xs font-medium text-[var(--text-main)] hover:border-[var(--border-subtle)] transition">
                      + Custom Meal
                    </button>
                  </div>

                  <div className="space-y-2">
                    <label className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] block">
                      Regional Indian Clinical Presets:
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      <button onClick={() => selectDish("roti_dal_sabzi")} className={`text-left p-3 rounded-lg border transition ${activeDishName.includes("Roti") ? "border-purple-500 bg-purple-500/5" : "border-[var(--border-main)] bg-[var(--bg-card-subtle)]"}`}>
                        <div className="text-xs font-medium text-[var(--text-main)]">Roti, Dal &amp; Sabzi</div>
                        <div className="text-[11px] text-[var(--text-secondary)] mt-0.5">48g C • 12g F • 16g P</div>
                      </button>
                      <button onClick={() => selectDish("masala_dosa")} className={`text-left p-3 rounded-lg border transition ${activeDishName.includes("Dosa") ? "border-purple-500 bg-purple-500/5" : "border-[var(--border-main)] bg-[var(--bg-card-subtle)]"}`}>
                        <div className="text-xs font-medium text-[var(--text-main)]">Masala Dosa + Sambar</div>
                        <div className="text-[11px] text-[var(--text-secondary)] mt-0.5">62g C • 18g F • 10g P</div>
                      </button>
                      <button onClick={() => selectDish("chicken_biryani")} className={`text-left p-3 rounded-lg border transition ${activeDishName.includes("Biryani") ? "border-purple-500 bg-purple-500/5" : "border-[var(--border-main)] bg-[var(--bg-card-subtle)]"}`}>
                        <div className="text-xs font-medium text-[var(--text-main)]">Chicken Biryani</div>
                        <div className="text-[11px] text-[var(--text-secondary)] mt-0.5">68g C • 22g F • 32g P</div>
                      </button>
                      <button onClick={() => selectDish("rajma_chawal")} className={`text-left p-3 rounded-lg border transition ${activeDishName.includes("Rajma") ? "border-purple-500 bg-purple-500/5" : "border-[var(--border-main)] bg-[var(--bg-card-subtle)]"}`}>
                        <div className="text-xs font-medium text-[var(--text-main)]">Rajma Chawal</div>
                        <div className="text-[11px] text-[var(--text-secondary)] mt-0.5">72g C • 14g F • 20g P</div>
                      </button>
                    </div>
                  </div>

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

                  <div className="space-y-4 pt-1">
                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-[var(--text-secondary)] font-medium">Carbohydrates</span>
                        <span className="font-mono font-semibold text-amber-600 dark:text-amber-400">{carbs} g</span>
                      </div>
                      <input type="range" min={10} max={140} value={carbs} onChange={(e) => setCarbs(Number(e.target.value))} className="w-full accent-amber-500" />
                    </div>

                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-[var(--text-secondary)] font-medium">Dietary Fat</span>
                        <span className="font-mono font-semibold text-sky-600 dark:text-sky-400">{fat} g</span>
                      </div>
                      <input type="range" min={0} max={60} value={fat} onChange={(e) => setFat(Number(e.target.value))} className="w-full accent-sky-500" />
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
                      <input type="range" min={25} max={200} step={25} value={portion} onChange={(e) => setPortion(Number(e.target.value))} className="w-full accent-purple-500" />
                    </div>
                  </div>

                  <div className="pt-3 border-t border-[var(--border-main)] space-y-2.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)]">Behavioral Interventions</span>
                      <span className="text-[11px] px-2 py-0.2 rounded font-mono font-semibold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
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

          {/* TAB 3: CHRONOLOGICAL MEAL TIMELINE (Refero Design Style) */}
          {activeTab === "timeline" && (
            <div className="space-y-6">
              
              <div className="clean-card p-4 flex flex-wrap items-center justify-between gap-4 text-xs">
                <div className="flex flex-wrap items-center gap-3">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[var(--text-secondary)]">Date range:</span>
                    <input type="text" value="February 2026 (Clinical Protocol)" className="bg-[var(--bg-card-subtle)] border border-[var(--border-main)] text-[var(--text-main)] rounded px-2.5 py-1 text-xs outline-none" readOnly />
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-[var(--text-secondary)]">Meal Type:</span>
                    <select className="bg-[var(--bg-card-subtle)] border border-[var(--border-main)] text-[var(--text-main)] rounded px-2.5 py-1 text-xs outline-none">
                      <option>All Postprandial Excursions</option>
                      <option>Breakfast Excursions</option>
                      <option>Lunch Excursions</option>
                      <option>Dinner Excursions</option>
                    </select>
                  </div>
                  <button className="px-4 py-1 rounded bg-[var(--text-main)] text-[var(--bg-card)] font-semibold shadow-sm hover:opacity-90 transition">
                    FILTER
                  </button>
                </div>
                <div>
                  <button onClick={() => triggerToast("Exporting postprandial parquet log to CSV...")} className="text-purple-600 dark:text-purple-400 hover:underline">
                    Want to export to a spreadsheet?
                  </button>
                </div>
              </div>

              <div className="clean-card overflow-hidden">
                <div className="p-4 border-b border-[var(--border-main)] flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-[var(--text-main)]">Recorded 180-Min Excursion Sessions</h3>
                  <span className="text-xs text-[var(--text-secondary)] font-mono">Total Meals: 54 Ingested</span>
                </div>
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-[var(--bg-card-subtle)] text-[var(--text-secondary)] border-b border-[var(--border-main)]">
                    <tr>
                      <th className="py-2.5 px-4 font-semibold">Excursion Type</th>
                      <th className="py-2.5 px-4 font-semibold">Carbs (g)</th>
                      <th className="py-2.5 px-4 font-semibold">Fat (g)</th>
                      <th className="py-2.5 px-4 font-semibold">Protein (g)</th>
                      <th className="py-2.5 px-4 font-semibold">Observed Peak</th>
                      <th className="py-2.5 px-4 font-semibold">Duration</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border-main)] text-[var(--text-main)]">
                    <tr>
                      <td className="py-2.5 px-4 font-medium">Standard Indian Mixed Meal</td>
                      <td className="py-2.5 px-4 font-mono">48.0g</td>
                      <td className="py-2.5 px-4 font-mono">12.0g</td>
                      <td className="py-2.5 px-4 font-mono">16.0g</td>
                      <td className="py-2.5 px-4 font-mono text-emerald-600 dark:text-emerald-400 font-semibold">162.0 mg/dL</td>
                      <td className="py-2.5 px-4 text-[var(--text-secondary)]">180 min</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium">High Carbohydrate Breakfast</td>
                      <td className="py-2.5 px-4 font-mono">68.0g</td>
                      <td className="py-2.5 px-4 font-mono">8.0g</td>
                      <td className="py-2.5 px-4 font-mono">10.0g</td>
                      <td className="py-2.5 px-4 font-mono text-rose-600 dark:text-rose-400 font-semibold">188.5 mg/dL</td>
                      <td className="py-2.5 px-4 text-[var(--text-secondary)]">180 min</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-medium">High Lipid Delayed Plateau</td>
                      <td className="py-2.5 px-4 font-mono">42.0g</td>
                      <td className="py-2.5 px-4 font-mono">28.0g</td>
                      <td className="py-2.5 px-4 font-mono">22.0g</td>
                      <td className="py-2.5 px-4 font-mono text-sky-600 dark:text-sky-400 font-semibold">154.0 mg/dL</td>
                      <td className="py-2.5 px-4 text-[var(--text-secondary)]">180 min</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div className="space-y-4">
                <div className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)]">
                  Chronological Timeline Feed
                </div>

                <div className="space-y-2">
                  <div className="bg-[var(--bg-card-subtle)] px-4 py-1.5 rounded-lg text-xs font-semibold text-[var(--text-secondary)] border border-[var(--border-main)]">
                    February 13, 2026 — Clinical Ingest Stream
                  </div>

                  <div className="clean-card p-4 flex items-center justify-between gap-4">
                    <div className="flex items-center gap-4">
                      <div className="text-xs font-mono text-[var(--text-secondary)] text-right w-16">
                        <div className="font-bold text-[var(--text-main)]">08:30</div>
                        <div>11:30</div>
                      </div>
                      <div className="w-1 h-10 rounded-full bg-emerald-500"></div>
                      <div>
                        <div className="text-xs font-semibold text-[var(--text-main)]">Breakfast: 2 Rotis with Dal &amp; Mixed Veg Sabzi</div>
                        <div className="text-[11px] text-[var(--text-secondary)]">Nutrients: 48g Carbs • 12g Fat • 16g Protein | Peak: 164.2 mg/dL at +55m</div>
                        <div className="text-[10px] text-[var(--text-muted)]">Verified Continuous 5-Min Telemetry Buffer</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[var(--bg-card-subtle)] text-[var(--text-secondary)] border border-[var(--border-main)]">
                        180 min
                      </span>
                    </div>
                  </div>

                  <div className="clean-card p-4 flex items-center justify-between gap-4">
                    <div className="flex items-center gap-4">
                      <div className="text-xs font-mono text-[var(--text-secondary)] text-right w-16">
                        <div className="font-bold text-[var(--text-main)]">13:15</div>
                        <div>16:15</div>
                      </div>
                      <div className="w-1 h-10 rounded-full bg-purple-500"></div>
                      <div>
                        <div className="text-xs font-semibold text-[var(--text-main)]">Lunch: Masala Dosa with Sambar &amp; Chutney</div>
                        <div className="text-[11px] text-[var(--text-secondary)]">Nutrients: 62g Carbs • 18g Fat • 10g Protein | Peak: 178.0 mg/dL at +45m</div>
                        <div className="text-[10px] text-[var(--text-muted)]">Post-meal walking intervention recorded (15 min)</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[var(--bg-card-subtle)] text-[var(--text-secondary)] border border-[var(--border-main)]">
                        180 min
                      </span>
                    </div>
                  </div>
                </div>
              </div>

            </div>
          )}

          {/* TAB 4: PATIENT PROFILE */}
          {activeTab === "profile" && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                
                <div className="clean-card p-6 space-y-4">
                  <h2 className="text-base font-semibold text-[var(--text-main)]">Clinical Baseline Profile</h2>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between py-2 border-b border-[var(--border-main)]"><span className="text-[var(--text-secondary)]">Patient:</span> <span className="font-mono text-[var(--text-main)] font-semibold">{patientId}</span></div>
                    <div className="flex justify-between py-2 border-b border-[var(--border-main)]"><span className="text-[var(--text-secondary)]">Diagnosis:</span> <span className="text-emerald-600 dark:text-emerald-400 font-semibold">{currentPatient.diagnosis}</span></div>
                    <div className="flex justify-between py-2 border-b border-[var(--border-main)]"><span className="text-[var(--text-secondary)]">Age &amp; Sex:</span> <span className="text-[var(--text-main)]">{currentPatient.age}</span></div>
                    <div className="flex justify-between py-2 border-b border-[var(--border-main)]"><span className="text-[var(--text-secondary)]">BMI:</span> <span className="text-[var(--text-main)] font-mono">{currentPatient.bmi}</span></div>
                    <div className="flex justify-between py-2 border-b border-[var(--border-main)]"><span className="text-[var(--text-secondary)]">Baseline HbA1c:</span> <span className="text-amber-600 dark:text-amber-400 font-semibold font-mono">{currentPatient.hba1c}</span></div>
                    <div className="flex justify-between py-2"><span className="text-[var(--text-secondary)]">Fasting Glucose:</span> <span className="text-[var(--text-main)] font-mono">{currentPatient.fasting}</span></div>
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
                      <span className="text-[var(--text-main)] mt-0.5 block">{currentPatient.meds}</span>
                    </div>
                    <div className="p-3 bg-[var(--bg-card-subtle)] rounded-lg border border-[var(--border-main)]">
                      <span className="text-[var(--text-secondary)] block font-medium">Diagnosed Comorbidities:</span>
                      <span className="text-[var(--text-main)] mt-0.5 block">{currentPatient.comorbidities}</span>
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

          {/* TAB 5: SENSOR STRESS AUDIT */}
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

          {/* TAB 6: DOCTRONIC AI DOCTOR PERSONA & SETTINGS */}
          {activeTab === "settings" && (
            <div className="space-y-8 max-w-4xl">
              
              <div className="space-y-3 pt-2">
                <h1 className="text-3xl font-serif text-[var(--text-main)]">Dr. Connie</h1>
                <p className="text-xs text-[var(--text-secondary)]">aegis.endocrinology.twin@happiesthealth.org</p>
                <div className="flex items-center gap-2 pt-1">
                  <button onClick={() => triggerToast("Connecting to clinical protocol support...")} className="px-3 py-1 rounded-full border border-[var(--border-main)] bg-[var(--bg-card)] hover:border-[var(--border-subtle)] text-xs text-[var(--text-main)] flex items-center gap-1.5 transition">
                    <span>✉</span> Contact us
                  </button>
                  <button onClick={() => triggerToast("Opening clinical guideline resources...")} className="px-3 py-1 rounded-full border border-[var(--border-main)] bg-[var(--bg-card)] hover:border-[var(--border-subtle)] text-xs text-[var(--text-main)] flex items-center gap-1.5 transition">
                    <span>?</span> Resources
                  </button>
                  <button onClick={() => triggerToast("Feedback submitted to team Aegis.")} className="px-3 py-1 rounded-full border border-[var(--border-main)] bg-[var(--bg-card)] hover:border-[var(--border-subtle)] text-xs text-[var(--text-main)] flex items-center gap-1.5 transition">
                    <span>☆</span> Feedback
                  </button>
                </div>
              </div>

              <div className="h-px bg-[var(--border-main)]"></div>

              <div className="space-y-8 text-xs">
                
                {/* Response Style Row (Doctronic Step 1, 2, 3) */}
                <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
                  <div className="md:col-span-4 flex items-center gap-2.5 text-sm font-medium text-[var(--text-main)]">
                    <svg className="w-5 h-5 text-[var(--text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                    <span>Response style</span>
                  </div>

                  <div className="md:col-span-8 relative">
                    <button
                      onClick={() => setIsStylePopoverOpen((p) => !p)}
                      className="w-full flex items-center justify-between p-3 rounded-xl border border-[var(--border-main)] bg-[var(--bg-card)] text-left hover:border-[var(--border-subtle)] transition"
                    >
                      <span className="font-medium text-[var(--text-main)]">{doctorResponseStyle}</span>
                      <svg className="w-4 h-4 text-[var(--text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"/></svg>
                    </button>

                    {isStylePopoverOpen && (
                      <div className="absolute top-full mt-2 left-0 right-0 z-50 bg-[var(--bg-card)] rounded-xl border border-[var(--border-main)] shadow-xl overflow-hidden p-1.5 space-y-1">
                        {[
                          { name: "Default", desc: "Aegis standard clinical medical tone with professionalism and physiological context" },
                          { name: "Just the facts", desc: "Clinical precision without the bedside manner (numeric metrics, deltas, and ADA ranges only)" },
                          { name: "The wise professor", desc: "Detailed mechanistic endocrinology explanations with metabolic physiology context" },
                          { name: "Supportive", desc: "Empathetic preventive wellness guidance, post-meal walking prompts, and positive reinforcement" },
                          { name: "Your friendly neighbor", desc: "Warm, approachable conversation free of heavy clinical jargon" },
                        ].map((style) => (
                          <div
                            key={style.name}
                            onClick={() => {
                              setDoctorResponseStyle(style.name);
                              setIsStylePopoverOpen(false);
                              triggerToast("Your settings have been updated");
                            }}
                            className={`p-2.5 rounded-lg cursor-pointer transition ${
                              doctorResponseStyle === style.name ? "bg-emerald-500/10 text-[var(--text-main)]" : "hover:bg-[var(--bg-card-subtle)] text-[var(--text-secondary)]"
                            }`}
                          >
                            <div className="flex items-center justify-between font-semibold">
                              <span>{style.name}</span>
                              {doctorResponseStyle === style.name && <span className="text-emerald-500">✓</span>}
                            </div>
                            <div className="text-[11px] mt-0.5">{style.desc}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Time Zone */}
                <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
                  <div className="md:col-span-4 flex items-center gap-2.5 text-sm font-medium text-[var(--text-main)]">
                    <svg className="w-5 h-5 text-[var(--text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
                    <span>Clinical Time Zone</span>
                  </div>
                  <div className="md:col-span-8">
                    <div className="flex items-center gap-2 p-3 rounded-xl border border-[var(--border-main)] bg-[var(--bg-card)]">
                      <svg className="w-4 h-4 text-[var(--text-muted)]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                      <input type="text" defaultValue="Asia / Kolkata (GMT+5:30)" className="w-full bg-transparent text-[var(--text-main)] outline-none font-medium" onChange={(e) => triggerToast(`Time zone updated to ${e.target.value}`)} />
                    </div>
                  </div>
                </div>

                {/* Memory & Sync */}
                <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
                  <div className="md:col-span-4 flex items-center gap-2.5 text-sm font-medium text-[var(--text-main)]">
                    <svg className="w-5 h-5 text-[var(--text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg>
                    <span>Twin Memory</span>
                  </div>
                  <div className="md:col-span-8 space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-semibold text-[var(--text-main)]">Reference patient chat history</div>
                        <div className="text-[11px] text-[var(--text-secondary)]">Let Aegis reference previous endocrinology consultations when predicting response.</div>
                      </div>
                      <span className="font-semibold text-[var(--text-main)] px-2.5 py-1 rounded bg-[var(--bg-card-subtle)] border border-[var(--border-main)]">On</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-semibold text-[var(--text-main)]">Reference synthetic medical records</div>
                        <div className="text-[11px] text-[var(--text-secondary)]">Let Aegis reference shared EHR biomarkers (HbA1c, fasting glucose) when calibrating Ridge weights.</div>
                      </div>
                      <span className="font-semibold text-[var(--text-main)] px-2.5 py-1 rounded bg-[var(--bg-card-subtle)] border border-[var(--border-main)]">On</span>
                    </div>
                  </div>
                </div>

              </div>

              <div className="pt-8 border-t border-[var(--border-main)] space-y-4">
                <div className="flex justify-center">
                  <button onClick={() => triggerToast("Clinician session reset.")} className="px-8 py-2 rounded-full border border-[var(--border-main)] bg-[var(--bg-card)] text-xs font-semibold text-[var(--text-main)] hover:border-[var(--border-subtle)] transition">
                    Reset Session
                  </button>
                </div>
                <p className="text-center text-[11px] text-[var(--text-muted)] max-w-xl mx-auto">
                  Always review digital twin trajectories with licensed endocrinologists. Aegis is an AI research prototype, not a certified medical device, and does not provide prescription or acute titration decisions.
                </p>
              </div>

            </div>
          )}

        </main>

      </div>

      {/* 4. Command Palette Modal */}
      {isPaletteOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-start justify-center pt-24 px-4">
          <div className="w-full max-w-xl bg-[var(--bg-card)] rounded-xl border border-[var(--border-main)] shadow-2xl overflow-hidden">
            <div className="p-3.5 border-b border-[var(--border-main)] flex items-center gap-3 bg-[var(--bg-card-subtle)]">
              <input
                type="text"
                autoFocus
                value={paletteQuery}
                onChange={(e) => { setPaletteQuery(e.target.value); setPaletteIndex(0); }}
                placeholder="Search actions, twins, meal presets, or theme..."
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
                      idx === paletteIndex ? "bg-purple-500/10 border border-purple-500/40 text-[var(--text-main)]" : "bg-[var(--bg-card-subtle)] border border-transparent text-[var(--text-secondary)] hover:text-[var(--text-main)] hover:border-[var(--border-main)]"
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-purple-500"></span>
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

      {/* 5. Custom Meal Modal */}
      {isCustomMealOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-[var(--bg-card)] rounded-xl border border-[var(--border-main)] shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-[var(--border-main)] pb-3">
              <h3 className="text-sm font-semibold text-[var(--text-main)]">Build Custom Nutritional Input</h3>
              <button onClick={() => setIsCustomMealOpen(false)} className="text-[var(--text-secondary)] hover:text-[var(--text-main)] text-xs">✕</button>
            </div>
            <div className="space-y-3 text-xs">
              <div>
                <label className="text-[var(--text-secondary)] font-medium block mb-1">Meal Name:</label>
                <input
                  type="text"
                  value={customName}
                  onChange={(e) => setCustomName(e.target.value)}
                  className="w-full bg-[var(--bg-card-subtle)] border border-[var(--border-main)] text-[var(--text-main)] rounded-lg p-2.5 outline-none focus:border-purple-500"
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
                className="px-4 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-sm transition"
              >
                Apply to Sandbox
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
