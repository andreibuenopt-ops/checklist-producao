// ===== EXTRAS: fotos com marcação · aprovação · justificativa · copiar · prévia de PDF =====
const nrs=t=>[...new Set((String(t).match(/NR[- ]?\d{1,2}/gi)||[]).map(x=>x.toUpperCase().replace(/[- ]/,"")))].sort((a,b)=>parseInt(a.slice(2))-parseInt(b.slice(2)));
const dtBR=s=>s?String(s).slice(0,10).split("-").reverse().join("/"):"—";

// ---------- copiar ----------
async function copiar(t){try{await navigator.clipboard.writeText(t);}catch(e){const a=document.createElement("textarea");a.value=t;a.style.position="fixed";a.style.opacity="0";document.body.appendChild(a);a.select();try{document.execCommand("copy");}catch(_){}a.remove();}toast("Copiado! Cole onde quiser.");}

// ---------- aprovação do supervisor ----------
const podeAprovar=()=>ME&&(ME.master||["SUPERVISOR","COORDENADOR"].includes(ME.funcao));
const aprSt=o=>(o.aprovacao&&o.aprovacao.status)||"";
const aprChip=o=>aprSt(o)==="APROVADA"?'<span class="chip ok">✔ APROVADA</span>':aprSt(o)==="REPROVADA"?'<span class="chip bad">✖ REPROVADA</span>':'<span class="chip warn">⏳ AGUARDA APROVAÇÃO</span>';
const aprTxt=o=>{const a=o.aprovacao||{};return aprSt(o)?`${aprSt(o)} por ${a.por} (mat. ${a.matricula}) em ${dtBR(a.em)}${a.obs?" — "+a.obs:""}`:"AGUARDANDO APROVAÇÃO DO SUPERVISOR";};
function aprBox(o,tab){const s=aprSt(o),a=o.aprovacao||{};
 return `<div class="apr ${s==="APROVADA"?"ok":s==="REPROVADA"?"bad":"wait"}"><div><b>${s==="APROVADA"?"✔ APROVADA PELO SUPERVISOR":s==="REPROVADA"?"✖ REPROVADA":"⏳ AGUARDANDO APROVAÇÃO DO SUPERVISOR"}</b>${s?`<div class="meta">${esc(a.por)} · ${dtBR(a.em)}${a.obs?" · "+esc(a.obs):""}</div>`:""}</div>${podeAprovar()?`<div class="act"><button class="btn" data-apr="1" data-tab="${tab}">✔ APROVAR</button><button class="btn red" data-apr="0" data-tab="${tab}">✖ REPROVAR</button></div>`:""}</div>`;}
async function aprovar(tab,id,ok){let obs="";if(!ok){obs=prompt("Motivo da reprovação:")||"";if(!obs)return;}
 const r=await SB.rpc("aprovar",{p_tab:tab,p_id:id,p_ok:ok,p_obs:obs});if(r.error)return dbErr(r.error,"Sem permissão para aprovar");await loadAll();toast(ok?"Aprovada":"Reprovada");render();}

// ---------- justificativa técnica (pronta para o gerente) ----------
const lst=a=>(a||[]).map(x=>"• "+x).join("\n");
function justFts(f){const J=f.just||{},al=f.atividades||[],per=f.dataProg||f.periodo||"a definir";
 const nr=nrs([...(f.mo||[]).map(m=>m.nr||""),...(f.reqMO||[]),...(f.epis||[]).map(e=>e[0])].join(" "));
 const kit=FERRAMENTAS.filter(t=>(f.ferr||[]).includes(t.cod));
 const mo=(f.mo||[]).map(m=>`${m.q||"—"}× ${m.f}${m.nr?" ("+m.nr+")":""}`);
 const L=[`JUSTIFICATIVA TÉCNICA — ${f.titulo}`,`SS/OM ${f.ssom} · ${f.linha} · ${f.area} · ${per}`,"",
 "1. OBJETO",`Solicita-se a autorização para execução do serviço "${f.titulo}", na área ${f.area} (${f.linha}), SS/OM ${f.ssom}, classificado como ${TIPOS[f.tipo]||"—"} (${CLASSIF[f.classif]||"—"}), programado para ${per}.`+(f.areaOp||dOk(f.disc)?` Especialidade: ${dOk(f.disc)?DISC[f.disc]:"a definir"}${f.areaOp?" · Área operacional: "+f.areaOp+(donoDe(f.areaOp)?" (dono: "+donoDe(f.areaOp)+")":""):""}.`:""),"",
 "2. ESCOPO DOS TRABALHOS",al.length?lst(al):"• A detalhar.",...(f.oQue?["",`Descrição: ${f.oQue}`]:[]),...(f.como?[`Forma de execução: ${f.como}`]:[]),"",
 "3. JUSTIFICATIVA TÉCNICA",
 ...(J.hist?[`Condição atual / histórico: ${J.hist}`,""]:[]),
 `A execução dos trabalhos acima, dentro da janela programada (${per}), visa preservar a confiabilidade, a disponibilidade e a segurança operacional do equipamento, aproveitando a janela planejada para intervir de forma organizada, com mão de obra, ferramental e materiais previamente dimensionados, em vez de depender de intervenções emergenciais durante a operação.`,"",
 `Consequência da não execução: ${J.conseq||"aumento do risco de falhas não planejadas e de parada emergencial, com perda de produção, maior custo de reparo e exposição das equipes a intervenções em condição não programada."}`,"",
 `Benefício esperado: ${J.benef||"redução do risco de falhas, maior previsibilidade da manutenção e manutenção das condições seguras de operação, dentro do planejamento aprovado."}`,"",
 "4. PLANEJAMENTO E RESPONSÁVEIS",`• Período: ${per}`,`• Responsável técnico: ${f.rt||"a definir"}`,`• Supervisor da área: ${f.sup||"a definir"}`,`• Planejador: ${f.plan||"a definir"}`,`• Solicitante: ${f.solicitante||"—"}`,...(f.acomp?[`• Acompanhamento: ${f.acomp}`]:[]),"",
 "5. RECURSOS",`• Mão de obra: ${mo.join("; ")||"a definir"}`,`• Ferramental: ${kit.length?kit.length+" item(ns) da caixa de ferramentas padrão (lista na aba C.3)":"conforme necessidade da atividade"}`,...((f.forn||[]).length?[`• Fornecedores homologados: ${f.forn.join(", ")}`]:[]),...((f.reqMO||[]).length?["• Requisitos da mão de obra:",...f.reqMO.map(x=>"   – "+x)]:[]),"",
 "6. SEGURANÇA E CONFORMIDADE",`• EPIs obrigatórios: ${(f.epis||[]).map(e=>e[0]).join(", ")||"conforme norma interna"}.`,...(nr.length?[`• Normas regulamentadoras aplicáveis aos trabalhos: ${nr.join(", ")}.`]:[]),"• Bloqueio e etiquetagem do equipamento, emissão de PT/RT e liberação da área antes do início, conforme procedimentos da planta.","",
 "7. CONCLUSÃO E SOLICITAÇÃO",`Diante do exposto, solicita-se a aprovação para execução do serviço conforme escopo, prazo e recursos acima descritos.`,`Situação da aprovação do supervisor: ${aprTxt(f)}.`];
 return L.join("\n");}
const MOTIVOS=["SUBSTITUIÇÃO POR DESGASTE","QUEBRA","ADEQUAÇÃO","MELHORIA","ESTOQUE CRÍTICO","NOVO PROJETO"];
const IMPACTO_PADRAO={"SUBSTITUIÇÃO POR DESGASTE":"A não aquisição mantém em operação componentes desgastados, com risco de falha não planejada, parada do equipamento, perda de produção e aumento de manutenção corretiva.","QUEBRA":"Sem o material, o equipamento permanece indisponível ou operando com restrição, com perda de produção e risco de agravamento do dano.","ADEQUAÇÃO":"Sem o material, a adequação fica pendente, mantendo risco de segurança e/ou de não conformidade no equipamento.","MELHORIA":"Sem o material, a melhoria não é implantada e permanecem as perdas e limitações atuais do equipamento.","ESTOQUE CRÍTICO":"Sem a reposição, o estoque fica abaixo do nível mínimo, com risco de não atender manutenções corretivas e de aumentar o tempo de parada.","NOVO PROJETO":"Sem o material, o projeto não avança e o cronograma de implantação fica comprometido."};
function justCm(c){const J=c.just||{},sig=siglaDe(c),ss=[...new Set(c.itens.map(i=>i.ss).filter(Boolean))],as=[...new Set(c.itens.map(i=>i.area).filter(Boolean))];
 const eq=[...new Set(c.itens.map(i=>i.equip).filter(Boolean))],fs=ss.map(x=>ftsPorSS(x)).filter(Boolean);
 const local=J.local||((eq.length?eq.join(" / "):"equipamento a definir")+(as.length?" — "+as.join(" / "):"")),
  ativ=J.atividade||(fs.length?fs.map(f=>f.titulo).join("; "):"atividade a definir"),
  mt=J.motivoTipo||"",mot=(mt?mt:"A DEFINIR")+(J.motivo?" — "+J.motivo:""),
  imp=J.impactos||J.conseq||IMPACTO_PADRAO[mt]||"Sem o material, o serviço não pode ser concluído na janela programada, com risco de adiamento, reprogramação e falhas não planejadas.";
 return [`FTCM (${sig}) ${ss.join(" / ")}`,"JUSTIFICATIVA TÉCNICA PARA UTILIZAÇÃO DOS MATERIAIS SOLICITADOS","",
 "1. LOCAL/EQUIPAMENTO ONDE O MATERIAL SERÁ APLICADO",local,"",
 "2. ATIVIDADE OU INTERVENÇÃO A SER REALIZADA",ativ,"",
 "3. MOTIVO DA SOLICITAÇÃO",mot,"",
 "4. IMPACTOS OPERACIONAIS E/OU RISCOS CASO O MATERIAL NÃO SEJA ADQUIRIDO",imp,"",
 "5. MATERIAIS SOLICITADOS",...c.itens.flatMap((i,n)=>[`Item ${n+1}`,`Solicitação de serviço: ${i.ss||"—"}`,`Equipamento: ${i.equip||"—"}`,`Modelo: ${i.modelo||"—"}`,`Item: ${i.item||i.desc||"—"}${i.item&&i.desc?" — "+i.desc:""}`,`Quantidade: ${i.qtd} ${i.un||"pç"}`,""]),
 "6. ÁREAS E RESPONSÁVEIS",...(as.length?as.map(a=>`• ${a}: ${donoDe(a)||"dono não cadastrado"}`):["• A definir"]),"",
 `Situação da aprovação do supervisor: ${aprTxt(c)}.`].join("\n");}
function pgJust(o,tipo){const J=o.just||{},fields=tipo==="fts"?[["hist","Condição atual / histórico do equipamento (opcional)"],["conseq","Consequência da não execução (substitui o texto padrão)"],["benef","Benefício esperado (substitui o texto padrão)"]]:[["local","1. Local/equipamento (vazio = automático dos itens)"],["atividade","2. Atividade ou intervenção (vazio = título da FTS da SS)"],["motivo","3. Motivo — detalhe (além do tipo escolhido)"],["impactos","4. Impactos operacionais e/ou riscos (vazio = texto padrão do motivo)"]];
 const txt=tipo==="fts"?justFts(o):justCm(o);
 return `<div class="card"><b>COMPLEMENTE (OPCIONAL)</b><div class="meta">O texto abaixo já sai completo. Preencha só se quiser personalizar.</div>${tipo==="fts"?"":`<label>3. Tipo do motivo</label><select data-jf="motivoTipo"><option value="">— ESCOLHA —</option>${MOTIVOS.map(m=>`<option ${J.motivoTipo===m?"selected":""}>${m}</option>`).join("")}</select>`}${fields.map(([k,l])=>`<label>${l}</label><textarea data-jf="${k}" rows="2">${esc(J[k]||"")}</textarea>`).join("")}</div>
 <div class="card"><div class="act"><button class="btn" id="cpj">📋 COPIAR JUSTIFICATIVA</button>${tipo==="fts"?"":`<button class="btn ghost" id="cpmail">📧 COPIAR E ABRIR E-MAIL</button>`}</div><textarea id="jtxt" readonly class="cptxt">${esc(txt)}</textarea></div>`;}

// ---------- texto completo para copiar ----------
function textoFts(f){const kit=FERRAMENTAS.filter(t=>(f.ferr||[]).includes(t.cod)),fo=(photos[f.id]||[]);
 return [`FICHA TÉCNICA DE SERVIÇO — ${f.id}`,`SS/OM: ${f.ssom}`,`Título: ${f.titulo}`,`Linha: ${f.linha} · Área/equipamento: ${f.area}`,`Especialidade: ${dOk(f.disc)?DISC[f.disc]:"a definir"} · Área operacional: ${f.areaOp||"a definir"}${f.areaOp&&donoDe(f.areaOp)?" · Dono: "+donoDe(f.areaOp):""}`,
 `Data programada: ${f.dataProg||f.periodo}`,`Tipo: ${TIPOS[f.tipo]||"—"} · Classificação: ${CLASSIF[f.classif]||"—"}`,`Supervisor: ${f.sup||"—"} · Planejador: ${f.plan||"—"} · RT: ${f.rt||"—"} · Solicitante: ${f.solicitante||"—"}`,
 `Pedido: ${f.pedido||"—"} · NF envio: ${f.nfEnvio||"—"} · NF retorno: ${f.nfRetorno||"—"}`,...(f.sdcv&&f.sdcv.num?[`SDCV: ${f.sdcv.num} · ${dtBR(f.sdcv.data)} · ${f.sdcv.resp||""}`]:[]),`Aprovação: ${aprTxt(f)}`,"",
 "ATIVIDADES",lst(f.atividades),"","O QUE: "+(f.oQue||"—"),"COMO: "+(f.como||"—"),"ACOMPANHAMENTO: "+(f.acomp||"—"),"",
 "MÃO DE OBRA",...(f.mo||[]).map(m=>`• ${m.q||"—"}× ${m.f} (${m.nr||"—"})`),"","REQUISITOS DA MÃO DE OBRA",lst(f.reqMO),"","FORNECEDORES",(f.forn||[]).join(", ")||"—","",
 "OBRIGAÇÕES GUARARAPES",...(f.obrG||[]).map(x=>`• ${x[0]}`),"","OBRIGAÇÕES DA CONTRATADA",...(f.obrC||[]).map(x=>`• ${x[0]}`),"","EPIs",...(f.epis||[]).map(e=>`• ${e[0]} — ${e[1]}`),"",
 `FERRAMENTAS (${kit.length})`,...kit.map(t=>`• ${t.cod} · ${t.qtd}× ${t.desc}`),"",`FOTOS (${fo.length})`,...fo.map((p,i)=>`${i+1}. [${p.cat}] ${p.leg||"sem legenda"}`),"","──────────","",justFts(f)].join("\n");}
function textoCm(c){const fo=photos[c.id]||[];return [`COMPRA DE MATERIAL — ${c.id}`,`Sigla: ${siglaDe(c)}`,`Programação: ${PROG[c.tipo].nome} · Linha ${c.linha}`,`Status: ${CM_ST[c.status]} · Comprada em: ${dtBR(dataCompra(c))} · Recebida em: ${dtBR(dataRec(c))}`,...(c.sdcv&&c.sdcv.num?[`SDCV: ${c.sdcv.num} · ${dtBR(c.sdcv.data)} · ${c.sdcv.resp||""}`]:[]),`Aprovação: ${aprTxt(c)}`,"","ITENS",
 ...c.itens.map((i,n)=>`${n+1}. SS ${i.ss} · ${i.item||"—"} · ${i.desc}${i.equip?" · EQUIP.: "+i.equip:""}${i.modelo?" · MODELO: "+i.modelo:""} · ${i.qtd} ${i.un||""} · ${i.area||"—"} (${donoDe(i.area)||"sem dono"}) · ${dOk(i.disc)?DISC[i.disc]:"—"}`),"","Observação: "+(c.obs||"—"),"","HISTÓRICO",...(c.hist||[]).map(h=>`• ${h[0]} — ${dtBR(h[1])} — ${h[2]}`),...(fo.length?["",`FOTOS (${fo.length})`,...fo.map((p,i)=>`${i+1}. ${p.leg||"sem legenda"}`)]:[]),"","──────────","",justCm(c)].join("\n");}
function textoCe(e){const fo=photos[e.id]||[];return [`CONSERTO EXTERNO — ${e.id}`,`SS: ${e.ss} · ${e.ficha?"Ficha":"Programação"}: ${siglaCe(e).replace("FICHA ","")}`,`Item: ${e.item} — ${e.desc}`,`Defeito/serviço: ${e.defeito||"—"}`,`Especialidade: ${dOk(e.disc)?DISC[e.disc]:"—"} · Área: ${e.area||"—"} (${donoDe(e.area)||"sem dono"})`,`Status: ${CE_ST[e.status]}`,
 `Fornecedor: ${e.fornecedor||"—"} · NF envio: ${e.nfEnvio||"—"} · Envio: ${dtBR(e.dtEnvio)} · Previsão: ${dtBR(e.dtPrev)} · NF retorno: ${e.nfRetorno||"—"} · Retorno: ${dtBR(e.dtRet)}`,`Valor orçado: ${brl(e.valor)}`,...(e.sdcv&&e.sdcv.num?[`SDCV: ${e.sdcv.num} · ${dtBR(e.sdcv.data)} · ${e.sdcv.resp||""}`]:[]),"Observação: "+(e.obs||"—"),"","HISTÓRICO",...(e.hist||[]).map(h=>`• ${h[0]} — ${dtBR(h[1])} — ${h[2]}`),...(fo.length?["",`FOTOS (${fo.length})`,...fo.map((p,i)=>`${i+1}. ${p.leg||"sem legenda"}`)]:[])].join("\n");}
function pgCopy(o,tipo){loadPhotos(o.id);const t=tipo==="fts"?textoFts(o):tipo==="cm"?textoCm(o):textoCe(o);
 return `<div class="card"><div class="act"><button class="btn" id="cpy">📋 COPIAR TUDO</button></div><div class="meta" style="margin:8px 0">Todas as informações em texto puro, prontas para colar em e-mail, sistema ou chat.</div><textarea id="cptxt" readonly class="cptxt">${esc(t)}</textarea></div>`;}

// ---------- fotos: câmera/galeria + marcação ----------
function desenha(ctx,W,H,S){const k=W/900;S.forEach(s=>{ctx.strokeStyle=ctx.fillStyle=s.c;ctx.lineWidth=s.w*k;ctx.lineCap=ctx.lineJoin="round";
 if(s.t==="pen"){ctx.beginPath();s.p.forEach((q,i)=>i?ctx.lineTo(q[0]*W,q[1]*H):ctx.moveTo(q[0]*W,q[1]*H));ctx.stroke();}
 else if(s.t==="arrow"){const x1=s.x1*W,y1=s.y1*H,x2=s.x2*W,y2=s.y2*H,a=Math.atan2(y2-y1,x2-x1),h=s.w*k*4+10;ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke();ctx.beginPath();ctx.moveTo(x2,y2);ctx.lineTo(x2-h*Math.cos(a-.45),y2-h*Math.sin(a-.45));ctx.lineTo(x2-h*Math.cos(a+.45),y2-h*Math.sin(a+.45));ctx.closePath();ctx.fill();}
 else if(s.t==="circle"){ctx.beginPath();ctx.ellipse((s.x1+s.x2)/2*W,(s.y1+s.y2)/2*H,Math.max(2,Math.abs(s.x2-s.x1)/2*W),Math.max(2,Math.abs(s.y2-s.y1)/2*H),0,0,7);ctx.stroke();}
 else if(s.t==="rect"){ctx.strokeRect(Math.min(s.x1,s.x2)*W,Math.min(s.y1,s.y2)*H,Math.abs(s.x2-s.x1)*W,Math.abs(s.y2-s.y1)*H);}
 else if(s.t==="text"){const fs=Math.round(W/22);ctx.font=`bold ${fs}px Inter,Arial,sans-serif`;ctx.lineWidth=fs/6;ctx.strokeStyle="#000";ctx.strokeText(s.s,s.x*W,s.y*H);ctx.fillText(s.s,s.x*W,s.y*H);}});}
const imgDe=src=>new Promise(r=>{const i=new Image();i.onload=()=>r(i);i.onerror=()=>r(null);i.src=src;});
async function flatten(p){if(!p.anot||!p.anot.length)return{data:p.data,w:p.w,h:p.h};const im=await imgDe(p.data);if(!im)return{data:p.data,w:p.w,h:p.h};const c=document.createElement("canvas");c.width=im.width;c.height=im.height;const x=c.getContext("2d");x.drawImage(im,0,0);desenha(x,c.width,c.height,p.anot);return{data:c.toDataURL("image/jpeg",.8),w:c.width,h:c.height};}
async function flatPhotos(id){await loadPhotos(id);return Promise.all((photos[id]||[]).map(async p=>({cat:p.cat,leg:p.leg,...(await flatten(p))})));}
const catSel=(p)=>`<select data-pc="${p.id}">${CATS.map(c=>`<option ${c===p.cat?"selected":""}>${c}</option>`).join("")}</select>`;
function pgFotos(f){loadPhotos(f.id);const L=photos[f.id]||[];
 return `<div class="sheet"><div class="sh-head"><span></span><span>E.5 · FOTOS DOS TRABALHOS</span><small>${L.length} FOTO(S)</small></div><div class="sh-body">
 <div class="act"><button class="btn" id="cam">📷 TIRAR FOTO</button><button class="btn ghost" id="gal">🖼 GALERIA</button></div>
 <input type="file" id="fcam" accept="image/*" capture="environment" style="display:none"><input type="file" id="fgal" accept="image/*" multiple style="display:none">
 <div class="meta" style="margin:8px 0 12px">Toque na foto para marcar com setas, círculos, retângulos e texto. As fotos são reduzidas automaticamente e saem no PDF com as marcações e a explicação.</div>
 <div class="photos">${L.map((p,i)=>`<div class="ph"><img src="${p.prev||p.data}" data-ed="${p.id}"><div><b>FOTO ${i+1}</b>${catSel(p)}<textarea data-pl="${p.id}" rows="3" placeholder="Explique o que a foto mostra…">${esc(p.leg)}</textarea><div class="act"><button class="btn sm" data-ed="${p.id}">✏️ MARCAR</button><button class="btn red sm" data-pd="${p.id}">REMOVER</button></div></div></div>`).join("")}</div>
 ${L.length?"":'<div class="meta">Nenhuma foto ainda.</div>'}</div></div>`;}
function lightbox(src){const l=document.createElement("div");l.className="lb";l.innerHTML=`<img src="${src}">`;l.onclick=()=>l.remove();document.body.appendChild(l);}
function editorFoto(rid,pid){const p=photos[rid].find(x=>x.id===pid);if(!p)return;const S=JSON.parse(JSON.stringify(p.anot||[]));let tool="arrow",cor="#ff2d2d",esp=5,cur=null,im=null;
 const m=document.createElement("div");m.className="edm";
 m.innerHTML=`<div class="edt"><div class="act">${[["arrow","↗ SETA"],["circle","◯ CÍRCULO"],["rect","▭ RETÂNGULO"],["pen","✎ LIVRE"],["text","T TEXTO"]].map(t=>`<button class="btn ghost sm tl" data-tl="${t[0]}">${t[1]}</button>`).join("")}</div>
 <div class="act">${["#ff2d2d","#ffe600","#39ff14","#ffffff","#111111"].map(c=>`<button class="cor" data-c="${c}" style="background:${c}"></button>`).join("")}<select id="esp"><option value="3">FINO</option><option value="5" selected>MÉDIO</option><option value="9">GROSSO</option></select><button class="btn ghost sm" id="und">↶ DESFAZER</button><button class="btn ghost sm" id="lmp">LIMPAR</button></div></div>
 <div class="edc"><canvas id="edcv"></canvas></div>
 <div class="edb"><label>EXPLICAÇÃO DA FOTO</label><textarea id="edl" rows="2">${esc(p.leg)}</textarea><div class="act" style="margin-top:8px"><button class="btn" id="eds">💾 SALVAR</button><button class="btn ghost" id="edx">CANCELAR</button></div></div>`;
 document.body.appendChild(m);const cv=m.querySelector("#edcv"),cx=cv.getContext("2d");
 const redraw=()=>{if(!im)return;cx.clearRect(0,0,cv.width,cv.height);cx.drawImage(im,0,0,cv.width,cv.height);desenha(cx,cv.width,cv.height,cur?S.concat([cur]):S);};
 imgDe(p.data).then(i=>{im=i;cv.width=i.width;cv.height=i.height;redraw();});
 const hl=()=>{m.querySelectorAll(".tl").forEach(b=>b.classList.toggle("on",b.dataset.tl===tool));m.querySelectorAll(".cor").forEach(b=>b.classList.toggle("on",b.dataset.c===cor));};hl();
 m.querySelectorAll(".tl").forEach(b=>b.onclick=()=>{tool=b.dataset.tl;hl();});m.querySelectorAll(".cor").forEach(b=>b.onclick=()=>{cor=b.dataset.c;hl();});
 m.querySelector("#esp").onchange=e=>esp=+e.target.value;m.querySelector("#und").onclick=()=>{S.pop();redraw();};m.querySelector("#lmp").onclick=()=>{S.length=0;redraw();};
 const pt=e=>{const r=cv.getBoundingClientRect();return[Math.min(1,Math.max(0,(e.clientX-r.left)/r.width)),Math.min(1,Math.max(0,(e.clientY-r.top)/r.height))];};
 cv.onpointerdown=e=>{e.preventDefault();cv.setPointerCapture(e.pointerId);const[x,y]=pt(e);
  if(tool==="text"){const t=prompt("Texto da marcação:");if(t){S.push({t:"text",x,y,s:t,c:cor,w:esp});redraw();}return;}
  cur=tool==="pen"?{t:"pen",p:[[x,y]],c:cor,w:esp}:{t:tool,x1:x,y1:y,x2:x,y2:y,c:cor,w:esp};};
 cv.onpointermove=e=>{if(!cur)return;const[x,y]=pt(e);if(cur.t==="pen")cur.p.push([x,y]);else{cur.x2=x;cur.y2=y;}redraw();};
 cv.onpointerup=()=>{if(!cur)return;const c=cur;cur=null;const tiny=c.t!=="pen"&&Math.abs(c.x2-c.x1)<.01&&Math.abs(c.y2-c.y1)<.01;if(!tiny)S.push(c);redraw();};
 m.querySelector("#edx").onclick=()=>m.remove();
 m.querySelector("#eds").onclick=async()=>{p.anot=S;p.leg=m.querySelector("#edl").value;p.prev=(await flatten(p)).data;await fotoUpd(p,{anot:S,legenda:p.leg});m.remove();toast("Foto salva");render();};}

// ---------- prévia do PDF na tela ----------
let _pdfUrl=null;
function saveDoc(doc,name){if(_pdfUrl)URL.revokeObjectURL(_pdfUrl);_pdfUrl=URL.createObjectURL(doc.output("blob"));
 const m=document.createElement("div");m.className="pvw";m.innerHTML=`<div class="pvh"><b>${esc(name)}</b><div class="act"><button class="btn" id="pvdl">⬇ BAIXAR PDF</button><a class="btn ghost" href="${_pdfUrl}" target="_blank" rel="noopener">ABRIR EM NOVA ABA</a><button class="btn ghost" id="pvx">✕ FECHAR</button></div></div><iframe src="${_pdfUrl}"></iframe>`;
 document.body.appendChild(m);m.querySelector("#pvx").onclick=()=>m.remove();
 m.querySelector("#pvdl").onclick=()=>{const a=document.createElement("a");a.href=_pdfUrl;a.download=name;document.body.appendChild(a);a.click();a.remove();toast("Download iniciado");};}

// ---------- ligações de eventos ----------
function bindExtras(){const Q=s=>document.querySelectorAll(s),id=()=>state.sel;
 Q("[data-apr]").forEach(b=>b.onclick=()=>aprovar(b.dataset.tab,id(),b.dataset.apr==="1"));
 if($("#cam")){$("#cam").onclick=()=>$("#fcam").click();$("#gal").onclick=()=>$("#fgal").click();$("#fcam").onchange=e=>addFiles([...e.target.files]);$("#fgal").onchange=e=>addFiles([...e.target.files]);}
 Q("[data-ed]").forEach(x=>x.onclick=()=>{const p=photos[id()].find(q=>q.id===x.dataset.ed);canEdit("fotos")?editorFoto(id(),x.dataset.ed):lightbox(p.prev||p.data);});
 const P=()=>photos[id()];
 Q("[data-pc]").forEach(s=>s.onchange=()=>{const p=P().find(p=>p.id===s.dataset.pc);p.cat=s.value;fotoUpd(p,{cat:s.value});});
 Q("[data-pl]").forEach(s=>s.oninput=()=>{const p=P().find(p=>p.id===s.dataset.pl);p.leg=s.value;clearTimeout(p._t);p._t=setTimeout(()=>fotoUpd(p,{legenda:s.value}),600);});
 Q("[data-pd]").forEach(b=>b.onclick=async()=>{if(!confirm("Remover esta foto?"))return;const p=P().find(p=>p.id===b.dataset.pd);await fotoDel(p);photos[id()]=P().filter(x=>x.id!==p.id);render();});
 if($("#cpy"))$("#cpy").onclick=()=>copiar($("#cptxt").value);
 if($("#cpj"))$("#cpj").onclick=()=>copiar($("#jtxt").value);if($("#cpmail"))$("#cpmail").onclick=()=>{const c=cmFind(id());copiar($("#jtxt").value);const ss=[...new Set(c.itens.map(i=>i.ss).filter(Boolean))].join(" / ");location.href="mailto:?subject="+encodeURIComponent("RES: FTCM ("+siglaDe(c)+") "+ss)+"&body="+encodeURIComponent("(Cole aqui a justificativa copiada: Ctrl+V)");};
 Q("[data-jf]").forEach(t=>t.oninput=t.onchange=()=>{const o=FTS.find(x=>x.id===id())||cmFind(id());if(!o)return;o.just=o.just||{};o.just[t.dataset.jf]=t.value;$("#jtxt").value=o.id.startsWith("CM-")?justCm(o):justFts(o);clearTimeout(o._jt);o._jt=setTimeout(()=>persistRec(o),700);});}
