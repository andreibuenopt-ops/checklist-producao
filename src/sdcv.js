// ===== SDCV DO ERP: materiais (CM) e serviços CNAE (FTS) — importados por CSV =====
const SD_ST={AC:"APROV. COMPRA",T:"TRIAGEM",A:"EM APROVAÇÃO"}; // demais códigos aparecem como "ST xx" até termos a legenda
const sdStTxt=c=>c?(SD_ST[c]||"ST "+c):"—";
const sdDias=(a,b)=>Math.round((new Date(a+"T12:00:00")-new Date(b+"T12:00:00"))/864e5);
const rowSd=r=>({id:r.id,item:r.item||"",desc:r.descricao||"",comprador:r.comprador||"",tipo:r.tipo||"",tipoCompra:r.tipo_compra||"",cc:r.cc||"",categoria:r.categoria||"",qtd:r.qtd==null?null:+r.qtd,erp:r.erp||"",
 abertura:r.abertura,triagem:r.triagem,previsao:r.previsao,ultMov:r.ult_mov,status:r.status||"",tempo:r.tempo,ss:r.ss||"",ssMan:!!r.ss_man,kind:r.kind||"M",cnae:r.cnae||"",disc:r.disc,solic:r.solic_real||"",ref:r.ref,
 aprovador:r.aprovador||"",tipoApr:r.tipo_apr||"",dtEnvio:r.dt_envio,dias:r.dias_parado,aprov2:r.aprov2||"",ativo:r.ativo!==false});
const sdToRow=x=>({id:x.id,item:x.item||null,descricao:x.desc||null,comprador:x.comprador||null,tipo:x.tipo||null,tipo_compra:x.tipoCompra||null,cc:x.cc||null,categoria:x.categoria||null,qtd:x.qtd,erp:x.erp||null,
 abertura:x.abertura||null,triagem:x.triagem||null,previsao:x.previsao||null,ult_mov:x.ultMov||null,status:x.status||null,tempo:x.tempo??null,ss:x.ss||null,ss_man:!!x.ssMan,kind:x.kind,cnae:x.cnae||null,disc:x.disc??null,
 solic_real:x.solic||null,ref:x.ref||null,aprovador:x.aprovador||null,tipo_apr:x.tipoApr||null,dt_envio:x.dtEnvio||null,dias_parado:x.dias??null,aprov2:x.aprov2||null,ativo:x.ativo!==false});
const sdAtivos=()=>SDS.filter(x=>x.ativo);
const sdFts=f=>sdAtivos().filter(x=>x.ss&&x.ss===f.ssom);
const sdNFts=f=>typeof SDS==="undefined"?0:sdFts(f).length;
const sdRef=()=>SDS.reduce((m,x)=>x.ref&&x.ref>m?x.ref:m,"");
const sdAtraso=x=>{if(!x.previsao||!x.ref)return 0;const d=sdDias(x.ref,x.previsao);return d>0?d:0;};
const sdTitulo=x=>(x.desc||"").split(/\s{2,}/)[0].slice(0,140);
function sdDup(){const m={},out={};sdAtivos().forEach(x=>{if(!x.ss)return;const k=x.ss+"|"+x.kind+"|"+(x.kind==="M"?x.item:x.cnae);(m[k]=m[k]||[]).push(x.id);});
 Object.values(m).filter(a=>a.length>1).forEach(a=>a.forEach(i=>out[i]=a.filter(j=>j!==i)));return out;}

// ---------- leitura do CSV ----------
function csvParse(t){const R=[];let r=[],f="",q=false;t=t.replace(/^﻿/,"");
 for(let i=0;i<t.length;i++){const c=t[i];
  if(q){if(c==='"'){if(t[i+1]==='"'){f+='"';i++;}else q=false;}else f+=c;}
  else if(c==='"')q=true;else if(c===";"){r.push(f);f="";}
  else if(c==="\n"||c==="\r"){if(c==="\r"&&t[i+1]==="\n")i++;r.push(f);f="";if(r.some(x=>x!==""))R.push(r);r=[];}
  else f+=c;}
 if(f!==""||r.length){r.push(f);if(r.some(x=>x!==""))R.push(r);}return R;}
const sdBr=v=>{const s=String(v??"").trim();if(/^[-–—]*$/.test(s))return"";const m=/^\[(.*)\]$/.exec(s);return m?m[1].trim():s;};
const sdD=v=>{const m=/^(\d{2})\/(\d{2})\/(\d{4})/.exec(sdBr(v));return m?`${m[3]}-${m[2]}-${m[1]}`:null;};
const sdDT=v=>{const m=/^(\d{2})\/(\d{2})\/(\d{4})(?:\s+(\d{2}:\d{2}:\d{2}))?/.exec(sdBr(v));return m?`${m[3]}-${m[2]}-${m[1]}T${m[4]||"00:00:00"}`:null;};
const sdN=v=>{const s=sdBr(v).replace(",",".");const n=parseFloat(s);return isNaN(n)?null:n;};
function csvObjs(rows){const h=rows[0].map(nrm);return rows.slice(1).map(r=>{const o={};h.forEach((k,i)=>o[k]=r[i]??"");return o;});}
async function lerTexto(file){const b=await file.arrayBuffer();let t=new TextDecoder("utf-8").decode(b);if(t.includes("�"))t=new TextDecoder("windows-1252").decode(b);return t;}

// ---------- extração dos campos do texto ----------
const sdSS=t=>{const m=/ORDEM\s+(?:DE\s+)?SERVI[ÇC]O\s*:?\s*(\d[\d.]*)/i.exec(t);if(!m)return"";const n=m[1].replace(/\./g,"");return n.length>=6?n:"";};
const sdSolic=t=>{const m=/SOLICITANTE:\s*(.*?)\s*(?:PARADA|HOR[ÁA]RIO|CAPEX|IMPORTADO|DATA DE|TRABALHAR|DADOS|OBSERVA|$)/i.exec(t.replace(/\s+/g," "));return m?m[1].trim().slice(0,60):"";};
function sdKind(item,t){const m=/CNAE[\s-]*(\d{2})\.(\d{2})/i.exec(t);if(m)return{kind:"S",cnae:m[1]+"."+m[2]};const n=/^7\.9911(\d{2})(\d{2})/.exec(item);return n?{kind:"S",cnae:n[1]+"."+n[2]}:{kind:"M",cnae:""};}
const SD_CAT_EL=/el[eé]tric|cabo|motor|bobina|sensor|l[aâ]mpada|conector|canaleta|eletroc|cx luvas|diodo|transform|acess[oó]rios el|eletr[oô]nic|fios/i,SD_CAT_ME=/rolament|acoplament|mancal|junta|v[aá]lvula|mangueira|correia|abra[cç]adeira|uni[aã]o|pe[cç]as|chapas|manuten[cç][aã]o mec/i;
function sdInfDisc(x){const f=ftsPorSS(x.ss);if(f&&dOk(f.disc))return f.disc;
 if(x.kind==="S"){const m=/ESPECIALIDADE\s+T[ÉE]CNICA:?\s*([^-]{0,60})/i.exec(x.desc||"");if(m){if(/MEC/i.test(m[1]))return 1;if(/EL[ÉE]TR/i.test(m[1]))return 0;}}
 const c=x.categoria||"";if(SD_CAT_EL.test(c)&&!/mec/i.test(c))return 0;if(SD_CAT_ME.test(c))return 1;return null;}

// ---------- importação ----------
const SDI={sd:null,ap:null,recs:[],info:null,msg:""};
function sdImportar(){const i=document.createElement("input");i.type="file";i.accept=".csv,.txt";i.multiple=true;
 i.onchange=async()=>{SDI.sd=null;SDI.ap=null;SDI.msg="";
  try{for(const f of i.files){const rows=csvParse(await lerTexto(f));if(!rows.length)continue;const h=rows[0].map(nrm);
   if(h.includes("codsdcv"))SDI.sd=csvObjs(rows);else if(h.includes("tipoapr")&&h.includes("documento"))SDI.ap=csvObjs(rows);else SDI.msg+="ARQUIVO NÃO RECONHECIDO: "+f.name+". ";}
   if(!SDI.sd&&!SDI.ap&&!SDI.msg)SDI.msg="NENHUM ARQUIVO LIDO.";else sdMontar();}catch(e){SDI.msg="ERRO AO LER: "+e.message;}
  sdImpModal();};i.click();}
function sdMontar(){const ex={};SDS.forEach(x=>ex[x.id]=x);let base=[];
 if(SDI.sd){base=SDI.sd.filter(o=>sdBr(o.codsdcv)).map(o=>{const id=sdBr(o.codsdcv),e=ex[id],t=String(o.itemdescricao||""),it=sdBr(o.item),k=sdKind(it,t);
  const x={id,item:it,desc:t,comprador:sdBr(o.comprador),tipo:sdBr(o.sdcvtipo),tipoCompra:sdBr(o.tipocompra),cc:sdBr(o.centrodecusto),categoria:sdBr(o.categoria),qtd:sdN(o.qtddesdcv),erp:sdBr(o.codsdcvdoerp),
   abertura:sdD(o.datadeabertura),triagem:sdD(o.datadetriagem),previsao:sdD(o.dataprevisao),ultMov:sdDT(o.dataultmovimentacao),status:sdBr(o.status),tempo:sdN(o.tempodaultimamovimentacao),kind:k.kind,cnae:k.cnae,solic:sdSolic(t),ativo:true};
  x.ss=e&&e.ssMan?e.ss:sdSS(t);x.ssMan=!!(e&&e.ssMan);x.disc=e&&dOk(e.disc)?e.disc:sdInfDisc(x);
  if(e){x.aprovador=e.aprovador;x.tipoApr=e.tipoApr;x.dtEnvio=e.dtEnvio;x.dias=e.dias;x.aprov2=e.aprov2;}return x;});
  const ref=base.reduce((m,x)=>{const d=(x.ultMov||"").slice(0,10);return d>m?d:m;},"");base.forEach(x=>x.ref=ref||null);}
 else base=SDS.filter(x=>x.ativo).map(x=>({...x}));
 let semDoc=0;
 if(SDI.ap){const M={};SDI.ap.forEach(o=>{const d=sdBr(o.documento);if(!d)return;const dias=sdN(o.diasparado),m=M[d]=M[d]||{cur:null,prox:[]};
   if(dias!=null){if(!m.cur||dias>m.cur.dias)m.cur={ap:sdBr(o.aprovador),tp:sdBr(o.tipoapr),dt:sdD(o.dtenvio),dias};}else m.prox.push(sdBr(o.aprovador));});
  const ids=new Set();base.forEach(x=>{const m=M[x.id.replace("/","")];if(m&&(m.cur||m.prox.length)){ids.add(x.id);x.aprovador=m.cur?m.cur.ap:"";x.tipoApr=m.cur?m.cur.tp:"";x.dtEnvio=m.cur?m.cur.dt:null;x.dias=m.cur?m.cur.dias:null;x.aprov2=m.prox.join(" / ");}
   else{x.aprovador="";x.tipoApr="";x.dtEnvio=null;x.dias=null;x.aprov2="";}});
  semDoc=Object.keys(M).filter(d=>!base.some(x=>x.id.replace("/","")===d)).length;}
 const novos=base.filter(x=>!ex[x.id]).length,sai=SDI.sd?SDS.filter(x=>x.ativo&&!base.some(b=>b.id===x.id)).map(x=>x.id):[];
 SDI.recs=base;SDI.sai=sai;
 SDI.info={total:base.length,mat:base.filter(x=>x.kind==="M").length,srv:base.filter(x=>x.kind==="S").length,novos,semSS:base.filter(x=>!x.ss).length,semDisc:base.filter(x=>!dOk(x.disc)).length,aprov:base.filter(x=>x.aprovador).length,semDoc,sai:sai.length,ref:base[0]&&base[0].ref,temSd:!!SDI.sd,temAp:!!SDI.ap};}
function sdImpModal(){let m=document.getElementById("impm");if(!m){m=document.createElement("div");m.id="impm";m.className="impm";document.body.appendChild(m);}
 const I=SDI.info&&(SDI.sd||SDI.ap)?SDI.info:null;
 m.innerHTML=`<div class="impb"><div style="display:flex;justify-content:space-between;align-items:center"><h3 style="margin:0">📥 IMPORTAR SDCV DO ERP (CSV)</h3><button class="btn ghost sm" id="impx">FECHAR</button></div>
 ${SDI.msg?`<div class="card" style="margin-top:10px">${esc(SDI.msg)}</div>`:""}
 ${I?`<div class="card" style="margin-top:10px"><b>${I.total} SDCV</b> · ${I.mat} MATERIAL(IS) · ${I.srv} SERVIÇO(S) CNAE · ${I.novos} NOVO(S)${I.ref?` · POSIÇÃO DO ERP: <b>${fmtD(I.ref)}</b>`:""}
 <div class="meta" style="margin-top:6px">${I.temSd?"ARQUIVO “SDCV EM ANDAMENTO” LIDO. ":"SÓ APROVAÇÕES: OS SDCV JÁ NO APP SERÃO ATUALIZADOS. "}${I.temAp?`APROVAÇÕES LIDAS: ${I.aprov} SDCV COM APROVAÇÃO PENDENTE${I.semDoc?` (${I.semDoc} DOC(S) DO ARQUIVO NÃO ESTÃO NOS SDCV)`:""}. `:"SEM O ARQUIVO DE APROVAÇÕES, AS APROVAÇÕES ATUAIS SÃO MANTIDAS. "}</div>
 <div class="meta" style="margin-top:6px">VÍNCULO COM A FTS PELA SS/OM LIDA NO TEXTO: ${I.total-I.semSS} COM Nº · <b>${I.semSS} SEM Nº</b> (VOCÊ PODE LIGAR À MÃO) · ${I.semDisc} SEM ESPECIALIDADE DEFINIDA.</div>
 ${I.sai?`<div class="meta" style="margin-top:6px">${I.sai} SDCV QUE ESTAVAM NO APP NÃO VIERAM NESTE ARQUIVO E SERÃO MARCADOS COMO CONCLUÍDOS (SAEM DAS LISTAS, FICAM NO BANCO).</div>`:""}
 <div class="meta" style="margin-top:6px">NO REIMPORT, SS/OM E ESPECIALIDADE AJUSTADAS À MÃO SÃO PRESERVADAS.</div></div>
 <div class="act" style="margin-top:12px"><button class="btn" id="sdgo" ${I.total?"":"disabled"}>IMPORTAR ${I.total} SDCV</button></div>`:""}</div>`;
 m.querySelector("#impx").onclick=()=>m.remove();
 const go=m.querySelector("#sdgo");if(go)go.onclick=async()=>{go.disabled=true;let n=0;const R=SDI.recs.map(sdToRow);
  for(let i=0;i<R.length;i+=100){go.textContent="IMPORTANDO… "+n+"/"+R.length;const r=await SB.from("sdcv").upsert(R.slice(i,i+100),{onConflict:"id"});if(r.error){dbErr(r.error,"Erro ao importar (rodou a migracao10_sdcv.sql?)");go.disabled=false;go.textContent="TENTAR DE NOVO";return;}n+=Math.min(100,R.length-i);}
  for(let i=0;i<SDI.sai.length;i+=100){const r=await SB.from("sdcv").update({ativo:false}).in("id",SDI.sai.slice(i,i+100));if(r.error){dbErr(r.error);break;}}
  await loadAll();m.remove();render();toast(n+" SDCV importado(s)");};}

// ---------- telas ----------
const sdTabsHtml=(onde,v,l1,l2)=>`<div class="sdt">${[["",l1],["sd",l2]].map(([k,t])=>`<button data-sdv="${onde}:${k}" class="${(v||"")===k?"on":""}">${t}</button>`).join("")}</div>`;
function vCm(){return sdTabsHtml("cm",state.cmv,"CM · COMPRAS DO APP",`SDCV MATERIAIS (ERP) · ${sdAtivos().filter(x=>x.kind==="M"&&espOk(x.disc)).length}`)+(state.cmv==="sd"?vSdcv("M"):vCmBase());}
function vBusca(){return sdTabsHtml("fts",state.ftv,"FTS",`SDCV CNAE 14.01 (ERP) · ${sdAtivos().filter(x=>x.kind==="S"&&espOk(x.disc)).length}`)+(state.ftv==="sd"?vSdcv("S"):vBuscaBase());}
function sdCard(x,dup,q){const at=sdAtraso(x),f=x.ss?ftsPorSS(x.ss):null;
 return `<div class="card res${bdCls([x.disc])}" data-sd="${esc(x.id)}"><div style="display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap"><h3>${hl(x.id,q)} · ${hl(sdTitulo(x),q)}</h3><div><span class="chip">${esc(sdStTxt(x.status))}</span>${at?`<span class="chip bad">ATRASADO ${at} D</span>`:""}</div></div>
 <div class="meta">${x.kind==="M"?`ITEM ${hl(x.item,q)} · QTD ${x.qtd??"—"}`:`CNAE ${esc(x.cnae)}`} · ${esc(x.cc||"—")} · COMPRADOR: ${esc(x.comprador||"—")} · PREVISÃO ${fmtD(x.previsao)}${x.solic?" · SOLIC.: "+esc(x.solic):""}</div>
 <div style="margin-top:6px">${discChip(x.disc)}${x.ss?(f?`<span class="chip ok">FTS ${esc(f.id)}</span>`:`<span class="chip warn">SS ${hl(x.ss,q)} · SEM FTS</span>`):'<span class="chip warn">SEM SS/OM</span>'}${x.aprovador?`<span class="chip warn">${esc(x.tipoApr)} · ${esc(x.aprovador)}${x.dias!=null?" · "+x.dias+" D PARADO":""}</span>`:""}${dup?`<span class="chip bad">VERIFICAR DUPLICIDADE (${dup.map(esc).join(", ")})</span>`:""}</div></div>`;}
function vSdcv(kind){const q=state.sq||"",fl=state.sf||"",cn=state.scn??"14.01",ref=sdRef(),dup=sdDup();
 let L=sdAtivos().filter(x=>x.kind===kind&&espOk(x.disc));
 if(kind==="S"&&cn)L=L.filter(x=>x.cnae===cn);
 const cnaes=[...new Set(sdAtivos().filter(x=>x.kind==="S").map(x=>x.cnae))].sort();
 const tot=L.length,atr=L.filter(x=>sdAtraso(x)>0).length,apr=L.filter(x=>x.aprovador).length,dp=L.filter(x=>dup[x.id]).length,sf=L.filter(x=>!ftsPorSS(x.ss||"")).length;
 L=L.filter(x=>({"":1,A:sdAtraso(x)>0,P:!!x.aprovador,D:!!dup[x.id],F:!ftsPorSS(x.ss||"")})[fl]);
 const n=norm(q);if(n)L=L.filter(x=>norm([x.id,x.item,x.desc,x.ss,x.cc,x.comprador,x.solic,x.categoria,x.aprovador].join(" ")).includes(n));
 L.sort((a,b)=>sdAtraso(b)-sdAtraso(a)||b.id.localeCompare(a.id));
 const lim=state.slim||60,hoje=hojeISO(),idade=ref?sdDias(hoje,ref):0;
 return `<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px;flex-wrap:wrap"><div><h2>${kind==="M"?"SDCV · MATERIAIS (ERP)":"SDCV · SERVIÇOS CNAE (ERP)"}</h2><div class="sub">${kind==="M"?"MATERIAIS EM COMPRA NO ERP, LIGADOS ÀS CM/FTS PELA SS/OM.":"SERVIÇOS CONTRATADOS NO ERP, LIGADOS ÀS FTS PELA SS/OM."}</div></div>${ME&&ME.master?'<button class="btn ghost" id="impsd">📥 IMPORTAR CSV DO ERP</button>':""}</div>
 ${ref?`<div class="card ${idade>3?"warn":""}" style="${idade>3?"border-color:#e0a800":""}"><b>POSIÇÃO DO ERP: ${fmtD(ref)}</b>${idade>3?` · ${idade} DIAS ATRÁS — REIMPORTE OS CSVs PARA ATUALIZAR`:""}<div class="meta">ATRASO = PREVISÃO VENCIDA NA DATA DA POSIÇÃO.</div></div>`:'<div class="card meta">NENHUM SDCV IMPORTADO AINDA. '+(ME&&ME.master?"USE “IMPORTAR CSV DO ERP” (SDCV EM ANDAMENTO + APROVAÇÕES PENDENTES).":"PEÇA AO PCM PARA IMPORTAR.")+"</div>"}
 <div class="card">${guiaEsp()}<input class="srch" id="sdq" placeholder="Nº SDCV · ITEM · SS/OM · DESCRIÇÃO · SOLICITANTE" value="${esc(q)}"><div class="fl" style="margin-top:8px"><select id="sdf"><option value="">TODOS (${tot})</option><option value="A" ${fl==="A"?"selected":""}>ATRASADOS (${atr})</option><option value="P" ${fl==="P"?"selected":""}>EM APROVAÇÃO (${apr})</option><option value="D" ${fl==="D"?"selected":""}>POSSÍVEL DUPLICIDADE (${dp})</option><option value="F" ${fl==="F"?"selected":""}>SEM FTS LIGADA (${sf})</option></select>
 ${kind==="S"?`<select id="sdc"><option value="">TODOS OS CNAE</option>${cnaes.map(c=>`<option value="${c}" ${c===cn?"selected":""}>CNAE ${c}</option>`).join("")}</select>`:""}</div><div class="meta" style="margin-top:9px">${L.length} RESULTADO(S)</div></div>
 ${L.slice(0,lim).map(x=>sdCard(x,dup[x.id],q)).join("")||'<div class="card meta">NADA ENCONTRADO.</div>'}${L.length>lim?'<div class="act"><button class="btn ghost" id="sdmais">MOSTRAR MAIS</button></div>':""}`;}
function sdFtsPainel(f){const L=sdFts(f),dup=sdDup(),M=L.filter(x=>x.kind==="M"),S=L.filter(x=>x.kind==="S");
 const bloco=(t,A)=>A.length?`<div class="card"><b>${t} (${A.length})</b></div>${A.map(x=>sdCard(x,dup[x.id],"")).join("")}`:"";
 return `<div class="card"><div><b>SDCV DO ERP NA SS ${esc(f.ssom)}</b><div class="meta">${S.length} SERVIÇO(S) CNAE · ${M.length} MATERIAL(IS)${SDS.length?"":" · NENHUM SDCV IMPORTADO"}</div></div></div>${bloco("SERVIÇOS CNAE",S)}${bloco("MATERIAIS",M)}${L.length||!SDS.length?"":'<div class="card meta">NENHUM SDCV DO ERP COM ESTA SS/OM. SE EXISTIR, LIGUE À MÃO ABRINDO O SDCV NA LISTA.</div>'}`;}
function sdModal(id){const x=SDS.find(s=>s.id===id);if(!x)return;const f=x.ss?ftsPorSS(x.ss):null,ed=ME&&ME.master,dup=sdDup()[id],at=sdAtraso(x);
 const m=document.createElement("div");m.className="impm";document.body.appendChild(m);
 const k=(l,v)=>`<div><span class="k">${l}</span>${v==null||v===""?"—":esc(v)}</div>`;
 m.innerHTML=`<div class="impb"><div style="display:flex;justify-content:space-between;align-items:center"><h3 style="margin:0">SDCV ${esc(x.id)} · ${x.kind==="M"?"MATERIAL":"SERVIÇO CNAE "+esc(x.cnae)}</h3><button class="btn ghost sm" id="sdx">FECHAR</button></div>
 <div class="grid2" style="margin-top:10px">${k("STATUS",sdStTxt(x.status)+(x.status?" ("+x.status+")":""))}${k("COMPRADOR",x.comprador)}${k("ABERTURA",fmtD(x.abertura))}${k("TRIAGEM",fmtD(x.triagem))}${k("PREVISÃO",fmtD(x.previsao)+(at?` · ATRASADO ${at} D`:""))}${k("ÚLT. MOVIMENTAÇÃO",x.ultMov?fmtD(x.ultMov.slice(0,10))+" "+x.ultMov.slice(11,16)+(x.tempo!=null?` (${x.tempo} D)`:""):"")}${k("CENTRO DE CUSTO",x.cc)}${k("CATEGORIA",x.categoria)}${k("QTD",x.qtd)}${k("ITEM",x.item)}${k("SOLICITANTE (TEXTO)",x.solic)}${k("COD. ERP",x.erp)}${k("APROVAÇÃO PENDENTE",x.aprovador?`${x.tipoApr} · ${x.aprovador}${x.dias!=null?" · "+x.dias+" D":""}`:"")}${k("PRÓXIMO APROVADOR",x.aprov2)}</div>
 ${dup?`<div class="card" style="margin-top:10px;border-color:#c0392b">VERIFICAR DUPLICIDADE: MESMA SS/OM E MESMO ${x.kind==="M"?"ITEM":"CNAE"} EM ${dup.map(esc).join(", ")}</div>`:""}
 <label style="margin-top:10px">DESCRIÇÃO COMPLETA</label><div class="card" style="max-height:180px;overflow:auto;font-size:12px;white-space:pre-wrap">${esc(x.desc)}</div>
 <div class="row" style="margin-top:10px"><div><label>SS/OM (VÍNCULO COM A FTS)</label><input id="sdss" value="${esc(x.ss)}" ${ed?"":"disabled"}></div><div><label>ESPECIALIDADE</label><select id="sdd" ${ed?"":"disabled"}>${optEsp(dOk(x.disc)?x.disc:undefined,"— A DEFINIR —")}</select></div></div>
 <div class="act" style="margin-top:12px">${f?`<button class="btn ghost" id="sdfts">ABRIR ${esc(f.id)}</button>`:""}${ed?'<button class="btn" id="sdsv">SALVAR</button>':""}</div>${x.ssMan?'<div class="meta" style="margin-top:6px">SS/OM AJUSTADA À MÃO: NÃO É SOBRESCRITA NO REIMPORT.</div>':""}</div>`;
 m.querySelector("#sdx").onclick=()=>m.remove();
 const a=m.querySelector("#sdfts");if(a)a.onclick=()=>{m.remove();open(f.id,"mat");};
 const s=m.querySelector("#sdsv");if(s)s.onclick=async()=>{const ss=m.querySelector("#sdss").value.trim().replace(/\D/g,""),d=m.querySelector("#sdd").value;
  const man=ss!==x.ss||x.ssMan;const r=await SB.from("sdcv").update({ss:ss||null,ss_man:man,disc:d===""?null:+d}).eq("id",id);if(r.error){dbErr(r.error);return;}await loadAll();m.remove();render();toast("SDCV atualizado");};}
function bindSd(){document.querySelectorAll("[data-sdv]").forEach(b=>b.onclick=()=>{const [o,v]=b.dataset.sdv.split(":");state[o==="cm"?"cmv":"ftv"]=v;state.slim=0;state.sf="";state.sq="";render();});
 if($("#sdq"))keep("#sdq","sq");if($("#sdf"))$("#sdf").onchange=e=>{state.sf=e.target.value;state.slim=0;render();};if($("#sdc"))$("#sdc").onchange=e=>{state.scn=e.target.value;state.slim=0;render();};
 if($("#sdmais"))$("#sdmais").onclick=()=>{state.slim=(state.slim||60)+100;render();};if($("#impsd"))$("#impsd").onclick=sdImportar;
 document.querySelectorAll("[data-sd]").forEach(c=>c.onclick=()=>sdModal(c.dataset.sd));}
