import streamlit as st
import pandas as pd
from datetime import date

from football_api import FootballAPI


# =========================
# CONFIGURAÇÃO
# =========================

st.set_page_config(
    page_title="Football Stats AI",
    page_icon="⚽",
    layout="wide",
)


# =========================
# ESTILO
# =========================

st.markdown("""
<style>

.main {
    background-color: #05070b;
}

.block-container {
    padding-top: 1.5rem;
}

h1, h2, h3 {
    color: white;
}

.card {
    background: #10141c;
    border: 1px solid #202734;
    border-radius: 15px;
    padding: 20px;
    margin-bottom: 15px;
}

.match-card {
    background: linear-gradient(
        135deg,
        #10141c,
        #171d29
    );
    border-radius: 16px;
    padding: 20px;
    border: 1px solid #293244;
    margin-bottom: 15px;
}

.team {
    font-size: 20px;
    font-weight: bold;
    color: white;
}

.small {
    color: #8e99aa;
    font-size: 13px;
}

.prob {
    font-size: 26px;
    font-weight: bold;
    color: #4ade80;
}

.market {
    background: #0b0f16;
    border-radius: 10px;
    padding: 12px;
    margin: 5px;
    border: 1px solid #202734;
}

</style>
""", unsafe_allow_html=True)


# =========================
# API KEY
# =========================

try:
    API_KEY = st.secrets["FOOTBALLDATA_API_KEY"]
except Exception:
    API_KEY = ""

if not API_KEY:
    st.error(
        "API Key não encontrada. "
        "Adiciona FOOTBALLDATA_API_KEY nos Secrets do Streamlit."
    )
    st.stop()


api = FootballAPI(API_KEY)


# =========================
# SIDEBAR
# =========================

st.sidebar.title("⚽ Football Stats AI")

menu = st.sidebar.radio(
    "Menu",
    [
        "🏠 Dashboard",
        "📅 Jogos do Dia",
        "🔎 Analisar Jogo",
        "🔍 Buscar Time",
        "🏆 Classificação",
        "📊 Estatísticas",
        "💳 Uso da API",
    ],
)


# =========================
# FUNÇÕES
# =========================

def extract_list(data):

    if not data:
        return []

    if isinstance(data, list):
        return data

    if isinstance(data, dict):

        if isinstance(data.get("data"), list):
            return data["data"]

        for key in [
            "matches",
            "fixtures",
            "teams",
            "leagues",
            "results",
        ]:

            if isinstance(data.get(key), list):
                return data[key]

        if isinstance(data.get("data"), dict):

            for key in [
                "matches",
                "fixtures",
                "teams",
                "results",
            ]:

                if isinstance(data["data"].get(key), list):
                    return data["data"][key]

    return []


def get_team_name(team):

    if not team:
        return "?"

    if isinstance(team, str):
        return team

    return (
        team.get("name")
        or team.get("short_name")
        or team.get("title")
        or "?"
    )


def get_match_teams(match):

    home = (
        match.get("home_team")
        or match.get("home")
        or match.get("homeTeam")
        or {}
    )

    away = (
        match.get("away_team")
        or match.get("away")
        or match.get("awayTeam")
        or {}
    )

    return get_team_name(home), get_team_name(away)


def get_match_id(match):

    return (
        match.get("match_id")
        or match.get("id")
        or match.get("fixture_id")
    )


# =========================
# DASHBOARD
# =========================

if menu == "🏠 Dashboard":

    st.title("⚽ Football Stats AI")

    st.write(
        "Dashboard de estatísticas e análise de jogos "
        "alimentado pelo Footballdata.io."
    )

    data = api.today()

    matches = extract_list(data)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("📅 Jogos hoje", len(matches))

    live = api.live()
    live_matches = extract_list(live)

    col2.metric("🔴 Ao vivo", len(live_matches))

    upcoming = api.upcoming()
    upcoming_matches = extract_list(upcoming)

    col3.metric("⏭ Próximos", len(upcoming_matches))

    usage = api.usage()

    remaining = "—"

    if isinstance(usage, dict):

        d = usage.get("data", usage)

        remaining = (
            d.get("remaining")
            or d.get("requests_remaining")
            or "—"
        )

    col4.metric("API restante", remaining)

    st.divider()

    st.subheader("🔥 Jogos de hoje")

    if not matches:

        st.info("Nenhum jogo encontrado.")

    else:

        for match in matches[:20]:

            home, away = get_match_teams(match)

            match_id = get_match_id(match)

            st.markdown(
                f"""
                <div class="match-card">

                <div class="small">
                {match.get("league", {}).get("name", "") 
                if isinstance(match.get("league"), dict) else ""}
                </div>

                <div class="team">
                {home} 🆚 {away}
                </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

            if match_id:

                if st.button(
                    f"Analisar {home} x {away}",
                    key=f"dash_{match_id}",
                ):

                    st.session_state["selected_match"] = match_id

                    st.rerun()


# =========================
# JOGOS DO DIA
# =========================

elif menu == "📅 Jogos do Dia":

    st.title("📅 Jogos do Dia")

    selected_date = st.date_input(
        "Escolha a data",
        value=date.today(),
    )

    data = api.matches_by_date(
        selected_date.strftime("%Y-%m-%d")
    )

    matches = extract_list(data)

    st.write(f"**{len(matches)} jogos encontrados**")

    for match in matches:

        home, away = get_match_teams(match)
        match_id = get_match_id(match)

        st.markdown(
            f"""
            <div class="match-card">

            <div class="team">
            {home} 🆚 {away}
            </div>

            <div class="small">
            ID: {match_id}
            </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        if match_id:

            if st.button(
                "📊 Analisar",
                key=f"day_{match_id}",
            ):

                st.session_state["selected_match"] = match_id

                st.rerun()


# =========================
# ANALISAR JOGO
# =========================

elif menu == "🔎 Analisar Jogo":

    st.title("🔎 Analisar Jogo")

    default_id = st.session_state.get(
        "selected_match",
        "",
    )

    match_id = st.text_input(
        "ID da partida",
        value=str(default_id),
    )

    if st.button("🚀 ANALISAR"):

        if not match_id:

            st.warning("Digite o ID do jogo.")

        else:

            with st.spinner("Buscando dados..."):

                match_data = api.match(match_id)
                stats_data = api.stats(match_id)
                prob_data = api.probabilities(match_id)

            st.subheader("⚽ Partida")

            match = match_data.get(
                "data",
                match_data,
            )

            home, away = get_match_teams(match)

            st.markdown(
                f"""
                <div class="match-card">

                <div class="team">
                {home} 🆚 {away}
                </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

            # =================
            # PROBABILIDADES
            # =================

            st.subheader("📈 Probabilidades")

            probabilities = (
                prob_data.get("data", {})
                if isinstance(prob_data, dict)
                else {}
            )

            if "probabilities" in probabilities:

                probabilities = probabilities["probabilities"]

            if probabilities:

                cols = st.columns(3)

                winner = (
                    probabilities.get("match_winner")
                    or probabilities.get("winner")
                    or {}
                )

                cols[0].metric(
                    "🏠 Casa",
                    f"{winner.get('home', 0)}%",
                )

                cols[1].metric(
                    "🤝 Empate",
                    f"{winner.get('draw', 0)}%",
                )

                cols[2].metric(
                    "✈️ Fora",
                    f"{winner.get('away', 0)}%",
                )

            # =================
            # ESTATÍSTICAS
            # =================

            st.subheader("📊 Estatísticas")

            stats = (
                stats_data.get("data", {})
                if isinstance(stats_data, dict)
                else {}
            )

            if isinstance(stats, dict):

                if "stats" in stats:
                    stats = stats["stats"]

                rows = []

                for key, value in stats.items():

                    if isinstance(value, dict):

                        home_value = value.get("home")
                        away_value = value.get("away")

                        if (
                            home_value is not None
                            or away_value is not None
                        ):

                            rows.append(
                                {
                                    "Estatística": key,
                                    home: home_value,
                                    away: away_value,
                                }
                            )

                if rows:

                    st.dataframe(
                        pd.DataFrame(rows),
                        use_container_width=True,
                        hide_index=True,
                    )

            # =================
            # MERCADOS
            # =================

            st.subheader("🎯 Mercados")

            goals = probabilities.get(
                "goals",
                {},
            )

            btts = probabilities.get(
                "btts",
                {},
            )

            corners = probabilities.get(
                "corners",
                {},
            )

            c1, c2, c3 = st.columns(3)

            with c1:

                st.markdown(
                    '<div class="market">'
                    '<b>🥅 GOLS</b>',
                    unsafe_allow_html=True,
                )

                st.write(
                    f"Over 1.5: "
                    f"{goals.get('over_1_5', '—')}%"
                )

                st.write(
                    f"Over 2.5: "
                    f"{goals.get('over_2_5', '—')}%"
                )

                st.markdown("</div>", unsafe_allow_html=True)

            with c2:

                st.markdown(
                    '<div class="market">'
                    '<b>⚽ BTTS</b>',
                    unsafe_allow_html=True,
                )

                potential = (
                    btts.get("potential")
                    if isinstance(btts, dict)
                    else None
                )

                st.write(
                    f"Ambas marcam: "
                    f"{potential if potential is not None else '—'}%"
                )

                st.markdown("</div>", unsafe_allow_html=True)

            with c3:

                st.markdown(
                    '<div class="market">'
                    '<b>🚩 ESCANTEIOS</b>',
                    unsafe_allow_html=True,
                )

                corner_potential = (
                    corners.get("potential")
                    if isinstance(corners, dict)
                    else None
                )

                st.write(
                    f"Potencial: "
                    f"{corner_potential if corner_potential is not None else '—'}%"
                )

                st.markdown("</div>", unsafe_allow_html=True)


# =========================
# BUSCAR TIME
# =========================

elif menu == "🔍 Buscar Time":

    st.title("🔍 Buscar Time")

    query = st.text_input(
        "Digite o nome do time",
        placeholder="Ex: Arsenal",
    )

    if st.button("🔎 PESQUISAR"):

        if query:

            data = api.search(query)

            st.json(data)


# =========================
# CLASSIFICAÇÃO
# =========================

elif menu == "🏆 Classificação":

    st.title("🏆 Classificação")

    league_id = st.number_input(
        "ID da Liga",
        min_value=1,
        step=1,
    )

    if st.button("VER CLASSIFICAÇÃO"):

        data = api.standings(
            int(league_id)
        )

        standings = extract_list(data)

        if standings:

            st.dataframe(
                pd.DataFrame(standings),
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.json(data)


# =========================
# ESTATÍSTICAS
# =========================

elif menu == "📊 Estatísticas":

    st.title("📊 Estatísticas de Time")

    team_id = st.number_input(
        "ID do time",
        min_value=1,
        step=1,
    )

    if st.button("CARREGAR ESTATÍSTICAS"):

        data = api.team_stats(
            int(team_id)
        )

        st.json(data)


# =========================
# USO
# =========================

elif menu == "💳 Uso da API":

    st.title("💳 Uso da API")

    data = api.usage()

    if data:

        st.json(data)

    else:

        st.error(
            "Não foi possível consultar o uso da API."
        )
