##########################
# Agente Economico De IA #
# Herramientas           #
##########################

# Importaciones necesarias
import os
import requests
from datetime import datetime, timedelta, timezone

# matplotlib en modo "Agg": no necesita pantalla, funciona en un servidor
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


class EconomicTools:

    # 1. Tipo de cambio de una moneda respecto al quetzal (Frankfurter API)
    def consultar_tipo_cambio(self, moneda: str):
        try:
            url = f"https://api.frankfurter.dev/v2/latest?base={moneda}&symbols=GTQ"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return {
                "moneda": moneda,
                "quetzales": data["rates"]["GTQ"],
                "fuente": "Frankfurter API"
            }
        except Exception as e:
            return {"error": f"No se pudo obtener el tipo de cambio: {e}"}

    # 2. Tipo de cambio de respaldo (ExchangeRate-API)
    def consultar_tipo_cambio_respaldo(self, moneda: str):
        try:
            url = f"https://open.er-api.com/v6/latest/{moneda}"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return {
                "moneda": moneda,
                "quetzales": data["rates"]["GTQ"],
                "fuente": "ExchangeRate-API"
            }
        except Exception as e:
            return {"error": f"No se pudo obtener el tipo de cambio de respaldo: {e}"}

    # 3. PIB mas reciente de un pais (World Bank API)
    def consultar_pib_pais(self, pais: str):
        try:
            url = f"https://api.worldbank.org/v2/country/{pais}/indicator/NY.GDP.MKTP.CD?format=json&mrnev=1"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            registro = data[1][0]
            return {
                "pais": registro["country"]["value"],
                "anio": registro["date"],
                "pib_usd": registro["value"],
                "fuente": "World Bank API"
            }
        except Exception as e:
            return {"error": f"No se pudo obtener el PIB: {e}"}

    # 4. Moneda oficial de un pais (countries.dev)
    def consultar_moneda_pais(self, pais: str):
        try:
            url = f"https://countries.dev/alpha/{pais}"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            moneda = data["currencies"][0]
            return {
                "pais": data["name"],
                "moneda_codigo": moneda["code"],
                "moneda_nombre": moneda["name"],
                "simbolo": moneda.get("symbol"),
                "fuente": "countries.dev"
            }
        except Exception as e:
            return {"error": f"No se pudo obtener la moneda del pais: {e}"}

    # 5. Precio actual en USD de una criptomoneda (CoinGecko API)
    def consultar_precio_cripto(self, cripto: str):
        try:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={cripto}&vs_currencies=usd"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            precio = data[cripto]["usd"]
            return {
                "cripto": cripto,
                "precio_usd": precio,
                "fuente": "CoinGecko API"
            }
        except Exception as e:
            return {"error": f"No se pudo obtener el precio de la criptomoneda: {e}"}

    # 6. Variacion del tipo de cambio en un periodo (Frankfurter API, serie historica)
    def analizar_variacion_tipo_cambio(self, moneda: str, dias: int = 7):
        try:
            hoy = datetime.now(timezone.utc).date()
            inicio = hoy - timedelta(days=dias)
            url = f"https://api.frankfurter.dev/v2/{inicio}..{hoy}?base={moneda}&symbols=GTQ"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            fechas = sorted(data["rates"].keys())
            valor_inicial = data["rates"][fechas[0]]["GTQ"]
            valor_final = data["rates"][fechas[-1]]["GTQ"]
            variacion_pct = ((valor_final - valor_inicial) / valor_inicial) * 100
            return {
                "moneda": moneda,
                "desde": fechas[0],
                "hasta": fechas[-1],
                "valor_inicial": valor_inicial,
                "valor_final": valor_final,
                "variacion_porcentual": round(variacion_pct, 2),
                "fuente": "Frankfurter API"
            }
        except Exception as e:
            return {"error": f"No se pudo analizar la variacion: {e}"}

    # 7. Grafica del tipo de cambio en un periodo (Frankfurter API + matplotlib)
    # Guarda el archivo en una carpeta local "generated" para que Streamlit lo muestre con st.image()
    def generar_grafica_tipo_cambio(self, moneda: str, dias: int = 7):
        try:
            hoy = datetime.now(timezone.utc).date()
            inicio = hoy - timedelta(days=dias)
            url = f"https://api.frankfurter.dev/v2/{inicio}..{hoy}?base={moneda}&symbols=GTQ"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            fechas = sorted(data["rates"].keys())
            valores = [data["rates"][f]["GTQ"] for f in fechas]

            plt.figure(figsize=(7, 4))
            plt.plot(fechas, valores, marker="o")
            plt.title(f"Tipo de cambio {moneda} a GTQ")
            plt.xlabel("Fecha")
            plt.ylabel("Quetzales")
            plt.xticks(rotation=45)
            plt.tight_layout()

            carpeta = "generated"
            os.makedirs(carpeta, exist_ok=True)
            nombre_archivo = f"grafica_{moneda.lower()}_gtq_{int(datetime.now().timestamp())}.png"
            ruta_completa = os.path.join(carpeta, nombre_archivo)
            plt.savefig(ruta_completa)
            plt.close()

            return {
                "moneda": moneda,
                "archivo": ruta_completa,
                "mensaje": f"Grafica generada correctamente ({nombre_archivo})",
                "fuente": "Frankfurter API"
            }
        except Exception as e:
            return {"error": f"No se pudo generar la grafica: {e}"}

    # 8. Reporte breve combinando PIB y tipo de cambio de un pais
    def generar_reporte_pais(self, pais: str, moneda: str):
        try:
            pib = self.consultar_pib_pais(pais)
            cambio = self.consultar_tipo_cambio(moneda)

            if "error" in pib or "error" in cambio:
                return {"error": "No se pudo generar el reporte completo, falta informacion de alguna fuente."}

            reporte = (
                f"Reporte economico de {pib['pais']} ({pib['anio']}):\n"
                f"- PIB: ${pib['pib_usd']:,.0f} USD\n"
                f"- Tipo de cambio: 1 {cambio['moneda']} = Q{cambio['quetzales']}"
            )
            return {
                "pais": pib["pais"],
                "reporte": reporte,
                "fuente": "World Bank API + Frankfurter API"
            }
        except Exception as e:
            return {"error": f"No se pudo generar el reporte: {e}"}

    # 9. Recomendacion de fuentes oficiales segun el tema
    def recomendar_recursos(self, tema: str):
        recursos = {
            "tipo_cambio": ["Banco de Guatemala (banguat.gob.gt)", "Frankfurter API (frankfurter.dev)"],
            "pib": ["World Bank Open Data (data.worldbank.org)", "Banco de Guatemala - Cuentas Nacionales"],
            "inflacion": ["Instituto Nacional de Estadistica - INE Guatemala (ine.gob.gt)", "Banco de Guatemala"],
            "cripto": ["CoinGecko (coingecko.com)"],
            "moneda": ["countries.dev"]
        }
        clave = tema.lower().strip()
        fuentes = recursos.get(clave)
        if not fuentes:
            return {"error": f"No tengo recursos para el tema '{tema}'. Temas disponibles: {list(recursos.keys())}"}
        return {"tema": tema, "recursos": fuentes}
