from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import xml.etree.ElementTree as ET

app = Flask(__name__)
CORS(app)

CATASTRO_URL = "https://ovc.catastro.meh.es/OVCServWeb/OVCWcfCallejero/COVCCallejero.svc/json/Consulta_DNPRC"

USOS = {
    'V': 'Residencial (vivienda)',
    'C': 'Comercial',
    'I': 'Industrial',
    'O': 'Oficinas',
    'A': 'Agrario',
    'T': 'Turístico',
    'G': 'Ocio y hostelería',
    'Y': 'Sanidad y beneficencia',
    'E': 'Cultural',
    'R': 'Religioso',
    'M': 'Obras de urbanización',
    'P': 'Vía pública',
    'B': 'Almacén',
    'D': 'Deportivo',
    'K': 'Singular',
}

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
        return jsonify({'error': 'El Catastro tardó demasiado en responder. Inténtalo de nuevo.'}), 504
    except Exception as e:
        return jsonify({'error': f'Error al conectar con el Catastro: {str(e)}'}), 502

    # Check Catastro error
    lerr = data.get('consulta_dnprcResult', {}).get('lerr', {}).get('err', {})
    if lerr:
        cod = lerr.get('cod', '')
        msg = lerr.get('msg', 'Error desconocido del Catastro')
        return jsonify({'error': f'Catastro: {msg} (código {cod})'}), 404

    inmuebles_raw = data.get('consulta_dnprcResult', {}).get('lrcdnp', {}).get('rcdnp', [])
    if not inmuebles_raw:
        return jsonify({'error': 'No se encontraron datos para esta referencia catastral.'}), 404

    if not isinstance(inmuebles_raw, list):
        inmuebles_raw = [inmuebles_raw]

    # Parse each unit
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
        ref_completa = (rc.get('pc1','') + rc.get('pc2','') + rc.get('car','') +
                        rc.get('cc1','') + rc.get('cc2','')).strip()

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

    # Aggregate by uso
    sup_total = sum(u['superficie'] for u in unidades)
    n_unidades = len(unidades)
    densidad = sup_total / 70
    margen = densidad - n_unidades
    viable = margen > 0

    # Build address from first unit
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
