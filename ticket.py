def gerar_bilhete(jogos, minimo=10):

    selecionados = []

    for jogo in jogos:

        prediction = jogo.get(
            "prediction"
        )

        if not prediction:
            continue

        melhor = prediction.get(
            "best"
        )

        if not melhor:
            continue

        confidence = melhor.get(
            "confidence",
            0
        )

        if confidence >= 65:

            selecionados.append({

                "game_id":
                    jogo.get("game_id"),

                "home":
                    jogo.get("home_name"),

                "away":
                    jogo.get("away_name"),

                "market":
                    melhor.get("market"),

                "confidence":
                    confidence
            })

    selecionados.sort(
        key=lambda x:
        x["confidence"],
        reverse=True
    )

    return selecionados[:max(minimo, len(selecionados))]
