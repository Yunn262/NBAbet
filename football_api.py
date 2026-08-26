import requests
from datetime import date

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

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "message": response.text,
                }

            return response.json()

        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e),
            }

    def today(self):
        return self.get("/fixtures/today")

    def upcoming(self):
        return self.get("/fixtures/upcoming")

    def live(self):
        return self.get("/fixtures/live")

    def results(self):
        return self.get("/fixtures/results")

    def matches_by_date(self, match_date):
        return self.get(f"/matches/date/{match_date}")

    def match(self, match_id):
        return self.get(f"/matches/{match_id}")

    def stats(self, match_id):
        return self.get(f"/matches/{match_id}/stats")

    def probabilities(self, match_id):
        return self.get(f"/matches/{match_id}/probabilities")

    def odds(self, match_id):
        return self.get(f"/matches/{match_id}/odds")

    def predictions(self, match_id):
        return self.get(f"/matches/{match_id}/predictions")

    def btts(self, match_id):
        return self.get(f"/matches/{match_id}/btts")

    def corners(self, match_id):
        return self.get(f"/matches/{match_id}/corners")

    def teams(self):
        return self.get("/teams")

    def team(self, team_id):
        return self.get(f"/teams/{team_id}")

    def team_matches(self, team_id):
        return self.get(f"/teams/{team_id}/matches")

    def team_stats(self, team_id):
        return self.get(f"/teams/{team_id}/stats")

    def h2h(self, team_id, opponent_id):
        return self.get(f"/teams/{team_id}/h2h/{opponent_id}")

    def leagues(self):
        return self.get("/leagues")

    def standings(self, league_id):
        return self.get(f"/leagues/{league_id}/standings")

    def search(self, query):
        return self.get("/search", {"q": query})

    def usage(self):
        return self.get("/account/usage")
