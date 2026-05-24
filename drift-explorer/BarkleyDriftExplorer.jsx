/**
 * Barkley Drift Explorer
 * Behavioral Intelligence MVP for Dogs
 * -------------------------------------------------------
 * Version:
 * V1.0 Owner-Centric Prototype
 *
 * A front-end-only demonstrator exploring:
 * - Individual behavioral baselines
 * - Longitudinal drift detection
 * - Silence as signal
 * - Context-aware behavioral observability
 *
 * Core thesis:
 * A dog can remain normal for its breed
 * while drifting away from its own baseline.
 *
 * Conceptual foundation:
 * "From Surveillance to Cognition"
 * A framework for longitudinal behavioral intelligence
 * in companion animals.
 *
 * Full framework paper:
 * "From Surveillance to Cognition:
 * A Unified Framework for Precision Behavioral
 * and Metabolic Intelligence in Companion Animals"
 *
 * DOI:
 * https://doi.org/10.5281/zenodo.20060327
 *
 * Zenodo:
 * https://zenodo.org/records/20060327
 *
 * Academia:
 * https://www.academia.edu/166873379/From_Surveillance_to_Cognition_A_Unified_Framework_for_Precision_Behavioral_and_Metabolic_Intelligence_in_Companion_Animals
 *
 * Built for:
 * HackerNoon "Proof of Usefulness" Tech & AI Hackathon 2026
 *
 * Tech Stack:
 * React, Recharts, Tailwind CSS
 * Single-file architecture
 *
 * Built by:
 * Elodie Aishwarya P. Remoissenet
 * Founder, Barkley AI
 *
 * Barkley:
 * https://getbarkley.com
 *
 * GitHub:
 * https://github.com/labs-barkley/barkley-canine-cognition-lab
 *
 * Reference Architecture:
 * https://github.com/labs-barkley/barkley-reference-architecture
 *
 * Hugging Face Dataset:
 * https://huggingface.co/datasets/labs-barkley/synthetic-doggraph-sample
 *
 * ORCID:
 * https://orcid.org/0009-0004-6031-659X
 *
 * Medium Publication:
 * https://medium.com/@labs-barkley/your-dog-can-be-normal-for-its-breed-and-abnormal-for-itself-0a4c9a7b3f58
 *
 * Synthetic Data Notice:
 * This MVP uses fully synthetic behavioral data
 * for demonstration and research visualization purposes only.
 *
 * Disclaimer:
 * This demonstrator is not a medical or veterinary diagnostic tool.
 *
 * Copyright © 2026 Barkley AI
 * All rights reserved.
 */
import { useState, useEffect, useRef, useMemo, useCallback } from "react";
import {
  ComposedChart, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer, ReferenceLine, ReferenceArea,
} from "recharts";

// ─────────────────────────────────────────────
//  DESIGN TOKENS
// ─────────────────────────────────────────────
const C = {
  bg:    "#000",
  s1:    "#06060a",
  white: "#f0ede8",
  dim:   "rgba(240,237,232,.55)",
  muted: "rgba(240,237,232,.38)",
  ghost: "rgba(240,237,232,.18)",
  line:  "rgba(240,237,232,.08)",
  blue:  "#7b9fff",
  pink:  "#c97bff",
  teal:  "#3fd6bc",
  amber: "#f5a623",
  red:   "#ff8a80",
};
const MONO = "'DM Mono','Courier New',monospace";
const SANS = "'Plus Jakarta Sans','Helvetica Neue',sans-serif";

const DOG = { name: "Kikoo", breed: "Jack Russell Terrier", age: "Adult" };

// ─────────────────────────────────────────────
//  SYNTHETIC DATA  (seed 2026, deterministic)
// ─────────────────────────────────────────────
const BREED_MU  = 72;
const BREED_SIG = 17;
const BASELINE  = 90;
const DRIFT_DAY = 35;

const SILENCE_META = {
  10: { label:"Collar removal",        owner:"Kikoo wasn't wearing the sensor." },
  11: { label:"Collar removal",        owner:"Kikoo wasn't wearing the sensor." },
  32: { label:"Sensor dropout",        owner:"Signal gap — device issue." },
  54: { label:"Behavioral withdrawal", owner:"Kikoo went quiet." },
  66: { label:"Behavioral withdrawal", owner:"Kikoo went quiet." },
  67: { label:"Behavioral withdrawal", owner:"Kikoo went quiet." },
  77: { label:"Behavioral withdrawal", owner:"Kikoo went quiet." },
};

const CTX_EVENTS = [
  { day:36, label:"Heatwave",           short:"☀", color:C.amber },
  { day:49, label:"Owner at work",      short:"⊕", color:C.muted },
  { day:59, label:"Weekend hike",       short:"△", color:C.teal  },
  { day:65, label:"New dog nearby",     short:"◎", color:C.blue  },
  { day:78, label:"Routine disruption", short:"↯", color:C.red   },
];

const DATA = (() => {
  let s = 2026;
  const rng = () => { s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; };
  return Array.from({ length:90 }, (_, i) => {
    const silent = i in SILENCE_META;
    const df     = i >= DRIFT_DAY ? Math.min(1,(i - DRIFT_DAY)/55) : 0;
    const wave   = Math.sin((i/7)*Math.PI*2)*3.8;
    const noise  = (rng()-.5)*9;
    const raw    = BASELINE + wave + noise - df*34;
    const value  = silent ? null : Math.round(Math.max(30,raw)*10)/10;
    return { day:i+1, value, stableVal:(!silent&&i<DRIFT_DAY)?value:null,
             driftVal:(!silent&&i>=DRIFT_DAY)?value:null, silent, sMeta:SILENCE_META[i]??null };
  });
})();

const SIL_SPANS = (() => {
  const days = Object.keys(SILENCE_META).map(Number).sort((a,b)=>a-b);
  const runs=[]; let r=[days[0]];
  for(let k=1;k<days.length;k++){
    if(days[k]===days[k-1]+1) r.push(days[k]); else { runs.push(r); r=[days[k]]; }
  }
  runs.push(r);
  return runs.map(g=>({x1:g[0]+.55,x2:g[g.length-1]+1.45}));
})();

// ─────────────────────────────────────────────
//  CARD DATA  — two layers: metric + owner
// ─────────────────────────────────────────────
const BREED_CARDS = [
  { label:"Activity score",  val:"Normal",      sub:"Consistent with breed patterns.",            accent:C.muted                                                          },
  { label:"Recovery",        val:"Typical",     sub:"No deviation from population range.",        accent:C.muted                                                          },
  { label:"Rate of decay",   val:"Not visible", sub:"Breed baseline cannot see individual drift.",insight:"The signal is there. This frame can't reach it.", accent:C.amber },
  { label:"Anomaly status",  val:"Clear",       sub:"No population-level anomaly detected.",      accent:C.muted                                                          },
];
const INDIV_CARDS = [
  { label:"Activity drift",    val:"−18%",    sub:"vs. Kikoo's own W1–5 baseline",  insight:"Kikoo is moving less than their usual pattern.",               accent:C.pink, pulse:true },
  { label:"Recovery latency",  val:"+31%",    sub:"Post-stimulation recovery time", insight:"Recovery after stimulation appears slower.",                   accent:C.pink, pulse:true },
  { label:"Silence frequency", val:"3×",      sub:"Informative absence events",     insight:"More moments of absence are appearing in the pattern.",        accent:C.teal, pulse:true },
  { label:"Rate of decay",     val:"Detected",sub:"−0.4 σ / week · 6-week trend",  insight:"The change is gradual — easy to miss with breed averages.",    accent:C.red,  pulse:true },
];

// ─────────────────────────────────────────────
//  GLOBAL CSS
// ─────────────────────────────────────────────
const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=DM+Mono:wght@400;500&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{-webkit-font-smoothing:antialiased}body{background:#000}

@keyframes pulse  {0%,100%{opacity:1;transform:scale(1)}50%{opacity:.3;transform:scale(.88)}}
@keyframes spin   {to{transform:rotate(360deg)}}
@keyframes cardIn {from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
@keyframes fadeUp {from{opacity:0;transform:translateY(7px)}to{opacity:1;transform:none}}
@keyframes glow   {0%,100%{box-shadow:0 0 20px rgba(201,123,255,.07)}50%{box-shadow:0 0 40px rgba(201,123,255,.2)}}
@keyframes haloBreath {0%,100%{opacity:.52;transform:scale(1)}50%{opacity:.82;transform:scale(1.07)}}

@media(prefers-reduced-motion:reduce){
  *,*::before,*::after{
    animation-duration:.01ms!important;
    animation-iteration-count:1!important;
    transition-duration:.1ms!important;
  }
}

.bde-ctrl:hover  {color:rgba(240,237,232,.72)!important;border-color:rgba(240,237,232,.22)!important}
.bde-link:hover  {opacity:.8}
.bde-ibtn:hover  {background:rgba(240,237,232,.1)!important}

.bde-toggle:focus-visible,.bde-ctrl:focus-visible,.bde-link:focus-visible,.bde-ibtn:focus-visible{
  outline:2px solid rgba(123,159,255,.65);outline-offset:2px;
}

.bde-tg-eyebrow{display:flex;align-items:center;gap:.4rem;flex-wrap:wrap;
  font-size:10px;font-family:'DM Mono','Courier New',monospace;letter-spacing:.08em;
  text-transform:uppercase;color:rgba(240,237,232,.3);margin:1.2rem 0 .7rem}
.bde-tg-eyebrow b{color:rgba(240,237,232,.62);font-weight:500}

.bde-toggle{position:relative;display:flex;flex-direction:column;gap:.55rem;
  padding:1.1rem 1.25rem;border-radius:14px;text-align:left;cursor:pointer;
  border:1px solid rgba(240,237,232,.08);background:transparent;opacity:.5;
  transition:opacity .4s cubic-bezier(.4,0,.2,1),border-color .4s cubic-bezier(.4,0,.2,1),
             background .4s cubic-bezier(.4,0,.2,1),box-shadow .45s cubic-bezier(.4,0,.2,1),
             transform .35s cubic-bezier(.34,1.4,.5,1)}
.bde-toggle[data-active="false"]:hover{opacity:.82;transform:translateY(-1px);
  border-color:rgba(240,237,232,.18);background:rgba(240,237,232,.02)}
.bde-toggle[data-active="true"]{opacity:1;transform:translateY(-2px) scale(1.008)}
.bde-toggle[data-active="true"][data-frame="breed"]{
  border-color:rgba(240,237,232,.34);background:rgba(240,237,232,.055);
  box-shadow:0 6px 24px rgba(0,0,0,.35)}
.bde-toggle[data-active="true"][data-frame="individual"]{
  border-color:rgba(201,123,255,.5);background:rgba(201,123,255,.06);
  box-shadow:0 0 0 1px rgba(201,123,255,.12),0 0 40px rgba(201,123,255,.15),0 6px 24px rgba(0,0,0,.35)}

.bde-tg-head{display:flex;align-items:center;gap:.5rem}
.bde-tg-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0;
  background:rgba(240,237,232,.22);transition:background .4s,box-shadow .4s,transform .4s cubic-bezier(.34,1.4,.5,1)}
.bde-toggle[data-active="true"][data-frame="breed"] .bde-tg-dot{
  background:rgba(240,237,232,.95);box-shadow:0 0 10px rgba(240,237,232,.5);transform:scale(1.25)}
.bde-toggle[data-active="true"][data-frame="individual"] .bde-tg-dot{
  background:#c97bff;box-shadow:0 0 13px #c97bff;transform:scale(1.25);animation:pulse 2s ease infinite}

.bde-tg-label{font-size:clamp(.95rem,2.2vw,1.08rem);font-weight:700;letter-spacing:-.02em;
  color:rgba(240,237,232,.5);transition:color .4s}
.bde-toggle[data-active="true"] .bde-tg-label{color:#f0ede8}

.bde-tg-state{margin-left:auto;font-size:8px;letter-spacing:.16em;text-transform:uppercase;
  font-family:'DM Mono','Courier New',monospace;padding:2px 7px;border-radius:5px;
  opacity:0;transform:scale(.85);transition:opacity .4s .05s,transform .4s .05s}
.bde-toggle[data-active="true"][data-frame="breed"] .bde-tg-state{
  opacity:1;transform:none;color:rgba(240,237,232,.62);background:rgba(240,237,232,.09)}
.bde-toggle[data-active="true"][data-frame="individual"] .bde-tg-state{
  opacity:1;transform:none;color:#c97bff;background:rgba(201,123,255,.14)}

.bde-tg-verdict{font-size:11.5px;font-family:'DM Mono','Courier New',monospace;
  line-height:1.45;color:rgba(240,237,232,.28);transition:color .4s}
.bde-toggle[data-active="true"][data-frame="breed"] .bde-tg-verdict{color:rgba(240,237,232,.6)}
.bde-toggle[data-active="true"][data-frame="individual"] .bde-tg-verdict{color:#c97bff}

.bde-main{animation:fadeUp .45s ease}
.bde-cards{display:grid;grid-template-columns:repeat(4,1fr);gap:.65rem;margin-bottom:1rem}
.bde-grid {display:grid;grid-template-columns:1fr 1fr;gap:.65rem;padding:0 0 1rem}
.bde-legend{display:flex;gap:1rem;align-items:center}
.bde-chart{height:272px}

.bde-chartwrap{transition:border-color .55s cubic-bezier(.4,0,.2,1),box-shadow .55s cubic-bezier(.4,0,.2,1)}
.bde-chartwrap[data-frame="individual"]{
  border-color:rgba(201,123,255,.22)!important;
  box-shadow:0 0 36px rgba(201,123,255,.07);
}
.bde-scan{position:absolute;top:0;bottom:0;left:0;width:38%;z-index:3;pointer-events:none;
  background:linear-gradient(90deg,transparent,rgba(201,123,255,.13),transparent);
  transform:translateX(-130%);
  animation:scanSweep .95s cubic-bezier(.33,0,.2,1) 1 forwards}
@keyframes scanSweep{to{transform:translateX(330%)}}

.bde-ctx{display:flex;border:1px solid rgba(240,237,232,.08);border-radius:8px;
  overflow-x:auto;margin-bottom:1.4rem;background:rgba(240,237,232,.01);
  scrollbar-width:none;-webkit-overflow-scrolling:touch}
.bde-ctx::-webkit-scrollbar{display:none}
.bde-ctx-item{display:flex;align-items:center;gap:.36rem;padding:.58rem .88rem;
  border-right:1px solid rgba(240,237,232,.08);flex-shrink:0}

@media(max-width:680px){
  .bde-cards{grid-template-columns:repeat(2,1fr)!important}
  .bde-grid {grid-template-columns:1fr!important}
  .bde-chart{height:230px!important}
  .bde-ps{display:none}
  .bde-legend{flex-wrap:wrap;width:100%;gap:.45rem .9rem}
}
@media(max-width:380px){.bde-cards{grid-template-columns:1fr!important}}
`;

// ─────────────────────────────────────────────
//  INTRO
// ─────────────────────────────────────────────
function Intro({ onBegin }) {
  const [p, setP] = useState(0);
  const timers = useRef([]);
  useEffect(() => {
    const add = (fn,ms) => { const t=setTimeout(fn,ms); timers.current.push(t); };
    add(()=>setP(1),200); add(()=>setP(2),750); add(()=>setP(3),1400);
    add(()=>setP(4),2050); add(()=>setP(5),2600); add(onBegin,8000);
    return () => timers.current.forEach(clearTimeout);
  }, [onBegin]);

  const sh = n => ({
    opacity:p>=n?1:0, position:"relative", zIndex:1,
    transform:p>=n?"none":"translateY(13px)",
    transition:"opacity .7s ease,transform .7s ease",
  });

  return (
    <div style={{position:"fixed",inset:0,zIndex:200,
      background:"radial-gradient(ellipse 80% 55% at 50% 44%,#09090f,#000)",
      display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",
      padding:"2rem",textAlign:"center",overflow:"hidden"}}>

      <div aria-hidden style={{
        position:"absolute", top:"50%", left:"50%",
        transform:"translate(-50%,-50%)", pointerEvents:"none",
      }}>
        <img
          src="https://getbarkley.com/images/Barkley_Halo_512x512.png"
          alt=""
          decoding="async"
          onError={(e) => { e.currentTarget.style.display = "none"; }}
          style={{
            width:"min(520px,90vw)", height:"min(520px,90vw)",
            display:"block",
            animation:"haloBreath 4s ease-in-out infinite",
          }}
        />
      </div>

      <div style={{...sh(1),marginBottom:"2.5rem"}}>
        <div aria-hidden style={{width:8,height:8,borderRadius:"50%",margin:"0 auto",
          background:C.teal,boxShadow:`0 0 18px ${C.teal}`,animation:"pulse 2.2s ease infinite"}}/>
      </div>

      <h1 style={{...sh(2),fontFamily:SANS,fontWeight:700,color:C.white,
        fontSize:"clamp(1.65rem,5.2vw,3.3rem)",letterSpacing:"-0.035em",
        lineHeight:1.08,margin:"0 0 1.2rem",maxWidth:580}}>
        Breed models miss what{" "}
        <span style={{background:"linear-gradient(128deg,#7b9fff,#c97bff)",
          WebkitBackgroundClip:"text",WebkitTextFillColor:"transparent"}}>
          individual baselines
        </span>{" "}reveal.
      </h1>

      <p style={{...sh(3),fontFamily:SANS,fontSize:"clamp(13px,2vw,15px)",
        color:C.dim,lineHeight:1.7,margin:"0 0 1.3rem",maxWidth:360}}>
        Same dog.&ensp;Same data.&ensp;Different reference frame.
      </p>

      <div style={{...sh(4),display:"inline-flex",alignItems:"center",gap:"0.5rem",
        padding:"0.32rem 0.82rem",border:"1px solid rgba(123,159,255,.22)",
        borderRadius:100,background:"rgba(123,159,255,.07)",marginBottom:"2.4rem"}}>
        <div aria-hidden style={{width:5,height:5,borderRadius:"50%",
          background:C.teal,boxShadow:`0 0 8px ${C.teal}`,animation:"pulse 2s infinite"}}/>
        <span style={{fontSize:11,fontFamily:MONO,color:"rgba(123,159,255,.82)",letterSpacing:"0.04em"}}>
          {DOG.name} · {DOG.breed} · Monitoring
        </span>
      </div>

      <button className="bde-ibtn" onClick={onBegin}
        aria-label="Begin the behavioral intelligence demo"
        style={{...sh(5),fontFamily:SANS,fontSize:13,fontWeight:600,
          padding:"0.72rem 2rem",border:"1px solid rgba(240,237,232,.22)",
          borderRadius:8,background:"rgba(240,237,232,.06)",color:C.white,
          cursor:"pointer",transition:"background .2s"}}>
        Begin →
      </button>

      <p aria-hidden style={{position:"absolute",bottom:"1.4rem",fontSize:9,
        fontFamily:MONO,color:C.ghost,letterSpacing:"0.12em",textTransform:"uppercase"}}>
        Barkley · Proof of Usefulness · HackerNoon 2026
      </p>
    </div>
  );
}

// ─────────────────────────────────────────────
//  PROFILE BANNER
// ─────────────────────────────────────────────
function ProfileBanner({ isBreed }) {
  return (
    <div style={{display:"flex",alignItems:"center",gap:"1rem",
      padding:"1.2rem 0 1.25rem",borderBottom:`1px solid ${C.line}`,flexWrap:"wrap"}}>
      <div aria-hidden style={{width:40,height:40,borderRadius:"50%",flexShrink:0,
        background:"linear-gradient(135deg,rgba(123,159,255,.2),rgba(201,123,255,.15))",
        border:"1px solid rgba(123,159,255,.22)",display:"flex",alignItems:"center",
        justifyContent:"center",fontSize:15,fontWeight:700,color:C.blue,fontFamily:SANS}}>
        K
      </div>
      <div style={{flex:1,minWidth:0}}>
        <div style={{fontSize:"clamp(1rem,2.5vw,1.1rem)",fontWeight:700,
          letterSpacing:"-0.02em",color:C.white,marginBottom:"0.15rem",fontFamily:SANS}}>
          {DOG.name}
        </div>
        <div style={{fontSize:11,color:C.muted,fontFamily:MONO,lineHeight:1.4}}>
          {DOG.breed} · {DOG.age} · 90-day monitoring window
        </div>
      </div>
      <div className="bde-ps" style={{display:"flex",flexDirection:"column",alignItems:"flex-end",gap:"0.28rem"}}>
        <div style={{display:"flex",alignItems:"center",gap:"0.38rem"}}>
          <div aria-hidden style={{width:5,height:5,borderRadius:"50%",
            background:isBreed?C.teal:C.pink,boxShadow:`0 0 7px ${isBreed?C.teal:C.pink}`,
            animation:"pulse 2s infinite",transition:"background .4s,box-shadow .4s"}}/>
          <span style={{fontSize:10.5,fontFamily:MONO,letterSpacing:"0.06em",
            color:isBreed?"rgba(63,214,188,.78)":C.pink,transition:"color .4s"}}>
            {isBreed?"Monitoring · No anomaly":"Monitoring · Drift signal"}
          </span>
        </div>
        <span style={{fontSize:9,fontFamily:MONO,color:C.ghost,letterSpacing:"0.07em"}}>
          Synthetic prototype profile
        </span>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
//  TOOLTIP
// ─────────────────────────────────────────────
function BTooltip({ active, payload, view }) {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  if (!d) return null;
  const base = {background:C.s1,borderRadius:9,padding:"10px 14px",fontFamily:SANS,maxWidth:230,pointerEvents:"none"};

  if (d.silent) return (
    <div style={{...base,border:"1px solid rgba(63,214,188,.3)"}}>
      <p style={{color:C.teal,fontSize:9.5,fontWeight:700,letterSpacing:"0.1em",textTransform:"uppercase",marginBottom:5}}>
        Informative Absence
      </p>
      <p style={{color:C.dim,fontSize:12,lineHeight:1.55,marginBottom:6}}>
        Day {d.day} · classified, not deleted.
      </p>
      <div style={{height:1,background:"rgba(63,214,188,.12)",marginBottom:6}}/>
      <p style={{color:"rgba(63,214,188,.72)",fontSize:11.5,lineHeight:1.5,fontStyle:"italic"}}>
        {d.sMeta?.owner ?? "This may reflect context, rest, withdrawal, or device removal."}
      </p>
    </div>
  );

  if (d.value == null) return null;
  return (
    <div style={{...base,border:`1px solid ${C.line}`}}>
      <p style={{color:C.muted,fontSize:9.5,marginBottom:4,fontFamily:MONO}}>Day {d.day}</p>
      <p style={{color:C.white,fontSize:14,fontWeight:700}}>Score {Math.round(d.value)}</p>
      <p style={{fontSize:11,marginTop:3,color:view==="individual"?C.pink:C.muted}}>
        {view==="individual"
          ? `${d.value<BASELINE?"↓":"↑"}${Math.abs(Math.round(d.value-BASELINE))} from ${DOG.name}'s baseline`
          : `Breed range ${BREED_MU-BREED_SIG}–${BREED_MU+BREED_SIG} · within norm`}
      </p>
    </div>
  );
}

// ─────────────────────────────────────────────
//  CARD
// ─────────────────────────────────────────────
function Card({ label, val, sub, insight, accent, pulse=false, animDelay=0, animated=false }) {
  return (
    <div style={{borderRadius:10,border:"1px solid rgba(240,237,232,.09)",
      borderLeft:`2px solid ${accent}`,padding:"1rem 1.1rem",background:C.s1,
      fontFamily:SANS,display:"flex",flexDirection:"column",
      ...(animated?{animation:`cardIn .48s ${animDelay}ms ease both`}:{})}}>
      <div>
        <div style={{display:"flex",alignItems:"center",gap:"0.4rem",marginBottom:"0.45rem"}}>
          <div aria-hidden style={{width:5,height:5,borderRadius:"50%",flexShrink:0,background:accent,
            boxShadow:pulse&&animated?`0 0 7px ${accent}`:"none",
            animation:pulse&&animated?"pulse 1.9s ease infinite":"none"}}/>
          <span style={{fontSize:9.5,textTransform:"uppercase",letterSpacing:"0.1em",color:C.muted,fontFamily:MONO}}>
            {label}
          </span>
        </div>
        <div style={{fontSize:"clamp(.86rem,2.2vw,1.18rem)",fontWeight:700,
          letterSpacing:"-0.02em",color:accent,marginBottom:"0.2rem",fontFamily:MONO}}>
          {val}
        </div>
        <div style={{fontSize:10.5,color:C.muted,lineHeight:1.45}}>{sub}</div>
      </div>
      {insight && (<>
        <div style={{height:1,background:C.line,margin:"0.7rem 0 0.6rem"}}/>
        <p style={{fontSize:12,color:C.dim,lineHeight:1.55,fontStyle:"italic"}}>"{insight}"</p>
      </>)}
    </div>
  );
}

// ─────────────────────────────────────────────
//  MICRO COMPONENTS
// ─────────────────────────────────────────────
function LI({ color, label, type }) {
  const mk = {
    band:<div aria-hidden style={{width:13,height:7,borderRadius:2,background:color,border:`1px solid ${color}`}}/>,
    line:<div aria-hidden style={{width:14,height:2,background:color,borderRadius:2}}/>,
    dash:<div aria-hidden style={{width:14,height:0,borderTop:`1.5px dashed ${color}`}}/>,
    dot: <div aria-hidden style={{width:7,height:7,borderRadius:"50%",border:`1.5px solid ${color}`,boxShadow:`0 0 5px ${color}`}}/>,
  }[type];
  return (
    <div style={{display:"flex",alignItems:"center",gap:"0.35rem"}}>
      {mk}
      <span style={{fontSize:9.5,color:C.muted,fontFamily:MONO}}>{label}</span>
    </div>
  );
}

function CtrlBtn({ children, onClick, disabled, active, activeColor }) {
  return (
    <button className="bde-ctrl" onClick={onClick} disabled={disabled} aria-pressed={active}
      style={{padding:"0.36rem 0.8rem",fontSize:11.5,fontWeight:500,fontFamily:SANS,
        border:`1px solid ${active?`${activeColor}55`:"rgba(240,237,232,.14)"}`,
        borderRadius:6,background:"transparent",
        color:active?activeColor:C.muted,cursor:disabled?"default":"pointer",
        display:"flex",alignItems:"center",gap:"0.3rem",
        transition:"color .2s,border-color .2s",opacity:disabled?.4:1}}>
      {children}
    </button>
  );
}

function CTALink({ href, children, variant="ghost" }) {
  const S = {
    primary:{background:C.white,                color:"#000",border:"none"},
    accent: {background:"rgba(123,159,255,.1)", color:C.blue,border:"1px solid rgba(123,159,255,.28)"},
    ghost:  {background:"transparent",          color:C.dim, border:"1px solid rgba(240,237,232,.14)"},
  }[variant];
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" className="bde-link"
      style={{...S,padding:"0.62rem 1.4rem",fontSize:12.5,fontWeight:600,fontFamily:SANS,
        borderRadius:8,textDecoration:"none",display:"inline-block",transition:"opacity .2s"}}>
      {children}
    </a>
  );
}

// ─────────────────────────────────────────────
//  MAIN
// ─────────────────────────────────────────────
export default function BarkleyDriftExplorer() {
  const [showIntro, setShowIntro] = useState(true);
  const [view,      setView]      = useState("breed");
  const [animDays,  setAnimDays]  = useState(90);
  const [playing,   setPlaying]   = useState(false);
  const [showCtx,   setShowCtx]   = useState(true);
  const [cardKey,   setCardKey]   = useState(0);

  const isBreed = view === "breed";
  const data    = useMemo(() => DATA.slice(0, animDays), [animDays]);
  const cards   = isBreed ? BREED_CARDS : INDIV_CARDS;

  const handleBegin     = useCallback(() => setShowIntro(false), []);
  const handleReplay    = useCallback(() => { setAnimDays(1); setPlaying(true); }, []);
  const handleToggleCtx = useCallback(() => setShowCtx(p => !p), []);
  const switchView      = useCallback((v) => {
    setView(v);
    if (v === "individual") setCardKey(k => k + 1);
  }, []);

  useEffect(() => {
    if (!playing) return;
    if (animDays >= 90) { setPlaying(false); return; }
    const ms = animDays < DRIFT_DAY ? 36 : animDays < 65 ? 50 : 65;
    const t = setTimeout(() => setAnimDays(p => p + 1), ms);
    return () => clearTimeout(t);
  }, [playing, animDays]);

  if (showIntro) return <><style>{CSS}</style><Intro onBegin={handleBegin}/></>;

  return (
    <>
      <style>{CSS}</style>
      <div className="bde-main" style={{minHeight:"100vh",background:C.bg,color:C.white,fontFamily:SANS}}>

        {/* HEADER */}
        <header style={{padding:"1.4rem 2rem",borderBottom:`1px solid ${C.line}`,
          display:"flex",alignItems:"center",justifyContent:"space-between",flexWrap:"wrap",gap:"0.75rem"}}>
          <div style={{display:"flex",alignItems:"center",gap:"0.65rem"}}>
            <div aria-hidden style={{width:7,height:7,borderRadius:"50%",
              background:C.teal,boxShadow:`0 0 10px ${C.teal}`,animation:"pulse 2.2s ease infinite"}}/>
            <img
              src="https://getbarkley.com/images/Barkley_Logo.png"
              alt="Barkley AI"
              decoding="async"
              onError={(e) => {
                e.currentTarget.style.display = "none";
                const fb = e.currentTarget.nextElementSibling;
                if (fb) fb.style.display = "inline";
              }}
              style={{ height:"100px", display:"block" }}
            />
            <span style={{display:"none",fontWeight:700,fontSize:"1.05rem",letterSpacing:"-0.02em",color:C.white}}>
              Barkley.
            </span>
            <span style={{fontSize:9.5,color:C.muted,fontFamily:MONO,letterSpacing:"0.07em",
              borderLeft:`1px solid ${C.line}`,paddingLeft:"0.65rem"}}>
              Drift Explorer
            </span>
          </div>
          <div style={{display:"flex",gap:"0.45rem",alignItems:"center"}}>
            <CtrlBtn onClick={handleToggleCtx} active={showCtx} activeColor={C.amber}>◈ Context</CtrlBtn>
            <CtrlBtn onClick={handleReplay} disabled={playing}>
              {playing
                ? <span style={{display:"flex",alignItems:"center",gap:"0.3rem"}}>
                    <span aria-hidden style={{width:5,height:5,borderRadius:"50%",background:C.teal,
                      display:"inline-block",animation:"pulse .8s infinite"}}/>
                    Day {animDays}
                  </span>
                : "↺ Replay 90 days"}
            </CtrlBtn>
          </div>
        </header>

        <main style={{maxWidth:1040,margin:"0 auto",padding:"0 1.5rem"}}>

          {/* PROFILE */}
          <ProfileBanner isBreed={isBreed}/>

          {/* FRAMING */}
          <p style={{
            fontSize:11.5, color:C.muted, fontFamily:SANS, lineHeight:1.55,
            padding:"0.9rem 0 0",
          }}>
            Same dog, same data — two reference frames.{" "}
            <span style={{color:C.dim}}>This is why individual baselines matter.</span>
          </p>

          {/* TOGGLE */}
          <div className="bde-tg-eyebrow">
            Same dog · same data — <b>switch the reference frame</b>
          </div>
          <div className="bde-grid" role="group" aria-label="Select comparison reference frame">

            <button className="bde-toggle" data-frame="breed" data-active={isBreed}
              onClick={() => switchView("breed")} aria-pressed={isBreed}>
              <div className="bde-tg-head">
                <span className="bde-tg-dot" aria-hidden />
                <span className="bde-tg-label">Breed Average</span>
                <span className="bde-tg-state" aria-hidden>Active</span>
              </div>
              <p className="bde-tg-verdict">
                {isBreed
                  ? "Everything looks normal for a Jack Russell."
                  : "Population reference frame"}
              </p>
            </button>

            <button className="bde-toggle" data-frame="individual" data-active={!isBreed}
              onClick={() => switchView("individual")} aria-pressed={!isBreed}>
              <div className="bde-tg-head">
                <span className="bde-tg-dot" aria-hidden />
                <span className="bde-tg-label">{DOG.name}'s Baseline</span>
                <span className="bde-tg-state" aria-hidden>Active</span>
              </div>
              <p className="bde-tg-verdict">
                {!isBreed
                  ? `${DOG.name} is drifting from their own baseline.`
                  : "Individual reference frame"}
              </p>
            </button>
          </div>

          {/* STATUS BANNER */}
          <div role="status" aria-live="polite"
            style={{padding:"0.9rem 1.3rem",marginBottom:"1rem",
              border:`1px solid ${isBreed?"rgba(240,237,232,.1)":"rgba(201,123,255,.28)"}`,
              borderRadius:10,
              background:isBreed?"rgba(240,237,232,.02)":"rgba(201,123,255,.05)",
              display:"flex",alignItems:"flex-start",gap:"0.85rem",
              transition:"border-color .4s,background .4s"}}>
            <div aria-hidden style={{width:8,height:8,borderRadius:"50%",flexShrink:0,marginTop:3,
              background:isBreed?"rgba(240,237,232,.42)":C.pink,
              boxShadow:isBreed?"none":`0 0 10px ${C.pink}`,
              transition:"background .4s,box-shadow .4s"}}/>
            <div>
              <p style={{fontSize:11,fontWeight:700,letterSpacing:"0.07em",textTransform:"uppercase",
                fontFamily:MONO,marginBottom:2,color:isBreed?C.muted:C.pink,transition:"color .4s"}}>
                {isBreed?"No population-level anomaly detected.":"Behavioral drift signal detected."}
              </p>
              <p style={{fontSize:12,color:C.muted,lineHeight:1.55}}>
                {isBreed
                  ?`${DOG.name} remains within expected ranges for a ${DOG.breed}.`
                  :`${DOG.name}'s individual baseline reveals a pattern invisible to breed averages.`}
              </p>
            </div>
          </div>

          {/* CHART */}
          <div className="bde-chartwrap" data-frame={view}
            style={{border:`1px solid ${C.line}`,borderRadius:12,background:C.s1,
            padding:"1.2rem .5rem .7rem",marginBottom:"1rem",position:"relative",overflow:"hidden"}}>
            <div aria-hidden style={{position:"absolute",inset:0,zIndex:0,pointerEvents:"none",
              backgroundImage:"radial-gradient(circle,rgba(240,237,232,.036) 1px,transparent 1px)",
              backgroundSize:"32px 32px"}}/>
            <div aria-hidden style={{position:"absolute",top:0,left:0,right:0,height:36,
              zIndex:1,pointerEvents:"none",
              background:"linear-gradient(to bottom,rgba(6,6,10,.9),transparent)"}}/>
            {!isBreed && <div key={`scan-${cardKey}`} className="bde-scan" aria-hidden/>}

            <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",
              padding:"0 1.3rem .85rem",position:"relative",zIndex:2,flexWrap:"wrap",gap:"0.5rem"}}>
              <span style={{fontSize:9.5,fontFamily:MONO,letterSpacing:"0.08em",textTransform:"uppercase",color:C.muted}}>
                {DOG.name}'s behavioral activity score · {isBreed?"Breed frame":"Individual frame"}
              </span>
              <div className="bde-legend">
                {isBreed?(<>
                  <LI color="rgba(240,237,232,.18)" label="Breed ±1σ" type="band"/>
                  <LI color="rgba(240,237,232,.72)" label={DOG.name}  type="line"/>
                </>):(<>
                  <LI color={C.blue} label="Baseline" type="dash"/>
                  <LI color={C.blue} label="Stable"   type="line"/>
                  <LI color={C.pink} label="Drift"    type="line"/>
                  <LI color={C.teal} label="Silence"  type="dot"/>
                </>)}
              </div>
            </div>

            <div
              className="bde-chart"
              style={{position:"relative",zIndex:2}}
              role="img"
              aria-label={isBreed
                ? `${DOG.name}'s 90-day activity stays within the breed normal band. No anomaly is visible at the population level.`
                : `${DOG.name}'s 90-day activity drifts downward from their own baseline of ${BASELINE} after day ${DRIFT_DAY}, with three silence periods. The drift is invisible to the breed average.`}
            >
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={data} margin={{top:4,right:64,bottom:2,left:0}}>
                  <XAxis dataKey="day" tickLine={false}
                    axisLine={{stroke:"rgba(240,237,232,.08)"}}
                    tick={{fill:C.muted,fontSize:9.5,fontFamily:MONO}}
                    tickFormatter={v=>(v===1||v%15===0)?`D${v}`:""}
                    interval={0}/>
                  <YAxis domain={[30,110]} tickLine={false} axisLine={false} tickCount={5}
                    tick={{fill:C.muted,fontSize:9.5,fontFamily:MONO}}/>
                  <Tooltip content={<BTooltip view={view}/>}
                    cursor={{stroke:"rgba(240,237,232,.07)",strokeDasharray:"4 4",strokeWidth:1}}
                    isAnimationActive={false}/>

                  <ReferenceArea y1={BREED_MU-BREED_SIG} y2={BREED_MU+BREED_SIG}
                    fill={isBreed?"rgba(240,237,232,.05)":"rgba(240,237,232,.022)"}
                    stroke={isBreed?"rgba(240,237,232,.1)":"rgba(240,237,232,.045)"}
                    strokeWidth={1} ifOverflow="extendDomain"/>

                  {SIL_SPANS.map((r,i)=>(
                    <ReferenceArea key={i} x1={r.x1} x2={r.x2}
                      fill="rgba(63,214,188,.07)" stroke="rgba(63,214,188,.22)" strokeWidth={1} ifOverflow="extendDomain"/>
                  ))}

                  {showCtx&&CTX_EVENTS.filter(e=>e.day<=animDays).map(ev=>(
                    <ReferenceLine key={ev.label} x={ev.day} stroke={ev.color}
                      strokeWidth={1} strokeDasharray="3 5"
                      label={{value:ev.short,position:"insideTop",fill:ev.color,fontSize:11,fontFamily:MONO}}/>
                  ))}

                  {isBreed&&<ReferenceLine y={BREED_MU} stroke="rgba(240,237,232,.2)"
                    strokeDasharray="5 4" strokeWidth={1.5}
                    label={{value:`μ ${BREED_MU}`,position:"right",fill:C.muted,fontSize:9.5,fontFamily:MONO}}/>}
                  {!isBreed&&<ReferenceLine y={BASELINE} stroke="rgba(123,159,255,.55)"
                    strokeDasharray="5 4" strokeWidth={1.5}
                    label={{value:`Baseline ${BASELINE}`,position:"right",fill:"rgba(123,159,255,.7)",fontSize:9.5,fontFamily:MONO}}/>}
                  {!isBreed&&animDays>DRIFT_DAY&&<ReferenceLine x={DRIFT_DAY+1}
                    stroke="rgba(201,123,255,.2)" strokeWidth={1} strokeDasharray="2 4"/>}

                  {isBreed&&(<>
                    <Line dataKey="value" stroke="rgba(240,237,232,.09)" strokeWidth={5} dot={false} connectNulls={false} isAnimationActive={false}/>
                    <Line dataKey="value" stroke="rgba(240,237,232,.75)" strokeWidth={2} dot={false} connectNulls={false} isAnimationActive={false}/>
                  </>)}
                  {!isBreed&&(<>
                    <Line dataKey="stableVal" stroke="rgba(123,159,255,.11)" strokeWidth={5} dot={false} connectNulls={false} isAnimationActive={false}/>
                    <Line dataKey="stableVal" stroke={C.blue} strokeWidth={2.5} dot={false} connectNulls={false} isAnimationActive={false}/>
                    <Line key={`drift-glow-${cardKey}`} dataKey="driftVal" stroke="rgba(201,123,255,.11)" strokeWidth={5}
                      dot={false} connectNulls={false}
                      isAnimationActive={!playing} animationDuration={900} animationEasing="ease-out"/>
                    <Line key={`drift-${cardKey}`} dataKey="driftVal" stroke={C.pink} strokeWidth={2.6}
                      dot={false} connectNulls={false}
                      isAnimationActive={!playing} animationDuration={900} animationEasing="ease-out"/>
                  </>)}
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            {playing&&(
              <div aria-hidden style={{margin:"0.4rem 1.3rem 0",height:2,
                background:"rgba(240,237,232,.06)",borderRadius:2,overflow:"hidden"}}>
                <div style={{height:"100%",width:`${(animDays/90)*100}%`,
                  background:`linear-gradient(90deg,${C.blue},${C.pink})`,
                  borderRadius:2,transition:"width .05s linear"}}/>
              </div>
            )}

            <p style={{
              padding:"0.7rem 1.3rem 0", fontSize:9, fontFamily:MONO,
              color:C.ghost, letterSpacing:"0.1em", textTransform:"uppercase",
            }}>
              Synthetic data · prototype visualization
            </p>
          </div>

          {/* CARDS */}
          <div key={`cards-${view}-${cardKey}`} className="bde-cards">
            {cards.map((c,i)=>(
              <Card key={i} {...c} animDelay={!isBreed?i*145:0} animated={!isBreed}/>
            ))}
          </div>

          {/* CONTEXT LEGEND */}
          {showCtx&&(
            <div className="bde-ctx" role="list" aria-label="Context events legend">
              {[
                {color:"rgba(240,237,232,.2)",label:"Breed ±1σ",dot:"rect"},
                ...CTX_EVENTS.map(e=>({color:e.color,label:e.label,dot:"sq"})),
                {color:C.teal,label:"Silence · informative absence",dot:"circ"},
              ].map((e,i)=>(
                <div key={i} className="bde-ctx-item" role="listitem">
                  {e.dot==="rect"
                    ?<div aria-hidden style={{width:10,height:6,background:e.color,borderRadius:2,flexShrink:0}}/>
                    :e.dot==="circ"
                      ?<div aria-hidden style={{width:7,height:7,borderRadius:"50%",border:`1.5px solid ${e.color}`,flexShrink:0}}/>
                      :<div aria-hidden style={{width:8,height:8,borderRadius:2,background:e.color,opacity:.75,flexShrink:0}}/>}
                  <span style={{fontSize:9.5,color:C.muted,fontFamily:MONO,whiteSpace:"nowrap"}}>{e.label}</span>
                </div>
              ))}
            </div>
          )}

          {/* INDIVIDUAL CALLOUT */}
          {!isBreed&&(
            <div role="complementary" aria-label="Behavioral drift insight"
              style={{border:"1px solid rgba(201,123,255,.22)",borderRadius:10,
                padding:"1.2rem 1.6rem",background:"rgba(201,123,255,.04)",
                marginBottom:"1.6rem",animation:"cardIn .5s .75s ease both"}}>
              <p style={{fontSize:9,textTransform:"uppercase",letterSpacing:"0.12em",
                color:C.pink,fontFamily:MONO,marginBottom:"0.5rem"}}>
                Barkley · {DOG.name}'s individual signal
              </p>
              <p style={{fontSize:"clamp(.88rem,1.8vw,1rem)",fontWeight:600,
                letterSpacing:"-0.015em",color:C.white,marginBottom:"0.45rem",lineHeight:1.45}}>
                The breed model sees no problem.
              </p>
              <p style={{fontSize:12.5,color:C.dim,lineHeight:1.72,maxWidth:520}}>
                {DOG.name}'s own baseline reveals something the breed average can't: six weeks of quiet change —
                less movement, slower recovery, more absence. Not alarming. A pattern worth knowing.
              </p>
            </div>
          )}

          {/* CTA FOOTER */}
          <footer style={{border:`1px solid ${C.line}`,borderRadius:12,padding:"2.2rem",
            background:C.s1,textAlign:"center",marginBottom:"2.5rem"}}>
            <p style={{fontSize:9,textTransform:"uppercase",letterSpacing:"0.15em",
              color:C.ghost,fontFamily:MONO,marginBottom:"0.85rem"}}>
              Barkley AI · Applied Research · Pre-Seed
            </p>
            <h2 style={{fontSize:"clamp(1.2rem,3vw,1.85rem)",fontWeight:700,
              letterSpacing:"-0.025em",lineHeight:1.1,margin:"0 0 0.65rem"}}>
              Because your dog is{" "}
              <span style={{background:`linear-gradient(128deg,${C.blue},${C.pink})`,
                WebkitBackgroundClip:"text",WebkitTextFillColor:"transparent"}}>
                not an average.
              </span>
            </h2>
            <p style={{fontSize:13,color:C.muted,lineHeight:1.72,maxWidth:400,margin:"0 auto 1.8rem"}}>
              Individual baselines. Longitudinal modeling. Behavioral drift detection.
              The infrastructure to understand one dog at a time.
            </p>
            <div style={{display:"flex",gap:"0.6rem",justifyContent:"center",flexWrap:"wrap"}}>
              <CTALink href="https://github.com/labs-barkley/barkley-canine-cognition-lab"                              variant="ghost"  >◎ View GitHub</CTALink>
              <CTALink href="https://huggingface.co/datasets/labs-barkley/synthetic-doggraph-sample/tree/main"         variant="accent" >⬡ Explore Dataset</CTALink>
              <CTALink href="https://tally.so/r/2EOgWe"                                                                variant="primary">→ Join Waitlist</CTALink>
            </div>

            {/* Reference Architecture — link */}
            <p style={{marginTop:"0.85rem",fontSize:10,fontFamily:MONO,color:C.ghost}}>
              Explore the computational backbone →{" "}
              <a
                href="https://github.com/labs-barkley/barkley-reference-architecture"
                target="_blank"
                rel="noopener noreferrer"
                style={{color:"rgba(123,159,255,.6)",textDecoration:"none"}}
              >
                Barkley Reference Architecture
              </a>
            </p>

            <p style={{marginTop:"1.2rem",fontSize:9.5,fontFamily:MONO,color:C.ghost}}>
              Not a diagnostic tool · Synthetic data only · Prototype visualization · © 2026 Barkley AI. All rights reserved.
            </p>
          </footer>

        </main>
      </div>
    </>
  );
}
