import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const D = JSON.parse(document.getElementById('scene-data').textContent);
const $ = id => document.getElementById(id);
const ko = D.language === 'KO', L = (k, e) => ko ? k : e;
const [W, H, Z] = D.size, span = Math.max(W, H, Z), mode = D.mode;
const isSite = mode === 'site', isThermal = mode === 'thermal', isFire = mode === 'fire';
const stateNames = ko ? ['대기','가열','열폭주','화재','화염 억제 · 내부 TR 지속','소진'] : ['Normal','Heating','Thermal runaway','Fire','Knockdown · TR ongoing','Burned out'];
const stateColors = ['#72959d','#eeb650','#ec7d32','#e84b35','#3ea6ed','#596374'];
const kindNames = {enc:L('배터리 인클로저','Battery enclosure'),pcs:'PCS / MV',tr:L('주변압기','Main transformer'),tank:L('소방 수조','Fire water tank'),rack:L('배터리 랙','Battery rack')};
const titles = {site:L('부지 배치 · 설계 모델','Site layout · design model'),thermal:L('열 · 공기 흐름','Thermal · airflow'),fire:L('소방 · 열폭주 전파','Fire · thermal runaway'),smoke:L('연기층 · 배연','Smoke layer · extraction'),structure:L('기초 지지압','Foundation pressure')};
$('subtitle').textContent = titles[mode];
$('top').textContent = L('평면','PLAN'); $('front').textContent = L('정면','FRONT');
$('fit').textContent = L('전체 맞춤','FIT'); $('edges').textContent = L('모서리','EDGES');
$('measure').textContent = L('거리 측정','MEASURE'); $('shot').textContent = L('이미지 저장','PNG');
$('panels').textContent = L('패널','PANELS');
$('panels').onclick=()=>{const open=getComputedStyle($('layers')).display==='none';$('layers').style.display=open?'block':'none';$('inspector').style.display=open?'none':'block';};
$('layers-title').textContent = L('표시 레이어','LAYERS'); $('properties-title').textContent = L('속성 / 선택','PROPERTIES');
$('section-title').textContent = L('수평 절단 높이','Horizontal cut');
$('hint').textContent = L('드래그: 회전 · 우클릭: 이동 · 휠: 확대\n설비를 클릭하면 속성이 표시됩니다.','Drag: orbit · right drag: pan · scroll: zoom. Click equipment to inspect.');
$('model-note').textContent = L('형상 상세 = 시각화용 가정 · 실시설계 CAD 아님','Detail geometry illustrative · not fabrication CAD');
const vp = $('viewport');
let renderer;
try {
  renderer = new THREE.WebGLRenderer({antialias:true,alpha:false,preserveDrawingBuffer:true});
} catch (err) {
  $('error').style.display='block'; $('error').textContent=L('이 환경에서 WebGL을 사용할 수 없습니다. 아래의 분석 그래프를 사용하거나 브라우저 하드웨어 가속을 켜세요.','WebGL unavailable. Use the analytical plots below or enable browser hardware acceleration.');
  throw err;
}
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.7));
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure=1.15;
renderer.localClippingEnabled=true;
vp.prepend(renderer.domElement);
renderer.domElement.addEventListener('webglcontextlost', e => {e.preventDefault();$('error').style.display='block';$('error').textContent=L('GPU 컨텍스트가 중단되었습니다. 페이지를 새로고침하세요.','GPU context lost. Reload this page.');});
const scene = new THREE.Scene(); scene.background = new THREE.Color('#a5bac8');
scene.fog = new THREE.Fog('#a5bac8', span*3, span*10);
const camP = new THREE.PerspectiveCamera(42, 1, .05, span*30+100);
const camO = new THREE.OrthographicCamera(-span,span,span,-span,.05,span*30+100);
let camera=camP, controls=new OrbitControls(camera,renderer.domElement);
controls.enableDamping=true; controls.dampingFactor=.1; controls.maxPolarAngle=Math.PI*.49;
controls.minDistance=.5;controls.maxDistance=span*8;
scene.add(new THREE.HemisphereLight('#e6f6ff','#62634f',2.4));
const sun=new THREE.DirectionalLight('#fff2d5',3.5);sun.position.set(-span*.35,span*1.2,-span*.65);sun.target.position.set(W/2,0,-H/2);
sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);Object.assign(sun.shadow.camera,{left:-span,right:span,top:span,bottom:-span,near:.1,far:span*5+20});sun.shadow.normalBias=.04;sun.shadow.bias=-.00015;
scene.add(sun,sun.target);
const clipping=new THREE.Plane(new THREE.Vector3(0,-1,0),Z+1);
const materials=[];
function mat(color,options={}) {const m=new THREE.MeshStandardMaterial({color,roughness:.72,metalness:.12,...options,clippingPlanes:[clipping]});materials.push(m);return m;}
const concrete=mat('#a5aaa5',{roughness:.98}), steel=mat('#778997',{metalness:.65,roughness:.42}), dark=mat('#233544'), white=mat('#d7e2e3'), accent=mat('#2f8598'), red=mat('#b94a3d');
const groups={};
for(const key of ['equipment','civil','utilities','fence','shell','results','flow','labels','baseline']) {groups[key]=new THREE.Group();scene.add(groups[key]);}
const cube=new THREE.BoxGeometry(1,1,1), pickables=[], assets=[], detailBatches=new Map(), edges=[];
function box(parent,x,y,z,dx,dy,dz,material,cast=true) {
  const mesh=new THREE.Mesh(cube,material);mesh.position.set(x+dx/2,z+dz/2,-y-dy/2);mesh.scale.set(dx,dz,dy);mesh.castShadow=cast;mesh.receiveShadow=true;parent.add(mesh);return mesh;
}
function detail(parent,x,y,z,dx,dy,dz,material) {
  const key=parent.uuid+material.uuid;
  if(!detailBatches.has(key))detailBatches.set(key,{parent,material,transforms:[]});
  detailBatches.get(key).transforms.push([x,y,z,dx,dy,dz]);
}
function flushDetails(){const dummy=new THREE.Object3D();for(const {parent,material,transforms} of detailBatches.values()){
  const inst=new THREE.InstancedMesh(cube,material,transforms.length);transforms.forEach(([x,y,z,dx,dy,dz],i)=>{dummy.position.set(x+dx/2,z+dz/2,-y-dy/2);dummy.scale.set(dx,dz,dy);dummy.updateMatrix();inst.setMatrixAt(i,dummy.matrix);});inst.castShadow=D.boxes.length<160;inst.receiveShadow=true;parent.add(inst);
}}
function line(parent,points,color='#5e7485',opacity=1){const geo=new THREE.BufferGeometry().setFromPoints(points.map(p=>new THREE.Vector3(p[0],p[2],-p[1])));const l=new THREE.Line(geo,new THREE.LineBasicMaterial({color,transparent:opacity<1,opacity,clippingPlanes:[clipping]}));parent.add(l);return l;}
function label(text,x,y,z){const el=document.createElement('div');el.className='model-label';el.textContent=text;$('labels').appendChild(el);return {el,pos:new THREE.Vector3(x,z,-y)};}
const labelList=[];
// Procedural gravel texture: deterministic pixels, no external image/network requests.
const canvas=document.createElement('canvas');canvas.width=canvas.height=128;const ctx=canvas.getContext('2d');const pixels=ctx.createImageData(128,128);
for(let i=0;i<128*128;i++){const v=138+((i*73+(i>>7)*31)%41);pixels.data.set([v,v+2,v-3,255],i*4);}ctx.putImageData(pixels,0,0);
const gravel=new THREE.CanvasTexture(canvas);gravel.wrapS=gravel.wrapT=THREE.RepeatWrapping;gravel.repeat.set(W/3,H/3);gravel.colorSpace=THREE.SRGBColorSpace;
const ground=box(groups.civil,-1,-1,-.45,W+2,H+2,.12,mat(isSite?'#c0c0ad':'#a8b0b3',{map:isSite?gravel:null,roughness:1}),false);pickables.push(ground);
const grid=new THREE.GridHelper(Math.max(W,H)*1.2,Math.min(100,Math.max(10,Math.round(span))), '#76939e','#849fa6');grid.position.set(W/2,-.31,-H/2);grid.material.transparent=true;grid.material.opacity=.25;groups.civil.add(grid);

function equipment(b){
  const {x,y,dx,dy,dz}=b;
  const color=b.kind==='pcs'?'#c3d4dd':b.kind==='tr'?'#829795':b.kind==='tank'?'#b8cacc':b.kind==='rack'?'#354c5e':'#dce3e0';
  const body=box(groups.equipment,x,y,0,dx,dy,dz,mat(color),D.boxes.length<220);body.userData.asset=b;pickables.push(body);
  const edge=new THREE.LineSegments(new THREE.EdgesGeometry(cube),new THREE.LineBasicMaterial({color:'#2a4557',transparent:true,opacity:.65,clippingPlanes:[clipping]}));edge.scale.copy(body.scale);edge.position.copy(body.position);edge.visible=false;groups.equipment.add(edge);edges.push(edge);
  const asset={b,body,edge};assets.push(asset);
  if(labelList.length<36)labelList.push(label(b.label,x+dx/2,y+dy/2,dz+.35));
  if(b.kind==='tr'){
    body.scale.set(dx*.66,dz*.54,dy*.66);body.position.y=dz*.34;
    for(let i=0;i<8;i++) for(const side of [0,1]) detail(groups.equipment,x+dx*(.04+i*.117),y+dy*(side?.84:.06),.22,dx*.045,dy*.10,dz*.55,steel);
    for(let i=0;i<3;i++){
      const insulator=new THREE.Mesh(new THREE.CylinderGeometry(dx*.025,dx*.035,dz*.3,12),mat('#5e4740'));insulator.position.set(x+dx*(.3+i*.2),dz*.75,-y-dy*.5);groups.equipment.add(insulator);
      for(let j=0;j<5;j++)detail(groups.equipment,x+dx*(.27+i*.2),y+dy*.46,dz*(.6+j*.055),dx*.06,dy*.08,dz*.016,dark);
    }
  } else if(b.kind==='tank'){
    // Rectangular panel tank preserves the calculated storage footprint and volume.
    for(let i=1;i<Math.min(12,Math.ceil(dx));i++)detail(groups.equipment,x+i*dx/Math.ceil(dx),y-.015,.05,.025,.025,dz-.1,steel);
    for(let j=1;j<4;j++)detail(groups.equipment,x,y-.02,dz*j/4,dx,.025,.025,steel);
    detail(groups.equipment,x+dx*.82,y-.04,.1,.04,.04,dz,steel);
    for(let j=0;j<9;j++)detail(groups.equipment,x+dx*.82,y-.06,.2+j*dz/10,Math.min(.45,dx*.12),.04,.025,steel);
  } else if(b.kind==='rack'){
    for(let k=0;k<7;k++){detail(groups.equipment,x+.04,y-.012,.15+k*dz*.115,Math.max(.05,dx-.08),.035,dz*.087,white);detail(groups.equipment,x+dx*.75,y-.035,.18+k*dz*.115,.04,.02,.025,accent);}
  } else {
    // Corrugation, door seams, louvres and plinth remain within the equipment envelope.
    for(let i=1;i<Math.min(34,Math.ceil(dx/.22));i++)detail(groups.equipment,x+i*dx/Math.ceil(dx/.22),y-.018,.12,.025,.025,dz-.24,white);
    for(let j=0;j<2;j++){
      detail(groups.equipment,x+dx*.035,y+dy*(.08+j*.43),.10,.025,dy*.39,dz*.88,steel);
      detail(groups.equipment,x-.015,y+dy*(.12+j*.43),.16,.035,dy*.33,dz*.8,white);
      detail(groups.equipment,x-.04,y+dy*(.34+j*.43),dz*.32,.035,.035,dz*.4,steel);
    }
    detail(groups.equipment,x,y,dz-.08,dx,dy,.08,white);
    detail(groups.equipment,x,y,.04,dx,dy,.09,dark);
    detail(groups.equipment,x+dx*.65,y-.027,dz*.3,dx*.25,.03,dz*.48,dark);
    for(let k=0;k<8;k++)detail(groups.equipment,x+dx*.66,y-.045,dz*(.32+k*.054),dx*.23,.025,.025,steel);
    detail(groups.equipment,x+dx*.08,y-.04,dz*.68,Math.min(.35,dx*.1),.02,.18,red);
    detail(groups.equipment,x+dx*.08,y-.04,dz*.18,dx*.4,.025,.1,accent);
  }
  return asset;
}
D.boxes.forEach(equipment);
(D.pads||[]).forEach(b=>box(groups.civil,b.x,b.y,b.z??-.3,b.dx,b.dy,b.dz,concrete));
if(!isSite)box(groups.civil,0,0,-.3,W,H,.3,concrete);
for(const path of D.trench||[]) for(let i=1;i<path.length;i++){
  const a=path[i-1],b=path[i],tw=D.trenchWidth;
  box(groups.utilities,Math.min(a[0],b[0])-tw/2,Math.min(a[1],b[1])-tw/2,-D.trenchDepth,Math.abs(a[0]-b[0])+tw,Math.abs(a[1]-b[1])+tw,D.trenchDepth,mat('#b8996d',{transparent:true,opacity:.6}),false);
  line(groups.utilities,[[...a,.035],[...b,.035]],'#e59631');
}
if(isSite){
  const fenceH=D.fenceHeight||2.4;
  const points=[[0,0],[W,0],[W,H],[0,H],[0,0]];
  for(let i=1;i<points.length;i++){
    const a=points[i-1],b=points[i],len=Math.hypot(b[0]-a[0],b[1]-a[1]),n=Math.ceil(len/3);
    for(let j=0;j<=n;j++){const t=j/n;detail(groups.fence,a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,0,.05,.05,fenceH,steel);}
    for(const z of [.2,fenceH*.5,fenceH])line(groups.fence,[[...a,z],[...b,z]],'#6e808b',.7);
    // Fine vertical mesh lines, bounded to avoid geometry explosion on large sites.
    const count=Math.min(160,Math.ceil(len/.3));for(let j=0;j<count;j++){const t=j/count;line(groups.fence,[[a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,0],[a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,fenceH]],'#8c9b9e',.35);}
  }
  // Asphalt only in the clear horizontal aisles between actual equipment rows.
  const rows=[...new Set(D.boxes.filter(b=>b.kind==='enc').map(b=>b.y))].sort((a,b)=>a-b);
  for(let i=1;i<rows.length;i++){
    const end=Math.max(...D.boxes.filter(b=>b.y===rows[i-1]&&['enc','pcs'].includes(b.kind)).map(b=>b.y+b.dy));
    const gap=rows[i]-end;if(gap<2)continue;
    const roadW=Math.min(gap*.65,5);
    box(groups.civil,.4,end+(gap-roadW)/2,-.305,W-.8,roadW,.03,mat('#626d70',{roughness:1}),false);
    for(let x=2;x<W-2;x+=5)detail(groups.civil,x,end+gap/2,-.27,2,.07,.008,white);
  }
} else {
  const shellMat=mat('#b3d2e0',{transparent:true,opacity:.13,depthWrite:false,side:THREE.DoubleSide});
  box(groups.shell,0,H-.04,0,W,.04,Z,shellMat,false);box(groups.shell,W-.04,0,0,.04,H,Z,shellMat,false);
  line(groups.shell,[[0,0,0],[W,0,0],[W,H,0],[0,H,0],[0,0,0]],'#648599');
  line(groups.shell,[[0,0,Z],[W,0,Z],[W,H,Z],[0,H,Z],[0,0,Z]],'#648599');
  for(const [x,y] of [[0,0],[W,0],[W,H],[0,H]])line(groups.shell,[[x,y,0],[x,y,Z]],'#648599');
  for(const v of D.vents||[]){const m=v.intake?accent:steel;box(groups.utilities,v.x-.12,v.y-.12,Z*.75,.24,.24,.22,m);for(let j=0;j<5;j++)detail(groups.utilities,v.x-.1,v.y-.13,Z*.77+j*.035,.2,.02,.012,dark);}
}
for(const b of D.baseline||[])line(groups.baseline,[[b.x,b.y,b.dz],[b.x+b.dx,b.y,b.dz],[b.x+b.dx,b.y+b.dy,b.dz],[b.x,b.y+b.dy,b.dz],[b.x,b.y,b.dz]],'#e0a2dc',.65);
flushDetails();
if(mode==='structure'){
  // Pressure acts at the footprint: ghost the enclosure so the result is visible.
  groups.equipment.traverse(o=>{if(o.isMesh){o.material=o.material.clone();o.material.transparent=true;o.material.opacity=.12;o.material.depthWrite=false;materials.push(o.material);}});
  edges.forEach(e=>e.visible=true);$('edges').classList.add('active');
}
// Dimension callouts and north arrow are geometric; displayed units are metres.
line(groups.civil,[[0,-.8,.02],[W,-.8,.02]],'#385a6d');labelList.push(label(`${W.toFixed(2)} m`,W/2,-.8,.1));
line(groups.civil,[[-.8,0,.02],[-.8,H,.02]],'#385a6d');labelList.push(label(`${H.toFixed(2)} m`,-.8,H/2,.1));
const north=new THREE.ArrowHelper(new THREE.Vector3(0,0,-1),new THREE.Vector3(-1,.05,-H*.15),Math.max(1,span*.07),0x285c74,.5,.25);groups.civil.add(north);

let selected=null, selectionBox=null, frame=0, playing=false, measureOn=false, measurePoints=[], measureLine=null;
const colorStops=['#2676c7','#33bdca','#b8d75b','#f6ad40','#e34b32'].map(c=>new THREE.Color(c));
let minVal=Infinity,maxVal=-Infinity;
for(const f of D.fields||[])for(const row of f)for(const v of row){minVal=Math.min(minVal,v);maxVal=Math.max(maxVal,v);}
if(!Number.isFinite(minVal)){minVal=0;maxVal=1;}if(maxVal-minVal<1)maxVal=minVal+1;
function heatColor(v){const t=THREE.MathUtils.clamp((v-minVal)/(maxVal-minVal),0,1)*4,i=Math.min(3,Math.floor(t));return colorStops[i].clone().lerp(colorStops[i+1],t-i);}
let heatMap,heatTexture,heatCanvas,heatCtx;
if(D.fields?.length && !isFire){
  heatCanvas=document.createElement('canvas');[heatCanvas.width,heatCanvas.height]=D.grid;heatCtx=heatCanvas.getContext('2d');heatTexture=new THREE.CanvasTexture(heatCanvas);heatTexture.colorSpace=THREE.SRGBColorSpace;heatTexture.magFilter=THREE.LinearFilter;
  const material=mat('#ffffff',{map:heatTexture,transparent:true,opacity:.76,side:THREE.DoubleSide,depthWrite:false,roughness:1});
  heatMap=new THREE.Mesh(new THREE.PlaneGeometry(W,H),material);heatMap.rotation.x=-Math.PI/2;heatMap.position.set(W/2,.045,-H/2);groups.results.add(heatMap);
}
const flameMat=mat('#ff8c38',{emissive:'#ff420b',emissiveIntensity:1.3,transparent:true,opacity:.75,depthWrite:false});
const flameObjects=[];
if(isFire||mode==='smoke')for(const a of assets){
  const flame=new THREE.Mesh(new THREE.ConeGeometry(Math.min(a.b.dx,.6)*.55,1.4,9),flameMat);flame.position.set(a.b.x+a.b.dx/2,a.b.dz+.7,-a.b.y-a.b.dy/2);groups.results.add(flame);flameObjects.push(flame);
}
let smokeLayer=null,plumeCloud=null;
if(mode==='smoke'){
  smokeLayer=box(groups.results,0,0,Z-.01,W,H,.01,mat('#515e69',{transparent:true,opacity:.12,depthWrite:false}),false);
  line(groups.results,[[0,0,2],[W,0,2],[W,H,2],[0,H,2],[0,0,2]],'#35c397');
  const sprite=document.createElement('canvas');sprite.width=sprite.height=64;const sc=sprite.getContext('2d'),g=sc.createRadialGradient(32,32,0,32,32,32);g.addColorStop(0,'rgba(220,228,230,0.8)');g.addColorStop(.45,'rgba(150,162,170,0.4)');g.addColorStop(1,'rgba(100,110,120,0)');sc.fillStyle=g;sc.fillRect(0,0,64,64);
  plumeCloud=new THREE.Points(new THREE.BufferGeometry(),new THREE.PointsMaterial({map:new THREE.CanvasTexture(sprite),color:'#76818b',size:.9,transparent:true,opacity:.8,depthWrite:false,clippingPlanes:[clipping]}));groups.results.add(plumeCloud);
}
// Airflow trajectories come directly from the existing kinematic model, never invented CFD.
let flowLine=null,flowPoints=null;
let flowFrame=0;
const flowClock=document.createElement('div');flowClock.style.marginTop='6px';flowClock.style.color='#77dce8';
if(D.airflow){
  $('legend').appendChild(flowClock);
  flowLine=new THREE.LineSegments(new THREE.BufferGeometry(),new THREE.LineBasicMaterial({color:'#e7ffff',transparent:true,opacity:.7}));groups.flow.add(flowLine);
  flowPoints=new THREE.Points(new THREE.BufferGeometry(),new THREE.PointsMaterial({color:'#56f0ff',size:.06,sizeAttenuation:true}));groups.flow.add(flowPoints);
}
function updateFlow(k){if(!D.airflow)return;const a=D.airflow,points=[],lines=[];k=Math.min(k,a.x.length-1);
  flowClock.textContent=L('공기 궤적 별도 시각','Separate airflow time')+` · ${(k*D.airflowDt).toFixed(2)} s`;
  for(let p=0;p<a.x[k].length;p++){
    points.push(a.x[k][p],a.z[k][p],-a.y[k][p]);
    for(let j=Math.max(1,k-5);j<=k;j++){
      const dist=Math.hypot(a.x[j][p]-a.x[j-1][p],a.y[j][p]-a.y[j-1][p],a.z[j][p]-a.z[j-1][p]);
      if(dist<span*.3)lines.push(a.x[j-1][p],a.z[j-1][p],-a.y[j-1][p],a.x[j][p],a.z[j][p],-a.y[j][p]);
    }
  }
  flowPoints.geometry.dispose();flowPoints.geometry=new THREE.BufferGeometry();flowPoints.geometry.setAttribute('position',new THREE.Float32BufferAttribute(points,3));
  flowLine.geometry.dispose();flowLine.geometry=new THREE.BufferGeometry();flowLine.geometry.setAttribute('position',new THREE.Float32BufferAttribute(lines,3));
  if(window.__epcViewer)window.__epcViewer.flowFrame=k;
}
function resetFlow(){flowFrame=0;updateFlow(0);}
const format=v=>Number(v).toFixed(2);
function property(key,value){const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=key;dd.textContent=value;$('properties').append(dt,dd);}
function inspect(asset){
  selected=asset;$('properties').replaceChildren();
  if(!asset){$('selection-kind').textContent=L('프로젝트 범위','PROJECT EXTENT');$('selection-name').textContent=titles[mode];property('X × Y',`${format(W)} × ${format(H)} m`);property(L('설비 수','Equipment'),`${D.boxes.length}`);property(L('좌표계','Coordinates'),'X / Y / Z · m');return;}
  const b=asset.b;$('selection-kind').textContent=kindNames[b.kind]||b.kind;$('selection-name').textContent=b.label;
  property(L('길이 × 폭','Length × width'),`${format(b.dx)} × ${format(b.dy)} m`);property(L('높이','Height'),`${format(b.dz)} m`);property('X / Y',`${format(b.x)} / ${format(b.y)} m`);
  if(b.block)property(L('블록','Block'),String(b.block));
  if(b.cell && D.fields?.[frame]){const [x,y]=b.cell;property(L('계산값','Result'),`${format(D.fields[frame][y][x])} ${D.unit}`);if(D.states)property(L('상태','State'),stateNames[D.states[frame][y][x]]);}
}
function setFrame(k){
  frame=THREE.MathUtils.clamp(k,0,Math.max(0,D.times.length-1));$('timeline').value=frame;
  $('clock').textContent=D.times.length?`t = ${format(D.times[frame])} s`:L('설계 모델','DESIGN MODEL');
  if(heatMap){const field=D.fields[frame],image=heatCtx.createImageData(...D.grid);for(let y=0;y<D.grid[1];y++)for(let x=0;x<D.grid[0];x++){const c=heatColor(field[y][x]).convertLinearToSRGB(),i=((D.grid[1]-1-y)*D.grid[0]+x)*4;image.data.set([c.r*255,c.g*255,c.b*255,255],i);}heatCtx.putImageData(image,0,0);heatTexture.needsUpdate=true;}
  if(D.fields?.[frame]){
    let peak=-Infinity;for(const row of D.fields[frame])for(const v of row)peak=Math.max(peak,v);
    $('readout').textContent=`MAX ${format(peak)} ${D.unit}`;
    for(const a of assets)if(a.b.cell){const [x,y]=a.b.cell;a.body.material.color.copy(isFire?new THREE.Color(stateColors[D.states[frame][y][x]]):heatColor(D.fields[frame][y][x]));}
  }
  if(isFire)flameObjects.forEach((f,i)=>{const [x,y]=assets[i].b.cell,s=D.states[frame][y][x];f.visible=s===3;});
  if(smokeLayer){const z=D.layers[frame];smokeLayer.scale.y=Math.max(.005,Z-z);smokeLayer.position.y=(Z+z)/2;smokeLayer.visible=Z-z>.01;$('readout').textContent=`z = ${format(z)} m · ${format(D.layerTemps[frame])} °C`;
    const points=[];for(const p of D.plume[frame])points.push(p[0],p[2],-p[1]);plumeCloud.geometry.dispose();plumeCloud.geometry=new THREE.BufferGeometry();plumeCloud.geometry.setAttribute('position',new THREE.Float32BufferAttribute(points,3));
  }
  if(mode==='structure')$('readout').textContent+=` · e = ${format(D.eccentricities[frame])} m`;
  if(selected)inspect(selected);
  window.__epcViewer={ready:true,mode,frame,equipmentCount:assets.length,geometry:D.boxes,view:currentView,flowFrame:window.__epcViewer?.flowFrame||0,drawCalls:renderer.info.render.calls};
}
function setPlaying(value){playing=value;$('play').textContent=playing?'Ⅱ':'▶';$('play').setAttribute('aria-label',playing?'Pause':'Play');}
$('timeline').max=Math.max(0,D.times.length-1);$('timeline').disabled=!D.times.length;$('play').disabled=!D.times.length;$('reset').disabled=!D.times.length;
$('timeline').addEventListener('input',()=>{setPlaying(false);accum=0;setFrame(Number($('timeline').value));resetFlow();});
$('play').onclick=()=>{if(frame>=D.times.length-1){setFrame(0);resetFlow();}accum=0;setPlaying(!playing);};
$('reset').onclick=()=>{setPlaying(false);accum=0;setFrame(0);resetFlow();};

const layerNames={equipment:L('설비','Equipment'),civil:L('기초 · 도로','Civil / roads'),utilities:L('트렌치 · 덕트','Trench / ducts'),fence:L('경계 펜스','Fence'),shell:L('외곽 / 단면','Enclosure'),results:L('해석 결과','Result overlay'),flow:L('공기 궤적','Air trajectories'),labels:L('이름 · 치수','Labels / dimensions'),baseline:L('기준안 윤곽','Baseline')};
const layerKeys=isSite?['equipment','civil','utilities','fence','labels',...(D.baseline?.length?['baseline']:[])]:['equipment','civil','shell','utilities','results',...(D.airflow?['flow']:[]),'labels'];
const visibility={labels:true};
for(const key of layerKeys){const labelEl=document.createElement('label');labelEl.className='check';const input=document.createElement('input');input.type='checkbox';input.checked=true;input.dataset.layer=key;input.onchange=()=>{groups[key].visible=input.checked;visibility[key]=input.checked;};labelEl.append(input,document.createTextNode(layerNames[key]));$('layer-list').append(labelEl);}
$('section').oninput=()=>{const value=Z*Number($('section').value)/100;clipping.constant=Number($('section').value)===100?Z+1:value;$('section-value').textContent=`Z ≤ ${format(value)} m`;};$('section').oninput();
$('edges').onclick=()=>{const active=$('edges').classList.toggle('active');edges.forEach(e=>e.visible=active);};
let currentView='iso';
function setView(view){
  currentView=view;const target=new THREE.Vector3(W/2,Math.min(Z*.3,1.5),-H/2);
  camera=view==='iso'?camP:camO;controls.object=camera;camera.up.set(0,1,0);
  if(view==='top'){camera.position.set(W/2,span*2+Z,-H/2);camera.up.set(0,0,-1);target.y=0;}
  else if(view==='front')camera.position.set(W/2,Z*.65,span*1.6);
  else camera.position.set(W/2-span*.70,span*.66+Z,H*.05+span*.65);
  controls.target.copy(target);controls.enableRotate=view==='iso';camera.lookAt(target);controls.update();resize();
  document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===view));if(window.__epcViewer)window.__epcViewer.view=view;
}
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>setView(b.dataset.view));$('fit').onclick=()=>setView(currentView);
function resize(){const w=vp.clientWidth,h=vp.clientHeight;if(w<1||h<1)return;renderer.setSize(w,h);camP.aspect=w/h;camP.updateProjectionMatrix();const s=Math.max(H,W/(w/h),Z)*.65;camO.left=-s*w/h;camO.right=s*w/h;camO.top=s;camO.bottom=-s;camO.updateProjectionMatrix();}
const observer=new ResizeObserver(resize);observer.observe(vp);setView('iso');
const raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2();let down=null;
renderer.domElement.addEventListener('pointerdown',e=>{down=[e.clientX,e.clientY];});
renderer.domElement.addEventListener('pointerup',e=>{
  if(!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>5||e.button!==0)return;
  const rect=renderer.domElement.getBoundingClientRect();pointer.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);raycaster.setFromCamera(pointer,camera);
  const hits=raycaster.intersectObjects(pickables).filter(h=>h.object.parent.visible&&h.point.y<=clipping.constant);if(!hits.length)return;
  if(measureOn){
    if(measurePoints.length===2){measurePoints=[];if(measureLine){scene.remove(measureLine);measureLine.geometry.dispose();measureLine.material.dispose();measureLine=null;}}
    measurePoints.push(hits[0].point.clone());$('measure-result').style.display='block';
    if(measurePoints.length===2){const geo=new THREE.BufferGeometry().setFromPoints(measurePoints);measureLine=new THREE.Line(geo,new THREE.LineBasicMaterial({color:'#05ecff',depthTest:false}));measureLine.renderOrder=999;scene.add(measureLine);$('measure-result').textContent=`${measurePoints[0].distanceTo(measurePoints[1]).toFixed(3)} m · ${L('두 점 직선거리','point-to-point')}`;}
    else $('measure-result').textContent=L('두 번째 점을 선택하세요','Select second point');return;
  }
  const b=hits[0].object.userData.asset;if(!b)return;inspect(assets.find(a=>a.b===b));
  if(selectionBox){scene.remove(selectionBox);selectionBox.dispose();}selectionBox=new THREE.BoxHelper(hits[0].object,0x00cce8);scene.add(selectionBox);
});
$('measure').onclick=()=>{measureOn=!measureOn;$('measure').classList.toggle('active',measureOn);$('measure-result').style.display=measureOn?'block':'none';$('measure-result').textContent=L('측정할 두 점을 클릭하세요','Click two points to measure');};
$('shot').onclick=()=>{renderer.render(scene,camera);const a=document.createElement('a');a.download=`epc-${mode}-${frame}.png`;a.href=renderer.domElement.toDataURL('image/png');a.click();};
$('fullscreen').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await $('app').requestFullscreen();}catch{$('status').textContent=L('브라우저가 전체화면을 허용하지 않습니다.','Fullscreen unavailable in this browser.');}};
document.addEventListener('fullscreenchange',()=>{$('app').style.height=document.fullscreenElement?'100vh':'640px';resize();});
if(isSite){$('legend-title').textContent=L('설계 모델 · 실치수','Design model · metre scale');$('gradient').style.display='none';$('legend-scale').textContent=L('컨테이너 / PCS / 변압기 / 수조','Enclosure / PCS / transformer / tank');}
else if(isFire){$('legend-title').textContent=L('계산된 랙 상태 · 화염은 설명용','Calculated rack states · illustrative flames');$('gradient').style.display='none';$('legend-scale').style.display='block';stateNames.forEach((s,i)=>{const el=document.createElement('span');el.textContent=`■ ${s}  `;el.style.color=stateColors[i];$('legend-scale').append(el);});}
else if(mode==='smoke'){$('legend-title').textContent=L('계산된 연기층 경계 · 녹색선 2 m','Computed layer interface · green line 2 m');$('gradient').style.display='none';$('legend-scale').textContent=L('플룸 형상은 설명용','Plume geometry illustrative');}
else {$('legend-title').textContent=mode==='structure'?L('기초 지지압 · 변형 미산정','Bearing pressure · no deformation solved'):L('깊이 평균 공기온도 · 바닥 투영','Depth-averaged air temperature · floor projection');$('legend-scale').innerHTML=`<span>${format(minVal)}</span><span>${format(maxVal)} ${D.unit}</span>`;}
$('status').textContent=D.airflow?L('열: FDM · 공기: 운동학 궤적(정상 열장), CFD 아님','Heat: FDM · flow: kinematic trajectories (final thermal field), not CFD'):isSite?L('휠 확대 · 설비 클릭 · 단위 m','Scroll to zoom · click equipment · units m'):L('축소 해석 모델 · 정량 그래프는 아래 참조','Reduced-order model · analytical plots below');
inspect(null);setFrame(0);updateFlow(0);
let last=performance.now(),accum=0,active=true;
const intersection=new IntersectionObserver(entries=>{active=entries[0].isIntersecting;});intersection.observe($('app'));
renderer.setAnimationLoop(now=>{
  const dt=Math.min((now-last)/1000,.1);last=now;if(document.hidden||!active)return;
  controls.update();
  if(playing){accum+=dt;if(accum>.35){accum=0;if(frame<D.times.length-1){setFrame(frame+1);if(D.airflow){flowFrame=(flowFrame+1)%D.airflow.x.length;updateFlow(flowFrame);}}else setPlaying(false);}}
  for(const f of flameObjects)if(f.visible){f.scale.x=1+.08*Math.sin(frame*2);f.scale.z=f.scale.x;}
  for(const l of labelList){const p=l.pos.clone().project(camera);l.el.style.display=visibility.labels!==false&&p.z<1&&p.z>-1?'block':'none';l.el.style.left=`${(p.x*.5+.5)*vp.clientWidth}px`;l.el.style.top=`${(-p.y*.5+.5)*vp.clientHeight}px`;}
  renderer.render(scene,camera);
});
window.addEventListener('pagehide',()=>{renderer.setAnimationLoop(null);observer.disconnect();intersection.disconnect();controls.dispose();scene.traverse(o=>{if(o.geometry)o.geometry.dispose();});materials.forEach(m=>m.dispose());renderer.dispose();});
