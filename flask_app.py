from flask import Flask, request, jsonify, send_from_directory
import requests
import re

app = Flask(__name__)

TIPOS_DOCUMENTO = {
    "1": "CI Uruguay",
    "3": "DNI Argentina",
    "4": "RG Brasil",
    "5": "CPF Brasil",
    "6": "CI Paraguay",
    "7": "Pasaporte"
}

def limpiar_html(texto):
    texto_limpio = re.sub(r'<.*?>', '', texto)
    html_entities = {
        '&aacute;': 'á', '&eacute;': 'é', '&iacute;': 'í',
        '&oacute;': 'ó', '&uacute;': 'ú', '&nbsp;': ' ',
        '&ntilde;': 'ñ', '&uuml;': 'ü', '&quot;': '"',
        '&#39;': "'", '&lt;': '<', '&gt;': '>',
        '&amp;': '&'
    }
    for ent, char in html_entities.items():
        texto_limpio = texto_limpio.replace(ent, char)
    return texto_limpio.strip()

def obtener_color_titulo(titulo):
    # No se puede enviar colores a front, lo omitimos o enviamos texto plano
    titulo_lower = titulo.lower()
    if "beneficiario" in titulo_lower and "no" not in titulo_lower:
        return "green"
    elif "no beneficiario" in titulo_lower:
        return "red"
    else:
        return "yellow"

@app.route('/')
@app.route('/index.html')
def index():
    # Sirve el archivo index.html que esté en la misma carpeta que app.py
    return send_from_directory('.', 'index.html')

@app.route('/consultar_beca', methods=['POST'])
def consultar_beca():
    data = request.json
    documento = data.get('documento')
    tipo_doc = data.get('tipo_doc')

    if documento is None or tipo_doc is None:
        return jsonify({"error": "Faltan parámetros"}), 400

    url = 'https://becas.mec.gub.uy/ConsultarBecas/controller.php'
    payload = {
        'accion': 'consultar',
        'documento': documento,
        'cboTDoc': tipo_doc
    }

    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        resultado = response.json()

        titulo = resultado.get('titulo', '').strip()
        mensaje_raw = resultado.get('mensaje', '')
        mensaje = limpiar_html(mensaje_raw)

        color_titulo = obtener_color_titulo(titulo)

        return jsonify({
            "documento": documento,
            "titulo": titulo,
            "mensaje": mensaje,
            "color_titulo": color_titulo
        })
    except requests.RequestException as e:
        return jsonify({"error": f"Error de conexión o consulta: {e}"}), 500
    except ValueError:
        return jsonify({"error": "No se pudo interpretar la respuesta del servidor."}), 500

if __name__ == '__main__':
    app.run(debug=True)
