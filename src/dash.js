// ===== DASHBOARD e ÁREAS E DONOS =====
function dashFiltros(){const y=new Date().getFullYear();state.dy=state.dy||y;state.dd=state.dd??"";state.da=state.da||"";}
function escopo(){if(!ME||ME.master||ME.funcao==="PCM")return{disc:null,areas:null};
 let d=dOk(ME.disc)?ME.disc:(SETOR_DISC[ME.setor]??null);
 let ar=null;if(["DONO_AREA","EXECUTANTE"].includes(ME.funcao)){const m=AREAS.filter(a=>(EQUIPE[a]||[]).some(x=>x.pid===ME.id));if(m.length)ar=m;}
 return{disc:d,areas:ar};}
const scOk=(disc,area)=>{const E=escopo();return(E.disc==null||disc===E.disc)&&(!E.areas||E.areas.includes(area));};
const mOk=(disc,area)=>scOk(disc,area)&&(state.dd===""||disc===+state.dd)&&(!state.da||area===state.da);
function dashLinhas(){const L=[];CMS.forEach(c=>{const d=dataCompra(c);if(!d||+d.slice(0,4)!==+state.dy)return;c.itens.forEach(it=>{if(mOk(it.disc,it.area))L.push({d,c,it});});});return L.sort((a,b)=>b.d.localeCompare(a.d));}
function vDash(){dashFiltros();
 const L=dashLinhas(),h=hojeISO();
 const cmF=CMS.filter(c=>c.itens.some(i=>mOk(i.disc,i.area))),ceF=CES.filter(e=>mOk(e.disc,e.area));
 const kp={itens:L.length,aguard:cmF.filter(c=>c.status<=1).length,compra:cmF.filter(c=>c.status===2).length,rec:cmF.filter(c=>c.status===3).length,
  ceAb:ceF.filter(e=>ceAberto(e)).length,ceAtr:ceF.filter(e=>ceAberto(e)&&e.dtPrev&&e.dtPrev<h).length};
 const mes=MESES.map(m=>({m,n:[0,0,0,0],ou:0}));L.forEach(x=>{const o=mes[+x.d.slice(5,7)-1];if(dOk(x.it.disc))o.n[x.it.disc]++;else o.ou++;});
 const tot=o=>o.ou+o.n.reduce((a,b)=>a+b,0),mx=Math.max(1,...mes.map(tot)),hh=120;
 const bars=mes.map(o=>{const t=tot(o),sg=(n,c)=>n?`<div class="seg ${c}" style="height:${Math.max(16,n/mx*hh)}px">${n}</div>`:"";return `<div class="c"><div style="font-size:11px">${t||""}</div>${sg(o.ou,"")}${ESP_ORD.map(d=>sg(o.n[d],discCls(d))).join("")}<div style="margin-top:4px">${o.m.slice(0,3)}</div></div>`;}).join("");
 const pan=(d)=>{const ls=dashLinhas().filter(x=>x.it.disc===d),cs=CMS.filter(c=>c.itens.some(i=>i.disc===d&&scOk(i.disc,i.area)&&(!state.da||i.area===state.da))),es=CES.filter(e=>e.disc===d&&scOk(e.disc,e.area)&&(!state.da||e.area===state.da));
  return `<div class="dpanel ${discCls(d)}"><h3>${DISC[d]}</h3><div class="r"><span>ITENS COMPRADOS (${state.dy})</span><b>${ls.length}</b></div><div class="r"><span>CM EM ABERTO</span><b>${cs.filter(c=>c.status<3).length}</b></div><div class="r"><span>CE EM ABERTO</span><b>${es.filter(e=>ceAberto(e)).length}</b></div>
  <div style="margin-top:10px;font-weight:800">ÚLTIMAS COMPRAS</div>${ls.slice(0,4).map(x=>`<div class="r"><span>${fmtD(x.d)} · ${esc(x.it.desc)}</span><b>${esc(x.it.qtd)} ${esc(x.it.un)}</b></div>`).join("")||'<div class="r"><span>NENHUMA</span></div>'}</div>`;};
 const EC=escopo(),AV=EC.areas||AREAS;
 const ar=AV.map(a=>{const its=CMS.flatMap(c=>c.itens.filter(i=>i.area===a&&scOk(i.disc,i.area)&&(state.dd===""||i.disc===+state.dd)).map(i=>({c,i})));
  return `<div class="card res" data-area="${esc(a)}" style="${state.da===a?"border-color:var(--g6);box-shadow:0 0 0 2px #bfe3cd":""}"><h3>${esc(a)}</h3><div class="meta">DONO: <b>${esc(donoDe(a)||"A DEFINIR")}</b></div><div style="margin-top:6px"><span class="chip">${its.filter(x=>x.c.status<3).length} ITENS EM ABERTO</span><span class="chip">${CES.filter(e=>e.area===a&&ceAberto(e)&&scOk(e.disc,e.area)).length} CE EM CONSERTO</span></div></div>`;}).join("");
 const semArea=CMS.flatMap(c=>c.itens).filter(i=>!i.area&&scOk(i.disc,i.area)).length;
 const ceAb=CES.filter(e=>ceAberto(e)&&mOk(e.disc,e.area)).sort((a,b)=>(a.dtPrev||"9").localeCompare(b.dtPrev||"9"));
 const yrs=[...new Set([new Date().getFullYear(),...CMS.map(c=>+dataCompra(c).slice(0,4)||0).filter(Boolean)])].sort((a,b)=>b-a);
 return `<h2>DASHBOARD</h2><div class="sub">DATAS DAS COMPRAS, STATUS DAS CMs E CONSERTOS EXTERNOS.${EC.disc!=null||EC.areas?` <b>VISÃO: ${EC.disc!=null?DISC[EC.disc]:"TODAS AS ESPECIALIDADES"}${EC.areas?" · "+EC.areas.map(areaCurta).join(", "):""}</b>`:""}</div>
 <div class="card"><div class="fl"><select id="dy">${yrs.map(y=>`<option ${y===+state.dy?"selected":""}>${y}</option>`).join("")}</select>
 ${EC.disc!=null?"":`<select id="ddl"><option value="">TODAS AS ESPECIALIDADES</option>${DISC.map((d,i)=>`<option value="${i}" ${String(i)===String(state.dd)?"selected":""}>${d}</option>`).join("")}</select>`}
 <select id="dal"><option value="">TODAS AS ÁREAS</option>${optAreas(state.da,"",AV)}</select></div></div>
 <div class="kpis"><div class="kpi"><b>${kp.itens}</b><span>ITENS COMPRADOS EM ${state.dy}</span></div><div class="kpi"><b>${kp.aguard}</b><span>CM AGUARDANDO COMPRA</span></div><div class="kpi"><b>${kp.compra}</b><span>CM EM COMPRA</span></div><div class="kpi"><b>${kp.rec}</b><span>CM RECEBIDAS</span></div><div class="kpi"><b>${kp.ceAb}</b><span>CE EM CONSERTO</span></div><div class="kpi ${kp.ceAtr?"bad":""}"><b>${kp.ceAtr}</b><span>CE ATRASADOS</span></div></div>
 <div class="card"><b>COMPRAS POR MÊS (${state.dy})</b><div class="legend">${ESP_ORD.filter(d=>EC.disc==null||EC.disc===d).map(d=>`<span class="chip ${discCls(d)}">${DISC[d]}</span>`).join("")}</div><div class="bars">${bars}</div></div>
 <div class="row">${ESP_ORD.filter(d=>EC.disc==null||EC.disc===d).map(pan).join("")}</div>
 <h3 style="margin:18px 0 8px">ÁREAS E DONOS ${semArea?`<span class="chip warn">${semArea} ITEM(NS) SEM ÁREA</span>`:""}</h3><div class="areas">${ar}</div>
 <div class="card" style="margin-top:14px;overflow-x:auto"><b>DATAS DAS COMPRAS</b><table style="margin-top:8px"><tr><th>DATA DA COMPRA</th><th>CM / SIGLA</th><th>SS</th><th>ITEM</th><th>QTD</th><th>ESP.</th><th>ÁREA / DONO</th><th>SDCV</th><th>RECEBIDO EM</th><th>PRAZO</th></tr>
 ${L.map(({d,c,it})=>{const r=dataRec(c);return `<tr class="res-row" data-cm="${esc(c.id)}" style="cursor:pointer"><td><b>${fmtD(d)}</b></td><td>${esc(siglaDe(c))}</td><td>${esc(it.ss)}</td><td>${esc(it.item)} — ${esc(it.desc)}</td><td>${esc(it.qtd)} ${esc(it.un)}</td><td>${discChip(it.disc)}</td><td>${areaChip(it.area)}</td><td>${esc(c.sdcv&&c.sdcv.num||"—")}</td><td>${fmtD(r)}</td><td>${r?dias(d,r)+" DIA(S)":'<span class="chip warn">'+dias(d,h)+" DIA(S) EM ABERTO</span>"}</td></tr>`;}).join("")||'<tr><td colspan="10" class="meta">NENHUMA COMPRA COM ESSES FILTROS.</td></tr>'}</table></div>
 <div class="card" style="overflow-x:auto"><b>CONSERTOS EXTERNOS EM ABERTO</b><table style="margin-top:8px"><tr><th>CE</th><th>ITEM</th><th>ESP.</th><th>ÁREA / DONO</th><th>FORNECEDOR</th><th>ENVIADO EM</th><th>PREVISÃO</th><th>SITUAÇÃO</th></tr>
 ${ceAb.map(e=>{const atr=e.dtPrev&&e.dtPrev<h;return `<tr class="res-row" data-ce="${esc(e.id)}" style="cursor:pointer"><td><b>${esc(e.id)}</b></td><td>${esc(e.item)}</td><td>${discChip(e.disc)}</td><td>${areaChip(e.area)}</td><td>${esc(e.fornecedor||"—")}</td><td>${fmtD(e.dtEnvio)}</td><td>${fmtD(e.dtPrev)}</td><td>${atr?`<span class="chip bad">ATRASADO ${dias(e.dtPrev,h)} DIA(S)</span>`:'<span class="chip ok">NO PRAZO</span>'}</td></tr>`;}).join("")||'<tr><td colspan="8" class="meta">NENHUM CE EM ABERTO.</td></tr>'}</table></div>`;}
function vAreas(){
 const g={};AREAS.forEach(a=>{const l=(AREA_INFO[a]&&AREA_INFO[a].linha)||"OUTRAS";(g[l]=g[l]||[]).push(a);});
 const col=(eq,d,t)=>{const l=eq.filter(x=>d===null?(!dOk(x.disc)):x.disc===d);return `<div><div class="meta" style="font-weight:700">${t}</div>${l.map(x=>`<div style="font-size:13px;padding:2px 0">${esc(x.nome)} ${x.papel==="DONO"?'<span class="chip">DONO</span>':""}</div>`).join("")||'<div class="meta">—</div>'}</div>`;};
 return `<h2>ÁREAS E DONOS</h2><div class="sub">POR LINHA: ÁREAS INTERNAS, CENTRO DE CUSTO E EQUIPE (MECÂNICA / ELÉTRICA). O MASTER EDITA EM ADMINISTRAÇÃO.</div>`+
 ([...LINHAS,"OUTRAS"].filter(l=>g[l]).map(l=>`<h3 style="margin:16px 0 8px">${l}</h3><div class="areas">${g[l].map(a=>{const eq=EQUIPE[a]||[];return `<div class="card"><h3>${esc(areaCurta(a))}</h3><div class="meta">CENTRO DE CUSTO: <b>${esc(ccDe(a)||"A DEFINIR")}</b></div><div class="meta">DONO: <b>${esc(donoDe(a)||"A DEFINIR")}</b></div><div class="row" style="margin-top:8px;align-items:flex-start">${col(eq,1,"MECÂNICA")}${col(eq,0,"ELÉTRICA")}</div></div>`;}).join("")}</div>`).join("")||'<div class="meta">NENHUMA ÁREA CADASTRADA</div>');}
function bindDash(){
 if($("#dy"))$("#dy").onchange=e=>{state.dy=+e.target.value;render();};
 if($("#ddl"))$("#ddl").onchange=e=>{state.dd=e.target.value;render();};
 if($("#dal"))$("#dal").onchange=e=>{state.da=e.target.value;render();};
 document.querySelectorAll("[data-area]").forEach(c=>c.onclick=()=>{state.da=state.da===c.dataset.area?"":c.dataset.area;render();});
}
