from flask import Flask, request, jsonify
import requests
import re
import os

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
    titulo_lower = titulo.lower()
    if "beneficiario" in titulo_lower and "no" not in titulo_lower:
        return "green"
    elif "no beneficiario" in titulo_lower:
        return "red"
    else:
        return "yellow"

@app.route('/')
def index():
    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8" />
        <title>Consulta Beca Butiá</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #000; /* fondo negro general */
                color: #eee; /* texto claro */
                padding: 20px;
            }
            .alerta {
                background-color: #000; /* fondo negro */
                color: #fff; /* texto blanco */
                padding: 15px;
                border-left: 6px solid #ffcc00; /* borde amarillo */
                margin-top: 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
                font-family: Arial, sans-serif;
                max-width: 400px;
                margin-left: auto;
                margin-right: auto;
            }
            .formulario {
                background-color: #111; /* negro muy oscuro */
                padding: 20px;
                border-radius: 6px;
                max-width: 400px;
                margin: 0 auto 30px auto;
                box-shadow: 0 2px 8px rgba(255, 255, 255, 0.1);
            }
            .grupo-campos {
                background-color: #222; /* bloque oscuro para inputs juntos */
                padding: 15px;
                border-radius: 6px;
                margin-bottom: 15px;
            }
            label {
                display: block;
                margin: 8px 0 4px 0;
                font-weight: bold;
            }
            input[type="text"], select {
                width: 100%;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #444;
                background-color: #111;
                color: #eee;
                font-family: inherit;
                font-size: 14px;
                box-sizing: border-box;
            }
            input[type="text"]:focus,
            select:focus {
                outline: 2px solid #ffcc00; /* borde amarillo */
                background-color: #111 !important; /* fondo negro forzado */
                color: #eee !important;
                box-sizing: border-box;
            }
            button {
                display: block;
                width: 100%;
                background-color: #444;
                color: #eee;
                font-weight: bold;
                padding: 10px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                margin-top: 10px;
            }
            button:hover {
                background-color: #666;
            }
            #resultado {
                margin-top: 20px;
                white-space: pre-wrap;
                max-width: 400px;
                margin-left: auto;
                margin-right: auto;
                color: #eee;
            }
        </style>
    </head>
    <body>
        <div class="formulario">
            <h2>Consulta de Beca Butiá</h2>
            <form id="formConsulta">
                <div class="grupo-campos">
                    <label for="documento">Documento:</label>
                    <input type="text" id="documento" name="documento" required />
                    <label for="tipo_doc">Tipo de Documento:</label>
                    <select id="tipo_doc" name="tipo_doc" required>
                        <option value="">Seleccione...</option>
                        <option value="1">CI Uruguay</option>
                        <option value="3">DNI Argentina</option>
                        <option value="4">RG Brasil</option>
                        <option value="5">CPF Brasil</option>
                        <option value="6">CI Paraguay</option>
                        <option value="7">Pasaporte</option>
                    </select>
                </div>

                <button type="submit">Consultar</button>
            </form>
            <div id="resultado"></div>
        </div>

        <div class="alerta">
            <strong>Advertencia:</strong> Esta página no es oficial. Los resultados pueden no ser definitivos. Consultá siempre el sitio del MEC para confirmarlos.
        </div>
        <div class="alerta">
            Esta herramienta no guarda ni comparte tu documento. Sólo consulta si hay datos disponibles con tu consentimiento.
        </div>

        <script>
            const form = document.getElementById('formConsulta');
            const resultadoDiv = document.getElementById('resultado');

            form.addEventListener('submit', async (e) => {
                e.preventDefault();

                const documento = document.getElementById('documento').value.trim();
                const tipo_doc = document.getElementById('tipo_doc').value;

                resultadoDiv.textContent = "Consultando...";

                try {
                    const res = await fetch('/consultar_beca', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ documento, tipo_doc })
                    });

                    const data = await res.json();

                    if (res.ok) {
                        resultadoDiv.innerHTML = `
                            <p style="color: ${data.color_titulo}; font-weight: bold;">${data.titulo}</p>
                            <p>${data.mensaje}</p>
                        `;
                    } else {
                        resultadoDiv.textContent = "Error: " + (data.error || "Error desconocido");
                    }
                } catch (error) {
                    resultadoDiv.textContent = "Error de conexión: " + error.message;
                }
            });
        </script>
    </body>
    </html>
    """
    return html

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

        print(f"[CONSULTA] Documento: {documento} | Tipo: {TIPOS_DOCUMENTO.get(tipo_doc, tipo_doc)}", flush=True)
        print(f"[RESULTADO] {titulo} - {mensaje}", flush=True)

        return jsonify({
            "documento": documento,
            "titulo": titulo,
            "mensaje": mensaje,
            "color_titulo": color_titulo
        })
    except requests.RequestException as e:
        print(f"[ERROR DE CONEXIÓN] {e}", flush=True)
        return jsonify({"error": f"Error de conexión o consulta: {e}"}), 500
    except ValueError:
        print("[ERROR] No se pudo interpretar la respuesta del servidor.", flush=True)
        return jsonify({"error": "No se pudo interpretar la respuesta del servidor."}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
