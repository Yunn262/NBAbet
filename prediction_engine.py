import math


def clamp(value, minimum=1, maximum=99):
    return max(minimum, min(maximum, value))


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


def calculate_prediction(
    home_points_avg=112,
    away_points_avg=109,
    home_defense_avg=108,
    away_defense_avg=111,
    home_advantage=3.0
):
    """
    Motor inicial de previsão.

    Estes valores podem posteriormente ser
    substituídos pelas estatísticas reais
    da Sportradar.
    """

    expected_home = (
        home_points_avg +
        away_defense_avg
    ) / 2 + home_advantage

    expected_away = (
        away_points_avg +
        home_defense_avg
    ) / 2

    expected_total = (
        expected_home +
        expected_away
    )

    difference = expected_home - expected_away

    home_probability = (
        50 + difference * 4
    )

    away_probability = (
        100 - home_probability
    )

    home_probability = clamp(
        home_probability,
        5,
        95
    )

    away_probability = clamp(
        away_probability,
        5,
        95
    )

    over_200 = clamp(
        50 + (expected_total - 200) * 2
    )

    over_210 = clamp(
        50 + (expected_total - 210) * 2
    )

    over_220 = clamp(
        50 + (expected_total - 220) * 2
    )

    return {

        "expected_home": round(
            expected_home,
            1
        ),

        "expected_away": round(
            expected_away,
            1
        ),

        "expected_total": round(
            expected_total,
            1
        ),

        "home_probability": round(
            home_probability
        ),

        "away_probability": round(
            away_probability
        ),

        "over_200": round(
            over_200
        ),

        "over_210": round(
            over_210
        ),

        "over_220": round(
            over_220
        )
    }


def choose_best_prediction(prediction):

    markets = {

        "🏠 Vitória Casa":
            prediction["home_probability"],

        "🚀 Over 200.5 pontos":
            prediction["over_200"],

        "🔥 Over 210.5 pontos":
            prediction["over_210"],

        "💥 Over 220.5 pontos":
            prediction["over_220"]
    }

    best_market = max(
        markets,
        key=markets.get
    )

    confidence = markets[best_market]

    return {
        "market": best_market,
        "confidence": confidence
    }
