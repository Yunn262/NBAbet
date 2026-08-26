from math import exp


def get_data(response):

    if not isinstance(response, dict):
        return {}

    data = response.get("data")

    if isinstance(data, dict):
        return data

    return {}


def extract_predictions(response):

    data = get_data(response)

    predictions = data.get(
        "predictions",
        data
    )

    if not isinstance(predictions, dict):
        return {}

    return predictions


def percentage(value):

    if value is None:
        return None

    try:

        value = float(value)

        if value <= 1:
            value *= 100

        return round(value, 1)

    except Exception:

        return None


def confidence_label(value):

    if value is None:
        return "Sem dados"

    if value >= 80:
        return "🔥 MUITO ALTA"

    if value >= 70:
        return "🟢 ALTA"

    if value >= 60:
        return "🟡 MÉDIA"

    if value >= 50:
        return "🟠 BAIXA"

    return "🔴 MUITO BAIXA"


def analisar_partida(
    predictions_response,
    probabilities_response=None,
    stats_response=None,
):

    prediction = extract_predictions(
        predictions_response
    )

    probabilities = get_data(
        probabilities_response or {}
    )

    stats = get_data(
        stats_response or {}
    )

    # =====================================================
    # RESULTADO
    # =====================================================

    winner = (
        prediction.get("match_winner")
        or probabilities.get("match_winner")
        or probabilities.get("winner")
        or {}
    )

    home = percentage(
        winner.get("home")
    )

    draw = percentage(
        winner.get("draw")
    )

    away = percentage(
        winner.get("away")
    )

    # =====================================================
    # GOLS
    # =====================================================

    goals = (
        prediction.get("goals")
        or probabilities.get("goals")
        or {}
    )

    over05 = percentage(
        goals.get("over_0_5")
    )

    over15 = percentage(
        goals.get("over_1_5")
    )

    over25 = percentage(
        goals.get("over_2_5")
    )

    over35 = percentage(
        goals.get("over_3_5")
    )

    over45 = percentage(
        goals.get("over_4_5")
    )

    # =====================================================
    # BTTS
    # =====================================================

    btts_data = (
        prediction.get("btts")
        or probabilities.get("btts")
        or {}
    )

    btts = percentage(
        btts_data.get("potential")
        or btts_data.get("yes")
    )

    # =====================================================
    # ESCANTEIOS
    # =====================================================

    corners_data = (
        prediction.get("corners")
        or probabilities.get("corners")
        or {}
    )

    corners_potential = percentage(
        corners_data.get("potential")
    )

    corners85 = percentage(
        corners_data.get("over_8_5")
        or corners_data.get(
            "over_8_5_potential"
        )
    )

    corners95 = percentage(
        corners_data.get("over_9_5")
        or corners_data.get(
            "over_9_5_potential"
        )
    )

    corners105 = percentage(
        corners_data.get("over_10_5")
        or corners_data.get(
            "over_10_5_potential"
        )
    )

    # =====================================================
    # XG
    # =====================================================

    xg = (
        prediction.get("xg_prematch")
        or {}
    )

    xg_home = xg.get("home")
    xg_away = xg.get("away")
    xg_total = xg.get("total")

    # =====================================================
    # PPG
    # =====================================================

    ppg = (
        prediction.get("ppg")
        or {}
    )

    ppg_home = ppg.get("home")
    ppg_away = ppg.get("away")

    # =====================================================
    # MERCADO PRINCIPAL
    # =====================================================

    markets = []

    if over15 is not None:
        markets.append(
            (
                "Over 1.5 gols",
                over15
            )
        )

    if over25 is not None:
        markets.append(
            (
                "Over 2.5 gols",
                over25
            )
        )

    if btts is not None:
        markets.append(
            (
                "BTTS",
                btts
            )
        )

    if corners85 is not None:
        markets.append(
            (
                "Over 8.5 escanteios",
                corners85
            )
        )

    if corners95 is not None:
        markets.append(
            (
                "Over 9.5 escanteios",
                corners95
            )
        )

    markets.sort(
        key=lambda x: x[1],
        reverse=True
    )

    if markets:

        best_market = markets[0][0]
        best_confidence = markets[0][1]

    else:

        best_market = "Dados insuficientes"
        best_confidence = None

    # =====================================================
    # CONFIANÇA GERAL
    # =====================================================

    confidence_values = [
        x for x in [
            home,
            draw,
            away,
            over15,
            over25,
            btts,
            corners85,
        ]
        if x is not None
    ]

    if confidence_values:

        average = sum(
            confidence_values
        ) / len(
            confidence_values
        )

    else:

        average = None

    # =====================================================
    # PALPITES
    # =====================================================

    picks = []

    if over15 is not None and over15 >= 70:

        picks.append(
            (
                "⚽ Over 1.5 gols",
                over15
            )
        )

    if over25 is not None and over25 >= 70:

        picks.append(
            (
                "⚽ Over 2.5 gols",
                over25
            )
        )

    if btts is not None and btts >= 65:

        picks.append(
            (
                "⚽ BTTS — Sim",
                btts
            )
        )

    if corners85 is not None and corners85 >= 65:

        picks.append(
            (
                "🚩 Over 8.5 escanteios",
                corners85
            )
        )

    # Resultado

    result_values = [
        ("Casa", home),
        ("Empate", draw),
        ("Fora", away),
    ]

    result_values = [
        x for x in result_values
        if x[1] is not None
    ]

    if result_values:

        best_result = max(
            result_values,
            key=lambda x: x[1]
        )

    else:

        best_result = (
            "Sem dados",
            None
        )

    return {

        "winner": {
            "home": home,
            "draw": draw,
            "away": away,
        },

        "goals": {
            "over_0_5": over05,
            "over_1_5": over15,
            "over_2_5": over25,
            "over_3_5": over35,
            "over_4_5": over45,
        },

        "btts": btts,

        "corners": {
            "potential": corners_potential,
            "over_8_5": corners85,
            "over_9_5": corners95,
            "over_10_5": corners105,
        },

        "xg": {
            "home": xg_home,
            "away": xg_away,
            "total": xg_total,
        },

        "ppg": {
            "home": ppg_home,
            "away": ppg_away,
        },

        "best_market": best_market,

        "best_confidence": best_confidence,

        "confidence": average,

        "confidence_label": confidence_label(
            average
        ),

        "best_result": best_result,

        "picks": picks,
    }
