name = "Ada Lovelace"
print(name.upper())
print(name.lower())


    if resposta.status_code == 200:
        dados = resposta.json()
        nome = dados["name"]
        temp = dados["main"]["temp"]
        descricao = dados["weather"][0]["description"]
        umidade = dados["main"]["humidity"]
        vento = (3.6 * dados["wind"]["speed"])
        return (f" Clima em {nome}.\n"
                f"🌤 {descricao}.\n"
                f"🌡️ Temp: {temp}°C\n"
                f"💧 Umidade: {umidade}%\n"
                f"💨 Vento: {vento} km/h")