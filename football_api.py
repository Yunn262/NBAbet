import requests


BASE_URL = "https://footballdata.io/api/v1"


class FootballAPI:

    def __init__(self, api_key):

        self.api_key = api_key

        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    # =====================================================
    # REQUEST PRINCIPAL
    # =====================================================

    def get(self, endpoint, params=None):

        url = BASE_URL + endpoint

        try:

            response = requests.get(
                url,
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

        except requests.exceptions.Timeout:

            return {
                "success": False,
                "error": "Tempo limite da API excedido.",
            }

        except requests.exceptions.ConnectionError:

            return {
                "success": False,
                "error": "Não foi possível conectar à API.",
            }

        except Exception as e:

            return {
                "success": False,
                "error": str(e),
            }

    # =====================================================
    # JOGOS
    # =====================================================

    def today(self):

        return self.get(
            "/fixtures/today"
        )

    def upcoming(self):

        return self.get(
            "/fixtures/upcoming"
        )

    def live(self):

        return self.get(
            "/fixtures/live"
        )

    def results(self):

        return self.get(
            "/fixtures/results"
        )

    def matches_by_date(self, match_date):

        # Método oficial:
        # /matches/date/YYYY-MM-DD

        return self.get(
            f"/matches/date/{match_date}",
            params={
                "limit": 100,
                "sort": "asc",
            },
        )

    def matches_by_date_alt(self, match_date):

        # Segunda forma oficial:
        # /matches?date=YYYY-MM-DD

        return self.get(
            "/matches",
            params={
                "date": match_date,
                "limit": 100,
                "sort": "asc",
            },
        )

    def matches(
        self,
        date=None,
        league_id=None,
        season_id=None,
        team_id=None,
        status=None,
        page=1,
        limit=100,
    ):

        params = {
            "page": page,
            "limit": limit,
        }

        if date:
            params["date"] = date

        if league_id:
            params["league_id"] = league_id

        if season_id:
            params["season_id"] = season_id

        if team_id:
            params["team_id"] = team_id

        if status:
            params["status"] = status

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

    def events(self, match_id):

        return self.get(
            f"/matches/{match_id}/events"
        )

    def odds(self, match_id):

        return self.get(
            f"/matches/{match_id}/odds"
        )

    def probabilities(self, match_id):

        return self.get(
            f"/matches/{match_id}/probabilities"
        )

    def predictions(self, match_id):

        return self.get(
            f"/matches/{match_id}/predictions"
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

    def teams(
        self,
        query=None,
        country=None,
        page=1,
        limit=25,
    ):

        params = {
            "page": page,
            "limit": limit,
        }

        if query:
            params["q"] = query

        if country:
            params["country"] = country

        return self.get(
            "/teams",
            params=params,
        )

    def team(self, team_id):

        return self.get(
            f"/teams/{team_id}"
        )

    def team_matches(
        self,
        team_id,
        season_id=None,
        league_id=None,
        from_date=None,
        to_date=None,
        limit=100,
    ):

        params = {
            "limit": limit,
        }

        if season_id:
            params["season_id"] = season_id

        if league_id:
            params["league_id"] = league_id

        if from_date:
            params["from"] = from_date

        if to_date:
            params["to"] = to_date

        return self.get(
            f"/teams/{team_id}/matches",
            params=params,
        )

    def team_stats(self, team_id):

        return self.get(
            f"/teams/{team_id}/stats"
        )

    def h2h(
        self,
        team_id,
        opponent_id,
    ):

        return self.get(
            f"/teams/{team_id}/h2h/{opponent_id}"
        )

    # =====================================================
    # LIGAS
    # =====================================================

    def leagues(
        self,
        query=None,
        country=None,
        page=1,
        limit=100,
    ):

        params = {
            "page": page,
            "limit": limit,
        }

        if query:
            params["q"] = query

        if country:
            params["country"] = country

        return self.get(
            "/leagues",
            params=params,
        )

    def standings(self, league_id):

        return self.get(
            f"/leagues/{league_id}/standings"
        )

    def league_matches(
        self,
        league_id,
        date=None,
        season_id=None,
        limit=100,
    ):

        params = {
            "limit": limit,
        }

        if date:
            params["date"] = date

        if season_id:
            params["season_id"] = season_id

        return self.get(
            f"/leagues/{league_id}/matches",
            params=params,
        )

    # =====================================================
    # PESQUISA
    # =====================================================

    def search(
        self,
        query,
        search_type=None,
        limit=25,
    ):

        params = {
            "q": query,
            "limit": limit,
        }

        if search_type:
            params["type"] = search_type

        return self.get(
            "/search",
            params=params,
        )

    # =====================================================
    # CONTA
    # =====================================================

    def usage(self):

        return self.get(
            "/account/usage"
        )

    # =====================================================
    # META
    # =====================================================

    def status(self):

        return self.get(
            "/meta/status"
        )

    def coverage(self):

        return self.get(
            "/meta/coverage"
        )
