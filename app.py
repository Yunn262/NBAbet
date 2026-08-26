import streamlit as st
import pandas as pd
from datetime import date, datetime

from football_api import FootballAPI


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="Football Stats AI",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

html, body, [class*="css"] {
    font-family: Arial, sans-serif;
}

.stApp {
    background:
        radial-gradient(
            circle at top right,
            rgba(30, 80, 150, 0.18),
            transparent 35%
        ),
        #05080d;
}

.block-container {
    max-width: 1400px;
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}

[data-testid="stSidebar"] {
    background: #080c12;
    border-right: 1px solid #202936;
}

.hero {
    background:
        linear-gradient(
            135deg,
            #0c1420,
            #111c2b
        );
    border: 1px solid #263447;
    border-radius: 22px;
    padding: 28px;
    margin-bottom: 22px;
}

.hero-title {
    font-size: 34px;
    font-weight: 800;
    color: white;
}

.hero-subtitle {
    color: #91a0b5;
    margin-top: 7px;
}

.team-card {
    background: linear-gradient(
        135deg,
        #0d1520,
        #121c29
    );
    border: 1px solid #263548;
    border-radius: 20px;
    padding: 22px;
    margin: 12px 0;
}

.team-name {
    color: white;
    font-size: 24px;
    font-weight: 800;
}

.team-country {
    color: #94a3b8;
    font-size: 14px;
}

.match-card {
    background: linear-gradient(
        135deg,
        #0b111a,
        #111a26
    );
    border: 1px solid #253246;
    border-radius: 18px;
    padding: 20px;
    margin: 12px 0;
}

.match-date {
    color: #8291a5;
    font-size: 13px;
}

.team-home,
.team-away {
    color: white;
    font-size: 19px;
    font-weight: 700;
}

.vs {
    color: #64748b;
    font-size: 13px;
    text-align: center;
    padding: 5px;
}

.score {
    font-size: 26px;
    font-weight: 800;
    color: white;
    text-align: center;
}

.status {
    color: #60a5fa;
    font-size: 13px;
    font-weight: 700;
}

.section-title {
    color: white;
    font-size: 22px;
    font-weight: 800;
    margin-top: 25px;
    margin-bottom: 12px;
}

.stat-card {
    background: #0d141e;
    border: 1px solid #253142;
    border-radius: 15px;
    padding: 18px;
    text-align: center;
    margin-bottom: 10px;
}

.stat-title {
    color: #8492a6;
    font-size: 13px;
}

.stat-value {
    color: white;
    font-size: 25px;
    font-weight: 800;
    margin-top: 5px;
}

.market-card {
    background: #0c131d;
    border: 1px solid #263548;
    border-radius: 14px;
    padding: 15px;
    margin-bottom: 10px;
}

.market-title {
    color: #9aa9bc;
    font-size: 13px;
}

.market-value {
    color: white;
    font-size: 20px;
    font-weight: 800;
}

.search-result {
    background: #0c131d;
    border: 1px solid #263548;
    border-radius: 16px;
    padding: 18px;
    margin-bottom: 10px;
}

div.stButton > button {
    border-radius: 10px;
    border: 1px solid #2c3b50;
    background: #111b28;
    color: white;
    font-weight: 700;
}

div.stButton > button:hover {
    border-color: #4f8cff;
    color: white;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# API KEY
# ============================================================

try:
    API_KEY = st.secrets["FOOTBALLDATA_API_KEY"]
except Exception:
    API_KEY = ""


if not API_KEY:

    st.error(
        "❌ API Key não encontrada."
    )

    st.info(
        "No Streamlit Cloud, adiciona "
        "`FOOTBALLDATA_API_KEY` nos Secrets."
    )

    st.stop()


api = FootballAPI(API_KEY)


# ============================================================
# SESSION STATE
# ============================================================

if "selected_match" not in st.session_state:
    st.session_state.selected_match = None

if "selected_team" not in st.session_state:
    st.session_state.selected_team = None

if "search_results" not in st.session_state:
    st.session_state.search_results = None


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def safe_dict(value):
    if isinstance(value, dict):
        return value
    return {}


def safe_list(value):
    if isinstance(value, list):
        return value
    return []


def get_api_data(response):

    if not isinstance(response, dict):
        return {}

    data = response.get("data")

    if isinstance(data, dict):
        return data

    return {}


def format_date(value):

    if not value:
        return "Data não disponível"

    try:

        dt = datetime.strptime(
            str(value),
            "%Y-%m-%d %H:%M:%S"
        )

        return dt.strftime(
            "%d/%m/%Y • %H:%M"
        )

    except Exception:

        return str(value)


def team_name(team):

    team = safe_dict(team)

    return (
        team.get("team_name")
        or team.get("name")
        or "Desconhecido"
    )


def team_id(team):

    team = safe_dict(team)

    return (
        team.get("team_id")
        or team.get("id")
    )


def league_name(league):

    league = safe_dict(league)

    return (
        league.get("name")
        or league.get("competition_name")
        or "Liga desconhecida"
    )


def match_home(match):

    return team_name(
        match.get("home_team")
    )


def match_away(match):

    return team_name(
        match.get("away_team")
    )


def match_id(match):

    return (
        match.get("match_id")
        or match.get("id")
    )


def match_score(match):

    score = safe_dict(
        match.get("score")
    )

    home = score.get("home", 0)
    away = score.get("away", 0)

    return home, away


def get_matches_from_response(response):

    data = get_api_data(response)

    results = safe_dict(
        data.get("results")
    )

    return safe_list(
        results.get("matches")
    )


def get_teams_from_response(response):

    data = get_api_data(response)

    results = safe_dict(
        data.get("results")
    )

    return safe_list(
        results.get("teams")
    )


def open_match(match):

    st.session_state.selected_match = match_id(match)

    st.session_state.selected_match_data = match

    st.rerun()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown(
    """
    <div style="
        font-size:25px;
        font-weight:800;
        color:white;
        margin-bottom:20px;
    ">
        ⚽ Football Stats AI
    </div>
    """,
    unsafe_allow_html=True,
)


menu = st.sidebar.radio(
    "NAVEGAÇÃO",
    [
        "🏠 Dashboard",
        "📅 Jogos do Dia",
        "🔎 Analisar Jogo",
        "🔍 Buscar Time",
        "📊 Estatísticas",
        "🏆 Classificação",
        "💳 Uso da API",
    ],
)


st.sidebar.divider()

st.sidebar.caption(
    "Powered by Footballdata.io"
)


# ============================================================
# DASHBOARD
# ============================================================

if menu == "🏠 Dashboard":

    st.markdown(
        """
        <div class="hero">
            <div class="hero-title">
                ⚽ Football Stats AI
            </div>
            <div class="hero-subtitle">
                Plataforma de análise e estatísticas de futebol
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------
    # Jogos
    # --------------------------

    with st.spinner("Carregando jogos..."):

        today_response = api.today()

    today_matches = get_matches_from_response(
        today_response
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "📅 Jogos hoje",
        len(today_matches)
    )

    try:

        live_response = api.live()

        live_matches = get_matches_from_response(
            live_response
        )

    except Exception:

        live_matches = []

    col2.metric(
        "🔴 Ao vivo",
        len(live_matches)
    )

    try:

        upcoming_response = api.upcoming()

        upcoming_matches = get_matches_from_response(
            upcoming_response
        )

    except Exception:

        upcoming_matches = []

    col3.metric(
        "⏭ Próximos",
        len(upcoming_matches)
    )

    try:

        usage_response = api.usage()

        usage_data = get_api_data(
            usage_response
        )

        remaining = (
            usage_data.get("remaining")
            or usage_data.get("requests_remaining")
            or "—"
        )

    except Exception:

        remaining = "—"

    col4.metric(
        "🔑 API restante",
        remaining
    )

    st.markdown(
        '<div class="section-title">'
        '🔥 Jogos de hoje'
        '</div>',
        unsafe_allow_html=True
    )

    if not today_matches:

        st.info(
            "Nenhum jogo encontrado para hoje."
        )

    else:

        for match in today_matches[:20]:

            home = match_home(match)
            away = match_away(match)

            home_score, away_score = match_score(
                match
            )

            st.markdown(
                f"""
                <div class="match-card">

                    <div class="match-date">
                        {format_date(match.get("match_date"))}
                        &nbsp; • &nbsp;
                        {league_name(match.get("league"))}
                    </div>

                    <br>

                    <div class="team-home">
                        🏠 {home}
                    </div>

                    <div class="score">
                        {home_score} - {away_score}
                    </div>

                    <div class="team-away">
                        ✈️ {away}
                    </div>

                    <div class="status">
                        {match.get("status_localized", "Scheduled")}
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                "📊 Analisar jogo",
                key=f"dashboard_match_{match_id(match)}",
            ):

                open_match(match)


# ============================================================
# JOGOS DO DIA
# ============================================================

elif menu == "📅 Jogos do Dia":

    st.title("📅 Jogos do Dia")

    selected_date = st.date_input(
        "Selecionar data",
        value=date.today(),
    )

    if st.button(
        "🔎 CARREGAR JOGOS",
        use_container_width=True,
    ):

        with st.spinner(
            "Buscando jogos..."
        ):

            response = api.matches_by_date(
                selected_date.strftime(
                    "%Y-%m-%d"
                )
            )

        matches = get_matches_from_response(
            response
        )

        st.session_state.day_matches = matches

    matches = st.session_state.get(
        "day_matches",
        []
    )

    if matches:

        st.success(
            f"{len(matches)} jogos encontrados."
        )

        for match in matches:

            home = match_home(match)
            away = match_away(match)

            home_score, away_score = match_score(
                match
            )

            st.markdown(
                f"""
                <div class="match-card">

                    <div class="match-date">
                        {format_date(match.get("match_date"))}
                    </div>

                    <br>

                    <div class="team-home">
                        {home}
                    </div>

                    <div class="score">
                        {home_score} - {away_score}
                    </div>

                    <div class="team-away">
                        {away}
                    </div>

                    <br>

                    <div class="status">
                        {league_name(match.get("league"))}
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                "📊 ANALISAR",
                key=f"date_{match_id(match)}",
            ):

                open_match(match)

    elif st.session_state.get(
        "day_matches"
    ) is not None:

        st.info(
            "Nenhum jogo encontrado para essa data."
        )


# ============================================================
# ANALISAR JOGO
# ============================================================

elif menu == "🔎 Analisar Jogo":

    st.title("🔎 Analisar Jogo")

    selected = st.session_state.get(
        "selected_match"
    )

    match_data_saved = st.session_state.get(
        "selected_match_data",
        {}
    )

    if selected:

        st.success(
            f"Jogo selecionado: {selected}"
        )

    match_input = st.text_input(
        "ID da partida",
        value=str(selected or ""),
        placeholder="Ex: 2491004563",
    )

    if st.button(
        "🚀 ANALISAR PARTIDA",
        use_container_width=True,
    ):

        if not match_input:

            st.warning(
                "Digite o ID da partida."
            )

        else:

            with st.spinner(
                "Buscando informações da partida..."
            ):

                match_response = api.match(
                    match_input
                )

                stats_response = api.stats(
                    match_input
                )

                probabilities_response = api.probabilities(
                    match_input
                )

            st.session_state.analysis_match = (
                match_response
            )

            st.session_state.analysis_stats = (
                stats_response
            )

            st.session_state.analysis_probabilities = (
                probabilities_response
            )

    if "analysis_match" in st.session_state:

        response = st.session_state.analysis_match

        match = get_api_data(response)

        if not match:

            match = match_data_saved

        home = match_home(match)
        away = match_away(match)

        home_score, away_score = match_score(
            match
        )

        st.markdown(
            f"""
            <div class="hero">

                <div class="match-date">
                    {format_date(match.get("match_date"))}
                </div>

                <br>

                <div class="team-home">
                    🏠 {home}
                </div>

                <div class="score">
                    {home_score} - {away_score}
                </div>

                <div class="team-away">
                    ✈️ {away}
                </div>

                <br>

                <div class="status">
                    {match.get(
                        "status_localized",
                        match.get("status", "")
                    )}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        # ====================================================
        # PROBABILIDADES
        # ====================================================

        st.markdown(
            '<div class="section-title">'
            '📈 Probabilidades'
            '</div>',
            unsafe_allow_html=True
        )

        probability_data = get_api_data(
            st.session_state.analysis_probabilities
        )

        if probability_data:

            # Tentamos encontrar a estrutura
            probabilities = probability_data.get(
                "probabilities",
                probability_data
            )

            if isinstance(
                probabilities,
                dict
            ):

                winner = probabilities.get(
                    "match_winner",
                    probabilities.get(
                        "winner",
                        {}
                    )
                )

                winner = safe_dict(
                    winner
                )

                c1, c2, c3 = st.columns(3)

                c1.markdown(
                    f"""
                    <div class="stat-card">
                        <div class="stat-title">
                            🏠 Vitória Casa
                        </div>
                        <div class="stat-value">
                            {winner.get("home", "—")}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                c2.markdown(
                    f"""
                    <div class="stat-card">
                        <div class="stat-title">
                            🤝 Empate
                        </div>
                        <div class="stat-value">
                            {winner.get("draw", "—")}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                c3.markdown(
                    f"""
                    <div class="stat-card">
                        <div class="stat-title">
                            ✈️ Vitória Fora
                        </div>
                        <div class="stat-value">
                            {winner.get("away", "—")}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # -------------------------
                # GOLS
                # -------------------------

                goals = safe_dict(
                    probabilities.get(
                        "goals"
                    )
                )

                btts = safe_dict(
                    probabilities.get(
                        "btts"
                    )
                )

                corners = safe_dict(
                    probabilities.get(
                        "corners"
                    )
                )

                st.markdown(
                    '<div class="section-title">'
                    '🎯 Mercados'
                    '</div>',
                    unsafe_allow_html=True
                )

                m1, m2, m3 = st.columns(3)

                with m1:

                    st.markdown(
                        f"""
                        <div class="market-card">

                            <div class="market-title">
                                🥅 OVER 1.5 GOLS
                            </div>

                            <div class="market-value">
                                {goals.get(
                                    "over_1_5",
                                    "—"
                                )}
                            </div>

                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.markdown(
                        f"""
                        <div class="market-card">

                            <div class="market-title">
                                🥅 OVER 2.5 GOLS
                            </div>

                            <div class="market-value">
                                {goals.get(
                                    "over_2_5",
                                    "—"
                                )}
                            </div>

                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with m2:

                    st.markdown(
                        f"""
                        <div class="market-card">

                            <div class="market-title">
                                ⚽ BTTS
                            </div>

                            <div class="market-value">
                                {btts.get(
                                    "potential",
                                    btts.get(
                                        "yes",
                                        "—"
                                    )
                                )}
                            </div>

                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with m3:

                    st.markdown(
                        f"""
                        <div class="market-card">

                            <div class="market-title">
                                🚩 ESCANTEIOS
                            </div>

                            <div class="market-value">
                                {corners.get(
                                    "potential",
                                    "—"
                                )}
                            </div>

                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        else:

            st.info(
                "A API não retornou probabilidades para esta partida."
            )

        # ====================================================
        # ESTATÍSTICAS
        # ====================================================

        st.markdown(
            '<div class="section-title">'
            '📊 Estatísticas da partida'
            '</div>',
            unsafe_allow_html=True
        )

        stats_data = get_api_data(
            st.session_state.analysis_stats
        )

        if stats_data:

            stats = stats_data.get(
                "stats",
                stats_data
            )

            rows = []

            if isinstance(stats, dict):

                for key, value in stats.items():

                    if isinstance(value, dict):

                        h = (
                            value.get("home")
                            or value.get("home_value")
                        )

                        a = (
                            value.get("away")
                            or value.get("away_value")
                        )

                        if h is not None or a is not None:

                            rows.append(
                                {
                                    "Estatística": key,
                                    home: h if h is not None else "—",
                                    away: a if a is not None else "—",
                                }
                            )

                    elif isinstance(
                        value,
                        (str, int, float)
                    ):

                        rows.append(
                            {
                                "Estatística": key,
                                "Valor": value,
                            }
                        )

            if rows:

                df = pd.DataFrame(rows)

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info(
                    "As estatísticas retornadas "
                    "não possuem formato tabular."
                )

        else:

            st.info(
                "Nenhuma estatística disponível."
            )


# ============================================================
# BUSCAR TIME
# ============================================================

elif menu == "🔍 Buscar Time":

    st.title("🔍 Buscar Time")

    st.write(
        "Pesquisa equipes, partidas e outras informações "
        "disponíveis na API."
    )

    query = st.text_input(
        "Digite o nome do time",
        placeholder="Ex: Barcelona",
    )

    if st.button(
        "🔎 PESQUISAR",
        use_container_width=True,
    ):

        if not query.strip():

            st.warning(
                "Digite o nome de um time."
            )

        else:

            with st.spinner(
                f"Pesquisando {query}..."
            ):

                response = api.search(
                    query.strip()
                )

            st.session_state.search_results = (
                response
            )

    response = st.session_state.get(
        "search_results"
    )

    if response:

        data = get_api_data(
            response
        )

        # ====================================================
        # RESULTADOS
        # ====================================================

        results = safe_dict(
            data.get("results")
        )

        teams = safe_list(
            results.get("teams")
        )

        matches = safe_list(
            results.get("matches")
        )

        query_returned = data.get(
            "query",
            query
        )

        st.success(
            f"Resultados para: {query_returned}"
        )

        # ====================================================
        # TIMES
        # ====================================================

        if teams:

            st.markdown(
                '<div class="section-title">'
                '⚽ Times encontrados'
                '</div>',
                unsafe_allow_html=True
            )

            for team in teams:

                tid = team.get(
                    "team_id"
                )

                name = team.get(
                    "team_name",
                    "Time"
                )

                country = team.get(
                    "country",
                    ""
                )

                logo = team.get(
                    "team_logo",
                    ""
                )

                col1, col2 = st.columns(
                    [1, 5]
                )

                with col1:

                    if logo:

                        st.image(
                            logo,
                            width=75
                        )

                with col2:

                    st.markdown(
                        f"""
                        <div class="team-card">

                            <div class="team-name">
                                {name}
                            </div>

                            <div class="team-country">
                                🌍 {country}
                            </div>

                            <div class="team-country">
                                ID: {tid}
                            </div>

                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if st.button(
                        "📊 Abrir estatísticas do time",
                        key=f"team_{tid}",
                    ):

                        st.session_state.selected_team = team

                        st.rerun()

        # ====================================================
        # PARTIDAS ENCONTRADAS
        # ====================================================

        if matches:

            st.markdown(
                '<div class="section-title">'
                '📅 Partidas encontradas'
                '</div>',
                unsafe_allow_html=True
            )

            for match in matches:

                home = match_home(match)
                away = match_away(match)

                home_score, away_score = match_score(
                    match
                )

                mid = match_id(match)

                st.markdown(
                    f"""
                    <div class="match-card">

                        <div class="match-date">
                            {format_date(
                                match.get("match_date")
                            )}
                        </div>

                        <br>

                        <div class="team-home">
                            {home}
                        </div>

                        <div class="score">
                            {home_score} - {away_score}
                        </div>

                        <div class="team-away">
                            {away}
                        </div>

                        <div class="status">
                            {league_name(
                                match.get("league")
                            )}
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.button(
                    "📊 Analisar partida",
                    key=f"search_match_{mid}",
                ):

                    open_match(match)

        if not teams and not matches:

            st.info(
                "Nenhum time ou partida encontrado."
            )


# ============================================================
# ESTATÍSTICAS DO TIME
# ============================================================

elif menu == "📊 Estatísticas":

    st.title("📊 Estatísticas do Time")

    selected_team = st.session_state.get(
        "selected_team"
    )

    if selected_team:

        selected_id = selected_team.get(
            "team_id"
        )

        selected_name = selected_team.get(
            "team_name"
        )

        st.success(
            f"Time selecionado: {selected_name} "
            f"(ID {selected_id})"
        )

    else:

        selected_id = None

    team_input = st.number_input(
        "ID do time",
        min_value=1,
        value=int(selected_id or 1),
        step=1,
    )

    if st.button(
        "📊 CARREGAR ESTATÍSTICAS",
        use_container_width=True,
    ):

        with st.spinner(
            "Carregando estatísticas..."
        ):

            response = api.team_stats(
                int(team_input)
            )

        st.session_state.team_stats_response = (
            response
        )

    response = st.session_state.get(
        "team_stats_response"
    )

    if response:

        data = get_api_data(
            response
        )

        if data:

            st.json(data)

        else:

            st.warning(
                "Nenhuma estatística retornada."
            )


# ============================================================
# CLASSIFICAÇÃO
# ============================================================

elif menu == "🏆 Classificação":

    st.title("🏆 Classificação")

    league_id = st.number_input(
        "ID da liga",
        min_value=1,
        value=10,
        step=1,
    )

    if st.button(
        "🏆 CARREGAR CLASSIFICAÇÃO",
        use_container_width=True,
    ):

        with st.spinner(
            "Carregando classificação..."
        ):

            response = api.standings(
                int(league_id)
            )

        st.session_state.standings_response = (
            response
        )

    response = st.session_state.get(
        "standings_response"
    )

    if response:

        data = get_api_data(
            response
        )

        standings = []

        if isinstance(
            data,
            dict
        ):

            standings = (
                data.get("standings")
                or data.get("table")
                or []
            )

        if isinstance(
            standings,
            list
        ) and standings:

            df = pd.DataFrame(
                standings
            )

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.json(data)


# ============================================================
# USO DA API
# ============================================================

elif menu == "💳 Uso da API":

    st.title("💳 Uso da API")

    if st.button(
        "🔄 ATUALIZAR",
        use_container_width=True,
    ):

        with st.spinner(
            "Consultando utilização..."
        ):

            response = api.usage()

        st.session_state.usage_response = (
            response
        )

    response = st.session_state.get(
        "usage_response"
    )

    if response:

        data = get_api_data(
            response
        )

        if data:

            col1, col2, col3 = st.columns(3)

            total = (
                data.get("total")
                or data.get("limit")
                or "—"
            )

            used = (
                data.get("used")
                or data.get("requests_used")
                or "—"
            )

            remaining = (
                data.get("remaining")
                or data.get("requests_remaining")
                or "—"
            )

            col1.metric(
                "📦 Limite",
                total
            )

            col2.metric(
                "📊 Utilizado",
                used
            )

            col3.metric(
                "✅ Restante",
                remaining
            )

            st.divider()

            st.json(data)

        else:

            st.warning(
                "Não foi possível obter "
                "os dados de utilização."
            )
