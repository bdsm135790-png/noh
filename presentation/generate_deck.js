const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE";
p.author = "팀 군체";
p.title = "AI 기반 드론-UGV 협업 도심 화재·재난 정밀 진압 모델";

const RR = p.ShapeType.roundRect, RECT = p.ShapeType.rect, OVAL = p.ShapeType.ellipse,
      TRI = p.ShapeType.triangle, LINE = p.ShapeType.line;
const F = "Malgun Gothic", FM = "Consolas";

const C = {
  bg:"0F172A", bgDark:"0B1220", panel:"0B1220",
  card:"1E293B", card2:"172033", border:"334155", border2:"1E293B",
  text:"E2E8F0", mute:"94A3B8", dim:"64748B",
  orange:"F97316", orange2:"FB923C",
  blue:"38BDF8", blue2:"0EA5E9", blueDk:"1E3A5F",
  red:"DC2626", red2:"F87171", redSoft:"FCA5A5", redDk:"3F1D1D", redBg:"2A1215",
  green:"4ADE80", green2:"86EFAC", mint:"34D399",
  yellow:"FBBF24", amber:"F59E0B", violet:"A78BFA", violetDk:"7C3AED", indigo:"6366F1",
  fuel:"334155", burnt:"1C1917", wet:"0C4A6E",
};
// 편대 색 (시뮬레이션 SQUADS)
const SQ = {
  GCS:"94A3B8", RECON:"A78BFA", SAR:"38BDF8", SUP:"2563EB", COMMS:"F59E0B",
};
const bg = (s, c=C.bg) => { s.background = { color:c }; };
function header(s, kicker, title, kColor=C.orange){
  s.addText(kicker.toUpperCase(), {x:0.6, y:0.42, w:12.1, h:0.3, fontFace:F,
    fontSize:12.5, color:kColor, bold:true, charSpacing:3, margin:0});
  s.addText(title, {x:0.6, y:0.72, w:12.1, h:0.72, fontFace:F,
    fontSize:28, color:C.text, bold:true, margin:0});
}
function card(s, x, y, w, h, fill=C.card, border=C.border, radius=0.09){
  s.addShape(RR, {x,y,w,h, rectRadius:radius, fill:{color:fill}, line:{color:border, width:1}});
}
function dot(s, x, y, d, color, ring){
  s.addShape(OVAL, {x, y, w:d, h:d, fill:{color}, line: ring ? {color:ring, width:1} : {type:"none"}});
}
function chip(s, x, y, w, text, color){
  s.addShape(RR, {x, y, w, h:0.34, rectRadius:0.17, fill:{color:C.bgDark}, line:{color, width:1}});
  s.addText(text, {x, y, w, h:0.34, align:"center", valign:"middle", fontFace:F,
    fontSize:10.5, color, bold:true, margin:0});
}
/* 화재 격자 모티프 */
const OR = 5.4, OC = 5.2;
function burnCol(d, a, b){ const f=(d-a)/(b-a); return f>0.62?C.yellow:f>0.32?C.orange:C.red; }
function cellColor(r, c, stage){
  if (r === 8) return C.blueDk;
  if (c === 3) return C.blueDk;
  if (c === 7) return C.redDk;
  const d = Math.hypot(r-OR, c-OC);
  const front = ((r-OR)*0.7 + (OC-c)*0.7);
  const jump = (c>=8 && c<=10 && r>=3 && r<=6), jd = Math.hypot(r-4.5, c-9);
  if (stage===0){ if(d<=1.25)return C.red; if(d<=1.9)return C.orange; return C.fuel; }
  if (stage===1){ if(d<=1.7)return C.burnt; if(d<=3.9)return burnCol(d,1.7,3.9);
    if(jump&&jd<=1.4)return burnCol(jd,0,1.4); return C.fuel; }
  if (stage===2){ if(d<=2.1)return C.burnt; if(d<=3.7)return burnCol(d,2.1,3.7);
    if(d>3.7&&d<=4.9&&front>0.2)return C.wet; if(jump&&jd<=1.1)return C.wet; return C.fuel; }
  if (d<=4.7) return ((r*2+c)%3===0)?C.wet:C.burnt;
  if (jump&&jd<=1.4) return C.wet; return C.fuel;
}
function fireGrid(s, gx, gy, cell, stage, opts={}){
  const N = 12;
  s.addShape(RR, {x:gx-0.08, y:gy-0.08, w:N*cell+0.16, h:N*cell+0.16, rectRadius:0.06,
    fill:{color:C.panel}, line:{color:C.border, width:1}});
  for (let r=0;r<N;r++) for (let c=0;c<N;c++)
    s.addShape(RECT, {x:gx+c*cell, y:gy+r*cell, w:cell, h:cell, fill:{color:cellColor(r,c,stage)}, line:{type:"none"}});
  dot(s, gx+OC*cell, gy+OR*cell, cell*0.9, C.yellow, "78350F");
  (opts.drones||[]).forEach(([dr,dc]) => dot(s, gx+dc*cell, gy+dr*cell, cell*0.72, C.orange, "FED7AA"));
  if (opts.label)
    s.addText(opts.label, {x:gx-0.08, y:gy+N*cell+0.02, w:N*cell+0.16, h:0.3, align:"center",
      fontFace:F, fontSize:11, color:opts.labelColor||C.mute, bold:true, margin:0});
}

/* ═════════ ① 표지 ═════════ */
{
  const s = p.addSlide(); bg(s, C.bgDark);
  fireGrid(s, 8.75, 1.55, 0.31, 2, {drones:[[3,5],[4,9],[8,4],[2,7]]});
  s.addText("제6회 빅데이터로 우리동네 문제해결 아이디어 공모대회 · 경남", {
    x:0.72, y:0.62, w:7.7, h:0.32, fontFace:F, fontSize:12.5, color:C.blue, bold:true, margin:0});
  chip(s, 0.72, 1.02, 1.55, "방산융합", C.violet);
  chip(s, 2.37, 1.02, 1.35, "자유주제", C.orange);
  s.addText([
    {text:"AI 드론 – 지상 무인차량(UGV) 협업\n", options:{color:C.text}},
    {text:"도심 화재·재난 정밀 진압 모델", options:{color:C.orange}},
  ], {x:0.7, y:1.65, w:7.9, h:1.85, fontFace:F, fontSize:33, bold:true, lineSpacingMultiple:1.08, margin:0});
  s.addText("국방 군집 무인체계 알고리즘의 민간 스마트시티 재난 대응 스핀오프", {
    x:0.72, y:3.62, w:7.8, h:0.45, fontFace:F, fontSize:15, color:C.mute, margin:0});
  card(s, 0.72, 4.35, 7.5, 1.1, C.card, C.border);
  s.addText([
    {text:"유무인 복합 재난 진압 편대 시스템\n", options:{color:C.text, bold:true, fontSize:15}},
    {text:"소방차가 못 들어가는 화재 취약지의 초동 골든타임을 드론 편대가 확보한다.", options:{color:C.mute, fontSize:12.5}},
  ], {x:0.98, y:4.35, w:7.0, h:1.1, valign:"middle", fontFace:F, lineSpacingMultiple:1.15, margin:0});
  s.addText([
    {text:"팀 군체", options:{color:C.orange, bold:true}},
    {text:"   ·   한태영 · 김상도 · 노현수   ·   경상국립대학교 USG융합전공 방산시스템", options:{color:C.dim}},
  ], {x:0.72, y:6.35, w:11, h:0.4, fontFace:F, fontSize:12.5, margin:0});
}

/* ═════════ ② 배경 ═════════ */
{
  const s = p.addSlide(); bg(s);
  header(s, "01 · 기획 배경", "경남 원도심 · 전통시장의 좁은 골목");
  const rows = [
    ["구도심·전통시장 밀집", "마산어시장·부림시장·진해 중앙동 등 노후 시가지는 폭이 좁은 이면도로와 골목으로 얽혀 있다."],
    ["목조·경량 밀집 시가지", "건물이 붙어 있고 가연물이 많아, 한 곳의 발화가 곧 이웃 건물로 옮겨붙는다."],
    ["고령·교통약자 밀집", "대피가 어려운 65세 이상 고령층이 많아, 초기 대응이 늦으면 인명 피해로 직결된다."],
  ];
  let y = 1.75;
  rows.forEach(([t, d], i) => {
    card(s, 0.6, y, 6.35, 1.5, C.card, C.border);
    dot(s, 0.9, y+0.32, 0.5, C.bgDark, C.orange);
    s.addText(String(i+1), {x:0.9, y:y+0.32, w:0.5, h:0.5, align:"center", valign:"middle",
      fontFace:FM, fontSize:17, color:C.orange, bold:true, margin:0});
    s.addText(t, {x:1.6, y:y+0.2, w:5.15, h:0.4, fontFace:F, fontSize:16, color:C.text, bold:true, margin:0});
    s.addText(d, {x:1.6, y:y+0.62, w:5.2, h:0.75, fontFace:F, fontSize:12.5, color:C.mute, margin:0, lineSpacingMultiple:1.05});
    y += 1.65;
  });
  // 우: 골목 도식
  const px=7.35, py=1.75, pw=5.35, ph=4.95;
  s.addShape(RR, {x:px, y:py, w:pw, h:ph, rectRadius:0.08, fill:{color:C.panel}, line:{color:C.border, width:1}});
  const blk=(bx,by,bw,bh)=>s.addShape(RECT,{x:bx,y:by,w:bw,h:bh,fill:{color:C.fuel},line:{color:C.border2,width:1}});
  const gcols=[px+0.35,px+2.05,px+3.75], roadX=[px+1.75,px+3.45];
  for(let r=0;r<4;r++){ const by=py+0.4+r*1.12; gcols.forEach(cx=>blk(cx,by,1.35,0.9)); }
  roadX.forEach(rx=>s.addShape(RECT,{x:rx,y:py+0.35,w:0.28,h:ph-0.65,fill:{color:C.redDk},line:{type:"none"}}));
  s.addShape(RECT,{x:px+0.2,y:py+ph-0.55,w:pw-0.4,h:0.34,fill:{color:C.blueDk},line:{type:"none"}});
  s.addText("폭 3.0m", {x:roadX[0]-0.55, y:py+0.05, w:1.4, h:0.28, align:"center", fontFace:FM, fontSize:10.5, color:C.redSoft, bold:true, margin:0});
  s.addText("소방차 진입 가능 도로", {x:px+0.2, y:py+ph-0.55, w:pw-0.4, h:0.34, valign:"middle", align:"center", fontFace:F, fontSize:10.5, color:C.blue, bold:true, margin:0});
  s.addText("건물이 붙어 있고 골목이 좁다", {x:px, y:py+ph+0.08, w:pw, h:0.3, align:"center", fontFace:F, fontSize:11, color:C.dim, margin:0});
  s.addNotes("경남 원도심·전통시장의 좁은 골목, 밀집 시가지, 고령 인구 — 세 조건이 화재 위험을 키운다.");
}

/* ═════════ ③ 문제 정의 ═════════ */
{
  const s = p.addSlide(); bg(s);
  header(s, "01 · 문제 정의", "가장 위험한 곳에, 가장 늦게 도착한다");
  const cards = [
    ["4m", "미만 도로 = 소방차 진입 불가", "소방차 최소 통행폭 기준. 좁은 골목엔 진입 자체가 막힌다.", C.red2, C.redBg, "7F1D1D"],
    ["1인 1기", "기존 소방 드론의 한계", "조종사 1명이 드론 1기만 운용 — 급확산 대형 재난의 입체 대응 불가.", C.orange, C.card, C.border],
    ["복사열", "불은 좁은 골목을 건너뛴다", "3~6m 간극은 자연 방화선이 못 된다 — 골목을 그대로 넘어 번진다.", C.yellow, C.card, C.border],
  ];
  let x = 0.6; const cw=3.9, gap=0.2, cy=1.85, ch=2.9;
  cards.forEach(([big, t, d, col, fill, bd]) => {
    card(s, x, cy, cw, ch, fill, bd);
    s.addText(big, {x:x+0.1, y:cy+0.28, w:cw-0.2, h:0.85, align:"center", fontFace:FM,
      fontSize: big.length>3?40:52, color:col, bold:true, margin:0});
    s.addText(t, {x:x+0.15, y:cy+1.2, w:cw-0.3, h:0.5, align:"center", fontFace:F, fontSize:14, color:C.text, bold:true, margin:0});
    s.addText(d, {x:x+0.25, y:cy+1.75, w:cw-0.5, h:1.0, align:"center", fontFace:F, fontSize:11.5, color:C.mute, margin:0, lineSpacingMultiple:1.15, valign:"top"});
    x += cw + gap;
  });
  card(s, 0.6, 5.05, 12.1, 1.3, C.card2, C.border);
  s.addText([
    {text:"초동 골든타임을 확보할 상공 대응 수단이 필요하다.  ", options:{color:C.text, bold:true}},
    {text:"소방관이 직접 진입하기 전, 다수의 무인체가 스스로 현장을 감시하고 진압을 시작해야 한다.", options:{color:C.mute}},
  ], {x:0.9, y:5.05, w:11.5, h:1.3, valign:"middle", fontFace:F, fontSize:14, lineSpacingMultiple:1.2, margin:0});
  s.addNotes("세 가지 한계: 소방차 진입불가, 기존 소방드론 1인1기, 복사열 확산. 그래서 자율 군집 상공 대응이 필요하다.");
}

/* ═════════ ④ 해결 접근 (방산 스핀오프) ═════════ */
{
  const s = p.addSlide(); bg(s);
  header(s, "01 · 해결 접근", "국방 군집 알고리즘을 민간 재난 대응으로", C.violet);
  // 스핀오프 플로우
  const boxes = [
    ["국방 군집 무인체계", "다수 무인체 상호 통신 · 자율 최적경로 · 임무 자율 배정", C.violet, C.violetDk],
    ["기술 전용 (Spin-off)", "방산시스템 전공 군집 운용 알고리즘", C.orange, "7C2D12"],
    ["민간 스마트시티 재난대응", "화재 취약지 초동 진압 · 유무인 복합 편대", C.green, "166534"],
  ];
  let x=0.6; const cw=3.7, gap=0.62, cy=1.95, ch=2.15;
  boxes.forEach(([t,d,col,bd],i)=>{
    card(s, x, cy, cw, ch, C.card, bd);
    s.addText(t, {x:x+0.25, y:cy+0.3, w:cw-0.5, h:0.85, fontFace:F, fontSize:16.5, color:col, bold:true, margin:0, valign:"top", lineSpacingMultiple:1.05});
    s.addText(d, {x:x+0.25, y:cy+1.1, w:cw-0.5, h:0.95, fontFace:F, fontSize:12, color:C.mute, margin:0, lineSpacingMultiple:1.2, valign:"top"});
    if(i<2) s.addText("›", {x:x+cw+0.02, y:cy, w:gap-0.04, h:ch, align:"center", valign:"middle", fontFace:F, fontSize:34, color:C.dim, bold:true, margin:0});
    x += cw+gap;
  });
  card(s, 0.6, 4.5, 12.1, 1.85, C.card2, C.border);
  s.addText("추진 배경 — 방산-민간 기술 스핀오프", {x:0.9, y:4.7, w:11, h:0.4, fontFace:F, fontSize:15, color:C.violet, bold:true, margin:0});
  s.addText([
    {text:"현재 소방 드론은 1인 1기 운용이라 대형 재난의 입체 대응에 한계가 있다. ", options:{color:C.mute}},
    {text:"방산시스템 전공에서 학습한 군집 체계 자율 운용 기술", options:{color:C.text, bold:true}},
    {text:"을 도시 인프라에 결합하면, 인명 피해를 최소화하고 소방관 안전을 보장하는 최첨단 스마트 재난 대응 인프라를 실현할 수 있다.", options:{color:C.mute}},
  ], {x:0.9, y:5.15, w:11.5, h:1.1, fontFace:F, fontSize:13.5, lineSpacingMultiple:1.25, margin:0});
  s.addNotes("핵심 프레이밍: 국방 군집 알고리즘 → 스핀오프 → 민간 재난대응. 1인1기 한계를 자율 군집으로 넘는다.");
}

/* ═════════ ⑤ 실행계획 · 데이터 파이프라인 ═════════ */
{
  const s = p.addSlide(); bg(s);
  header(s, "02 · 기술 스택 · 데이터 파이프라인", "실행계획 2단계", C.blue);
  // 1단계
  card(s, 0.6, 1.8, 6.0, 4.55, C.card, C.border);
  dot(s, 0.9, 2.05, 0.55, C.bgDark, C.blue);
  s.addText("1", {x:0.9, y:2.05, w:0.55, h:0.55, align:"center", valign:"middle", fontFace:FM, fontSize:20, color:C.blue, bold:true, margin:0});
  s.addText("빅데이터 기반 취약지 도출", {x:1.6, y:2.08, w:4.8, h:0.5, fontFace:F, fontSize:16.5, color:C.text, bold:true, margin:0});
  const s1=[
    "경남소방본부 화재 이력 + 도로폭 데이터 결합",
    "공간 네트워크 분석 — 골든타임(5분) 내 소방차 도달 불가 지역 시각화",
    "시스템 우선 도입 스마트 방재 거점 최적 입지 선정",
  ];
  let y1=2.85;
  s1.forEach(t=>{ dot(s,0.95,y1+0.07,0.14,C.blue); s.addText(t,{x:1.25,y:y1-0.05,w:5.1,h:0.7,fontFace:F,fontSize:12.5,color:C.mute,margin:0,lineSpacingMultiple:1.1,valign:"top"}); y1+=0.75; });
  // 2단계
  card(s, 6.7, 1.8, 6.0, 4.55, C.card, C.border);
  dot(s, 7.0, 2.05, 0.55, C.bgDark, C.orange);
  s.addText("2", {x:7.0, y:2.05, w:0.55, h:0.55, align:"center", valign:"middle", fontFace:FM, fontSize:20, color:C.orange, bold:true, margin:0});
  s.addText("동역학 시뮬 · 군집 최적화", {x:7.7, y:2.08, w:4.8, h:0.5, fontFace:F, fontSize:16.5, color:C.text, bold:true, margin:0});
  const s2=[
    "MATLAB · Ansys로 좁은 구도심 골목 3D 가상 인프라 구축",
    "국방 군집 기술 기반 충돌 방지 · 경로 분산 · 자율 임무 배정 설계",
    "기구학·동역학 안정성 및 에너지 효율성 시뮬레이션 검증",
  ];
  let y2=2.85;
  s2.forEach(t=>{ dot(s,7.05,y2+0.07,0.14,C.orange); s.addText(t,{x:7.35,y:y2-0.05,w:5.1,h:0.7,fontFace:F,fontSize:12.5,color:C.mute,margin:0,lineSpacingMultiple:1.1,valign:"top"}); y2+=0.75; });
  s.addNotes("1단계 데이터로 어디에 배치할지 정하고, 2단계 시뮬레이션으로 군집이 어떻게 움직일지 최적화한다.");
}

/* ═════════ ⑥ 분석용 빅데이터 ═════════ */
{
  const s = p.addSlide(); bg(s);
  header(s, "02 · 기술 스택 · 데이터 파이프라인", "빅데이터 분석용 데이터", C.blue);
  const data = [
    ["통계청 KOSIS · SGIS", "주민등록 인구 · 고령인구(65세+) 통계", "대피 취약 교통약자 밀집 위험지역 추출", C.blue],
    ["공공데이터포털 data.go.kr", "소방용수시설 · 소방차 진입곤란 지역 현황", "진입불가 격자 매핑 · 드론·UGV 방재 거점 선정", C.orange],
    ["국가공간정보포털", "건축물대장 표준데이터 · 수치지형도 (CSV/SHP)", "노후 건축물 비율 필터링 → 화재 취약 지수 산출", C.green],
  ];
  let x=0.6; const cw=3.9, gap=0.2, cy=1.8, ch=3.15;
  data.forEach(([src,name,use,col])=>{
    card(s, x, cy, cw, ch, C.card, C.border);
    s.addText(src, {x:x+0.28, y:cy+0.28, w:cw-0.56, h:0.7, fontFace:F, fontSize:14.5, color:col, bold:true, margin:0, valign:"top", lineSpacingMultiple:1.05});
    s.addShape(RR, {x:x+0.28, y:cy+1.05, w:cw-0.56, h:0.9, rectRadius:0.05, fill:{color:C.bgDark}, line:{color:C.border2, width:1}});
    s.addText(name, {x:x+0.42, y:cy+1.12, w:cw-0.84, h:0.78, fontFace:F, fontSize:11.5, color:C.text, margin:0, valign:"middle", lineSpacingMultiple:1.1});
    s.addText([{text:"활용  ", options:{color:C.dim, bold:true}}, {text:use, options:{color:C.mute}}],
      {x:x+0.28, y:cy+2.1, w:cw-0.56, h:0.95, fontFace:F, fontSize:11.5, margin:0, lineSpacingMultiple:1.2, valign:"top"});
    x += cw+gap;
  });
  card(s, 0.6, 5.2, 12.1, 1.15, C.card2, C.border);
  s.addText("Python 데이터 프로세싱", {x:0.9, y:5.36, w:4, h:0.4, fontFace:F, fontSize:13.5, color:C.green2, bold:true, margin:0});
  let cxp=5.0; ["Pandas","NumPy","Matplotlib","Seaborn"].forEach(t=>{ chip(s,cxp,5.34,1.55,t,C.blue); cxp+=1.7; });
  s.addText("수집·정제 → 상관관계 시각화 → 거점 후보 도출", {x:0.9, y:5.82, w:11, h:0.4, fontFace:F, fontSize:12, color:C.mute, margin:0});
  s.addNotes("공공 빅데이터 3종으로 취약지와 거점을 데이터 기반으로 선정한다. 파이썬 스택으로 수집·시각화.");
}

/* ═════════ ⑦ 기술 스택 · 구현 ═════════ */
{
  const s = p.addSlide(); bg(s);
  header(s, "02 · 기술 스택 · 데이터 파이프라인", "구현 · 프로토타입 기술 스택", C.blue);
  const groups = [
    ["현장 지도 · 라우팅", C.blue, [["Leaflet · OSM 실측", "소방서 거점 · 진입가능/불가 도로"],["OSRM", "소방차 실도로 최속경로·주행시간"]]],
    ["3D 시뮬레이션", C.violet, [["Three.js", "2층 건물 3D · 편대별 드론 메쉬"],["실주소 화재확산", "도로망·골목폭·복사열 격자 모델"]]],
    ["군집 로직 코어", C.orange, [["Python 상태머신", "SOP-D 임무 상태 전이 (house_mission)"],["군집 알고리즘", "충돌방지·경로분산·자율 임무배정"]]],
  ];
  let x=0.6; const cw=3.9, gap=0.2, cy=1.8, ch=4.05;
  groups.forEach(([title,col,items])=>{
    card(s, x, cy, cw, ch, C.card, C.border);
    dot(s, x+0.3, cy+0.3, 0.42, C.bgDark, col); dot(s, x+0.4, cy+0.4, 0.22, col);
    s.addText(title, {x:x+0.85, y:cy+0.26, w:cw-1.0, h:0.5, valign:"middle", fontFace:F, fontSize:14, color:C.text, bold:true, margin:0});
    let iy=cy+1.05;
    items.forEach(([t,d])=>{
      s.addShape(RR, {x:x+0.28, y:iy, w:cw-0.56, h:1.28, rectRadius:0.06, fill:{color:C.bgDark}, line:{color:C.border2, width:1}});
      s.addText(t, {x:x+0.45, y:iy+0.15, w:cw-0.9, h:0.4, fontFace:F, fontSize:12.5, color:col, bold:true, margin:0});
      s.addText(d, {x:x+0.45, y:iy+0.55, w:cw-0.9, h:0.65, fontFace:F, fontSize:10.5, color:C.mute, margin:0, lineSpacingMultiple:1.1, valign:"top"});
      iy += 1.42;
    });
    x += cw+gap;
  });
  s.addText("※ 공모 시연 프로토타입은 공개 API(OSM·OSRM)와 Three.js로 구현 — 본 사업에서는 경남 공공 빅데이터로 확장.", {
    x:0.6, y:6.02, w:12.1, h:0.35, fontFace:F, fontSize:10.5, color:C.dim, italic:true, margin:0});
}

/* ═════════ ⑧ 확산 모델 원리 ═════════ */
{
  const s = p.addSlide(); bg(s);
  header(s, "03 · 화재 확산 시뮬레이션", "확산 모델은 이렇게 움직인다", C.orange);
  fireGrid(s, 0.9, 1.95, 0.33, 1, {});
  const leg = [["건물(가연물)", C.fuel], ["진입가능 도로", C.blueDk], ["협소 골목", C.redDk], ["연소", C.orange], ["전소", C.burnt], ["드론 진압", C.wet]];
  leg.forEach(([t,col],i)=>{ const lx=0.78+(i%3)*1.75, ly=6.2+Math.floor(i/3)*0.35;
    s.addShape(RECT,{x:lx,y:ly+0.03,w:0.18,h:0.18,fill:{color:col},line:{type:"none"}});
    s.addText(t,{x:lx+0.24,y:ly-0.04,w:1.5,h:0.3,fontFace:F,fontSize:9.5,color:C.mute,margin:0}); });
  const items = [
    ["실제 도로망을 골격으로", "도로 사이 가구(街區)를 건물 조직으로 복원해 3m 격자로 채운다."],
    ["골목 폭이 확산을 가른다", "넓은 도로는 자연 방화선, 좁은 골목은 복사열로 불을 그대로 건너보낸다."],
    ["소방차 진입 가능성 반영", "폭 4m 미만 구간과 진입곤란 지역을 우선 데이터로 표시한다."],
  ];
  let y=2.0;
  items.forEach(([t,d])=>{ card(s,6.35,y,6.35,1.28,C.card,C.border);
    s.addText(t,{x:6.6,y:y+0.16,w:5.9,h:0.4,fontFace:F,fontSize:15,color:C.orange,bold:true,margin:0});
    s.addText(d,{x:6.6,y:y+0.58,w:5.95,h:0.62,fontFace:F,fontSize:12,color:C.mute,margin:0,lineSpacingMultiple:1.05}); y+=1.42; });
  s.addText("조절 변수", {x:6.35, y:6.3, w:2, h:0.3, fontFace:F, fontSize:11, color:C.dim, bold:true, margin:0});
  let vx=7.55; ["풍향","풍속","건물 밀집도","인지~도착"].forEach(v=>{ chip(s,vx,6.26,1.2,v,C.blue); vx+=1.3; });
}

/* ═════════ ⑨ 시연 4컷 ═════════ */
{
  const s = p.addSlide(); bg(s);
  header(s, "03 · 화재 확산 시뮬레이션", "시연 — 발화부터 완전 진화까지", C.orange);
  const panels = [
    [0,"발화","실제 도면상 건물에서 착화",[]],
    [1,"확산","골목을 건너 외곽으로 번짐",[]],
    [2,"포위 진압","드론 편대 외곽 화선 차단",[[3,5],[4,9],[8,4],[7,7],[2,7]]],
    [3,"완전 진화","신규 착화 중단 → 진화",[[5,4],[6,8],[4,6]]],
  ];
  const cell=0.19, gx0=1.4, gy0=1.85, stepx=6.1, stepy=2.55, tdx=2.55;
  panels.forEach(([stage,t,d,drones],i)=>{
    const gx=gx0+(i%2)*stepx, gy=gy0+Math.floor(i/2)*stepy;
    fireGrid(s, gx, gy, cell, stage, {drones});
    s.addText(`${i+1}. ${t}`, {x:gx+tdx, y:gy+0.35, w:2.6, h:0.4, fontFace:F, fontSize:15, color:C.orange, bold:true, margin:0});
    s.addText(d, {x:gx+tdx, y:gy+0.82, w:2.6, h:1.4, fontFace:F, fontSize:11.5, color:C.mute, margin:0, lineSpacingMultiple:1.15, valign:"top"});
  });
  s.addText("국면: 확산 → 포위 진압 → 화선 후퇴 → 확산 저지 → 완전 진화 (전환 시각 자동 기록)", {
    x:0.6, y:6.9, w:12.1, h:0.35, align:"center", fontFace:F, fontSize:11, color:C.dim, italic:true, margin:0});
}

/* ═════════ ⑩ 대응시간 비교 ═════════ */
{
  const s = p.addSlide(); bg(s);
  header(s, "03 · 화재 확산 시뮬레이션", "대응시간 — 소방차 vs 드론 편대", C.orange);
  s.addText("화재 인지 시점을 공통 기준으로 비교 (진입불가 지점 예시 시나리오)", {
    x:0.6, y:1.5, w:12, h:0.35, fontFace:F, fontSize:12.5, color:C.mute, margin:0});
  card(s, 0.6, 2.05, 3.85, 3.05, C.card, C.border);
  s.addText("소방차", {x:0.6, y:2.3, w:3.85, h:0.4, align:"center", fontFace:F, fontSize:16, color:C.blue, bold:true, margin:0});
  s.addText("실도로 주행 + 출동준비", {x:0.6, y:2.72, w:3.85, h:0.35, align:"center", fontFace:F, fontSize:11, color:C.mute, margin:0});
  s.addText("8:40", {x:0.6, y:3.15, w:3.85, h:1.0, align:"center", fontFace:FM, fontSize:52, color:C.blue, bold:true, margin:0});
  s.addText("+ 좁은 골목은 입구까지만", {x:0.6, y:4.35, w:3.85, h:0.5, align:"center", fontFace:F, fontSize:11.5, color:C.redSoft, margin:0});
  card(s, 4.65, 2.05, 3.85, 3.05, "1F1206", C.orange);
  s.addText("드론 편대 (직선 비행)", {x:4.65, y:2.3, w:3.85, h:0.4, align:"center", fontFace:F, fontSize:16, color:C.orange, bold:true, margin:0});
  s.addText("최근접 거점 → 화점 직상공", {x:4.65, y:2.72, w:3.85, h:0.35, align:"center", fontFace:F, fontSize:11, color:C.orange2, margin:0});
  s.addText("3:20", {x:4.65, y:3.15, w:3.85, h:1.0, align:"center", fontFace:FM, fontSize:52, color:C.orange, bold:true, margin:0});
  s.addText("골목 위를 그대로 넘어 도착", {x:4.65, y:4.35, w:3.85, h:0.5, align:"center", fontFace:F, fontSize:11.5, color:C.orange2, margin:0});
  card(s, 8.7, 2.05, 4.0, 3.05, C.card2, "166534");
  s.addText("드론이 먼저", {x:8.7, y:2.35, w:4.0, h:0.4, align:"center", fontFace:F, fontSize:15, color:C.green2, bold:true, margin:0});
  s.addText("5:20", {x:8.7, y:2.85, w:4.0, h:1.1, align:"center", fontFace:FM, fontSize:60, color:C.green, bold:true, margin:0});
  s.addText("먼저 도착", {x:8.7, y:3.95, w:4.0, h:0.4, align:"center", fontFace:F, fontSize:16, color:C.green2, bold:true, margin:0});
  s.addText("초동 골든타임을 확보한다", {x:8.7, y:4.45, w:4.0, h:0.4, align:"center", fontFace:F, fontSize:12, color:C.mute, margin:0});
  s.addText([{text:"공통 인지·신고 지연은 양쪽에 동일 적용. ", options:{color:C.dim}},
    {text:"소방차 = OSRM 실도로 라우팅 + 출동준비 1분, 드론 = 거점→화점 직선 비행.", options:{color:C.mute}}],
    {x:0.6, y:5.35, w:12.1, h:0.5, fontFace:F, fontSize:12, margin:0, lineSpacingMultiple:1.1});
  s.addText("※ 수치는 예시 시나리오 — 지점·거점 거리에 따라 달라진다.", {x:0.6, y:6.05, w:12, h:0.35, fontFace:F, fontSize:10.5, color:C.dim, italic:true, margin:0});
}

/* ═════════ ⑪ 군집 자율비행 기반 ═════════ */
{
  const s = p.addSlide(); bg(s);
  header(s, "04 · 드론 군집 로직", "군집 자율비행 — 중앙 제어 없는 편대", C.violet);
  s.addText("각 드론은 이웃의 위치·속도만 보고 스스로 움직인다. 여기에 국방 군집 운용 알고리즘을 얹는다.", {
    x:0.6, y:1.5, w:12, h:0.35, fontFace:F, fontSize:12.5, color:C.mute, margin:0});
  // 상: Boids 3규칙 (미니)
  const rules=[["분리 Separation","안전거리 내 이웃을 밀어내 충돌 방지",C.red2],
    ["정렬 Alignment","이웃 평균 속도에 방향을 맞춤",C.blue],
    ["결합 Cohesion","이웃 무게중심으로 모임",C.green]];
  let x=0.6; const cw=3.9, gap=0.2, cy=2.0, ch=1.75;
  rules.forEach(([t,d,col])=>{ card(s,x,cy,cw,ch,C.card,C.border);
    s.addText(t,{x:x+0.25,y:cy+0.22,w:cw-0.5,h:0.5,fontFace:F,fontSize:14.5,color:col,bold:true,margin:0});
    s.addText(d,{x:x+0.25,y:cy+0.78,w:cw-0.5,h:0.8,fontFace:F,fontSize:12,color:C.mute,margin:0,lineSpacingMultiple:1.15,valign:"top"}); x+=cw+gap; });
  // 하: 국방 군집 알고리즘 3
  s.addText("＋ 국방 군집 운용 알고리즘", {x:0.6, y:3.95, w:8, h:0.4, fontFace:F, fontSize:14, color:C.violet, bold:true, margin:0});
  const algo=[["충돌 방지","다수 무인체 근접 비행 시 상호 회피"],
    ["경로 분산","편대가 겹치지 않게 임무 공간을 나눔"],
    ["자율 임무 배정","화점·요구조자별로 담당을 스스로 할당"]];
  x=0.6; const cy2=4.45, ch2=1.85;
  algo.forEach(([t,d])=>{ card(s,x,cy2,cw,ch2,C.card2,C.violetDk);
    s.addText(t,{x:x+0.25,y:cy2+0.25,w:cw-0.5,h:0.5,fontFace:F,fontSize:15,color:C.violet,bold:true,margin:0});
    s.addText(d,{x:x+0.25,y:cy2+0.82,w:cw-0.5,h:0.9,fontFace:F,fontSize:12,color:C.mute,margin:0,lineSpacingMultiple:1.2,valign:"top"}); x+=cw+gap; });
  s.addNotes("Boids 3규칙이 기본 안전, 그 위에 국방 군집 알고리즘 3종으로 편대 임무를 자율 수행한다.");
}

/* ═════════ ⑫ 5개 편대 편성 ═════════ */
{
  const s = p.addSlide(); bg(s);
  header(s, "04 · 드론 군집 로직", "유무인 복합 편대 편성 · SOP-D", C.violet);
  const squads=[
    ["GCS","지휘통제","공중지휘권 선언 · 3D 매핑 융합 · 통합 제어·자원 관리",SQ.GCS],
    ["1편대","공중정찰대","사방 3D 스캐닝 · 열화상 화점 탐지 · 연소확대선 모니터링",SQ.RECON],
    ["2편대","인명수색·구조","고립 구조대상자 식별 · 생명유지 키트 투하 · 대피 인도",SQ.SAR],
    ["3편대","화재진압대","창문·진입점 파악 · 창문 파쇄 후 정밀 소화탄 투하",SQ.SUP],
    ["4편대","통신중계·조명","Mesh 통신망 형성 · 음영지역 신호 중계 · 광역 조명",SQ.COMMS],
  ];
  let y=1.75; const rh=0.95, rw=12.1;
  squads.forEach(([code,name,task,col])=>{
    card(s, 0.6, y, rw, rh, C.card, C.border);
    s.addShape(RR,{x:0.8,y:y+0.19,w:1.3,h:0.57,rectRadius:0.08,fill:{color:C.bgDark},line:{color:col,width:1.5}});
    s.addText(code,{x:0.8,y:y+0.19,w:1.3,h:0.57,align:"center",valign:"middle",fontFace:FM,fontSize:15,color:col,bold:true,margin:0});
    s.addText(name,{x:2.3,y:y,w:3.0,h:rh,valign:"middle",fontFace:F,fontSize:16,color:C.text,bold:true,margin:0});
    s.addText(task,{x:5.4,y:y,w:7.0,h:rh,valign:"middle",fontFace:F,fontSize:12.5,color:C.mute,margin:0,lineSpacingMultiple:1.1});
    y += rh+0.13;
  });
  s.addNotes("한 대 여러 대가 아니라, 임무별 5개 편대가 동시에 역할을 나눠 수행한다. 이게 1인1기 한계를 넘는 핵심.");
}

/* ═════════ ⑬ SOP-D 5단계 ═════════ */
{
  const s = p.addSlide(); bg(s);
  header(s, "04 · 드론 군집 로직", "SOP-D 표준 행동요령 · 5단계", C.violet);
  const phases=[
    ["전개","DEPLOY","정찰 편대 출격·상승, 진압·구조 편대 전개","101-D",C.indigo],
    ["정찰·평가","ASSESS","사방 3D 스캐닝 · 열화상 화점 탐지 · 진입점 파악","102-D",C.blue2],
    ["작전","OPERATE","창문 파쇄 후 정밀 소화탄 투하 · 대피 인도","222-D",C.orange],
    ["중계·호위","RELAY","요구조자 호위 · 외벽 연소차단 · 배터리 릴레이","105-D",C.red],
    ["종결","CLEAR","대피 완료 확인 · 잔불 감시 · 임무 이양 후 RTH","113-D",C.green],
  ];
  const n=5, gap=0.25, cw=(12.1-gap*(n-1))/n, cy=2.0, ch=3.9;
  let x=0.6;
  phases.forEach(([ko,en,d,code,col],i)=>{
    card(s,x,cy,cw,ch,C.card,C.border);
    s.addShape(OVAL,{x:x+cw/2-0.4,y:cy+0.3,w:0.8,h:0.8,fill:{color:C.bgDark},line:{color:col,width:2}});
    s.addText(String(i+1),{x:x+cw/2-0.4,y:cy+0.3,w:0.8,h:0.8,align:"center",valign:"middle",fontFace:FM,fontSize:24,color:col,bold:true,margin:0});
    s.addText(ko,{x:x+0.05,y:cy+1.25,w:cw-0.1,h:0.4,align:"center",fontFace:F,fontSize:14.5,color:col,bold:true,margin:0});
    s.addText(en,{x:x+0.05,y:cy+1.68,w:cw-0.1,h:0.3,align:"center",fontFace:FM,fontSize:9.5,color:C.dim,bold:true,charSpacing:1,margin:0});
    s.addText(d,{x:x+0.12,y:cy+2.05,w:cw-0.24,h:1.35,align:"center",fontFace:F,fontSize:10.5,color:C.mute,margin:0,lineSpacingMultiple:1.15,valign:"top"});
    s.addText(code,{x:x+0.05,y:cy+ch-0.42,w:cw-0.1,h:0.3,align:"center",fontFace:FM,fontSize:10,color:col,bold:true,margin:0});
    if(i<n-1) s.addText("›",{x:x+cw-0.02,y:cy,w:gap+0.04,h:ch,align:"center",valign:"middle",fontFace:F,fontSize:22,color:C.dim,bold:true,margin:0});
    x+=cw+gap;
  });
  s.addText("각 편대가 단계별 표준 행동요령(SOP 코드)에 따라 자율 수행 — 지휘·정찰·진압·구조·통신이 한 타임라인에서 맞물린다.", {
    x:0.6, y:6.3, w:12.1, h:0.4, align:"center", fontFace:F, fontSize:12, color:C.dim, italic:true, margin:0});
}

/* ═════════ ⑭ 3D 건물 시연 ═════════ */
{
  const s = p.addSlide(); bg(s);
  header(s, "04 · 드론 군집 로직", "3D 건물 시뮬레이션 · 2층 주택 화재", C.violet);
  // 좌: 건물 정면도
  const px=0.7, py=1.85, pw=5.6, ph=4.5;
  s.addShape(RR,{x:px,y:py,w:pw,h:ph,rectRadius:0.06,fill:{color:C.panel},line:{color:C.border,width:1}});
  // 지면
  s.addShape(RECT,{x:px+0.2,y:py+ph-0.7,w:pw-0.4,h:0.06,fill:{color:C.border},line:{type:"none"}});
  // 집 몸체
  const hx=px+1.55, hw=2.5, hFloor=1.35, hy=py+ph-0.7-2*hFloor;
  s.addShape(RECT,{x:hx,y:hy,w:hw,h:2*hFloor,fill:{color:C.fuel},line:{color:C.border,width:1.5}});
  // 지붕
  s.addShape(TRI,{x:hx-0.25,y:hy-0.85,w:hw+0.5,h:0.85,fill:{color:"475569"},line:{type:"none"}});
  // 층 구분선
  s.addShape(LINE,{x:hx,y:hy+hFloor,w:hw,h:0,line:{color:C.border,width:1}});
  // 창문 — 1층 정상 2개
  const win=(wx,wy,col)=>s.addShape(RECT,{x:wx,y:wy,w:0.5,h:0.5,fill:{color:col},line:{color:C.border2,width:1}});
  win(hx+0.35,hy+hFloor+0.45,C.blueDk); win(hx+1.65,hy+hFloor+0.45,C.blueDk);
  // 문
  s.addShape(RECT,{x:hx+1.0,y:hy+2*hFloor-0.75,w:0.5,h:0.75,fill:{color:"1E293B"},line:{color:C.border2,width:1}});
  // 2층 좌: 요구조자, 2층 우: 화점
  s.addShape(OVAL,{x:hx+0.42,y:hy+0.4,w:0.4,h:0.4,fill:{color:"22D3EE"},line:{color:"CFFAFE",width:1}});
  s.addShape(RECT,{x:hx+1.6,y:hy+0.35,w:0.55,h:0.55,fill:{color:C.orange},line:{color:C.yellow,width:1.5}});
  // 드론들 (편대색)
  dot(s, hx+hw+0.55, hy-1.1, 0.24, SQ.RECON, C.text);      // 정찰 상공
  dot(s, hx+2.25, hy+0.45, 0.24, SQ.SUP, C.text);           // 진압 화점 앞
  dot(s, hx+0.1, hy+0.5, 0.24, SQ.SAR, C.text);             // 구조 요구조자 앞
  dot(s, hx-0.7, hy-0.9, 0.24, SQ.COMMS, C.text);           // 통신·조명 고공
  // 대피 집결지
  s.addShape(OVAL,{x:px+0.55,y:py+ph-0.55,w:0.7,h:0.28,fill:{color:"16A34A"},line:{type:"none"}});
  s.addText("대피 집결지",{x:px+0.35,y:py+ph-0.3,w:1.5,h:0.25,align:"center",fontFace:F,fontSize:8.5,color:C.green2,margin:0});
  s.addText("드래그 회전 · 휠 확대/축소 (Three.js)",{x:px,y:py+ph+0.06,w:pw,h:0.28,align:"center",fontFace:F,fontSize:10,color:C.dim,margin:0});
  // 우: 편대 액션 + 요소 범례
  const acts=[
    ["1편대 공중정찰","2층 우측 방 화점을 열화상으로 탐지",SQ.RECON],
    ["3편대 화재진압","창문 파쇄 후 화점에 정밀 소화탄 투하",SQ.SUP],
    ["2편대 인명수색·구조","2층 좌측 요구조자 앞·위에서 대피 인도",SQ.SAR],
    ["4편대 통신중계·조명","고공에서 Mesh 통신 중계 · 광역 조명",SQ.COMMS],
  ];
  let y=1.9;
  acts.forEach(([t,d,col])=>{
    card(s,6.5,y,6.2,1.02,C.card,C.border);
    dot(s,6.75,y+0.36,0.3,col);
    s.addText(t,{x:7.2,y:y+0.14,w:5.3,h:0.35,fontFace:F,fontSize:13.5,color:col,bold:true,margin:0});
    s.addText(d,{x:7.2,y:y+0.5,w:5.35,h:0.45,fontFace:F,fontSize:11,color:C.mute,margin:0});
    y+=1.12;
  });
  s.addNotes("실제 2층 단독주택 3D. 정찰이 화점 탐지 → 진압이 창문 파쇄·소화탄 → 구조가 요구조자 대피 인도 → 통신·조명 지원.");
}

/* ═════════ ⑮ 유무인 복합 · UGV 협업 ═════════ */
{
  const s = p.addSlide(); bg(s);
  header(s, "04 · 드론 군집 로직", "유무인 복합 — 지상 무인차량(UGV) 협업", C.violet);
  // 좌: 도식 (골목 진입 UGV + 상공 드론)
  const px=0.7, py=1.85, pw=5.5, ph=4.5;
  s.addShape(RR,{x:px,y:py,w:pw,h:ph,rectRadius:0.06,fill:{color:C.panel},line:{color:C.border,width:1}});
  // 건물 블록 + 좁은 골목
  s.addShape(RECT,{x:px+0.4,y:py+1.3,w:1.7,h:2.4,fill:{color:C.fuel},line:{color:C.border2,width:1}});
  s.addShape(RECT,{x:px+3.4,y:py+1.3,w:1.7,h:2.4,fill:{color:C.fuel},line:{color:C.border2,width:1}});
  s.addShape(RECT,{x:px+2.1,y:py+1.3,w:1.3,h:2.4,fill:{color:C.redDk},line:{type:"none"}}); // 좁은 골목
  s.addText("진입불가 골목",{x:px+2.0,y:py+3.72,w:1.5,h:0.25,align:"center",fontFace:F,fontSize:9,color:C.redSoft,margin:0});
  // 화점 (골목 안쪽 건물)
  s.addShape(RECT,{x:px+4.1,y:py+1.6,w:0.5,h:0.5,fill:{color:C.orange},line:{color:C.yellow,width:1.5}});
  // UGV (골목 입구)
  const ux=px+2.35, uy=py+2.95;
  s.addShape(RR,{x:ux,y:uy,w:0.8,h:0.42,rectRadius:0.05,fill:{color:C.mint},line:{color:"065F46",width:1}});
  dot(s, ux+0.08, uy+0.34, 0.2, "0B1220", C.text); dot(s, ux+0.52, uy+0.34, 0.2, "0B1220", C.text);
  s.addText("UGV",{x:ux-0.15,y:uy-0.02,w:1.1,h:0.34,align:"center",valign:"middle",fontFace:FM,fontSize:9,color:"065F46",bold:true,margin:0});
  // 상공 드론 편대
  dot(s, px+2.4, py+0.55, 0.22, SQ.RECON, C.text);
  dot(s, px+3.0, py+0.4, 0.22, SQ.SUP, C.text);
  dot(s, px+3.6, py+0.62, 0.22, SQ.SAR, C.text);
  s.addText("상공: 드론 편대 정밀 진압·정찰",{x:px+0.2,y:py+0.05,w:pw-0.4,h:0.3,align:"center",fontFace:F,fontSize:10,color:C.violet,bold:true,margin:0});
  s.addText("지상: UGV 진입·보급",{x:ux-1.0,y:uy+0.5,w:2.8,h:0.3,align:"center",fontFace:F,fontSize:10,color:C.mint,bold:true,margin:0});
  // 우: 3 역할 카드
  const roles=[
    ["지상 무인차량(UGV)","장애물 극복 · 소화수 보급 · 스마트 방재 거점에서 출발",C.mint],
    ["드론 편대","상공에서 정밀 정찰·진압 — 골목 위를 그대로 넘는다",C.violet],
    ["유무인 복합 협업","UGV가 지상 보급·거점, 드론이 공중 타격 — 상호 통신으로 한 편대처럼",C.orange],
  ];
  let y=1.95;
  roles.forEach(([t,d,col])=>{
    card(s,6.5,y,6.2,1.32,C.card,col);
    s.addText(t,{x:6.78,y:y+0.2,w:5.7,h:0.4,fontFace:F,fontSize:15.5,color:col,bold:true,margin:0});
    s.addText(d,{x:6.78,y:y+0.66,w:5.75,h:0.6,fontFace:F,fontSize:12,color:C.mute,margin:0,lineSpacingMultiple:1.15,valign:"top"});
    y+=1.45;
  });
  s.addNotes("드론만이 아니라 지상 UGV와 협업. UGV는 소화수 보급·거점, 드론은 공중 정밀 진압. 유무인 복합 편대.");
}

/* ═════════ ⑯ 핵심 성과 ═════════ */
{
  const s = p.addSlide(); bg(s);
  header(s, "05 · 기대효과", "핵심 성과 — 골든타임을 되찾는다", C.green);
  card(s, 0.6, 1.9, 4.35, 4.45, C.card2, "166534");
  s.addText("초동 진압 시점", {x:0.6, y:2.2, w:4.35, h:0.4, align:"center", fontFace:F, fontSize:15, color:C.green2, bold:true, margin:0});
  s.addText("10분+", {x:0.6, y:2.7, w:4.35, h:1.4, align:"center", fontFace:FM, fontSize:74, color:C.green, bold:true, margin:0});
  s.addText("단축", {x:0.6, y:4.2, w:4.35, h:0.5, align:"center", fontFace:F, fontSize:22, color:C.green2, bold:true, margin:0});
  s.addText("소방차 진입 불가 지역 기준", {x:0.6, y:4.8, w:4.35, h:0.4, align:"center", fontFace:F, fontSize:12.5, color:C.mute, margin:0});
  s.addText("소방관 직접 투입 전 정밀 정찰을 선행해 인명 피해 발생률을 크게 낮춘다.", {
    x:0.85, y:5.35, w:3.85, h:0.9, align:"center", fontFace:F, fontSize:12, color:C.text, margin:0, lineSpacingMultiple:1.25, valign:"top"});
  const stats=[
    ["편대 동시 운용","5개 편대",C.violet],
    ["지휘·정찰·진압·구조·통신","동시 수행",C.blue],
    ["드론 도착","소방차보다 먼저",C.orange],
    ["소방관 안전","투입 전 정찰",C.green],
  ];
  stats.forEach(([t,v,col],i)=>{
    const cx=5.2+(i%2)*3.85, cyy=1.9+Math.floor(i/2)*1.2;
    card(s,cx,cyy,3.6,1.05,C.card,C.border);
    s.addText(v,{x:cx+0.25,y:cyy+0.12,w:3.1,h:0.55,fontFace:F,fontSize:22,color:col,bold:true,margin:0});
    s.addText(t,{x:cx+0.25,y:cyy+0.68,w:3.15,h:0.3,fontFace:F,fontSize:11,color:C.mute,margin:0});
  });
  card(s, 5.2, 4.35, 7.5, 2.0, "1F1206", C.orange);
  s.addText("차별성", {x:5.45, y:4.55, w:3, h:0.4, fontFace:F, fontSize:14, color:C.orange, bold:true, margin:0});
  const diffs=["국방 군집 무인체계 알고리즘의 민간 스핀오프","드론 편대 + 지상 UGV 유무인 복합 협업","실주소·실도로 빅데이터 기반 검증"];
  let dy=5.0;
  diffs.forEach(d=>{ dot(s,5.5,dy+0.08,0.14,C.orange2);
    s.addText(d,{x:5.78,y:dy-0.05,w:6.7,h:0.4,fontFace:F,fontSize:12.5,color:C.text,margin:0}); dy+=0.45; });
  s.addText("※ 골든타임 단축 등 효과는 계획서 목표치 — 실증으로 검증 예정.", {x:0.6, y:6.55, w:12, h:0.3, fontFace:F, fontSize:10, color:C.dim, italic:true, margin:0});
}

/* ═════════ ⑰ 기대효과 3측면 · 마무리 ═════════ */
{
  const s = p.addSlide(); bg(s, C.bgDark);
  header(s, "05 · 기대효과", "기대효과 — 기술 · 사회 · 지역", C.green);
  const eff=[
    ["기술·학문","방산-민간 스핀오프 선도","기계공학 제어·역학 + 국방과학 자율 군집 운용의 고가치 융합 사례",C.violet],
    ["사회·안전","원도심 골든타임 단축","초동 진압 최대 10분+ 단축 · 소방관 투입 전 정밀 정찰로 인명 보호",C.orange],
    ["지역 혁신","경남형 스마트시티·방산","방위산업·항공우주 인프라를 스마트시티에 결합한 지역 특화 혁신",C.blue],
  ];
  let x=0.6; const cw=3.97, gap=0.2, cy=1.9, ch=3.0;
  eff.forEach(([tag,t,d,col])=>{
    card(s,x,cy,cw,ch,C.card,C.border);
    chip(s,x+0.28,cy+0.3,1.6,tag,col);
    s.addText(t,{x:x+0.28,y:cy+0.95,w:cw-0.56,h:0.85,fontFace:F,fontSize:16,color:C.text,bold:true,margin:0,valign:"top",lineSpacingMultiple:1.05});
    s.addText(d,{x:x+0.28,y:cy+1.85,w:cw-0.56,h:1.0,fontFace:F,fontSize:12,color:C.mute,margin:0,lineSpacingMultiple:1.25,valign:"top"});
    x+=cw+gap;
  });
  card(s, 0.6, 5.2, 12.1, 1.55, C.card2, C.orange);
  s.addText("소방차가 못 가는 골목을, 유무인 복합 편대가 먼저 지킨다", {x:0.9, y:5.42, w:11.5, h:0.5, fontFace:F, fontSize:19, color:C.orange, bold:true, margin:0});
  s.addText("국방 군집 알고리즘 · 실주소 화재확산 시뮬레이션 · 드론-UGV SOP-D를 하나로 — 팀 군체. 감사합니다. (Q&A)", {
    x:0.9, y:6.02, w:11.5, h:0.5, fontFace:F, fontSize:13.5, color:C.mute, margin:0});
}

const OUT = process.argv[2] || "deck2.pptx";
p.writeFile({ fileName: OUT }).then(f => console.log("saved", f));
