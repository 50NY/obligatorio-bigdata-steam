"""
Conversión de formato del dataset Steam (UCSD, Julian McAuley) a JSON Lines.

Fuente: https://cseweb.ucsd.edu/~jmcauley/datasets.html#steam_data

PROBLEMA
Los archivos originales NO son JSON válido. Cada línea es un diccionario de
Python escrito como texto (comillas simples, prefijos u'...', True/False/None),
por lo que Spark no puede leerlos con spark.read.json().

QUÉ HACE ESTE SCRIPT
Lee cada archivo .json.gz línea por línea, interpreta cada línea como un literal
de Python (ast.literal_eval, que solo evalúa literales y no ejecuta código) y la
vuelve a escribir como JSON válido, un objeto por línea (formato JSON Lines),
comprimido en .gz.

QUÉ NO HACE
No modifica, filtra, limpia ni elimina ningún dato: solo cambia el formato.
Toda la limpieza se hace después en Spark, como exige el obligatorio.
La cantidad de registros de salida es igual a la de entrada, y el script lo
verifica comparando registro a registro el contenido original con el convertido.

USO
    python convertir_a_json.py <carpeta_origen> <carpeta_destino>
"""
import ast
import gzip
import json
import sys
from pathlib import Path

# archivo original -> nombre de salida (se quita el " (1)" que agregó la descarga)
ARCHIVOS = {
    "steam_games.json.gz": "steam_games.json.gz",
    "australian_users_items (1).json.gz": "australian_users_items.json.gz",
    "australian_user_reviews (1).json.gz": "australian_user_reviews.json.gz",
    "bundle_data.json.gz": "bundle_data.json.gz",
}


def convertir(origen: Path, destino: Path) -> int:
    n = 0
    with gzip.open(origen, "rt", encoding="utf-8") as f_in, \
         gzip.open(destino, "wt", encoding="utf-8") as f_out:
        for nro_linea, linea in enumerate(f_in, start=1):
            linea = linea.strip()
            if not linea:
                continue
            try:
                registro = ast.literal_eval(linea)
            except (ValueError, SyntaxError) as e:
                raise RuntimeError(f"{origen.name}, línea {nro_linea}: no se pudo interpretar ({e})")
            # allow_nan=False: si apareciera un NaN/Infinity (no válido en JSON) se detiene
            f_out.write(json.dumps(registro, ensure_ascii=False, allow_nan=False) + "\n")
            n += 1
    return n


def verificar(origen: Path, destino: Path) -> int:
    """Relee ambos archivos y confirma que cada registro convertido es idéntico al original."""
    n = 0
    with gzip.open(origen, "rt", encoding="utf-8") as f_o, \
         gzip.open(destino, "rt", encoding="utf-8") as f_d:
        originales = (l.strip() for l in f_o if l.strip())
        for orig, conv in zip(originales, f_d):
            if ast.literal_eval(orig) != json.loads(conv):
                raise RuntimeError(f"{destino.name}: el registro {n + 1} no coincide con el original")
            n += 1
        if next(originales, None) is not None or f_d.readline():
            raise RuntimeError(f"{destino.name}: distinta cantidad de registros que el original")
    return n


def main():
    if len(sys.argv) != 3:
        sys.exit("Uso: python convertir_a_json.py <carpeta_origen> <carpeta_destino>")
    carpeta_origen, carpeta_destino = Path(sys.argv[1]), Path(sys.argv[2])
    carpeta_destino.mkdir(parents=True, exist_ok=True)

    for nombre_origen, nombre_destino in ARCHIVOS.items():
        origen, destino = carpeta_origen / nombre_origen, carpeta_destino / nombre_destino
        escritos = convertir(origen, destino)
        verificados = verificar(origen, destino)
        print(f"{nombre_origen:40s} -> {nombre_destino:35s} {escritos:>8,} registros | verificados: {verificados:,} OK")


if __name__ == "__main__":
    main()
