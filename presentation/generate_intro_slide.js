const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE";
p.title = "문제 인식 - 문제 제기";
const RR=p.ShapeType.roundRect, F="Malgun Gothic", FM="Consolas";
const C={ dark:"0F172A", onDark:"E2E8F0", mute:"94A3B8", dim:"64748B",
  red:"DC2626", red2:"F87171", orange:"F97316", amber:"FBBF24", card:"172033" };

function chip(s,x,y,w,text,color){
  s.addShape(RR,{x,y,w,h:0.4,rectRadius:0.2,fill:{color:"0B1220"},line:{color,width:1}});
  s.addText(text,{x,y,w,h:0.4,align:"center",valign:"middle",fontFace:F,fontSize:11,color,bold:true,margin:0});
}

{
  const s=p.addSlide(); s.background={color:C.dark};
  s.addText("문제 인식 · WHY",{x:0.6,y:0.48,w:11,h:0.32,fontFace:F,fontSize:12.5,color:C.red,bold:true,charSpacing:3,margin:0});
  s.addText("소방차가 닿지 못하는 곳에서, 사람이 죽는다",{x:0.6,y:0.8,w:12.1,h:0.7,fontFace:F,fontSize:27,color:C.onDark,bold:true,margin:0});

  /* 좌: 항공사진(주인공) 자리 */
  const px=0.6,py=1.62,pw=7.0,ph=4.35;
  s.addShape(RR,{x:px,y:py,w:pw,h:ph,rectRadius:0.09,fill:{color:"0B1220"},line:{color:C.red,width:1.5,dashType:"dash"}});
  s.addText("자산동 노후 다세대 밀집 항공사진(스카이뷰) 삽입",{x:px+0.5,y:py+ph/2-0.28,w:pw-1,h:0.4,align:"center",fontFace:F,fontSize:13,color:C.mute,bold:true,margin:0});
  s.addText("마산합포구 자산동 노후 다세대(빌라) 밀집지",{x:px,y:py+ph+0.08,w:pw,h:0.3,fontFace:F,fontSize:12,color:C.onDark,bold:true,margin:0});
  s.addText("폭 4m 미만 골목 밀집 → 소방차 진입 곤란   ·   출처: 카카오맵 스카이뷰",{x:px,y:py+ph+0.38,w:pw,h:0.28,fontFace:F,fontSize:9.5,color:C.dim,margin:0});

  /* 우: 사례 카드 + 보도 컷 + 골든타임 */
  const rx=7.85, rw=4.88;
  // 사례 카드
  s.addShape(RR,{x:rx,y:1.62,w:rw,h:1.72,rectRadius:0.1,fill:{color:C.card},line:{color:C.orange,width:1.3}});
  chip(s,rx+0.26,1.8,2.7,"노후 주거·고령 인명 위험",C.orange);
  s.addText("마산합포 자산동 노후 빌라 새벽 화재",{x:rx+0.28,y:2.34,w:rw-0.56,h:0.4,fontFace:F,fontSize:14,color:C.onDark,bold:true,margin:0});
  s.addText("2층 발화 → 90대 사망 · 50대 중상 · 주민 18명 대피",{x:rx+0.28,y:2.76,w:rw-0.56,h:0.5,fontFace:F,fontSize:11.5,color:C.mute,margin:0,lineSpacingMultiple:1.2,valign:"top"});
  // 보도 컷 자리(작게)
  const ny=3.5, nh=1.5;
  s.addShape(RR,{x:rx,y:ny,w:rw,h:nh,rectRadius:0.1,fill:{color:"0B1220"},line:{color:"334155",width:1,dashType:"dash"}});
  s.addText("관련 보도 이미지(작게) 삽입",{x:rx+0.3,y:ny+nh/2-0.28,w:rw-0.6,h:0.35,align:"center",fontFace:F,fontSize:11.5,color:C.mute,bold:true,margin:0});
  s.addText("자산동 빌라 화재 보도 · 출처: 언론",{x:rx+0.3,y:ny+nh/2+0.06,w:rw-0.6,h:0.3,align:"center",fontFace:F,fontSize:9.5,color:C.dim,margin:0});
  // 골든타임 스탯
  s.addShape(RR,{x:rx,y:5.18,w:rw,h:0.8,rectRadius:0.1,fill:{color:"1A0E06"},line:{color:C.amber,width:1.2}});
  s.addText([{text:"골든타임  ",options:{color:C.amber,bold:true}},{text:"5분 초과 시 피해 2.1배 · 10분 초과 사망률 2.5배",options:{color:C.mute}}],
    {x:rx+0.28,y:5.18,w:rw-0.56,h:0.8,valign:"middle",fontFace:F,fontSize:10.5,margin:0,lineSpacingMultiple:1.15});

  s.addText("출처: 소방청 국가화재정보시스템(NFDS)·골든타임 연구 / 창원 마산합포 빌라 화재 사례는 언론 보도.",
    {x:0.6,y:6.75,w:12.1,h:0.3,fontFace:F,fontSize:9,color:C.dim,italic:true,margin:0});
  s.addNotes("깔끔 버전: 좌측 항공사진을 주인공으로 크게, 우측은 사례 카드 + 작은 보도 컷 + 골든타임. 사진 두 장이 겹치지 않게 정리.");
}

p.writeFile({ fileName: process.argv[2] || "intro.pptx" }).then(f=>console.log("saved", f));
