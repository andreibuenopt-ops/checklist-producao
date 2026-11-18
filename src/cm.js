// ===== CM (Compra de Material) e CE (Conserto Externo) — telas separadas, tudo em maiúsculo =====
const U=s=>String(s??"").toUpperCase();
const fmtD=d=>d?d.split("-").reverse().join("/"):"—";
const hojeISO=()=>new Date().toISOString().slice(0,10);
const dias=(a,b)=>Math.round((new Date(b)-new Date(a))/864e5);
const matFind=c=>MATERIAIS.find(m=>m.cod===U(c).trim());
const cmFind=id=>CMS.find(c=>c.id===id),ceFind=id=>CES.find(c=>c.id===id);
const brl=v=>v?"R$ "+(+v).toLocaleString("pt-BR",{minimumFractionDigits:2}):"—";
const ftsPorSS=ss=>FTS.find(f=>f.ssom===String(ss).trim());
const linhaDe=f=>({"MDF-I":"MDF01","MDF-II":"MDF02"})[f.linha]||U(f.linha);
const progDe=f=>{const t=U(f.dataProg),mes=MESES.findIndex(m=>t.includes(m)),a=(t.match(/20\d\d/)||[new Date().getFullYear()])[0];return {linha:linhaDe(f),tipo:/ANUAL/.test(t)?2:/SEMANAL|SEMANA/.test(t)?0:1,mes:mes<0?new Date().getMonth():mes,semana:"",ano:+a};};
const stC=(st,list)=>`<span class="chip ${st===list.length-1?"ok":st===0?"":"warn"}">${esc(list[st])}</span>`;
// especialidade / área / dono
const discCls=d=>["d-el","d-me","d-pr","d-ou"][d]||"";
const discChip=d=>dOk(d)?`<span class="chip ${discCls(d)}">${DISC[d]}</span>`:'<span class="chip warn">ESPECIALIDADE A DEFINIR</span>';
const areaChip=a=>a?`<span class="chip">${esc(a)}${ccDe(a)?" · CC "+esc(ccDe(a)):""} · ${esc(donoDe(a)||"DONO A DEFINIR")}</span>`:'<span class="chip warn">ÁREA A DEFINIR</span>';
const discSet=arr=>[...new Set(arr.filter(d=>dOk(d)))];
const bdCls=arr=>{const s=discSet(arr);return s.length===1?" bd-"+discCls(s[0]).slice(2):"";};
const pd=v=>v===""||v===undefined?"":+v;
const histData=(o,st)=>{const h=(o.hist||[]).find(x=>x[0]===st);return h?h[1]:"";};
const dataCompra=c=>histData(c,"EM COMPRA")||(c.sdcv&&c.sdcv.data)||"";
const dataRec=c=>histData(c,"RECEBIDA");
const optSel=(a,v,ph)=>`${ph?`<option value="">${ph}</option>`:""}${a.map((x,i)=>`<option value="${i}" ${v===i?"selected":""}>${esc(x)}</option>`).join("")}`;
const optStr=(a,v,ph)=>`${ph?`<option value="">${ph}</option>`:""}${a.map(x=>`<option ${x===v?"selected":""}>${esc(x)}</option>`).join("")}`;

// ---------- validações ----------
function cmValidar(d){const r=[],fin=d.status>=3,warnedDono={};
 if(d.tipo===0&&!(+d.semana>=1&&+d.semana<=53))r.push(["bad","INFORME A SEMANA (1 A 53)"]);
 if(!(+d.ano>=2020))r.push(["bad","INFORME O ANO"]);
 if(!d.itens.length)r.push(["bad","INCLUA AO MENOS UM ITEM"]);
 if(d.status>=1&&d.id&&aprSt(d)!=="APROVADA")r.push(["warn","SEM APROVAÇÃO DO SUPERVISOR"]);
 if(d.status>=2&&!(d.sdcv&&d.sdcv.num))r.push(["warn","SEM Nº DA SDCV (ABA D)"]);
 const seen={};
 d.itens.forEach((it,i)=>{const n="LINHA "+(i+1)+": ";
  if(!String(it.ss||"").trim())r.push(["bad",n+"NÚMERO DA SS OBRIGATÓRIO"]);else if(!ftsPorSS(it.ss))r.push(["warn",n+"SS "+it.ss+" NÃO ESTÁ NO BANCO DE FTS"]);
  if(!String(it.item||"").trim()&&!String(it.desc||"").trim())r.push(["bad",n+"INFORME O ITEM OU A DESCRIÇÃO"]);
  if(!(+it.qtd>0))r.push(["bad",n+"QUANTIDADE INVÁLIDA"]);
  if(!it.area)r.push(["bad",n+"INFORME A ÁREA"]);else if(!donoDe(it.area)&&!warnedDono[it.area]){warnedDono[it.area]=1;r.push(["warn","ÁREA "+it.area+" SEM DONO CADASTRADO (MENU ÁREAS E DONOS)"]);}
  if(!dOk(it.disc))r.push(["warn",n+"ESPECIALIDADE NÃO INFORMADA"]);
  const m=matFind(it.item);
  if(it.item&&!m)r.push(["warn",n+it.item+" NÃO ESTÁ NO CATÁLOGO"]);
  if(m&&!fin&&+it.qtd>m.estoque)r.push(["warn",n+m.cod+": PEDIDO "+it.qtd+" "+m.un+", ESTOQUE "+m.estoque+" → VAI PARA COMPRA"]);
  const key=it.ss+"|"+it.item;if(it.item&&seen[key])r.push(["warn",n+"ITEM REPETIDO PARA A MESMA SS"]);seen[key]=1;});
 return r;}
function ceValidar(d){const r=[],h=hojeISO();
 if(!String(d.ss||"").trim())r.push(["bad","NÚMERO DA SS OBRIGATÓRIO"]);else if(!ftsPorSS(d.ss))r.push(["warn","SS "+d.ss+" NÃO ESTÁ NO BANCO DE FTS"]);
 if(!String(d.item||"").trim())r.push(["bad","ITEM OBRIGATÓRIO"]);
 
 if(!String(d.defeito||"").trim())r.push(["bad","DEFEITO / SERVIÇO A EXECUTAR OBRIGATÓRIO"]);
 if(!d.area)r.push(["bad","INFORME A ÁREA"]);else if(!donoDe(d.area))r.push(["warn","ÁREA "+d.area+" SEM DONO CADASTRADO (MENU ÁREAS E DONOS)"]);
 if(!dOk(d.disc))r.push(["warn","ESPECIALIDADE NÃO INFORMADA"]);
 if(d.tipo===0&&!(+d.semana>=1&&+d.semana<=53))r.push(["bad","INFORME A SEMANA (1 A 53)"]);
 const K=x=>d.ficha?"warn":x;
 if(d.status>=4&&d.status<=7){if(!d.fornecedor)r.push([K("bad"),"FORNECEDOR OBRIGATÓRIO APÓS O ENVIO"]);if(!d.nfEnvio)r.push([K("bad"),"NF DE ENVIO OBRIGATÓRIA"]);if(!d.dtEnvio)r.push([K("bad"),"DATA DE ENVIO OBRIGATÓRIA"]);if(!d.dtPrev&&d.status===4)r.push(["warn","SEM PREVISÃO DE RETORNO"]);}
 if(d.status>=5&&d.status<=7){if(!d.nfRetorno)r.push([K("bad"),"NF DE RETORNO OBRIGATÓRIA"]);if(!d.dtRet)r.push([K("bad"),"DATA DE RETORNO OBRIGATÓRIA"]);}
 if(d.status<5&&d.nfRetorno)r.push(["warn","TEM NF DE RETORNO, MAS O STATUS NÃO É RETORNO"]);
 if(d.dtEnvio&&d.dtRet&&d.dtRet<d.dtEnvio)r.push(["bad","DATA DE RETORNO ANTERIOR À DE ENVIO"]);
 if(ceAberto(d)&&d.dtPrev&&d.dtPrev<h)r.push(["bad","CONSERTO ATRASADO HÁ "+dias(d.dtPrev,h)+" DIA(S)"]);
 return r;}
const alerts=r=>r.length?r.map(x=>`<div class="alert ${x[0]}">${x[0]==="bad"?"✖":"⚠"} ${esc(x[1])}</div>`).join(""):'<div class="alert ok">✔ SEM PENDÊNCIAS.</div>';

// ---------- listas (CM e CE separadas) ----------
function cmHits(c,q){const n=norm(q.trim());if(!n)return[];const h=[];
 if(norm(c.id+" "+siglaDe(c)).includes(n))h.push(["SIGLA",siglaDe(c)]);if(c.sdcv&&norm(c.sdcv.num||"").includes(n))h.push(["SDCV",c.sdcv.num]);
 c.itens.forEach(i=>{if(norm(i.ss).includes(n))h.push(["SS",i.ss]);else if(norm(i.item+" "+i.desc).includes(n))h.push(["ITEM",(i.item||"")+" — "+i.desc]);else if(norm(i.area||"").includes(n)||norm(donoDe(i.area)).includes(n))h.push(["ÁREA",i.area+" · "+donoDe(i.area)]);});return h;}
function ceHits(e,q){const n=norm(q.trim());if(!n)return[];const h=[];
 if(norm(e.id+" "+siglaCe(e)+" "+(e.cte||"")+" "+(e.compra||"")).includes(n))h.push(["CÓDIGO",e.id+" · "+siglaCe(e)]);if(e.sdcv&&norm(e.sdcv.num||"").includes(n))h.push(["SDCV",e.sdcv.num]);if(norm(e.ss).includes(n))h.push(["SS",e.ss]);
 if(norm(e.item+" "+e.desc).includes(n))h.push(["ITEM",e.item+" — "+e.desc]);if(norm(e.fornecedor).includes(n))h.push(["FORNECEDOR",e.fornecedor]);if(norm((e.responsavel||"")+" "+(e.pcm||"")+" "+(e.transportadora||"")+" "+(e.aplicacao||"")+" "+(e.areaTexto||"")).includes(n))h.push(["RESP./PCM/ÁREA",[e.responsavel,e.pcm,e.areaTexto].filter(Boolean).join(" · ")]);if(norm(e.nfEnvio+" "+e.nfRetorno).includes(n))h.push(["NF",e.nfEnvio+" / "+e.nfRetorno]);
 if(norm(e.area||"").includes(n)||norm(donoDe(e.area)).includes(n))h.push(["ÁREA",e.area+" · "+donoDe(e.area)]);return h;}
const fOk=(disc,area)=>espOk(disc)&&(!state.fa||area===state.fa);
function filtrosHtml(prog){const fd=state.fd??"";return `${guiaEsp()}<div class="fl">${prog?`<select id="cfl"><option value="">TODAS AS PROGRAMAÇÕES</option>${PROG.map((p,i)=>`<option value="${i}" ${String(i)===String(state.cf??"")?"selected":""}>${p.nome}</option>`).join("")}</select>`:""}

 <select id="fal"><option value="">TODAS AS ÁREAS</option>${optAreas(state.fa)}</select></div>`;}
function vCmBase(){const q=state.cq||"",f=state.cf??"";
 const L=CMS.filter(c=>(f===""||c.tipo===+f)&&c.itens.some(i=>fOk(i.disc,i.area))).map(c=>({c,h:cmHits(c,q)})).filter(x=>!q.trim()||x.h.length);
 return `<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px;flex-wrap:wrap"><div><h2>CM · COMPRA DE MATERIAL</h2><div class="sub">BUSQUE POR SIGLA, SS, CÓDIGO OU DESCRIÇÃO DO ITEM, SDCV OU DONO DA ÁREA.</div></div><button class="btn" id="ncm">➕ NOVA CM</button></div>
 <div class="card"><input class="srch" id="cq" placeholder="MDF02-PM-NOVEMBRO-2026 · 17057164 · MAT-00101 · ALETA" value="${esc(q)}">${filtrosHtml(true)}<div class="meta" style="margin-top:9px">${L.length} RESULTADO(S)</div></div>
 ${L.map(({c,h})=>`<div class="card res${bdCls(c.itens.map(i=>i.disc))}" data-cm="${esc(c.id)}"><div style="display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap"><h3>${hl(siglaDe(c),q)}</h3><div>${stC(c.status,CM_ST)}${c.sdcv&&c.sdcv.num?`<span class="chip ok">SDCV ${hl(c.sdcv.num,q)}</span>`:""}${c.exemplo?'<span class="chip ex">EXEMPLO FICTÍCIO</span>':""}</div></div>
  <div class="meta">${esc(c.id)} · ${esc(PROG[c.tipo].nome)} · ${c.itens.length} ITEM(NS) · SS: ${[...new Set(c.itens.map(i=>i.ss))].map(s=>hl(s,q)).join(", ")}${dataCompra(c)?" · COMPRADA EM "+fmtD(dataCompra(c)):""}</div>
  <div style="margin-top:6px">${discSet(c.itens.map(i=>i.disc)).map(discChip).join("")}${[...new Set(c.itens.map(i=>i.area))].map(areaChip).join("")}${aprChip(c)}</div>
  ${h.length?`<div class="meta" style="margin-top:6px">ENCONTRADO EM: ${h.slice(0,3).map(x=>`<b>${x[0]}</b> ${hl(x[1],q)}`).join(" · ")}</div>`:""}</div>`).join("")||'<div class="card meta">NADA ENCONTRADO.</div>'}`;}
function vCe(){const q=state.eq||"";
 const pcms=[...new Set(CES.map(e=>e.pcm).filter(Boolean))].sort(),sts=state.es??"",pc=state.ep||"";
 const L0=CES.filter(e=>fOk(e.disc,e.area)&&(sts===""||e.status===+sts||(sts==="A"&&ceAberto(e)))&&(!pc||e.pcm===pc)).map(e=>({e,h:ceHits(e,q)})).filter(x=>!q.trim()||x.h.length),lim=state.elim||80,L=L0.slice(0,lim);
 return `<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px;flex-wrap:wrap"><div><h2>CE · CONSERTO EXTERNO</h2><div class="sub">BUSQUE POR CÓDIGO, SS, ITEM, FORNECEDOR, NF, SDCV OU DONO DA ÁREA.</div></div><div class="act"><button class="btn ghost" id="impce">📥 IMPORTAR PLANILHA</button>${ME&&ME.master?'<button class="btn ghost" id="clsce">🧩 CLASSIFICAR ESPECIALIDADE</button>':""}<button class="btn" id="nce">➕ NOVO CE</button></div></div>
 <div class="card"><input class="srch" id="eq" placeholder="CE-0001 · 17061500 · MOTORREDUTOR · NF 12345" value="${esc(q)}">${filtrosHtml(false)}<div class="fl" style="margin-top:8px"><select id="ces"><option value="">TODOS OS STATUS</option><option value="A" ${sts==="A"?"selected":""}>EM ABERTO</option>${CE_ST.map((t,i)=>`<option value="${i}" ${String(i)===String(sts)?"selected":""}>${t}</option>`).join("")}</select><select id="cep"><option value="">TODOS OS PCM</option>${pcms.map(x=>`<option ${x===pc?"selected":""}>${esc(x)}</option>`).join("")}</select></div><div class="meta" style="margin-top:9px">${L0.length} RESULTADO(S)${L0.length>lim?" · MOSTRANDO "+lim:""}</div></div>
 ${L.map(({e,h})=>{const atr=ceAberto(e)&&e.dtPrev&&e.dtPrev<hojeISO();return `<div class="card res${bdCls([e.disc])}" data-ce="${esc(e.id)}"><div style="display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap"><h3>${hl(e.id,q)} · ${hl(e.item,q)}</h3><div>${stC(e.status,CE_ST)}${e.sdcv&&e.sdcv.num?`<span class="chip ok">SDCV ${hl(e.sdcv.num,q)}</span>`:""}${atr?'<span class="chip bad">ATRASADO</span>':""}${e.exemplo?'<span class="chip ex">EXEMPLO FICTÍCIO</span>':""}</div></div>
  <div style="font-weight:600">${hl(e.desc,q)}</div><div class="meta">SS ${hl(e.ss,q)} · ${esc(siglaCe(e))} · FORNECEDOR: ${hl(e.fornecedor||"—",q)} · NF ENVIO ${hl(e.nfEnvio||"—",q)} · PREVISÃO ${fmtD(e.dtPrev)}</div>
  <div style="margin-top:6px">${discChip(e.disc)}${e.area?areaChip(e.area):(e.areaTexto?`<span class="chip">${esc(e.areaTexto)}</span>`:areaChip(""))}${e.pcm?`<span class="chip">PCM ${esc(e.pcm)}</span>`:""}${e.responsavel?`<span class="chip">${esc(e.responsavel)}</span>`:""}${e.validada&&/^n/i.test(e.validada)?'<span class="chip warn">NÃO VALIDADA</span>':""}</div>
  ${h.length?`<div class="meta" style="margin-top:6px">ENCONTRADO EM: ${h.slice(0,3).map(x=>`<b>${x[0]}</b> ${hl(x[1],q)}`).join(" · ")}</div>`:""}</div>`;}).join("")||'<div class="card meta">NADA ENCONTRADO.</div>'}${L0.length>lim?'<div class="act"><button class="btn ghost" id="emais">MOSTRAR MAIS</button></div>':""}`;}

// ---------- detalhe CM ----------
function cmA(c){return `<div class="sheet"><div class="sh-head"><span></span><span>COMPRA DE MATERIAL – CM</span><small>${esc(c.id)}</small></div>
 <div class="sh-yel" style="font-size:18px;text-align:center">${esc(siglaDe(c))}</div>
 <div class="grid2"><div><span class="k">PROGRAMAÇÃO</span>${esc(PROG[c.tipo].nome)}</div><div><span class="k">LINHA</span>${esc(c.linha)}</div><div><span class="k">PERÍODO</span>${c.tipo===0?"SEMANA "+esc(c.semana):esc(MESES[c.mes])} / ${esc(c.ano)}</div><div><span class="k">STATUS</span>${esc(CM_ST[c.status])}</div>
 <div><span class="k">DATA DA COMPRA</span>${fmtD(dataCompra(c))}</div><div><span class="k">DATA DE RECEBIMENTO</span>${fmtD(dataRec(c))}</div></div>
 <div class="sh-bar">ITENS</div><div class="sh-body" style="overflow-x:auto"><table><tr><th>#</th><th>SS</th><th>ITEM</th><th>DESCRIÇÃO DO ITEM</th><th>EQUIPAMENTO / MODELO</th><th>UN</th><th>QTD</th><th>ÁREA / DONO</th><th>ESP.</th><th>ESTOQUE</th></tr>
 ${c.itens.map((it,i)=>{const m=matFind(it.item),f=ftsPorSS(it.ss);return `<tr><td>${i+1}</td><td>${f?`<a href="#" class="lnk" data-go="${esc(f.id)}">${esc(it.ss)}</a>`:esc(it.ss)}</td><td>${esc(it.item||"—")}</td><td>${esc(it.desc)}</td><td>${esc([it.equip,it.modelo].filter(Boolean).join(" · ")||"—")}</td><td>${esc(it.un)}</td><td><b>${esc(it.qtd)}</b></td><td>${areaChip(it.area)}</td><td>${discChip(it.disc)}</td><td>${m?(+it.qtd<=m.estoque?`<span class="chip ok">${m.estoque} OK</span>`:`<span class="chip warn">${m.estoque} · COMPRA</span>`):"—"}</td></tr>`;}).join("")}</table></div>
 <div class="sh-bar">OBSERVAÇÃO</div><div class="sh-body">${val(c.obs)}</div></div>`;}
function stepper(list,cur,advId,volId,hist){return `<div class="sheet"><div class="sh-head"><span></span><span>STATUS</span><small>${esc(list[cur])}</small></div><div class="sh-body"><div class="stp">${list.map((t,i)=>`<div class="st ${i<cur?"done":i===cur?"cur":""}"><i>${i<cur?"✓":i+1}</i><span>${esc(t)}</span></div>`).join("")}</div>
 <div class="act" style="margin:14px 0">${cur<list.length-1?`<button class="btn" id="${advId}">AVANÇAR PARA “${esc(list[cur+1])}”</button>`:'<span class="chip ok">CICLO CONCLUÍDO</span>'}${cur>0?`<button class="btn ghost" id="${volId}">VOLTAR UM STATUS</button>`:""}</div>
 <table><tr><th>STATUS</th><th>DATA</th><th>POR</th></tr>${hist.map(h=>`<tr><td>${esc(h[0])}</td><td>${fmtD(h[1])}</td><td>${esc(h[2])}</td></tr>`).join("")}</table></div></div>`;}
function sdcvTab(c){const s=c.sdcv||{};const f=(k,l,t)=>`<div><label>${l}</label><input ${t||""} data-sdcvf="${k}" value="${esc(s[k]||"")}"></div>`;
 return `<div class="sheet"><div class="sh-head"><span></span><span>SDCV</span><small>${esc(s.num||"A PREENCHER")}</small></div><div class="sh-body">
 <div class="meta" style="margin-bottom:6px">PREENCHA QUANDO ESTE REGISTRO VIRAR SDCV. O Nº PASSA A SER PESQUISÁVEL E SAI NO PDF.</div>
 <div class="row3">${f("num","Nº DA SDCV")}${f("data","DATA DA SDCV",'type="date"')}${f("resp","RESPONSÁVEL")}</div><label>OBSERVAÇÃO</label><input data-sdcvf="obs" value="${esc(s.obs||"")}"></div></div>`;}
function vCmDet(){const c=cmFind(state.sel);if(!c)return vCm();const n=cmValidar(c).length,np=(photos[c.id]||[]).length;
 const tabs=[["a","A · LISTA DE COMPRA"],["b","B · STATUS"],["fotos","C · FOTOS"+(np?` (${np})`:"")],["sdcv","D · SDCV"+(c.sdcv&&c.sdcv.num?" ✓":"")],["just","JUSTIFICATIVA"],["copy","📋 COPIAR TUDO"],["val","VALIDAÇÃO"]];
 const body={a:cmA,just:x=>pgJust(x,"cm"),copy:x=>pgCopy(x,"cm"),sdcv:sdcvTab,b:x=>stepper(CM_ST,x.status,"advcm","volcm",x.hist),fotos:pgFotos,val:x=>alerts(cmValidar(x))}[state.stab||"a"](c);
 return `<button class="btn ghost sm" id="backcm">← VOLTAR</button><div class="hero" style="margin-top:12px"><div class="code">${esc(c.id)} · CM · COMPRA DE MATERIAL</div><h2>${esc(siglaDe(c))}</h2>
 <div style="margin-bottom:12px"><span class="chip">${esc(PROG[c.tipo].nome)}</span><span class="chip">${esc(CM_ST[c.status])}</span><span class="chip">${c.itens.length} ITEM(NS)</span>${dataCompra(c)?`<span class="chip">COMPRADA EM ${fmtD(dataCompra(c))}</span>`:""}${c.sdcv&&c.sdcv.num?`<span class="chip">SDCV ${esc(c.sdcv.num)}</span>`:""}${c.exemplo?'<span class="chip">EXEMPLO FICTÍCIO</span>':""}</div>
 <div style="margin-bottom:12px">${discSet(c.itens.map(i=>i.disc)).map(discChip).join("")}${[...new Set(c.itens.map(i=>i.area))].map(areaChip).join("")}</div>
 ${aprBox(c,"cm")}<div class="act"><button class="btn" id="pdfcm">👁 VISUALIZAR / BAIXAR PDF DA CM</button></div></div>
 <div class="tabs">${tabs.map(t=>`<button data-cmt="${t[0]}" class="${(state.stab||"a")===t[0]?"on":""}">${t[1]}${t[0]==="val"&&n?`<span class="n">${n}</span>`:""}</button>`).join("")}</div>${body}`;}

// ---------- detalhe CE ----------
function ceA(e){const atr=ceAberto(e)&&e.dtPrev&&e.dtPrev<hojeISO();return `<div class="sheet"><div class="sh-head"><span></span><span>CONSERTO EXTERNO – CE</span><small>${esc(e.id)}</small></div>
 <div class="sh-yel">${esc(e.item)} — ${esc(e.desc)}</div>
 <div class="grid2"><div><span class="k">SS</span>${ftsPorSS(e.ss)?`<a href="#" class="lnk" data-go="${esc(ftsPorSS(e.ss).id)}">${esc(e.ss)}</a>`:esc(e.ss)}</div><div><span class="k">${e.ficha?"FICHA":"PROGRAMAÇÃO"}</span>${esc(siglaCe(e).replace("FICHA ",""))}</div>
 <div><span class="k">ESPECIALIDADE</span>${discChip(e.disc)}</div><div><span class="k">ÁREA / DONO</span>${e.area?areaChip(e.area):`<span class="chip">${esc(e.areaTexto||"ÁREA A DEFINIR")}</span>`}</div>
 <div><span class="k">RESPONSÁVEL / PCM</span>${val([e.responsavel,e.pcm].filter(Boolean).join(" · "))}</div><div><span class="k">QTD · RETORNO</span>${val((e.qtd!==""?e.qtd:"—")+" · "+(e.retorno||"—"))}</div>
 <div><span class="k">FORNECEDOR</span>${val(e.fornecedor)}</div><div><span class="k">VALOR ORÇADO</span>${esc(brl(e.valor))}</div>
 <div><span class="k">STATUS</span>${esc(CE_ST[e.status])} ${atr?'<span class="chip bad">ATRASADO</span>':""}</div><div><span class="k">PREVISÃO DE RETORNO</span>${fmtD(e.dtPrev)}</div></div>
 <div class="sh-bar">DEFEITO / SERVIÇO A EXECUTAR</div><div class="sh-body">${val(e.defeito)}</div><div class="sh-bar">OBSERVAÇÃO</div><div class="sh-body">${val(e.obs)}</div></div>`;}
function ceB(e){const f=(k,l,t)=>`<div><label>${l}</label><input ${t||""} data-cef="${k}" value="${esc(e[k])}"></div>`;
 return `<div class="sheet"><div class="sh-head"><span></span><span>REMESSA E RETORNO</span><small>NF</small></div><div class="sh-body">
 <div class="row3">${f("fornecedor","FORNECEDOR")}${f("nfEnvio","NF DE ENVIO")}${f("dtEnvio","DATA DE ENVIO",'type="date"')}</div>
 <div class="row3">${f("dtPrev","PREVISÃO DE RETORNO",'type="date"')}${f("nfRetorno","NF DE RETORNO")}${f("dtRet","DATA DE RETORNO",'type="date"')}</div>
 <div class="row3"><div><label>SITUAÇÃO ATUAL</label><select id="cest">${optSel(CE_ST,e.status)}</select></div>${f("ficha","FICHA")}${f("compra","COMPRA / PEDIDO")}</div>
 <div class="row3">${f("cte","CT-E")}${f("dtFollow","DATA FOLLOW UP",'type="date"')}${f("transportadora","TRANSPORTADORA")}</div>
 <div class="row3">${f("responsavel","RESPONSÁVEL")}${f("pcm","PCM")}${f("aprovador","APROVADOR ATUAL")}</div>
 <div class="row3">${f("retorno","RETORNO (ESTOQUE / APLICAÇÃO DIRETA)")}${f("aplicacao","APLICAÇÃO")}${f("qtd","QTD",'type="number" min="0"')}</div>
 <div class="row3">${f("validada","VALIDADA? (SIM / NÃO)")}${f("cadastro","CADASTRO")}${f("areaTexto","ÁREA (TEXTO DA PLANILHA)")}</div>
 <label>OBSERVAÇÃO</label><input data-cef="obs" value="${esc(e.obs)}">
 <div class="row">${f("valor","VALOR ORÇADO (R$)",'type="number" min="0" step="0.01"')}<div><label>DIAS FORA</label><div style="padding:10px 0;font-weight:700">${e.dtEnvio?dias(e.dtEnvio,e.dtRet||hojeISO())+" DIA(S)":"—"}</div></div></div></div></div>
 ${stepper(CE_ST,e.status,"advce","volce",e.hist)}`;}
function vCeDet(){const e=ceFind(state.sel);if(!e)return vCe();const n=ceValidar(e).length,np=(photos[e.id]||[]).length;
 const tabs=[["a","A · CONSERTO EXTERNO"],["b","B · REMESSA E RETORNO"],["fotos","C · FOTOS"+(np?` (${np})`:"")],["sdcv","D · SDCV"+(e.sdcv&&e.sdcv.num?" ✓":"")],["copy","📋 COPIAR TUDO"],["val","VALIDAÇÃO"]];
 const body={a:ceA,copy:x=>pgCopy(x,"ce"),b:ceB,sdcv:sdcvTab,fotos:pgFotos,val:x=>alerts(ceValidar(x))}[state.stab||"a"](e);
 return `<button class="btn ghost sm" id="backce">← VOLTAR</button><div class="hero" style="margin-top:12px"><div class="code">${esc(e.id)} · CE · CONSERTO EXTERNO · SS ${esc(e.ss)}</div><h2>${esc(e.item)}</h2>
 <div style="margin-bottom:12px"><span class="chip">${esc(CE_ST[e.status])}</span><span class="chip">${esc(siglaCe(e))}</span>${e.sdcv&&e.sdcv.num?`<span class="chip">SDCV ${esc(e.sdcv.num)}</span>`:""}${e.fornecedor?`<span class="chip">${esc(e.fornecedor)}</span>`:""}${e.exemplo?'<span class="chip">EXEMPLO FICTÍCIO</span>':""}</div>
 <div style="margin-bottom:12px">${discChip(e.disc)}${e.area?areaChip(e.area):`<span class="chip">${esc(e.areaTexto||"ÁREA A DEFINIR")}</span>`}${e.validada&&/^n/i.test(e.validada)?'<span class="chip warn">NÃO VALIDADA</span>':""}</div>
 <div class="act"><button class="btn" id="pdfce">👁 VISUALIZAR / BAIXAR PDF DO CE</button></div></div>
 <div class="tabs">${tabs.map(t=>`<button data-cmt="${t[0]}" class="${(state.stab||"a")===t[0]?"on":""}">${t[1]}${t[0]==="val"&&n?`<span class="n">${n}</span>`:""}</button>`).join("")}</div>${body}`;}

// ---------- aba na FTS ----------
const cmDaFts=f=>CMS.filter(c=>c.itens.some(i=>i.ss===f.ssom)),ceDaFts=f=>CES.filter(e=>e.ss===f.ssom);
function pgMat(f){const A=cmDaFts(f),B=ceDaFts(f);
 return sdFtsPainel(f)+`<div class="card"><div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap"><div><b>COMPRAS E CONSERTOS DA SS ${esc(f.ssom)}</b><div class="meta">${A.length} CM · ${B.length} CE</div></div><div class="act"><button class="btn" id="gcm">➕ GERAR CM</button><button class="btn ghost" id="gce">➕ GERAR CE</button></div></div>
 <div class="meta" style="margin-top:8px">A NOVA CM JÁ VEM COM A SS, A SIGLA, A ÁREA, A ESPECIALIDADE E ITENS SUGERIDOS PELAS ATIVIDADES DA FTS.</div></div>
 ${A.map(c=>`<div class="card res${bdCls(c.itens.map(i=>i.disc))}" data-cm="${esc(c.id)}"><h3>CM · ${esc(siglaDe(c))} ${stC(c.status,CM_ST)}</h3><div class="meta">${esc(c.id)} · ${c.itens.filter(i=>i.ss===f.ssom).length} ITEM(NS) DESTA SS</div></div>`).join("")}
 ${B.map(e=>`<div class="card res${bdCls([e.disc])}" data-ce="${esc(e.id)}"><h3>CE · ${esc(e.item)} ${stC(e.status,CE_ST)}</h3><div class="meta">${esc(e.id)} · ${esc(e.fornecedor||"SEM FORNECEDOR")}</div></div>`).join("")}`;}

// ---------- formulários ----------
const itBlank=()=>({ss:"",item:"",desc:"",equip:"",modelo:"",un:"",qtd:"",area:"",disc:espPerm().length===1?espPerm()[0]:""});
const cmVazia=()=>{const d=new Date();return {linha:"MDF02",tipo:1,mes:d.getMonth(),semana:"",ano:d.getFullYear(),itens:[itBlank()],obs:"",status:0};};
const ceVazio=()=>({...cmVazia(),ss:"",item:"",desc:"",defeito:"",fornecedor:"",nfEnvio:"",nfRetorno:"",dtEnvio:"",dtPrev:"",dtRet:"",valor:"",area:"",disc:espPerm().length===1?espPerm()[0]:"",itens:undefined});
const sugerir=f=>{const t=norm(f.atividades.join(" ")+" "+f.titulo),set=[];SM_KW.forEach(([re,cs])=>{if(re.test(t))cs.forEach(c=>{if(!set.includes(c))set.push(c);});});return set.map(c=>{const m=matFind(c);return {ss:f.ssom,item:m.cod,desc:m.desc,un:m.un,qtd:"",area:f.areaOp||"",disc:m.disc};});};
const autoRow=it=>{const f=ftsPorSS(it.ss);if(f){if(!it.area&&f.areaOp)it.area=f.areaOp;if(it.disc===""&&(dOk(f.disc)))it.disc=f.disc;}};
const progFields=(d,pre)=>`<div class="row3"><div><label>LINHA</label><select data-${pre}="linha">${LINHAS.map(l=>`<option ${l===d.linha?"selected":""}>${l}</option>`).join("")}</select></div>
 <div><label>PROGRAMAÇÃO</label><select data-${pre}="tipo" data-n="1">${optSel(PROG.map(p=>p.nome),d.tipo)}</select></div>
 <div>${d.tipo===0?`<label>SEMANA (1 A 53)</label><input type="number" min="1" max="53" data-${pre}="semana" value="${esc(d.semana)}">`:`<label>MÊS</label><select data-${pre}="mes" data-n="1">${optSel(MESES,d.mes)}</select>`}</div></div>
 <div class="row"><div><label>ANO</label><input type="number" data-${pre}="ano" value="${esc(d.ano)}"></div><div><label>SIGLA GERADA</label><div id="sigla" class="sh-yel" style="border-radius:8px">${esc(siglaDe(d))}</div></div></div>`;
function vCmNova(){const d=state.dcm||(state.dcm=cmVazia());
 return `<button class="btn ghost sm" id="backcm">← VOLTAR</button><h2 style="margin-top:12px">NOVA CM · COMPRA DE MATERIAL</h2><div class="sub">${d._sug?"ITENS SUGERIDOS PELA FTS. CONFIRA E PREENCHA AS QUANTIDADES.":"INFORME A PROGRAMAÇÃO E, EM CADA LINHA, A SS, O ITEM, A ÁREA E A ESPECIALIDADE."}</div>
 <datalist id="matlist">${MATERIAIS.map(m=>`<option value="${m.cod}">${esc(m.desc)}</option>`).join("")}</datalist><datalist id="sslist">${FTS.map(f=>`<option value="${f.ssom}">${esc(f.area)}</option>`).join("")}</datalist>
 <div class="card">${progFields(d,"h")}</div>
 <div class="card"><b>ITENS</b> <span class="meta"><span class="rq"> *</span> OBRIGATÓRIO (ITEM OU DESCRIÇÃO)</span><div style="overflow-x:auto;margin-top:8px"><table class="itb"><tr><th>SS<span class="rq"> *</span></th><th>ITEM<span class="rq"> *</span></th><th>DESCRIÇÃO<span class="rq"> *</span></th><th>EQUIPAMENTO</th><th>MODELO</th><th style="width:60px">UN</th><th style="width:80px">QTD<span class="rq"> *</span></th><th>ÁREA<span class="rq"> *</span></th><th>ESPECIALIDADE</th><th></th></tr>
 ${d.itens.map((it,i)=>`<tr><td><input list="sslist" data-r="${i}" data-k="ss" value="${esc(it.ss)}" placeholder="NÚMERO DA SS"></td><td><input list="matlist" data-r="${i}" data-k="item" value="${esc(it.item)}" placeholder="MAT-00101"></td><td><input data-r="${i}" data-k="desc" value="${esc(it.desc)}"></td><td><input data-r="${i}" data-k="equip" value="${esc(it.equip)}" placeholder="EX.: PRENSA CABO NYLON"></td><td><input data-r="${i}" data-k="modelo" value="${esc(it.modelo)}"></td><td><input data-r="${i}" data-k="un" value="${esc(it.un)}"></td><td><input type="number" min="0" data-r="${i}" data-k="qtd" value="${esc(it.qtd)}"></td>
 <td><select data-r="${i}" data-k="area">${optAreas(it.area,"— ÁREA —")}</select></td><td><select data-r="${i}" data-k="disc">${optEsp(it.disc,"— ESP. —",espPerm())}</select></td><td><button class="btn red sm" data-rm="${i}">✕</button></td></tr>`).join("")}</table></div>
 <div class="act" style="margin-top:10px"><button class="btn ghost sm" id="addit">➕ ADICIONAR LINHA</button><button class="btn ghost sm" id="sug">✨ SUGERIR ITENS PELA FTS DA SS</button></div>
 <label>OBSERVAÇÃO</label><input data-h="obs" value="${esc(d.obs)}"></div>
 <div id="valbox"></div><div class="act"><button class="btn" id="salvarcm">SALVAR CM</button><button class="btn ghost" id="limparcm">LIMPAR</button></div>`;}
function vCeNovo(){const d=state.dce||(state.dce=ceVazio());
 const f=(k,l,t,ph)=>`<div><label>${l}</label><input ${t||""} data-h="${k}" value="${esc(d[k])}" ${ph?`placeholder="${ph}"`:""}></div>`;
 return `<button class="btn ghost sm" id="backce">← VOLTAR</button><h2 style="margin-top:12px">NOVO CE · CONSERTO EXTERNO</h2><div class="sub">ITEM QUE VAI PARA CONSERTO FORA DA PLANTA. CAMPOS COM <span class="rq">*</span> SÃO OBRIGATÓRIOS.</div><datalist id="sslist">${FTS.map(x=>`<option value="${x.ssom}">${esc(x.area)}</option>`).join("")}</datalist>
 <div class="card"><div class="row">${f("ss",'NÚMERO DA SS<span class="rq"> *</span>','list="sslist"')}${f("item",'ITEM<span class="rq"> *</span>')}</div><label>DESCRIÇÃO DO ITEM</label><input data-h="desc" value="${esc(d.desc)}">
 <label>DEFEITO / SERVIÇO A EXECUTAR<span class="rq"> *</span></label><textarea data-h="defeito">${esc(d.defeito)}</textarea>
 <div class="row"><div><label>ÁREA<span class="rq"> *</span></label><select data-h="area">${optAreas(d.area,"— SELECIONE —")}</select></div><div><label>ESPECIALIDADE</label><select data-h="disc" data-n="1">${optEsp(d.disc,"— SELECIONE —",espPerm())}</select></div></div>${progFields(d,"h")}
 <div class="row3">${f("fornecedor","FORNECEDOR")}${f("nfEnvio","NF DE ENVIO")}${f("dtPrev","PREVISÃO DE RETORNO",'type="date"')}</div><label>OBSERVAÇÃO</label><input data-h="obs" value="${esc(d.obs)}"></div>
 <div id="valbox"></div><div class="act"><button class="btn" id="salvarce">SALVAR CE</button><button class="btn ghost" id="limparce">LIMPAR</button></div>`;}

// ---------- catálogo ----------
function vCat(){const q=state.iq,ct=state.ct||"mat";
 const tabs=`<div class="tabs"><button data-ct="mat" class="${ct==="mat"?"on":""}">MATERIAIS</button><button data-ct="fer" class="${ct==="fer"?"on":""}">FERRAMENTAS (CAIXA PADRÃO)</button></div>`;let tbl="";
 if(ct==="mat"){const L=MATERIAIS.filter(m=>!q||norm(m.cod+" "+m.desc).includes(norm(q)));
  tbl=`<tr><th>CÓDIGO</th><th>DESCRIÇÃO</th><th>UN</th><th>ESP.</th><th>ESTOQUE</th><th>USADO EM</th></tr>${L.map(m=>`<tr><td>${hl(m.cod,q)}</td><td>${hl(m.desc,q)}</td><td>${m.un}</td><td>${discChip(m.disc)}</td><td>${m.estoque?`<span class="chip ok">${m.estoque}</span>`:'<span class="chip warn">0</span>'}</td><td>${CMS.filter(c=>c.itens.some(i=>i.item===m.cod)).map(c=>`<a href="#" class="lnk" data-cm="${esc(c.id)}">${esc(siglaDe(c))}</a>`).join("<br>")}</td></tr>`).join("")}`;}
 else{const L=FERRAMENTAS.filter(i=>!q||norm(i.cod+" "+i.desc).includes(norm(q)));
  tbl=`<tr><th>CÓDIGO</th><th>QTD</th><th>DESCRIÇÃO</th><th>USADO EM</th></tr>${L.map(i=>`<tr><td>${hl(i.cod,q)}</td><td>${esc(i.qtd)}</td><td>${hl(i.desc,q)}</td><td>${FTS.filter(f=>f.ferr.includes(i.cod)).map(f=>`<a href="#" class="lnk" data-go="${esc(f.id)}">${esc(f.id)}</a>`).join("<br>")}</td></tr>`).join("")}`;}
 return `<h2>CATÁLOGO DE ITENS</h2><div class="sub">BUSQUE POR CÓDIGO OU DESCRIÇÃO E VEJA ONDE O ITEM É USADO.</div>${tabs}<div class="card"><input class="srch" id="iq" placeholder="MAT-00101, FER-016, ROLAMENTO…" value="${esc(q)}"></div>
 <div class="card" style="overflow-x:auto"><table>${tbl}</table></div><div class="banner">CÓDIGOS MAT-XXXXX / FER-XXX E ESTOQUES SÃO ILUSTRATIVOS. NA VERSÃO REAL VÊM DO ERP TOTVS.</div>`;}

// ---------- PDF ----------
async function baixarCm(){const c=cmFind(state.sel);if(!window.jspdf){toast("BIBLIOTECA DE PDF NÃO CARREGOU");return;}const fl=await flatPhotos(c.id);await saveDoc(buildPdfCm({...c,_just:justCm(c)},fl,window.jspdf,fmtD),c.id+"-"+siglaDe(c)+".pdf");}
async function baixarCe(){const e=ceFind(state.sel);if(!window.jspdf){toast("BIBLIOTECA DE PDF NÃO CARREGOU");return;}const fl=await flatPhotos(e.id);await saveDoc(buildPdfCe(e,fl,window.jspdf,fmtD),e.id+".pdf");}

// ---------- eventos ----------
function uv(el){let v=el.value;if(el.type==="text"||el.tagName==="TEXTAREA"){const p=el.selectionStart;v=v.toUpperCase();if(v!==el.value){el.value=v;try{el.setSelectionRange(p,p);}catch(e){}}}return v;}
function openCm(id){state.sel=id;state.stab="a";state.v="cmd";render();window.scrollTo(0,0);}
function openCe(id){state.sel=id;state.stab="a";state.v="ced";render();window.scrollTo(0,0);}
function bindCm(){
 if($("#cq"))keep("#cq","cq");if($("#eq"))keep("#eq","eq");
 if($("#cfl"))$("#cfl").onchange=e=>{state.cf=e.target.value;render();};
 document.querySelectorAll("[data-gd]").forEach(b=>b.onclick=()=>{state.fd=b.dataset.gd;state.elim=0;render();});
 if($("#fal"))$("#fal").onchange=e=>{state.fa=e.target.value;render();};
 document.querySelectorAll("[data-cm]").forEach(c=>c.onclick=e=>{e.preventDefault();openCm(c.dataset.cm);});
 document.querySelectorAll("[data-ce]").forEach(c=>c.onclick=e=>{e.preventDefault();openCe(c.dataset.ce);});
 document.querySelectorAll("[data-cmt]").forEach(b=>b.onclick=()=>{state.stab=b.dataset.cmt;render();});
 document.querySelectorAll("[data-ct]").forEach(b=>b.onclick=()=>{state.ct=b.dataset.ct;render();});
 if($("#backcm"))$("#backcm").onclick=()=>{state.v="cm";render();};
 if($("#backce"))$("#backce").onclick=()=>{state.v="ce";render();};
 if($("#ncm"))$("#ncm").onclick=()=>{state.dcm=null;state.v="cmn";render();};
 if($("#ces"))$("#ces").onchange=ev=>{state.es=ev.target.value;state.elim=0;render();};if($("#cep"))$("#cep").onchange=ev=>{state.ep=ev.target.value;state.elim=0;render();};if($("#emais"))$("#emais").onclick=()=>{state.elim=(state.elim||80)+120;render();};if($("#impce"))$("#impce").onclick=impAbrir;if($("#clsce"))$("#clsce").onclick=clsAbrir;
 if($("#nce"))$("#nce").onclick=()=>{state.dce=null;state.v="cen";render();};
 if($("#pdfcm"))$("#pdfcm").onclick=baixarCm;if($("#pdfce"))$("#pdfce").onclick=baixarCe;
 if($("#gcm"))$("#gcm").onclick=()=>{const f=FTS.find(x=>x.id===state.sel);state.dcm={...cmVazia(),...progDe(f),itens:sugerir(f),_sug:1};if(!state.dcm.itens.length)state.dcm.itens=[{...itBlank(),ss:f.ssom,area:f.areaOp||"",disc:f.disc??""}];state.v="cmn";render();window.scrollTo(0,0);};
 if($("#gce"))$("#gce").onclick=()=>{const f=FTS.find(x=>x.id===state.sel);state.dce={...ceVazio(),...progDe(f),ss:f.ssom,area:f.areaOp||"",disc:f.disc??""};state.v="cen";render();window.scrollTo(0,0);};
 const mv=(get,list,dir)=>{const o=get(state.sel);if(list===CM_ST&&dir>0&&o.status===0&&aprSt(o)!=="APROVADA"){toast("A CM precisa da aprovação do supervisor antes de ir para compras");return;}o.status+=dir;if(dir>0)o.hist.push([list[o.status],hojeISO(),quem()]);else o.hist.pop();persistRec(o);render();};
 if($("#advcm"))$("#advcm").onclick=()=>mv(cmFind,CM_ST,1);if($("#volcm"))$("#volcm").onclick=()=>mv(cmFind,CM_ST,-1);
 if($("#cest"))$("#cest").onchange=ev=>{const o=ceFind(state.sel);o.status=+ev.target.value;o.hist=o.hist||[];o.hist.push([CE_ST[o.status],hojeISO(),quem()]);persistRec(o);render();};if($("#advce"))$("#advce").onclick=()=>mv(ceFind,CE_ST,1);if($("#volce"))$("#volce").onclick=()=>mv(ceFind,CE_ST,-1);
 document.querySelectorAll("[data-sdcvf]").forEach(el=>{el.oninput=()=>uv(el);el.onchange=()=>{const o=cmFind(state.sel)||ceFind(state.sel)||FTS.find(x=>x.id===state.sel);o.sdcv=o.sdcv||{};o.sdcv[el.dataset.sdcvf]=uv(el);persistRec(o);render();};});
 document.querySelectorAll("[data-cef]").forEach(el=>el.onchange=()=>{const e=ceFind(state.sel);e[el.dataset.cef]=uv(el);persistRec(e);render();});
 const hdr=(d,val)=>{document.querySelectorAll("[data-h]").forEach(el=>{const h=ev=>{d[el.dataset.h]=el.dataset.n?pd(ev.target.value):uv(el);
   if(["tipo","linha","mes"].includes(el.dataset.h)){render();}else{const s=$("#sigla");if(s)s.textContent=siglaDe(d);val();}};el.oninput=h;el.onchange=h;});};
 if(state.v==="cmn"){const d=state.dcm,val=()=>{$("#valbox").innerHTML=alerts(cmValidar(d));};hdr(d,val);
  document.querySelectorAll("[data-r]").forEach(el=>{const i=+el.dataset.r,k=el.dataset.k;
   if(k==="area"||k==="disc"){el.onchange=()=>{d.itens[i][k]=k==="disc"?pd(el.value):el.value;val();};return;}
   el.oninput=()=>{d.itens[i][k]=uv(el);if(k!=="item"&&k!=="ss")val();};
   if(k==="item")el.onchange=()=>{const v=uv(el).trim();let m=matFind(v);if(!m&&v){const c=MATERIAIS.filter(x=>norm(x.desc).includes(norm(v)));if(c.length===1)m=c[0];}if(m){Object.assign(d.itens[i],{item:m.cod,desc:m.desc,un:m.un});if(d.itens[i].disc==="")d.itens[i].disc=m.disc;}else d.itens[i].item=v;autoRow(d.itens[i]);render();};
   if(k==="ss")el.onchange=()=>{d.itens[i].ss=uv(el);autoRow(d.itens[i]);render();};});
  document.querySelectorAll("[data-rm]").forEach(b=>b.onclick=()=>{d.itens.splice(+b.dataset.rm,1);if(!d.itens.length)d.itens.push(itBlank());render();});
  $("#addit").onclick=()=>{const l=d.itens[d.itens.length-1];d.itens.push({...itBlank(),ss:l?l.ss:"",area:l?l.area:""});render();};
  $("#sug").onclick=()=>{const f=d.itens.map(i=>ftsPorSS(i.ss)).find(Boolean);if(!f){toast("INFORME UMA SS QUE EXISTA NO BANCO DE FTS");return;}const s=sugerir(f).filter(n=>!d.itens.some(i=>i.ss===n.ss&&i.item===n.item));d.itens=d.itens.filter(i=>i.item||i.desc).concat(s);if(!d.itens.length)d.itens=[itBlank()];d._sug=1;toast(s.length+" ITEM(NS) SUGERIDO(S)");render();};
  $("#limparcm").onclick=()=>{state.dcm=null;render();};
  $("#salvarcm").onclick=async()=>{if(cmValidar(d).some(x=>x[0]==="bad")){toast("CORRIJA OS CAMPOS OBRIGATÓRIOS");return;}
   const o={...d,status:0,exemplo:false,itens:d.itens.filter(i=>i.item||i.desc),hist:[["RASCUNHO",hojeISO(),quem()]]};delete o._sug;const r=await criarCm(o);if(r.erro){dbErr(r.erro,"NÃO FOI POSSÍVEL SALVAR: "+(r.erro.message||""));return;}state.dcm=null;toast(r.id+" SALVA");openCm(r.id);};
  val();}
 if(state.v==="cen"){const d=state.dce,val=()=>{$("#valbox").innerHTML=alerts(ceValidar(d));};hdr(d,val);
  $("#limparce").onclick=()=>{state.dce=null;render();};
  $("#salvarce").onclick=async()=>{if(ceValidar(d).some(x=>x[0]==="bad")){toast("CORRIJA OS CAMPOS OBRIGATÓRIOS");return;}
   const r=await criarCe({...d,status:0,exemplo:false,hist:[["AGUARDANDO ENVIO",hojeISO(),quem()]]});if(r.erro){dbErr(r.erro,"NÃO FOI POSSÍVEL SALVAR: "+(r.erro.message||""));return;}state.dce=null;toast(r.id+" SALVO");openCe(r.id);};
  val();}
}
