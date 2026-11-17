// FINAL SLAUGHTER - boss fight rhythm game. Keys: D F J K (or touch the 4 columns)
const C=document.getElementById('c'),X=C.getContext('2d'),A=document.getElementById('song');
const W=800,H=600;C.width=W;C.height=H;
const START=+new URLSearchParams(location.search).get('start')||0;
// ---- embedded mode: CatnipCauldron opens this fight inside its easter-egg overlay (index.html?embed=1&mv=..&sv=..) ----
const _q=new URLSearchParams(location.search),EMBED=_q.has('embed');
const MV=Math.min(1,Math.max(0,+(_q.get('mv')??1))),SV=Math.min(1,Math.max(0,+(_q.get('sv')??1)));   // music / effects volume from the host game's Settings
let leftEmbed=false;
// ---- embedded count-down: 3, 2, 1, GO! before the song starts (like in FNF) ----
const COUNT_WAIT=1.0,COUNT_STEP=.8,COUNT_LABELS=['3','2','1','GO!'];   // wait for the screen to fade in, then one number every 0.8 s
let countT=0,countBeat=-1,_actx=null;
function beep(freq,dur,gain){   // a soft low thump made with the browser's own sound engine (no file needed)
  if(SV<=0)return;
  try{_actx=_actx||new(window.AudioContext||window.webkitAudioContext)();if(_actx.state==='suspended')_actx.resume();
    const o=_actx.createOscillator(),g=_actx.createGain(),n=_actx.currentTime;
    o.type='sine';o.frequency.setValueAtTime(freq,n);o.frequency.exponentialRampToValueAtTime(freq*.55,n+dur);
    g.gain.setValueAtTime(gain*SV,n);g.gain.exponentialRampToValueAtTime(.001,n+dur);o.connect(g);g.connect(_actx.destination);o.start(n);o.stop(n+dur)}catch(e){}
}
function countUpdate(dt){
  countT+=dt;
  const beat=Math.floor(countT/COUNT_STEP);
  if(countT>=0&&beat!==countBeat&&beat<COUNT_LABELS.length){countBeat=beat;beep(beat<3?110:220,beat<3?.28:.45,beat<3?.35:.5)}
  if(countT>=COUNT_LABELS.length*COUNT_STEP)start();
}
function drawCountdown(){
  if(state!=='count'||countT<0)return;
  const k=Math.min(COUNT_LABELS.length-1,Math.floor(countT/COUNT_STEP)),f=(countT-k*COUNT_STEP)/COUNT_STEP,go=k===COUNT_LABELS.length-1;
  const pop=1+.55*Math.pow(1-Math.min(1,f*3.2),2),a=f>.72?1-(f-.72)/.28:1;
  X.save();X.globalAlpha=Math.max(0,a);
  if(!go)text('GET READY',400,160,24,'#9a8aa8');
  X.translate(400,go?300:305);X.scale(pop,pop);
  X.shadowColor=go?'#ff2a4a':'#c06bff';X.shadowBlur=28;text(COUNT_LABELS[k],0,0,go?120:150,go?'#ff4d6a':'#d9a6ff');
  X.restore();X.shadowBlur=0;
}
function leave(result){if(leftEmbed)return;leftEmbed=true;try{parent.postMessage({type:'egg-result',result},location.origin)}catch(e){}}   // tells the host: 'win' or 'lose'
if(location.search.includes('test')){try{const c=JSON.parse(localStorage.getItem('fs_chart'));if(c)CHART.notes=c}catch(e){}}
const REC=location.search.includes('record');
const KEYS=['KeyD','KeyF','KeyJ','KeyK'],LAB=['D','F','J','K'];
const COL=['#c06bff','#8a3bff','#8a3bff','#c06bff'],LX=[265,355,445,535],HY=500,BASE=420;
const NOTE_SPEED=2.2,mult=NOTE_SPEED; // fixed on purpose: no speed customization in this easter egg
let SPEED=BASE*mult;
const WIN={sick:.075,good:.125,bad:.17};
const img=s=>{const i=new Image();i.src=s;return i};
const bgImg=img('Assets/BG/BG_Main.png');
const POSE=[img('Assets/Hoax/web/Hoax_Pose_1.png'),img('Assets/Hoax/web/Hoax_Pose_2.png')];
const EYES=[img('Assets/Hoax/web/EYES_1.png'),img('Assets/Hoax/web/EYES_2.png')];
// ---- SCENE TIMELINE (seconds into the song) + easy tuning knobs ----
const T_PEEK=71,T_TEXT=30;                // 1:11 Hoax creeps in at the sides, 0:30 creepy texts begin
const T_SLASH=90,T_RAGE=110,T_CALM=131;   // 1:30 slash, 1:50 intensify, 2:11 calm/fade
const SIL_RIM=14;                          // faint rim light on the peeking silhouette (0 = none)
const DIM_PEEK=.3,DIM_HOAX=.42;           // how dark Hoax is (0 = fully lit, 1 = black) while peeking / in the middle
const GAPMAX=380;                         // how far the note bars split apart (px)
const BG_DARK=.86;                         // 0-1, how much the bg is darkened (higher = darker)
const FADE_END_PAD=3;                     // fully black this many sec before song ends
// ---- SOUNDS ----
const SFX_SLASH=new Audio('Assets/Sound Fx/slash_boosted.wav'),SFX_DEATH=new Audio('Assets/Sound Fx/Death_SoundEffect.mp3');SFX_SLASH.volume=SV;
const DEATH_VOL=.4;                          // death sound loudness (0-1). slash_boosted.wav = slash.wav made louder
const VO_POST=[['Assets/Voicelines/I_Assure_You_Im_Real_This_Time.mp3',"I assure you, I'm REAL this time."],
               ['Assets/Voicelines/Your_Breathing_Gives_You_Away.mp3','Your breathing gives you Awa-a-ay...']];
const VO_LOSE=[["Assets/Voicelines/I'll_See_You_Again.mp3","I-I'll see you AGAIN"],
               ['Assets/Voicelines/So_Much_Effort_For_Nothing.mp3','SO MUCH EFFORT FOR NOTHING']];
for(const v of [...VO_POST,...VO_LOSE])v.push(new Audio(v[0]));
const T_VOICE=T_SLASH+2,DUCK=.3;            // voiceline plays 2s after the slash; music drops to 30% while he talks
let animStart=0;                             // key intro animation clock
const PANEL_D=[0,.15,.3,.45],REC_D=[.9,1.45,.6,1.2];   // lane panels drop from the top (in order); key circles slide up one by one, NOT in sync
let curVO=null,voWasPlaying=false,sub={s:'',age:0,life:0},loseVO=false,endTextOut=5.4,endStats=6.6;
function playVO(list,sec){
  const pick=list[Math.floor(Math.random()*list.length)],a=pick[2];
  stopVO();a.currentTime=0;a.volume=SV;a.play().catch(()=>{});curVO=a;
  sub={s:pick[1],age:0,life:(a.duration&&isFinite(a.duration)?a.duration:4)+.3};
  return sub.life;
}
function stopVO(){if(curVO){curVO.pause();curVO.currentTime=0}curVO=null;sub.life=0;sub.age=0}
function voActive(){return curVO&&!curVO.paused&&!curVO.ended}
function drawSub(y,sz,maxW){
  if(sub.life<=0||sub.age>sub.life)return;
  const a=Math.min(1,sub.age/.25)*Math.min(1,(sub.life-sub.age)/.5);
  X.save();X.globalAlpha=a;X.textAlign='center';
  do{X.font=`bold ${sz}px "Trebuchet MS",sans-serif`;if(X.measureText(sub.s).width<=maxW||sz<=14)break;sz-=1}while(true);
  const j=sub.age<.4?(rnd()-.5)*4:0;
  X.fillStyle='#c06bff';X.shadowColor='#a040ff';X.shadowBlur=14;X.fillText(sub.s,400+j,y);
  X.shadowBlur=0;X.restore();
}
const tintCache={};
function tint(i,col){const k=i.src+col;if(tintCache[k])return tintCache[k];
  const c=document.createElement('canvas');c.width=i.naturalWidth;c.height=i.naturalHeight;
  const g=c.getContext('2d');g.drawImage(i,0,0);g.globalCompositeOperation='source-in';g.fillStyle=col;g.fillRect(0,0,c.width,c.height);return tintCache[k]=c}
const PK={st:'in',side:0,pose:0,tw:0,next:1.5,eh:0,tm:.25,depth:1};   // one peeker: show -> glitch out -> gone -> glitch in on the OTHER side
const texts=[];let txtNext=0;
const TXT=[['IT\'S ME','r'],['I ALWAYS COME BACK','r'],['COME PLAY WITH US','g'],['YOU CAN\'T HIDE','r'],['SAVE THEM','g'],['BEHIND YOU','r'],['HE IS WATCHING','r'],['REMEMBER ME','g'],['STAY WITH US','g'],['NO ESCAPE','r'],['IT\'S BEEN SO LONG','g'],['HOAX','r'],['FIVE NIGHTS','r'],['WE ARE STILL HERE','g']];
const hx={pose:0,swapT:0,eyeHide:0,ghost:0,sc:1,burst:0,wf:0,prevT:0};
const ok=i=>i.complete&&i.naturalWidth>0;
let state='title',notes=[],held=[null,null,null,null],down=[0,0,0,0],rec=[],recOpen={};
let score=0,combo=0,maxCombo=0,health=50,shake=0,flash=0,judge='',judgeT=0,counts={};
try{const o=localStorage.getItem('fs_off');if(o!==null)CHART.offset=+o}catch(e){}
let ac=0,ap=0,wflash=0,endT=0,lastState='title';
const END_BLACK=1.6;   // end screen timeline (sec): fade to black / title text out / stats in
function now(){const a=A.currentTime;if(a!==ac){ac=a;ap=performance.now()}return ac+(A.paused?0:Math.min(.05,(performance.now()-ap)/1000))-(CHART.offset||0)}

function start(){
  notes=CHART.notes.map(([t,l,len])=>({t,l,len,s:0}));
  held=[null,null,null,null];rec=[];recOpen={};
  score=combo=maxCombo=0;health=50;counts={Sick:0,Good:0,Bad:0,Miss:0,Ghost:0};
  stopVO();loseVO=false;A.volume=MV;if(countBeat<0)animStart=performance.now();SFX_DEATH.pause();SFX_DEATH.currentTime=0;hx.pose=0;hx.sc=1;hx.burst=0;texts.length=0;txtNext=0;PK.st='in';PK.side=0;PK.tm=.25;hx.prevT=START;wflash=0;
  A.currentTime=START;for(const n of notes)if(n.t<START)n.s=2;A.play().catch(()=>{if(EMBED)state='title'});state='play';
}
function advance(){if(state==='title')start();else if(endT<endStats){endT=endStats;stopVO()}else if(EMBED)leave(state);else start()}   // ENTER skips the end sequence, then retries (embedded: leaves)
function say(t,c){judge=t;judgeT=.6;if(c)counts[t]=(counts[t]||0)+1}
// ---- DIFFICULTY (health is 0-100, starts at 50). Bigger numbers = more punishing ----
const DMG={miss:8,bad:2.5,ghost:2.5,sick:2,good:1,hold:2.5};   // ghost = pressing a key with no note near it; hold = hp/sec while holding a long note
function hp(d){health=Math.max(0,Math.min(100,health+d))}
function miss(n){n.s=n.len?4:2;combo=0;hp(-DMG.miss);shake=.3;flash=.35;say('Miss',1)}

function press(l){
  if(state!=='play'||down[l])return;down[l]=1;
  const t=now();
  if(REC){recOpen[l]=t;return}
  let n=null;
  for(const k of notes)if(k.l===l&&k.s===0&&Math.abs(k.t-t)<=WIN.bad&&(!n||Math.abs(k.t-t)<Math.abs(n.t-t)))n=k;
  if(!n){combo=0;hp(-DMG.ghost);shake=.15;flash=.2;say('Ghost',1);return}   // ghost tap: hurts now
  const d=Math.abs(n.t-t);
  const j=d<=WIN.sick?'Sick':d<=WIN.good?'Good':'Bad';
  if(j==='Bad'){combo=0;hp(-DMG.bad)}else{combo++;hp(j==='Sick'?DMG.sick:DMG.good);score+=j==='Sick'?350:200}
  maxCombo=Math.max(maxCombo,combo);say(j,1);
  if(n.len){n.s=3;held[l]=n}else n.s=1;
}
function release(l){
  down[l]=0;const t=now();
  if(REC){if(recOpen[l]!=null){const len=t-recOpen[l];rec.push([+recOpen[l].toFixed(3),l,len>.3?+len.toFixed(2):0]);delete recOpen[l]}return}
  const n=held[l];
  if(n){held[l]=null;if(t<n.t+n.len-.15)miss(n);else{n.s=1;score+=150;say('Sick')}}
}
addEventListener('keydown',e=>{
  if(e.repeat)return;
  if(EMBED&&e.code==='KeyQ'&&state==='pause'){leave('lose');return}
  if(e.code==='Escape'&&(state==='play'||state==='pause')){if(state==='play'){A.pause();state='pause'}else{A.play();state='play'}return}
  if(e.code==='Enter'||e.code==='Space'){if(state==='title'||state==='win'||state==='lose'){e.preventDefault();advance();return}if(state==='pause'){A.play();state='play'}return}
  const l=KEYS.indexOf(e.code);if(l>=0)press(l);
});
addEventListener('keydown',e=>{if(e.key==='['||e.key===']'){CHART.offset=Math.round(((CHART.offset||0)+(e.key===']'?.01:-.01))*100)/100;try{localStorage.setItem('fs_off',CHART.offset)}catch(_){}}});
addEventListener('blur',()=>{for(let l=0;l<4;l++)if(down[l])release(l)});
addEventListener('keyup',e=>{const l=KEYS.indexOf(e.code);if(l>=0)release(l)});
const ptr={};
C.addEventListener('pointerdown',e=>{
  if(state!=='play'){if(state==='title'||state==='win'||state==='lose')advance();else if(state==='pause'){A.play();state='play'}return}
  const r=C.getBoundingClientRect(),px=(e.clientX-r.left)/r.width*W,l=[0,1,2,3].reduce((b,i)=>Math.abs(px-(LX[i]+(i<2?-1:1)*gapNow(fxTime())/2))<Math.abs(px-(LX[b]+(b<2?-1:1)*gapNow(fxTime())/2))?i:b,0);
  ptr[e.pointerId]=l;press(l);
});
const up=e=>{if(ptr[e.pointerId]!=null){release(ptr[e.pointerId]);delete ptr[e.pointerId]}};
C.addEventListener('pointerup',up);C.addEventListener('pointercancel',up);

function update(dt){
  if(state==='hold')return;
  if(state==='count'){countUpdate(dt);return}
  if(state!==lastState){
    if(state==='win'||state==='lose')endT=0;
    if(state==='lose'){   // Hoax slashes us + death sound
      stopVO();A.volume=MV;SFX_SLASH.currentTime=0;SFX_SLASH.play().catch(()=>{});
      SFX_DEATH.currentTime=0;SFX_DEATH.volume=DEATH_VOL*SV;SFX_DEATH.play().catch(()=>{});
      shake=.7;wflash=1;flash=.6;loseVO=false}
    lastState=state}
  if(state==='win'||state==='lose')endT+=dt;
  if(EMBED&&(state==='win'||state==='lose')&&endT>endStats+5)leave(state);   // nobody pressed ENTER: leave by itself
  if(sub.life>0)sub.age+=dt;
  // pause/resume the voiceline together with the game
  if(state==='pause'&&voActive()){curVO.pause();voWasPlaying=true}
  else if(state==='play'&&voWasPlaying){voWasPlaying=false;if(curVO)curVO.play().catch(()=>{})}
  // music ducks while Hoax talks
  if(state==='play'||state==='pause'){const tv=(voActive()||voWasPlaying?DUCK:1)*MV;A.volume=clamp(A.volume+(tv-A.volume)*Math.min(1,dt*8),0,1)}
  // lose: black screen -> title text appears -> Hoax speaks
  if(state==='lose'&&!loseVO&&endT>=END_BLACK){loseVO=true;const L=playVO(VO_LOSE);endTextOut=Math.max(5.4,END_BLACK+L+.6);endStats=endTextOut+1.2}
  if(state==='win'){endTextOut=5.4;endStats=6.6}
  if(state==='lose'){   // death sound: quieter while he talks, fades out when the stats appear
    SFX_DEATH.volume=clamp(SV*DEATH_VOL*(voActive()?.55:1)*clamp(1-(endT-endStats)/1.2,0,1),0,1);
    if(endT>endStats+1.2)SFX_DEATH.pause()}
  shake=Math.max(0,shake-dt);flash=Math.max(0,flash-dt);judgeT=Math.max(0,judgeT-dt);
  wflash=Math.max(0,wflash-dt*1.6);
  if(state!=='play')return;
  const t=now();fxUpdate(dt,t+(CHART.offset||0));
  if(!REC){
    for(const n of notes)if(n.s===0&&t-n.t>WIN.bad+.02)miss(n);
    for(let l=0;l<4;l++){const n=held[l];if(!n)continue;
      if(t>=n.t+n.len){n.s=1;held[l]=null;score+=150;say('Sick');}
      else{hp(DMG.hold*dt);score+=60*dt}}
    if(health<=0){A.pause();state='lose'}
  }
  if(A.ended||t>=A.duration-.05){A.pause();
    if(REC){rec.sort((a,b)=>a[0]-b[0]);const txt='const CHART={offset:0,notes:'+JSON.stringify(rec)+'};\n';
      const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([txt]));a.download='chart.js';a.click();state='recdone'}
    else state='win'}
}

const rnd=Math.random,clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
function fxTime(){return now()+(CHART.offset||0)}
function fadeAmt(t){return t<T_CALM?0:clamp((t-T_CALM)/Math.max(8,(A.duration||160)-T_CALM-FADE_END_PAD),0,1)}
function fxUpdate(dt,t){
  // one-shot hits when the song crosses a timestamp
  if(t-hx.prevT<.5){
    if(hx.prevT<T_SLASH&&t>=T_SLASH){shake=.5;wflash=.9;hx.wf=1;SFX_SLASH.currentTime=0;SFX_SLASH.play().catch(()=>{})}
    if(hx.prevT<T_VOICE&&t>=T_VOICE)playVO(VO_POST)
    if(hx.prevT<T_RAGE&&t>=T_RAGE){shake=.45;wflash=.35}
  }
  hx.prevT=t;
  // side creepers (1:11 -> 1:30): occasional twitch, much calmer than rage
  if(t>=T_PEEK&&t<T_SLASH+.2){
    PK.tm-=dt;PK.eh-=dt;if(PK.eh<=0&&rnd()<2*dt)PK.eh=.04+rnd()*.1;
    if(PK.st==='show'){PK.next-=dt;PK.tw=Math.max(0,PK.tw-dt);
      if(rnd()<.5*dt){PK.tw=.1+rnd()*.14;PK.pose^=1}
      if(PK.next<=0){PK.st='out';PK.tm=.28}}
    else if(PK.tm<=0){
      if(PK.st==='out'){PK.st='gone';PK.tm=.35+rnd()*.55}
      else if(PK.st==='gone'){PK.st='in';PK.side^=1;PK.pose=rnd()<.5?0:1;PK.depth=.85+rnd()*.15;PK.tm=.25}
      else if(PK.st==='in'){PK.st='show';PK.next=1.3+rnd()*1.6}
    }
  }
  // creepy background texts from 0:30
  for(let i=texts.length-1;i>=0;i--){texts[i].age+=dt;if(texts[i].age>texts[i].life)texts.splice(i,1)}
  txtNext-=dt;
  if(t>=T_TEXT&&t<T_SLASH&&txtNext<=0&&texts.length<4){
    txtNext=t<T_PEEK?1.3+rnd()*1.6:t<T_RAGE?.8+rnd()*1.1:.45+rnd()*.7;
    const[str,kind]=TXT[Math.floor(rnd()*TXT.length)];
    // keep texts OUT of the note zone: left or right strip only, wrapped so nothing gets cut
    const zoneW=215-20,right=rnd()<.5;
    let sz=(26+rnd()*20)*(t>=T_RAGE?1.15:1);
    const lines=wrapText(str,sz,zoneW);
    sz=lines.sz;
    texts.push({lines:lines.l,col:kind==='r'?'#b0001c':'#7d858c',x:right?W-zoneW/2-10:zoneW/2+10,y:90+rnd()*(H-260),rot:(rnd()-.5)*.5,sz,age:0,life:.45+rnd()*.7})
  }
  // glitch bursts
  hx.burst-=dt;
  if(hx.burst<=0&&t<T_CALM){const rate=t<T_SLASH?.3:t<T_RAGE?1.4:7;if(rnd()<rate*dt)hx.burst=.07+rnd()*.18}
  if(t>=T_CALM)hx.burst=0;
  // pose swapping (Pose1+Eyes1 <-> Pose2+Eyes2)
  if(t>=T_SLASH&&t<T_CALM){hx.swapT-=dt;if(hx.swapT<=0){hx.pose^=1;hx.swapT=t<T_RAGE?.12+rnd()*.55:.04+rnd()*.2}}
  else if(t>=T_CALM)hx.pose=0;
  // eye stutter
  hx.eyeHide-=dt;if(hx.eyeHide<=0&&rnd()<3*dt)hx.eyeHide=.03+rnd()*.1;
  hx.ghost-=dt;if(hx.ghost<=0&&rnd()<1.5*dt)hx.ghost=.06+rnd()*.1;
  // scale: slow lunge during rage, settles back in calm
  const target=t<T_RAGE?1:t<T_CALM?1.04+(t-T_RAGE)/(T_CALM-T_RAGE)*.14:1;
  hx.sc+=(target-hx.sc)*Math.min(1,dt*(t<T_CALM?4:1.5));
}
function glitchSlices(amt){
  if(amt<=0)return;X.save();X.setTransform(1,0,0,1,0,0);
  const n=3+Math.floor(amt*9);
  for(let i=0;i<n;i++){const y=rnd()*H,h=3+rnd()*38*amt,dx=(rnd()-.5)*70*amt;X.drawImage(C,0,y,W,h,dx,y,W,h)}
  X.restore();
}
function wrapText(str,sz,maxW){
  const words=str.split(' ');
  for(;;){
    X.font=`bold ${sz}px "Courier New",monospace`;
    const l=[];let cur='';
    for(const wd of words){const tryl=cur?cur+' '+wd:wd;if(X.measureText(tryl).width<=maxW||!cur)cur=tryl;else{l.push(cur);cur=wd}}
    l.push(cur);
    if(l.every(x=>X.measureText(x).width<=maxW)||sz<=14)return{l,sz};
    sz-=2;
  }
}
function drawTexts(t,fade){
  for(const q of texts){
    const a=(q.age<.06?q.age/.06:1)*Math.pow(1-q.age/q.life,.6)*(rnd()<.1?.25:1)*(1-fade);
    X.save();X.globalAlpha=a*.7;X.translate(q.x+(hx.burst>0?(rnd()-.5)*10:0),q.y);X.rotate(q.rot);
    X.font=`bold ${q.sz}px "Courier New",monospace`;X.textAlign='center';
    X.fillStyle=q.col;X.shadowColor=q.col;X.shadowBlur=14;
    q.lines.forEach((ln,i)=>X.fillText(ln,0,(i-(q.lines.length-1)/2)*q.sz*1.1));X.restore();
  }
  X.globalAlpha=1;
}
function drawSides(t){
  if(t<T_PEEK||t>T_SLASH+.15)return;
  const out=t>=T_SLASH?1-(t-T_SLASH)/.15:1;
  const st=PK.st;if(st==='gone')return;
  const glitchy=st==='out'||st==='in';
  const P=POSE[PK.pose],E=EYES[PK.pose];if(!ok(P))return;
  const h=500,s=h/P.naturalHeight,w=P.naturalWidth*s;
  const a=out*(glitchy?(rnd()<.6?1:.2):1);
  // fixed spot (no sliding): most of him is in view, just a tiny sway + jitter
  const cx=120+Math.sin(t*1.1)*2+((glitchy||PK.tw>0)?(rnd()-.5)*(glitchy?34:16):0),dy=100,dx=cx-w/2;
  X.save();if(PK.side){X.translate(W,0);X.scale(-1,1)}
  X.globalAlpha=a;
  if(glitchy||PK.tw>0){X.globalCompositeOperation='lighter';X.globalAlpha=a*.45;
    const o=glitchy?12:7;X.drawImage(tint(P,'#ff1030'),dx-o,dy,w,h);X.drawImage(tint(P,'#20e0ff'),dx+o,dy,w,h);
    X.globalCompositeOperation='source-over';X.globalAlpha=a}
  X.shadowColor='#5a2a90';X.shadowBlur=SIL_RIM;X.drawImage(tint(P,'#040106'),dx,dy,w,h);X.shadowBlur=0;   // full silhouette (faint rim so he stays visible)
  if(ok(E)&&PK.eh<=0){X.globalAlpha=a*(.75+.25*rnd());X.shadowColor='#fff';X.shadowBlur=14;X.drawImage(E,dx,dy,w,h)}
  X.restore();
}
function drawHoax(t,fade){
  if(t<T_SLASH+.02)return;
  const rage=t>=T_RAGE&&t<T_CALM,calm=t>=T_CALM,k=clamp((t-T_SLASH)/.3,0,1);
  const P=POSE[hx.pose];if(!ok(P))return;
  const bursting=hx.burst>0&&!calm;
  const al=k;
  // backlight so he reads against the dark
  const pulse=.5+.5*Math.sin(t*(rage?23:3));
  const bl=rage?(.26+.14*pulse)*(bursting?1.4:1):0;
  const g=X.createRadialGradient(400,260,20,400,260,340);
  const rc=rage?'200,10,30':'100,40,170';
  g.addColorStop(0,`rgba(${rc},${bl*k})`);g.addColorStop(1,`rgba(${rc},0)`);
  X.fillStyle=g;X.fillRect(0,0,W,H);
  const h=600,s=h/P.naturalHeight,w=P.naturalWidth*s;
  X.save();
  const jx=bursting?(rnd()-.5)*(rage?22:10):0,sway=Math.sin(t*1.3)*3;
  X.translate(400+sway+jx,133);X.scale(hx.sc,hx.sc);X.translate(-400,-133);
  const dx=400-w/2,dy=30;
  X.globalAlpha=al;
  // RGB split fringes
  if(bursting||rage){const o=(rage?9:5)*(bursting?1.4:.6);
    X.globalCompositeOperation='lighter';X.globalAlpha=al*.45;
    X.drawImage(tint(P,'#ff1030'),dx-o,dy,w,h);X.drawImage(tint(P,'#20e0ff'),dx+o,dy,w,h);
    X.globalCompositeOperation='source-over';X.globalAlpha=al}
  // real colors, kept dark; brightens for a split second on glitch bursts
  X.shadowColor=rage?'#d01030':'#000';X.shadowBlur=rage?44:20;
  X.drawImage(P,dx,dy,w,h);X.shadowBlur=0;
  const dk=DIM_HOAX*(bursting?.35:1)*(rage?.8:1),dark=dk+(1-dk)*Math.pow(fade,.55);   // fade: shade toward pure black
  X.globalAlpha=al*dark;X.drawImage(tint(P,'#000'),dx,dy,w,h);X.globalAlpha=al;
  // eyes: 1:30 -> 1:50 stuttering, and again in the calm ending where they fade LAST
  if(t<T_RAGE||calm){
    const E=EYES[hx.pose],E2=EYES[hx.pose^1];
    const dur=A.duration||160;
    const ea=calm?(1-clamp((t-(dur-FADE_END_PAD))/FADE_END_PAD,0,1))*(.85+.15*Math.sin(t*2.2)):al;
    if(ok(E)&&(calm||hx.eyeHide<=0)){
      X.shadowColor='#fff';X.shadowBlur=calm?30:14;X.globalAlpha=calm?ea:ea*(.75+.25*rnd());
      const ej=!calm&&rnd()<.15?(rnd()-.5)*5:0;
      X.drawImage(E,dx+ej,dy,w,h);
      if(!calm&&hx.ghost>0&&ok(E2)){X.globalAlpha=ea*.5;X.drawImage(E2,dx-ej,dy,w,h)}
      X.shadowBlur=0}
  }
  X.restore();X.globalAlpha=1;
}
function worldBG(t,fade){
  X.fillStyle='#030005';X.fillRect(-20,-20,W+40,H+40);
  if(ok(bgImg)){
    X.drawImage(bgImg,0,0,W,H);
    // dark overlay: wall + checker stripe become a barely-there silhouette
    const flick=hx.burst>0&&t<T_CALM?rnd()*.16:0;
    X.fillStyle=`rgba(2,0,6,${BG_DARK-flick})`;X.fillRect(0,0,W,H);
  }
  const v=X.createRadialGradient(400,300,120,400,300,520);v.addColorStop(0,'rgba(0,0,0,0)');v.addColorStop(1,'rgba(0,0,0,.65)');
  X.fillStyle=v;X.fillRect(0,0,W,H);
  if(fade>0){X.fillStyle=`rgba(0,0,0,${fade})`;X.fillRect(-20,-20,W+40,H+40)}
}
// jagged slash line down the middle
const CUT=[];for(let y=-20;y<=H+20;y+=40)CUT.push([400+(y-300)*.025+Math.sin(y*.37)*3.5+Math.cos(y*.91)*2.5,y]);
function cutPath(side){X.beginPath();X.moveTo(side*900+400,-20);for(const[x,y]of CUT)X.lineTo(x,y);X.lineTo(side*900+400,H+20);X.closePath()}
function gapNow(t){
  if(t<T_SLASH+.1)return 0;
  const u=clamp((t-T_SLASH-.1)/.4,0,1);let g=GAPMAX*(1-Math.pow(1-u,3));
  if(t>=T_RAGE&&t<T_CALM)g=g*(1+.04*Math.sin(t*8));
  return g;
}
function slashFX(t){
  const tS=t-T_SLASH;if(tS<0||tS>.4)return;
  const sw=Math.min(1,tS/.12),a=1-tS/.4,lim=-20+sw*(H+40);
  X.save();X.lineJoin='round';X.strokeStyle=`rgba(255,255,255,${a})`;X.lineWidth=7*a+1;X.shadowColor='#ff1030';X.shadowBlur=30;
  X.beginPath();let first=true;for(const[x,y]of CUT){if(y>lim)break;first?X.moveTo(x,y):X.lineTo(x,y);first=false}X.stroke();X.restore();
}
const LJ=[];for(let i=0;i<=16;i++)LJ.push([Math.sin(i*2.3)*14,Math.cos(i*1.7)*14]);
function loseSlash(e){   // two crossing slashes, like claws
  [[0,820,-40,-20,640],[.12,-20,-40,820,640]].forEach(([dl,x0,y0,x1,y1])=>{
    const k=e-dl;if(k<0||k>.8)return;
    const sw=Math.min(1,k/.1),a=1-clamp((k-.1)/.7,0,1)**1.5;
    X.save();X.lineJoin='round';X.lineCap='round';X.strokeStyle=`rgba(255,255,255,${a})`;X.lineWidth=4+20*a;
    X.shadowColor='#ff1030';X.shadowBlur=40;X.beginPath();
    for(let i=0;i<=16;i++){if(i/16>sw)break;const f=i/16,x=x0+(x1-x0)*f+LJ[i][0],y=y0+(y1-y0)*f+LJ[i][1];i?X.lineTo(x,y):X.moveTo(x,y)}
    X.stroke();X.restore();
  });
}
function drawLanes(t){
  const g=gapNow(t);
  if(g<.5){lanes();return}
  for(const side of[-1,1]){
    X.save();X.translate(side*g/2,0);cutPath(side);X.clip();lanes();
    X.globalAlpha=1-.75*fadeAmt(t);X.strokeStyle='#ff2a4a99';X.lineWidth=3;X.shadowColor='#ff1030';X.shadowBlur=12;
    X.beginPath();CUT.forEach(([x,y],i)=>i?X.lineTo(x,y):X.moveTo(x,y));X.stroke();
    X.restore();
  }
}
function lanes(){
  const tt=now(),it=(performance.now()-animStart)/1000;
  const eo=x=>1-Math.pow(1-x,3),ob=x=>{const c=1.70158;return 1+(c+1)*Math.pow(x-1,3)+c*Math.pow(x-1,2)};
  for(let l=0;l<4;l++){   // dark lane panels slide DOWN from the top, one after another
    const p=clamp((it-PANEL_D[l])/.9,0,1);if(p<=0)continue;
    const x0=l===0?215:LX[l]-45,x1=l===3?585:LX[l]+45;
    X.fillStyle='#0009';X.fillRect(x0,-H*(1-eo(p)),x1-x0,H);
    X.globalAlpha=p;X.strokeStyle='#ffffff10';X.lineWidth=1;X.beginPath();X.moveTo(LX[l],0);X.lineTo(LX[l],H);X.stroke();X.globalAlpha=1;
    if(down[l]){X.fillStyle=COL[l]+'33';X.fillRect(LX[l]-40,0,80,H)}
  }
  if(!REC)for(const n of notes){
    if(n.s===1||n.s===2)continue;
    const y=HY-(n.t-tt)*SPEED,x=LX[n.l];
    if(y<-60&&n.s!==3)continue;if(y>H+80&&!n.len)continue;
    const dead=n.s===4;X.globalAlpha=dead?.25:1;
    if(n.len){const top=HY-(n.t+n.len-tt)*SPEED,bot=n.s===3?HY:y;
      X.fillStyle=dead?'#444':COL[n.l]+'99';X.fillRect(x-14,top,28,bot-top)}
    {const yy=n.s===3?HY:y;
      X.fillStyle='#120018';X.strokeStyle=COL[n.l];X.lineWidth=5;X.shadowColor=COL[n.l];X.shadowBlur=14;
      X.beginPath();X.arc(x,yy,30,0,7);X.fill();X.stroke();X.shadowBlur=0}
    X.globalAlpha=1;
  }
  for(let l=0;l<4;l++){ // receptors slide UP into place, each at its own time
    const rp=clamp((it-REC_D[l])/.8,0,1);if(rp<=0)continue;
    const ry=HY+(1-ob(rp))*(H-HY+90);X.globalAlpha=Math.min(1,rp*3);
    X.strokeStyle=down[l]?'#fff':COL[l];X.lineWidth=down[l]?7:4;X.fillStyle=down[l]?COL[l]+'66':'#00000088';
    X.beginPath();X.arc(LX[l],ry,32,0,7);X.fill();X.stroke();
    text(LAB[l],LX[l],ry+8,22,'#ffffffaa');X.globalAlpha=1;
  }
}
function draw(){
  if(state==='hold'){X.fillStyle='#000';X.fillRect(0,0,W,H);return}
  const hr=health/100,t=fxTime(),tm=state==='title'?0:t,fade=fadeAmt(tm);
  const rage=tm>=T_RAGE&&tm<T_CALM;
  X.save();
  if(shake>0)X.translate((Math.random()-.5)*14*shake*4,(Math.random()-.5)*14*shake*4);
  if(rage)X.translate((rnd()-.5)*4,(rnd()-.5)*4);
  worldBG(tm,fade);
  drawTexts(tm,fade);
  drawSides(tm);
  drawHoax(tm,fade);
  // static noise (stops once he calms down)
  if(tm<T_CALM){
    const amt=tm<T_SLASH?20:tm<T_RAGE?45:130;
    X.fillStyle='#fff';for(let i=0;i<amt+(1-hr)*30;i++){X.globalAlpha=rnd()*.07;X.fillRect(rnd()*W,rnd()*H,rnd()*120,1+rnd()*2)}
    X.globalAlpha=1;
    if(hx.burst>0)glitchSlices(tm<T_SLASH?.35:tm<T_RAGE?.7:1);
  }
  if(state==='title')return end(),REC&&text('RECORDER MODE',400,220,22,'#ff2a4a'),
    text('Keys: D  F  J  K  (or touch)',400,270,26,'#ddd'),text(REC?'Press ENTER, then tap D F J K along with the song':'Press ENTER to start',400,315,20,'#aaa');
  drawLanes(tm);
  drawCountdown();
  slashFX(tm);
  if(state==='play'||state==='pause')drawSub(538,22,370);   // bottom-middle, in the free space between the two key groups
  if(judgeT>0)text(judge,400,380,34*(1+judgeT*.3),judge==='Miss'||judge==='Ghost'?'#ff2a4a':judge==='Sick'?'#e7b6ff':'#fff');
  if(combo>2)text(combo+' combo',400,425,22,'#c06bff');
  // health bar: purple = you, red = Hoax
  X.fillStyle='#ff1030';X.fillRect(230,565,340,16);X.fillStyle='#8a3bff';X.fillRect(230+340*(1-hr),565,340*hr,16);
  X.strokeStyle='#fff';X.lineWidth=2;X.strokeRect(230,565,340,16);
  text('You',250,560,13,'#c06bff');text('Hoax',550,560,13,'#ff6a80');
  text('Score '+Math.floor(score),90,40,20,'#ddd');text('Sync '+Math.round((CHART.offset||0)*1000)+'ms  ( [ / ] to adjust )',130,585,13,'#777');
  if(A.duration)X.fillStyle='#8a3bff',X.fillRect(0,0,W*Math.min(1,A.currentTime/A.duration),4);
  if(REC)text('● REC',720,40,22,'#ff2a4a');
  if(flash>0){X.fillStyle=`rgba(255,0,30,${flash})`;X.fillRect(0,0,W,H)}
  if(wflash>0){X.fillStyle=`rgba(255,255,255,${Math.min(1,wflash)*.6})`;X.fillRect(0,0,W,H)}
  X.restore();
  if(state==='pause'){X.fillStyle='#000a';X.fillRect(0,0,W,H);text('PAUSED',400,300,44,'#c06bff');text('Esc / tap to resume',400,345,20,'#aaa');if(EMBED)text('Q to leave',400,378,18,'#777')}
  if(state==='recdone'){X.fillStyle='#000c';X.fillRect(0,0,W,H);
    return text('Chart saved!',400,260,40,'#c06bff'),text('chart.js was downloaded. Replace the old chart.js with it.',400,310,18,'#ddd')}
  if(state==='win'||state==='lose'){
    const e=endT;
    const bs=state==='lose'?.35:0;
    X.fillStyle=`rgba(0,0,0,${clamp((e-bs)/(END_BLACK-bs-.2),0,1)})`;X.fillRect(0,0,W,H);   // everything (keys + HUD) fades out
    if(state==='lose')loseSlash(e);
    const ta=e<END_BLACK?0:e<END_BLACK+1.5?(e-END_BLACK)/1.5:e<endTextOut?1:clamp(1-(e-endTextOut)/1,0,1);
    if(ta>0){X.globalAlpha=ta;text(state==='win'?'YOU SURVIVED... for now.':'HOAX GOT YOU.',400,310,46,state==='win'?'#c06bff':'#ff2a4a');X.globalAlpha=1}
    if(state==='lose'&&e<endTextOut)drawSub(375,28,700);
    const sa=clamp((e-endStats)/.8,0,1);
    if(sa>0){X.globalAlpha=sa;
      text(`Score ${Math.floor(score)}   Max combo ${maxCombo}`,400,225,24,'#fff');
      text(`Sick ${counts.Sick||0}  Good ${counts.Good||0}  Bad ${counts.Bad||0}  Miss ${counts.Miss||0}  Ghost taps ${counts.Ghost||0}`,400,265,20,'#ccc');
      text(EMBED?'Press ENTER to continue':'Press ENTER to retry',400,330,22,'#aaa');X.globalAlpha=1}
  }
}
function end(){X.restore()}
function text(s,x,y,sz,c){X.font=`bold ${sz}px "Trebuchet MS",sans-serif`;X.textAlign='center';X.fillStyle=c;X.shadowColor='#000';X.shadowBlur=6;X.fillText(s,x,y);X.shadowBlur=0}
let last=performance.now();
(function loop(t){const dt=Math.min(.05,(t-last)/1000);last=t;update(dt);draw();requestAnimationFrame(loop)})(last);
// ---- embedded mode: wait on black until the host game sends 'egg-go' (it fades the screen in at that moment) ----
if(EMBED){
  state='hold';
  const ready=()=>{try{parent.postMessage({type:'egg-ready'},location.origin)}catch(e){}};
  if(A.readyState>=3)ready();else A.addEventListener('canplaythrough',ready,{once:true});
  addEventListener('message',e=>{if(e.origin===location.origin&&e.data&&e.data.type==='egg-go'&&state==='hold'){countT=-COUNT_WAIT;countBeat=-1;animStart=performance.now()+COUNT_WAIT*1000;state='count'}});   // the lanes slide in, 3-2-1-GO, then the song
}
