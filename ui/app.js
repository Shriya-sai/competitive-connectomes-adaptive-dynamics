const state = { data: null, response: null, progress: 0, playing: false, last: 0 };
const canvas = document.getElementById("brain");
const ctx = canvas.getContext("2d");
const controls = Object.fromEntries(["condition", "site", "amplitude", "duration"].map(id => [id, document.getElementById(id)]));

function option(select, value, label = value) {
  const item = document.createElement("option"); item.value = value; item.textContent = label; select.append(item);
}
function unique(key) { return [...new Set(state.data.responses.map(item => item[key]))]; }
function setup() {
  unique("condition").forEach(value => option(controls.condition, value, value.replaceAll("-", " ")));
  unique("site").forEach(value => option(controls.site, value, value.replace("_", " ")));
  unique("amplitude").sort((a,b)=>a-b).forEach(value => option(controls.amplitude, value, `${Number(value) > 0 ? "+" : ""}${value} Δa`));
  unique("duration_seconds").sort((a,b)=>a-b).forEach(value => option(controls.duration, value, `${value} seconds`));
  controls.condition.value = "fitted-signed"; controls.site.value = "central_A"; controls.amplitude.value = "0.03"; controls.duration.value = "7.2";
  selectResponse(); resize(); requestAnimationFrame(frame);
  document.getElementById("status-text").textContent = "Frozen confirmation loaded";
  document.getElementById("status-dot").style.background = "var(--coop)";
}
function selectResponse() {
  state.response = state.data.responses.find(item => item.condition === controls.condition.value && item.site === controls.site.value && item.amplitude === Number(controls.amplitude.value) && item.duration_seconds === Number(controls.duration.value));
  const m = state.response.metrics;
  document.getElementById("direct").textContent = m.direct_response.toPrecision(3);
  document.getElementById("propagation").textContent = m.propagation.toPrecision(3);
  document.getElementById("reconfiguration").textContent = m.phase_reconfiguration.toPrecision(3);
  document.getElementById("recovery").textContent = `${m.recovery_time_seconds.toFixed(1)} s`;
  state.progress = 0; state.playing = true;
}
function resize() { const dpr = devicePixelRatio || 1; const box = canvas.getBoundingClientRect(); canvas.width = box.width*dpr; canvas.height = box.height*dpr; ctx.setTransform(dpr,0,0,dpr,0,0); }
function brainOutline(w,h) {
  ctx.save(); ctx.translate(w/2,h/2); ctx.strokeStyle="#2b4540"; ctx.lineWidth=1.2; ctx.fillStyle="rgba(33,61,56,.16)";
  [-1,1].forEach(side => { ctx.beginPath(); ctx.moveTo(side*8,-h*.37); ctx.bezierCurveTo(side*w*.22,-h*.46,side*w*.43,-h*.22,side*w*.38,h*.08); ctx.bezierCurveTo(side*w*.34,h*.36,side*w*.11,h*.43,side*8,h*.33); ctx.closePath(); ctx.fill(); ctx.stroke(); }); ctx.restore();
}
function draw(progress) {
  const w=canvas.clientWidth,h=canvas.clientHeight; ctx.clearRect(0,0,w,h); brainOutline(w,h);
  const nodes=state.data.nodes.map(n=>({...n,px:n.x*w,py:(.05+n.y*.88)*h}));
  const byId=Object.fromEntries(nodes.map(n=>[n.id,n])); const targetSet=new Set(state.data.site_sets[controls.site.value]);
  const condition=controls.condition.value; const showPos=condition!=="competitive-only"&&condition!=="uncoupled"; const showNeg=condition!=="cooperative-only"&&condition!=="uncoupled";
  state.data.edges.forEach(edge=>{ if((edge.weight>0&&!showPos)||(edge.weight<0&&!showNeg))return; const a=byId[edge.source],b=byId[edge.target]; const active=Math.max(state.response.regional_response[edge.source],state.response.regional_response[edge.target]); ctx.globalAlpha=.035+Math.min(.22,active*15*progress); ctx.strokeStyle=edge.weight>0?"#61e6ad":"#ff7085"; ctx.lineWidth=.35+Math.min(1.3,Math.abs(edge.weight)*8); ctx.beginPath();ctx.moveTo(a.px,a.py);ctx.lineTo(b.px,b.py);ctx.stroke(); }); ctx.globalAlpha=1;
  const max=Math.max(...state.response.regional_response,1e-8);
  nodes.forEach(node=>{ const response=state.response.regional_response[node.id]/max; const target=targetSet.has(node.id); const delay=target?0:(.12+Math.abs(node.x-.5)*.35); const envelope=Math.max(0,Math.min(1,(progress-delay)*2.8)); const pulse=response*envelope; const radius=target?5.5:2.3+7*pulse; ctx.beginPath();ctx.arc(node.px,node.py,radius,0,Math.PI*2); ctx.fillStyle=target?"#ffd166":pulse>.35?"#8ff0c7":"#71938a"; ctx.globalAlpha=target?.95:.42+.5*pulse; ctx.fill(); if(pulse>.18){ctx.strokeStyle=`rgba(97,230,173,${.55*pulse})`;ctx.lineWidth=1;ctx.beginPath();ctx.arc(node.px,node.py,radius+5+5*Math.sin(progress*12+node.id),0,Math.PI*2);ctx.stroke();} });ctx.globalAlpha=1;
}
function frame(time){ if(state.playing){ if(!state.last)state.last=time; state.progress+=Math.min(.025,(time-state.last)/5200); if(state.progress>=1){state.progress=1;state.playing=false;} state.last=time;} else state.last=time; draw(state.progress); document.getElementById("phase").textContent=state.progress===0?"Ready":state.progress<.24?"Local response":state.progress<.78?"Network propagation":state.progress<1?"Reconfiguration":"Response peak"; requestAnimationFrame(frame); }
document.getElementById("apply").addEventListener("click",selectResponse);
document.getElementById("pause").addEventListener("click",event=>{state.playing=!state.playing;event.currentTarget.textContent=state.playing?"Pause playback":"Resume playback";});
Object.values(controls).forEach(control=>control.addEventListener("change",()=>{state.playing=false;state.progress=0;selectResponse();}));
addEventListener("resize",resize);
fetch("data/brain-dynamics-demo.json").then(response=>response.json()).then(data=>{state.data=data;setup();}).catch(error=>{document.getElementById("status-text").textContent=`Could not load data: ${error.message}`;});
