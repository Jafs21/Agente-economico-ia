#######################
# Agente Basico De IA #
# Agente              #
#######################

from dotenv import load_dotenv
from groq import Groq
import os
import json
import streamlit as st

from basic_memory import BasicMemory
from economic_tools_JF import EconomicTools


# =========================
# CONFIGURACIÓN ORIGINAL
# =========================

load_dotenv()

MEMORY_MAX_MESSAGES = 10


def obtener_api_key():
    # Localmente la toma del archivo .env; ya desplegado en Streamlit Cloud,
    # la toma de los "Secrets" configurados en el panel de la app.
    clave = os.environ.get("GROQ_API_KEY")
    if clave:
        return clave
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        return None


api_key = obtener_api_key()

client = Groq(api_key=api_key)

economic_tools = EconomicTools()


# =========================
# PROMPT DEL AGENTE
# =========================

SYSTEM_PROMPT = """
Eres EconoIA Jafs, un agente económico que habla en español y responde de manera clara y concisa.
Tu objetivo es ayudar al usuario a comprender la situación económica y financiera actual,
mediante la consulta, el análisis y la interpretación de datos económicos confiables.

Capacidades principales:
- Análisis de series económicas: identificar tendencias y variaciones en los datos consultados.
- Interpretación de indicadores: explicar en palabras simples qué significa un dato (PIB, tipo de cambio, etc.).
- Generación de resúmenes y reportes: armar un resumen breve de los datos consultados.
- Recomendación de recursos: sugerir fuentes oficiales confiables según el tema consultado.

Herramientas:
- consultar_tipo_cambio: tipo de cambio de una moneda respecto al quetzal (Frankfurter API).
- consultar_tipo_cambio_respaldo: lo mismo, usando una fuente alterna (ExchangeRate-API).
- consultar_pib_pais: PIB más reciente de un país (World Bank API).
- consultar_moneda_pais: moneda oficial de un país (countries.dev).
- consultar_precio_cripto: precio actual en dólares de una criptomoneda (CoinGecko API).
- analizar_variacion_tipo_cambio: compara el tipo de cambio de una moneda entre dos fechas y calcula el cambio porcentual.
- generar_grafica_tipo_cambio: genera una gráfica de la evolución del tipo de cambio.
- generar_reporte_pais: arma un reporte breve combinando el PIB y el tipo de cambio de un país.
- recomendar_recursos: recomienda fuentes oficiales según el tema (tipo_cambio, pib, inflacion, cripto, moneda).
- Al llamar a cualquiera de estas herramientas, el o los argumentos solicitados son obligatorios.
- La respuesta que de estas herramientas debes regresarla tal cual, considerando que es correcta.
- Cuando uses generar_grafica_tipo_cambio, siempre describe brevemente en texto lo que muestra la gráfica.
"""


# =========================
# HERRAMIENTAS (TOOLS)
# =========================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "consultar_tipo_cambio",
            "description": "Consulta el tipo de cambio de una moneda respecto al quetzal de Guatemala.",
            "parameters": {
                "type": "object",
                "properties": {
                    "moneda": {"type": "string", "description": "Codigo de la moneda, por ejemplo USD"}
                },
                "required": ["moneda"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_tipo_cambio_respaldo",
            "description": "Consulta el tipo de cambio de una moneda respecto al quetzal, usando una fuente alterna.",
            "parameters": {
                "type": "object",
                "properties": {
                    "moneda": {"type": "string", "description": "Codigo de la moneda, por ejemplo USD"}
                },
                "required": ["moneda"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_pib_pais",
            "description": "Consulta el PIB (Producto Interno Bruto) mas reciente de un pais.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pais": {"type": "string", "description": "Codigo ISO alpha-2 del pais, por ejemplo GT"}
                },
                "required": ["pais"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_moneda_pais",
            "description": "Consulta la moneda oficial de un pais.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pais": {"type": "string", "description": "Codigo ISO alpha-2 del pais, por ejemplo GT"}
                },
                "required": ["pais"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_precio_cripto",
            "description": "Consulta el precio actual en dolares de una criptomoneda.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cripto": {"type": "string", "description": "Id de la criptomoneda en CoinGecko, por ejemplo bitcoin"}
                },
                "required": ["cripto"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analizar_variacion_tipo_cambio",
            "description": "Consulta la variacion porcentual del tipo de cambio de una moneda en los ultimos N dias.",
            "parameters": {
                "type": "object",
                "properties": {
                    "moneda": {"type": "string", "description": "Codigo de la moneda, por ejemplo USD"},
                    "dias": {"type": "integer", "description": "Cantidad de dias hacia atras a analizar, por ejemplo 7"}
                },
                "required": ["moneda"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generar_grafica_tipo_cambio",
            "description": "Genera una grafica de la evolucion del tipo de cambio de una moneda en los ultimos N dias.",
            "parameters": {
                "type": "object",
                "properties": {
                    "moneda": {"type": "string", "description": "Codigo de la moneda, por ejemplo USD"},
                    "dias": {"type": "integer", "description": "Cantidad de dias hacia atras a graficar, por ejemplo 7"}
                },
                "required": ["moneda"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generar_reporte_pais",
            "description": "Genera un reporte breve combinando el PIB y el tipo de cambio de un pais.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pais": {"type": "string", "description": "Codigo ISO alpha-2 del pais, por ejemplo GT"},
                    "moneda": {"type": "string", "description": "Codigo de la moneda a incluir en el reporte, por ejemplo USD"}
                },
                "required": ["pais", "moneda"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recomendar_recursos",
            "description": "Recomienda fuentes oficiales segun el tema consultado (tipo_cambio, pib, inflacion, cripto, moneda).",
            "parameters": {
                "type": "object",
                "properties": {
                    "tema": {"type": "string", "description": "Tema sobre el cual se desean recursos, por ejemplo tipo_cambio"}
                },
                "required": ["tema"]
            }
        }
    }
]


def despachar_herramienta(name, args):
    if name == "consultar_tipo_cambio":
        return economic_tools.consultar_tipo_cambio(moneda=args["moneda"])
    elif name == "consultar_tipo_cambio_respaldo":
        return economic_tools.consultar_tipo_cambio_respaldo(moneda=args["moneda"])
    elif name == "consultar_pib_pais":
        return economic_tools.consultar_pib_pais(pais=args["pais"])
    elif name == "consultar_moneda_pais":
        return economic_tools.consultar_moneda_pais(pais=args["pais"])
    elif name == "consultar_precio_cripto":
        return economic_tools.consultar_precio_cripto(cripto=args["cripto"])
    elif name == "analizar_variacion_tipo_cambio":
        return economic_tools.analizar_variacion_tipo_cambio(moneda=args["moneda"], dias=args.get("dias", 7))
    elif name == "generar_grafica_tipo_cambio":
        return economic_tools.generar_grafica_tipo_cambio(moneda=args["moneda"], dias=args.get("dias", 7))
    elif name == "generar_reporte_pais":
        return economic_tools.generar_reporte_pais(pais=args["pais"], moneda=args["moneda"])
    elif name == "recomendar_recursos":
        return economic_tools.recomendar_recursos(tema=args["tema"])
    else:
        return {"error": f"Herramienta desconocida: {name}"}


def process_response(messages):
    """
    Envia los mensajes al modelo. Si el modelo pide usar una herramienta,
    la ejecuta y le regresa el resultado, hasta que el modelo entregue
    una respuesta final de texto.
    """

    imagen_generada = None

    while True:

        resp = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            tools=TOOLS
        )

        msg = resp.choices[0].message

        # Si no hay llamados a herramientas, ya tenemos la respuesta final
        if not getattr(msg, "tool_calls", None):
            return (msg.content or ""), imagen_generada

        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [tc.model_dump() for tc in msg.tool_calls]
        })

        for tool_call in msg.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments or "{}")
            result = despachar_herramienta(name, args)

            if name == "generar_grafica_tipo_cambio" and isinstance(result, dict) and "archivo" in result:
                imagen_generada = result["archivo"]

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, ensure_ascii=False)
            })


# =========================
# MEMORIA PARA STREAMLIT
# =========================

if "memory" not in st.session_state:
    st.session_state.memory = BasicMemory(
        max_messages=MEMORY_MAX_MESSAGES
    )

memory = st.session_state.memory


# =========================
# CONFIGURACIÓN STREAMLIT
# =========================

st.set_page_config(
    page_title="EconoIA Jafs",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 EconoIA Jafs")
st.caption("Tipo de cambio, PIB, criptomonedas y más, con datos de fuentes oficiales.")

if not api_key:
    st.error(
        "No se encontró la variable GROQ_API_KEY. "
        "Agrégala a tu archivo .env (en local) o a los Secrets de la app (ya desplegada)."
    )


# =========================
# MOSTRAR CONVERSACIÓN
# =========================

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


for message in st.session_state.chat_history:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message.get("imagen"):
            st.image(message["imagen"])


# =========================
# ENTRADA DEL USUARIO
# =========================

user_text = st.chat_input("Escribe tu mensaje...")


if user_text:

    user_text = user_text.strip()

    if user_text:

        # Mostrar mensaje del usuario
        st.session_state.chat_history.append(
            {
                "role": "user",
                "content": user_text
            }
        )

        with st.chat_message("user"):
            st.markdown(user_text)


        # =========================
        # OBTENER MEMORIA
        # =========================

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(memory.messages())

        messages.append(
            {
                "role": "user",
                "content": user_text
            }
        )


        # =========================
        # LLAMADA AL MODELO (con herramientas)
        # =========================

        imagen_generada = None

        with st.chat_message("assistant"):

            with st.spinner("Pensando..."):

                assistant_text, imagen_generada = process_response(messages)

                st.markdown(assistant_text)

                if imagen_generada:
                    st.image(imagen_generada)


        # =========================
        # ACTUALIZAR LA MEMORIA
        # =========================

        memory.add("user", user_text)

        memory.add("assistant", assistant_text)


        # Guardar conversación para
        # volver a mostrarla después
        st.session_state.chat_history.append(
            {
                "role": "assistant",
                "content": assistant_text,
                "imagen": imagen_generada
            }
        )
