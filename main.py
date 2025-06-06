import requests
import re
from colorama import init, Fore, Style

# Inicializar colorama para Windows
init(autoreset=True)

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
    # Reemplazos comunes
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

def validar_documento(documento):
    return documento.isdigit()

def validar_tipo_documento(tipo):
    return tipo in TIPOS_DOCUMENTO

def obtener_color_titulo(titulo):
    titulo_lower = titulo.lower()
    if "beneficiario" in titulo_lower and "no" not in titulo_lower:
        return Fore.GREEN
    elif "no beneficiario" in titulo_lower:
        return Fore.RED
    else:
        return Fore.YELLOW

def consultar_beca(documento, tipo_doc):
    url = 'https://becas.mec.gub.uy/ConsultarBecas/controller.php'
    data = {
        'accion': 'consultar',
        'documento': documento,
        'cboTDoc': tipo_doc
    }

    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        resultado = response.json()

        titulo = resultado.get('titulo', '').strip()
        mensaje_raw = resultado.get('mensaje', '')
        mensaje = limpiar_html(mensaje_raw)

        color_titulo = obtener_color_titulo(titulo)

        return {
            "documento": documento,
            "titulo": titulo,
            "mensaje": mensaje,
            "color_titulo": color_titulo
        }

    except requests.RequestException as e:
        print(f"{Fore.RED}Error de conexión o consulta: {e}")
        return None
    except ValueError:
        print(f"{Fore.RED}No se pudo interpretar la respuesta del servidor.")
        return None

def imprimir_resultado(resultado):
    if resultado is None:
        print(f"{Fore.RED}No se pudo obtener resultado de la consulta.")
        return

    print(f"\nResultado para documento: {resultado['documento']}\n")
    print(f"Título: {resultado['color_titulo']}{resultado['titulo']}\n")
    print(f"Mensaje:\n{Fore.WHITE}{resultado['mensaje']}\n")

def guardar_resultado_en_archivo(resultado):
    nombre_archivo = f"resultado_beca_{resultado['documento']}.txt"
    with open(nombre_archivo, "w", encoding="utf-8") as f:
        f.write(f"Resultado para documento: {resultado['documento']}\n\n")
        f.write(f"Título: {resultado['titulo']}\n\n")
        f.write(f"Mensaje:\n{resultado['mensaje']}\n")

    print(f"{Fore.GREEN}Resultado guardado en '{nombre_archivo}'")

def main():
    print("=== Consulta de Beca Butiá ===")

    while True:
        documento = input("Ingrese su cédula o número de documento (sin puntos ni guiones): ").strip()
        if validar_documento(documento):
            break
        print(f"{Fore.YELLOW}Por favor ingrese solo números válidos.")

    print("\nSeleccione el tipo de documento:")
    for key, val in TIPOS_DOCUMENTO.items():
        print(f"{key} - {val}")

    while True:
        tipo_doc = input("Ingrese el número correspondiente al tipo de documento: ").strip()
        if validar_tipo_documento(tipo_doc):
            break
        print(f"{Fore.YELLOW}Por favor ingrese un tipo de documento válido.")

    resultado = consultar_beca(documento, tipo_doc)
    imprimir_resultado(resultado)

    if resultado:
        save = input("¿Querés guardar el resultado en un archivo? (s/n): ").strip().lower()
        if save == "s":
            guardar_resultado_en_archivo(resultado)

    input(f"\n{Style.DIM}Presione ENTER para salir...")

if __name__ == "__main__":
    main()
