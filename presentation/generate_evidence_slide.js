const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE";
p.title = "실증 근거";
const RR=p.ShapeType.roundRect, LINE=p.ShapeType.line, F="Malgun Gothic";
const C={ page:"FFFFFF", card:"FFFFFF", panel2:"F8FAFC", border:"E2E8F0",
  ink:"0F172A", body:"334155", mute:"64748B", dim:"94A3B8",
  red:"DC2626", orange:"EA580C", blue:"2563EB", green:"15803D", violet:"7C3AED" };

function chip(s,x,y,w,text,color){
  s.addShape(RR,{x,y,w,h:0.34,rectRadius:0.17,fill:{color:"F8FAFC"},line:{color,width:1}});
  s.addText(text,{x,y,w,h:0.34,align:"center",valign:"middle",fontFace:F,fontSize:9.5,color,bold:true,margin:0});
}
{
  const s=p.addSlide(); s.background={color:C.page};
  s.addText("실현 가능성 · 이미 되는 기술",{x:0.6,y:0.42,w:12.1,h:0.3,fontFace:F,fontSize:12.5,color:C.red,bold:true,charSpacing:3,margin:0});
  s.addText("실증 근거 — 시뮬레이션이 아니라, 현실에서 검증 중",{x:0.6,y:0.72,w:12.1,h:0.7,fontFace:F,fontSize:26,color:C.ink,bold:true,margin:0});
  s.addText("우리 시뮬레이션의 요소는 국내에서 이미 실운용·실증되고 있다.",{x:0.6,y:1.5,w:12,h:0.35,fontFace:F,fontSize:12.5,color:C.mute,margin:0});

  const cards=[
    ["군집 자율 편대 (정찰→분석→진압)","산림청 군집드론 운용 실증 — 감시·분석·진화 편대로\n'헬기 도착 전 30분 골든타임'을 메운다","실증 ’26",C.violet],
    ["드론 화재 진압 (방수)","소방청 고중량 드론으로 고층건물 화재\n방수 진압 기술 현장 실증 완료","실증 ’25",C.blue],
    ["정찰 · 대피유도 · 투하","소방청 드론 실운용 — 열화상 정찰 · 확성기 ·\n투하장치로 대피 유도·물자 전달","실운용",C.green],
    ["정밀 소화탄","소화탄 화재진압 드론 특허(KR101741578B1) ·\n자동소화드론 운용 논문(KAIS·KCI)","특허·논문",C.orange],
  ];
  const cw=6.0, gap=0.15, ch=1.72;
  cards.forEach(([t,d,tag,col],i)=>{
    const x=0.6+(i%2)*(cw+gap), y=1.95+Math.floor(i/2)*(ch+0.14);
    s.addShape(RR,{x,y,w:cw,h:ch,rectRadius:0.09,fill:{color:C.card},line:{color:C.border,width:1},
      shadow:{type:"outer",color:"334155",opacity:0.12,blur:6,offset:2,angle:90}});
    s.addText([{text:"우리 → ",options:{color:C.dim,bold:true}},{text:t,options:{color:col,bold:true}}],
      {x:x+0.28,y:y+0.2,w:cw-1.55,h:0.4,fontFace:F,fontSize:13.5,margin:0,valign:"top"});
    chip(s,x+cw-1.35,y+0.2,1.1,tag,col);
    s.addText(d,{x:x+0.28,y:y+0.66,w:cw-0.56,h:0.95,fontFace:F,fontSize:11.5,color:C.body,margin:0,lineSpacingMultiple:1.25,valign:"top"});
  });

  s.addShape(RR,{x:0.6,y:5.75,w:12.1,h:1.02,rectRadius:0.1,fill:{color:"1F1206"},line:{color:C.orange,width:1.2}});
  s.addText([{text:"우리의 확장 — ",options:{color:"FB923C",bold:true}},
    {text:"산불이 아닌 도심 원도심 골목(진입불가) + 지상 UGV 유무인 복합 + SOP-D. ",options:{color:"E2E8F0"}},
    {text:"(군집·소화탄 자율은 실증 단계, 그 위에 도심 특화를 얹는다.)",options:{color:"94A3B8"}}],
    {x:0.9,y:5.75,w:11.5,h:1.02,valign:"middle",fontFace:F,fontSize:13,margin:0,lineSpacingMultiple:1.2});
  s.addText("출처: 산림청·소방청 보도(2025~2026), 특허 KR101741578B1, KAIS·KCI 소방드론 연구.",{x:0.6,y:6.86,w:12.1,h:0.3,fontFace:F,fontSize:9,color:C.dim,italic:true,margin:0});
}
p.writeFile({ fileName: process.argv[2] || "evidence.pptx" }).then(f=>console.log("saved",f));
