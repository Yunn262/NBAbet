import streamlit as st
from datetime import date, datetime
import pandas as pd

from football_api import FootballAPI
from ai_engine import analisar_partida


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="Football Stats AI",
    page_icon="âš½",
    layout="wide",
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

.stApp {
    background:#05080d;
}

.block-container {
    max-width:1400px;
    padding-top:1.5rem;
}

[data-testid="stSidebar"] {
    background:#080c12;
}

.hero {
    background:linear-gradient(
        135deg,
        #0c1624,
        #111e30
    );
    border:1px solid #26374b;
    border-radius:22px;
    padding:28px;
    margin-bottom:25px;
}

.hero-title {
    color:white;
    font-size:34px;
    font-weight:800;
}

.hero-sub {
    color:#8fa0b5;
    margin-top:8px;
}

.section {
    color:white;
    font-size:22px;
    font-weight:800;
    margin-top:25px;
    margin-bottom:15px;
}

.match-card {
    background:linear-gradient(
        135deg,
        #0b1119,
        #111b28
    );
    border:1px solid #253449;
    border-radius:18px;
    padding:20px;
    margin:12px 0;
}

.match-date {
    color:#8190a4;
    font-size:13px;
}

.team {
    color:white;
    font-size:19px;
    font-weight:750;
}

.vs {
    color:#64748b;
    text-align:center;
    font-weight:700;
    padding:8px;
}

.score {
    color:white;
    font-size:26px;
    font-weight:800;
    text-align:center;
}

.league {
    color:#60a5fa;
    font-size:13px;
    margin-top:8px;
}

.ai-card {
    background:#0b1420;
    border:1px solid #2d4057;
    border-radius:18px;
    padding:22px;
    margin:10px 0;
}

.ai-title {
    color:#60a5fa;
    font-size:14px;
    font-weight:700;
}

.ai-value {
    color:white;
    font-size:25px;
    font-weight:850;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# API KEY
# ============================================================

try:

    API_KEY = st.secrets[
        "FOOTBALLDATA_API_KEY"
    ]

except Exception:

    API_KEY = ""


if not API_KEY:

    st.error(
        "âŒ FOOTBALLDATA_API_KEY nÃ£o encontrada."
    )

    st.info(
        "No Streamlit Cloud, adiciona a tua "
        "chave em Settings â†’ Secrets."
    )

    st.stop()


api = FootballAPI(API_KEY)


# ============================================================
# SESSION
# ============================================================

if "menu" not in st.session_state:
    st.session_state.menu = "ðŸ  Dashboard"

if "selected_match" not in st.session_state:
    st.session_state.selected_match = None

if "selected_match_data" not in st.session_state:
    st.session_state.selected_match_data = None


# ============================================================
# HELPERS
# ============================================================

def data_of(response):

    if not isinstance(response, dict):
        return {}

    data = response.get("data")

    if isinstance(data, dict):
        return data

    return {}


def extract_matches(response):

    if not isinstance(response, dict):
        return []

    data = response.get(
        "data",
        response
    )

    if isinstance(data, list):
        return data

    if not isinstance(data, dict):
        return []

    for key in [
        "matches",
        "fixtures",
        "games",
    ]:

        if isinstance(
            data.get(key),
            list
        ):

            return data[key]

    results = data.get(
        "results"
    )

    if isinstance(results, list):
        return results

    if isinstance(results, dict):

        for key in [
            "matches",
            "fixtures",
            "games",
        ]:

            if isinstance(
                results.get(key),
                list
            ):

                return results[key]

    return []


def team_obj(match, side):

    if side == "home":

        return (
            match.get("home_team")
            or match.get("homeTeam")
            or match.get("home")
            or {}
        )

    return (
        match.get("away_team")
        or match.get("awayTeam")
        or match.get("away")
        or {}
    )


def team_name(team):

    if isinstance(team, str):
        return team

    if not isinstance(team, dict):
        return "?"

    return (
        team.get("team_name")
        or team.get("name")
        or team.get("full_name")
        or "?"
    )


def match_id(match):

    return (
        match.get("match_id")
        or match.get("fixture_id")
        or match.get("id")
    )


def league_name(match):

    league = match.get(
        "league",
        {}
    )

    if not isinstance(
        league,
        dict
    ):
        return "CompetiÃ§Ã£o"

    return (
        league.get("name")
        or league.get(
            "competition_name"
        )
        or "CompetiÃ§Ã£o"
    )


def score(match):

    s = match.get(
        "score",
        {}
    )

    if not isinstance(s, dict):
        return 0, 0

    return (
        s.get("home", 0),
        s.get("away", 0)
    )


def fmt_date(value):

    if not value:
        return "â€”"

    value = str(value)

    for fmt in [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ]:

        try:

            dt = datetime.strptime(
                value,
                fmt
            )

            return dt.strftime(
                "%d/%m/%Y â€¢ %H:%M"
            )

        except Exception:
            pass

    return value


def pct(value):

    if value is None:
        return "â€”"

    try:

        value = float(value)

        return f"{value:.1f}%"

    except Exception:

        return str(value)


def select_match(match):
    """Guarda o jogo selecionado e abre a anÃ¡lise sem alterar
    diretamente a chave de um widget do Streamlit."""

    mid = match_id(match)

    if not mid:
        st.error("âŒ NÃ£o foi possÃ­vel identificar o ID da partida.")
        return

    st.session_state.selected_match = mid
    st.session_state.selected_match_data = match

    # Chave separada do widget radio. Isto evita StreamlitAPIException.
    st.session_state.open_analysis = True

    st.rerun()


# ============================================================
# SIDEBAR
# ============================================================

if "open_analysis" not in st.session_state:
    st.session_state.open_analysis = False

menu_options = [
    "ðŸ  Dashboard",
    "ðŸ“… Jogos",
    "ðŸ”Ž Analisar Jogo",
    "ðŸ” Buscar Time",
    "ðŸ“Š EstatÃ­sticas",
    "ðŸ† ClassificaÃ§Ã£o",
    "ðŸ’³ Uso da API",
]

# O radio nÃ£o usa mais key="menu". Assim o cÃ³digo nÃ£o tenta
# modificar o estado de um widget depois que ele foi criado.
menu = st.sidebar.radio(
    "MENU",
    menu_options,
)

# ApÃ³s clicar em "Analisar", mostramos a pÃ¡gina de anÃ¡lise.
if st.session_state.open_analysis:
    menu = "ðŸ”Ž Analisar Jogo"
    st.session_state.open_analysis = False


# ============================================================
# DASHBOARD
# ============================================================

if menu == "ðŸ  Dashboard":

    st.markdown(
        """
        <div class="hero">

            <div class="hero-title">
                âš½ Football Stats AI
            </div>

            <div class="hero-sub">
                EstatÃ­sticas e anÃ¡lise de futebol
                baseada nos dados da API
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    with st.spinner(
        "Carregando jogos..."
    ):

        today_response = api.today()

        live_response = api.live()

        upcoming_response = api.upcoming()

    today_matches = extract_matches(
        today_response
    )

    live_matches = extract_matches(
        live_response
    )

    upcoming_matches = extract_matches(
        upcoming_response
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "ðŸ“… Jogos",
        len(today_matches)
    )

    c2.metric(
        "ðŸ”´ Ao vivo",
        len(live_matches)
    )

    c3.metric(
        "â­ PrÃ³ximos",
        len(upcoming_matches)
    )

    st.markdown(
        '<div class="section">'
        'ðŸ”¥ Jogos de hoje'
        '</div>',
        unsafe_allow_html=True
    )

    if not today_matches:

        st.warning(
            "Nenhum jogo encontrado."
        )

    else:

        for match in today_matches:

            home = team_name(
                team_obj(match, "home")
            )

            away = team_name(
                team_obj(match, "away")
            )

            mid = match_id(match)

            hs, aws = score(match)

            st.markdown(
                f"""
                <div class="match-card">

                    <div class="match-date">
                        {fmt_date(
                            match.get(
                                "match_date"
                            )
                        )}
                    </div>

                    <br>

                    <div class="team">
                        ðŸ  {home}
                    </div>

                    <div class="vs">
                        ðŸ†š
                    </div>

                    <div class="team">
                        âœˆï¸ {away}
                    </div>

                    <div class="score">
                        {hs} - {aws}
                    </div>

                    <div class="league">
                        ðŸ† {league_name(match)}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(
                f"ðŸ“Š Analisar {home} x {away}",
                key=f"an_{mid}",
                use_container_width=True
            ):

                select_match(match)


# ============================================================
# JOGOS
# ============================================================

elif menu == "ðŸ“… Jogos":

    st.title(
        "ðŸ“… Jogos por data"
    )

    selected_date = st.date_input(
        "Selecionar data",
        value=date.today()
    )

    if st.button(
        "ðŸ”Ž CARREGAR JOGOS",
        use_container_width=True
    ):

        date_string = (
            selected_date.strftime(
                "%Y-%m-%d"
            )
        )

        with st.spinner(
            "Buscando jogos..."
        ):

            response = api.matches_by_date(
                date_string
            )

        matches = extract_matches(
            response
        )

        st.session_state.date_matches = (
            matches
        )

        st.session_state.date_response = (
            response
        )

    matches = st.session_state.get(
        "date_matches"
    )

    if matches is not None:

        if not matches:

            st.warning(
                "Nenhum jogo encontrado "
                "para essa data."
            )

            with st.expander(
                "ðŸ”§ Resposta da API"
            ):

                st.json(
                    st.session_state.get(
                        "date_response",
                        {}
                    )
                )

        else:

            st.success(
                f"âš½ {len(matches)} jogos encontrados."
            )

            for match in matches:

                home = team_name(
                    team_obj(
                        match,
                        "home"
                    )
                )

                away = team_name(
                    team_obj(
                        match,
                        "away"
                    )
                )

                mid = match_id(match)

                hs, aws = score(match)

                st.markdown(
                    f"""
                    <div class="match-card">

                        <div class="match-date">
                            {fmt_date(
                                match.get(
                                    "match_date"
                                )
                            )}
                        </div>

                        <br>

                        <div class="team">
                            ðŸ  {home}
                        </div>

                        <div class="vs">
                            ðŸ†š
                        </div>

                        <div class="team">
                            âœˆï¸ {away}
                        </div>

                        <div class="score">
                            {hs} - {aws}
                        </div>

                        <div class="league">
                            ðŸ† {league_name(match)}
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if st.button(
                    f"ðŸ“Š Analisar {home} x {away}",
                    key=f"date_{mid}",
                    use_container_width=True
                ):

                    select_match(match)


# ============================================================
# ANÃLISE
# ============================================================

elif menu == "ðŸ”Ž Analisar Jogo":

    st.title(
        "ðŸ”Ž AnÃ¡lise Inteligente"
    )

    selected_id = st.session_state.get(
        "selected_match"
    )

    selected_match = st.session_state.get(
        "selected_match_data"
    )

    if not selected_id:

        st.info(
            "Escolha um jogo primeiro."
        )

        st.stop()

    if not selected_match:

        selected_match = {}

    home = team_name(
        team_obj(
            selected_match,
            "home"
        )
    )

    away = team_name(
        team_obj(
            selected_match,
            "away"
        )
    )

    hs, aws = score(
        selected_match
    )

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    st.markdown(
        f"""
        <div class="hero">

            <div style="
                text-align:center;
                color:#60a5fa;
                font-size:14px;
            ">
                ðŸ† {league_name(
                    selected_match
                )}
            </div>

            <div style="
                text-align:center;
                color:#8190a4;
                margin-top:5px;
            ">
                {fmt_date(
                    selected_match.get(
                        "match_date"
                    )
                )}
            </div>

            <br>

            <div style="
                text-align:center;
                color:white;
                font-size:24px;
                font-weight:800;
            ">
                ðŸ  {home}
            </div>

            <div style="
                text-align:center;
                color:white;
                font-size:34px;
                font-weight:900;
                margin:10px;
            ">
                {hs} - {aws}
            </div>

            <div style="
                text-align:center;
                color:white;
                font-size:24px;
                font-weight:800;
            ">
                âœˆï¸ {away}
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.caption(
        f"Match ID: {selected_id}"
    )

    # --------------------------------------------------------
    # API
    # --------------------------------------------------------

    with st.spinner(
        "ðŸ§  A IA estÃ¡ analisando os dados..."
    ):

        detail_response = api.match(
            selected_id
        )

        stats_response = api.stats(
            selected_id
        )

        probabilities_response = (
            api.probabilities(
                selected_id
            )
        )

        predictions_response = (
            api.predictions(
                selected_id
            )
        )

    # --------------------------------------------------------
    # MOTOR
    # --------------------------------------------------------

    analysis = analisar_partida(
        predictions_response,
        probabilities_response,
        stats_response,
    )

    # --------------------------------------------------------
    # MELHOR MERCADO
    # --------------------------------------------------------

    st.markdown(
        '<div class="section">'
        'ðŸ§  Melhor oportunidade'
        '</div>',
        unsafe_allow_html=True
    )

    a1, a2 = st.columns(2)

    with a1:

        st.markdown(
            f"""
            <div class="ai-card">

                <div class="ai-title">
                    ðŸŽ¯ MELHOR MERCADO
                </div>

                <div class="ai-value">
                    {analysis[
                        "best_market"
                    ]}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    with a2:

        st.markdown(
            f"""
            <div class="ai-card">

                <div class="ai-title">
                    ðŸ”¥ CONFIANÃ‡A
                </div>

                <div class="ai-value">
                    {pct(
                        analysis[
                            "best_confidence"
                        ]
                    )}
                </div>

                <div>
                    {analysis[
                        "confidence_label"
                    ]}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    st.markdown(
        '<div class="section">'
        'ðŸ† Resultado'
        '</div>',
        unsafe_allow_html=True
    )

    r1, r2, r3 = st.columns(3)

    r1.metric(
        f"ðŸ  {home}",
        pct(
            analysis[
                "winner"
            ]["home"]
        )
    )

    r2.metric(
        "ðŸ¤ Empate",
        pct(
            analysis[
                "winner"
            ]["draw"]
        )
    )

    r3.metric(
        f"âœˆï¸ {away}",
        pct(
            analysis[
                "winner"
            ]["away"]
        )
    )

    # --------------------------------------------------------
    # GOLS
    # --------------------------------------------------------

    st.markdown(
        '<div class="section">'
        'âš½ Gols'
        '</div>',
        unsafe_allow_html=True
    )

    goals = analysis["goals"]

    g1, g2, g3, g4, g5 = st.columns(5)

    g1.metric(
        "Over 0.5",
        pct(
            goals["over_0_5"]
        )
    )

    g2.metric(
        "Over 1.5",
        pct(
            goals["over_1_5"]
        )
    )

    g3.metric(
        "Over 2.5",
        pct(
            goals["over_2_5"]
        )
    )

    g4.metric(
        "Over 3.5",
        pct(
            goals["over_3_5"]
        )
    )

    g5.metric(
        "Over 4.5",
        pct(
            goals["over_4_5"]
        )
    )

    # --------------------------------------------------------
    # BTTS
    # --------------------------------------------------------

    st.markdown(
        '<div class="section">'
        'âš½ Ambas Marcam'
        '</div>',
        unsafe_allow_html=True
    )

    st.metric(
        "BTTS â€” SIM",
        pct(
            analysis["btts"]
        )
    )

    # --------------------------------------------------------
    # ESCANTEIOS
    # --------------------------------------------------------

    st.markdown(
        '<div class="section">'
        'ðŸš© Escanteios'
        '</div>',
        unsafe_allow_html=True
    )

    corners = analysis["corners"]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Potencial",
        pct(
            corners["potential"]
        )
    )

    c2.metric(
        "Over 8.5",
        pct(
            corners["over_8_5"]
        )
    )

    c3.metric(
        "Over 9.5",
        pct(
            corners["over_9_5"]
        )
    )

    c4.metric(
        "Over 10.5",
        pct(
            corners["over_10_5"]
        )
    )

    # --------------------------------------------------------
    # XG
    # --------------------------------------------------------

    st.markdown(
        '<div class="section">'
        'ðŸ“ˆ xG prÃ©-jogo'
        '</div>',
        unsafe_allow_html=True
    )

    xg = analysis["xg"]

    x1, x2, x3 = st.columns(3)

    x1.metric(
        home,
        xg["home"]
        if xg["home"] is not None
        else "â€”"
    )

    x2.metric(
        away,
        xg["away"]
        if xg["away"] is not None
        else "â€”"
    )

    x3.metric(
        "Total",
        xg["total"]
        if xg["total"] is not None
        else "â€”"
    )

    # --------------------------------------------------------
    # PALPITES
    # --------------------------------------------------------

    st.markdown(
        '<div class="section">'
        'ðŸŽ¯ Palpites sugeridos'
        '</div>',
        unsafe_allow_html=True
    )

    picks = analysis["picks"]

    if picks:

        for name, value in picks:

            st.success(
                f"{name}  â€¢  {pct(value)}"
            )

    else:

        st.info(
            "NÃ£o hÃ¡ mercados com confianÃ§a "
            "suficiente para sugerir um palpite."
        )

    # --------------------------------------------------------
    # CONFIANÃ‡A
    # --------------------------------------------------------

    st.markdown(
        '<div class="section">'
        'ðŸ”¥ ConfianÃ§a geral'
        '</div>',
        unsafe_allow_html=True
    )

    confidence = analysis[
        "confidence"
    ]

    if confidence is not None:

        st.progress(
            min(
                max(
                    int(confidence),
                    0
                ),
                100
            )
        )

        st.write(
            f"**{confidence:.1f}%** â€” "
            f"{analysis['confidence_label']}"
        )

    else:

        st.info(
            "Dados insuficientes."
        )

    # --------------------------------------------------------
    # DEBUG
    # --------------------------------------------------------

    with st.expander(
        "ðŸ”§ Dados recebidos da API"
    ):

        st.write("### Partida")

        st.json(
            detail_response
        )

        st.write("### EstatÃ­sticas")

        st.json(
            stats_response
        )

        st.write("### Probabilidades")

        st.json(
            probabilities_response
        )

        st.write("### Predictions")

        st.json(
            predictions_response
        )


# ============================================================
# BUSCAR TIME
# ============================================================

elif menu == "ðŸ” Buscar Time":

    st.title(
        "ðŸ” Buscar Time"
    )

    query = st.text_input(
        "Digite o nome do time",
        placeholder="Barcelona"
    )

    if st.button(
        "ðŸ”Ž PESQUISAR",
        use_container_width=True
    ):

        response = api.search(
            query,
            search_type="teams"
        )

        data = data_of(
            response
        )

        results = data.get(
            "results",
            {}
        )

        teams = results.get(
            "teams",
            []
        )

        if not teams:

            st.warning(
                "Nenhum time encontrado."
            )

        for team in teams:

            name = team.get(
                "team_name",
                "?"
            )

            country = team.get(
                "country",
                "?"
            )

            tid = team.get(
                "team_id"
            )

            st.markdown(
                f"""
                <div class="match-card">

                    <div class="team">
                        âš½ {name}
                    </div>

                    <div class="match-date">
                        ðŸŒ {country}
                        â€¢ ID {tid}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )


# ============================================================
# ESTATÃSTICAS
# ============================================================

elif menu == "ðŸ“Š EstatÃ­sticas":

    st.title(
        "ðŸ“Š EstatÃ­sticas do Time"
    )

    team_id = st.number_input(
        "ID do time",
        min_value=1,
        value=77
    )

    if st.button(
        "ðŸ“Š CARREGAR",
        use_container_width=True
    ):

        response = api.team_stats(
            int(team_id)
        )

        st.json(
            response
        )


# ============================================================
# CLASSIFICAÃ‡ÃƒO
# ============================================================

elif menu == "ðŸ† ClassificaÃ§Ã£o":

    st.title(
        "ðŸ† ClassificaÃ§Ã£o"
    )

    league_id = st.number_input(
        "ID da liga",
        min_value=1,
        value=10
    )

    if st.button(
        "ðŸ† CARREGAR",
        use_container_width=True
    ):

        response = api.standings(
            int(league_id)
        )

        st.json(
            response
        )


# ============================================================
# USO
# ============================================================

elif menu == "ðŸ’³ Uso da API":

    st.title(
        "ðŸ’³ Uso da API"
    )

    response = api.usage()

    st.json(
        response
    )
