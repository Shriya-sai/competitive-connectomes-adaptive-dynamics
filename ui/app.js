const state = { data: null, trajectories: null, response: null, trajectory: null, frame: 0, playhead: 0, playing: false, last: 0 };
const PLAYBACK_SPEED = 8;
const canvas = document.getElementById("brain");
const ctx = canvas.getContext("2d");
const controls = Object.fromEntries(["condition", "site", "amplitude", "duration"].map(id => [id, document.getElementById(id)]));

function option(select, value, label = value) { const item=document.createElement("option"); item.value=value; item.textContent=label; select.append(item); }
function unique(key) { return [...new Set(state.data.responses.map(item => item[key]))]; }
function matching(item) { return item.condition===controls.condition.value && item.site===controls.site.value && item.amplitude===Number(controls.amplitude.value) && item.duration_seconds===Number(controls.duration.value); }
function setup() {
  unique("condition").forEach(value=>option(controls.condition,value,value.replaceAll("-"," ")));
  unique("site").forEach(value=>option(controls.site,value,value.replace("_"," ")));
  unique("amplitude").sort((a,b)=>a-b).forEach(value=>option(controls.amplitude,value,`${Number(value)>0?"+":""}${value} Δa`));
  unique("duration_seconds").sort((a,b)=>a-b).forEach(value=>option(controls.duration,value,`${value} seconds`));
  controls.condition.value="fitted-signed"; controls.site.value="central_A"; controls.amplitude.value="0.03"; controls.duration.value="7.2";
  selectResponse(); resize(); requestAnimationFrame(animate);
  document.getElementById("status-text").textContent="Literal seed-300 trajectory loaded";
  document.getElementById("status-dot").style.background="var(--coop)";
}
function selectResponse() {
  state.response=state.data.responses.find(matching); state.trajectory=state.trajectories.trajectories.find(matching);
  if(!state.response||!state.trajectory) throw new Error("Selected condition is missing from the frozen export");
  const m=state.response.metrics;
  document.getElementById("direct").textContent=m.direct_response.toPrecision(3);
  document.getElementById("propagation").textContent=m.propagation.toPrecision(3);
  document.getElementById("reconfiguration").textContent=m.phase_reconfiguration.toPrecision(3);
  document.getElementById("recovery").textContent=`${m.recovery_time_seconds.toFixed(1)} s`;
  state.frame=0; state.playhead=state.trajectory.times_seconds[0]; state.playing=true; state.last=0; document.getElementById("pause").textContent="Pause playback";
}
function resize(){const dpr=devicePixelRatio||1,box=canvas.getBoundingClientRect();canvas.width=box.width*dpr;canvas.height=box.height*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);}
function brainOutline(w,h){ctx.save();ctx.translate(w/2,h/2);ctx.strokeStyle="#2b4540";ctx.lineWidth=1.2;ctx.fillStyle="rgba(33,61,56,.16)";[-1,1].forEach(side=>{ctx.beginPath();ctx.moveTo(side*8,-h*.37);ctx.bezierCurveTo(side*w*.22,-h*.46,side*w*.43,-h*.22,side*w*.38,h*.08);ctx.bezierCurveTo(side*w*.34,h*.36,side*w*.11,h*.43,side*8,h*.33);ctx.closePath();ctx.fill();ctx.stroke();});ctx.restore();}
function currentValues(){const n=state.trajectories.regions,start=state.frame*n,raw=state.trajectory.values_int16_time_major;return raw.slice(start,start+n).map(value=>value*state.trajectory.scale/32767);}
function draw(){
  const w=canvas.clientWidth,h=canvas.clientHeight;ctx.clearRect(0,0,w,h);brainOutline(w,h);
  const nodes=state.data.nodes.map(n=>({...n,px:n.x*w,py:(.05+n.y*.88)*h})),byId=Object.fromEntries(nodes.map(n=>[n.id,n]));
  const targetSet=new Set(state.data.site_sets[controls.site.value]),condition=controls.condition.value,showPos=condition!=="competitive-only"&&condition!=="uncoupled",showNeg=condition!=="cooperative-only"&&condition!=="uncoupled";
  const values=currentValues(),max=Math.max(...values.map(Math.abs),state.trajectory.scale*.03,1e-12);
  state.data.edges.forEach(edge=>{if((edge.weight>0&&!showPos)||(edge.weight<0&&!showNeg))return;const a=byId[edge.source],b=byId[edge.target];const active=Math.max(Math.abs(values[edge.source]),Math.abs(values[edge.target]))/max;ctx.globalAlpha=.025+.18*active;ctx.strokeStyle=edge.weight>0?"#61e6ad":"#ff7085";ctx.lineWidth=.35+Math.min(1.3,Math.abs(edge.weight)*8);ctx.beginPath();ctx.moveTo(a.px,a.py);ctx.lineTo(b.px,b.py);ctx.stroke();});ctx.globalAlpha=1;
  nodes.forEach(node=>{const value=values[node.id],strength=Math.min(1,Math.abs(value)/max),target=targetSet.has(node.id),radius=(target?4.8:2.3)+7*strength;ctx.beginPath();ctx.arc(node.px,node.py,radius,0,Math.PI*2);ctx.fillStyle=value<0?"#ff7085":value>0?"#61e6ad":"#71938a";ctx.globalAlpha=.38+.58*strength;ctx.fill();if(target){ctx.strokeStyle="#ffd166";ctx.lineWidth=1.8;ctx.globalAlpha=.95;ctx.stroke();}});ctx.globalAlpha=1;
  const time=state.trajectory.times_seconds[state.frame]; document.getElementById("time").textContent=`t = ${time.toFixed(2)} s`;
  document.getElementById("phase").textContent=time<0?"Paired baseline":time<state.trajectory.duration_seconds?"Perturbation on":"Recovery";
}
function animate(time){
  if(state.playing&&state.trajectory){
    if(state.last) state.playhead+=(time-state.last)/1000*PLAYBACK_SPEED;
    const times=state.trajectory.times_seconds;
    if(state.playhead>times[times.length-1]) state.playhead=times[0];
    state.frame=0; while(state.frame+1<times.length&&times[state.frame+1]<=state.playhead) state.frame++;
  }
  state.last=time;if(state.data&&state.trajectory)draw();requestAnimationFrame(animate);
}
document.getElementById("apply").addEventListener("click",selectResponse);
document.getElementById("pause").addEventListener("click",event=>{state.playing=!state.playing;event.currentTarget.textContent=state.playing?"Pause playback":"Resume playback";});
Object.values(controls).forEach(control=>control.addEventListener("change",selectResponse));
addEventListener("resize",resize);
Promise.all([fetch("data/brain-dynamics-demo.json").then(r=>r.json()),fetch("data/brain-dynamics-trajectories.json").then(r=>r.json())]).then(([data,trajectories])=>{state.data=data;state.trajectories=trajectories;setup();}).catch(error=>{document.getElementById("status-text").textContent=`Could not load data: ${error.message}`;});
