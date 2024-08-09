import discord # type: ignore
from discord.ext import commands, tasks # type: ignore
import requests
import os
import random
import asyncio
from dotenv import load_dotenv

# Cargar el token de Discord desde el archivo .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN_BALOO')

# Configuración del bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Función para obtener preguntas de trivia de una API
def obtener_pregunta_tematica(tema):
    url = f"https://opentdb.com/api.php?amount=1&category={tema}&type=multiple"
    response = requests.get(url)
    data = response.json()
    if data['response_code'] == 0:
        return data['results'][0]
    return None

# Comando para generar una trivia
@bot.command(name='trivia')
async def trivia(ctx, tema):
    pregunta_data = obtener_pregunta_tematica(tema)
    if pregunta_data:
        pregunta = pregunta_data['question']
        respuestas = pregunta_data['incorrect_answers'] + [pregunta_data['correct_answer']]
        random.shuffle(respuestas)
        
        # Enviar la pregunta y opciones
        opciones = '\n'.join([f"{i+1}. {respuesta}" for i, respuesta in enumerate(respuestas)])
        await ctx.send(f"**Pregunta:** {pregunta}\n\n**Opciones:**\n{opciones}")

        # Esperar un tiempo para recoger votos
        await asyncio.sleep(300)  # Espera de 5 minutos

        # Recoger votos
        def check(m):
            return m.author != bot.user and m.content.isdigit() and 1 <= int(m.content) <= len(respuestas)

        votos = {}
        try:
            while True:
                mensaje = await bot.wait_for('message', timeout=300, check=check)
                opcion_votada = int(mensaje.content)
                votos[mensaje.author] = opcion_votada
        except asyncio.TimeoutError:
            pass

        # Contar los votos
        conteo_votos = [list(votos.values()).count(i+1) for i in range(len(respuestas))]
        mayor_voto = max(conteo_votos)
        mejor_respuesta = [i+1 for i, count in enumerate(conteo_votos) if count == mayor_voto]

        # Mostrar resultados
        respuesta_correcta = pregunta_data['correct_answer']
        indice_correcto = respuestas.index(respuesta_correcta) + 1
        if indice_correcto in mejor_respuesta:
            await ctx.send(f"La respuesta correcta es **{respuesta_correcta}** 🎉. Fue votada correctamente por {mayor_voto} usuarios.")
        else:
            await ctx.send(f"Nadie acertó. La respuesta correcta era **{respuesta_correcta}**.")

    else:
        await ctx.send("Lo siento, no pude encontrar una pregunta de trivia para este tema.")

# Iniciar el bot
bot.run(TOKEN)
