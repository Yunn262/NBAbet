from typing import Optional, Dict, Any, Tuple, List, Union


def get_data(response: Any) -> Dict:
    """Extrai o campo 'data' se existir e for dicionário."""
    if not isinstance(response, dict):
        return {}
    data = response.get("data")
    return data if isinstance(data, dict) else {}


def extract_predictions(response: Dict) -> Dict:
    """Extrai previsões do campo 'predictions' ou retorna dados diretamente."""
    data = get_data(response)
    predictions = data.get("predictions", data)
    return predictions if isinstance(predictions, dict) else {}


def safe_percentage(value: Optional[Union[str, float]]) -> Optional[float]:
    """Converte valor para float e ajusta para percentual se necessário."""
    if value is None:
        return None
    try:
        value_float = float(value)
        if value_float <= 1:
            value_float *= 100
        return round(value_float, 1)
    except (ValueError, TypeError):
        return None


def confidence_label(value: Optional[float]) -> str:
    """Retorna etiqueta de confiança baseada no valor percentual."""
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


def get_best_value(*dicts: Dict[str, Any], key: str) -> Dict:
    """Tenta obter o valor correspondente a 'key' do primeiro dicionário que contiver."""
    for d in dicts:
        value = d.get(key)
        if value is not None:
            return value
    return {}


def analisar_partida(
    predictions_response: Dict,
    probabilities_response: Optional[Dict] = None,
    stats_response: Optional[Dict] = None,
) -> Dict:

    prediction = extract_predictions(predictions_response)
    probabilities = get_data(probabilities_response or {})
    stats = get_data(stats_response or {})

    winner = get_best_value(prediction, probabilities, key="match_winner") or get_best_value(prediction, probabilities, key="winner") or {}
    home = safe_percentage(winner.get("home"))
    draw = safe_percentage(winner.get("draw"))
    away = safe_percentage(winner.get("away"))

    goals = get_best_value(prediction, probabilities, key="goals")
    over05 = safe_percentage(goals.get("over_0_5"))
    over15 = safe_percentage(goals.get("over_1_5"))
    over25 = safe_percentage(goals.get("over_2_5"))
    over35 = safe_percentage(goals.get("over_3_5"))
    over45 = safe_percentage(goals.get("over_4_5"))

    btts_data = get_best_value(prediction, probabilities, key="btts")
    btts = safe_percentage(btts_data.get("potential") or btts_data.get("yes"))

    corners_data = get_best_value(prediction, probabilities, key="corners")
    corners_potential = safe_percentage(corners_data.get("potential"))
    corners85 = safe_percentage(corners_data.get("over_8_5") or corners_data.get("over_8_5_potential"))
    corners95 = safe_percentage(corners_data.get("over_9_5") or corners_data.get("over_9_5_potential"))
    corners105 = safe_percentage(corners_data.get("over_10_5") or corners_data.get("over_10_5_potential"))

    xg = prediction.get("xg_prematch", {})
    xg_home = xg.get("home")
    xg_away = xg.get("away")
    xg_total = xg.get("total")

    ppg = prediction.get("ppg", {})
    ppg_home = ppg.get("home")
    ppg_away = ppg.get("away")

    markets: List[Tuple[str, Optional[float]]] = [
        ("Over 1.5 gols", over15),
        ("Over 2.5 gols", over25),
        ("BTTS", btts),
        ("Over 8.5 escanteios", corners85),
        ("Over 9.5 escanteios", corners95)
    ]

    markets = [m for m in markets if m[1] is not None]
    markets.sort(key=lambda x: x[1], reverse=True)

    best_market, best_confidence = markets[0] if markets else ("Dados insuficientes", None)

    confidence_values = [v for v in [home, draw, away, over15, over25, btts, corners85] if v is not None]
    average_confidence = sum(confidence_values) / len(confidence_values) if confidence_values else None

    picks = []
    if over15 and over15 >= 70:
        picks.append(("⚽ Over 1.5 gols", over15))
    if over25 and over25 >= 70:
        picks.append(("⚽ Over 2.5 gols", over25))
    if btts and btts >= 65:
        picks.append(("⚽ BTTS — Sim", btts))
    if corners85 and corners85 >= 65:
        picks.append(("🚩 Over 8.5 escanteios", corners85))

    result_options = [(label, val) for label, val in [("Casa", home), ("Empate", draw), ("Fora", away)] if val is not None]
    best_result = max(result_options, key=lambda x: x[1]) if result_options else ("Sem dados", None)

    return {
        "winner": {"home": home, "draw": draw, "away": away},
        "goals": {"over_0_5": over05, "over_1_5": over15, "over_2_5": over25, "over_3_5": over35, "over_4_5": over45},
        "btts": btts,
        "corners": {"potential": corners_potential, "over_8_5": corners85, "over_9_5": corners95, "over_10_5": corners105},
        "xg": {"home": xg_home, "away": xg_away, "total": xg_total},
        "ppg": {"home": ppg_home, "away": ppg_away},
        "best_market": best_market,
        "best_confidence": best_confidence,
        "confidence": average_confidence,
        "confidence_label": confidence_label(average_confidence),
        "best_result": best_result,
        "picks": picks,
    }
