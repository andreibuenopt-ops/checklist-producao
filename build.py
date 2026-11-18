import pathlib
S=pathlib.Path(__file__).parent/'src'
t=(S/'template.html').read_text(encoding='utf8')
import base64
LOGO='const LOGO_PNG="data:image/png;base64,'+base64.b64encode((pathlib.Path(__file__).parent/'assets'/'logo.png').read_bytes()).decode()+'";\n'
for k,f in [('/*CSS*/','style.css'),('/*DATA*/','data.js'),('/*PDF*/','pdf.js'),('/*PDFCM*/','pdfcm.js'),('/*CORE*/','core.js'),('/*CM*/','cm.js'),('/*DASH*/','dash.js'),('/*ADMIN*/','admin.js'),('/*EXTRAS*/','extras.js'),('/*IMPCE*/','importce.js'),('/*SDCV*/','sdcv.js'),('/*APP*/','app.js')]:
    t=t.replace(k,((LOGO if f=='data.js' else '')+(S/f).read_text(encoding='utf8')))
(pathlib.Path(__file__).parent/'index.html').write_text(t,encoding='utf8');print('index.html',len(t))
