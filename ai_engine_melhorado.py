# -*- coding: utf-8 -*-
"""Motor de anÃ¡lise de partidas.

Melhorias face Ã  versÃ£o original:
- `stats_response` deixa de ser ignorado: entra na cadeia de fallback junto
  com predictions/probabilities (antes era calculado e nunca usado).
- Busca por chaves alternativas (ex.: "match_winner" / "winner") passou a
  ser uma Ãºnica funÃ§Ã£o em vez de duas chamadas encadeadas com `or`.
- Limiares de confianÃ§a (70, 65, 80...) viraram constantes nomeadas.
"""

from typing import Any, Dict, List, Optional, Sequence, Tuple, Union


# ============================================================
# LIMIARES DE CONFIANÃ‡A
# ============================================================

CONFIDENCE_VERY_HIGH = 80
CONFIDENCE_HIGH = 70
CONFIDENCE_MEDIUM = 60
CONFIDENCE_LOW = 50

PICK_THRESHOLD_GOALS = 70
PICK_THRESHOLD_BTTS = 65
PICK_THRESHOLD_CORNERS = 65


def get_data(response: Any) -> Dict:
    """Extrai o campo 'data' se existir e for dicionÃ¡rio."""
    if not isinstance(response, dict):
        return {}
    data = response.get("data")
    return data if isinstance(data, dict) else {}


def extract_predictions(response: Dict) -> Dict:
    """Extrai previsÃµes do campo 'predictions' ou retorna dados diretamente."""
    data = get_data(response)
    predictions = data.get("predictions", data)
    return predictions if isinstance(predictions, dict) else {}


def safe_percentage(value: Optional[Union[str, float]]) -> Optional[float]:
    """Converte valor para float e ajusta para percentual se necessÃ¡rio."""
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
    """Retorna etiqueta de confianÃ§a baseada no valor percentual."""
    if value is None:
        return "Sem dados"
    if value >= CONFIDENCE_VERY_HIGH:
        return "ðŸ”¥ MUITO ALTA"
    if value >= CONFIDENCE_HIGH:
        return "ðŸŸ¢ ALTA"
    if value >= CONFIDENCE_MEDIUM:
        return "ðŸŸ¡ MÃ‰DIA"
    if value >= CONFIDENCE_LOW:
        return "ðŸŸ  BAIXA"
    return "ðŸ”´ MUITO BAIXA"


def get_best_value(*dicts: Dict[str, Any], key: str) -> Dict:
    """Devolve o valor de 'key' no primeiro dicionÃ¡rio (na ordem dada) que o contiver."""
    for d in dicts:
        value = d.get(key)
        if value is not None:
            return value
    return {}


def get_best_value_multi(dicts: Sequence[Dict[str, Any]], keys: Sequence[str]) -> Dict:
    """Como get_best_value, mas tenta vÃ¡rias chaves alternativas (ex.: nomes
    diferentes que a API usa para o mesmo dado consoante o endpoint)."""
    for key in keys:
        value = get_best_value(*dicts, key=key)
        if value:
            return value
    return {}


def analisar_partida(
    predictions_response: Dict,
    probabilities_response: Optional[Dict] = None,
    stats_response: Optional[Dict] = None,
) -> Dict:
    """Combina predictions, probabilities e stats numa anÃ¡lise Ãºnica.

    As trÃªs fontes sÃ£o consultadas por ordem de prioridade (predictions >
    probabilities > stats) â€” a primeira que tiver o dado pedido Ã© usada.
    """

    prediction = extract_predictions(predictions_response)
    probabilities = get_data(probabilities_response or {})
    stats = get_data(stats_response or {})

    sources = (prediction, probabilities, stats)

    winner = get_best_value_multi(sources, keys=("match_winner", "winner"))
    home = safe_percentage(winner.get("home"))
    draw = safe_percentage(winner.get("draw"))
    away = safe_percentage(winner.get("away"))

    goals = get_best_value_multi(sources, keys=("goals",))
    over05 = safe_percentage(goals.get("over_0_5"))
    over15 = safe_percentage(goals.get("over_1_5"))
    over25 = safe_percentage(goals.get("over_2_5"))
    over35 = safe_percentage(goals.get("over_3_5"))
    over45 = safe_percentage(goals.get("over_4_5"))

    btts_data = get_best_value_multi(sources, keys=("btts",))
    btts = safe_percentage(btts_data.get("potential") or btts_data.get("yes"))

    corners_data = get_best_value_multi(sources, keys=("corners",))
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
        ("Over 9.5 escanteios", corners95),
    ]

    markets = [m for m in markets if m[1] is not None]
    markets.sort(key=lambda x: x[1], reverse=True)

    best_market, best_confidence = markets[0] if markets else ("Dados insuficientes", None)

    confidence_values = [v for v in [home, draw, away, over15, over25, btts, corners85] if v is not None]
    average_confidence = sum(confidence_values) / len(confidence_values) if confidence_values else None

    picks = []
    if over15 and over15 >= PICK_THRESHOLD_GOALS:
        picks.append(("âš½ Over 1.5 gols", over15))
    if over25 and over25 >= PICK_THRESHOLD_GOALS:
        picks.append(("âš½ Over 2.5 gols", over25))
    if btts and btts >= PICK_THRESHOLD_BTTS:
        picks.append(("âš½ BTTS â€” Sim", btts))
    if corners85 and corners85 >= PICK_THRESHOLD_CORNERS:
        picks.append(("ðŸš© Over 8.5 escanteios", corners85))

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
