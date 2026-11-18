function drawDiscBand(doc,M,UW,y,disc,area,dono){
  const has=(dOk(disc));
  const bg=has?ESP_BG[disc]:[235,235,235];
  const fg=has?ESP_FG[disc]:[120,120,120];
  doc.setFillColor(bg[0],bg[1],bg[2]);doc.rect(M,y,UW,7,"F");doc.setTextColor(fg[0],fg[1],fg[2]);doc.setFont("helvetica","bold");doc.setFontSize(9.5);
  doc.text(has?DISC[disc]:"ESPECIALIDADE A DEFINIR",M+3,y+4.8);
  doc.text(String((area||"ÁREA A DEFINIR")+(ccDe(area)?"  ·  CC "+ccDe(area):"")+(dono?"  ·  DONO: "+dono:"")).toUpperCase(),M+UW-3,y+4.8,{align:"right"});
  return 10;
}
function pdfKit(J,title,id){
  const doc=new J.jsPDF({unit:"mm",format:"a4"});
  const M=12,W=210,UW=W-2*M,BOT=278;
  const G=[196,98,8],GR=[190,194,200],INK=[31,36,48],MUT=[107,114,128],LG=[247,244,238];
  const U=s=>String(s??"").toUpperCase();
  const k={doc,M,W,UW,BOT,G,GR,INK,MUT,LG,U,y:M};
  k.col=c=>doc.setTextColor(c[0],c[1],c[2]);k.fill=c=>doc.setFillColor(c[0],c[1],c[2]);
  k.header=()=>{const first=doc.getNumberOfPages()===1;k.y+=gHeader(doc,M,W,UW,k.y,title,U(id),first);k.col(INK);};
  k.ensure=h=>{if(k.y+h>BOT){doc.addPage();k.y=M;k.header();}};
  k.bar=t=>{k.ensure(20);gBar(doc,M,UW,k.y,U(t));k.y+=9;};
  k.para=(t,o={})=>{doc.setFont("helvetica",o.b?"bold":"normal");doc.setFontSize(o.s||9.5);k.col(o.c||INK);doc.splitTextToSize(U(t||"—"),UW).forEach(l=>{k.ensure(5);doc.text(l,M,k.y+3.2);k.y+=4.4;});k.y+=1.5;};
  k.kv=(rows,cols)=>{const cw=UW/cols;let i=0;while(i<rows.length){k.ensure(11);for(let c=0;c<cols&&i<rows.length;c++,i++){const x=M+c*cw;doc.setFont("helvetica","bold");doc.setFontSize(7.5);k.col(MUT);doc.text(U(rows[i][0]),x,k.y+2.5);doc.setFont("helvetica","normal");doc.setFontSize(9.5);k.col(INK);doc.text(doc.splitTextToSize(U(rows[i][1]||"—"),cw-4)[0],x,k.y+7);}k.y+=10.5;}};
  k.sign=labels=>{k.ensure(34);k.y+=10;labels.forEach((t,i)=>{const w=UW/labels.length,x=M+i*w+3;doc.setDrawColor(90,90,90);doc.line(x,k.y,x+w-9,k.y);doc.setFont("helvetica","normal");doc.setFontSize(8);k.col(MUT);doc.text(U(t),x,k.y+4);doc.text("DATA: ___/___/______",x,k.y+9);});k.y+=14;};
  k.fotos=fotos=>{if(!fotos||!fotos.length)return;doc.addPage();k.y=M;k.header();k.bar("FOTOS / ANEXOS ("+fotos.length+")");const cw=(UW-6)/2;let c2=0,rowH=0;
    fotos.forEach(p=>{const r=p.h/p.w;let iw=cw,ih=iw*r;if(ih>78){ih=78;iw=ih/r;}const ll=doc.splitTextToSize(U(p.leg||""),cw).slice(0,6);const need=ih+9+ll.length*3.8+3;if(c2===0)k.ensure(need);else if(k.y+Math.max(rowH,need)>BOT){doc.addPage();k.y=M;k.header();c2=0;}
      const x=M+c2*(cw+6);try{doc.addImage(p.data,"JPEG",x,k.y,iw,ih);}catch(e){}doc.setFont("helvetica","bold");doc.setFontSize(8);k.col(G);doc.text(U(p.cat),x,k.y+ih+4);doc.setFont("helvetica","normal");k.col(INK);doc.text(ll,x,k.y+ih+8);
      rowH=Math.max(rowH,need);if(c2===1){k.y+=rowH;rowH=0;c2=0;}else c2=1;});};
  k.footer=()=>{const n=doc.getNumberOfPages();for(let i=1;i<=n;i++){doc.setPage(i);gFooter(doc,M,W,n);doc.setFont("helvetica","normal");doc.setFontSize(7.5);k.col(MUT);doc.text("GERADO EM "+new Date().toLocaleDateString("pt-BR")+" · "+U(id),M,291);doc.text("PÁG. "+i+"/"+n,W-M,291,{align:"right"});}};
  k.header();return k;
}
const siglaDe=d=>[d.linha||"—",PROG[d.tipo].sg,d.tipo===0?(d.semana?"S"+d.semana:"—"):MESES[d.mes]||"—",d.ano||"—"].join("-");
function buildPdfCm(c,fotos,J,fmt){
  const k=pdfKit(J,"COMPRA DE MATERIAL - CM",c.id),doc=k.doc,U=k.U,M=k.M,UW=k.UW;
  k.kv([["SIGLA DA PROGRAMAÇÃO",siglaDe(c)],["CM",c.id],["PROGRAMAÇÃO",PROG[c.tipo].nome],["STATUS",CM_ST[c.status]]],2);
  if(c.sdcv&&c.sdcv.num)k.kv([["Nº DA SDCV",c.sdcv.num],["DATA DA SDCV",fmt(c.sdcv.data)],["RESPONSÁVEL",c.sdcv.resp]],3);
  k.bar("ITENS");
  const cx=[M,M+8,M+30,M+54,M+114,M+123,M+134,M+158],cw=[8,22,24,60,9,11,24,28];
  const th=()=>{k.fill(k.LG);doc.rect(M,k.y,UW,6,"F");doc.setFont("helvetica","bold");doc.setFontSize(8);k.col(k.INK);["#","SS","ITEM","DESCRIÇÃO","UN","QTD","ÁREA","DISC."].forEach((h,i)=>doc.text(h,cx[i]+1,k.y+4.1));k.y+=7;};
  th();
  c.itens.forEach((it,i)=>{doc.setFont("helvetica","normal");doc.setFontSize(8.5);const d=doc.splitTextToSize(U((it.desc||"—")+(it.equip||it.modelo?" | EQUIP.: "+(it.equip||"—")+(it.modelo?" · MODELO: "+it.modelo:""):"")),cw[3]-2);const h=Math.max(d.length,1)*4+2.5;
    if(k.y+h>k.BOT){doc.addPage();k.y=M;k.header();th();}
    k.col(k.INK);doc.text(String(i+1),cx[0]+1,k.y+3.6);doc.text(U(it.ss||"—"),cx[1]+1,k.y+3.6);doc.text(U(it.item||"—"),cx[2]+1,k.y+3.6);doc.text(d,cx[3]+1,k.y+3.6);doc.text(U(it.un||""),cx[4]+1,k.y+3.6);doc.text(U(it.qtd||""),cx[5]+1,k.y+3.6);doc.text(U(it.area||"A DEFINIR"),cx[6]+1,k.y+3.6);
    const dd=it.disc;if(dOk(dd)){const bg=ESP_BG[dd],fg=ESP_FG[dd];doc.setFillColor(bg[0],bg[1],bg[2]);doc.rect(cx[7],k.y,cw[7],5.2,"F");doc.setTextColor(fg[0],fg[1],fg[2]);doc.setFont("helvetica","bold");doc.text(DISC[dd],cx[7]+1.5,k.y+3.7);}else{k.col(k.MUT);doc.text("A DEFINIR",cx[7]+1,k.y+3.6);}
    doc.setDrawColor(225,229,226);doc.line(M,k.y+h-0.5,M+UW,k.y+h-0.5);k.y+=h;});
  k.y+=3;
  const as=[...new Set(c.itens.map(i=>i.area).filter(Boolean))];
  if(as.length){k.bar("ÁREAS E DONOS");as.forEach(a=>k.para("• "+a+": "+(donoDe(a)||"DONO NÃO CADASTRADO"),{s:9}));}
  k.bar("OBSERVAÇÃO");k.para(c.obs||"—");
  if(c._just){k.bar("JUSTIFICATIVA DE COMPRA");c._just.split("\n").forEach((l,i)=>{if(!l.trim()){k.y+=1.5;return;}const hd=/^\d\. /.test(l);k.para(l,{s:hd||!i?10:9,b:hd||!i,c:hd?k.G:k.INK});});}
  {const a=c.aprovacao||{};k.bar("APROVAÇÃO DO SUPERVISOR");k.para(a.status?a.status+" POR "+a.por+" (MAT. "+a.matricula+") EM "+String(a.em||"").slice(0,10).split("-").reverse().join("/")+(a.obs?" - "+a.obs:""):"AGUARDANDO APROVAÇÃO DO SUPERVISOR",{s:10,b:true,c:a.status==="APROVADA"?k.G:[168,90,5]});}
  k.bar("HISTÓRICO");c.hist.forEach(h=>k.para("• "+h[0]+" - "+fmt(h[1])+" - "+h[2],{s:8.5}));
  k.sign(["SOLICITANTE","APROVAÇÃO","COMPRAS"]);k.fotos(fotos);k.footer();return doc;
}
function buildPdfCe(e,fotos,J,fmt){
  const k=pdfKit(J,"CONSERTO EXTERNO - CE",e.id),U=k.U;
  k.y+=drawDiscBand(k.doc,k.M,k.UW,k.y,e.disc,e.area,donoDe(e.area));
  const valor=e.valor?"R$ "+(+e.valor).toLocaleString("pt-BR",{minimumFractionDigits:2}):"—";
  k.kv([["SS",e.ss],[e.ficha?"FICHA":"PROGRAMAÇÃO",siglaCe(e).replace("FICHA ","")],["ITEM",e.item],["FORNECEDOR",e.fornecedor],["STATUS",CE_ST[e.status]],["VALOR ORÇADO",valor]],2);
  if(e.sdcv&&e.sdcv.num)k.kv([["Nº DA SDCV",e.sdcv.num],["DATA DA SDCV",fmt(e.sdcv.data)],["RESPONSÁVEL",e.sdcv.resp]],3);
  k.bar("DESCRIÇÃO DO ITEM");k.para(e.desc,{b:1});
  k.bar("DEFEITO / SERVIÇO A EXECUTAR");k.para(e.defeito);
  k.bar("REMESSA E RETORNO");
  k.kv([["NF DE ENVIO",e.nfEnvio],["DATA DE ENVIO",fmt(e.dtEnvio)],["PREVISÃO DE RETORNO",fmt(e.dtPrev)],["NF DE RETORNO",e.nfRetorno],["DATA DE RETORNO",fmt(e.dtRet)]],2);
  k.bar("OBSERVAÇÃO");k.para(e.obs||"—");
  k.bar("HISTÓRICO");e.hist.forEach(h=>k.para("• "+h[0]+" - "+fmt(h[1])+" - "+h[2],{s:8.5}));
  k.sign(["SOLICITANTE","PORTARIA / EXPEDIÇÃO","RECEBIMENTO"]);k.fotos(fotos);k.footer();return k.doc;
}
