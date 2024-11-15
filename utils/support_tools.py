# utils/support_tools.py
import os
from twilio.rest import Client
import openai
import pandas as pd


# 1) Configuración de Twilio
account_sid = 'ACafd7cf686a65ca34cf406506bef3e179'
auth_token = os.getenv('auth_token')  # Usa la variable de entorno para el token de autenticación
client = Client(account_sid, auth_token)

def send_whatsapp_message(body, to):
    """
    Envía un mensaje de WhatsApp usando Twilio.

    Parámetros:
        body (str): Contenido del mensaje a enviar.
        to (str): Número de WhatsApp del destinatario, e.g., 'whatsapp:+123456789'.

    Retorna:
        Message: Objeto del mensaje de Twilio con detalles del mensaje enviado.
    """
    return client.messages.create(
        from_='whatsapp:+14155238886',  # Reemplaza con tu número de Twilio
        body=body,
        to=to
    )










# 2)GPT-4
def ask_openai(messages, temperature, model):
    """
    Realiza una consulta a la API de OpenAI con los parámetros dados.

    Parámetros:
        messages (list): Lista de diccionarios de mensajes para el historial de la conversación.
        temperature (float): Configuración de temperatura para la generación.
        model (str): Modelo de OpenAI a utilizar, e.g., "gpt-4".

    Retorna:
        str: La respuesta generada o un mensaje por defecto.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("API key no encontrada. Configura la variable de entorno OPENAI_API_KEY.")

    # Crear la consulta de completado de chat con los parámetros dados
    completion = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature
    )

    # Retorna el contenido del mensaje de la primera elección, o un mensaje predeterminado
    if completion.choices and completion.choices[0].message:
        return completion.choices[0].message.content
    else:
        return "Dirigite a la guardia."













### 3) CARGA DE ARCHIVOS

def load_context_files():
    # Carga de archivos de texto
    with open('contexto/0. dni.txt', 'r') as archivo:
        dni = archivo.read()

    with open('contexto/1. contexto.txt', 'r') as archivo:
        contexto = archivo.read()

    with open('contexto/2. pregunta_abierta.txt', 'r') as archivo:
        pregunta_abierta = archivo.read()

    with open('contexto/3 mensaje_derivacion.txt', 'r') as archivo:
        mensaje_derivacion = archivo.read()

    # Carga de archivos CSV
    df = pd.read_csv('contexto/preguntas.csv')
    defi = pd.read_csv('contexto/plan_de_accion.csv')

    # Retorna todos los datos, incluyendo el archivo adicional
    return dni, contexto, pregunta_abierta, mensaje_derivacion, df, defi
