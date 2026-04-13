from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

CATASTRO_URL = "https://ovc.catastro.meh.es/OVCServWeb/OVCWcfCallejero/COVCCallejero.svc/json/Consulta_DNPRC"

USOS = {
    'V': 'Residencial (vivienda)', 'C': 'Comercial', 'I': 'Industrial',
    'O': 'Oficinas', 'A': 'Agrario', 'T': 'Turístico', 'G': 'Ocio y hostelería',
    'Y': 'Sanidad y beneficencia', 'E': 'Cultural', 'R': 'Religioso',
    'M': 'Obras de urbanización', 'P': 'Vía pública', 'B': 'Almacén',
    'D': 'Deportivo', 'K': 'Singular',
}

HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Cambio de Uso</title>
  <style>
    :root{--bg:#f5f4f0;--card:#fff;--border:#e2e0d8;--text:#1a1a18;--muted:#6b6b66;--hint:#9e9e98;--green-bg:#eaf3de;--green-text:#3b6d11;--red-bg:#fcebeb;--red-text:#a32d2d;--blue-bg:#e6f1fb;--blue-text:#185fa5;--r:12px;--rs:8px}
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--text);min-height:100vh}
    .wrap{max-width:480px;margin:0 auto;padding:2rem 1.25rem 4rem}
    h1{font-size:26px;font-weight:600;letter-spacing:-.5px}
    .sub{font-size:14px;color:var(--muted);margin-top:4px}
    .hdr{margin-bottom:2rem}
    .card{background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:1.25rem;margin-bottom:1rem}
    label{display:block;font-size:13px;color:var(--muted);margin-bottom:6px;font-weight:500}
    input{width:100%;padding:12px 14px;font-size:16px;border:1.5px solid var(--border);border-radius:var(--rs);background:var(--bg);color:var(--text);outline:none;font-family:'SF Mono','Fira Code',monospace;letter-spacing:.05em}
    input:focus{border-color:#aaa}
    .btn{width:100%;padding:13px;font-size:16px;font-weight:600;background:var(--text);color:var(--card);border:none;border-radius:var(--rs);cursor:pointer;margin-top:10px}
    .btn:disabled{opacity:.4;cursor:not-allowed}
    .bdemo{width:100%;padding:11px;font-size:14px;color:var(--muted);background:transparent;border:1px dashed var(--border);border-radius:var(--rs);cursor:pointer;margin-top:.5rem}
    .rc{background:var(--card);border:1px solid var(--border);border-radius:var(--r);overflow:hidden;margin-top:1.5rem}
    .rh{padding:1.25rem;border-bottom:1px solid var(--border)}
    .rref{font-family:monospace;font-size:12px;color:var(--hint)}
    .radr{font-size:16px;font-weight:600;margin-top:4px;line-height:1.4}
    .badge{display:inline-block;margin-top:8px;font-size:12px;padding:4px 10px;border-radius:99px;background:var(--blue-bg);color:var(--blue-text);font-weight:500}
    .grid{display:grid;grid-template-columns:1fr 1fr}
    .met{padding:1rem 1.25rem;border-right:1px solid var(--border);border-bottom:1px solid var(--border)}
    .met:nth-child(even){border-right:none}
    .met:nth-last-child(-n+2){border-bottom:none}
    .ml{font-size:12px;color:var(--hint)}
    .mv{font-size:24px;font-weight:600;margin-top:2px}
    .mu{font-size:12px;color:var(--hint)}
    .calc{padding:1rem 1.25rem;border-bottom:1px solid var(--border)}
    .ct{font-size:12px;color:var(--hint);font-weight:500;letter-spacing:.05em;text-transform:uppercase;margin-bottom:10px}
    .step{display:flex;align-items:baseline;gap:10px;padding:3px 0;font-size:14px}
    .so{color:var(--hint);min-width:18px;font-family:monospace}
    .sd{color:var(--muted);flex:1}
    .sv{font-family:monospace;font-size:14px;font-weight:600}
    .verd{padding:1.25rem;display:flex;align-items:center;gap:14px}
    .verd.ok{background:var(--green-bg)}
    .verd.ko{background:var(--red-bg)}
    .vi{width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0;font-weight:700}
    .ok .vi{background:var(--green-text);color:#fff}
    .ko .vi{background:var(--red-text);color:#fff}
    .vt{font-size:16px;font-weight:600}
    .ok .vt{color:var(--green-text)}
    .ko .vt{color:var(--red-text)}
    .vs{font-size:13px;color:var(--muted);margin-top:3px}
    .ul{padding:1rem 1.25rem;border-top:1px solid var(--border)}
    .ut{font-size:12px;color:var(--hint);font-weight:500;letter-spacing:.05em;text-transform:uppercase;margin-bottom:10px}
    .ui{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid var(--border);font-size:14px}
    .ui:last-child{border-bottom:none}
    .uinfo{color:var(--muted);font-size:12px;margin-top:2px}
    .usup{font-family:monospace;font-weight:600}
    .ld{text-align:center;padding:2.5rem 1rem}
    .sp{width:30px;height:30px;border:2px solid var(--border);border-top-color:var(--text);border-radius:50%;animation:spin .8s linear infinite;margin:0 auto 14px}
    @keyframes spin{to{transform:rotate(360deg)}}
    .lt{font-size:14px;color:var(--muted)}
    .err{background:var(--red-bg);border:1px solid #f7c1c1;border-radius:var(--r);padding:1.25rem;margin-top:1.5rem}
    .et{font-size:15px;font-weight:600;color:var(--red-text)}
    .ed{font-size:13px;color:var(--muted);margin-top:6px}
  </style>
</head>
<body>
<div class="wrap">
  <div class="hdr"><h1>Cambio de uso</h1><p class="sub">Viabilidad según el Catastro</p></div>
  <div class="card">
    <label>Referencia catastral</label>
    <input id="ri" placeholder="ej. 9872023VH5797S0001WX" maxlength="20" autocomplete="off" autocorrect="off" autocapitalize="characters" spellcheck="false"/>
    <button class="btn" id="sb" onclick="buscar()">Consultar</button>
    <button class="bdemo" onclick="demo()">Usar ejemplo: 9872023VH5797S0001WX</button>
  </div>
  <div id="out"></div>
</div>
<script>
function buscar(){
  const ref=document.getElementById('ri').value.trim().toUpperCase().replace(/\s/g,'');
  if(ref.length<14){err('Referencia no válida','Introduce al menos 14 caracteres.');return;}
  call(ref);
}
function demo(){document.getElementById('ri').value='9872023VH5797S0001WX';call('9872023VH5797S0001WX');}
async function call(ref){
  document.getElementById('out').innerHTML='<div class="ld"><div class="sp"></div><p class="lt">Consultando el Catastro...</p></div>';
  document.getElementById('sb').disabled=true;
  try{
    const r=await fetch('/consulta?ref='+encodeURIComponent(ref));
    const d=await r.json();
    if(!r.ok){err('Error',d.error||'Error desconocido');return;}
    show(d);
  }catch(e){err('Error de conexión',e.message);}
  finally{document.getElementById('sb').disabled=false;}
}
function show(d){
  const v=d.viable;
  const us=d.unidades.map(u=>`<div class="ui"><div><div style="font-weight:500">${u.planta?'Planta '+u.planta:'Unidad'}${u.puerta?' · '+u.puerta:''}</div><div class="uinfo">${u.uso_texto}</div></div><div class="usup">${Math.round(u.superficie)} m²</div></div>`).join('');
  document.getElementById('out').innerHTML=`
  <div class="rc">
    <div class="rh"><div class="rref">${d.referencia}</div><div class="radr">${d.direccion||'Sin dirección'}</div><span class="badge">${d.uso_texto}</span></div>
    <div class="grid">
      <div class="met"><div class="ml">Superficie total</div><div class="mv">${Math.round(d.superficie_total)}</div><div class="mu">m²</div></div>
      <div class="met"><div class="ml">Unidades existentes</div><div class="mv">${d.n_unidades}</div></div>
      <div class="met"><div class="ml">Densidad máxima</div><div class="mv">${d.densidad.toFixed(1)}</div><div class="mu">sup ÷ 70</div></div>
      <div class="met"><div class="ml">Margen</div><div class="mv" style="color:${v?'var(--green-text)':'var(--red-text)'}">${d.margen>0?'+':''}${d.margen.toFixed(1)}</div></div>
    </div>
    <div class="calc">
      <div class="ct">Cálculo</div>
      <div class="step"><span class="so">1.</span><span class="sd">Superficie total</span><span class="sv">${Math.round(d.superficie_total)} m²</span></div>
      <div class="step"><span class="so">÷</span><span class="sd">Factor de densidad</span><span class="sv">70</span></div>
      <div class="step"><span class="so">=</span><span class="sd">Densidad máxima</span><span class="sv">${d.densidad.toFixed(2)} uds</span></div>
      <div class="step"><span class="so">−</span><span class="sd">Unidades existentes</span><span class="sv">${d.n_unidades}</span></div>
      <div class="step"><span class="so">=</span><span class="sd">Capacidad disponible</span><span class="sv" style="color:${v?'var(--green-text)':'var(--red-text)'}">${d.margen>0?'+':''}${d.margen.toFixed(2)}</span></div>
    </div>
    <div class="verd ${v?'ok':'ko'}">
      <div class="vi">${v?'✓':'✗'}</div>
      <div><div class="vt">${v?'Cambio de uso viable':'Cambio de uso no viable'}</div>
      <div class="vs">${v?'Capacidad disponible: '+d.margen.toFixed(1)+' unidades':'Déficit de '+Math.abs(d.margen).toFixed(1)+' unidades'}</div></div>
    </div>
    ${d.unidades.length>1?'<div class="ul"><div class="ut">Unidades del inmueble</div>'+us+'</div>':''}
  </div>`;
}
function err(t,m){document.getElementById('out').innerHTML=`<div class="err"><div class="et">${t}</div><div class="ed">${m}</div></div>`;}
</script>
</body>
</html>"""


@app.route('/', methods=['GET'])
def index():
    return Response(HTML, mimetype='text/html')


@app.route('/consulta', methods=['GET'])
def consulta():
    ref = request.args.get('ref', '').strip().upper().replace(' ', '')
    if len(ref) < 14:
        return jsonify({'error': 'Referencia catastral no válida. Debe tener al menos 14 caracteres.'}), 400

    try:
        r = requests.get(CATASTRO_URL, params={'RefCatastral': ref}, timeout=10)
        r.raise_for_status()
        data = r.json()
    except requests.exceptions.Timeout:
        return jsonify({'error': 'El Catastro tardó demasiado. Inténtalo de nuevo.'}), 504
    except Exception as e:
        return jsonify({'error': f'Error al conectar con el Catastro: {str(e)}'}), 502

    # El Catastro a veces devuelve una lista en el nivel raíz
    if isinstance(data, list):
        data = data[0] if data else {}

    resultado = data.get('consulta_dnprcResult', data)
    if isinstance(resultado, list):
        resultado = resultado[0] if resultado else {}

    lerr = resultado.get('lerr', {})
    if isinstance(lerr, list):
        lerr = lerr[0] if lerr else {}
    lerr = lerr.get('err', {}) if isinstance(lerr, dict) else {}
    if lerr:
        cod = lerr.get('cod', '') if isinstance(lerr, dict) else ''
        msg = lerr.get('msg', 'Error desconocido del Catastro') if isinstance(lerr, dict) else str(lerr)
        return jsonify({'error': f'Catastro: {msg} (código {cod})'}), 404

    lrcdnp = resultado.get('lrcdnp', {})
    if isinstance(lrcdnp, list):
        lrcdnp = lrcdnp[0] if lrcdnp else {}
    inmuebles_raw = lrcdnp.get('rcdnp', []) if isinstance(lrcdnp, dict) else []
    if not inmuebles_raw:
        return jsonify({'error': 'No se encontraron datos para esta referencia catastral.'}), 404

    if not isinstance(inmuebles_raw, list):
        inmuebles_raw = [inmuebles_raw]

    unidades = []
    for item in inmuebles_raw:
        rc = item.get('rc', {})
        debi = item.get('debi', {})
        dt = item.get('dt', {})
        locs = dt.get('locs', {}).get('lous', {}).get('lourb', {})
        dir_ = locs.get('dir', {})

        sup_str = debi.get('sfc') or debi.get('stot') or '0'
        try:
            sup = float(sup_str)
        except:
            sup = 0.0

        uso_cod = debi.get('luso', rc.get('co', '')).upper()
        ref_completa = (rc.get('pc1', '') + rc.get('pc2', '') + rc.get('car', '') +
                        rc.get('cc1', '') + rc.get('cc2', '')).strip()

        unidades.append({
            'referencia': ref_completa or ref,
            'uso_codigo': uso_cod,
            'uso_texto': USOS.get(uso_cod, uso_cod or 'Sin especificar'),
            'superficie': sup,
            'via': dir_.get('nv', ''),
            'numero': dir_.get('pnp', ''),
            'municipio': dt.get('nm', ''),
            'cp': locs.get('dp', ''),
            'planta': debi.get('npm', ''),
            'puerta': debi.get('snp', ''),
        })

    sup_total = sum(u['superficie'] for u in unidades)
    n_unidades = len(unidades)
    densidad = sup_total / 70
    margen = densidad - n_unidades
    viable = margen > 0

    u0 = unidades[0]
    direccion = ' '.join(filter(None, [u0['via'], u0['numero'], u0['municipio'], u0['cp']]))

    return jsonify({
        'referencia': u0['referencia'],
        'direccion': direccion,
        'uso_codigo': u0['uso_codigo'],
        'uso_texto': u0['uso_texto'],
        'superficie_total': round(sup_total, 2),
        'n_unidades': n_unidades,
        'densidad': round(densidad, 2),
        'margen': round(margen, 2),
        'viable': viable,
        'unidades': unidades,
    })


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
