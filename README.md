# Triage Médico con WhatsApp con GPT-4 🚀

¡Bienvenido! Este proyecto es un chatbot de WhatsApp creado con Flask que utiliza GPT-4 para responder preguntas de forma inteligente consultas medicas de guardia. También incluye una base de datos para guardar las conversaciones y funciones útiles para gestionar mensajes. Ideal para automatizar respuestas y brindar soporte personalizado.

## 🚀 ¿Qué puede hacer este bot?

- Responder en WhatsApp usando Twilio.
- Entender preguntas gracias a la integración con OpenAI GPT-4.
- Guardar conversaciones en una base de datos segura.
- Usar contexto dinámico desde archivos TXT y CSV para respuestas más precisas.
- Personalizar mensajes para adaptarlo a tus necesidades.

## 🛠️ ¿Cómo usarlo?

1. Instalar todo:
   Clona este proyecto e instala las dependencias necesarias:
   git clone <repository_url>
   cd <repository_name>
   pip install -r requirements.txt

2. Configurar claves:
   Crea un archivo .env y agrega las claves necesarias:
   - OpenAI: OPENAI_API_KEY
   - Twilio: TWILIO_ACCOUNT_SID y TWILIO_AUTH_TOKEN

3. Configurar la base de datos:
   El bot usa SQLite para guardar las conversaciones. Ya incluye funciones para crear y gestionar la base de datos en utils/database.py.

4. ¡A correr!
   Levanta el servidor Flask:
   python main.py
   Conecta Twilio para redirigir los mensajes de WhatsApp a tu bot, ¡y listo!

## 🗂️ ¿Cómo está organizado?

- main.py: El corazón del proyecto. Aquí vive el servidor Flask.
- utils/:
  - support_tools.py: Funciones para enviar mensajes y hablar con OpenAI.
  - database.py: Todo lo relacionado con la base de datos.
- Archivos de contexto: TXT y CSV para personalizar respuestas.

## 🛠️ Funciones principales

- Chat en WhatsApp:
  - Enviar mensajes: send_whatsapp_message(phone, message)
  - Contar preguntas y gestionar usuarios.

- Manejo de base de datos:
  - Guardar mensajes de forma segura y encriptada.
  - Exportar las conversaciones a CSV.

- Respuestas inteligentes:
  - Hablar con GPT-4: ask_openai(prompt, model, temperature)

## 🎨 Personalización

- Modelo OpenAI: Cambia entre "gpt-4" o otros.
- Tono de respuesta: Ajusta el temperature para hacerlo más creativo o preciso.
- Mensajes finales: Edita la variable mensaje_fin_en_guardia.

## ✉️ Contribuir

Si tienes ideas o mejoras, no dudes en abrir un pull request o crear un issue.

## 📝 Licencia

Este proyecto está bajo licencia.

¡Diviértete creando! 🚀
