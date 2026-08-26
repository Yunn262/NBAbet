import requests


BASE_URL = "https://footballdata.io/api/v1"


class FootballAPI:

    def __init__(self, api_key):
        self.api_key = api_key

        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        }

    def get(self, endpoint, params=None):

        try:

            response = requests.get(
                BASE_URL + endpoint,
                headers=self.headers,
                params=params,
                timeout=30,
            )

            try:
                data = response.json()
            except Exception:
                data = {
                    "success": False,
                    "error": response.text,
                }

            if response.status_code != 200:

                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": data,
                }

            return data

        except Exception as e:

            return {
                "success": False,
                "error": str(e),
            }

    # =====================================================
    # JOGOS
    # =====================================================

    def today(self):
        return self.get("/fixtures/today")

    def live(self):
        return self.get("/fixtures/live")

    def upcoming(self):
        return self.get("/fixtures/upcoming")

    def results(self):
        return self.get("/fixtures/results")

    def matches_by_date(self, date):

        return self.get(
            f"/matches/date/{date}",
            params={
                "limit": 100,
                "sort": "asc",
            },
        )

    def matches(self, date=None, page=1, limit=100):

        params = {
            "page": page,
            "limit": limit,
        }

        if date:
            params["date"] = date

        return self.get(
            "/matches",
            params=params,
        )

    # =====================================================
    # PARTIDA
    # =====================================================

    def match(self, match_id):

        return self.get(
            f"/matches/{match_id}"
        )

    def stats(self, match_id):

        return self.get(
            f"/matches/{match_id}/stats"
        )

    def probabilities(self, match_id):

        return self.get(
            f"/matches/{match_id}/probabilities"
        )

    def predictions(self, match_id):

        return self.get(
            f"/matches/{match_id}/predictions"
        )

    def odds(self, match_id):

        return self.get(
            f"/matches/{match_id}/odds"
        )

    def btts(self, match_id):

        return self.get(
            f"/matches/{match_id}/btts"
        )

    def corners(self, match_id):

        return self.get(
            f"/matches/{match_id}/corners"
        )

    # =====================================================
    # TIMES
    # =====================================================

    def search(self, query, search_type=None):

        params = {
            "q": query,
            "limit": 25,
        }

        if search_type:
            params["type"] = search_type

        return self.get(
            "/search",
            params=params,
        )

    def team(self, team_id):

        return self.get(
            f"/teams/{team_id}"
        )

    def team_stats(self, team_id):

        return self.get(
            f"/teams/{team_id}/stats"
        )

    def team_matches(self, team_id):

        return self.get(
            f"/teams/{team_id}/matches",
            params={
                "limit": 100
            },
        )

    def h2h(self, team_a, team_b):

        return self.get(
            f"/teams/{team_a}/h2h/{team_b}"
        )

    # =====================================================
    # LIGAS
    # =====================================================

    def leagues(self):

        return self.get(
            "/leagues",
            params={
                "limit": 100
            },
        )

    def standings(self, league_id):

        return self.get(
            f"/leagues/{league_id}/standings"
        )

    # =====================================================
    # CONTA
    # =====================================================

    def usage(self):

        return self.get(
            "/account/usage"
        )

    def coverage(self):

        return self.get(
            "/meta/coverage"
        )
