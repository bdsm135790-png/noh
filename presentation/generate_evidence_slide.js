const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE";
p.title = "실증 근거";
const RR=p.ShapeType.roundRect, F="Malgun Gothic";
const C={ page:"FFFFFF", panel2:"F8FAFC", border:"E2E8F0",
  ink:"0F172A", body:"334155", mute:"64748B", dim:"94A3B8",
  red:"DC2626", orange:"EA580C", blue:"2563EB", green:"15803D", violet:"7C3AED" };

function chip(s,x,y,w,text,color){
  s.addShape(RR,{x,y,w,h:0.32,rectRadius:0.16,fill:{color:"F8FAFC"},line:{color,width:1}});
  s.addText(text,{x,y,w,h:0.32,align:"center",valign:"middle",fontFace:F,fontSize:9,color,bold:true,margin:0});
}
{
  const s=p.addSlide(); s.background={color:C.page};
  s.addText("실현 가능성 · 이미 되는 기술",{x:0.6,y:0.42,w:12.1,h:0.3,fontFace:F,fontSize:12.5,color:C.red,bold:true,charSpacing:3,margin:0});
  s.addText("실증 근거 — 시뮬레이션이 아니라, 현실에서 검증 중",{x:0.6,y:0.72,w:12.1,h:0.7,fontFace:F,fontSize:26,color:C.ink,bold:true,margin:0});
  s.addText("우리 시뮬레이션의 요소는 국내에서 이미 실운용·실증되고 있다.",{x:0.6,y:1.5,w:12,h:0.35,fontFace:F,fontSize:12.5,color:C.mute,margin:0});

  // 좌: 우리 요소 → 실제 (4행)
  const rows=[
    ["군집 자율 편대","산림청 군집드론 산불 실증 — 감시·분석·진화 편대","실증 ’26",C.violet],
    ["드론 화재 진압(방수)","소방청 고중량 드론 고층건물 화재 방수 실증","실증 ’25",C.blue],
    ["정찰·대피유도·투하","소방청 드론 실운용 — 열화상·투하장치·확성기","실운용",C.green],
    ["정밀 소화탄","소화탄 진압 드론 특허 · 자동소화드론 논문","특허·논문",C.orange],
  ];
  const rw=7.5, rh=0.86; let y=1.95;
  rows.forEach(([t,d,tag,col])=>{
    s.addShape(RR,{x:0.6,y,w:rw,h:rh,rectRadius:0.08,fill:{color:C.panel2},line:{color:C.border,width:1}});
    s.addText([{text:"우리 → ",options:{color:C.dim,bold:true}},{text:t,options:{color:col,bold:true}}],
      {x:0.85,y:y+0.11,w:4.5,h:0.34,fontFace:F,fontSize:13,margin:0,valign:"middle"});
    chip(s,0.6+rw-1.3,y+0.14,1.12,tag,col);
    s.addText(d,{x:0.85,y:y+0.46,w:rw-0.5,h:0.32,fontFace:F,fontSize:11,color:C.body,margin:0,valign:"middle"});
    y+=rh+0.1;
  });

  // 우: 언론 보도 패널
  const nx=8.3, nw=4.42, ny=1.95, nh=4*0.86+3*0.1;  // 좌측 높이와 맞춤
  s.addShape(RR,{x:nx,y:ny,w:nw,h:nh,rectRadius:0.09,fill:{color:C.page},line:{color:C.border,width:1},
    shadow:{type:"outer",color:"334155",opacity:0.12,blur:6,offset:2,angle:90}});
  s.addText("■ 언론 보도",{x:nx+0.28,y:ny+0.2,w:nw-0.56,h:0.34,fontFace:F,fontSize:13.5,color:C.red,bold:true,margin:0});
  const news=[
    ["「고층건물 화재, 드론으로 잡는다」","YTN · 2026.08 (소방청 방수 실증)"],
    ["「산불 30분 골든타임, 드론이 메운다」","SBS · 2026.07 (산림청 군집드론)"],
    ["「하늘 나는 공중 소방드론 떴다」","경향신문 · 2017 (서울소방 고층화재 투입)"],
  ];
  let ny2=ny+0.72;
  news.forEach(([h,src])=>{
    s.addShape(RR,{x:nx+0.24,y:ny2,w:nw-0.48,h:1.0,rectRadius:0.06,fill:{color:C.panel2},line:{color:C.border,width:1}});
    s.addText(h,{x:nx+0.42,y:ny2+0.14,w:nw-0.84,h:0.5,fontFace:F,fontSize:11.5,color:C.ink,bold:true,margin:0,valign:"top",lineSpacingMultiple:1.05});
    s.addText(src,{x:nx+0.42,y:ny2+0.64,w:nw-0.84,h:0.3,fontFace:F,fontSize:9.5,color:C.mute,margin:0});
    ny2+=1.1;
  });

  // 하단: 우리의 확장
  s.addShape(RR,{x:0.6,y:5.7,w:12.13,h:1.0,rectRadius:0.1,fill:{color:"1F1206"},line:{color:C.orange,width:1.2}});
  s.addText([{text:"우리의 확장 — ",options:{color:"FB923C",bold:true}},
    {text:"산불이 아닌 도심 원도심 골목(진입불가) + 지상 UGV 유무인 복합 + SOP-D. ",options:{color:"E2E8F0"}},
    {text:"(군집·소화탄 자율은 실증 단계, 그 위에 도심 특화를 얹는다.)",options:{color:"94A3B8"}}],
    {x:0.9,y:5.7,w:11.5,h:1.0,valign:"middle",fontFace:F,fontSize:13,margin:0,lineSpacingMultiple:1.2});
  s.addText("정찰·실시간 영상·물자전달은 실전 투입, 진압·군집은 실증 단계(2025~26). 출처: YTN·SBS·경향·이데일리 보도, 특허 KR101741578B1.",
    {x:0.6,y:6.8,w:12.13,h:0.3,fontFace:F,fontSize:9,color:C.dim,italic:true,margin:0});
}
p.writeFile({ fileName: process.argv[2] || "evidence.pptx" }).then(f=>console.log("saved",f));
