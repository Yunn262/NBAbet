import requests
import streamlit as st
from datetime import date


BASE_URL = "https://api.sportradar.com"


def get_api_key():
    try:
        return st.secrets["SPORTRADAR_API_KEY"]
    except Exception:
        return None


def request_api(url):
    api_key = get_api_key()

    if not api_key:
        return {
            "error": "SPORTRADAR_API_KEY não configurada."
        }

    headers = {
        "x-api-key": api_key,
        "Accept": "application/json"
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=20
        )

        if response.status_code != 200:
            return {
                "error": f"HTTP {response.status_code}",
                "details": response.text[:500]
            }

        return response.json()

    except requests.RequestException as e:
        return {
            "error": str(e)
        }


def get_daily_schedule(
    selected_date=None,
    access_level="trial",
    language="br"
):
    """
    Obtém os jogos da NBA de um determinado dia.
    """

    if selected_date is None:
        selected_date = date.today()

    url = (
        f"{BASE_URL}/nba/"
        f"{access_level}/v8/"
        f"{language}/games/"
        f"{selected_date.year}/"
        f"{selected_date.month:02d}/"
        f"{selected_date.day:02d}/"
        f"schedule.json"
    )

    return request_api(url)


def get_game_summary(
    game_id,
    access_level="trial",
    language="br"
):
    """
    Obtém o resumo detalhado de uma partida.
    """

    url = (
        f"{BASE_URL}/nba/"
        f"{access_level}/v8/"
        f"{language}/games/"
        f"{game_id}/"
        f"summary.json"
    )

    return request_api(url)


def extract_games(data):
    """
    Converte a resposta da Sportradar
    para uma estrutura simples.
    """

    if not data or "error" in data:
        return []

    games = data.get("games", [])

    resultado = []

    for game in games:

        home = game.get("home", {})
        away = game.get("away", {})

        resultado.append({

            "game_id": game.get("id"),

            "status": game.get("status"),

            "scheduled": game.get("scheduled"),

            "home_id": home.get("id"),

            "home_name": home.get(
                "name",
                home.get("alias", "Casa")
            ),

            "home_alias": home.get(
                "alias",
                ""
            ),

            "away_id": away.get("id"),

            "away_name": away.get(
                "name",
                away.get("alias", "Fora")
            ),

            "away_alias": away.get(
                "alias",
                ""
            ),

            "venue": game.get(
                "venue",
                {}
            ).get("name", "")
        })

    return resultado
