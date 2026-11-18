function buildPdf(f, fotos, ferr, tipos, classif, epiTexto, J){
  const doc=new J.jsPDF({unit:"mm",format:"a4"});
  const M=12,W=210,UW=W-2*M,BOT=284;
  const G=[196,98,8],LG=[247,244,238],Y=[253,236,214],GR=[190,194,200],INK=[31,36,48],MUT=[107,114,128];
  let y=M;
  const col=(c)=>doc.setTextColor(c[0],c[1],c[2]);
  const fill=(c)=>doc.setFillColor(c[0],c[1],c[2]);
  const ensure=(h)=>{if(y+h>BOT){doc.addPage();y=M;header(false);}};
  const header=(first)=>{y+=gHeader(doc,M,W,UW,y,"FICHA TÉCNICA DE SERVIÇO - FTS",f.id,first);col(INK);};
  const bar=(t,c)=>{ensure(20);gBar(doc,M,UW,y,t);y+=9;};
  const para=(t,o={})=>{
    doc.setFont("helvetica",o.b?"bold":"normal");doc.setFontSize(o.s||9.5);col(o.c||INK);
    const lines=doc.splitTextToSize(String(t||"—"),(o.w||UW)-(o.ind||0));
    const lh=(o.s||9.5)*0.44;
    lines.forEach(l=>{ensure(lh+1);doc.text(l,(o.x||M)+(o.ind||0),y+3.2);y+=lh+0.9;});
    y+=o.gap??1.5;
  };
  const kv=(rows,cols=2)=>{
    const cw=UW/cols;let i=0;
    while(i<rows.length){
      ensure(9);
      for(let c=0;c<cols&&i<rows.length;c++,i++){
        const x=M+c*cw;
        doc.setFont("helvetica","bold");doc.setFontSize(7.5);col(MUT);doc.text(rows[i][0].toUpperCase(),x,y+2.5);
        doc.setFont("helvetica","normal");doc.setFontSize(9.5);col(INK);
        const ls=doc.splitTextToSize(String(rows[i][1]||"—"),cw-4);doc.text(ls[0]||"—",x,y+7);
      }
      y+=10.5;
    }
  };
  const cb=(x,yy,on)=>{doc.setDrawColor(60,60,60);doc.setLineWidth(0.3);doc.rect(x,yy,3.6,3.6);if(on){fill(INK);doc.rect(x+.7,yy+.7,2.2,2.2,"F");}};
  const checkList=(items,cols)=>{
    const cw=UW/cols;let i=0;
    while(i<items.length){
      let rowH=5;const lsList=[];
      for(let c=0;c<cols&&i+c<items.length;c++){const ls=doc.splitTextToSize(items[i+c][0],cw-8);lsList.push(ls);rowH=Math.max(rowH,ls.length*4+1.5);}
      ensure(rowH);
      lsList.forEach((ls,c)=>{const it=items[i+c];const x=M+c*cw;cb(x,y,it[1]);doc.setFont("helvetica","normal");doc.setFontSize(8.5);col(INK);ls.forEach((l,k)=>doc.text(l,x+5.5,y+3+k*4));});
      y+=rowH;i+=cols;
    }
    y+=2;
  };
  // ---- Pág 1
  header(true);
  y+=drawDiscBand(doc,M,UW,y,f.disc,f.areaOp,donoDe(f.areaOp));
  kv([["Data programada para execução",f.dataProg]],1);
  if(f.sdcv&&f.sdcv.num)kv([["Nº da SDCV",f.sdcv.num],["Data da SDCV",(f.sdcv.data||"").split("-").reverse().join("/")],["Responsável",f.sdcv.resp]],3);
  bar("DESCRIÇÃO DO SERVIÇO");
  fill(Y);const tl=doc.splitTextToSize(f.titulo,UW-6);const th=tl.length*5+3;ensure(th);doc.rect(M,y-2,UW,th,"F");
  doc.setFont("helvetica","bold");doc.setFontSize(11);col(INK);tl.forEach((l,k)=>doc.text(l,M+3,y+3+k*5));y+=th+3;
  kv([["Linha",f.linha],["N. SS ou OM",f.ssom],["Área",f.area],["N. Pedido",f.pedido],["Supervisor da área",f.sup],["N. NF envio",f.nfEnvio],["Planejador da linha",f.plan],["N. NF retorno",f.nfRetorno]]);
  bar("TIPO DO SERVIÇO");
  checkList(tipos.map((t,i)=>[t,i===f.tipo]),2);
  bar("CLASSIFICAÇÃO DO SERVIÇO");
  checkList(classif.map((t,i)=>[t,i===f.classif]),2);
  bar("ÁREA SOLICITANTE: "+f.solicitante);
  para("Descrição detalhada do tipo de serviço a ser contratado",{b:1,s:8,c:MUT,gap:1});
  f.atividades.forEach(a=>para("• "+a,{ind:2,gap:0.4}));y+=2;
  bar("SUGESTÕES DE FORNECEDORES (SE HOUVER)");para(f.forn.join(" - ")||"—");
  bar("NÍVEIS DE MÃO DE OBRA");
  f.mo.forEach(m=>para(m.q+" "+m.f+"  ["+m.nr+"]",{b:1,gap:0.8}));
  f.reqMO.forEach(r=>para("• "+r,{ind:2,s:9,gap:0.3}));y+=2;
  para("Caixa de ferramentas padrão: ver lista (ferramentas). EPI: ver lista (EPIs).",{s:8.5,c:MUT});
  // ---- Pág 2
  doc.addPage();y=M;header(false);
  bar("DESCRIÇÃO GERAL DO SERVIÇO");para(f.titulo,{b:1});
  bar("O QUE PRECISA");para(f.oQue);
  bar("COMO");para(f.como||"(não preenchido)");
  bar("OBRIGAÇÕES DA GUARARAPES");checkList(f.obrG,1);
  bar("OBRIGAÇÕES DA CONTRATADA");checkList(f.obrC,1);
  bar("LISTA DE EPIs");
  checkList(f.epis.map(e=>[e[0]+"  —  "+e[1],e[2]]),1);
  bar("PERÍODO");para(f.periodo);
  bar("FORMA DE ACOMPANHAMENTO");para(f.acomp||"(não preenchido)");
  bar("RESPONSÁVEL TÉCNICO");para(f.rt,{b:1});
  // ---- Ferramentas
  doc.addPage();y=M;header(false);
  bar("CAIXA DE FERRAMENTA PADRÃO");
  const half=Math.ceil(ferr.length/2);
  for(let i=0;i<half;i++){
    ensure(5);
    [ferr[i],ferr[i+half]].forEach((it,c)=>{if(!it)return;const x=M+c*(UW/2);doc.setFont("helvetica","bold");doc.setFontSize(8);col(MUT);doc.text(String(it.qtd),x,y+3);doc.setFont("helvetica","normal");col(INK);doc.text(it.desc,x+11,y+3);});
    y+=4.6;
  }
  // ---- EPIs
  doc.addPage();y=M;header(false);
  bar("EPI (EQUIPAMENTO DE PROTEÇÃO INDIVIDUAL)");
  epiTexto.forEach(t=>para(t,{s:9,gap:2.5}));
  // ---- Justificativa + aprovação
  if(f._just){doc.addPage();y=M;header(false);bar("JUSTIFICATIVA TÉCNICA");
    f._just.split("\n").forEach((l,i)=>{if(!l.trim()){y+=1.5;return;}if(i<2){para(l,{s:i?9:11,b:!i,gap:1});return;}const hd=/^\d\. /.test(l);para(l,{s:hd?10:9,b:hd,gap:hd?1.2:0.8,c:hd?G:INK});});}
  {ensure(26);bar("APROVAÇÃO DO SUPERVISOR");const a=f.aprovacao||{};
   para(a.status?(a.status+" por "+a.por+" (mat. "+a.matricula+") em "+String(a.em||"").slice(0,10).split("-").reverse().join("/")+(a.obs?" - "+a.obs:"")):"AGUARDANDO APROVAÇÃO DO SUPERVISOR",{s:10,b:true,c:a.status==="APROVADA"?G:[168,90,5]});}
  // ---- Fotos
  if(fotos&&fotos.length){
    doc.addPage();y=M;header(false);bar("E.5 - FOTOS DOS TRABALHOS ("+fotos.length+")");
    const cw=(UW-6)/2;let col2=0,rowH=0;
    fotos.forEach(p=>{
      const ratio=p.h/p.w;let iw=cw,ih=iw*ratio;if(ih>78){ih=78;iw=ih/ratio;}
      const ll=doc.splitTextToSize(p.leg||"",cw).slice(0,6);
      const need=ih+9+ll.length*3.8+3;
      if(col2===0)ensure(need);
      else if(y+Math.max(rowH,need)>BOT){doc.addPage();y=M;header(false);col2=0;}
      const x=M+col2*(cw+6);
      try{doc.addImage(p.data,"JPEG",x,y,iw,ih);}catch(e){}
      doc.setFont("helvetica","bold");doc.setFontSize(8);col(G);doc.text(p.cat.toUpperCase(),x,y+ih+4);
      doc.setFont("helvetica","normal");col(INK);doc.text(ll,x,y+ih+8);
      rowH=Math.max(rowH,need);
      if(col2===1){y+=rowH;rowH=0;col2=0;}else col2=1;
    });
  }
  const n=doc.getNumberOfPages();
  for(let i=1;i<=n;i++){doc.setPage(i);gFooter(doc,M,W,n);doc.setFont("helvetica","normal");doc.setFontSize(7.5);col(MUT);doc.text("Gerado em "+new Date().toLocaleDateString("pt-BR")+" · "+f.id,M,291);doc.text("Pág. "+i+"/"+n,W-M,291,{align:"right"});}
  return doc;
}
