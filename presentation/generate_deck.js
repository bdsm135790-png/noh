const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE";                 // 13.33 x 7.5
p.author = "군집 소방 드론 팀";
p.title = "골목을 건너는 불, 골목을 건너는 드론";

const RR = p.ShapeType.roundRect, RECT = p.ShapeType.rect, OVAL = p.ShapeType.ellipse;
const F = "Malgun Gothic";                // 본문 (한글)
const FM = "Consolas";                    // 수치

/* ── 팔레트 (시뮬레이션 UI 그대로) ── */
const C = {
  bg:"0F172A", bgDark:"0B1220", panel:"0B1220",
  card:"1E293B", card2:"172033", border:"334155", border2:"1E293B",
  text:"E2E8F0", mute:"94A3B8", dim:"64748B",
  orange:"F97316", orange2:"FB923C",
  blue:"38BDF8", blue2:"0EA5E9", blueDk:"1E3A5F",
  red:"DC2626", red2:"F87171", redSoft:"FCA5A5", redDk:"3F1D1D", redBg:"2A1215",
  green:"4ADE80", green2:"86EFAC", mint:"34D399",
  yellow:"FBBF24", amber:"F59E0B",
  fuel:"334155", burnt:"1C1917", wet:"0C4A6E",
};

const NEG = "010A18"; // 아주 어두운 배경
const bg = (s, c=C.bg) => { s.background = { color:c }; };

/* ── 공통 헤더 ── */
function header(s, kicker, title, kColor=C.orange){
  s.addText(kicker.toUpperCase(), {x:0.6, y:0.44, w:12, h:0.3, fontFace:F,
    fontSize:12.5, color:kColor, bold:true, charSpacing:3, margin:0});
  s.addText(title, {x:0.6, y:0.74, w:12.1, h:0.72, fontFace:F,
    fontSize:29, color:C.text, bold:true, margin:0});
}
function card(s, x, y, w, h, fill=C.card, border=C.border, radius=0.09){
  s.addShape(RR, {x,y,w,h, rectRadius:radius, fill:{color:fill},
    line:{color:border, width:1}});
}
function dot(s, x, y, d, color, ring){
  s.addShape(OVAL, {x, y, w:d, h:d, fill:{color},
    line: ring ? {color:ring, width:1} : {type:"none"}});
}
function chip(s, x, y, w, text, color){
  s.addShape(RR, {x, y, w, h:0.34, rectRadius:0.17,
    fill:{color:C.bgDark}, line:{color, width:1}});
  s.addText(text, {x, y, w, h:0.34, align:"center", valign:"middle",
    fontFace:F, fontSize:10.5, color, bold:true, margin:0});
}

/* ── 화재 격자 모티프 (시뮬레이션 캔버스 재현) ── */
const OR = 5.4, OC = 5.2;                 // 발화 격자 좌표
function burnCol(d, a, b){
  const f = (d - a) / (b - a);
  return f > 0.62 ? C.yellow : f > 0.32 ? C.orange : C.red;
}
function cellColor(r, c, stage){
  if (r === 8) return C.blueDk;           // 진입가능 도로(가로)
  if (c === 3) return C.blueDk;           // 진입가능 도로(세로)
  if (c === 7) return C.redDk;            // 협소 골목(진입불가)
  const d = Math.hypot(r - OR, c - OC);
  const front = ((r - OR) * 0.7 + (OC - c) * 0.7); // 풍하(남서) 방향
  const jump = (c >= 8 && c <= 10 && r >= 3 && r <= 6);
  const jd = Math.hypot(r - 4.5, c - 9);
  if (stage === 0){
    if (d <= 1.25) return C.red;
    if (d <= 1.9) return C.orange;
    return C.fuel;
  }
  if (stage === 1){
    if (d <= 1.7) return C.burnt;
    if (d <= 3.9) return burnCol(d, 1.7, 3.9);
    if (jump && jd <= 1.4) return burnCol(jd, 0, 1.4);
    return C.fuel;
  }
  if (stage === 2){
    if (d <= 2.1) return C.burnt;
    if (d <= 3.7) return burnCol(d, 2.1, 3.7);
    if (d > 3.7 && d <= 4.9 && front > 0.2) return C.wet;
    if (jump && jd <= 1.1) return C.wet;
    return C.fuel;
  }
  // stage 3 (완전 진화)
  if (d <= 4.7) return ((r * 2 + c) % 3 === 0) ? C.wet : C.burnt;
  if (jump && jd <= 1.4) return C.wet;
  return C.fuel;
}
function fireGrid(s, gx, gy, cell, stage, opts={}){
  const N = 12;
  s.addShape(RR, {x:gx-0.08, y:gy-0.08, w:N*cell+0.16, h:N*cell+0.16,
    rectRadius:0.06, fill:{color:C.panel}, line:{color:C.border, width:1}});
  for (let r=0; r<N; r++) for (let c=0; c<N; c++){
    s.addShape(RECT, {x:gx+c*cell, y:gy+r*cell, w:cell, h:cell,
      fill:{color:cellColor(r,c,stage)}, line:{type:"none"}});
  }
  // 발화점
  dot(s, gx+OC*cell, gy+OR*cell, cell*0.9, C.yellow, "78350F");
  // 드론
  (opts.drones||[]).forEach(([dr,dc]) =>
    dot(s, gx+dc*cell, gy+dr*cell, cell*0.72, C.orange, "FED7AA"));
  if (opts.label)
    s.addText(opts.label, {x:gx-0.08, y:gy+N*cell+0.02, w:N*cell+0.16, h:0.3,
      align:"center", fontFace:F, fontSize:11, color:opts.labelColor||C.mute,
      bold:true, margin:0});
}

/* ══════════════════════════════════════════════════════════
   ① 표지
   ══════════════════════════════════════════════════════════ */
{
  const s = p.addSlide(); bg(s, C.bgDark);
  // 우측 배경 격자 모티프
  fireGrid(s, 8.55, 1.7, 0.32, 2, {drones:[[3,5],[4,9],[8,4],[2,7]]});
  s.addText("제6회 빅데이터로 우리동네 문제해결 아이디어 공모대회 · 창원시", {
    x:0.75, y:0.7, w:7.4, h:0.35, fontFace:F, fontSize:13, color:C.blue, bold:true, margin:0});
  s.addText([
    {text:"골목을 건너는 불,\n", options:{color:C.orange}},
    {text:"골목을 건너는 드론", options:{color:C.text}},
  ], {x:0.72, y:1.6, w:7.6, h:2.1, fontFace:F, fontSize:44, bold:true, lineSpacingMultiple:1.05, margin:0});
  s.addText("군집 소방 드론 × 실주소 도면 기반 화재확산 시뮬레이션", {
    x:0.75, y:3.85, w:7.5, h:0.5, fontFace:F, fontSize:18, color:C.mute, margin:0});
  // 태그라인 카드
  card(s, 0.75, 4.7, 7.35, 0.9, C.card, C.border);
  s.addText("소방차가 못 들어가는 폭 4m 미만 골목 — 그 상공을 드론이 대신 지킨다.", {
    x:1.0, y:4.7, w:6.9, h:0.9, valign:"middle", fontFace:F, fontSize:14.5,
    color:C.text, margin:0});
  s.addText("발표자 ______     ·     팀명 ______     ·     2026", {
    x:0.75, y:6.55, w:8, h:0.4, fontFace:F, fontSize:12.5, color:C.dim, margin:0});
}

/* ══════════════════════════════════════════════════════════
   ② 배경 — 구도심의 좁은 골목
   ══════════════════════════════════════════════════════════ */
{
  const s = p.addSlide(); bg(s);
  header(s, "02 · 기획 배경", "창원 구도심 · 전통시장의 좁은 골목");
  // 좌: 설명
  const rows = [
    ["구도심·전통시장 밀집", "마산어시장·부림시장·진해 중앙동 등 노후 시가지는 폭이 좁은 이면도로와 골목으로 얽혀 있다."],
    ["목조·경량 밀집 시가지", "건물이 붙어 있고 가연물이 많아, 한 곳의 발화가 곧 이웃 건물로 옮겨붙는다."],
    ["좁을수록 위험이 겹친다", "소방차는 못 들어오고, 불은 오히려 더 잘 번진다 — 위험이 한 곳에 몰린다."],
  ];
  let y = 1.75;
  rows.forEach(([t, d], i) => {
    card(s, 0.6, y, 6.35, 1.5, C.card, C.border);
    dot(s, 0.9, y+0.32, 0.5, C.bgDark, C.orange);
    s.addText(String(i+1), {x:0.9, y:y+0.32, w:0.5, h:0.5, align:"center",
      valign:"middle", fontFace:FM, fontSize:17, color:C.orange, bold:true, margin:0});
    s.addText(t, {x:1.6, y:y+0.2, w:5.15, h:0.4, fontFace:F, fontSize:16,
      color:C.text, bold:true, margin:0});
    s.addText(d, {x:1.6, y:y+0.62, w:5.2, h:0.75, fontFace:F, fontSize:12.5,
      color:C.mute, margin:0, lineSpacingMultiple:1.05});
    y += 1.65;
  });
  // 우: 골목 도식 (건물 사이 좁은 붉은 골목)
  const px = 7.35, py = 1.75, pw = 5.35, ph = 4.95;
  s.addShape(RR, {x:px, y:py, w:pw, h:ph, rectRadius:0.08, fill:{color:C.panel},
    line:{color:C.border, width:1}});
  // 건물 블록
  const blk = (bx, by, bw, bh) => s.addShape(RECT, {x:bx, y:by, w:bw, h:bh,
    fill:{color:C.fuel}, line:{color:C.border2, width:1}});
  const gcols = [px+0.35, px+2.05, px+3.75];
  const roadX = [px+1.75, px+3.45];       // 좁은 골목 위치
  for (let r=0; r<4; r++){
    const by = py+0.4 + r*1.12;
    gcols.forEach(cx => blk(cx, by, 1.35, 0.9));
  }
  // 좁은 골목(붉은) — 세로
  roadX.forEach(rx => s.addShape(RECT, {x:rx, y:py+0.35, w:0.28, h:ph-0.65,
    fill:{color:C.redDk}, line:{type:"none"}}));
  // 넓은 도로(파랑) — 하단 가로
  s.addShape(RECT, {x:px+0.2, y:py+ph-0.55, w:pw-0.4, h:0.34,
    fill:{color:C.blueDk}, line:{type:"none"}});
  s.addText("폭 3.0m", {x:roadX[0]-0.55, y:py+0.05, w:1.4, h:0.28, align:"center",
    fontFace:FM, fontSize:10.5, color:C.redSoft, bold:true, margin:0});
  s.addText("소방차 진입 가능 도로", {x:px+0.2, y:py+ph-0.55, w:pw-0.4, h:0.34,
    valign:"middle", align:"center", fontFace:F, fontSize:10.5, color:C.blue, bold:true, margin:0});
  s.addText("건물이 붙어 있고 골목이 좁다", {x:px, y:py+ph+0.08, w:pw, h:0.3,
    align:"center", fontFace:F, fontSize:11, color:C.dim, margin:0});
}

/* ══════════════════════════════════════════════════════════
   ③ 문제 정의
   ══════════════════════════════════════════════════════════ */
{
  const s = p.addSlide(); bg(s);
  header(s, "02 · 문제 정의", "가장 위험한 곳에, 가장 늦게 도착한다");
  // 큰 스탯 2개
  card(s, 0.6, 1.85, 3.75, 2.35, C.redBg, "7F1D1D");
  s.addText("4m", {x:0.6, y:2.0, w:3.75, h:1.1, align:"center", fontFace:FM,
    fontSize:66, color:C.red2, bold:true, margin:0});
  s.addText("미만 도로 = 소방차 진입 불가", {x:0.6, y:3.15, w:3.75, h:0.45,
    align:"center", fontFace:F, fontSize:14, color:C.redSoft, bold:true, margin:0});
  s.addText("소방차 최소 통행폭 기준", {x:0.6, y:3.6, w:3.75, h:0.4, align:"center",
    fontFace:F, fontSize:11, color:C.mute, margin:0});

  card(s, 4.55, 1.85, 3.75, 2.35, C.card, C.border);
  s.addText("복사열", {x:4.55, y:2.0, w:3.75, h:1.1, align:"center", fontFace:F,
    fontSize:50, color:C.orange, bold:true, margin:0});
  s.addText("불은 좁은 골목을 건너뛴다", {x:4.55, y:3.15, w:3.75, h:0.45, align:"center",
    fontFace:F, fontSize:14, color:C.text, bold:true, margin:0});
  s.addText("3~6m 간극은 자연 방화선이 못 된다", {x:4.55, y:3.6, w:3.75, h:0.4,
    align:"center", fontFace:F, fontSize:11, color:C.mute, margin:0});

  // 하단 결론 배너
  card(s, 0.6, 4.5, 7.7, 1.85, C.card2, C.border);
  s.addText("두 위험이 같은 곳에서 겹친다", {x:0.9, y:4.72, w:7.2, h:0.45,
    fontFace:F, fontSize:17, color:C.orange, bold:true, margin:0});
  s.addText([
    {text:"좁은 골목일수록 ", options:{color:C.mute}},
    {text:"소방차는 못 들어오고", options:{color:C.redSoft, bold:true}},
    {text:", 동시에 ", options:{color:C.mute}},
    {text:"불은 더 잘 번진다", options:{color:C.orange2, bold:true}},
    {text:".\n초동 골든타임을 확보할 ", options:{color:C.mute}},
    {text:"상공 대응 수단", options:{color:C.text, bold:true}},
    {text:"이 필요하다.", options:{color:C.mute}},
  ], {x:0.9, y:5.25, w:7.3, h:1.0, fontFace:F, fontSize:14, lineSpacingMultiple:1.15, margin:0});

  // 우측: 화재 확산 격자
  fireGrid(s, 9.05, 2.0, 0.33, 1, {label:"발화 → 골목 건너 확산", labelColor:C.mute});
}

/* ══════════════════════════════════════════════════════════
   ④ 현장 데이터 — 진입불가 10곳
   ══════════════════════════════════════════════════════════ */
{
  const s = p.addSlide(); bg(s);
  header(s, "02 · 현장 데이터", "팀이 직접 확인한 소방차 진입불가 구간");
  // 좌: 큰 숫자 + 지도 도식
  card(s, 0.6, 1.8, 5.15, 4.55, C.panel, C.border);
  s.addText("10", {x:0.75, y:1.95, w:2.0, h:1.05, fontFace:FM, fontSize:60,
    color:C.red2, bold:true, margin:0});
  s.addText("개 구간", {x:2.55, y:2.55, w:1.8, h:0.5, fontFace:F, fontSize:18,
    color:C.redSoft, bold:true, margin:0});
  s.addText("창원시 전역 현장조사", {x:0.78, y:3.0, w:4.5, h:0.35, fontFace:F,
    fontSize:12, color:C.mute, margin:0});
  // 간이 지도: 붉은 진입불가 선분들
  const mx = 0.95, my = 3.55, mw = 4.45, mh = 2.6;
  s.addShape(RR, {x:mx, y:my, w:mw, h:mh, rectRadius:0.06, fill:{color:C.bgDark},
    line:{color:C.border2, width:1}});
  const segs = [[0.4,0.5,1.3,0.9],[1.9,0.4,2.7,1.0],[3.3,0.7,4.0,0.5],
    [0.6,1.6,1.5,2.1],[2.1,1.5,2.9,2.0],[3.4,1.7,4.05,2.15],
    [1.0,2.25,1.8,2.4],[2.6,2.25,3.4,2.35]];
  segs.forEach(([x1,y1,x2,y2]) => s.addShape(p.ShapeType.line,
    {x:mx+x1, y:my+y1, w:x2-x1, h:y2-y1, line:{color:C.red, width:2.5}}));
  s.addText("● 붉은 선 = 진입불가 구간", {x:mx, y:my+mh-0.02, w:mw, h:0.3,
    align:"center", fontFace:F, fontSize:10, color:C.dim, margin:0});
  // 우: 대표 구간 리스트
  const zones = [
    "마산어시장 · 오동동 전통시장", "진해 중앙동 구도심 골목",
    "자산·완월동 고지대 골목길", "명서동 주거밀집 이면도로",
    "상남동 상업지구 이면도로", "봉곡동 상가·주택 이면도로",
    "합성동 상가주택 골목", "구암동 노후주택가 골목",
  ];
  card(s, 6.0, 1.8, 6.7, 4.55, C.card, C.border);
  s.addText("대표 진입불가 구간", {x:6.3, y:2.0, w:6.1, h:0.4, fontFace:F,
    fontSize:15, color:C.orange, bold:true, margin:0});
  let zy = 2.55;
  zones.forEach((z, i) => {
    const cx = 6.3 + (i % 2) * 3.15, cy = zy + Math.floor(i/2) * 0.92;
    dot(s, cx, cy+0.05, 0.16, C.red2);
    s.addText(z, {x:cx+0.28, y:cy-0.06, w:2.85, h:0.6, valign:"middle",
      fontFace:F, fontSize:12, color:C.text, margin:0});
  });
  s.addText("+ 웅남·신촌 공단로, 진해 이동·자은동 주거지 외", {x:6.3, y:6.05, w:6.1, h:0.3,
    fontFace:F, fontSize:11, color:C.dim, italic:true, margin:0});
}

/* ══════════════════════════════════════════════════════════
   ⑤ 데이터 파이프라인
   ══════════════════════════════════════════════════════════ */
{
  const s = p.addSlide(); bg(s);
  header(s, "03 · 기술 스택", "실주소를 실제 도로 위 시뮬레이션으로");
  const steps = [
    ["01", "도로명주소·장소명", "부림시장, 창원시청 …", C.blue],
    ["02", "위경도 좌표", "Kakao Local API", C.blue],
    ["03", "실제 도로망", "OpenStreetMap 실측", C.orange],
    ["04", "가구 복원·격자화", "3m 격자 · 300×300m", C.orange],
    ["05", "화재확산 모델", "골목폭·복사열·바람 반영", C.red2],
  ];
  const n = steps.length, gap = 0.32;
  const totalW = 12.1, cw = (totalW - gap*(n-1)) / n;
  let x = 0.6;
  const cy = 2.2, ch = 2.5;
  steps.forEach(([num, t, d, col], i) => {
    card(s, x, cy, cw, ch, C.card, C.border);
    s.addShape(OVAL, {x:x+cw/2-0.35, y:cy+0.3, w:0.7, h:0.7, fill:{color:C.bgDark},
      line:{color:col, width:1.5}});
    s.addText(num, {x:x+cw/2-0.35, y:cy+0.3, w:0.7, h:0.7, align:"center",
      valign:"middle", fontFace:FM, fontSize:20, color:col, bold:true, margin:0});
    s.addText(t, {x:x+0.1, y:cy+1.15, w:cw-0.2, h:0.7, align:"center",
      fontFace:F, fontSize:13.5, color:C.text, bold:true, margin:0, valign:"top"});
    s.addText(d, {x:x+0.1, y:cy+1.82, w:cw-0.2, h:0.55, align:"center",
      fontFace:F, fontSize:10.5, color:C.mute, margin:0});
    if (i < n-1)
      s.addText("›", {x:x+cw-0.02, y:cy, w:gap+0.04, h:ch, align:"center",
        valign:"middle", fontFace:F, fontSize:26, color:C.dim, bold:true, margin:0});
    x += cw + gap;
  });
  // 하단 근거 배너
  card(s, 0.6, 5.15, 12.1, 1.2, C.card2, C.border);
  s.addText("가정이 아니라 실제 데이터", {x:0.9, y:5.32, w:5, h:0.4, fontFace:F,
    fontSize:14, color:C.green2, bold:true, margin:0});
  s.addText([
    {text:"도로 형상은 OSM 실측, 소방차 도착은 OSRM 실도로 라우팅, 진입불가 구간은 팀 현장조사. ", options:{color:C.mute}},
    {text:"어느 주소를 넣어도 그 지점의 실제 도로 위에서 시뮬레이션한다.", options:{color:C.text, bold:true}},
  ], {x:0.9, y:5.72, w:11.5, h:0.55, fontFace:F, fontSize:12.5, margin:0, lineSpacingMultiple:1.05});
}

/* ══════════════════════════════════════════════════════════
   ⑥ 기술 스택 구성
   ══════════════════════════════════════════════════════════ */
{
  const s = p.addSlide(); bg(s);
  header(s, "03 · 기술 스택", "구성 요소");
  const groups = [
    ["프론트엔드 · 시각화", C.blue, [
      ["Leaflet", "소방서 거점·경로·도면 범위 지도"],
      ["HTML5 Canvas", "격자 확산 시뮬레이션 렌더·확대/이동"],
    ]],
    ["외부 데이터 API", C.orange, [
      ["Kakao Local", "주소·장소명 → 위경도"],
      ["OpenStreetMap", "실측 도로망·건물 형상"],
      ["OSRM", "소방차 실도로 최속경로·소요시간"],
    ]],
    ["시뮬레이션 코어", C.red2, [
      ["화재확산 모델", "복사열 건너뜀·바람·밀집도"],
      ["군집 드론 로직 (Python)", "Boids 비행 · 역할 기반 진압"],
    ]],
  ];
  let x = 0.6; const cw = 3.9, gap = 0.2, cy = 1.85, ch = 4.5;
  groups.forEach(([title, col, items]) => {
    card(s, x, cy, cw, ch, C.card, C.border);
    dot(s, x+0.3, cy+0.32, 0.42, C.bgDark, col);
    s.addShape(OVAL, {x:x+0.4, y:cy+0.42, w:0.22, h:0.22, fill:{color:col}, line:{type:"none"}});
    s.addText(title, {x:x+0.85, y:cy+0.28, w:cw-1.0, h:0.5, valign:"middle",
      fontFace:F, fontSize:14.5, color:C.text, bold:true, margin:0});
    let iy = cy+1.1;
    items.forEach(([t, d]) => {
      s.addShape(RR, {x:x+0.28, y:iy, w:cw-0.56, h:0.94, rectRadius:0.06,
        fill:{color:C.bgDark}, line:{color:C.border2, width:1}});
      s.addText(t, {x:x+0.45, y:iy+0.12, w:cw-0.9, h:0.35, fontFace:F,
        fontSize:12.5, color:col, bold:true, margin:0});
      s.addText(d, {x:x+0.45, y:iy+0.47, w:cw-0.9, h:0.42, fontFace:F,
        fontSize:10.5, color:C.mute, margin:0, lineSpacingMultiple:1.0});
      iy += 1.08;
    });
    x += cw + gap;
  });
}

/* ══════════════════════════════════════════════════════════
   ⑦ 확산 모델 원리
   ══════════════════════════════════════════════════════════ */
{
  const s = p.addSlide(); bg(s);
  header(s, "04 · 화재 확산 시뮬레이션", "확산 모델은 이렇게 움직인다", C.orange);
  // 좌: 격자
  fireGrid(s, 0.9, 1.95, 0.33, 1, {});
  // 범례 (격자 아래 · 2행 3열, 좌측에 한정)
  const leg = [["건물(가연물)", C.fuel], ["진입가능 도로", C.blueDk],
    ["협소 골목", C.redDk], ["연소", C.orange], ["전소", C.burnt], ["드론 진압", C.wet]];
  leg.forEach(([t, col], i) => {
    const lx = 0.78 + (i % 3) * 1.75, ly = 6.2 + Math.floor(i/3) * 0.35;
    s.addShape(RECT, {x:lx, y:ly+0.03, w:0.18, h:0.18, fill:{color:col}, line:{type:"none"}});
    s.addText(t, {x:lx+0.24, y:ly-0.04, w:1.5, h:0.3, fontFace:F, fontSize:9.5,
      color:C.mute, margin:0});
  });
  // 우: 원리 3줄 + 변수
  const items = [
    ["실제 도로망을 골격으로", "도로 사이 가구(街區)를 건물 조직으로 복원해 3m 격자로 채운다."],
    ["골목 폭이 확산을 가른다", "넓은 도로는 자연 방화선, 좁은 골목은 복사열로 불을 그대로 건너보낸다."],
    ["소방차 진입 가능성 반영", "폭 4m 미만 구간과 팀 조사 진입불가 구간을 우선 데이터로 표시한다."],
  ];
  let y = 2.0;
  items.forEach(([t, d], i) => {
    card(s, 6.35, y, 6.35, 1.28, C.card, C.border);
    s.addText(t, {x:6.6, y:y+0.16, w:5.9, h:0.4, fontFace:F, fontSize:15,
      color:C.orange, bold:true, margin:0});
    s.addText(d, {x:6.6, y:y+0.58, w:5.95, h:0.62, fontFace:F, fontSize:12,
      color:C.mute, margin:0, lineSpacingMultiple:1.05});
    y += 1.42;
  });
  // 변수 칩
  s.addText("조절 변수", {x:6.35, y:6.3, w:2, h:0.3, fontFace:F, fontSize:11,
    color:C.dim, bold:true, margin:0});
  const vars = ["풍향", "풍속", "건물 밀집도", "인지~도착 시간"];
  let vx = 7.55;
  vars.forEach(v => { chip(s, vx, 6.26, 1.25, v, C.blue); vx += 1.35; });
}

/* ══════════════════════════════════════════════════════════
   ⑧ 국면 흐름 5단계
   ══════════════════════════════════════════════════════════ */
{
  const s = p.addSlide(); bg(s);
  header(s, "04 · 화재 확산 시뮬레이션", "발화부터 완전 진화까지 · 5국면", C.orange);
  const phases = [
    ["확산 중", "드론 도착 전 — 불길이 골목을 건너 번진다", C.red],
    ["포위 진압", "드론이 외곽 화선부터 차단한다", C.amber],
    ["화선 후퇴", "연소 구역 바깥선이 안쪽으로 밀린다", C.blue],
    ["확산 저지", "신규 착화가 멈춘다", C.mint],
    ["완전 진화", "모든 연소가 종료된다", C.green],
  ];
  const n = 5, gap = 0.25, cw = (12.1 - gap*(n-1))/n, cy = 2.15, ch = 3.7;
  let x = 0.6;
  phases.forEach(([t, d, col], i) => {
    card(s, x, cy, cw, ch, C.card, C.border);
    s.addShape(OVAL, {x:x+cw/2-0.4, y:cy+0.35, w:0.8, h:0.8, fill:{color:C.bgDark},
      line:{color:col, width:2}});
    s.addText(String(i+1), {x:x+cw/2-0.4, y:cy+0.35, w:0.8, h:0.8, align:"center",
      valign:"middle", fontFace:FM, fontSize:26, color:col, bold:true, margin:0});
    s.addText(t, {x:x+0.05, y:cy+1.35, w:cw-0.1, h:0.5, align:"center", fontFace:F,
      fontSize:15, color:col, bold:true, margin:0});
    s.addText(d, {x:x+0.15, y:cy+1.9, w:cw-0.3, h:1.6, align:"center", fontFace:F,
      fontSize:11.5, color:C.mute, margin:0, lineSpacingMultiple:1.15, valign:"top"});
    if (i < n-1)
      s.addText("›", {x:x+cw-0.02, y:cy, w:gap+0.04, h:ch, align:"center",
        valign:"middle", fontFace:F, fontSize:22, color:C.dim, bold:true, margin:0});
    x += cw + gap;
  });
  s.addText("각 국면 전환 시각은 시뮬레이션이 자동 기록한다 — 화선 후퇴·확산 저지·완전 진화 시점.", {
    x:0.6, y:6.35, w:12.1, h:0.4, align:"center", fontFace:F, fontSize:12,
    color:C.dim, italic:true, margin:0});
}

/* ══════════════════════════════════════════════════════════
   ⑨ 시연 캡처 4컷
   ══════════════════════════════════════════════════════════ */
{
  const s = p.addSlide(); bg(s);
  header(s, "04 · 화재 확산 시뮬레이션", "시연 — 마산어시장 지점 재생", C.orange);
  const panels = [
    [0, "발화", "실제 도면상 건물에서 착화", []],
    [1, "확산", "골목을 건너 외곽으로 번짐", []],
    [2, "포위 진압", "드론 6대 외곽 화선 차단", [[3,5],[4,9],[8,4],[7,7],[2,7]]],
    [3, "완전 진화", "신규 착화 중단 → 진화", [[5,4],[6,8],[4,6]]],
  ];
  const cell = 0.19, gx0 = 1.4, gy0 = 1.85, stepx = 6.1, stepy = 2.55, tdx = 2.55;
  panels.forEach(([stage, t, d, drones], i) => {
    const gx = gx0 + (i % 2) * stepx;
    const gy = gy0 + Math.floor(i/2) * stepy;
    fireGrid(s, gx, gy, cell, stage, {drones});
    s.addText(`${i+1}. ${t}`, {x:gx+tdx, y:gy+0.35, w:2.6, h:0.4, fontFace:F,
      fontSize:15, color:C.orange, bold:true, margin:0});
    s.addText(d, {x:gx+tdx, y:gy+0.82, w:2.6, h:1.4, fontFace:F, fontSize:11.5,
      color:C.mute, margin:0, lineSpacingMultiple:1.15, valign:"top"});
  });
}

/* ══════════════════════════════════════════════════════════
   ⑩ 대응시간 비교
   ══════════════════════════════════════════════════════════ */
{
  const s = p.addSlide(); bg(s);
  header(s, "04 · 화재 확산 시뮬레이션", "대응시간 — 소방차 vs 드론", C.orange);
  s.addText("화재 인지 시점을 공통 기준으로 비교 (마산어시장 예시 시나리오)", {
    x:0.6, y:1.5, w:12, h:0.35, fontFace:F, fontSize:12.5, color:C.mute, margin:0});
  // 소방차 카드
  card(s, 0.6, 2.05, 3.85, 3.05, C.card, C.border);
  s.addText("소방차", {x:0.6, y:2.3, w:3.85, h:0.4, align:"center", fontFace:F,
    fontSize:16, color:C.blue, bold:true, margin:0});
  s.addText("실도로 주행 + 출동준비", {x:0.6, y:2.72, w:3.85, h:0.35, align:"center",
    fontFace:F, fontSize:11, color:C.mute, margin:0});
  s.addText("8:40", {x:0.6, y:3.15, w:3.85, h:1.0, align:"center", fontFace:FM,
    fontSize:52, color:C.blue, bold:true, margin:0});
  s.addText("+ 좁은 골목은 입구까지만", {x:0.6, y:4.35, w:3.85, h:0.5, align:"center",
    fontFace:F, fontSize:11.5, color:C.redSoft, margin:0});
  // 드론 카드
  card(s, 4.65, 2.05, 3.85, 3.05, "1F1206", C.orange);
  s.addText("드론 (직선 비행)", {x:4.65, y:2.3, w:3.85, h:0.4, align:"center",
    fontFace:F, fontSize:16, color:C.orange, bold:true, margin:0});
  s.addText("최근접 거점 → 화점 직상공", {x:4.65, y:2.72, w:3.85, h:0.35, align:"center",
    fontFace:F, fontSize:11, color:C.orange2, margin:0});
  s.addText("3:20", {x:4.65, y:3.15, w:3.85, h:1.0, align:"center", fontFace:FM,
    fontSize:52, color:C.orange, bold:true, margin:0});
  s.addText("골목 위를 그대로 넘어 도착", {x:4.65, y:4.35, w:3.85, h:0.5, align:"center",
    fontFace:F, fontSize:11.5, color:C.orange2, margin:0});
  // 결과 배너 (우)
  card(s, 8.7, 2.05, 4.0, 3.05, C.card2, "166534");
  s.addText("드론이 먼저", {x:8.7, y:2.35, w:4.0, h:0.4, align:"center", fontFace:F,
    fontSize:15, color:C.green2, bold:true, margin:0});
  s.addText("5:20", {x:8.7, y:2.85, w:4.0, h:1.1, align:"center", fontFace:FM,
    fontSize:60, color:C.green, bold:true, margin:0});
  s.addText("먼저 도착", {x:8.7, y:3.95, w:4.0, h:0.4, align:"center", fontFace:F,
    fontSize:16, color:C.green2, bold:true, margin:0});
  s.addText("초동 골든타임을 확보한다", {x:8.7, y:4.45, w:4.0, h:0.4, align:"center",
    fontFace:F, fontSize:12, color:C.mute, margin:0});
  // 하단 주석
  s.addText([
    {text:"공통 인지·신고 지연은 양쪽에 동일하게 적용했다. ", options:{color:C.dim}},
    {text:"소방차 = OSRM 실도로 라우팅 + 출동준비 1분, 드론 = 거점→화점 직선 비행.", options:{color:C.mute}},
  ], {x:0.6, y:5.35, w:12.1, h:0.9, fontFace:F, fontSize:12, margin:0, lineSpacingMultiple:1.1});
  s.addText("※ 수치는 예시 시나리오 — 지점·거점 거리에 따라 달라진다.", {x:0.6, y:6.15, w:12,
    h:0.35, fontFace:F, fontSize:10.5, color:C.dim, italic:true, margin:0});
}

/* ══════════════════════════════════════════════════════════
   ⑪ 군집 비행 (Boids)
   ══════════════════════════════════════════════════════════ */
{
  const s = p.addSlide(); bg(s);
  header(s, "05 · 드론 군집 로직", "중앙 제어 없는 군집 자율비행 · Boids", C.blue);
  s.addText("각 드론은 주변 이웃의 위치·속도만 보고 스스로 가속도를 정한다 — 분산 제어.", {
    x:0.6, y:1.5, w:12, h:0.35, fontFace:F, fontSize:12.5, color:C.mute, margin:0});
  const rules = [
    ["분리", "Separation", "안전거리보다 가까운 이웃을 밀어내 충돌을 막는다", C.red2,
      [[0.9,0.55],[1.75,0.95],[0.75,1.25]], "sep"],
    ["정렬", "Alignment", "이웃의 평균 속도에 방향을 맞춘다", C.blue,
      [[0.7,0.7],[1.35,0.65],[2.0,0.6]], "ali"],
    ["결합", "Cohesion", "이웃 무게중심 방향으로 모인다", C.green,
      [[0.6,0.5],[2.0,0.6],[1.2,1.4]], "coh"],
  ];
  let x = 0.6; const cw = 3.9, gap = 0.2, cy = 2.05, ch = 4.35;
  rules.forEach(([ko, en, d, col, pts, kind]) => {
    card(s, x, cy, cw, ch, C.card, C.border);
    s.addText(ko, {x:x+0.3, y:cy+0.25, w:cw-0.6, h:0.45, fontFace:F, fontSize:19,
      color:col, bold:true, margin:0});
    s.addText(en, {x:x+0.3, y:cy+0.72, w:cw-0.6, h:0.3, fontFace:FM, fontSize:11,
      color:C.dim, bold:true, charSpacing:1, margin:0});
    // 미니 도식 패널
    const px = x+0.3, py = cy+1.15, pw = cw-0.6, ph = 1.75;
    s.addShape(RR, {x:px, y:py, w:pw, h:ph, rectRadius:0.06, fill:{color:C.bgDark},
      line:{color:C.border2, width:1}});
    pts.forEach(([dx, dy]) => dot(s, px+dx, py+dy, 0.2, col, C.text));
    s.addText(d, {x:x+0.3, y:cy+3.1, w:cw-0.6, h:1.1, fontFace:F, fontSize:12.5,
      color:C.mute, margin:0, lineSpacingMultiple:1.15, valign:"top"});
    x += cw + gap;
  });
}

/* ══════════════════════════════════════════════════════════
   ⑫ 역할 기반 소방 드론
   ══════════════════════════════════════════════════════════ */
{
  const s = p.addSlide(); bg(s);
  header(s, "05 · 드론 군집 로직", "역할 기반 소방 드론", C.blue);
  const roles = [
    ["SCOUT", "수색 · 경로 탐색", "열화상으로 화점·요구조자를 찾아 좌표를 공유한다", C.blue],
    ["SUPPRESSOR", "화점 초동 진압", "화점에 접근해 소화탄을 투하, 확산 전 시간을 번다", C.orange],
    ["GUIDE", "탈출 안내 · 보호", "요구조자에게 안전한 탈출 경로를 안내한다", C.green],
  ];
  let x = 0.6; const cw = 3.9, gap = 0.2, cy = 1.85, ch = 3.05;
  roles.forEach(([en, ko, d, col]) => {
    card(s, x, cy, cw, ch, C.card, col);
    s.addText(en, {x:x+0.3, y:cy+0.3, w:cw-0.6, h:0.45, fontFace:FM, fontSize:20,
      color:col, bold:true, charSpacing:1, margin:0});
    s.addText(ko, {x:x+0.3, y:cy+0.85, w:cw-0.6, h:0.4, fontFace:F, fontSize:15,
      color:C.text, bold:true, margin:0});
    s.addText(d, {x:x+0.3, y:cy+1.35, w:cw-0.6, h:1.5, fontFace:F, fontSize:12.5,
      color:C.mute, margin:0, lineSpacingMultiple:1.2, valign:"top"});
    x += cw + gap;
  });
  // 자율 전환 배너
  card(s, 0.6, 5.15, 12.1, 1.25, C.card2, C.border);
  s.addText("소화탄 소진 → 자율 역할 전환", {x:0.9, y:5.33, w:6, h:0.4, fontFace:F,
    fontSize:14.5, color:C.orange, bold:true, margin:0});
  s.addText([
    {text:"SUPPRESSOR는 소화탄이 떨어지면 스스로 ", options:{color:C.mute}},
    {text:"GUIDE로 전환", options:{color:C.green2, bold:true}},
    {text:"해, 진압을 마친 드론이 곧바로 인명 탈출 안내에 투입된다. 탐지 임계값·개수 음수 방지 등 방어 로직도 반영했다.", options:{color:C.mute}},
  ], {x:0.9, y:5.75, w:11.5, h:0.6, fontFace:F, fontSize:12.5, margin:0, lineSpacingMultiple:1.1});
}

/* ══════════════════════════════════════════════════════════
   ⑬ 화점 진압 · 탈출 안내 (A* / 좌표변환)
   ══════════════════════════════════════════════════════════ */
{
  const s = p.addSlide(); bg(s);
  header(s, "05 · 드론 군집 로직", "화염을 피하는 탈출 경로 · 실좌표 복원", C.blue);
  // 좌: A* 격자 도식
  const gx = 0.9, gy = 2.0, cs = 0.4, N = 10;
  s.addShape(RR, {x:gx-0.1, y:gy-0.1, w:N*cs+0.2, h:N*cs+0.2, rectRadius:0.06,
    fill:{color:C.panel}, line:{color:C.border, width:1}});
  const fireCells = new Set(["3,4","3,5","4,4","4,5","5,5","2,5","6,6","6,7"]);
  const path = ["8,1","7,1","6,1","5,2","4,2","3,2","2,3","1,4","1,5","1,6","1,7","2,8"];
  const pathSet = new Set(path);
  for (let r=0;r<N;r++) for (let c=0;c<N;c++){
    let col = C.fuel;
    if (fireCells.has(`${r},${c}`)) col = C.orange;
    else if (pathSet.has(`${r},${c}`)) col = C.mint;
    s.addShape(RECT, {x:gx+c*cs, y:gy+r*cs, w:cs*0.92, h:cs*0.92,
      fill:{color:col}, line:{type:"none"}});
  }
  // 시작/끝 마커
  dot(s, gx+1*cs+cs*0.1, gy+8*cs+cs*0.1, cs*0.72, C.green, C.text);
  dot(s, gx+8*cs+cs*0.1, gy+2*cs+cs*0.1, cs*0.72, C.blue, C.text);
  s.addText("● 요구조자   ● 안전지대   ■ 화염 회피 경로", {x:gx-0.1, y:gy+N*cs+0.15,
    w:N*cs+0.2, h:0.3, align:"center", fontFace:F, fontSize:10.5, color:C.mute, margin:0});
  // 우: 설명 카드 2개
  const items = [
    ["화염 회피 A* 경로 탐색", C.mint,
      "8방향(2D)·6방향(3D) A*로 화염 셀을 피해 탈출 경로를 계산한다. 3D hazard map을 넘기면 다층 건물의 계단·개구부 층간 이동까지 포함한다."],
    ["픽셀 → 월드 좌표 복원", C.blue,
      "핀홀 카메라 모델과 드론 자세(위치·요각)로 탐지 픽셀의 광선을 지면과 교차시켜 실제 위경도 좌표를 복원한다."],
  ];
  let y = 2.0;
  items.forEach(([t, col, d]) => {
    card(s, 5.85, y, 6.85, 2.15, C.card, C.border);
    s.addText(t, {x:6.15, y:y+0.25, w:6.3, h:0.45, fontFace:F, fontSize:16.5,
      color:col, bold:true, margin:0});
    s.addText(d, {x:6.15, y:y+0.78, w:6.35, h:1.25, fontFace:F, fontSize:13,
      color:C.mute, margin:0, lineSpacingMultiple:1.25, valign:"top"});
    y += 2.35;
  });
}

/* ══════════════════════════════════════════════════════════
   ⑭ 통합 시나리오
   ══════════════════════════════════════════════════════════ */
{
  const s = p.addSlide(); bg(s);
  header(s, "05 · 드론 군집 로직", "한 현장에서 맞물리는 통합 시나리오", C.blue);
  const flow = [
    ["탐지", "SCOUT", "열화상으로 화점·요구조자 좌표 확보", C.blue],
    ["포위 진압", "군집 + SUPPRESSOR", "외곽 화선부터 소화탄으로 차단", C.orange],
    ["탈출 안내", "GUIDE", "요구조자에게 화염 회피 경로 안내", C.green],
  ];
  const n = 3, gap = 0.55, cw = (12.1 - gap*(n-1))/n, cy = 2.2, ch = 2.9;
  let x = 0.6;
  flow.forEach(([t, tag, d, col], i) => {
    card(s, x, cy, cw, ch, C.card, C.border);
    s.addShape(OVAL, {x:x+0.3, y:cy+0.32, w:0.7, h:0.7, fill:{color:C.bgDark},
      line:{color:col, width:1.5}});
    s.addText(String(i+1), {x:x+0.3, y:cy+0.32, w:0.7, h:0.7, align:"center",
      valign:"middle", fontFace:FM, fontSize:20, color:col, bold:true, margin:0});
    s.addText(t, {x:x+1.15, y:cy+0.38, w:cw-1.4, h:0.55, valign:"middle", fontFace:F,
      fontSize:18, color:C.text, bold:true, margin:0});
    chip(s, x+0.32, cy+1.25, cw-0.64, tag, col);
    s.addText(d, {x:x+0.32, y:cy+1.8, w:cw-0.64, h:0.95, fontFace:F, fontSize:12.5,
      color:C.mute, margin:0, lineSpacingMultiple:1.2, valign:"top"});
    if (i < n-1)
      s.addText("›", {x:x+cw+0.02, y:cy, w:gap-0.04, h:ch, align:"center",
        valign:"middle", fontFace:F, fontSize:30, color:C.orange, bold:true, margin:0});
    x += cw + gap;
  });
  card(s, 0.6, 5.5, 12.1, 0.95, "1F1206", C.orange);
  s.addText([
    {text:"소방차가 진입하기 전, 상공의 군집 드론이 ", options:{color:C.mute}},
    {text:"탐지 → 진압 → 안내", options:{color:C.orange2, bold:true}},
    {text:"를 끊김 없이 이어 초동 대응을 채운다.", options:{color:C.mute}},
  ], {x:0.9, y:5.5, w:11.5, h:0.95, valign:"middle", fontFace:F, fontSize:14, margin:0});
}

/* ══════════════════════════════════════════════════════════
   ⑮ 핵심 성과
   ══════════════════════════════════════════════════════════ */
{
  const s = p.addSlide(); bg(s);
  header(s, "06 · 기대효과", "핵심 성과 — 피해를 얼마나 줄이나", C.green);
  // 좌: 큰 저감 스탯
  card(s, 0.6, 1.9, 4.35, 4.45, C.card2, "166534");
  s.addText("피해 면적", {x:0.6, y:2.2, w:4.35, h:0.4, align:"center", fontFace:F,
    fontSize:15, color:C.green2, bold:true, margin:0});
  s.addText("68%", {x:0.6, y:2.7, w:4.35, h:1.5, align:"center", fontFace:FM,
    fontSize:88, color:C.green, bold:true, margin:0});
  s.addText("저감", {x:0.6, y:4.25, w:4.35, h:0.5, align:"center", fontFace:F,
    fontSize:22, color:C.green2, bold:true, margin:0});
  s.addText("무대응 대비 · 드론 6대 투입", {x:0.6, y:4.85, w:4.35, h:0.4, align:"center",
    fontFace:F, fontSize:12.5, color:C.mute, margin:0});
  // 막대 비교
  const bx = 1.0, by = 5.5, bw = 3.55;
  s.addShape(RECT, {x:bx, y:by, w:bw, h:0.3, fill:{color:C.red}, line:{type:"none"}});
  s.addText("무대응 12,400㎡", {x:bx+0.1, y:by, w:bw, h:0.3, valign:"middle",
    fontFace:FM, fontSize:10, color:"FFFFFF", bold:true, margin:0});
  s.addShape(RECT, {x:bx, y:by+0.4, w:bw*0.32, h:0.3, fill:{color:C.green}, line:{type:"none"}});
  s.addText("드론 4,000㎡", {x:bx+bw*0.32+0.1, y:by+0.4, w:2, h:0.3, valign:"middle",
    fontFace:FM, fontSize:10, color:C.green2, bold:true, margin:0});
  // 우: 보조 지표 + 차별성
  const stats = [
    ["최대 화선 반경", "46 m", C.orange],
    ["동시 연소 최대", "23 동", C.red2],
    ["완전 진화", "21 분", C.green],
    ["드론이 먼저 도착", "5:20", C.blue],
  ];
  stats.forEach(([t, v, col], i) => {
    const cx = 5.2 + (i%2)*3.85, cyy = 1.9 + Math.floor(i/2)*1.2;
    card(s, cx, cyy, 3.6, 1.05, C.card, C.border);
    s.addText(v, {x:cx+0.25, y:cyy+0.12, w:3.1, h:0.6, fontFace:FM, fontSize:30,
      color:col, bold:true, margin:0});
    s.addText(t, {x:cx+0.25, y:cyy+0.68, w:3.1, h:0.3, fontFace:F, fontSize:11.5,
      color:C.mute, margin:0});
  });
  card(s, 5.2, 4.35, 7.5, 2.0, "1F1206", C.orange);
  s.addText("차별성", {x:5.45, y:4.55, w:3, h:0.4, fontFace:F, fontSize:14,
    color:C.orange, bold:true, margin:0});
  const diffs = [
    "가상 격자가 아닌 실주소·실도로 위에서 검증",
    "팀 현장조사 진입불가 구간을 근거 데이터로 반영",
    "비행 → 진압 → 탈출 안내를 하나로 통합",
  ];
  let dy = 5.0;
  diffs.forEach(d => {
    dot(s, 5.5, dy+0.08, 0.14, C.orange2);
    s.addText(d, {x:5.78, y:dy-0.05, w:6.7, h:0.4, fontFace:F, fontSize:12.5,
      color:C.text, margin:0});
    dy += 0.45;
  });
  s.addText("※ 수치는 예시 시나리오(마산어시장·드론 6대·풍속 3m/s·밀집도 88%).", {
    x:0.6, y:6.9, w:12, h:0.3, fontFace:F, fontSize:10, color:C.dim, italic:true, margin:0});
}

/* ══════════════════════════════════════════════════════════
   ⑯ 기대효과 & 마무리
   ══════════════════════════════════════════════════════════ */
{
  const s = p.addSlide(); bg(s, C.bgDark);
  header(s, "06 · 기대효과", "기대효과와 확장", C.green);
  const eff = [
    ["초동 골든타임 확보", "소방차 진입 전, 상공 드론이 확산을 먼저 늦춘다", C.orange],
    ["진입불가 구간 상시 감시", "취약 골목을 데이터로 관리·순찰한다", C.blue],
    ["인명 탈출 안내", "연기 속 요구조자에게 안전 경로를 제시한다", C.green],
    ["타 지자체 확장", "실주소만 넣으면 어느 구도심에도 적용된다", C.mint],
  ];
  let x = 0.6; const cw = 3.02, gap = 0.2, cy = 1.9, ch = 3.0;
  eff.forEach(([t, d, col], i) => {
    card(s, x, cy, cw, ch, C.card, C.border);
    dot(s, x+0.3, cy+0.35, 0.5, C.bgDark, col);
    s.addShape(OVAL, {x:x+0.42, y:cy+0.47, w:0.26, h:0.26, fill:{color:col}, line:{type:"none"}});
    s.addText(t, {x:x+0.25, y:cy+1.05, w:cw-0.5, h:0.75, fontFace:F, fontSize:14.5,
      color:C.text, bold:true, margin:0, valign:"top"});
    s.addText(d, {x:x+0.25, y:cy+1.85, w:cw-0.5, h:1.0, fontFace:F, fontSize:11.5,
      color:C.mute, margin:0, lineSpacingMultiple:1.2, valign:"top"});
    x += cw + gap;
  });
  // 마무리 배너
  card(s, 0.6, 5.2, 12.1, 1.55, C.card2, C.orange);
  s.addText("골목을 건너는 불을, 골목을 건너는 드론으로", {x:0.9, y:5.45, w:11.5, h:0.5,
    fontFace:F, fontSize:20, color:C.orange, bold:true, margin:0});
  s.addText("실제 도로 데이터 · 화재확산 시뮬레이션 · 군집 소방 드론을 하나로 — 감사합니다. (Q&A)", {
    x:0.9, y:6.05, w:11.5, h:0.5, fontFace:F, fontSize:14, color:C.mute, margin:0});
}

const OUT = process.argv[2] || "deck.pptx";
p.writeFile({ fileName: OUT }).then(f => console.log("saved", f));
