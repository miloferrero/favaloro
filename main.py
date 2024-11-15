import os
import openai
import sys
import numpy as np
import sqlite3
import pandas as pd
from utils.support_tools import (
    send_whatsapp_message,
    load_context_files,
    ask_openai
)
import pandas as pd
from utils.database import (
    connect_database,
    insert_encrypted_log,
    read_logs,
    create_logs_table,
    dni_exists,
    export_logs_to_csv,
    generate_log_entry_with_obfuscated_dni,
    insert_initial_log,
    finalize_log
)
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

# ARCHIVOS TXT Y CSV
dni, contexto, pregunta_abierta, mensaje_derivacion, df, defi = load_context_files()
mensaje_fin_en_guardia = "Gracias por la información brindada, sabe que podes elegir que hacer más allá de esta recomendación."


#GPT-4 
model = "gpt-4"
temperature = 0

app = Flask(__name__)

# Diccionario para rastrear los mensajes enviados a cada número de teléfono
user_message_count = {}
user_questions = {}
conversacion = {}

@app.route('/', methods=['GET', 'POST'])
def whatsapp_reply():
    global log_id  # Añade esto para declarar log_id como variable global
    #log_id = None# 1. Conectar a la base de datos y obtener el cursor
    global dni_number  # Añade esto para declarar log_id como variable global
    dni_number = None# 1. Conectar a la base de datos y obtener el cursor
    connection, cursor = connect_database()
    create_logs_table(cursor)
    
    if request.method == 'GET':
        return "Server is running and accessible via GET request."

    # Continuar con el código actual para manejar las solicitudes POST
    sender_number = request.form.get('From')
    message_body = request.form.get('Body')


    # Crear la respuesta adecuada
    response = MessagingResponse()

    if message_body == "x":
        user_message_count[sender_number] = -1
        response.message("Contador de mensajes reiniciado.")
    else:
        if sender_number not in user_message_count:
            user_message_count[sender_number] = 0
        else:
            user_message_count[sender_number] += 1
        
        if user_message_count[sender_number] == 0:
            send_whatsapp_message(dni, sender_number)

        if user_message_count[sender_number] == 1:
            #generate_log_entry_with_obfuscated_dni(cursor, dni_number)
            dni_number = message_body
            log_id = insert_initial_log(connection, cursor, dni_number)
            #print(f"Log iniciado con ID: {log_id}")
               
            send_whatsapp_message(pregunta_abierta, sender_number)


        elif user_message_count[sender_number] == 2:
            #print(log_id)
            conversacion[0] = "Pregunta: " + pregunta_abierta + "Respueta: " + message_body

            conversation_history = [{"role": "system", "content": contexto + pregunta_abierta+ ": "+ message_body}]
            mensaje_urgencia = "En base únicamente a la respuesta de mi amigo, necesitas hacerle más preguntas o ya podes concluir que tiene que hacerse alguna intervenciones medica. Respuestas: /0 si necesitas hacerle mas preguntas/, /1 si podes concluir que tiene que hacerse alguna intervenciones medica/, /Null si no entendes el mensaje de mi amigo/."
            conversation_history.append({"role": "user", "content": mensaje_urgencia})
            result = ask_openai(conversation_history, temperature, model)


            if result == "1":
                #print(log_id)
                #print("DNI: "+dni_number + " Log ID: "+ log_id)
                send_whatsapp_message("Estoy pensando, dame unos segundos...", sender_number)
                conversation_history.append({"role": "user", "content": mensaje_derivacion})
                result = ask_openai(conversation_history, temperature, model)
                send_whatsapp_message(result, sender_number)
                response.message(result)
                user_message_count[sender_number] = -1
                #response.message("Contador de mensajes reiniciado.")                send_whatsapp_message(mensaje_fin_en_guardia, sender_number)
                conversation_history.append({"role": "user", "content": "En base a este unicamente al reporte la recomendacion es: 0) que se quede en la guardia o 1) vuelva a su casa. Por favor contestame solo un numero"})
                #print(conversation_history)
                digitalizacion = ask_openai(conversation_history, temperature, model)
                #print(digitalizacion)
                log_level = "INFO"
                conversation_content = "\n".join(map(lambda message: f'{message["role"]}: {message["content"]}', conversation_history))


                validacion = "A definir"
               
                finalize_log(connection, cursor, log_id, log_level, conversation_content, digitalizacion, validacion)
                export_logs_to_csv()
                
                # Cerrar la conexión cuando termines
                connection.close()
                return "Registro Agregado con exito."


            
            elif result != "1":
            #En base a la pregunta abierta, califico en tipos de triage
                mis_preguntas = df.to_numpy()
                mis_triages = df[['# Camino', 'Camino']].drop_duplicates()

                mensaje_def_triage = ", ".join([f"{row['# Camino']}. {row['Camino']}" for index, row in mis_triages.iterrows()])                
                mensaje_def_triage = "Basado únicamente en la respuesta del paciente, cual de estas guardaias estas 100% seguro de que corresponde derivarlo?: "+mensaje_def_triage+" En caso de no estar seguro o que te falte informacion que vaya por el camino numero 11. Serias tan amable de responderme solamente con numeros la guardia?"
                conversation_history.append({"role": "user", "content": mensaje_def_triage})
                result = ask_openai(conversation_history, temperature, model)

                if result == "11":
                    send_whatsapp_message("Te recomiendo que te quedes en la guardia.",sender_number)
                    user_message_count[sender_number] = 0
            #print(result)
            derivacion = int(result)
            cantidad_caminos = df['# Camino'].nunique()
            filtered_data = df[df['# Camino'] == derivacion]
            result = ask_openai(conversation_history, temperature, model)

            if not filtered_data.empty:
                # Extraer el nombre del camino elegido
                camino_elegido = filtered_data['Camino'].iloc[0]
                # Imprimir el camino elegido
                #print("\nTu padecimiento es", camino_elegido + ". \nPor favor contestame las siguientes preguntas:")
                #response.message(camino_elegido)
            else:
                user_message_count[sender_number] = 0
                response.message("No hay camino")

            extracted_questions_numerers = filtered_data[['# Pregunta']]
            extracted_questions = filtered_data[['# Pregunta', 'Pregunta']]


            user_questions[0] = extracted_questions.iloc[0]['Pregunta']
            user_questions[1] = extracted_questions.iloc[1]['Pregunta']
            user_questions[2] = extracted_questions.iloc[2]['Pregunta']
            user_questions[3] = extracted_questions.iloc[3]['Pregunta']
            user_questions[4] = extracted_questions.iloc[4]['Pregunta']
            user_questions[5] = extracted_questions.iloc[5]['Pregunta']
            user_questions[6] = extracted_questions.iloc[6]['Pregunta']
            user_questions[7] = extracted_questions.iloc[7]['Pregunta']
            user_questions[8] = extracted_questions.iloc[8]['Pregunta']
            user_questions[9] = extracted_questions.iloc[9]['Pregunta']

            conversacion[0] = contexto + conversacion[0] + " Pregunta: "+user_questions[0]
            #conversation_history.append({"role": "user", "content": " Pregunta: "+user_questions[0]})
            
            response.message(user_questions[0])

        elif user_message_count[sender_number] == 3:
            conversacion[0] = conversacion[0] + " Respuesta: "+ message_body
            conversacion[0] = conversacion[0] + " Pregunta: "+user_questions[1]
            send_whatsapp_message(user_questions[1], sender_number)
            #response.message(user_questions[1])

        elif user_message_count[sender_number] == 4:
            conversacion[0] = conversacion[0] + " Respuesta: "+ message_body
            conversacion[0] = conversacion[0] + " Pregunta: "+user_questions[2]
            send_whatsapp_message(user_questions[2], sender_number)
            #response.message(user_questions[2])

        elif user_message_count[sender_number] == 5:
            conversacion[0] = conversacion[0] + " Respuesta: "+ message_body
            conversacion[0] = conversacion[0] + " Pregunta: "+user_questions[3]
            send_whatsapp_message(user_questions[3], sender_number)
            #response.message(user_questions[3])

        elif user_message_count[sender_number] == 6:
            conversacion[0] = conversacion[0] + " Respuesta: "+ message_body
            conversacion[0] = conversacion[0] + " Pregunta: "+user_questions[4]
            send_whatsapp_message(user_questions[4], sender_number)
            #response.message(user_questions[4])

        elif user_message_count[sender_number] == 7:
            conversacion[0] = conversacion[0] + " Respuesta: "+ message_body
            conversacion[0] = conversacion[0] + " Pregunta: "+user_questions[5]
            send_whatsapp_message(user_questions[5], sender_number)

        elif user_message_count[sender_number] == 8:
            conversacion[0] = conversacion[0] + " Respuesta: "+ message_body
            conversacion[0] = conversacion[0] + " Pregunta: "+user_questions[6]
            send_whatsapp_message(user_questions[6], sender_number)
            #response.message(user_questions[6])

        elif user_message_count[sender_number] == 9:
            conversacion[0] = conversacion[0] + " Respuesta: "+ message_body
            conversacion[0] = conversacion[0] + " Pregunta: "+user_questions[7]
            send_whatsapp_message(user_questions[7], sender_number)
            #response.message(user_questions[7])

        elif user_message_count[sender_number] == 10:
            conversacion[0] = conversacion[0] + " Respuesta: "+ message_body
            conversacion[0] = conversacion[0] + " Pregunta: "+user_questions[8]
            send_whatsapp_message(user_questions[8], sender_number)

#            response.message(user_questions[8])

        elif user_message_count[sender_number] == 11:
            conversacion[0] = conversacion[0] + " Respuesta: "+ message_body
            conversacion[0] = conversacion[0] + " Pregunta: "+user_questions[9]
            send_whatsapp_message(user_questions[9], sender_number)
            #response.message(user_questions[9])
        
        elif user_message_count[sender_number] > 11:
            #print(log_id)        
            conversacion[0] = conversacion[0] + " Respuesta: "+ message_body

            send_whatsapp_message("Estoy pensando, dame unos segundos...", sender_number)

            conversacion_str = str(conversacion[0])
            conversacion_str = "Historial de preguntas: "+conversacion_str + "Basado en el historial: "+mensaje_derivacion
            #print(conversacion_str)

            conversation_reporte = [{"role": "system", "content": conversacion_str}]
            result = ask_openai(conversation_reporte, temperature, model)

            
            send_whatsapp_message(result, sender_number)

            conversacion_str = conversacion_str + "Reporte: " + result
            conversacion_str = conversacion_str + " En base a este unicamente al reporte la recomendacion es: 0) que se quede en la guardia o 1) vuelva a su casa. Por favor contestame solo un numero"
            conversation_reporte = [{"role": "system", "content": conversacion_str}]
            
            digitalizacion = ask_openai(conversation_reporte, temperature, model)
            log_level = "INFO"
            #conversation_content = "\n".join(map(lambda message: f'{message["role"]}: {message["content"]}', conversation_history))


            validacion = "A definir"
            #print(log_id)
            # Insertar el registro encriptado
            # Actualizar el log con el contenido completo y el estado "finalizado"
            finalize_log(connection, cursor, log_id, log_level, conversacion_str, digitalizacion, validacion)
            export_logs_to_csv()

            # Cerrar la conexión cuando termines
            connection.close()
            user_message_count[sender_number] = -1
            send_whatsapp_message(mensaje_fin_en_guardia, sender_number)

        
    return str(response)



# Endpoint para reiniciar los contadores de mensajes de todos los usuarios
@app.route('/reiniciar_contadores', methods=['GET'])
def reiniciar_contadores():
    # Reiniciar el contador de todos los usuarios
    user_message_count.clear()
    return "Contadores de mensajes reiniciados para todos los usuarios."

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)
