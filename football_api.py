# -*- coding: utf-8 -*-
"""Cliente para a FootballData API.

Melhorias face Ã  versÃ£o original:
- Usa requests.Session() para reaproveitar conexÃµes (mais rÃ¡pido quando
  chamamos vÃ¡rios endpoints seguidos, como na pÃ¡gina de anÃ¡lise).
- ExceÃ§Ãµes tratadas de forma especÃ­fica (rede vs. JSON invÃ¡lido).
- Retry simples com backoff em erros de rede/5xx transitÃ³rios.
- ValidaÃ§Ã£o da api_key na criaÃ§Ã£o do cliente.
"""

import time
from typing import Any, Dict, Optional

import requests


BASE_URL = "https://footballdata.io/api/v1"

DEFAULT_TIMEOUT = 30
MAX_RETRIES = 2
RETRY_BACKOFF_SECONDS = 1.5


class FootballAPI:

    def __init__(self, api_key: str, timeout: int = DEFAULT_TIMEOUT):
        if not api_key:
            raise ValueError("api_key nÃ£o pode ser vazia.")

        self.api_key = api_key
        self.timeout = timeout

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
            }
        )

    def close(self) -> None:
        """Fecha a sessÃ£o HTTP. Chamar quando o cliente jÃ¡ nÃ£o for necessÃ¡rio."""
        self.session.close()

    def __enter__(self) -> "FootballAPI":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Faz um GET Ã  API, devolvendo sempre um dict.

        Em caso de erro, devolve {"success": False, "error": ...} em vez
        de deixar a exceÃ§Ã£o propagar â€” assim o resto da app nÃ£o precisa
        de estar cheio de try/except.
        """
        url = BASE_URL + endpoint
        last_error = None

        for attempt in range(MAX_RETRIES + 1):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.timeout,
                )
            except requests.exceptions.Timeout as exc:
                last_error = f"Timeout ao contactar a API: {exc}"
            except requests.exceptions.ConnectionError as exc:
                last_error = f"Erro de ligaÃ§Ã£o Ã  API: {exc}"
            except requests.exceptions.RequestException as exc:
                last_error = f"Erro ao contactar a API: {exc}"
            else:
                # Erros 5xx costumam ser transitÃ³rios â€” vale a pena tentar de novo.
                if response.status_code >= 500 and attempt < MAX_RETRIES:
                    last_error = f"Erro {response.status_code} do servidor."
                    time.sleep(RETRY_BACKOFF_SECONDS * (attempt + 1))
                    continue

                return self._parse_response(response)

            # Erro de rede: espera antes de tentar de novo (exceto na Ãºltima tentativa).
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS * (attempt + 1))

        return {"success": False, "error": last_error}

    @staticmethod
    def _parse_response(response: requests.Response) -> Dict[str, Any]:
        try:
            data = response.json()
        except ValueError:
            data = {"success": False, "error": response.text}

        if response.status_code != 200:
            return {
                "success": False,
                "status_code": response.status_code,
                "error": data,
            }

        return data

    # =====================================================
    # JOGOS
    # =====================================================

    def today(self) -> Dict[str, Any]:
        return self.get("/fixtures/today")

    def live(self) -> Dict[str, Any]:
        return self.get("/fixtures/live")

    def upcoming(self) -> Dict[str, Any]:
        return self.get("/fixtures/upcoming")

    def results(self) -> Dict[str, Any]:
        return self.get("/fixtures/results")

    def matches_by_date(self, date: str) -> Dict[str, Any]:
        return self.get(
            f"/matches/date/{date}",
            params={"limit": 100, "sort": "asc"},
        )

    def matches(self, date: Optional[str] = None, page: int = 1, limit: int = 100) -> Dict[str, Any]:
        params = {"page": page, "limit": limit}

        if date:
            params["date"] = date

        return self.get("/matches", params=params)

    # =====================================================
    # PARTIDA
    # =====================================================

    def match(self, match_id) -> Dict[str, Any]:
        return self.get(f"/matches/{match_id}")

    def stats(self, match_id) -> Dict[str, Any]:
        return self.get(f"/matches/{match_id}/stats")

    def probabilities(self, match_id) -> Dict[str, Any]:
        return self.get(f"/matches/{match_id}/probabilities")

    def predictions(self, match_id) -> Dict[str, Any]:
        return self.get(f"/matches/{match_id}/predictions")

    def odds(self, match_id) -> Dict[str, Any]:
        return self.get(f"/matches/{match_id}/odds")

    def btts(self, match_id) -> Dict[str, Any]:
        return self.get(f"/matches/{match_id}/btts")

    def corners(self, match_id) -> Dict[str, Any]:
        return self.get(f"/matches/{match_id}/corners")

    # =====================================================
    # TIMES
    # =====================================================

    def search(self, query: str, search_type: Optional[str] = None) -> Dict[str, Any]:
        params = {"q": query, "limit": 25}

        if search_type:
            params["type"] = search_type

        return self.get("/search", params=params)

    def team(self, team_id) -> Dict[str, Any]:
        return self.get(f"/teams/{team_id}")

    def team_stats(self, team_id) -> Dict[str, Any]:
        return self.get(f"/teams/{team_id}/stats")

    def team_matches(self, team_id) -> Dict[str, Any]:
        return self.get(f"/teams/{team_id}/matches", params={"limit": 100})

    def h2h(self, team_a, team_b) -> Dict[str, Any]:
        return self.get(f"/teams/{team_a}/h2h/{team_b}")

    # =====================================================
    # LIGAS
    # =====================================================

    def leagues(self) -> Dict[str, Any]:
        return self.get("/leagues", params={"limit": 100})

    def standings(self, league_id) -> Dict[str, Any]:
        return self.get(f"/leagues/{league_id}/standings")

    # =====================================================
    # CONTA
    # =====================================================

    def usage(self) -> Dict[str, Any]:
        return self.get("/account/usage")

    def coverage(self) -> Dict[str, Any]:
        return self.get("/meta/coverage")
