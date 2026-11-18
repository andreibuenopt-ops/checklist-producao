// ===== SUPABASE · LOGIN · DADOS · FOTOS =====
const SB_URL="https://lhsdronznkidtntbdwik.supabase.co",SB_KEY="sb_publishable_PnsnkwezuevmSsEOwBgeog_TSIVX69V";
const SB=supabase.createClient(SB_URL,SB_KEY);
const emailDe=m=>String(m).trim().toLowerCase()+"@fts.guararapes.local";
let ME=null,PERM={};const EQUIPE={};
const lv=m=>PERM[m]||0,canEdit=m=>lv(m)>=2,quem=()=>ME?ME.nome:"VOCÊ";
const dn=v=>dOk(v)?v:null,set=(a,b)=>{a.length=0;a.push(...b);};
const dbErr=(e,msg)=>{console.error(e);toast(msg||"Erro ao salvar no banco");};
const byCod=(a,b)=>a.cod.localeCompare(b.cod),byId=(a,b)=>b.id.localeCompare(a.id);

// ---------- mapeamento banco <-> telas ----------
const FTS_DEF={pedido:"",nfEnvio:"",nfRetorno:"",linha:"",area:"",dataProg:"",titulo:"",tipo:2,classif:0,periodo:"A definir",sup:"—",plan:"—",rt:"",status:"Rascunho",solicitante:"—",oQue:"",como:"",acomp:"",atividades:[],mo:[],reqMO:[],forn:[],obrG:[],obrC:[],epis:[],alertas:[],ferr:[]};
const rowFts=r=>({...FTS_DEF,...Object.fromEntries(Object.entries(r.dados||{}).filter(([k,v])=>v!=null)),id:r.id,ssom:r.ss,disc:r.disc,areaOp:r.area_op||"",sdcv:r.sdcv||{},aprovacao:r.aprovacao||{},exemplo:false});
const ftsRow=f=>{const {disc,areaOp,sdcv,user,aprovacao,...dados}=f;return {id:f.id,ss:f.ssom,titulo:f.titulo,linha:f.linha,area_texto:f.area,data_prog:f.dataProg||"",disc:dn(disc),area_op:areaOp||null,atividades:f.atividades||[],ferramentas:f.ferr||[],dados,sdcv:sdcv||{}};};
const rowCe=r=>({id:r.id,ss:r.ss,item:r.item,desc:r.descricao,defeito:r.defeito||"",area:r.area||"",disc:r.disc,linha:r.linha||"",tipo:r.tipo??1,mes:r.mes??0,semana:r.semana??"",ano:r.ano,ficha:r.ficha||"",cte:r.cte||"",compra:r.compra||"",dtFollow:r.dt_followup||"",validada:r.validada||"",pcm:r.pcm||"",responsavel:r.responsavel||"",cadastro:r.cadastro||"",retorno:r.retorno||"",aplicacao:r.aplicacao||"",qtd:r.qtd??"",aprovador:r.aprovador||"",transportadora:r.transportadora||"",areaTexto:r.area_texto||"",fornecedor:r.fornecedor||"",nfEnvio:r.nf_envio||"",nfRetorno:r.nf_retorno||"",dtEnvio:r.dt_envio||"",dtPrev:r.dt_prev||"",dtRet:r.dt_ret||"",valor:r.valor??"",status:r.status,obs:r.obs||"",sdcv:r.sdcv||{},hist:r.hist||[],exemplo:false});
const ceRow=e=>({id:e.id,ss:e.ss,item:e.item,descricao:e.desc,defeito:e.defeito||"",area:e.area||null,disc:dn(e.disc),linha:e.linha,tipo:e.tipo,mes:e.tipo===0?null:(+e.mes||0),semana:e.tipo===0?(+e.semana||null):null,ano:+e.ano||null,ficha:e.ficha||null,cte:e.cte||null,compra:e.compra||null,dt_followup:e.dtFollow||null,validada:e.validada||null,pcm:e.pcm||null,responsavel:e.responsavel||null,cadastro:e.cadastro||null,retorno:e.retorno||null,aplicacao:e.aplicacao||null,qtd:e.qtd===""||e.qtd==null?null:+e.qtd,aprovador:e.aprovador||null,transportadora:e.transportadora||null,area_texto:e.areaTexto||null,fornecedor:e.fornecedor||null,nf_envio:e.nfEnvio||null,nf_retorno:e.nfRetorno||null,dt_envio:e.dtEnvio||null,dt_prev:e.dtPrev||null,dt_ret:e.dtRet||null,valor:e.valor===""||e.valor==null?null:+e.valor,status:e.status,obs:e.obs||null,sdcv:e.sdcv||{},hist:e.hist||[]});

async function loadAll(){
 const g=async(t,f)=>{const r=await SB.from(t).select(f||"*");if(r.error){console.error(t,r.error.message);return[];}return r.data;};
 const [ar,pa,fe,ma,ft,cm,ci,ce,sd]=await Promise.all([g("areas"),g("perfil_areas","area,papel,perfil_id,perfis(nome,disc)"),g("ferramentas"),g("materiais"),g("fts"),g("cm"),g("cm_itens"),g("ce"),g("sdcv")]);
 set(AREAS,ar.map(a=>a.nome).sort());Object.keys(AREA_INFO).forEach(k=>delete AREA_INFO[k]);ar.forEach(a=>AREA_INFO[a.nome]={linha:a.linha||"",cc:a.cc||""});
 Object.keys(DONOS).forEach(k=>delete DONOS[k]);Object.keys(EQUIPE).forEach(k=>delete EQUIPE[k]);
 pa.forEach(r=>{if(r.perfis)(EQUIPE[r.area]=EQUIPE[r.area]||[]).push({pid:r.perfil_id,nome:r.perfis.nome,disc:r.perfis.disc,papel:r.papel});});
 AREAS.forEach(a=>{const d=(EQUIPE[a]||[]).filter(x=>x.papel==="DONO");if(d.length)DONOS[a]=d.map(x=>x.nome+(dOk(x.disc)?" ("+DISC[x.disc].slice(0,3)+")":"")).join(" / ");});
 set(FERRAMENTAS,fe.map(r=>({cod:r.cod,qtd:r.qtd,desc:r.descricao})).sort(byCod));
 set(MATERIAIS,ma.map(r=>({cod:r.cod,desc:r.descricao,un:r.un||"",estoque:+r.estoque||0,disc:r.disc})).sort(byCod));
 set(FTS,ft.map(rowFts).sort((a,b)=>a.id.localeCompare(b.id)));
 const by={};ci.sort((a,b)=>a.id-b.id).forEach(i=>(by[i.cm_id]=by[i.cm_id]||[]).push({ss:i.ss,item:i.item||"",desc:i.descricao||"",un:i.un||"",qtd:+i.qtd,area:i.area||"",disc:i.disc,equip:i.equip||"",modelo:i.modelo||""}));
 set(CMS,cm.map(r=>({id:r.id,linha:r.linha,tipo:r.tipo,mes:r.mes??0,semana:r.semana??"",ano:r.ano,status:r.status,obs:r.obs||"",sdcv:r.sdcv||{},hist:r.hist||[],itens:by[r.id]||[],aprovacao:r.aprovacao||{},just:(r.dados||{}).just||{},exemplo:false})).sort(byId));
 set(CES,ce.map(rowCe).sort(byId));set(SDS,sd.map(rowSd));}

// ---------- gravação ----------
async function persistRec(o){let r;
 if(o.id.startsWith("CM-"))r=await SB.from("cm").update({status:o.status,hist:o.hist,sdcv:o.sdcv||{},obs:o.obs||"",dados:{just:o.just||{}}}).eq("id",o.id);
 else if(o.id.startsWith("CE-")){const x=ceRow(o);delete x.id;r=await SB.from("ce").update(x).eq("id",o.id);}
 else r=await SB.from("fts").update({disc:dn(o.disc),area_op:o.areaOp||null,sdcv:o.sdcv||{},dados:ftsRow(o).dados}).eq("id",o.id);
 if(r.error)dbErr(r.error,"Sem permissão ou erro ao salvar");}
const nextId=(p,l)=>p+"-"+String(Math.max(0,...l.map(x=>+x.id.slice(p.length+1)||0))+1).padStart(4,"0");
async function criarCm(d){for(let t=0;t<2;t++){const id=nextId("CM",CMS);
  const r=await SB.from("cm").insert({id,linha:d.linha,tipo:d.tipo,mes:d.tipo===0?null:+d.mes,semana:d.tipo===0?+d.semana:null,ano:+d.ano,status:0,obs:d.obs||null,sdcv:{},hist:d.hist});
  if(!r.error){const ri=await SB.from("cm_itens").insert(d.itens.map(i=>({cm_id:id,ss:i.ss,item:i.item||null,descricao:i.desc,un:i.un,qtd:+i.qtd,area:i.area||null,disc:dn(i.disc),equip:i.equip||null,modelo:i.modelo||null})));
   if(ri.error){await SB.from("cm").delete().eq("id",id);return{erro:ri.error};}await loadAll();return{id};}
  if(r.error.code!=="23505")return{erro:r.error};await loadAll();}return{erro:{message:"conflito de código, tente de novo"}};}
async function criarCe(d){for(let t=0;t<2;t++){const id=nextId("CE",CES),r=await SB.from("ce").insert({...ceRow({...d,id}),status:0});
  if(!r.error){await loadAll();return{id};}if(r.error.code!=="23505")return{erro:r.error};await loadAll();}return{erro:{message:"conflito de código, tente de novo"}};}
async function criarFts(f){const r=await SB.from("fts").insert(ftsRow(f));if(r.error)return{erro:r.error};await loadAll();return{id:f.id};}

// ---------- fotos (reduzidas no navegador, Storage privado) ----------
const bucket=()=>SB.storage.from("fotos");
const blob2url=b=>new Promise(r=>{const f=new FileReader();f.onload=()=>r(f.result);f.readAsDataURL(b);});
async function loadPhotos(id){if(photos[id])return;photos[id]=[];
 const r=await SB.from("fotos").select("*").eq("registro",id).order("id");if(r.error)return;
 const L=await Promise.all(r.data.map(async x=>{const d=await bucket().download(x.path);return d.data?{id:String(x.id),path:x.path,cat:x.cat||"Durante",leg:x.legenda||"",data:await blob2url(d.data),w:x.w,h:x.h,anot:x.anot||[]}:null;}));
 photos[id]=L.filter(Boolean);await Promise.all(photos[id].map(async p=>{if(p.anot.length)p.prev=(await flatten(p)).data;}));if(state.sel===id&&(state.tab==="fotos"||state.stab==="fotos"))render();}
const fotoUpd=(p,o)=>SB.from("fotos").update(o).eq("id",+p.id).then(r=>{if(r.error)dbErr(r.error);});
async function fotoDel(p){await bucket().remove([p.path]);const r=await SB.from("fotos").delete().eq("id",+p.id);if(r.error)dbErr(r.error);}

// ---------- somente leitura conforme permissão ----------
const MODV={busca:"fts",detalhe:"fts",nova:"fts",cm:"cm",cmd:"cm",cmn:"cm",ced:"ce",ce:"ce",cen:"ce",cat:"catalogo",dash:"dashboard"};
function applyRO(){const m=MODV[state.v],hide=s=>document.querySelectorAll(s).forEach(e=>e.style.display="none"),dis=s=>document.querySelectorAll(s).forEach(e=>e.disabled=true);
 if(m&&m!=="dashboard"&&!canEdit(m)){hide("#ncm,#nce,#gcm,#gce,#advcm,#volcm,#advce,#volce,#salvarcm,#salvarce,#salvar,#limpar,#dup,#addit,#sug,#limparcm,#limparce");dis("[data-sdcvf],[data-cef],#fdisc,#farea");}
 if(!canEdit("fotos")){hide("#cam,#gal,[data-pd],button[data-ed]");dis("[data-pc],[data-pl]");}}
const _render=render;render=function(){try{_render();applyRO();}catch(e){console.error(e);const m=document.querySelector("#main");if(m)m.insertAdjacentHTML("afterbegin",`<div class="card" style="border-color:#c0392b;background:#fdecea"><b>ERRO AO ABRIR ESTA TELA</b><div class="meta">${String(e&&e.message||e).replace(/</g,"&lt;")}</div></div>`);}};

// ---------- login ----------
const gate=h=>{$("#gate").style.display="grid";document.querySelector(".app").style.display="none";$("#gate").innerHTML=`<div class="gbox"><img src="assets/logo.png" class="glogo" alt="Guararapes"><h2>FTS MANAGER</h2>${h}</div>`;};
function telaLogin(msg){gate(`<div class="tabs"><button class="on" id="t1">ENTRAR</button><button id="t2">SOLICITAR CADASTRO</button></div><div id="gb"></div>${msg?`<div class="alert bad">${esc(msg)}</div>`:""}`);
 const f1=()=>{$("#gb").innerHTML=`<label>MATRÍCULA</label><input id="gm" inputmode="numeric" autocomplete="username"><label>SENHA</label><input id="gs" type="password" autocomplete="current-password"><div class="act" style="margin-top:14px"><button class="btn" id="gok">ENTRAR</button></div>`;
  const go=async()=>{$("#gok").disabled=true;const e=await entrar($("#gm").value,$("#gs").value);if(e){telaLogin(e);}};$("#gok").onclick=go;$("#gs").onkeydown=e=>{if(e.key==="Enter")go();};};
 const f2=()=>{$("#gb").innerHTML=`<div class="meta">O acesso só é liberado depois que o PCM/Master aprovar.</div><label>NOME COMPLETO</label><input id="rn"><label>E-MAIL GUARARAPES</label><input id="re" type="email"><label>MATRÍCULA</label><input id="rm" inputmode="numeric"><label>SENHA (6+ CARACTERES)</label><input id="rs" type="password"><div class="act" style="margin-top:14px"><button class="btn" id="rok">ENVIAR CADASTRO</button></div><div id="rmsg"></div>`;
  $("#rok").onclick=async()=>{const r=await fetch("/api/signup",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({nome:$("#rn").value,email:$("#re").value,matricula:$("#rm").value,senha:$("#rs").value})}).then(x=>x.json()).catch(()=>({erro:"Falha de conexão"}));
   $("#rmsg").innerHTML=r.erro?`<div class="alert bad">${esc(r.erro)}</div>`:'<div class="alert ok">Cadastro enviado. Aguarde a liberação do Master.</div>';};};
 $("#t1").onclick=()=>{$("#t1").classList.add("on");$("#t2").classList.remove("on");f1();};$("#t2").onclick=()=>{$("#t2").classList.add("on");$("#t1").classList.remove("on");f2();};f1();}
function telaTroca(){gate(`<div class="alert warn">Primeiro acesso: defina uma senha só sua.</div><label>NOVA SENHA</label><input id="n1" type="password"><label>CONFIRME</label><input id="n2" type="password"><div class="act" style="margin-top:14px"><button class="btn" id="nok">SALVAR SENHA</button></div><div id="nm"></div>`);
 $("#nok").onclick=async()=>{const a=$("#n1").value;if(a!==$("#n2").value||a.length<6){$("#nm").innerHTML='<div class="alert bad">As senhas devem ser iguais e ter 6+ caracteres.</div>';return;}
  if(a==="Guara@123"){$("#nm").innerHTML='<div class="alert bad">Escolha uma senha diferente da padrão.</div>';return;}
  const r=await SB.auth.updateUser({password:a});if(r.error){$("#nm").innerHTML=`<div class="alert bad">${esc(r.error.message)}</div>`;return;}
  await SB.rpc("senha_trocada");ME.trocar_senha=false;await abrir();};}
async function sair(){await SB.auth.signOut();ME=null;PERM={};telaLogin();}
async function entrar(mat,senha){const r=await SB.auth.signInWithPassword({email:emailDe(mat),password:senha});if(r.error)return"Matrícula ou senha inválida.";return await iniciar(r.data.user.id);}
async function iniciar(uid){const p=await SB.from("perfis").select("*").eq("id",uid).maybeSingle();
 if(p.error||!p.data){gate(`<div class="alert bad">Seu usuário ainda não tem perfil. Peça ao Master.</div><button class="btn" id="so">SAIR</button>`);$("#so").onclick=sair;return null;}
 ME=p.data;
 if(!ME.ativo||!ME.aprovado){gate(`<div class="alert warn">${ME.ativo?"Seu cadastro ainda não foi liberado pelo Master.":"Usuário desativado."}</div><button class="btn" id="so">SAIR</button>`);$("#so").onclick=sair;return null;}
 const pm=await SB.from("permissoes").select("*").eq("perfil_id",uid);PERM={};MODS.forEach(m=>PERM[m]=ME.master?2:0);if(!ME.master)(pm.data||[]).forEach(x=>PERM[x.modulo]=x.nivel);
 if(ME.trocar_senha){telaTroca();return null;}
 await abrir();return null;}
async function abrir(){await loadAll();$("#gate").style.display="none";document.querySelector(".app").style.display="flex";
 const need={dash:"dashboard",busca:"fts",nova:"fts",cm:"cm",ce:"ce",cat:"catalogo",areas:"dashboard"};
 document.querySelectorAll("#nav button").forEach(b=>{const v=b.dataset.v;b.style.display=v==="admin"?(ME.master?"":"none"):(lv(need[v])>=(v==="nova"?2:1)?"":"none");});
 $("#who").innerHTML=`<b>${esc(ME.nome)}</b><br>${esc(ME.funcao)} · ${esc(ME.matricula)}`;
 const first=["dash","busca","cm","ce","cat"].find(v=>lv(need[v])>=1)||"areas";state.v=first;state.sel=null;render();}
async function boot(){$("#sair").onclick=sair;const s=await SB.auth.getSession();if(s.data.session)await iniciar(s.data.session.user.id);else telaLogin();}
