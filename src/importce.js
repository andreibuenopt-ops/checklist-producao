// ===== IMPORTAR PLANILHA DE CONSERTOS EXTERNOS (xlsx) =====
const IMP={buf:null,nomes:[],sheet:"",recs:[],info:null,msg:""};
const nrm=s=>String(s??"").normalize("NFD").replace(/[̀-ͯ]/g,"").toLowerCase().replace(/[^a-z0-9]/g,"");
const impLimpa=v=>{const s=String(v??"").trim();return /^[-–—]+$/.test(s)?"":s;};
function impData(v){const m=/^(\d{1,2})\/(\d{1,2})\/(\d{2,4})$/.exec(impLimpa(v));if(!m)return null;let [,d,mo,y]=m;y=y.length===2?"20"+y:y;d=+d;mo=+mo;if(mo<1||mo>12||d<1||d>31)return null;return y+"-"+String(mo).padStart(2,"0")+"-"+String(d).padStart(2,"0");}
function impLinha(raw){const s=String(raw||"").toUpperCase().replace(/\s+/g,"");let m=/^(?:PRENSA)?(MDF|MAD|ACB)0?([123])$/.exec(s);if(m)return m[1]+"0"+m[2];m=/^BP0?([1-4])$/.exec(s);if(m)return"BP"+m[1];return s==="ETE"?"ETE":null;}
function impStatus(v){const n=nrm(v);const i=CE_ST.findIndex(x=>nrm(x)===n);return i<0?0:i;}
function loadXlsx(){return new Promise((ok,no)=>{if(window.XLSX)return ok();const s=document.createElement("script");s.src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js";s.onload=ok;s.onerror=()=>no(new Error("Não foi possível carregar o leitor de planilhas"));document.head.appendChild(s);});}
function impAbrir(){const i=document.createElement("input");i.type="file";i.accept=".xlsx,.xlsm";i.onchange=async()=>{const f=i.files[0];if(!f)return;IMP.msg="LENDO A PLANILHA…";impModal();try{await loadXlsx();IMP.buf=await f.arrayBuffer();const wb=XLSX.read(IMP.buf,{type:"array",bookSheets:true});IMP.nomes=wb.SheetNames;const ok=IMP.nomes.filter(n=>/conserto|finalizados/i.test(n)&&!/\d{2}_\d{2}/.test(n));IMP.sheet=ok.find(n=>/^20\d\d/.test(n))||ok[0]||IMP.nomes[0];impParse();}catch(e){IMP.msg="ERRO: "+e.message;IMP.recs=[];IMP.info=null;}impModal();};i.click();}
function impParse(){IMP.recs=[];IMP.info=null;IMP.msg="";
 const wb=XLSX.read(IMP.buf,{type:"array",sheets:[IMP.sheet],cellDates:false});const ws=wb.Sheets[IMP.sheet];
 if(!ws){IMP.msg="ABA NÃO ENCONTRADA";return;}
 const rows=XLSX.utils.sheet_to_json(ws,{header:1,raw:false,dateNF:"dd/mm/yyyy",defval:""});
 let h=-1;for(let i=0;i<Math.min(rows.length,30);i++){const n=rows[i].map(nrm);if(n.includes("ficha")&&n.includes("ss")){h=i;break;}}
 if(h<0){IMP.msg="NÃO ACHEI A LINHA DE TÍTULOS (FICHA / SS) NESTA ABA. ESCOLHA OUTRA ABA.";return;}
 const hd=rows[h].map(nrm),C=k=>hd.indexOf(k),col={ficha:C("ficha"),nf:C("nf"),fu:C("datafollowup"),cte:C("cte"),compra:C("compra"),env:C("datadeenvio"),prev:C("dataprevistaentrega"),sit:C("situacaoatual"),resp:C("responsavel"),val:C("validada"),pcm:C("pcm"),item:C("item"),cad:C("cadastro"),desc:C("descricaoitem"),ret:C("retorno"),ss:C("ss"),area:C("area"),apl:C("aplicacao"),qtd:C("qtd"),apr:C("aprovadoratual"),tr:C("transport"),forn:C("fornecedor"),obs:C("observacoes")};
 const g=(r,k)=>col[k]<0?"":impLimpa(r[col[k]]);const cont={};let ign=0;
 rows.slice(h+1).forEach(r=>{const ficha=g(r,"ficha");if(!ficha){if(r.some(x=>String(x).trim()))ign++;return;}
  cont[ficha]=(cont[ficha]||0)+1;const id="CE-"+ficha.replace(/[^A-Za-z0-9]+/g,"-")+(cont[ficha]>1?"-"+cont[ficha]:"");
  const notas=[];const dt=(k,rot)=>{const v=g(r,k);if(!v)return null;const d=impData(v);if(!d)notas.push(rot+": "+v);return d;};
  const dEnv=dt("env","DATA DE ENVIO"),dPrev=dt("prev","PREVISÃO"),dFu=dt("fu","FOLLOW UP");
  const ob=g(r,"obs");const ym=/\/(\d{2})$/.exec(ficha);const area=g(r,"area"),q=parseFloat(g(r,"qtd").replace(",","."));
  IMP.recs.push({id,ficha,ss:g(r,"ss")||"-",item:g(r,"item")||"-",descricao:g(r,"desc")||"-",area_texto:area||null,linha:impLinha(area),ano:ym?2000+ +ym[1]:null,status:impStatus(g(r,"sit")),
   nf_envio:g(r,"nf")||null,cte:g(r,"cte")||null,compra:g(r,"compra")||null,dt_followup:dFu,dt_envio:dEnv,dt_prev:dPrev,validada:g(r,"val")||null,pcm:g(r,"pcm")||null,responsavel:g(r,"resp")||null,cadastro:g(r,"cad")||null,retorno:g(r,"ret")||null,aplicacao:g(r,"apl")||null,qtd:isFinite(q)?q:null,aprovador:g(r,"apr")||null,transportadora:g(r,"tr")||null,fornecedor:g(r,"forn")||null,obs:[ob,...notas].filter(Boolean).join(" | ")||null});});
 const ex=new Set(CES.map(e=>e.id)),st={};IMP.recs.forEach(x=>{st[CE_ST[x.status]]=(st[CE_ST[x.status]]||0)+1;});
 IMP.info={total:IMP.recs.length,novos:IMP.recs.filter(x=>!ex.has(x.id)).length,ign,st,semCol:Object.entries(col).filter(([k,v])=>v<0).map(([k])=>k)};}
function impModal(){let m=document.getElementById("impm");if(!m){m=document.createElement("div");m.id="impm";m.className="impm";document.body.appendChild(m);}
 const I=IMP.info;
 m.innerHTML=`<div class="impb"><div style="display:flex;justify-content:space-between;align-items:center"><h3 style="margin:0">📥 IMPORTAR PLANILHA DE CONSERTOS EXTERNOS</h3><button class="btn ghost sm" id="impx">FECHAR</button></div>
 ${IMP.msg?`<div class="card" style="margin-top:10px">${esc(IMP.msg)}</div>`:""}
 ${IMP.nomes.length?`<label style="margin-top:10px">ABA DA PLANILHA</label><select id="imps">${IMP.nomes.map(n=>`<option ${n===IMP.sheet?"selected":""}>${esc(n)}</option>`).join("")}</select>`:""}
 ${I?`<div class="card" style="margin-top:10px"><b>${I.total} LINHA(S) COM FICHA</b> · ${I.novos} NOVA(S) · ${I.total-I.novos} JÁ EXISTEM (SERÃO ATUALIZADAS)${I.ign?` · ${I.ign} IGNORADA(S) SEM FICHA`:""}
 <div class="meta" style="margin-top:6px">${Object.entries(I.st).map(([k,v])=>`${k}: <b>${v}</b>`).join(" · ")}</div>
 ${I.semCol.length?`<div class="meta" style="margin-top:6px">COLUNAS NÃO ENCONTRADAS: ${I.semCol.join(", ")}</div>`:""}
 <div class="meta" style="margin-top:6px">AO REIMPORTAR, OS CAMPOS DA PLANILHA SOBRESCREVEM OS DO APP. SDCV, FOTOS E HISTÓRICO SÃO MANTIDOS. ESPECIALIDADE E ÁREA INTERNA NÃO VÊM NA PLANILHA E FICAM PARA VOCÊ DEFINIR.</div></div>
 <div style="overflow-x:auto;margin-top:10px"><table class="itb"><tr><th>ID</th><th>SS</th><th>ITEM</th><th>DESCRIÇÃO</th><th>STATUS</th><th>ÁREA</th></tr>${IMP.recs.slice(0,6).map(x=>`<tr><td>${esc(x.id)}</td><td>${esc(x.ss)}</td><td>${esc(x.item)}</td><td>${esc(x.descricao.slice(0,50))}</td><td>${esc(CE_ST[x.status])}</td><td>${esc(x.area_texto||"—")}</td></tr>`).join("")}</table></div>
 <div class="act" style="margin-top:12px"><button class="btn" id="impgo" ${I.total?"":"disabled"}>IMPORTAR ${I.total} REGISTRO(S)</button></div>`:""}</div>`;
 m.querySelector("#impx").onclick=()=>m.remove();
 const s=m.querySelector("#imps");if(s)s.onchange=()=>{IMP.sheet=s.value;try{impParse();}catch(e){IMP.msg="ERRO: "+e.message;}impModal();};
 const go=m.querySelector("#impgo");if(go)go.onclick=async()=>{go.disabled=true;let n=0;for(let i=0;i<IMP.recs.length;i+=200){go.textContent="IMPORTANDO… "+n+"/"+IMP.recs.length;const r=await SB.from("ce").upsert(IMP.recs.slice(i,i+200),{onConflict:"id"});if(r.error){IMP.msg="ERRO NA IMPORTAÇÃO: "+r.error.message+" (JÁ IMPORTADOS: "+n+"). Se falar de coluna inexistente, rode o migracao7_ce_planilha.sql no Supabase.";impModal();return;}n+=Math.min(200,IMP.recs.length-i);}
  await loadAll();m.remove();state.es="";state.elim=0;render();toast(n+" registro(s) importado(s)");};}

// ===== CLASSIFICAR ESPECIALIDADE DOS CEs PELO RESPONSÁVEL =====
const tk=s=>String(s||"").normalize("NFD").replace(/[̀-ͯ]/g,"").toLowerCase().split(/[^a-z0-9]+/).filter(Boolean);
async function clsAbrir(){
 const r=await SB.from("perfis").select("nome,disc").eq("aprovado",true);if(r.error)return dbErr(r.error);
 const P=(r.data||[]).filter(p=>dOk(p.disc)).map(p=>({t:tk(p.nome),d:p.disc}));
 const g={};CES.filter(e=>!dOk(e.disc)).forEach(e=>{const k=(e.responsavel||"").trim();(g[k]=g[k]||[]).push(e.id);});
 const L=Object.entries(g).map(([k,ids])=>{const t=tk(k);let sug="";if(t.length){const c=P.filter(p=>t.every(x=>p.t.includes(x))).map(p=>p.d);if(c.length&&c.every(x=>x===c[0]))sug=c[0];}return{k,ids,sug};}).sort((a,b)=>b.ids.length-a.ids.length);
 const m=document.createElement("div");m.className="impm";document.body.appendChild(m);
 const total=CES.filter(e=>!dOk(e.disc)).length,ok=L.filter(x=>x.sug!=="").reduce((a,x)=>a+x.ids.length,0);
 m.innerHTML=`<div class="impb"><div style="display:flex;justify-content:space-between;align-items:center"><h3 style="margin:0">🧩 CLASSIFICAR ESPECIALIDADE DOS CEs</h3><button class="btn ghost sm" id="clx">FECHAR</button></div>
 <div class="card" style="margin-top:10px"><b>${total} CE(s) SEM ESPECIALIDADE</b> · ${ok} COM SUGESTÃO PELO NOME DO RESPONSÁVEL<div class="meta" style="margin-top:6px">A SUGESTÃO VEM DO CADASTRO DE USUÁRIOS (NOME + SETOR). CONFIRA E ESCOLHA PARA OS QUE FICARAM EM BRANCO. “— DEIXAR —” NÃO ALTERA.</div></div>
 <div style="overflow-x:auto;margin-top:10px"><table class="itb"><tr><th>RESPONSÁVEL (PLANILHA)</th><th>CEs</th><th>ESPECIALIDADE</th></tr>${L.map((x,i)=>`<tr><td>${esc(x.k||"(SEM RESPONSÁVEL)")}</td><td>${x.ids.length}</td><td><select data-cl="${i}">${optEsp(x.sug===""?undefined:x.sug,"— DEIXAR —")}</select></td></tr>`).join("")}</table></div>
 <div class="act" style="margin-top:12px"><button class="btn" id="clgo">APLICAR</button></div></div>`;
 m.querySelector("#clx").onclick=()=>m.remove();
 m.querySelector("#clgo").onclick=async e=>{const b=e.target;b.disabled=true;let n=0;
  for(const s of m.querySelectorAll("[data-cl]")){const v=s.value;if(v==="")continue;const x=L[+s.dataset.cl];
   for(let i=0;i<x.ids.length;i+=100){b.textContent="APLICANDO… "+n;const r=await SB.from("ce").update({disc:+v}).in("id",x.ids.slice(i,i+100));if(r.error){dbErr(r.error);b.disabled=false;return;}n+=Math.min(100,x.ids.length-i);}}
  await loadAll();m.remove();render();toast(n+" CE(s) classificado(s)");};}
