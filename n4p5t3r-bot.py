"""
Bot de Discord para manejar preguntas y respuestas almacenadas en una base de datos SQLite.

Autor: Ricardo Rosero
GitHub: rr-n4p5t3r
Email: rrosero2000@gmail.com

Este bot permite almacenar preguntas y respuestas en una base de datos SQLite,
actualizar respuestas existentes y responder a menciones con las respuestas
almacenadas previamente. Utiliza la biblioteca discord.py y la integración con Hugging Face Transformers
para responder preguntas usando modelos de lenguaje preentrenados.

Requiere un archivo .env para cargar variables de entorno como DISCORD_TOKEN para la autenticación del bot.

"""

# Importar las bibliotecas necesarias
import discord
from discord.ext import commands
import sqlite3
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde un archivo .env
load_dotenv()

# Conexión a la base de datos SQLite
conn = sqlite3.connect('preguntas_respuestas.db')
cursor = conn.cursor()

# Crear la tabla si no existe
cursor.execute('''CREATE TABLE IF NOT EXISTS preguntas_respuestas (
                    id INTEGER PRIMARY KEY,
                    pregunta TEXT,
                    respuesta TEXT
                )''')
conn.commit()

# Crear una instancia de Intents con los intents necesarios para manejar mensajes
intents = discord.Intents.default()
intents.message_content = True  # Habilitar el intent para manejar el contenido de los mensajes

# Crear un cliente de Discord con los intents especificados y el prefijo de comando '!'
client = commands.Bot(command_prefix='!', intents=intents)

# Evento que se activa cuando el bot se conecta exitosamente
@client.event
async def on_ready():
    """
    Evento activado cuando el bot se conecta exitosamente al servidor de Discord.
    """
    print(f'Conectado como {client.user}')

# Comando para almacenar preguntas y respuestas en la base de datos
@client.command()
async def pregunta(ctx, *, content: str):
    """
    Comando para almacenar una pregunta y su respuesta en la base de datos.

    Parameters:
        ctx (commands.Context): Contexto del comando.
        content (str): Contenido del mensaje que incluye la pregunta y la respuesta separadas por '?'.

    Raises:
        Exception: Si ocurre un error al procesar la pregunta.

    """
    try:
        # Separar la pregunta y la respuesta usando '?'
        separator_index = content.find('?') + 1
        pregunta = content[:separator_index].strip()
        respuesta = content[separator_index:].strip()

        # Almacenar la pregunta y respuesta en la base de datos
        cursor.execute('INSERT INTO preguntas_respuestas (pregunta, respuesta) VALUES (?, ?)', (pregunta, respuesta))
        conn.commit()

        # Enviar confirmación de que la pregunta y respuesta han sido guardadas
        await ctx.send(f'Pregunta guardada: {pregunta}')
        await ctx.send(f'Respuesta guardada: {respuesta}')

    except Exception as e:
        await ctx.send(f"Ocurrió un error al procesar tu pregunta: {str(e)}")
        print(f"Error: {e}")

# Comando para obtener una respuesta almacenada desde la base de datos
@client.command()
async def respuesta(ctx, *, pregunta: str):
    """
    Comando para obtener la respuesta almacenada previamente desde la base de datos.

    Parameters:
        ctx (commands.Context): Contexto del comando.
        pregunta (str): Pregunta para buscar en la base de datos.

    """
    try:
        # Buscar la respuesta en la base de datos que coincide parcialmente con la pregunta proporcionada
        cursor.execute('SELECT respuesta FROM preguntas_respuestas WHERE pregunta LIKE ?', ('%' + pregunta + '%',))
        respuesta = cursor.fetchone()
        if respuesta:
            await ctx.send(respuesta[0])  # Enviar solo la respuesta encontrada
        else:
            await ctx.send(f'Lo siento, no tengo información sobre "{pregunta}".')

    except Exception as e:
        await ctx.send("Ocurrió un error al intentar obtener la respuesta.")
        print(f"Error: {e}")

# Comando para permitir a los moderadores actualizar respuestas
@client.command()
@commands.has_permissions(administrator=True)
async def actualizar_respuesta(ctx, pregunta: str, *, nueva_respuesta: str):
    """
    Comando para permitir a los administradores actualizar una respuesta existente en la base de datos.

    Parameters:
        ctx (commands.Context): Contexto del comando.
        pregunta (str): Pregunta para actualizar.
        nueva_respuesta (str): Nueva respuesta para actualizar en la base de datos.

    """
    try:
        # Actualizar la respuesta en la base de datos que coincide parcialmente con la pregunta proporcionada
        cursor.execute('UPDATE preguntas_respuestas SET respuesta = ? WHERE pregunta LIKE ?', (nueva_respuesta, '%' + pregunta + '%',))
        conn.commit()
        await ctx.send(f"Se ha actualizado la respuesta para '{pregunta}'.")

    except Exception as e:
        await ctx.send(f"Ocurrió un error al actualizar la respuesta: {str(e)}")
        print(f"Error: {e}")

# Evento que se activa cuando alguien menciona al bot en un mensaje
@client.event
async def on_message(message):
    """
    Evento activado cuando alguien envía un mensaje en el servidor de Discord.

    Parameters:
        message (discord.Message): Mensaje enviado en el servidor de Discord.

    """
    if message.author == client.user:
        return

    if client.user.mentioned_in(message):
        mentioned_questions = []

        # Obtener todas las preguntas almacenadas en la base de datos
        cursor.execute('SELECT pregunta, respuesta FROM preguntas_respuestas')
        preguntas_respuestas = cursor.fetchall()

        # Buscar si alguna de las preguntas está mencionada en el mensaje
        for pregunta, respuesta in preguntas_respuestas:
            if pregunta.lower() in message.content.lower():
                mentioned_questions.append((pregunta, respuesta))

        # Responder si se encontraron preguntas mencionadas
        if mentioned_questions:
            response = "\n".join([f'{pregunta}: {respuesta}' for pregunta, respuesta in mentioned_questions])
            await message.channel.send(f"Estas son algunas respuestas que podrían ser de ayuda:\n{response}")
        else:
            await message.channel.send("No tengo la respuesta, pero prometo que voy a investigar.")

    await client.process_commands(message)

# Token de autenticación del bot obtenido desde el archivo .env
TOKEN = os.getenv('DISCORD_TOKEN')
print("Discord Token:", TOKEN)  # Mostrar el token de Discord cargado correctamente

# Conectar el bot usando el token proporcionado
client.run(TOKEN)

# Cerrar la conexión a la base de datos al finalizar
conn.close()
