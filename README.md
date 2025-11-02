# Validador de Direcciones - Posadas


Proyecto desarrollado en **Python** y **Django** para validar y normalizar direcciones urbanas de **Posadas, Misiones, Argentina**.
Utiliza datos públicos del **IDE Posadas** y scripts auxiliares para embellecer y estructurar archivos GeoJSON.


---


## Estructura de Datos

data/
raw/ # Archivos crudos descargados del IDE Posadas
pretty/ # (Se genera localmene con pretty_geojson.py)

Los archivos en `pretty/` no se versionan para mantener el repositorio liviano.
Para generarlos localmente:

```bash
python scripts/pretty_geojson.py --in data/raw --out data/pretty

## Entorno de desarrollo

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

## Objetivo general

Construir un sistema que permita:
* Validar y corregir direcciones urbanas.
* Detectar ambigüedades.
* Preparar datos limpios para sistemas logísticos inteligentes.

Repositorio de desarrollo académico - Tecnicatura en Ciencias de Datos e Inteligencia Artificial.