import streamlit as st
import pandas as pd
from datetime import date, datetime

from football_api import FootballAPI


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="Football Stats AI",
    page_icon="⚽",
    layout="wide",
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

.stApp {
    background: #05080d;
}

.block-container {
    max-width: 1400px;
    padding-top: 1.5rem;
}

[data-testid="stSidebar"] {
    background: #080c12;
}

.hero {
    background: linear-gradient(
        135deg,
        #0c1624,
        #111e30
    );
    border: 1px solid #26374b;
    border-radius: 22px;
    padding: 28px;
    margin-bottom: 25px;
}

.hero-title {
    color: white;
    font-size: 34px;
    font-weight: 800;
}

.hero-sub {
    color: #8fa0b5;
    margin-top: 8px;
}

.match-card {
    background: linear-gradient(
        135deg,
        #0b1119,
        #111b28
    );
    border: 1px solid #253449;
    border-radius: 18px;
    padding: 20px;
    margin: 12px 0;
}

.match-date {
    color: #8190a4;
    font-size: 13px;
}

.team {
    color: white;
    font-size: 19px;
    font-weight: 750;
}

.vs {
    color: #64748b;
    text-align: center;
    font-weight: 700;
    padding: 8px;
}

.score {
    color: white;
    font-size: 26px;
    font-weight: 800;
    text-align: center;
}

.league {
    color: #60a5fa;
    font-size: 13px;
    margin-top: 8px;
}

.section {
    color: white;
    font-size: 22px;
    font-weight: 800;
    margin-top: 25px;
    margin-bottom: 12px;
}

.team-box {
    background: #0c131c;
    border: 1px solid #263549;
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 12px;
}

.team-name {
    color: white;
    font-size: 22px;
    font-weight: 800;
}

.team-info {
    color: #8492a5;
    font-size: 14px;
    margin-top: 5px;
}

.stat {
    background: #0c131d;
    border: 1px solid #253449;
    border-radius: 14px;
    padding: 18px;
    text-align: center;
}

.stat-label {
    color: #8492a5;
    font-size: 13px;
}

.stat-value {
    color: white;
    font-size: 25px;
    font-weight: 800;
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
        "❌ FOOTBALLDATA_API_KEY não encontrada."
    )

    st.info(
        "Adiciona a tua API Key em "
        "Streamlit Cloud → Settings → Secrets."
    )

    st.stop()


api = FootballAPI(API_KEY)


# ============================================================
# SESSION
# ============================================================

if "selected_match" not in st.session_state:
    st.session_state.selected_match = None

if "selected_match_data" not in st.session_state:
    st.session_state.selected_match_data = None

if "selected_team" not in st.session_state:
    st.session_state.selected_team = None


# ============================================================
# FUNÇÕES
# ============================================================

def dictionary(value):

    return value if isinstance(value, dict) else {}


def list_value(value):

    return value if isinstance(value, list) else []


def api_data(response):

    if not isinstance(response, dict):
        return {}

    data = response.get("data")

    if isinstance(data, dict):
        return data

    return {}


def team_name(team):

    if isinstance(team, str):
        return team

    team = dictionary(team)

    return (
        team.get("team_name")
        or team.get("name")
        or team.get("full_name")
        or team.get("short_name")
        or "?"
    )


def team_id(team):

    team = dictionary(team)

    return (
        team.get("team_id")
        or team.get("id")
    )


def home_team(match):

    return (
        match.get("home_team")
        or match.get("homeTeam")
        or match.get("home")
        or {}
    )


def away_team(match):

    return (
        match.get("away_team")
        or match.get("awayTeam")
        or match.get("away")
        or {}
    )


def get_home_name(match):

    return team_name(
        home_team(match)
    )


def get_away_name(match):

    return team_name(
        away_team(match)
    )


def get_match_id(match):

    return (
        match.get("match_id")
        or match.get("fixture_id")
        or match.get("id")
    )


def get_league_name(match):

    league = dictionary(
        match.get("league")
    )

    return (
        league.get("name")
        or league.get("competition_name")
        or "Competição"
    )


def get_score(match):

    score = dictionary(
        match.get("score")
    )

    return (
        score.get("home", 0),
        score.get("away", 0)
    )


def format_date(value):

    if not value:
        return "Data não disponível"

    value = str(value)

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ]

    for fmt in formats:

        try:

            dt = datetime.strptime(
                value,
                fmt
            )

            return dt.strftime(
                "%d/%m/%Y • %H:%M"
            )

        except Exception:
            pass

    return value


# ============================================================
# EXTRATOR ROBUSTO DE JOGOS
# ============================================================

def extract_matches(response):

    """
    Aceita várias estruturas possíveis:

    data.matches
    data.fixtures
    data.results.matches
    data.results.fixtures
    data.results
    matches
    fixtures
    """

    if not isinstance(response, dict):
        return []

    data = response.get("data")

    if isinstance(data, list):

        return [
            x for x in data
            if isinstance(x, dict)
        ]

    if not isinstance(data, dict):

        data = response

    # 1
    for key in [
        "matches",
        "fixtures",
        "games",
    ]:

        value = data.get(key)

        if isinstance(value, list):

            return [
                x for x in value
                if isinstance(x, dict)
            ]

    # 2
    results = data.get("results")

    if isinstance(results, list):

        return [
            x for x in results
            if isinstance(x, dict)
        ]

    if isinstance(results, dict):

        for key in [
            "matches",
            "fixtures",
            "games",
        ]:

            value = results.get(key)

            if isinstance(value, list):

                return [
                    x for x in value
                    if isinstance(x, dict)
                ]

    return []


# ============================================================
# ABRIR PARTIDA
# ============================================================

def select_match(match):

    st.session_state.selected_match = (
        get_match_id(match)
    )

    st.session_state.selected_match_data = (
        match
    )

    st.rerun()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown(
    """
    <div style="
        color:white;
        font-size:25px;
        font-weight:800;
        margin-bottom:20px;
    ">
        ⚽ Football Stats AI
    </div>
    """,
    unsafe_allow_html=True,
)


menu = st.sidebar.radio(
    "MENU",
    [
        "🏠 Dashboard",
        "📅 Jogos",
        "🔎 Analisar Jogo",
        "🔍 Buscar Time",
        "📊 Estatísticas do Time",
        "🏆 Classificação",
        "💳 Uso da API",
    ],
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

            <div class="hero-sub">
                Estatísticas de futebol em tempo real
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    with st.spinner(
        "Carregando jogos de hoje..."
    ):

        response = api.today()

    matches = extract_matches(
        response
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "📅 Jogos",
        len(matches)
    )

    try:

        live_response = api.live()

        live = extract_matches(
            live_response
        )

    except Exception:

        live = []

    c2.metric(
        "🔴 Ao vivo",
        len(live)
    )

    try:

        upcoming_response = api.upcoming()

        upcoming = extract_matches(
            upcoming_response
        )

    except Exception:

        upcoming = []

    c3.metric(
        "⏭ Próximos",
        len(upcoming)
    )

    st.markdown(
        '<div class="section">'
        '🔥 Jogos de hoje'
        '</div>',
        unsafe_allow_html=True
    )

    if not matches:

        st.warning(
            "A API não devolveu jogos para hoje."
        )

        with st.expander(
            "🔧 Ver resposta da API"
        ):

            st.json(response)

    else:

        for match in matches:

            home = get_home_name(match)
            away = get_away_name(match)

            mid = get_match_id(match)

            hscore, ascore = get_score(
                match
            )

            st.markdown(
                f"""
                <div class="match-card">

                    <div class="match-date">
                        {format_date(
                            match.get("match_date")
                        )}
                    </div>

                    <br>

                    <div class="team">
                        🏠 {home}
                    </div>

                    <div class="vs">
                        🆚
                    </div>

                    <div class="team">
                        ✈️ {away}
                    </div>

                    <div class="score">
                        {hscore} - {ascore}
                    </div>

                    <div class="league">
                        🏆 {get_league_name(match)}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(
                f"📊 Analisar {home} x {away}",
                key=f"dash_{mid}",
                use_container_width=True,
            ):

                select_match(match)


# ============================================================
# JOGOS POR DATA
# ============================================================

elif menu == "📅 Jogos":

    st.title("📅 Jogos")

    selected_date = st.date_input(
        "Selecionar data",
        value=date.today()
    )

    date_string = selected_date.strftime(
        "%Y-%m-%d"
    )

    st.caption(
        f"Data enviada para a API: {date_string}"
    )

    if st.button(
        "🔎 CARREGAR JOGOS",
        use_container_width=True,
    ):

        with st.spinner(
            f"Buscando jogos de {date_string}..."
        ):

            # PRIMEIRA TENTATIVA
            response = api.matches_by_date(
                date_string
            )

            matches = extract_matches(
                response
            )

            # SEGUNDA TENTATIVA
            # /matches?date=YYYY-MM-DD

            if not matches:

                response_alt = (
                    api.matches_by_date_alt(
                        date_string
                    )
                )

                matches = extract_matches(
                    response_alt
                )

                if matches:

                    response = response_alt

        st.session_state.date_matches = (
            matches
        )

        st.session_state.date_response = (
            response
        )

    matches = st.session_state.get(
        "date_matches",
        None
    )

    if matches is not None:

        if matches:

            st.success(
                f"⚽ {len(matches)} jogos encontrados."
            )

            for match in matches:

                home = get_home_name(match)
                away = get_away_name(match)

                mid = get_match_id(match)

                hscore, ascore = get_score(
                    match
                )

                st.markdown(
                    f"""
                    <div class="match-card">

                        <div class="match-date">
                            {format_date(
                                match.get("match_date")
                            )}
                        </div>

                        <br>

                        <div class="team">
                            🏠 {home}
                        </div>

                        <div class="vs">
                            🆚
                        </div>

                        <div class="team">
                            ✈️ {away}
                        </div>

                        <div class="score">
                            {hscore} - {ascore}
                        </div>

                        <div class="league">
                            🏆 {get_league_name(match)}
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if st.button(
                    f"📊 Analisar {home} x {away}",
                    key=f"date_{mid}",
                    use_container_width=True,
                ):

                    select_match(match)

        else:

            st.warning(
                f"Nenhum jogo encontrado para "
                f"{selected_date.strftime('%d/%m/%Y')}."
            )

            response_debug = st.session_state.get(
                "date_response"
            )

            if response_debug:

                with st.expander(
                    "🔧 Ver resposta recebida da API"
                ):

                    st.json(
                        response_debug
                    )


# ============================================================
# ANALISAR JOGO
# ============================================================

elif menu == "🔎 Analisar Jogo":

    st.title("🔎 Analisar Jogo")

    selected_id = st.session_state.get(
        "selected_match"
    )

    selected_data = st.session_state.get(
        "selected_match_data"
    )

    if selected_id:

        st.success(
            f"Partida selecionada: {selected_id}"
        )

    match_id_input = st.text_input(
        "ID da partida",
        value=str(
            selected_id or ""
        ),
        placeholder="Ex: 2491004563"
    )

    if st.button(
        "🚀 ANALISAR PARTIDA",
        use_container_width=True,
    ):

        if not match_id_input:

            st.warning(
                "Digite o ID da partida."
            )

        else:

            with st.spinner(
                "Buscando dados da partida..."
            ):

                match_response = api.match(
                    match_id_input
                )

                stats_response = api.stats(
                    match_id_input
                )

                probabilities_response = (
                    api.probabilities(
                        match_id_input
                    )
                )

            st.session_state.match_response = (
                match_response
            )

            st.session_state.stats_response = (
                stats_response
            )

            st.session_state.probabilities_response = (
                probabilities_response
            )

    if "match_response" in st.session_state:

        response = st.session_state.match_response

        match = api_data(response)

        # Algumas respostas colocam o jogo
        # dentro de data.match

        if isinstance(
            match.get("match"),
            dict
        ):

            match = match["match"]

        # Se por algum motivo o endpoint
        # não trouxer o jogo, usamos o
        # objeto que já veio da lista.

        if not match and selected_data:

            match = selected_data

        home = get_home_name(match)
        away = get_away_name(match)

        hscore, ascore = get_score(
            match
        )

        st.markdown(
            f"""
            <div class="hero">

                <div class="match-date">
                    {format_date(
                        match.get("match_date")
                    )}
                </div>

                <br>

                <div class="team">
                    🏠 {home}
                </div>

                <div class="score">
                    {hscore} - {ascore}
                </div>

                <div class="team">
                    ✈️ {away}
                </div>

                <div class="league">
                    🏆 {get_league_name(match)}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

        # ====================================================
        # PROBABILIDADES
        # ====================================================

        st.markdown(
            '<div class="section">'
            '📈 Probabilidades'
            '</div>',
            unsafe_allow_html=True
        )

        probability = api_data(
            st.session_state.probabilities_response
        )

        if probability:

            if isinstance(
                probability.get(
                    "probabilities"
                ),
                dict
            ):

                probability = probability[
                    "probabilities"
                ]

            winner = dictionary(
                probability.get(
                    "match_winner"
                )
                or probability.get(
                    "winner"
                )
            )

            c1, c2, c3 = st.columns(3)

            c1.markdown(
                f"""
                <div class="stat">
                    <div class="stat-label">
                        🏠 CASA
                    </div>
                    <div class="stat-value">
                        {winner.get(
                            "home",
                            "—"
                        )}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            c2.markdown(
                f"""
                <div class="stat">
                    <div class="stat-label">
                        🤝 EMPATE
                    </div>
                    <div class="stat-value">
                        {winner.get(
                            "draw",
                            "—"
                        )}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            c3.markdown(
                f"""
                <div class="stat">
                    <div class="stat-label">
                        ✈️ FORA
                    </div>
                    <div class="stat-value">
                        {winner.get(
                            "away",
                            "—"
                        )}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.write("")

            goals = dictionary(
                probability.get(
                    "goals"
                )
            )

            btts = dictionary(
                probability.get(
                    "btts"
                )
            )

            corners = dictionary(
                probability.get(
                    "corners"
                )
            )

            m1, m2, m3 = st.columns(3)

            m1.metric(
                "🥅 Over 1.5",
                goals.get(
                    "over_1_5",
                    "—"
                )
            )

            m2.metric(
                "🥅 Over 2.5",
                goals.get(
                    "over_2_5",
                    "—"
                )
            )

            m3.metric(
                "⚽ BTTS",
                btts.get(
                    "potential",
                    btts.get(
                        "yes",
                        "—"
                    )
                )
            )

            st.metric(
                "🚩 Escanteios",
                corners.get(
                    "potential",
                    "—"
                )
            )

        else:

            st.info(
                "Não foram encontradas "
                "probabilidades para esta partida."
            )

        # ====================================================
        # ESTATÍSTICAS
        # ====================================================

        st.markdown(
            '<div class="section">'
            '📊 Estatísticas'
            '</div>',
            unsafe_allow_html=True
        )

        stats_data = api_data(
            st.session_state.stats_response
        )

        if isinstance(
            stats_data.get("stats"),
            dict
        ):

            stats_data = stats_data[
                "stats"
            ]

        rows = []

        if isinstance(
            stats_data,
            dict
        ):

            for key, value in stats_data.items():

                if isinstance(
                    value,
                    dict
                ):

                    home_value = (
                        value.get("home")
                    )

                    away_value = (
                        value.get("away")
                    )

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

                elif isinstance(
                    value,
                    (int, float, str)
                ):

                    rows.append(
                        {
                            "Estatística": key,
                            "Valor": value,
                        }
                    )

        if rows:

            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "Nenhuma estatística disponível "
                "para esta partida."
            )


# ============================================================
# BUSCAR TIME
# ============================================================

elif menu == "🔍 Buscar Time":

    st.title("🔍 Buscar Time")

    query = st.text_input(
        "Digite o nome do time",
        placeholder="Barcelona"
    )

    if st.button(
        "🔎 PESQUISAR",
        use_container_width=True,
    ):

        if not query.strip():

            st.warning(
                "Digite o nome do time."
            )

        else:

            with st.spinner(
                "Pesquisando..."
            ):

                response = api.search(
                    query.strip()
                )

            st.session_state.search_response = (
                response
            )

    response = st.session_state.get(
        "search_response"
    )

    if response:

        data = api_data(
            response
        )

        results = dictionary(
            data.get("results")
        )

        teams = list_value(
            results.get("teams")
        )

        matches = list_value(
            results.get("matches")
        )

        if teams:

            st.markdown(
                '<div class="section">'
                '⚽ Times encontrados'
                '</div>',
                unsafe_allow_html=True
            )

            for team in teams:

                tid = team_id(team)

                name = team.get(
                    "team_name",
                    "?"
                )

                country = team.get(
                    "country",
                    ""
                )

                logo = team.get(
                    "team_logo"
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
                        <div class="team-box">

                            <div class="team-name">
                                {name}
                            </div>

                            <div class="team-info">
                                🌍 {country}
                            </div>

                            <div class="team-info">
                                ID: {tid}
                            </div>

                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    if st.button(
                        f"📊 Ver {name}",
                        key=f"team_{tid}",
                        use_container_width=True,
                    ):

                        st.session_state.selected_team = (
                            team
                        )

                        st.session_state.team_response = (
                            api.team(tid)
                        )

                        st.rerun()

        if matches:

            st.markdown(
                '<div class="section">'
                '📅 Partidas encontradas'
                '</div>',
                unsafe_allow_html=True
            )

            for match in matches:

                home = get_home_name(match)
                away = get_away_name(match)

                mid = get_match_id(match)

                st.markdown(
                    f"""
                    <div class="match-card">

                        <div class="match-date">
                            {format_date(
                                match.get("match_date")
                            )}
                        </div>

                        <br>

                        <div class="team">
                            🏠 {home}
                        </div>

                        <div class="vs">
                            🆚
                        </div>

                        <div class="team">
                            ✈️ {away}
                        </div>

                        <div class="league">
                            🏆 {get_league_name(match)}
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if st.button(
                    f"📊 Analisar {home} x {away}",
                    key=f"search_{mid}",
                    use_container_width=True,
                ):

                    select_match(match)

        if not teams and not matches:

            st.info(
                "Nenhum resultado encontrado."
            )

        # ====================================================
        # DEBUG SOMENTE SE NÃO ENCONTRAR
        # ====================================================

        if not teams and not matches:

            with st.expander(
                "🔧 Ver resposta da API"
            ):

                st.json(response)


# ============================================================
# ESTATÍSTICAS DO TIME
# ============================================================

elif menu == "📊 Estatísticas do Time":

    st.title("📊 Estatísticas do Time")

    selected_team = st.session_state.get(
        "selected_team"
    )

    if selected_team:

        name = selected_team.get(
            "team_name",
            "Time"
        )

        tid = selected_team.get(
            "team_id"
        )

        st.success(
            f"⚽ {name} • ID {tid}"
        )

        team_response = st.session_state.get(
            "team_response"
        )

        if team_response:

            team_data = api_data(
                team_response
            )

            if isinstance(
                team_data.get("team"),
                dict
            ):

                team_data = team_data[
                    "team"
                ]

            st.json(
                team_data
            )

    else:

        tid = st.number_input(
            "ID do time",
            min_value=1,
            value=77,
            step=1
        )

        if st.button(
            "📊 CARREGAR",
            use_container_width=True,
        ):

            response = api.team_stats(
                int(tid)
            )

            st.json(response)


# ============================================================
# CLASSIFICAÇÃO
# ============================================================

elif menu == "🏆 Classificação":

    st.title("🏆 Classificação")

    league_id = st.number_input(
        "ID da liga",
        min_value=1,
        value=10,
        step=1
    )

    if st.button(
        "🏆 CARREGAR",
        use_container_width=True,
    ):

        response = api.standings(
            int(league_id)
        )

        data = api_data(
            response
        )

        standings = (
            data.get("standings")
            or data.get("table")
            or []
        )

        if isinstance(
            standings,
            list
        ) and standings:

            st.dataframe(
                pd.DataFrame(
                    standings
                ),
                use_container_width=True,
                hide_index=True
            )

        else:

            st.json(response)


# ============================================================
# USO DA API
# ============================================================

elif menu == "💳 Uso da API":

    st.title("💳 Uso da API")

    if st.button(
        "🔄 ATUALIZAR",
        use_container_width=True,
    ):

        response = api.usage()

        data = api_data(
            response
        )

        if data:

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "📦 Limite",
                data.get(
                    "requests_limit",
                    data.get(
                        "limit",
                        "—"
                    )
                )
            )

            c2.metric(
                "📊 Usado",
                data.get(
                    "requests_used",
                    data.get(
                        "used",
                        "—"
                    )
                )
            )

            c3.metric(
                "✅ Restante",
                data.get(
                    "remaining",
                    "—"
                )
            )

            st.json(
                response
            )

        else:

            st.error(
                "Não foi possível consultar "
                "o uso da API."
            )
