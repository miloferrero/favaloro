import sqlite3
import csv
from cryptography.fernet import Fernet
from datetime import datetime
import pytz

# Clave de encriptación (guárdala en un lugar seguro)
encryption_key = b'K2Rs9pG7Tm0vPrQz6JyF3mL9VoNcEdqSb0JxT1PaABQ='
cipher_suite = Fernet(encryption_key)

# Función para encriptar texto
def encrypt(text):
    return cipher_suite.encrypt(text.encode())

# Función para desencriptar texto
def decrypt(encrypted_text):
    return cipher_suite.decrypt(encrypted_text).decode()

# Conectar a la base de datos SQLite y crear la tabla si no existe
def connect_database():
    connection = sqlite3.connect("logs_database.db")
    cursor = connection.cursor()
    return connection, cursor

# Función para crear la tabla de logs con los nuevos campos
def create_logs_table(cursor):
    create_table_query = """
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        log_level TEXT,
        conversation_content TEXT,
        digitalizacion TEXT,
        dni TEXT,
        validacion TEXT
    );
    """
    cursor.execute(create_table_query)
    cursor.connection.commit()

# Insertar un registro encriptado en la base de datos con los nuevos campos
def insert_encrypted_log(connection, cursor, log_level, conversation_content, digitalizacion, dni, validacion):
    encrypted_log_level = encrypt(log_level)
    encrypted_content = encrypt(conversation_content)
    encrypted_digitalizacion = encrypt(digitalizacion)
    encrypted_dni = encrypt(dni)
    encrypted_validacion = encrypt(validacion)

    cursor.execute(
        "INSERT INTO logs (log_level, conversation_content, digitalizacion, dni, validacion) VALUES (?, ?, ?, ?, ?)", 
        (encrypted_log_level, encrypted_content, encrypted_digitalizacion, encrypted_dni, encrypted_validacion)
    )
    connection.commit()

# Leer y desencriptar registros de la base de datos
def read_logs(cursor):
    cursor.execute("SELECT timestamp, log_level, conversation_content, digitalizacion, dni, validacion FROM logs")
    logs = cursor.fetchall()
    decrypted_logs = []
    for log in logs:
        timestamp = log[0]  # Obtener el timestamp
        log_level = decrypt(log[1])
        decrypted_content = decrypt(log[2])
        digitalizacion = decrypt(log[3])
        dni = decrypt(log[4])
        validacion = decrypt(log[5])
        decrypted_logs.append((timestamp, log_level, decrypted_content, digitalizacion, dni, validacion))
    return decrypted_logs

# Verificar si un DNI encriptado ya existe en la base de datos
def dni_exists(cursor, dni):
    encrypted_dni = encrypt(dni)
    cursor.execute("SELECT 1 FROM logs WHERE dni = ?", (encrypted_dni,))
    return cursor.fetchone() is not None

# Exportar los datos desencriptados a un archivo CSV
def export_logs_to_csv():
    connection, cursor = connect_database()
    cursor.execute("SELECT id, timestamp, log_level, conversation_content, digitalizacion, dni, validacion FROM logs")
    rows = cursor.fetchall()

    with open("logs_database_decrypted.csv", mode="w", newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["id", "timestamp", "log_level", "conversation_content", "digitalizacion", "dni", "validacion"])

        for row in rows:
            decrypted_row = [
                row[0],  # id
                row[1],  # timestamp
                decrypt(row[2]),  # log_level
                decrypt(row[3]),  # conversation_content
                decrypt(row[4]),  # digitalizacion
                decrypt(row[5]),  # dni
                decrypt(row[6])   # validacion
            ]
            writer.writerow(decrypted_row)

    connection.close()

# Función para generar un registro con key, time y dni ofuscado
def generate_log_entry_with_obfuscated_dni(cursor, dni):
    key = encryption_key.decode()  # Obtener la clave como cadena
    time = datetime.now(pytz.UTC).isoformat()  # Usar UTC para el timestamp

    # Ofuscar el DNI (e.g., reemplazar todo menos los últimos 4 dígitos)
    dni_obfuscated = '*' * (len(dni) - 4) + dni[-4:]

    # Insertar el registro en la tabla (opcional si deseas guardarlo también en la DB)
    cursor.execute(
        "INSERT INTO logs (log_level, conversation_content, digitalizacion, dni, validacion) VALUES (?, ?, ?, ?, ?)", 
        (encrypt("INFO"), encrypt("Generated log entry with obfuscated DNI"), encrypt("N/A"), encrypt(dni_obfuscated), encrypt("N/A"))
    )
    cursor.connection.commit()

    return {"key": key, "time": time, "dni_obfuscated": dni_obfuscated}


# Insertar un registro inicial cuando se inicia la sesión
def insert_initial_log(connection, cursor, dni):
    dni_obfuscated = '*' * (len(dni) - 4) + dni[-4:]
    cursor.execute(
        "INSERT INTO logs (log_level, conversation_content, digitalizacion, dni, validacion) VALUES (?, ?, ?, ?, ?)",
        (encrypt("INFO"), encrypt("Sesion iniciada"), encrypt("N/A"), encrypt(dni_obfuscated), encrypt("iniciado"))
    )
    connection.commit()
    return cursor.lastrowid  # Devuelve el ID del registro insertado


# Actualizar el registro al finalizar la sesión
def finalize_log(connection, cursor, log_id, log_level, conversation_content, digitalizacion, validacion):
    encrypted_log_level = encrypt(log_level)
    encrypted_content = encrypt(conversation_content)
    encrypted_digitalizacion = encrypt(digitalizacion)
    encrypted_validacion = encrypt(validacion)

    cursor.execute(
        """
        UPDATE logs
        SET log_level = ?, conversation_content = ?, digitalizacion = ?, validacion = ?
        WHERE id = ?
        """,
        (encrypted_log_level, encrypted_content, encrypted_digitalizacion, encrypted_validacion, log_id)
    )
    connection.commit()
