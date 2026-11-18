const $=s=>document.querySelector(s);
const esc=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const norm=s=>String(s).normalize("NFD").replace(/[̀-ͯ]/g,"").toLowerCase();
const hl=(t,q)=>{t=String(t);if(!q)return esc(t);const i=norm(t).indexOf(norm(q));return i<0?esc(t):esc(t.slice(0,i))+"<mark>"+esc(t.slice(i,i+q.length))+"</mark>"+esc(t.slice(i+q.length));};
const toast=m=>{const t=$("#toast");t.textContent=m;t.classList.add("show");clearTimeout(toast.t);toast.t=setTimeout(()=>t.classList.remove("show"),2600);};
const state={v:"dash",at:"us",q:"",iq:"",sel:null,tab:"p1",draft:null};
const photos={};            // id -> [{id,cat,leg,data,w,h}]
let DL=null;                // capability de download
const CATS=["Antes","Durante","Depois","Local / equipamento","Documento"];


// ---- busca ----
function hits(f,q){const n=norm(q.trim());if(!n)return[];const h=[];
 if(norm(f.id).includes(n))h.push(["Código",f.id]);if(f.sdcv&&norm(f.sdcv.num||"").includes(n))h.push(["SDCV",f.sdcv.num]);if(norm(f.ssom).includes(n))h.push(["SS/OM",f.ssom]);
 if(norm(f.area+" "+f.linha).includes(n))h.push(["Área",f.linha+" · "+f.area]);if(norm(f.titulo).includes(n))h.push(["Título",f.titulo]);
 f.atividades.forEach(a=>{if(norm(a).includes(n))h.push(["Atividade",a]);});
 if(!f.exemplo||f.ferr.length<5)FERRAMENTAS.filter(t=>f.ferr.includes(t.cod)&&norm(t.cod+" "+t.desc).includes(n)).slice(0,1).forEach(t=>h.push(["Item",t.cod+" — "+t.desc]));
 return h;}
function vBuscaBase(){const q=state.q;const L=(q.trim()?FTS.map(f=>({f,h:hits(f,q)})).filter(x=>x.h.length):FTS.map(f=>({f,h:[]}))).filter(x=>espOk(x.f.disc));
 return `<h2>Buscar FTS</h2><div class="sub">Código da FTS, SS/OM, equipamento, atividade ou código/nome de um item.</div>
 <div class="card">${guiaEsp()}<input class="srch" id="q" placeholder="Ex.: 17057164 · SIFTER · motorredutor · FER-016" value="${esc(q)}" autofocus><div class="meta" style="margin-top:9px">${L.length} resultado(s) · ${FTS.length} FTS no banco</div></div>
 ${L.map(({f,h})=>`<div class="card res" data-id="${esc(f.id)}"><div style="display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap"><h3>${hl(f.id,q)}</h3><div><span class="chip ${f.status.startsWith("Aprov")?"ok":"warn"}">${esc(f.status)}</span>${f.sdcv&&f.sdcv.num?`<span class="chip ok">SDCV ${hl(f.sdcv.num,q)}</span>`:""}${f.exemplo?'<span class="chip ex">exemplo fictício</span>':""}</div></div>
 <div style="font-weight:600">${hl(f.titulo,q)}</div><div class="meta">SS/OM ${hl(f.ssom,q)} · ${esc(f.linha)} · ${hl(f.area,q)} · ${esc(f.periodo)}</div>
 <div style="margin-top:8px"><span class="chip">${esc(TIPOS[f.tipo])}</span><span class="chip">${f.atividades.length} atividade(s)</span>${aprChip(f)}${discChip(f.disc)}${areaChip(f.areaOp)}${f.alertas.length?`<span class="chip bad">${f.alertas.length} alerta(s)</span>`:""}</div>
 ${h.length?`<div class="meta" style="margin-top:6px">Encontrado em: ${h.slice(0,3).map(x=>`<b>${x[0]}</b> ${hl(x[1],q)}`).join(" · ")}</div>`:""}</div>`).join("")||'<div class="card meta">Nada encontrado.</div>'}`;}

// ---- detalhe ----
const pend=f=>{const p=[];if(!f.como.trim())p.push("“Como” não preenchido");if(!f.acomp.trim())p.push("Forma de acompanhamento não preenchida");if(!f.periodo||f.periodo==="A definir")p.push("Período não definido");return p;};
const cbl=(t,on)=>`<div class="cbl"><span class="cb ${on?"on":""}"></span><span>${esc(t)}</span></div>`;
const val=v=>v?esc(v):'<span class="empty">vazio</span>';
function pg1(f){return `<div class="sheet"><div class="sh-head"><span></span><span>FICHA TÉCNICA SERVIÇO – FTS</span><small>/${esc(f.linha.replace("-",""))}</small></div>
 <div class="sh-body"><span class="k meta" style="font-size:11px;font-weight:700">DATA PROGRAMADA PARA EXECUÇÃO</span><div class="sh-red">${esc(f.dataProg)}</div></div>
 <div class="sh-bar c">Descrição do serviço</div><div class="sh-yel">${esc(f.titulo)}</div>
 <div class="grid2"><div><span class="k">Linha</span>${esc(f.linha)}</div><div><span class="k">N. SS ou OM</span><span class="sh-red">${esc(f.ssom)}</span></div>
 <div><span class="k">Área</span>${esc(f.area)}</div><div><span class="k">N. Pedido</span>${val(f.pedido)}</div>
 <div><span class="k">Supervisor da área</span>${esc(f.sup)}</div><div><span class="k">N. NF envio</span>${val(f.nfEnvio)}</div>
 <div><span class="k">Planejador da linha</span>${esc(f.plan)}</div><div><span class="k">N. NF retorno</span>${val(f.nfRetorno)}</div></div>
 <div class="two" style="border-top:1px solid #dfe5e1"><div><div class="sh-bar c" style="margin:0 -0px">Tipo do serviço</div><div class="sh-body">${TIPOS.map((t,i)=>cbl(t,i===f.tipo)).join("")}</div></div>
 <div><div class="sh-bar c">Classificação do serviço</div><div class="sh-body">${CLASSIF.map((t,i)=>cbl(t,i===f.classif)).join("")}</div></div></div>
 <div class="sh-bar">Área solicitante: ${esc(f.solicitante)} — descrição detalhada do serviço a ser contratado</div>
 <div class="sh-body" style="background:#fffbd0"><b>${f.atividades.map(a=>"• "+esc(a)).join("<br>")}</b></div>
 <div class="sh-bar c">Sugestões de fornecedores (se houver)</div><div class="sh-body sh-red" style="text-align:center">${f.forn.map(esc).join(" · ")||"—"}</div>
 <div class="sh-bar c">Níveis de mão de obra, descrito abaixo</div><div class="sh-body"><b>${f.mo.map(m=>esc(m.q+" "+m.f)+` <span class="sh-red">[${esc(m.nr)}]</span>`).join("<br>")}</b><ul class="cl">${f.reqMO.map(r=>`<li>${esc(r)}</li>`).join("")}</ul></div>
 <div class="sh-bar c">Caixa de ferramentas padrão</div><div class="sh-body" style="text-align:center"><a href="#" data-t="ferr" class="lnk">Ver aba Ferramentas →</a></div>
 <div class="sh-bar c">EPI (equipamento de proteção individual)</div><div class="sh-body" style="text-align:center"><a href="#" data-t="epi" class="lnk">Ver aba EPIs →</a></div></div>`;}
function pg2(f){const o=(l)=>l.map(x=>cbl(x[0],x[1])).join("")||'<span class="meta">—</span>';
 return `<div class="sheet"><div class="sh-head"><span></span><span>FICHA TÉCNICA SERVIÇO – FTS · PÁG. 2</span><small>${esc(f.id)}</small></div>
 <div class="sh-bar">Descrição geral do serviço</div><div class="sh-body"><b>${esc(f.titulo)}</b></div>
 <div class="sh-bar">O que precisa</div><div class="sh-body">${esc(f.oQue)}</div>
 <div class="sh-bar">Como</div><div class="sh-body">${val(f.como)}</div>
 <div class="two"><div><div class="sh-bar">Obrigações da Guararapes</div><div class="sh-body">${o(f.obrG)}</div></div><div><div class="sh-bar">Obrigações da contratada</div><div class="sh-body">${o(f.obrC)}</div></div></div>
 <div class="sh-bar">Lista de EPIs e ferramentas</div><div class="sh-body">${f.epis.map(e=>cbl(e[0]+" — "+e[1],e[2])).join("")}</div>
 <div class="grid2"><div><span class="k">Período</span>${val(f.periodo)}</div><div><span class="k">Responsável técnico</span><b>${esc(f.rt)}</b></div><div style="grid-column:1/-1"><span class="k">Forma de acompanhamento</span>${val(f.acomp)}</div></div></div>`;}
function pgFerr(f){const q=state.fq||"";const L=FERRAMENTAS.filter(t=>f.ferr.includes(t.cod)&&(!q||norm(t.cod+" "+t.desc).includes(norm(q))));
 return `<div class="sheet"><div class="sh-head"><span></span><span>CAIXA DE FERRAMENTA PADRÃO</span><small>${L.length} itens</small></div><div class="sh-body"><input id="fq" placeholder="Filtrar ferramenta ou código…" value="${esc(q)}"><div class="two-l" style="margin-top:10px">${L.map(t=>`<div style="display:flex;gap:10px;padding:5px 0;border-bottom:1px solid #eef1ef"><b style="width:46px;color:var(--mut)">${esc(t.qtd)}</b><span style="flex:1">${hl(t.desc,q)}</span><span class="meta">${t.cod}</span></div>`).join("")}</div></div></div>`;}
function pgEpi(f){return `<div class="sheet"><div class="sh-head"><span></span><span>EPI – EQUIPAMENTO DE PROTEÇÃO INDIVIDUAL</span><small>NR-6</small></div><div class="sh-body">${EPI_TEXTO.map(t=>`<p style="margin:8px 0">${esc(t)}</p>`).join("")}</div></div>`;}
function pgVal(f){const p=pend(f);return (p.length?p.map(x=>`<div class="alert warn">⚠ ${esc(x)}</div>`).join(""):'<div class="alert ok">✔ Sem pendências de preenchimento.</div>')+f.alertas.map(a=>`<div class="alert ${a[0]}">${esc(a[1])}</div>`).join("");}
function vDetalhe(){const f=FTS.find(x=>x.id===state.sel);if(!f)return vBusca();const n=pend(f).length+f.alertas.length;const np=(photos[f.id]||[]).length;
 const tabs=[["p1","A.1 · FTS Pág. 1"],["p2","B.2 · FTS Pág. 2"],["ferr","C.3 · Ferramentas"],["epi","D.4 · EPIs"],["fotos","E.5 · Fotos dos trabalhos"+(np?` (${np})`:"")],["mat","Materiais / SDCV"+(sdNFts(f)?` (${sdNFts(f)})`:"")],["sdcv","SDCV"+(f.sdcv&&f.sdcv.num?" ✓":"")],["just","Justificativa técnica"],["copy","📋 Copiar tudo"],["val","Validação"]];
 const body={p1:pg1,p2:pg2,ferr:pgFerr,epi:pgEpi,fotos:pgFotos,mat:pgMat,sdcv:sdcvTab,just:x=>pgJust(x,"fts"),copy:x=>pgCopy(x,"fts"),val:pgVal}[state.tab](f);
 return `<button class="btn ghost sm" id="back">← Voltar</button>
 <div class="hero" style="margin-top:12px"><div class="code">${esc(f.id)} · SS/OM ${esc(f.ssom)}</div><h2>${esc(f.titulo)}</h2>
 <div style="margin-bottom:12px"><span class="chip">${esc(f.linha)} · ${esc(f.area)}</span><span class="chip">${esc(TIPOS[f.tipo])}</span><span class="chip">${esc(f.periodo)}</span><span class="chip">${esc(f.status)}</span>${f.sdcv&&f.sdcv.num?`<span class="chip">SDCV ${esc(f.sdcv.num)}</span>`:""}${f.exemplo?'<span class="chip">exemplo fictício</span>':""}</div>
 <div style="margin-bottom:12px">${discChip(f.disc)}${areaChip(f.areaOp)}${aprChip(f)}</div>
 <div class="act" style="margin-bottom:10px"><select id="fdisc" style="width:auto">${optEsp(f.disc,"— ESPECIALIDADE —",espPerm())}</select><select id="farea" style="width:auto">${optAreas(f.areaOp,"— ÁREA —")}</select></div>
 ${aprBox(f,"fts")}
 <div class="act"><button class="btn" id="pdf">👁 Visualizar / baixar PDF</button><button class="btn ghost" id="dup">Duplicar como nova FTS</button></div></div>
 <div class="tabs">${tabs.map(t=>`<button data-t="${t[0]}" class="${state.tab===t[0]?"on":""}">${t[1]}${t[0]==="val"&&n?`<span class="n">${n}</span>`:""}</button>`).join("")}</div>${body}`;}

// ---- nova FTS ----
function vNova(){const d=state.draft||{id:"",ssom:"",linha:"MDF02",disc:espPerm().length===1?espPerm()[0]:undefined,area:"",titulo:"",tipo:2,classif:0,periodo:"",sup:"",rt:"",como:"",acomp:"",atividades:"",mo:"",nr:""};
 const o=(a,v)=>a.map((x,i)=>`<option value="${i}" ${i===v?"selected":""}>${esc(x)}</option>`).join("");const os=(a,v)=>a.map(x=>`<option ${x===v?"selected":""}>${x}</option>`).join("");
 return `<h2>Nova FTS</h2><div class="sub">${d._dup?"Duplicada de "+esc(d._dup)+". Revise antes de salvar.":"Campos com <span class=\"rq\">*</span> são obrigatórios; o resto pode ser preenchido depois."}</div>
 <div class="card"><div class="row"><div><label>Código da FTS<span class="rq"> *</span></label><input data-f="id" value="${esc(d.id)}" placeholder="FTS-MDF2-XXXX-2027"></div><div><label>SS/OM<span class="rq"> *</span></label><input data-f="ssom" value="${esc(d.ssom)}"></div></div>
 <div class="row"><div><label>Linha<span class="rq"> *</span></label><select data-f="linha">${os(LINHAS,d.linha)}</select></div><div><label>Área / equipamento</label><input data-f="area" value="${esc(d.area)}"></div></div>
 <label>Especialidade<span class="rq"> *</span></label><select data-f="disc" data-n="1">${optEsp(d.disc,"— ESCOLHA A ESPECIALIDADE —",espPerm())}</select>
 <label>Título do serviço<span class="rq"> *</span></label><input data-f="titulo" value="${esc(d.titulo)}">
 <div class="row"><div><label>Tipo</label><select data-f="tipo" data-n="1">${o(TIPOS,d.tipo)}</select></div><div><label>Classificação</label><select data-f="classif" data-n="1">${o(CLASSIF,d.classif)}</select></div></div>
 <div class="row3"><div><label>Período</label><input data-f="periodo" value="${esc(d.periodo)}" placeholder="dd/mm a dd/mm/aaaa"></div><div><label>Supervisor</label><input data-f="sup" value="${esc(d.sup)}"></div><div><label>Responsável técnico</label><input data-f="rt" value="${esc(d.rt)}"></div></div>
 <label>Atividades (uma por linha)<span class="rq"> *</span></label><textarea data-f="atividades">${esc(d.atividades)}</textarea>
 <div class="row"><div><label>Mão de obra (ex.: 2 Mecânico ajustador)</label><input data-f="mo" value="${esc(d.mo)}"></div><div><label>NRs exigidas</label><input data-f="nr" value="${esc(d.nr)}" placeholder="NR11, NR12, NR35"></div></div>
 <label>Como (método de execução)</label><textarea data-f="como">${esc(d.como)}</textarea><label>Forma de acompanhamento</label><input data-f="acomp" value="${esc(d.acomp)}"></div>
 <div id="valbox"></div><div class="act"><button class="btn" id="salvar">Salvar no banco</button><button class="btn ghost" id="limpar">Limpar</button></div>`;}
function validar(d){const r=[],req={id:"Código",ssom:"SS/OM",titulo:"Título",linha:"Linha",atividades:"Atividades"};
 Object.keys(req).forEach(k=>{if(!String(d[k]??"").trim())r.push(["bad",req[k]+" obrigatório"]);});
 if(!dOk(d.disc))r.push(["bad","Especialidade obrigatória"]);else if(!espPerm().includes(d.disc))r.push(["bad","Você não pode abrir FTS de "+DISC[d.disc]+" (sua especialidade: "+espPerm().map(i=>DISC[i]).join(", ")+")"]);
 const t=norm((d.titulo||"")+" "+(d.atividades||"")),a=norm(d.area||""),nr=norm(d.nr||"");
 if(/andaime/.test(t)&&a&&!/(andaime|caldeira)/.test(a))r.push(["warn","Título/atividades falam de andaime, mas a área é “"+d.area+"”. Confira se o texto foi herdado de outra FTS."]);
 if(/andaime/.test(t)&&!/nr ?18/.test(nr))r.push(["warn","Serviço com andaime: considerar NR18."]);
 if(/(sifter|prensa|motorredutor|corrente|polia|correia)/.test(t)&&!/nr ?12/.test(nr))r.push(["warn","Máquina/equipamento mecânico: considerar NR12."]);
 if(/(tanque|silo|caldeira|interior|interna)/.test(t)&&!/nr ?33/.test(nr))r.push(["warn","Possível espaço confinado: considerar NR33."]);
 if(/(altura|andaime|telhado)/.test(t)&&!/nr ?35/.test(nr))r.push(["warn","Trabalho em altura: NR35 não listada."]);return r;}
const renderVal=()=>{const r=validar(state.draft||{});$("#valbox").innerHTML=r.length?r.map(x=>`<div class="alert ${x[0]}">${x[0]==="bad"?"✖":"⚠"} ${esc(x[1])}</div>`).join(""):'<div class="alert ok">✔ Tudo certo para salvar.</div>';};

// ---- PDF ----
async function baixarPdf(){const f=FTS.find(x=>x.id===state.sel);if(!window.jspdf){toast("Biblioteca de PDF não carregou");return;}
 const fl=await flatPhotos(f.id);
 const doc=buildPdf({...f,_just:justFts(f)},fl,FERRAMENTAS.filter(t=>f.ferr.includes(t.cod)),TIPOS,CLASSIF,EPI_TEXTO,window.jspdf);
 await saveDoc(doc,f.id+".pdf");}

// ---- fotos ----
function resize(file){return new Promise(res=>{const r=new FileReader();r.onload=()=>{const im=new Image();im.onload=()=>{const m=1280,s=Math.min(1,m/Math.max(im.width,im.height));const c=document.createElement("canvas");c.width=Math.round(im.width*s);c.height=Math.round(im.height*s);c.getContext("2d").drawImage(im,0,0,c.width,c.height);c.toBlob(async b=>{if(!b)return res(null);res({blob:b,data:await blob2url(b),w:c.width,h:c.height});},"image/jpeg",.72);};im.onerror=()=>res(null);im.src=r.result;};r.onerror=()=>res(null);r.readAsDataURL(file);});}
async function addFiles(files){const id=state.sel;if(!canEdit("fotos")){toast("Sem permissão para fotos");return;}photos[id]=photos[id]||[];let n=0;
 for(const fl of files){if(!/^image\//.test(fl.type))continue;const r=await resize(fl);if(!r)continue;const path=id+"/"+crypto.randomUUID()+".jpg";
  const up=await bucket().upload(path,r.blob,{contentType:"image/jpeg"});if(up.error){dbErr(up.error,"Falha no envio da foto");continue;}
  const ins=await SB.from("fotos").insert({registro:id,path,legenda:"",cat:"Durante",bytes:r.blob.size,w:r.w,h:r.h}).select().single();if(ins.error){dbErr(ins.error);continue;}
  photos[id].push({id:String(ins.data.id),path,cat:"Durante",leg:"",data:r.data,w:r.w,h:r.h,anot:[]});n++;}
 toast(n+" foto(s) enviada(s) · reduzidas automaticamente");render();}

// ---- render/bind ----
function render(){document.querySelectorAll("#nav button").forEach(b=>b.classList.toggle("on",b.dataset.v===state.v||({detalhe:"busca",cmd:"cm",cmn:"cm",ced:"ce",cen:"ce"})[state.v]===b.dataset.v));
 $("#main").className=["dash","areas","cm","ce","cmd","cmn","ced","cen","admin"].includes(state.v)?"up":"";
 $("#main").innerHTML=({busca:vBusca,detalhe:vDetalhe,nova:vNova,cat:vCat,dash:vDash,areas:vAreas,cm:vCm,ce:vCe,admin:vAdmin,cmd:vCmDet,cmn:vCmNova,ced:vCeDet,cen:vCeNovo})[state.v]();bind();}
const keep=(id,key)=>{const e=$(id);e.oninput=ev=>{state[key]=ev.target.value;const p=ev.target.selectionStart;render();const n=$(id);n.focus();n.setSelectionRange(p,p);};};
function open(id,tab){state.sel=id;state.tab=tab||"p1";state.v="detalhe";render();window.scrollTo(0,0);}
function bind(){
 if($("#q"))keep("#q","q");if($("#iq"))keep("#iq","iq");if($("#fq"))keep("#fq","fq");
 document.querySelectorAll(".res[data-id]").forEach(c=>c.onclick=()=>open(c.dataset.id));
 document.querySelectorAll("[data-go]").forEach(a=>a.onclick=e=>{e.preventDefault();open(a.dataset.go);});
 document.querySelectorAll(".tabs button").forEach(b=>b.onclick=()=>{state.tab=b.dataset.t;render();});
 document.querySelectorAll("a.lnk[data-t]").forEach(a=>a.onclick=e=>{e.preventDefault();state.tab=a.dataset.t;render();window.scrollTo(0,0);});
 if($("#back"))$("#back").onclick=()=>{state.v="busca";render();};
 if($("#pdf"))$("#pdf").onclick=baixarPdf;
 if($("#fdisc")){$("#fdisc").onchange=e=>{const f=FTS.find(x=>x.id===state.sel);f.disc=pd(e.target.value);persistRec(f);render();};$("#farea").onchange=e=>{const f=FTS.find(x=>x.id===state.sel);f.areaOp=e.target.value;persistRec(f);render();};}
 if($("#dup"))$("#dup").onclick=()=>{const f=FTS.find(x=>x.id===state.sel);state.draft={id:"",ssom:"",linha:f.linha,area:f.area,titulo:f.titulo,tipo:f.tipo,classif:f.classif,periodo:"",sup:f.sup,rt:f.rt,como:f.como,acomp:f.acomp,atividades:f.atividades.join("\n"),mo:f.mo.map(m=>m.q+" "+m.f).join("; "),nr:f.mo.map(m=>m.nr).join(", "),_dup:f.id};state.v="nova";render();};
 bindCm();bindSd();bindDash();bindAdmin();bindExtras();
 if(state.v==="nova"){document.querySelectorAll("[data-f]").forEach(el=>el.oninput=el.onchange=e=>{state.draft=state.draft||{linha:"MDF02",tipo:2,classif:0,disc:espPerm().length===1?espPerm()[0]:undefined};state.draft[el.dataset.f]=el.dataset.n?(e.target.value===""?undefined:+e.target.value):e.target.value;renderVal();});renderVal();
  $("#limpar").onclick=()=>{state.draft=null;render();};
  $("#salvar").onclick=()=>{const d=state.draft||{};if(validar(d).some(x=>x[0]==="bad")){toast("Corrija os campos obrigatórios");return;}if(FTS.some(f=>f.id===d.id)){toast("Código já existe");return;}
   const nf={id:d.id,ssom:d.ssom,pedido:"",nfEnvio:"",nfRetorno:"",linha:d.linha,area:d.area||"",dataProg:d.periodo||"",titulo:d.titulo.toUpperCase(),tipo:d.tipo??2,classif:d.classif??0,periodo:d.periodo||"A definir",sup:d.sup||"—",plan:"—",rt:d.rt||"",status:"Rascunho",exemplo:false,user:true,solicitante:"—",oQue:"",como:d.como||"",acomp:d.acomp||"",atividades:d.atividades.split("\n").filter(Boolean),mo:[{f:d.mo||"",q:"",nr:d.nr||""}],reqMO:[],forn:[],obrG:[],obrC:[],epis:[],alertas:[],ferr:[],disc:d.disc,areaOp:"",sdcv:{}};
   criarFts(nf).then(r=>{if(r.erro){dbErr(r.erro,"Não foi possível salvar: "+(r.erro.message||""));return;}state.draft=null;toast("FTS salva");open(nf.id);});};}
}
document.querySelectorAll("#nav button").forEach(b=>b.onclick=()=>{state.v=b.dataset.v;state.sel=null;render();window.scrollTo(0,0);});
(async()=>{try{if(window.claude&&claude.use)DL=await claude.use("downloads");}catch(e){DL=null;}})();
boot();
