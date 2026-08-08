const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE";
p.title = "종합 위험 지수 + 거점 선정";

const RR=p.ShapeType.roundRect, RECT=p.ShapeType.rect, OVAL=p.ShapeType.ellipse, LINE=p.ShapeType.line;
const F="Malgun Gothic", FM="Consolas";
const C = {
  page:"FFFFFF", card:"FFFFFF", panel2:"F8FAFC", border:"E2E8F0", border2:"CBD5E1",
  ink:"0F172A", body:"334155", mute:"64748B", dim:"94A3B8",
  red:"DC2626", orange:"EA580C", blue:"2563EB", green:"15803D",
};
const CAT = ["2563EB","EA580C","7C3AED","15803D"];

function header(s, kicker, title, kColor){
  s.addText(kicker.toUpperCase(), {x:0.6,y:0.42,w:12.1,h:0.3,fontFace:F,fontSize:12.5,color:kColor,bold:true,charSpacing:3,margin:0});
  s.addText(title, {x:0.6,y:0.72,w:12.1,h:0.72,fontFace:F,fontSize:27,color:C.ink,bold:true,margin:0});
}
function card(s,x,y,w,h,fill,border){
  s.addShape(RR,{x,y,w,h,rectRadius:0.09,fill:{color:fill||C.card},line:{color:border||C.border,width:1},
    shadow:{type:"outer",color:"334155",opacity:0.12,blur:6,offset:2,angle:90}});
}

{
  const s=p.addSlide(); s.background={color:C.page};
  header(s,"PART 1 · STEP 04","종합 위험 지수로 거점 소방서를 정한다",C.red);
  s.addText("화재 발생(실측 반영) · 도로협소 · 노후건물 · 고령인구를 가중 합산 (도로·노후·고령은 예시)",
    {x:0.6,y:1.5,w:11.5,h:0.35,fontFace:F,fontSize:12.5,color:C.mute,margin:0});
  // 누적 막대 차트
  s.addChart(p.ChartType.bar, [
    {name:"화재 발생", labels:["마산합포구","진해구","의창구","성산구"], values:[30,29,33,30]},
    {name:"도로협소", labels:["마산합포구","진해구","의창구","성산구"], values:[31,28,14,13]},
    {name:"노후건물", labels:["마산합포구","진해구","의창구","성산구"], values:[24,20,12,13]},
    {name:"고령인구", labels:["마산합포구","진해구","의창구","성산구"], values:[19,18,11,11]},
  ], {x:0.6,y:2.0,w:8.3,h:4.05, barDir:"col", barGrouping:"stacked", chartColors:CAT,
     showValue:false, showLegend:true, legendPos:"b", legendColor:C.body, legendFontFace:F, legendFontSize:11,
     showTitle:false, catAxisLabelColor:C.body, catAxisLabelFontFace:F, catAxisLabelFontSize:11,
     catGridLine:{style:"none"}, catAxisLineColor:C.border2, valAxisHidden:true, valGridLine:{style:"none"}, barGapWidthPct:60});
  s.addText("의창구는 화재건수 최다지만 도로·노후·고령이 낮아 종합은 하위 — 원도심(마산합포·진해)이 상위.",
    {x:0.6,y:6.12,w:8.3,h:0.35,fontFace:F,fontSize:10.5,color:C.dim,italic:true,margin:0});
  // 우: 종합 1위 + 거점 결론
  const rx=9.15, rw=3.55;
  card(s, rx, 2.0, rw, 1.78, C.panel2, C.border);
  s.addText("종합 위험 1위",{x:rx+0.28,y:2.2,w:rw-0.56,h:0.32,fontFace:F,fontSize:12.5,color:C.mute,bold:true,margin:0});
  s.addText("마산합포구",{x:rx+0.28,y:2.5,w:rw-0.56,h:0.5,fontFace:F,fontSize:21,color:C.red,bold:true,margin:0});
  s.addText([{text:"104",options:{fontFace:FM,fontSize:38,color:C.ink,bold:true}},{text:" 점 / 위험지수",options:{fontFace:F,fontSize:12,color:C.mute}}],
    {x:rx+0.28,y:3.02,w:rw-0.56,h:0.62,valign:"middle",margin:0});
  // 거점 결론 배지 카드
  card(s, rx, 3.95, rw, 2.1, "F0FDF4", "16A34A");
  s.addShape(RR,{x:rx+0.28,y:4.16,w:1.9,h:0.4,rectRadius:0.2,fill:{color:"FFFFFF"},line:{color:C.green,width:1}});
  s.addText("드론 거점 선정",{x:rx+0.28,y:4.16,w:1.9,h:0.4,align:"center",valign:"middle",fontFace:F,fontSize:11,color:C.green,bold:true,margin:0});
  s.addText("마산소방서",{x:rx+0.28,y:4.62,w:rw-0.56,h:0.55,fontFace:F,fontSize:24,color:C.blue,bold:true,margin:0});
  s.addText("종합 위험 최상위 원도심(마산합포·진해)을 최단 거리로 관할 → 소방 드론 배치 거점으로 선정",
    {x:rx+0.28,y:5.2,w:rw-0.56,h:0.78,fontFace:F,fontSize:11.5,color:C.body,margin:0,lineSpacingMultiple:1.25,valign:"top"});
  s.addNotes("종합 위험 지수(피해·도로·노후·고령) 1위 = 마산합포구 → 관할 마산소방서를 드론 거점으로 선정. (거점 단독 슬라이드를 이 한 장으로 통합)");
}

p.writeFile({ fileName: process.argv[2] || "one.pptx" }).then(f=>console.log("saved", f));
