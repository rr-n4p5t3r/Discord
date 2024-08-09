import discord
from discord.ext import commands
import requests
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde un archivo .env
load_dotenv()

# Crear una instancia de Intents con los intents necesarios
intents = discord.Intents.default()
intents.message_content = True  # Habilitar el intent para manejar el contenido de los mensajes

# Crear un cliente de Discord con los intents especificados
client = commands.Bot(command_prefix='!', intents=intents)

# OpenWeatherMap API key
API_KEY = os.getenv('WEATHER_API_KEY')

# URL base para la API de OpenWeatherMap
BASE_URL = "http://api.openweathermap.org/data/2.5/forecast"

# Función para obtener el clima de una ciudad
def get_weather(city_name):
    params = {
        'q': city_name,
        'appid': API_KEY,
        'units': 'metric',
        'lang': 'es',
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()
    
    if data["cod"] != "200":
        return None

    # Temperatura actual
    current_temp = data["list"][0]["main"]["temp"]
    
    # Pronóstico de las siguientes 12 horas (4 intervalos de 3 horas)
    forecast = []
    for i in range(4):
        temp = data["list"][i]["main"]["temp"]
        description = data["list"][i]["weather"][0]["description"]
        time = data["list"][i]["dt_txt"]
        forecast.append(f"{time}: {temp}°C, {description}")

    return current_temp, forecast

# Comando para obtener el clima
@client.command()
async def clima(ctx, *, city: str):
    weather = get_weather(city)
    
    if weather is None:
        await ctx.send(f"No se pudo encontrar el clima para '{city}'. Por favor, verifica el nombre de la ciudad.")
    else:
        current_temp, forecast = weather
        response = f"El clima actual en {city} es de {current_temp}°C.\n\nPronóstico para las próximas 12 horas:\n"
        response += "\n".join(forecast)
        await ctx.send(response)

# Evento que se activa cuando el bot se conecta exitosamente
@client.event
async def on_ready():
    print(f'Conectado como {client.user}')

# Token de autenticación del bot
TOKEN = os.getenv('DISCORD_TOKEN_MAX')
print("Discord Token:", TOKEN)  # Verificar que el token de Discord se cargue correctamente

# Conectar el bot usando el token
client.run(TOKEN)
