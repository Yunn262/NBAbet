# -*- coding: utf-8 -*-
"""Motor de análise de partidas.

Atualização importante: a API da footballdata.io exige o plano PRO para
/matches/{id}/predictions, /btts e /corners. No plano free, só
/matches/{id}/probabilities e /matches/{id}/stats estão disponíveis — e
esse endpoint devolve os campos com nomes diferentes (ex.: "home_win" em
vez de "match_winner": {"home": ...}).

Este módulo agora:
- Normaliza os dois formatos (Pro: match_winner.home/draw/away vs
  Free: home_win/draw/away_win) num único formato interno.
- Expõe is_plan_gated() para o app conseguir avisar o utilizador quando um
  mercado não apareceu por limitação de plano, em vez de mostrar
  "Dados insuficientes" sem explicação.
- stats_response entra na cadeia de fallback (antes era ignorado).
"""

from typing import Any, Dict, List, Optional, Sequence, Tuple, Union


# ============================================================
# LIMIARES DE CONFIANÇA
# ============================================================

CONFIDENCE_VERY_HIGH = 80
CONFIDENCE_HIGH = 70
CONFIDENCE_MEDIUM = 60
CONFIDENCE_LOW = 50

PICK_THRESHOLD_GOALS = 70
PICK_THRESHOLD_BTTS = 65
PICK_THRESHOLD_CORNERS = 65

PLAN_GATED_CODES = {"plan_upgrade_required", "api_key_inactive"}


def is_plan_gated(response: Any) -> bool:
    """True se a resposta indica que o endpoint exige um plano superior
    (ex.: 403 plan_upgrade_required no plano Pro)."""
    if not isinstance(response, dict):
        return False

    if response.get("success") is not False:
        return False

    if response.get("status_code") == 403:
        return True

    error = response.get("error")
    if isinstance(error, dict):
        # A resposta de erro pode vir aninhada: {"error": {"error": {"code": ...}}}
        code = error.get("code")
        if code in PLAN_GATED_CODES:
            return True
        inner_error = error.get("error")
        if isinstance(inner_error, dict) and inner_error.get("code") in PLAN_GATED_CODES:
            return True

    return False


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
    if value >= CONFIDENCE_VERY_HIGH:
        return "🔥 MUITO ALTA"
    if value >= CONFIDENCE_HIGH:
        return "🟢 ALTA"
    if value >= CONFIDENCE_MEDIUM:
        return "🟡 MÉDIA"
    if value >= CONFIDENCE_LOW:
        return "🟠 BAIXA"
    return "🔴 MUITO BAIXA"


def get_best_value(*dicts: Dict[str, Any], key: str) -> Dict:
    """Devolve o valor de 'key' no primeiro dicionário (na ordem dada) que o contiver."""
    for d in dicts:
        value = d.get(key)
        if value is not None:
            return value
    return {}


def get_best_value_multi(dicts: Sequence[Dict[str, Any]], keys: Sequence[str]) -> Dict:
    """Como get_best_value, mas tenta várias chaves alternativas."""
    for key in keys:
        value = get_best_value(*dicts, key=key)
        if value:
            return value
    return {}


def extract_winner(*sources: Dict[str, Any]) -> Dict[str, Optional[float]]:
    """Extrai probabilidades de vencedor, aceitando dois formatos:

    - Plano Pro (endpoint /predictions): {"match_winner": {"home": x, "draw": y, "away": z}}
    - Plano Free (endpoint /probabilities): {"home_win": x, "draw": y, "away_win": z} (achatado)
    """
    nested = get_best_value_multi(sources, keys=("match_winner", "winner"))
    if nested:
        return {
            "home": safe_percentage(nested.get("home")),
            "draw": safe_percentage(nested.get("draw")),
            "away": safe_percentage(nested.get("away")),
        }

    # Formato achatado do plano free.
    for source in sources:
        if not isinstance(source, dict):
            continue
        home = source.get("home_win")
        draw = source.get("draw")
        away = source.get("away_win")
        if home is not None or draw is not None or away is not None:
            return {
                "home": safe_percentage(home),
                "draw": safe_percentage(draw),
                "away": safe_percentage(away),
            }

    return {"home": None, "draw": None, "away": None}


def analisar_partida(
    predictions_response: Dict,
    probabilities_response: Optional[Dict] = None,
    stats_response: Optional[Dict] = None,
) -> Dict:
    """Combina predictions, probabilities e stats numa análise única.

    As três fontes são consultadas por ordem de prioridade (predictions >
    probabilities > stats) — a primeira que tiver o dado pedido é usada.
    """

    prediction = extract_predictions(predictions_response)
    probabilities = get_data(probabilities_response or {})
    stats = get_data(stats_response or {})

    sources = (prediction, probabilities, stats)

    winner = extract_winner(*sources)
    home = winner["home"]
    draw = winner["draw"]
    away = winner["away"]

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

    xg = prediction.get("xg_prematch") or stats.get("xg_prematch") or {}
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
        picks.append(("⚽ Over 1.5 gols", over15))
    if over25 and over25 >= PICK_THRESHOLD_GOALS:
        picks.append(("⚽ Over 2.5 gols", over25))
    if btts and btts >= PICK_THRESHOLD_BTTS:
        picks.append(("⚽ BTTS — Sim", btts))
    if corners85 and corners85 >= PICK_THRESHOLD_CORNERS:
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
        # Sinaliza ao app quais fontes ficaram bloqueadas por plano, para
        # mostrar um aviso em vez de "Dados insuficientes" sem explicação.
        "predictions_plan_gated": is_plan_gated(predictions_response),
    }
