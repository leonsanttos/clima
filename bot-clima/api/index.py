import os
import requests
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# ===== CARREGAR VARIÁVEIS DO .env =====
load_dotenv()  # procura .env na mesma pasta do script

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_KEY_CLIMA = os.getenv("OPENWEATHER_KEY")
URL_CLIMA = "https://api.openweathermap.org/data/2.5/weather"

dias_pt = {
    "Monday": "Segunda-feira",
    "Tuesday": "Terça-feira",
    "Wednesday": "Quarta-feira",
    "Thursday": "Quinta-feira",
    "Friday": "Sexta-feira",
    "Saturday": "Sábado",
    "Sunday": "Domingo"
}

def timestamp_para_hora(ts, timezone_sec):
    local_time = datetime.utcfromtimestamp(ts) + timedelta(seconds=timezone_sec)
    return local_time.strftime("%H:%M")

def pegar_clima(cidade):
    parametros = {
        "q": cidade,
        "appid": API_KEY_CLIMA,
        "lang": "pt_br",
        "units": "metric"
    }
    resposta = requests.get(URL_CLIMA, params=parametros)
    if resposta.status_code == 200:
        dados = resposta.json()
        nome = dados["name"]
        temp = dados["main"]["temp"]
        sensacao = dados["main"].get("feels_like", temp)
        descricao = dados["weather"][0]["description"]
        umidade = dados["main"]["humidity"]
        vento = round(dados["wind"]["speed"] * 3, 2)
        clima_id = dados["weather"][0]["id"]
        timezone_sec = dados["timezone"]

        hora_utc = datetime.now(timezone.utc)
        hora_atual = hora_utc + timedelta(seconds=timezone_sec)
        dia_semana_str = dias_pt[hora_atual.strftime("%A")]

        sunrise = timestamp_para_hora(dados["sys"]["sunrise"], timezone_sec)
        sunset = timestamp_para_hora(dados["sys"]["sunset"], timezone_sec)

        chuva = dados.get("rain", {}).get("1h", 0)
        chuva_str = f"{chuva} mm" if chuva > 0 else "0 mm"

        if 200 <= clima_id < 300:
            emoji_clima = "⛈️"
        elif 300 <= clima_id < 500:
            emoji_clima = "🌦️"
        elif 500 <= clima_id < 600:
            emoji_clima = "🌧️"
        elif 600 <= clima_id < 700:
            emoji_clima = "❄️"
        elif 700 <= clima_id < 800:
            emoji_clima = "🌫️"
        elif clima_id == 800:
            emoji_clima = "☀️"
        elif 801 <= clima_id <= 804:
            emoji_clima = "🌤️"
        else:
            emoji_clima = "🌈"

        mensagem = (
            f"📝 Clima em {nome}:\n"
            f"📅 {dia_semana_str}, {hora_atual.strftime('%d/%m/%Y')} \n"
            f"⏰ Hora local: {hora_atual.strftime('%H:%M')}\n"
            f"{emoji_clima} {descricao.capitalize()}\n"
            f"🌡️ Temp: {temp}°C (sensação: {sensacao}°C)\n"
            f"💧 Umidade: {umidade}%\n"
            f"💨 Vento: {vento} km/h\n"
            f"🌅 Nascer do sol: {sunrise}\n"
            f"🌇 Pôr do sol: {sunset}\n"
            f"🌧️ Chuva (última hora): {chuva_str}"
        )
        return mensagem
    elif resposta.status_code == 404:
        return "❌ Cidade não encontrada."
    else:
        return f"❌ Erro na API: {resposta.status_code}"

# ===== TELEGRAM BOT =====
app = Flask(__name__)
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()

async def clima(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("Use assim: /clima nome_da_cidade")
    else:
        cidade = " ".join(context.args)
        previsao = pegar_clima(cidade)
        await update.message.reply_text(previsao)

telegram_app.add_handler(CommandHandler("clima", clima))

# ===== ROTA DE TESTE (Home) =====
@app.route("/")
def index():
    return "🚀 Servidor funcionando!"

# ===== WEBHOOK PARA VERCEL =====
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, telegram_app.bot)
    telegram_app.update_queue.put(update)
    return jsonify({"status":"ok"})

# ===== PARA RODAR LOCALMENTE COM POLLING =====
VERCEL_ENV = os.getenv("VERCEL")  # Vercel define isso automaticamente

if __name__ == "__main__" and not VERCEL_ENV:
    print("Bot rodando localmente...")
    telegram_app.run_polling()
