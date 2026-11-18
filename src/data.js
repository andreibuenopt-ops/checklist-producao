const TIPOS=["Serviço Fixo","Serviço Periódico","Serviço Pontual","Serviços por Pacote"];
const CLASSIF=["Licitação Normal","Emergencial (autorização da gerência da planta)","Fornecedor exclusivo (fabricante ou autorizada)","Necessidade de único fornecedor (autorização da gerência)"];
const EPI_TEXTO=[
"A contratada, conforme a NR-6, deve fornecer gratuitamente aos seus colaboradores os EPIs necessários e adequados à execução dos serviços, dentro do prazo de validade e bem conservados, exigir o uso, substituí-los quando danificados ou extraviados e fazer a manutenção e higienização periódica.",
"A entrada na portaria só é liberada após verificação dos EPIs básicos: óculos de segurança, capacete, protetor auricular e sapato (bota) de segurança com biqueira de aço ou composite. Quem usa óculos de grau deve usar óculos de segurança com lentes graduadas ou de sobrepor.",
"Todo EPI deve possuir C.A. válido gravado de forma indelével. A contratada envia ao setor de contratação a cópia da lista de entrega de EPI, com C.A. e assinatura do colaborador.",
"NOTA 1 (altura): curso NR35 atualizado; cinto de segurança somente com talabarte duplo ou em Y com absorvedor de energia.",
"NOTA 2 (eletricidade): curso NR10 atualizado, ferramentas isoladas e vestimentas adequadas (capacete classe B, luvas de isolação classe 0, botina de eletricista, óculos e protetor sem partes metálicas, protetor facial e capuz balaclava risco 2, uniforme NR10 risco 2).",
"A não observância do uso dos EPIs será considerada falta GRAVE, com sanções que vão da retirada do colaborador da atividade até o impedimento de trabalhar nas unidades da Guararapes."
];
const SM_KW=[[/aleta/,["MAT-00101"]],[/motorredutor|motoredutor/,["MAT-00102","MAT-00108"]],[/corrente/,["MAT-00103","MAT-00104"]],[/mancal/,["MAT-00106","MAT-00107"]],[/correia|polia/,["MAT-00105"]],[/lubrific|graxa/,["MAT-00107","MAT-00108"]],[/bloqueio|loto/,["MAT-00115"]],[/inspe|limpeza/,["MAT-00113","MAT-00114"]]];
const MESES=["JANEIRO","FEVEREIRO","MARÇO","ABRIL","MAIO","JUNHO","JULHO","AGOSTO","SETEMBRO","OUTUBRO","NOVEMBRO","DEZEMBRO"];
const PROG=[{sg:"PS",nome:"PROGRAMAÇÃO SEMANAL"},{sg:"PM",nome:"PARADA MENSAL"},{sg:"PA",nome:"PARADA ANUAL"}];
const LINHAS=["MDF01","MDF02","MDF03","BP1","BP2","BP3","BP4","ACB01","ACB02","ACB03","MAD01","MAD02","MAD03","ETE"];
const CM_ST=["RASCUNHO","ENVIADA A COMPRAS","EM COMPRA","RECEBIDA"];
const CE_ST=["AGUARDANDO ENVIO","AGUARDANDO ORÇAMENTO","ORÇAMENTO EM APROVAÇÃO","EM PROCESSO DE COMPRAS","CONSERTO EM ANDAMENTO","RETORNO COM CONSERTO","RETORNO SEM CONSERTO","PROCESSO FINALIZADO","PROCESSO CANCELADO"];const ceAberto=e=>e.status<=4;const siglaCe=e=>e.ficha?"FICHA "+e.ficha:siglaDe(e);
const AREAS=[];const AREA_INFO={};const ccDe=a=>(AREA_INFO[a]&&AREA_INFO[a].cc)||"";const areaCurta=a=>String(a||"").split(" · ").slice(1).join(" · ")||a;const DISC=["ELÉTRICA","MECÂNICA","PRODUÇÃO","OUTROS"];const ESP_ORD=[1,0,2,3];const dOk=d=>Number.isInteger(d)&&d>=0&&d<DISC.length;const DONOS={};const donoDe=a=>DONOS[a]||"";
const FTS=[],MATERIAIS=[],FERRAMENTAS=[],CMS=[],CES=[],SDS=[];
const SETORES=["MECÂNICA","ELÉTRICA","PRODUÇÃO","OUTROS","PCM"],SETOR_DISC={"ELÉTRICA":0,"MECÂNICA":1,"PRODUÇÃO":2,"OUTROS":3};
const FUNCOES=["COORDENADOR","SUPERVISOR","DONO_AREA","EXECUTANTE","PCM"];
const MODS=["dashboard","fts","cm","ce","catalogo","fotos"],NIV=["SEM ACESSO","VER","EDITAR"];

function optAreas(v,ph,lista){const g={};(lista||AREAS).forEach(a=>{const l=(AREA_INFO[a]&&AREA_INFO[a].linha)||"OUTRAS";(g[l]=g[l]||[]).push(a);});
 const ord=[...LINHAS,"OUTRAS"].filter(l=>g[l]);
 return (ph?`<option value="">${ph}</option>`:"")+ord.map(l=>`<optgroup label="${l}">${g[l].map(a=>`<option value="${a.replace(/"/g,"&quot;")}" ${a===v?"selected":""}>${areaCurta(a)}${ccDe(a)?" · CC "+ccDe(a):""}</option>`).join("")}</optgroup>`).join("");}
const GCOR={ORG:[229,129,28],OLV:[95,122,46],BLK:[32,32,32],BEG:[247,244,238],ORGT:[253,236,214],ORGD:[196,98,8]};
function gHeader(doc,M,W,UW,y,title,id,first){
  const lw=first?26:13,lh=lw*110/160;
  try{doc.addImage(LOGO_PNG,"PNG",M,y,lw,lh);}catch(e){}
  const tx=M+lw+4;
  doc.setTextColor(32,32,32);doc.setFont("helvetica","bold");doc.setFontSize(first?16:10.5);
  doc.text(title,tx,y+(first?8.5:5.2));
  doc.setFont("helvetica","normal");doc.setFontSize(first?9:8);doc.setTextColor(196,98,8);
  doc.text("GUARARAPES · MANUTENÇÃO · PCM",tx,y+(first?14:8.6));
  doc.setFont("helvetica","bold");doc.setFontSize(first?10:8.5);doc.setTextColor(32,32,32);
  doc.text(String(id),W-M,y+(first?8.5:5.2),{align:"right"});
  const ry=y+lh+1.5;
  doc.setFillColor(229,129,28);doc.rect(M,ry,UW,first?1.3:0.9,"F");
  doc.setFillColor(95,122,46);doc.rect(M,ry+(first?1.3:0.9),UW,0.5,"F");
  return lh+1.5+(first?1.8:1.4)+3.5;
}
function gBar(doc,M,UW,y,t){
  doc.setFillColor(247,244,238);doc.rect(M,y,UW,6.5,"F");
  doc.setFillColor(229,129,28);doc.rect(M,y,1.8,6.5,"F");
  doc.setTextColor(32,32,32);doc.setFont("helvetica","bold");doc.setFontSize(9);doc.text(t,M+4.5,y+4.5);
}
function gFooter(doc,M,W,n){
  doc.setDrawColor(229,129,28);doc.setLineWidth(0.4);doc.line(M,288,W-M,288);
}

function espPerm(){if(!ME||ME.master||ME.funcao==="PCM")return ESP_ORD.slice();const d=dOk(ME.disc)?ME.disc:(SETOR_DISC[ME.setor]??null);return d==null?ESP_ORD.slice():[d];}
function optEsp(v,ph,lista){const l=[...(lista||ESP_ORD)];if(dOk(v)&&!l.includes(v))l.push(v);return (ph?`<option value="">${ph}</option>`:"")+l.map(i=>`<option value="${i}" ${v===i?"selected":""}>${DISC[i]}</option>`).join("");}
const espOk=d=>{const E=typeof escopo==="function"?escopo():{disc:null};if(E.disc!=null&&d!==E.disc)return false;return espOk0(d);};
const espOk0=d=>state.fd===""||state.fd===undefined||(state.fd==="N"?!dOk(d):d===+state.fd);
function guiaEsp(){const E=typeof escopo==="function"?escopo():{disc:null},fd=E.disc!=null?String(E.disc):(state.fd??"");return `<div class="tabs gui">${E.disc==null?`<button data-gd="" class="${fd===""?"on":""}">TODAS</button>`:""}${ESP_ORD.filter(i=>E.disc==null||i===E.disc).map(i=>`<button data-gd="${i}" class="${String(fd)===String(i)?"on":""}">${DISC[i]}</button>`).join("")}${E.disc==null?`<button data-gd="N" class="${fd==="N"?"on":""}">A DEFINIR</button>`:""}</div>`;}

const ESP_BG=[[75,82,96],[91,139,201],[95,122,46],[138,143,152]],ESP_FG=[[255,230,0],[57,255,20],[255,255,255],[255,255,255]];
