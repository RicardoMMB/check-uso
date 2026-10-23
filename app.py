from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import requests
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
CORS(app)

CATASTRO_URL = "https://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx/Consulta_DNPRC"

FACTOR_DENSIDAD = 70   # m2 por vivienda para calcular la densidad
M2_APARTAMENTO = 34    # m2 por apartamento de espacio unico

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
    input,select{width:100%;padding:12px 14px;font-size:16px;border:1.5px solid var(--border);border-radius:var(--rs);background:var(--bg);color:var(--text);outline:none}
    input{font-family:'SF Mono','Fira Code',monospace;letter-spacing:.05em}
    .gap{margin-top:14px}
    .btn{width:100%;padding:13px;font-size:16px;font-weight:600;background:var(--text);color:var(--card);border:none;border-radius:var(--rs);cursor:pointer;margin-top:14px}
    .btn:disabled{opacity:.4;cursor:not-allowed}
    .bdemo{width:100%;padding:11px;font-size:14px;color:var(--muted);background:transparent;border:1px dashed var(--border);border-radius:var(--rs);cursor:pointer;margin-top:.5rem}
    .rc{background:var(--card);border:1px solid var(--border);border-radius:var(--r);overflow:hidden;margin-top:1.5rem}
    .rh{padding:1.25rem;border-bottom:1px solid var(--border)}
    .rref{font-family:monospace;font-size:12px;color:var(--hint)}
    .radr{font-size:16px;font-weight:600;margin-top:4px;line-height:1.4}
    .badge{display:inline-block;margin-top:8px;font-size:12px;padding:4px 10px;border-radius:99px;background:var(--blue-bg);color:var(--blue-text);font-weight:500}
    .calc{padding:1rem 1.25rem;border-bottom:1px solid var(--border)}
    .ct{font-size:12px;color:var(--hint);font-weight:500;letter-spacing:.05em;text-transform:uppercase;margin-bottom:10px}
    .step{display:flex;align-items:baseline;gap:10px;padding:4px 0;font-size:14px}
    .so{color:var(--hint);min-width:18px;font-family:monospace}
    .sd{color:var(--muted);flex:1}
    .sv{font-family:monospace;font-size:14px;font-weight:600}
    .pass{color:var(--green-text)}
    .fail{color:var(--red-text)}
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
    <label>Referencia catastral del local (20 caracteres)</label>
    <input id="ri" placeholder="ej. 9872023VH5797S0001WX" maxlength="20" autocomplete="off" autocorrect="off" autocapitalize="characters" spellcheck="false"/>
    <label class="gap">¿El local da a una plaza o calle principal?</label>
    <select id="fa"><option value="0">No</option><option value="1">Sí</option></select>
    <button class="btn" id="sb" onclick="buscar()">Consultar</button>
    <button class="bdemo" onclick="demo()">Usar ejemplo: 9872023VH5797S0001WX</button>
  </div>
  <div id="out"></div>
</div>
<script>
function buscar(){
  const ref=document.getElementById('ri').value.trim().toUpperCase().replace(/\s/g,'');
  if(ref.length!==20){err('Referencia no válida','Introduce la referencia completa de 20 caracteres.');return;}
  call(ref);
}
function demo(){document.getElementById('ri').value='9872023VH5797S0001WX';call('9872023VH5797S0001WX');}
async function call(ref){
  document.getElementById('out').innerHTML='<div class="ld"><div class="sp"></div><p class="lt">Consultando el Catastro...</p></div>';
  document.getElementById('sb').disabled=true;
  const fa=document.getElementById('fa').value;
  try{
    const r=await fetch('/consulta?ref='+encodeURIComponent(ref)+'&fachada='+fa);
    const d=await r.json();
    if(!r.ok){err('Error',d.error||'Error desconocido');return;}
    show(d);
  }catch(e){err('Error de conexión',e.message);}
  finally{document.getElementById('sb').disabled=false;}
}
function chk(ok,titulo,detalle){
  return `<div class="step"><span class="so ${ok?'pass':'fail'}">${ok?'✓':'✗'}</span><span class="sd">${titulo}</span><span class="sv ${ok?'pass':'fail'}">${detalle}</span></div>`;
}
function show(d){
  const v=d.viable;
  const us=d.unidades.map(u=>`<div class="ui"><div><div style="font-weight:500">${u.planta?'Planta '+u.planta:'Unidad'}${u.puerta?' · '+u.puerta:''}</div><div class="uinfo">${u.uso_texto}</div></div><div class="usup">${Math.round(u.superficie)} m²</div></div>`).join('');
  const sg=d.margen>0?'+':'';
  document.getElementById('out').innerHTML=`
  <div class="rc">
    <div class="rh"><div class="rref">${d.referencia}</div><div class="radr">${d.direccion||'Sin dirección'}</div><span class="badge">${d.local_uso}</span></div>
    <div class="calc">
      <div class="ct">1. Densidad (viviendas)</div>
      <div class="step"><span class="so"></span><span class="sd">Superficie de viviendas</span><span class="sv">${Math.round(d.sup_viviendas)} m²</span></div>
      <div class="step"><span class="so">÷</span><span class="sd">Factor de densidad</span><span class="sv">${d.factor_densidad}</span></div>
      <div class="step"><span class="so">=</span><span class="sd">Densidad máxima</span><span class="sv">${d.densidad.toFixed(2)} uds</span></div>
      <div class="step"><span class="so">−</span><span class="sd">Viviendas existentes</span><span class="sv">${d.n_viviendas}</span></div>
      <div class="step"><span class="so">=</span><span class="sd">Capacidad disponible</span><span class="sv ${d.ok_densidad?'pass':'fail'}">${sg}${d.margen.toFixed(2)}</span></div>
    </div>
    <div class="calc">
      <div class="ct">Comprobaciones</div>
      ${chk(d.ok_densidad,'Densidad',d.ok_densidad?'Positiva':'Negativa')}
      ${chk(d.ok_planta,'Planta del local',d.planta_local?('Planta '+d.planta_local):'Sin dato')}
      ${chk(d.ok_fachada,'Fachada','Plaza/calle principal: '+(d.ok_fachada?'No':'Sí'))}
    </div>
    <div class="calc">
      <div class="ct">2. Apartamentos teóricos</div>
      <div class="step"><span class="so"></span><span class="sd">Superficie del local</span><span class="sv">${Math.round(d.sup_local)} m²</span></div>
      <div class="step"><span class="so">÷</span><span class="sd">m² por apartamento</span><span class="sv">${d.m2_apartamento}</span></div>
      <div class="step"><span class="so">=</span><span class="sd">Apartamentos de espacio único</span><span class="sv">${d.n_apartamentos}</span></div>
    </div>
    <div class="verd ${v?'ok':'ko'}">
      <div class="vi">${v?'✓':'✗'}</div>
      <div><div class="vt">${v?'Cambio de uso viable':'Cambio de uso no viable'}</div>
      <div class="vs">${v?('Hasta '+d.n_apartamentos+' apartamentos teóricos'):d.motivos.join(' · ')}</div></div>
    </div>
    ${d.unidades.length>1?'<div class="ul"><div class="ut">Unidades del inmueble</div>'+us+'</div>':''}
  </div>`;
}
function err(t,m){document.getElementById('out').innerHTML=`<div class="err"><div class="et">${t}</div><div class="ed">${m}</div></div>`;}
</script>
</body>
</html>"""


def es_vivienda(uso):
    u = (uso or '').upper()
    return 'VIVIENDA' in u or 'RESIDENCIAL' in u


def es_sotano(planta):
    p = (planta or '').strip().upper()
    return p.startswith('-') or p in ('SS', 'SM', 'ST', 'S')


def quitar_ns(root):
    """Elimina los espacios de nombres del XML para poder buscar etiquetas sencillas."""
    for el in root.iter():
        if '}' in el.tag:
            el.tag = el.tag.split('}', 1)[1]
    return root


def texto(el, ruta):
    n = el.find(ruta) if el is not None else None
    return (n.text or '').strip() if n is not None and n.text else ''


def pedir_catastro(rc):
    """Una consulta al Catastro. Devuelve (xml, error, codigo_http)."""
    try:
        r = requests.get(CATASTRO_URL, params={'Provincia': '', 'Municipio': '', 'RC': rc}, timeout=15)
        r.raise_for_status()
        root = quitar_ns(ET.fromstring(r.content))
    except requests.exceptions.Timeout:
        return None, 'El Catastro tardó demasiado. Inténtalo de nuevo.', 504
    except ET.ParseError:
        return None, 'El Catastro devolvió una respuesta que no se puede leer.', 502
    except Exception as e:
        return None, f'Error al conectar con el Catastro: {str(e)}', 502

    err = root.find('.//lerr/err')
    if err is not None:
        return None, f"Catastro: {texto(err, 'des')} (código {texto(err, 'cod')})", 404
    return root, None, 200


def detalle_unidad(rc):
    """Uso y superficie de una unidad (referencia de 20 caracteres)."""
    root, error, _ = pedir_catastro(rc)
    if error:
        return None
    debi = root.find('.//debi')
    if debi is None:
        return None
    try:
        sup = float(texto(debi, 'sfc').replace(',', '.') or 0)
    except ValueError:
        sup = 0.0
    return texto(debi, 'luso'), sup


def leer_unidades(rc_consulta):
    """Devuelve (lista_de_unidades, error, codigo_http)."""
    root, error, codigo = pedir_catastro(rc_consulta)
    if error:
        return None, error, codigo

    items = root.findall('.//lrcdnp/rcdnp') or root.findall('.//bico/bi')
    if not items:
        return None, 'No se encontraron datos para esta referencia catastral.', 404

    base = []
    for it in items:
        rc = it.find('.//rc')
        dt = it.find('.//dt')
        lourb = dt.find('.//lourb') if dt is not None else None
        base.append({
            'referencia': ''.join(texto(rc, c) for c in ('pc1', 'pc2', 'car', 'cc1', 'cc2')),
            'via': texto(lourb, 'dir/nv'),
            'numero': texto(lourb, 'dir/pnp'),
            'municipio': texto(dt, 'nm'),
            'cp': texto(lourb, 'dp'),
            'planta': texto(lourb, 'loint/pt'),
            'puerta': texto(lourb, 'loint/pu'),
        })

    # Uso y superficie de cada unidad: una consulta por referencia, en paralelo
    with ThreadPoolExecutor(max_workers=8) as ex:
        detalles = list(ex.map(detalle_unidad, [b['referencia'] for b in base]))

    fallos = sum(1 for d in detalles if d is None)
    if fallos:
        return None, f'No se pudieron leer los datos de {fallos} unidades del Catastro. Inténtalo de nuevo.', 502

    unidades = []
    for b, (uso, sup) in zip(base, detalles):
        b['uso_texto'] = uso or 'Sin especificar'
        b['es_vivienda'] = es_vivienda(uso)
        b['superficie'] = sup
        unidades.append(b)
    return unidades, None, 200


@app.route('/', methods=['GET'])
def index():
    return Response(HTML, mimetype='text/html')


@app.route('/consulta', methods=['GET'])
def consulta():
    ref = request.args.get('ref', '').strip().upper().replace(' ', '')
    fachada_principal = request.args.get('fachada', '0') == '1'

    if len(ref) != 20:
        return jsonify({'error': 'Referencia catastral no válida. Debe tener 20 caracteres.'}), 400

    # 1) Todas las unidades del inmueble (con los 14 primeros caracteres)
    unidades, error, codigo = leer_unidades(ref[:14])
    if error:
        return jsonify({'error': error}), codigo

    # 2) El local a cambiar de uso (la referencia completa)
    local = next((u for u in unidades if u['referencia'] == ref), None)
    if local is None:
        propias, error, codigo = leer_unidades(ref)
        if error:
            return jsonify({'error': error}), codigo
        local = propias[0]

    # Regla 1: densidad solo con viviendas
    viviendas = [u for u in unidades if u['es_vivienda']]
    sup_viviendas = sum(u['superficie'] for u in viviendas)
    n_viviendas = len(viviendas)
    densidad = sup_viviendas / FACTOR_DENSIDAD
    margen = densidad - n_viviendas
    ok_densidad = margen > 0

    # Regla 2: sotano o semisotano
    ok_planta = not es_sotano(local['planta'])

    # Regla 3: plaza o calle principal (la indica el usuario)
    ok_fachada = not fachada_principal

    # Resultado final: apartamentos teoricos de 34 m2
    n_apartamentos = int(local['superficie'] // M2_APARTAMENTO)

    motivos = []
    if not ok_densidad:
        motivos.append('Densidad negativa')
    if not ok_planta:
        motivos.append('Local en sótano o semisótano')
    if not ok_fachada:
        motivos.append('Da a plaza o calle principal')

    direccion = ' '.join(filter(None, [local['via'], local['numero'], local['municipio'], local['cp']]))

    return jsonify({
        'referencia': local['referencia'] or ref,
        'direccion': direccion,
        'local_uso': local['uso_texto'],
        'planta_local': local['planta'],
        'sup_local': round(local['superficie'], 2),
        'sup_viviendas': round(sup_viviendas, 2),
        'factor_densidad': FACTOR_DENSIDAD,
        'densidad': round(densidad, 2),
        'n_viviendas': n_viviendas,
        'margen': round(margen, 2),
        'm2_apartamento': M2_APARTAMENTO,
        'n_apartamentos': n_apartamentos,
        'ok_densidad': ok_densidad,
        'ok_planta': ok_planta,
        'ok_fachada': ok_fachada,
        'motivos': motivos,
        'viable': ok_densidad and ok_planta and ok_fachada,
        'unidades': unidades,
    })


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
