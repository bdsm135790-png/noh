const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE";
p.author = "팀 군체";
p.title = "데이터로 정한 소방 드론 거점, 그리고 현장 로직";

const RR=p.ShapeType.roundRect, RECT=p.ShapeType.rect, OVAL=p.ShapeType.ellipse,
      TRI=p.ShapeType.triangle, LINE=p.ShapeType.line, STAR=p.ShapeType.star5;
const F="Malgun Gothic", FM="Consolas";

const C = {
  page:"FFFFFF", dark:"0F172A",
  card:"FFFFFF", panel:"F1F5F9", panel2:"F8FAFC", border:"E2E8F0", border2:"CBD5E1",
  ink:"0F172A", body:"334155", mute:"64748B", dim:"94A3B8",
  red:"DC2626", redL:"FEE2E2", orange:"EA580C", orangeL:"FFEDD5",
  blue:"2563EB", blueL:"DBEAFE", sky:"0EA5E9", violet:"7C3AED", violetL:"EDE9FE",
  green:"15803D", greenL:"DCFCE7", amber:"D97706",
  onDark:"E2E8F0", onDarkMute:"94A3B8",
};
const CAT = ["2563EB","EA580C","7C3AED","15803D"];
const HEAT = ["FEE2E2","FECACA","FCA5A5","F87171","EF4444","DC2626","B91C1C","991B1B"];

const bg=(s,c=C.page)=>{ s.background={color:c}; };
function header(s, kicker, title, kColor=C.red){
  s.addText(kicker.toUpperCase(), {x:0.6, y:0.42, w:12.1, h:0.3, fontFace:F, fontSize:12.5, color:kColor, bold:true, charSpacing:3, margin:0});
  s.addText(title, {x:0.6, y:0.72, w:12.1, h:0.72, fontFace:F, fontSize:27, color:C.ink, bold:true, margin:0});
}
function headerDark(s, kicker, title, kColor=C.violet){
  s.addText(kicker.toUpperCase(), {x:0.6, y:0.42, w:12.1, h:0.3, fontFace:F, fontSize:12.5, color:kColor, bold:true, charSpacing:3, margin:0});
  s.addText(title, {x:0.6, y:0.72, w:12.1, h:0.72, fontFace:F, fontSize:26, color:C.onDark, bold:true, margin:0});
}
function card(s,x,y,w,h,fill=C.card,border=C.border,radius=0.09){
  s.addShape(RR,{x,y,w,h,rectRadius:radius,fill:{color:fill},line:{color:border,width:1},
    shadow:{type:"outer",color:"334155",opacity:0.12,blur:6,offset:2,angle:90}});
}
function flatCard(s,x,y,w,h,fill=C.panel,border=C.border){ s.addShape(RR,{x,y,w,h,rectRadius:0.08,fill:{color:fill},line:{color:border,width:1}}); }
function dot(s,x,y,d,color,ring){ s.addShape(OVAL,{x,y,w:d,h:d,fill:{color},line:ring?{color:ring,width:1.5}:{type:"none"}}); }
function chip(s,x,y,w,text,color,fillL){
  s.addShape(RR,{x,y,w,h:0.36,rectRadius:0.18,fill:{color:fillL||C.panel},line:{color,width:1}});
  s.addText(text,{x,y,w,h:0.36,align:"center",valign:"middle",fontFace:F,fontSize:10.5,color,bold:true,margin:0});
}
function numBadge(s,x,y,d,n,color){
  s.addShape(OVAL,{x,y,w:d,h:d,fill:{color},line:{type:"none"}});
  s.addText(String(n),{x,y,w:d,h:d,align:"center",valign:"middle",fontFace:FM,fontSize:d*36,color:"FFFFFF",bold:true,margin:0});
}
function riskMap(s, x, y, w, h, opts={}){
  const NX=11, NY=8, cw=w/NX, ch=h/NY;
  const hs=[[3.0,3.2,1.0],[4.2,4.6,0.85],[7.6,2.4,0.7]];
  s.addShape(RECT,{x,y,w,h,fill:{color:"EEF2F6"},line:{color:C.border,width:1}});
  for(let r=0;r<NY;r++) for(let c=0;c<NX;c++){
    let v=0; hs.forEach(([hx,hy,wt])=>{ const d=Math.hypot(c-hx,r-hy); v+=wt*Math.exp(-d*d/5.5); });
    let idx=Math.max(0,Math.min(HEAT.length-1,Math.round(v*7)));
    if(idx<1 && ((r+c)%3===0)) idx=1;
    s.addShape(RECT,{x:x+c*cw+0.01,y:y+r*ch+0.01,w:cw-0.02,h:ch-0.02,fill:{color:HEAT[idx]},line:{type:"none"}});
  }
  (opts.stations||[]).forEach(st=>{
    const sx=x+st.c*cw, sy=y+st.r*ch;
    if(st.sel){ s.addShape(OVAL,{x:sx-0.28,y:sy-0.28,w:0.56,h:0.56,fill:{color:"FFFFFF"},line:{color:C.blue,width:2.5}});
      s.addShape(STAR,{x:sx-0.17,y:sy-0.17,w:0.34,h:0.34,fill:{color:C.blue},line:{type:"none"}});
    } else { s.addShape(OVAL,{x:sx-0.13,y:sy-0.13,w:0.26,h:0.26,fill:{color:"FFFFFF"},line:{color:C.mute,width:2}}); }
    if(st.name) s.addText(st.name,{x:sx-0.9,y:sy+0.18,w:1.8,h:0.28,align:"center",fontFace:F,fontSize:9,color:st.sel?C.blue:C.mute,bold:true,margin:0});
  });
}

/* ═══ ① 표지 ═══ */
{
  const s=p.addSlide(); bg(s,C.dark);
  s.addText("제6회 빅데이터로 우리동네 문제해결 아이디어 공모대회 · 경남", {x:0.75,y:0.75,w:11,h:0.35,fontFace:F,fontSize:13,color:C.sky,bold:true,margin:0});
  s.addText([{text:"데이터로 정한 소방 드론 거점,\n",options:{color:C.onDark}},{text:"그리고 현장에서의 대응 로직",options:{color:C.orange}}],
    {x:0.72,y:1.75,w:11.9,h:1.9,fontFace:F,fontSize:40,bold:true,lineSpacingMultiple:1.08,margin:0});
  s.addText("최근 1년 화재 발생 빅데이터로 창원을 정하고, 지도 분석으로 거점을 정한다", {x:0.75,y:3.75,w:11.5,h:0.5,fontFace:F,fontSize:16.5,color:C.onDarkMute,margin:0});
  const parts=[["PART 1","어디에 배치할 것인가","화재 빅데이터 분석 → 창원 · 거점 소방서 선정",C.red],
    ["PART 2","도착 후 어떻게 움직이는가","출동 → 편대 SOP-D → 시연 → 기대효과",C.violet]];
  let x=0.75;
  parts.forEach(([tag,t,d,col])=>{
    s.addShape(RR,{x,y:4.75,w:5.75,h:1.35,rectRadius:0.1,fill:{color:"172033"},line:{color:col,width:1.3}});
    s.addText(tag,{x:x+0.3,y:4.92,w:2,h:0.32,fontFace:FM,fontSize:12,color:col,bold:true,charSpacing:2,margin:0});
    s.addText(t,{x:x+0.3,y:5.2,w:5.15,h:0.4,fontFace:F,fontSize:16,color:C.onDark,bold:true,margin:0});
    s.addText(d,{x:x+0.3,y:5.6,w:5.2,h:0.45,fontFace:F,fontSize:11,color:C.onDarkMute,margin:0});
    x+=6.05;
  });
  s.addText([{text:"팀 군체",options:{color:C.orange,bold:true}},{text:"   ·   한태영 · 김상도 · 노현수   ·   경상국립대학교 방산시스템",options:{color:C.dim}}],
    {x:0.75,y:6.55,w:11,h:0.4,fontFace:F,fontSize:12.5,margin:0});
}

/* ═══ ② PART 1 표지 ═══ */
{
  const s=p.addSlide(); bg(s,C.dark);
  s.addText("PART 1", {x:0.75,y:2.5,w:5,h:0.6,fontFace:FM,fontSize:22,color:C.red,bold:true,charSpacing:4,margin:0});
  s.addText("어디에 배치할 것인가", {x:0.72,y:3.1,w:11.5,h:0.9,fontFace:F,fontSize:38,color:C.onDark,bold:true,margin:0});
  s.addText("최근 1년 화재 발생 빈도로 대상 지역을 창원으로 정하고 — 지도에서 소방차가 못 가는 경로를 찾아 드론 거점 소방서를 정한다.",
    {x:0.75,y:4.05,w:11.4,h:0.8,fontFace:F,fontSize:15,color:C.onDarkMute,margin:0,lineSpacingMultiple:1.3});
  const steps=["데이터 수집","지역 선정 · 창원","취약지 분석","거점 선정"];
  let x=0.75;
  steps.forEach((t,i)=>{
    s.addShape(RR,{x,y:5.15,w:2.7,h:0.7,rectRadius:0.1,fill:{color:"172033"},line:{color:C.border2,width:1}});
    s.addText([{text:`0${i+1}  `,options:{color:C.red,bold:true,fontFace:FM}},{text:t,options:{color:C.onDark}}],
      {x:x+0.2,y:5.15,w:2.4,h:0.7,valign:"middle",fontFace:F,fontSize:12,bold:true,margin:0});
    if(i<3) s.addText("›",{x:x+2.7,y:5.15,w:0.35,h:0.7,align:"center",valign:"middle",fontFace:F,fontSize:20,color:C.dim,margin:0});
    x+=3.05;
  });
}

/* ═══ ③ STEP 01 데이터 수집 ═══ */
{
  const s=p.addSlide(); bg(s);
  header(s,"PART 1 · STEP 01","화재 관련 데이터를 모은다");
  const data=[
    ["화재 발생 빈도","소방안전 빅데이터 플랫폼","최근 1년 시·군구별 화재 건수",C.red,C.redL],
    ["도로폭·도로망","지자체 · OSM","골목 폭 · 소방차 진입 가능성",C.orange,C.orangeL],
    ["건축물대장","국가공간정보포털","노후 건축물 비율 → 취약 지수",C.violet,C.violetL],
    ["고령·인구","통계청 KOSIS·SGIS","65세+ 교통약자 밀집 지역",C.blue,C.blueL],
    ["소방용수·진입곤란","공공데이터포털","소화전 · 진입곤란 구간 현황",C.green,C.greenL],
  ];
  let x=0.6; const cw=2.4, gap=0.15, cy=1.85, ch=3.0;
  data.forEach(([t,src,use,col,fl])=>{
    card(s,x,cy,cw,ch);
    s.addShape(RR,{x:x+0.22,y:cy+0.25,w:cw-0.44,h:0.62,rectRadius:0.08,fill:{color:fl},line:{type:"none"}});
    s.addText(t,{x:x+0.22,y:cy+0.25,w:cw-0.44,h:0.62,align:"center",valign:"middle",fontFace:F,fontSize:12.5,color:col,bold:true,margin:0,lineSpacingMultiple:0.95});
    s.addText(src,{x:x+0.22,y:cy+1.02,w:cw-0.44,h:0.5,fontFace:F,fontSize:10.5,color:C.dim,bold:true,margin:0,valign:"top",lineSpacingMultiple:1.05});
    s.addText(use,{x:x+0.22,y:cy+1.6,w:cw-0.44,h:1.2,fontFace:F,fontSize:11.5,color:C.body,margin:0,lineSpacingMultiple:1.2,valign:"top"});
    x+=cw+gap;
  });
  flatCard(s,0.6,5.15,12.1,1.2,C.panel2);
  s.addText([{text:"핵심 = 소방안전 빅데이터 플랫폼의 최근 1년 화재 발생 빈도.  ",options:{color:C.ink,bold:true}},
    {text:"여기에 도로·건축·인구 데이터를 파이썬(Pandas·NumPy·Matplotlib)으로 통합·시각화한다.",options:{color:C.mute}}],
    {x:0.9,y:5.15,w:11.5,h:1.2,valign:"middle",fontFace:F,fontSize:13.5,margin:0,lineSpacingMultiple:1.2});
}

/* ═══ ④ STEP 02 지역 선정 = 창원 ═══ */
{
  const s=p.addSlide(); bg(s);
  header(s,"PART 1 · STEP 02","대상 지역을 창원으로 정한다",C.red);
  s.addText("소방안전 빅데이터 플랫폼 · 최근 1년 · 경남 시·군별 화재 발생 건수 (창원시 = 5개 구 합산)",{x:0.6,y:1.5,w:11.5,h:0.35,fontFace:F,fontSize:12.5,color:C.mute,margin:0});
  s.addChart(p.ChartType.bar, [{name:"화재건수", labels:["창원시","김해시","진주시","양산시","밀양시","함안군","거제시"], values:[563,457,318,271,239,193,187]}],
    {x:0.6,y:1.95,w:8.0,h:4.35, barDir:"col", chartColors:["DC2626","93C5FD","93C5FD","93C5FD","93C5FD","93C5FD","93C5FD"],
     showValue:true, dataLabelPosition:"outEnd", dataLabelColor:C.ink, dataLabelFontFace:FM, dataLabelFontSize:11.5, dataLabelFontBold:true,
     showLegend:false, showTitle:false, catAxisLabelColor:C.body, catAxisLabelFontFace:F, catAxisLabelFontSize:11, catGridLine:{style:"none"}, catAxisLineColor:C.border2,
     valAxisHidden:true, valGridLine:{style:"none"}, valAxisMaxVal:640, barGapWidthPct:45});
  card(s,8.9,1.95,3.8,4.35,C.panel2,C.border);
  s.addText("대상 지역",{x:9.2,y:2.2,w:3.2,h:0.35,fontFace:F,fontSize:13,color:C.mute,bold:true,margin:0});
  s.addText("창원시",{x:9.2,y:2.56,w:3.3,h:0.6,fontFace:F,fontSize:28,color:C.red,bold:true,margin:0});
  s.addText("563",{x:9.2,y:3.25,w:2.4,h:0.85,fontFace:FM,fontSize:50,color:C.ink,bold:true,margin:0});
  s.addText("건 · 경남 최다",{x:9.2,y:4.12,w:3.3,h:0.35,fontFace:F,fontSize:12.5,color:C.mute,margin:0});
  s.addShape(LINE,{x:9.2,y:4.55,w:3.2,h:0,line:{color:C.border,width:1}});
  s.addText("경남 전체 화재의 15.8% 집중 — 화재 최다 도시를 드론 배치 대상 지역으로 확정",{x:9.2,y:4.68,w:3.3,h:1.5,fontFace:F,fontSize:12.5,color:C.body,margin:0,valign:"top",lineSpacingMultiple:1.3});
}

/* ═══ ⑤ STEP 03 창원 구별 화재와 피해 ═══ */
{
  const s=p.addSlide(); bg(s);
  header(s,"PART 1 · STEP 03","분석 ① — 창원 구별 화재와 피해",C.orange);
  s.addText("소방안전 빅데이터 플랫폼 · 최근 1년 · 창원시 구별 화재 발생 건수",{x:0.6,y:1.5,w:11,h:0.35,fontFace:F,fontSize:12.5,color:C.mute,margin:0});
  s.addChart(p.ChartType.bar, [{name:"화재건수", labels:["의창구","진해구","마산합포구","성산구","마산회원구"], values:[126,117,116,116,88]}],
    {x:0.6,y:1.95,w:7.6,h:4.35, barDir:"col", chartColors:[C.orange],
     showValue:true, dataLabelPosition:"outEnd", dataLabelColor:C.ink, dataLabelFontFace:FM, dataLabelFontSize:12, dataLabelFontBold:true,
     showLegend:false, showTitle:false, catAxisLabelColor:C.body, catAxisLabelFontFace:F, catAxisLabelFontSize:11, catGridLine:{style:"none"}, catAxisLineColor:C.border2,
     valAxisHidden:true, valGridLine:{style:"none"}, valAxisMaxVal:145, barGapWidthPct:55});
  card(s,8.55,1.95,4.15,4.35,C.panel2,C.border);
  s.addText("읽는 법",{x:8.85,y:2.2,w:3.6,h:0.35,fontFace:F,fontSize:14,color:C.orange,bold:true,margin:0});
  ["구별 화재건수는 88~126건으로 비슷","차이는 도로·노후·인명피해에서 갈린다","마산합포구는 인명피해가 창원 최다"].forEach((t,i)=>{
    dot(s,8.9,2.78+i*0.62,0.15,C.orange);
    s.addText(t,{x:9.2,y:2.62+i*0.62,w:3.3,h:0.6,fontFace:F,fontSize:12,color:C.body,margin:0,valign:"middle",lineSpacingMultiple:1.1});
  });
  flatCard(s,8.85,4.75,3.6,1.3,C.redL,"FCA5A5");
  s.addText("마산합포구",{x:9.1,y:4.9,w:3.1,h:0.35,fontFace:F,fontSize:12,color:C.red,bold:true,margin:0});
  s.addText("인명피해 22명(사망 5) — 원도심 위험 집중",{x:9.1,y:5.25,w:3.2,h:0.8,fontFace:F,fontSize:12,color:C.ink,margin:0,valign:"top",lineSpacingMultiple:1.15});
}

/* ═══ ⑥ STEP 04 지도 — 소방차 진입불가 지역 ═══ */
{
  const s=p.addSlide(); bg(s);
  header(s,"PART 1 · STEP 04","지도에서 소방차 진입불가 지역을 찾는다",C.orange);
  const px=0.6,py=1.8,pw=7.7,ph=4.55;
  card(s,px,py,pw,ph,C.card,C.border);
  const mx=px+0.25,my=py+0.25,mw=pw-0.5,mh=ph-0.85;
  s.addShape(RECT,{x:mx,y:my,w:mw,h:mh,fill:{color:"EEF2F6"},line:{color:C.border,width:1}});
  const blk=(bx,by,bw,bh)=>s.addShape(RECT,{x:mx+bx,y:my+by,w:bw,h:bh,fill:{color:"DDE3EA"},line:{color:"CBD5E1",width:0.75}});
  [[0.4,0.4,1.3,0.9],[2.2,0.35,1.4,0.8],[5.0,0.45,1.4,0.9],[0.5,1.8,1.2,1.0],[3.6,1.7,1.3,1.1],[5.6,1.9,1.2,1.0],[1.9,2.6,1.3,0.7]].forEach(b=>blk(...b));
  const road=(x1,y1,x2,y2,col,wd)=>s.addShape(LINE,{x:mx+x1,y:my+y1,w:x2-x1,h:y2-y1,line:{color:col,width:wd}});
  road(0.2,1.55,mw-0.2,1.55,C.blue,4.5); road(2.0,0.2,2.0,mh-0.2,C.blue,4.5); road(4.9,1.55,4.9,mh-0.2,C.blue,4);
  road(2.0,1.55,3.1,0.7,C.red,3.5); road(4.9,1.55,5.9,0.85,C.red,3.5); road(0.9,1.55,0.9,2.7,C.red,3.5); road(3.5,2.9,4.6,3.15,C.red,3.5); road(6.2,1.55,6.7,2.7,C.red,3.5);
  const fire=(fx,fy)=>{ s.addShape(OVAL,{x:mx+fx-0.14,y:my+fy-0.14,w:0.28,h:0.28,fill:{color:C.orange},line:{color:C.red,width:1.5}}); };
  fire(3.1,0.7); fire(5.9,0.85); fire(0.9,2.7); fire(4.6,3.15); fire(6.7,2.7);
  s.addShape(OVAL,{x:mx+0.05,y:my+mh-0.55,w:0.4,h:0.4,fill:{color:"FFFFFF"},line:{color:C.blue,width:2.5}});
  s.addShape(RECT,{x:mx+0.14,y:my+mh-0.46,w:0.22,h:0.22,fill:{color:C.blue},line:{type:"none"}});
  s.addText("소방서",{x:mx-0.1,y:my+mh-0.16,w:0.7,h:0.22,align:"center",fontFace:F,fontSize:8,color:C.blue,bold:true,margin:0});
  const ly=py+ph-0.42;
  s.addShape(LINE,{x:px+0.3,y:ly+0.1,w:0.4,h:0,line:{color:C.red,width:3.5}}); s.addText("소방차 진입불가 경로",{x:px+0.78,y:ly-0.04,w:2.2,h:0.3,fontFace:F,fontSize:10,color:C.body,margin:0,valign:"middle"});
  s.addShape(LINE,{x:px+3.0,y:ly+0.1,w:0.4,h:0,line:{color:C.blue,width:3.5}}); s.addText("진입가능 도로",{x:px+3.48,y:ly-0.04,w:1.7,h:0.3,fontFace:F,fontSize:10,color:C.body,margin:0,valign:"middle"});
  dot(s,px+5.2,ly+0.02,0.18,C.orange,C.red); s.addText("화재 발생지점",{x:px+5.45,y:ly-0.04,w:1.9,h:0.3,fontFace:F,fontSize:10,color:C.body,margin:0,valign:"middle"});
  const steps=[
    ["화재지점 표시","최근 1년 창원 화재 발생지점을 지도에 올린다",C.orange],
    ["경로 탐색","각 지점까지 소방서에서 실측 도로망으로 경로를 찾는다",C.blue],
    ["빨간선 = 진입불가","경로 중 폭 4m 미만 구간을 빨간선으로 표시한다",C.red],
    ["드론 필요 지점","빨간선이 걸린 화재지점 = 드론이 가장 필요한 곳",C.violet],
  ];
  let y=1.9;
  steps.forEach(([t,d,col],i)=>{
    flatCard(s,8.5,y,4.2,1.02,C.panel2);
    numBadge(s,8.72,y+0.28,0.46,i+1,col);
    s.addText(t,{x:9.32,y:y+0.13,w:3.3,h:0.35,fontFace:F,fontSize:13,color:col,bold:true,margin:0});
    s.addText(d,{x:9.32,y:y+0.47,w:3.3,h:0.5,fontFace:F,fontSize:10.5,color:C.body,margin:0,lineSpacingMultiple:1.05,valign:"top"});
    y+=1.12;
  });
}

/* ═══ ⑦ STEP 05 종합 위험 지수 ═══ */
{
  const s=p.addSlide(); bg(s);
  header(s,"PART 1 · STEP 05","분석 ② — 종합 위험 지수로 합친다",C.orange);
  s.addText("화재빈도(실측 반영) · 도로협소 · 노후건물 · 고령인구 가중 합산 (도로·노후·고령은 예시)",{x:0.6,y:1.5,w:11.5,h:0.35,fontFace:F,fontSize:12.5,color:C.mute,margin:0});
  s.addChart(p.ChartType.bar, [
    {name:"화재빈도", labels:["마산합포구","진해구","의창구","성산구"], values:[30,29,33,30]},
    {name:"도로협소", labels:["마산합포구","진해구","의창구","성산구"], values:[31,28,14,13]},
    {name:"노후건물", labels:["마산합포구","진해구","의창구","성산구"], values:[24,20,12,13]},
    {name:"고령인구", labels:["마산합포구","진해구","의창구","성산구"], values:[19,18,11,11]},
  ], {x:0.6,y:2.0,w:8.2,h:4.05, barDir:"col", barGrouping:"stacked", chartColors:CAT,
     showValue:false, showLegend:true, legendPos:"b", legendColor:C.body, legendFontFace:F, legendFontSize:11,
     showTitle:false, catAxisLabelColor:C.body, catAxisLabelFontFace:F, catAxisLabelFontSize:11,
     catGridLine:{style:"none"}, catAxisLineColor:C.border2, valAxisHidden:true, valGridLine:{style:"none"}, barGapWidthPct:60});
  card(s,9.15,2.0,3.55,4.05,C.panel2,C.border);
  s.addText("종합 1위",{x:9.4,y:2.22,w:3.1,h:0.35,fontFace:F,fontSize:13,color:C.mute,bold:true,margin:0});
  s.addText("마산합포구",{x:9.4,y:2.58,w:3.1,h:0.55,fontFace:F,fontSize:22,color:C.red,bold:true,margin:0});
  s.addText("104",{x:9.4,y:3.15,w:2.2,h:0.8,fontFace:FM,fontSize:44,color:C.ink,bold:true,margin:0});
  s.addText("점 / 위험지수",{x:9.4,y:3.98,w:3.1,h:0.3,fontFace:F,fontSize:11,color:C.mute,margin:0});
  s.addShape(LINE,{x:9.4,y:4.4,w:3.0,h:0,line:{color:C.border,width:1}});
  s.addText("의창구는 화재건수 최다지만 도로·노후가 낮아 종합은 하위 — 원도심(마산합포·진해)이 상위",{x:9.4,y:4.5,w:3.1,h:1.5,fontFace:F,fontSize:12,color:C.body,margin:0,valign:"top",lineSpacingMultiple:1.25});
}

/* ═══ ⑧ STEP 06 거점 소방서 선정 ═══ */
{
  const s=p.addSlide(); bg(s);
  header(s,"PART 1 · STEP 06","창원 안에서 거점 소방서를 정한다",C.red);
  card(s,0.6,1.75,7.1,4.6);
  riskMap(s,0.85,2.0,6.6,3.85,{stations:[{r:3.4,c:2.6,name:"마산소방서",sel:true},{r:5.6,c:6.4,name:"성산소방서"},{r:2.0,c:8.6,name:"창원소방서"}]});
  s.addText("붉을수록 위험 지수 높음 · ★ 선정 거점",{x:0.85,y:5.9,w:6.6,h:0.3,align:"center",fontFace:F,fontSize:10,color:C.mute,margin:0});
  s.addText("선정 — 마산소방서",{x:8.0,y:1.85,w:4.7,h:0.45,fontFace:F,fontSize:19,color:C.blue,bold:true,margin:0});
  const reasons=[
    ["위험지수 최상위 인접","종합 1위 마산합포구를 최단 거리에서 커버",C.red],
    ["진입불가 경로 최다","빨간선 밀집 원도심 골목을 상공에서 보완",C.orange],
    ["교통약자 밀집","고령 인구 대피 취약지에 초동 대응",C.blue],
    ["보급 거점 확보","드론·UGV 재보급 스마트 방재 거점 병설",C.green],
  ];
  let y=2.45;
  reasons.forEach(([t,d,col])=>{
    flatCard(s,8.0,y,4.7,0.92,C.panel2);
    dot(s,8.25,y+0.33,0.26,col);
    s.addText(t,{x:8.65,y:y+0.12,w:3.9,h:0.35,fontFace:F,fontSize:13,color:C.ink,bold:true,margin:0});
    s.addText(d,{x:8.65,y:y+0.46,w:3.95,h:0.4,fontFace:F,fontSize:10.5,color:C.mute,margin:0});
    y+=1.0;
  });
}

/* ═══ ⑨ PART 2 표지 ═══ */
{
  const s=p.addSlide(); bg(s,C.dark);
  s.addText("PART 2", {x:0.75,y:2.5,w:5,h:0.6,fontFace:FM,fontSize:22,color:C.violet,bold:true,charSpacing:4,margin:0});
  s.addText("도착 후 어떻게 움직이는가", {x:0.72,y:3.1,w:11.5,h:0.9,fontFace:F,fontSize:38,color:C.onDark,bold:true,margin:0});
  s.addText("거점에서 출동한 드론 편대가 화점에 도착한 순간부터 — 표준 행동요령(SOP-D)에 따라 자율 수행한다.",
    {x:0.75,y:4.05,w:11.2,h:0.8,fontFace:F,fontSize:15,color:C.onDarkMute,margin:0,lineSpacingMultiple:1.3});
  const steps=["출동·도착","편대 전개","SOP-D 5단계","유무인 복합"];
  let x=0.75;
  steps.forEach((t,i)=>{
    s.addShape(RR,{x,y:5.15,w:2.7,h:0.7,rectRadius:0.1,fill:{color:"172033"},line:{color:C.border2,width:1}});
    s.addText([{text:`0${i+1}  `,options:{color:C.violet,bold:true,fontFace:FM}},{text:t,options:{color:C.onDark}}],
      {x:x+0.2,y:5.15,w:2.4,h:0.7,valign:"middle",fontFace:F,fontSize:12,bold:true,margin:0});
    if(i<3) s.addText("›",{x:x+2.7,y:5.15,w:0.35,h:0.7,align:"center",valign:"middle",fontFace:F,fontSize:20,color:C.dim,margin:0});
    x+=3.05;
  });
}

/* ═══ ⑩ STEP 01 출동·도착 ═══ */
{
  const s=p.addSlide(); bg(s);
  header(s,"PART 2 · STEP 01","출동 — 소방차보다 먼저 도착한다",C.violet);
  s.addText("거점 소방서 → 화점 직선 비행 · 화재 인지 시점 공통 기준 (예시)",{x:0.6,y:1.5,w:11,h:0.35,fontFace:F,fontSize:13,color:C.mute,margin:0});
  card(s,0.6,2.05,3.85,3.0);
  s.addText("소방차",{x:0.6,y:2.28,w:3.85,h:0.4,align:"center",fontFace:F,fontSize:16,color:C.blue,bold:true,margin:0});
  s.addText("실도로 주행+출동준비",{x:0.6,y:2.68,w:3.85,h:0.32,align:"center",fontFace:F,fontSize:10.5,color:C.mute,margin:0});
  s.addText("8:40",{x:0.6,y:3.05,w:3.85,h:1.0,align:"center",fontFace:FM,fontSize:50,color:C.blue,bold:true,margin:0});
  s.addText("좁은 골목은 입구까지만",{x:0.6,y:4.25,w:3.85,h:0.4,align:"center",fontFace:F,fontSize:11,color:C.red,margin:0});
  card(s,4.65,2.05,3.85,3.0,C.orangeL,"FDBA74");
  s.addText("드론 편대",{x:4.65,y:2.28,w:3.85,h:0.4,align:"center",fontFace:F,fontSize:16,color:C.orange,bold:true,margin:0});
  s.addText("거점→화점 직선 비행",{x:4.65,y:2.68,w:3.85,h:0.32,align:"center",fontFace:F,fontSize:10.5,color:C.amber,margin:0});
  s.addText("3:20",{x:4.65,y:3.05,w:3.85,h:1.0,align:"center",fontFace:FM,fontSize:50,color:C.orange,bold:true,margin:0});
  s.addText("골목 위를 그대로 넘어 도착",{x:4.65,y:4.25,w:3.85,h:0.4,align:"center",fontFace:F,fontSize:11,color:C.amber,margin:0});
  card(s,8.7,2.05,4.0,3.0,C.greenL,"86EFAC");
  s.addText("드론이 먼저",{x:8.7,y:2.35,w:4.0,h:0.4,align:"center",fontFace:F,fontSize:15,color:C.green,bold:true,margin:0});
  s.addText("5:20",{x:8.7,y:2.82,w:4.0,h:1.05,align:"center",fontFace:FM,fontSize:56,color:C.green,bold:true,margin:0});
  s.addText("초동 골든타임 확보",{x:8.7,y:3.92,w:4.0,h:0.4,align:"center",fontFace:F,fontSize:15,color:C.ink,bold:true,margin:0});
  s.addText("소방관 투입 전 정밀 정찰까지",{x:8.7,y:4.4,w:4.0,h:0.4,align:"center",fontFace:F,fontSize:11,color:C.mute,margin:0});
  s.addText("※ 수치는 예시 시나리오 — 거점·지점 거리에 따라 달라진다.",{x:0.6,y:5.35,w:12,h:0.35,fontFace:F,fontSize:10.5,color:C.dim,italic:true,margin:0});
}

/* ═══ ⑪ STEP 02 편대 편성 ═══ */
{
  const s=p.addSlide(); bg(s);
  header(s,"PART 2 · STEP 02","도착 즉시 — 5개 편대로 전개",C.violet);
  const squads=[
    ["GCS","지휘통제","공중지휘권 선언 · 3D 매핑 융합 · 통합 제어·자원 관리","64748B"],
    ["1편대","공중정찰대","사방 3D 스캐닝 · 열화상 화점 탐지 · 연소확대선 모니터링",C.violet],
    ["2편대","인명수색·구조","고립 구조대상자 식별 · 생명유지 키트 투하 · 대피 인도",C.sky],
    ["3편대","화재진압대","창문·진입점 파악 · 창문 파쇄 후 정밀 소화탄 투하",C.blue],
    ["4편대","통신중계·조명","Mesh 통신망 형성 · 음영지역 신호 중계 · 광역 조명",C.amber],
  ];
  let y=1.75; const rh=0.94, rw=12.1;
  squads.forEach(([code,name,task,col])=>{
    flatCard(s,0.6,y,rw,rh,C.panel2);
    s.addShape(RR,{x:0.8,y:y+0.19,w:1.3,h:0.56,rectRadius:0.08,fill:{color:"FFFFFF"},line:{color:col,width:1.5}});
    s.addText(code,{x:0.8,y:y+0.19,w:1.3,h:0.56,align:"center",valign:"middle",fontFace:FM,fontSize:14,color:col,bold:true,margin:0});
    s.addText(name,{x:2.3,y:y,w:3.0,h:rh,valign:"middle",fontFace:F,fontSize:15.5,color:C.ink,bold:true,margin:0});
    s.addText(task,{x:5.35,y:y,w:7.05,h:rh,valign:"middle",fontFace:F,fontSize:12,color:C.body,margin:0,lineSpacingMultiple:1.1});
    y+=rh+0.13;
  });
}

/* ═══ ⑫ STEP 03 SOP-D 5단계 ═══ */
{
  const s=p.addSlide(); bg(s);
  header(s,"PART 2 · STEP 03","SOP-D 표준 행동요령 · 5단계",C.violet);
  const phases=[
    ["전개","DEPLOY","정찰·진압·구조 편대 전개·상승","101-D","6366F1"],
    ["정찰·평가","ASSESS","3D 스캐닝·열화상 화점/진입점 파악","102-D",C.sky],
    ["작전","OPERATE","창문 파쇄 후 정밀 소화탄 · 대피 인도","222-D",C.orange],
    ["중계·호위","RELAY","요구조자 호위 · 외벽 연소차단 · 배터리 릴레이","105-D",C.red],
    ["종결","CLEAR","대피 완료 확인 · 잔불 감시 · RTH","113-D",C.green],
  ];
  const n=5, gap=0.25, cw=(12.1-gap*(n-1))/n, cy=2.0, ch=3.85;
  let x=0.6;
  phases.forEach(([ko,en,d,code,col],i)=>{
    card(s,x,cy,cw,ch);
    s.addShape(OVAL,{x:x+cw/2-0.4,y:cy+0.32,w:0.8,h:0.8,fill:{color:col},line:{type:"none"}});
    s.addText(String(i+1),{x:x+cw/2-0.4,y:cy+0.32,w:0.8,h:0.8,align:"center",valign:"middle",fontFace:FM,fontSize:24,color:"FFFFFF",bold:true,margin:0});
    s.addText(ko,{x:x+0.05,y:cy+1.28,w:cw-0.1,h:0.4,align:"center",fontFace:F,fontSize:14.5,color:col,bold:true,margin:0});
    s.addText(en,{x:x+0.05,y:cy+1.7,w:cw-0.1,h:0.28,align:"center",fontFace:FM,fontSize:9,color:C.dim,bold:true,charSpacing:1,margin:0});
    s.addText(d,{x:x+0.14,y:cy+2.05,w:cw-0.28,h:1.25,align:"center",fontFace:F,fontSize:10.5,color:C.body,margin:0,lineSpacingMultiple:1.18,valign:"top"});
    s.addText(code,{x:x+0.05,y:cy+ch-0.4,w:cw-0.1,h:0.28,align:"center",fontFace:FM,fontSize:10,color:col,bold:true,margin:0});
    if(i<n-1) s.addText("›",{x:x+cw-0.02,y:cy,w:gap+0.04,h:ch,align:"center",valign:"middle",fontFace:F,fontSize:22,color:C.border2,bold:true,margin:0});
    x+=cw+gap;
  });
  s.addText("지휘·정찰·진압·구조·통신 편대가 단계별 SOP 코드에 따라 한 타임라인에서 자율로 맞물려 움직인다.",{x:0.6,y:6.35,w:12.1,h:0.4,align:"center",fontFace:F,fontSize:12,color:C.mute,italic:true,margin:0});
}

/* ═══ ⑬ STEP 04 유무인 복합 (UGV) ═══ */
{
  const s=p.addSlide(); bg(s);
  header(s,"PART 2 · STEP 04","유무인 복합 — 지상 무인차량(UGV) 협업",C.violet);
  const roles=[
    ["지상 무인차량(UGV)","장애물 극복 · 소화수 보급 · 스마트 방재 거점에서 출발·재보급",C.green,C.greenL],
    ["드론 편대","상공에서 정밀 정찰·진압 — 골목 위를 그대로 넘는다",C.violet,C.violetL],
    ["유무인 복합 편대","UGV는 지상 보급·거점, 드론은 공중 타격 — 상호 통신으로 한 편대처럼",C.orange,C.orangeL],
  ];
  let x=0.6; const cw=3.9, gap=0.2, cy=1.9, ch=2.9;
  roles.forEach(([t,d,col,fl])=>{
    card(s,x,cy,cw,ch,C.card,col);
    s.addShape(RR,{x:x+0.28,y:cy+0.3,w:cw-0.56,h:0.55,rectRadius:0.08,fill:{color:fl},line:{type:"none"}});
    s.addText(t,{x:x+0.28,y:cy+0.3,w:cw-0.56,h:0.55,align:"center",valign:"middle",fontFace:F,fontSize:14.5,color:col,bold:true,margin:0});
    s.addText(d,{x:x+0.3,y:cy+1.05,w:cw-0.6,h:1.6,fontFace:F,fontSize:12.5,color:C.body,margin:0,lineSpacingMultiple:1.3,valign:"top"});
    x+=cw+gap;
  });
  flatCard(s,0.6,5.05,12.1,1.3,C.panel2);
  s.addText([{text:"소방차가 진입하기 전, 상공의 드론 편대와 지상의 UGV가 ",options:{color:C.body}},
    {text:"탐지 → 진압 → 대피 인도 → 보급",options:{color:C.orange,bold:true}},
    {text:"을 끊김 없이 이어 초동 대응을 채운다.",options:{color:C.body}}],
    {x:0.9,y:5.05,w:11.5,h:1.3,valign:"middle",fontFace:F,fontSize:14,margin:0,lineSpacingMultiple:1.2});
}

/* ═══ ⑭ 실제 시연 — 지도에 발화점 위치 지정 (자료 삽입용) ═══ */
{
  const s=p.addSlide(); bg(s,C.dark);
  headerDark(s,"실제 시연 · 마산어시장","지도에 발화점 위치 지정",C.violet);
  // 이미지 삽입 자리 (실제 지도 캡처)
  const px=0.6,py=1.7,pw=7.95,ph=4.95;
  s.addShape(RR,{x:px,y:py,w:pw,h:ph,rectRadius:0.09,fill:{color:"0B1220"},line:{color:C.violet,width:1.5,dashType:"dash"}});
  s.addShape(OVAL,{x:px+pw/2-0.45,y:py+ph/2-0.85,w:0.9,h:0.9,fill:{color:"172033"},line:{color:C.violet,width:1.5}});
  s.addShape(OVAL,{x:px+pw/2-0.16,y:py+ph/2-0.56,w:0.32,h:0.32,fill:{color:C.orange},line:{color:"FBBF24",width:2}});
  s.addText("여기에 실제 시뮬레이터 지도 화면을 넣으세요",{x:px+0.5,y:py+ph/2+0.15,w:pw-1.0,h:0.4,align:"center",fontFace:F,fontSize:14,color:C.onDark,bold:true,margin:0});
  s.addText("마산어시장 발화점 지정 · 마산소방서 거점 · 소방차 진입불가 빨간선 · 드론 직선 경로가 보이는 화면",
    {x:px+0.7,y:py+ph/2+0.6,w:pw-1.4,h:0.6,align:"center",fontFace:F,fontSize:11,color:C.onDarkMute,margin:0,lineSpacingMultiple:1.2});
  // 우: 출동 요약 (실측)
  const rx=8.75, rw=3.95;
  s.addShape(RR,{x:rx,y:1.7,w:rw,h:2.95,rectRadius:0.09,fill:{color:"172033"},line:{color:C.border2,width:1}});
  s.addText("출동 요약",{x:rx+0.3,y:1.9,w:rw-0.6,h:0.35,fontFace:F,fontSize:14,color:C.onDark,bold:true,margin:0});
  const rows=[["현장","마산어시장","FB923C"],["최근접 거점","마산소방서 · 직선 1.33km","38BDF8"],["드론 도착","1분 00초","F97316"],["소방차","진입불가 골목 다수 · 호스 연장","FCA5A5"]];
  let yy=2.36;
  rows.forEach(([k,v,col])=>{
    s.addText(k,{x:rx+0.3,y:yy,w:1.5,h:0.3,fontFace:F,fontSize:10.5,color:C.dim,margin:0});
    s.addText(v,{x:rx+1.5,y:yy,w:rw-1.7,h:0.34,fontFace:F,fontSize:11.5,color:col,bold:true,margin:0});
    yy+=0.54;
  });
  s.addShape(RR,{x:rx,y:4.8,w:rw,h:1.85,rectRadius:0.09,fill:{color:"0C1F16"},line:{color:"166534",width:1}});
  s.addText("드론이 먼저 도착",{x:rx+0.3,y:5.0,w:rw-0.6,h:0.4,fontFace:F,fontSize:14,color:"4ADE80",bold:true,margin:0});
  s.addText("소방차가 못 가는 골목을 드론이 상공으로 넘어 1분 만에 화점 도착 — 초동 골든타임 확보.",
    {x:rx+0.3,y:5.42,w:rw-0.6,h:1.1,fontFace:F,fontSize:11.5,color:C.onDarkMute,margin:0,lineSpacingMultiple:1.25,valign:"top"});
  s.addNotes("발표 PC(인터넷 연결)에서 시뮬레이터를 열어 마산어시장 지정 → 지도 화면을 캡처해 이 자리(점선 박스)에 삽입.");
}

/* ═══ ⑮ 실제 시연 — 3D 건물 SOP-D 시뮬레이션 (실제 캡처) ═══ */
{
  const s=p.addSlide(); bg(s,C.dark);
  headerDark(s,"실제 시연 · 마산어시장","3D 건물 SOP-D 시뮬레이션",C.violet);
  s.addImage({ path:"cap_3d_crop.png", x:0.75, y:1.5, w:11.83, h:5.24 });
  s.addText("정찰(열화상 화점 탐지) · 진압(창문 파쇄·정밀 소화탄) · 인명수색구조(대피 인도) · 통신중계·조명 편대가 SOP-D 단계별로 동시에 자율 수행 — 실제 시뮬레이션 화면.",
    {x:0.75,y:6.82,w:11.83,h:0.5,fontFace:F,fontSize:11.5,color:C.onDarkMute,margin:0,lineSpacingMultiple:1.1});
}

/* ═══ ⑯ 기대효과 ① — 골든타임과 화재 피해 (문헌 수치) ═══ */
{
  const s=p.addSlide(); bg(s);
  header(s,"기대효과","소방 골든타임과 화재 피해 — 데이터로 본 근거",C.green);
  s.addText("소방청 국가화재정보시스템 기반 분석 · 골든타임 연구 (현장도착 5분 기준)",{x:0.6,y:1.5,w:11.5,h:0.35,fontFace:F,fontSize:12.5,color:C.mute,margin:0});
  // 차트: 도착시간별 건당 재산피해
  s.addChart(p.ChartType.bar, [{name:"건당 재산피해(천원)", labels:["5분 이내 도착","5~10분 도착"], values:[5425,11198]}],
    {x:0.6,y:2.0,w:5.6,h:3.65, barDir:"col", chartColors:["15803D","DC2626"],
     showValue:true, dataLabelPosition:"outEnd", dataLabelColor:C.ink, dataLabelFontFace:FM, dataLabelFontSize:13, dataLabelFontBold:true, dataLabelFormatCode:"#,##0",
     showLegend:false, showTitle:false, catAxisLabelColor:C.body, catAxisLabelFontFace:F, catAxisLabelFontSize:12, catGridLine:{style:"none"}, catAxisLineColor:C.border2,
     valAxisHidden:true, valGridLine:{style:"none"}, valAxisMaxVal:13000, barGapWidthPct:70});
  s.addText("도착시간별 건당 재산피해 (천원)",{x:0.6,y:5.62,w:5.6,h:0.3,align:"center",fontFace:F,fontSize:10.5,color:C.mute,margin:0});
  // 우: 3 스탯
  const stats=[
    ["재산피해","2.1배 ↑","도착 5분 → 5~10분 (건당 5,425 → 11,198천원)",C.red],
    ["사망률","2.5배 ↑","현장도착 10분 초과 시 (10분 이하 대비)",C.orange],
    ["사망 확률","4배 ↓","5분 이내 골든타임 확보 시",C.green],
  ];
  let y=2.0;
  stats.forEach(([t,v,d,col])=>{
    card(s,6.5,y,6.2,1.15,C.card,C.border);
    dot(s,6.78,y+0.42,0.3,col);
    s.addText(t,{x:7.22,y:y+0.15,w:2.3,h:0.35,fontFace:F,fontSize:13,color:C.mute,bold:true,margin:0});
    s.addText(v,{x:7.22,y:y+0.48,w:2.5,h:0.55,fontFace:F,fontSize:24,color:col,bold:true,margin:0});
    s.addText(d,{x:9.55,y:y,w:2.95,h:1.15,valign:"middle",fontFace:F,fontSize:10.5,color:C.body,margin:0,lineSpacingMultiple:1.15});
    y+=1.27;
  });
  // 하단 결론 배너
  flatCard(s,0.6,6.02,12.1,0.8,"0C1F16","166534");
  s.addText([{text:"우리 시스템 = 골든타임 확보 수단.  ",options:{color:C.green,bold:true}},
    {text:"소방차가 못 가는 골목도 드론이 5분 내 도착 → 문헌 기준 건당 피해 11,198 → 5,425천원(약 52%↓) 구간 유지, 인명 사망 위험 대폭 감소.",options:{color:C.body}}],
    {x:0.9,y:6.02,w:11.5,h:0.8,valign:"middle",fontFace:F,fontSize:12,margin:0,lineSpacingMultiple:1.1});
  s.addText("출처: 소방청 국가화재정보시스템(NFDS) 기반 분석 · 한국방재학회논문집 등 소방 골든타임 연구.",{x:0.6,y:6.92,w:12.1,h:0.3,fontFace:F,fontSize:9.5,color:C.dim,italic:true,margin:0});
  s.addNotes("골든타임(5분) 확보 시 건당 재산피해가 절반 수준(11,198→5,425천원), 10분 초과 시 사망률 약 2.5배. 드론은 진입불가 골목에서도 골든타임을 확보하는 수단.");
}

/* ═══ ⑰ 기대효과 ② — 종합 3측면 · 마무리 ═══ */
{
  const s=p.addSlide(); bg(s,C.dark);
  headerDark(s,"기대효과","기술 · 사회 · 지역, 그리고 마무리",C.green);
  const eff=[
    ["기술·학문","방산-민간 스핀오프 선도","기계공학 제어·역학 + 국방과학 자율 군집 운용의 고가치 융합 사례",C.violet],
    ["사회·안전","원도심 골든타임 확보","진입불가 골목도 5분 내 초동 대응 → 재산피해 약 52%↓·인명 위험 대폭 감소",C.orange],
    ["지역 혁신","경남형 스마트시티·방산","방위산업·항공우주 인프라를 스마트시티에 결합한 지역 특화 혁신",C.sky],
  ];
  let x=0.6; const cw=3.97, gap=0.2, cy=1.9, ch=3.0;
  eff.forEach(([tag,t,d,col])=>{
    s.addShape(RR,{x,y:cy,w:cw,h:ch,rectRadius:0.09,fill:{color:"172033"},line:{color:C.border2,width:1}});
    chip(s,x+0.28,cy+0.3,1.6,tag,col,"0B1220");
    s.addText(t,{x:x+0.28,y:cy+0.95,w:cw-0.56,h:0.85,fontFace:F,fontSize:16,color:C.onDark,bold:true,margin:0,valign:"top",lineSpacingMultiple:1.05});
    s.addText(d,{x:x+0.28,y:cy+1.85,w:cw-0.56,h:1.0,fontFace:F,fontSize:11.5,color:C.onDarkMute,margin:0,lineSpacingMultiple:1.25,valign:"top"});
    x+=cw+gap;
  });
  s.addShape(RR,{x:0.6,y:5.2,w:12.1,h:1.55,rectRadius:0.1,fill:{color:"1F1206"},line:{color:C.orange,width:1.3}});
  s.addText("데이터로 창원·거점을 정하고, 편대가 골든타임을 먼저 지킨다",{x:0.9,y:5.42,w:11.5,h:0.5,fontFace:F,fontSize:19,color:C.orange,bold:true,margin:0});
  s.addText("최근 1년 화재 빅데이터 → 창원·거점 소방서 선정 → SOP-D 현장 대응 → UGV 유무인 복합. 팀 군체 · 감사합니다. (Q&A)",
    {x:0.9,y:6.02,w:11.5,h:0.5,fontFace:F,fontSize:13,color:C.onDarkMute,margin:0});
}

const OUT=process.argv[2]||"deck3.pptx";
p.writeFile({fileName:OUT}).then(f=>console.log("saved",f));
