# -*- coding: utf-8 -*-
"""Football Stats AI — dashboard Streamlit.

Melhorias face à versão original:
- Removida duplicação do "match-card" (agora é uma função reutilizável)
- Chamadas à API com cache (st.cache_data) para evitar pedidos repetidos
- Corrigido o bug em que a sidebar não refletia a página "Analisar Jogo"
  depois de clicar no botão de um jogo
- Nomes de variáveis mais claros (sem reaproveitar c1/c2/c3 em contextos
  diferentes)
- Exceções tratadas de forma mais específica, com mensagens úteis
"""

from datetime import date, datetime

import streamlit as st

from football_api import FootballAPI
from ai_engine import analisar_partida


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="Football Stats AI",
    page_icon="⚽",
    layout="wide",
)

CSS = """
<style>
.stApp { background:#05080d; }
.block-container { max-width:1400px; padding-top:1.5rem; }
[data-testid="stSidebar"] { background:#080c12; }

.hero {
    background:linear-gradient(135deg, #0c1624, #111e30);
    border:1px solid #26374b;
    border-radius:22px;
    padding:28px;
    margin-bottom:25px;
}
.hero-title { color:white; font-size:34px; font-weight:800; }
.hero-sub { color:#8fa0b5; margin-top:8px; }

.section {
    color:white;
    font-size:22px;
    font-weight:800;
    margin-top:25px;
    margin-bottom:15px;
}

.match-card {
    background:linear-gradient(135deg, #0b1119, #111b28);
    border:1px solid #253449;
    border-radius:18px;
    padding:20px;
    margin:12px 0;
}
.match-date { color:#8190a4; font-size:13px; }
.team { color:white; font-size:19px; font-weight:750; }
.vs { color:#64748b; text-align:center; font-weight:700; padding:8px; }
.score { color:white; font-size:26px; font-weight:800; text-align:center; }
.league { color:#60a5fa; font-size:13px; margin-top:8px; }

.ai-card {
    background:#0b1420;
    border:1px solid #2d4057;
    border-radius:18px;
    padding:22px;
    margin:10px 0;
}
.ai-title { color:#60a5fa; font-size:14px; font-weight:700; }
.ai-value { color:white; font-size:25px; font-weight:850; }
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)


# ============================================================
# API KEY
# ============================================================

API_KEY = st.secrets.get("FOOTBALLDATA_API_KEY", "")

if not API_KEY:
    st.error("❌ FOOTBALLDATA_API_KEY não encontrada.")
    st.info("No Streamlit Cloud, adiciona a tua chave em Settings → Secrets.")
    st.stop()

api = FootballAPI(API_KEY)


# ============================================================
# SESSION STATE
# ============================================================

DEFAULTS = {
    "selected_match": None,
    "selected_match_data": None,
    "open_analysis": False,
    "current_menu": None,
}
for _key, _value in DEFAULTS.items():
    st.session_state.setdefault(_key, _value)


# ============================================================
# HELPERS — extração de dados da API
# ============================================================

def data_of(response: dict) -> dict:
    if not isinstance(response, dict):
        return {}
    data = response.get("data")
    return data if isinstance(data, dict) else {}


def extract_matches(response) -> list:
    if not isinstance(response, dict):
        return []

    data = response.get("data", response)

    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []

    for key in ("matches", "fixtures", "games"):
        if isinstance(data.get(key), list):
            return data[key]

    results = data.get("results")
    if isinstance(results, list):
        return results
    if isinstance(results, dict):
        for key in ("matches", "fixtures", "games"):
            if isinstance(results.get(key), list):
                return results[key]

    return []


def team_obj(match: dict, side: str) -> dict:
    if side == "home":
        return match.get("home_team") or match.get("homeTeam") or match.get("home") or {}
    return match.get("away_team") or match.get("awayTeam") or match.get("away") or {}


def team_name(team) -> str:
    if isinstance(team, str):
        return team
    if not isinstance(team, dict):
        return "?"
    return team.get("team_name") or team.get("name") or team.get("full_name") or "?"


def match_id(match: dict):
    return match.get("match_id") or match.get("fixture_id") or match.get("id")


def league_name(match: dict) -> str:
    league = match.get("league", {})
    if not isinstance(league, dict):
        return "Competição"
    return league.get("name") or league.get("competition_name") or "Competição"


def score(match: dict):
    s = match.get("score", {})
    if not isinstance(s, dict):
        return 0, 0
    return s.get("home", 0), s.get("away", 0)


DATE_FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d")


def fmt_date(value) -> str:
    if not value:
        return "—"

    value = str(value)

    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime("%d/%m/%Y • %H:%M")
        except ValueError:
            continue

    return value


def pct(value) -> str:
    if value is None:
        return "—"
    try:
        return f"{float(value):.1f}%"
    except (TypeError, ValueError):
        return str(value)


def section_title(text: str) -> None:
    st.markdown(f'<div class="section">{text}</div>', unsafe_allow_html=True)


def select_match(match: dict) -> None:
    """Guarda o jogo selecionado e sinaliza abertura da página de análise."""
    mid = match_id(match)

    if not mid:
        st.error("❌ Não foi possível identificar o ID da partida.")
        return

    st.session_state.selected_match = mid
    st.session_state.selected_match_data = match
    st.session_state.open_analysis = True
    st.rerun()


def render_match_card(match: dict, key_prefix: str) -> None:
    """Desenha um cartão de jogo + botão de análise. Usado no Dashboard e em Jogos."""
    home = team_name(team_obj(match, "home"))
    away = team_name(team_obj(match, "away"))
    mid = match_id(match)
    hs, aws = score(match)

    st.markdown(
        f"""
        <div class="match-card">
            <div class="match-date">{fmt_date(match.get("match_date"))}</div>
            <br>
            <div class="team">🏠 {home}</div>
            <div class="vs">🆚</div>
            <div class="team">✈️ {away}</div>
            <div class="score">{hs} - {aws}</div>
            <div class="league">🏆 {league_name(match)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        f"📊 Analisar {home} x {away}",
        key=f"{key_prefix}_{mid}",
        use_container_width=True,
    ):
        select_match(match)


# ============================================================
# CHAMADAS À API COM CACHE
# ============================================================

@st.cache_data(ttl=60, show_spinner=False)
def cached_today():
    return api.today()


@st.cache_data(ttl=30, show_spinner=False)
def cached_live():
    return api.live()


@st.cache_data(ttl=60, show_spinner=False)
def cached_upcoming():
    return api.upcoming()


@st.cache_data(ttl=300, show_spinner=False)
def cached_matches_by_date(date_string: str):
    return api.matches_by_date(date_string)


@st.cache_data(ttl=120, show_spinner=False)
def cached_match_bundle(mid):
    """Agrupa as 4 chamadas necessárias para a página de análise."""
    return (
        api.match(mid),
        api.stats(mid),
        api.probabilities(mid),
        api.predictions(mid),
    )


# ============================================================
# SIDEBAR
# ============================================================

MENU_OPTIONS = [
    "🏠 Dashboard",
    "📅 Jogos",
    "🔎 Analisar Jogo",
    "🔍 Buscar Time",
    "📊 Estatísticas",
    "🏆 Classificação",
    "💳 Uso da API",
]

# Decidimos o menu a mostrar ANTES de criar o widget, para que a sidebar
# reflita corretamente a página atual (isto corrige o bug em que, ao clicar
# em "Analisar", o conteúdo mudava mas a seleção da sidebar ficava desatualizada).
if st.session_state.open_analysis:
    default_menu = "🔎 Analisar Jogo"
    st.session_state.open_analysis = False
else:
    default_menu = st.session_state.current_menu or MENU_OPTIONS[0]

menu = st.sidebar.radio(
    "MENU",
    MENU_OPTIONS,
    index=MENU_OPTIONS.index(default_menu),
)
st.session_state.current_menu = menu


# ============================================================
# DASHBOARD
# ============================================================

if menu == "🏠 Dashboard":

    st.markdown(
        """
        <div class="hero">
            <div class="hero-title">⚽ Football Stats AI</div>
            <div class="hero-sub">Estatísticas e análise de futebol baseada nos dados da API</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.spinner("Carregando jogos..."):
        today_matches = extract_matches(cached_today())
        live_matches = extract_matches(cached_live())
        upcoming_matches = extract_matches(cached_upcoming())

    col_today, col_live, col_upcoming = st.columns(3)
    col_today.metric("📅 Jogos", len(today_matches))
    col_live.metric("🔴 Ao vivo", len(live_matches))
    col_upcoming.metric("⭐ Próximos", len(upcoming_matches))

    section_title("🔥 Jogos de hoje")

    if not today_matches:
        st.warning("Nenhum jogo encontrado.")
    else:
        for match in today_matches:
            render_match_card(match, key_prefix="dash")


# ============================================================
# JOGOS
# ============================================================

elif menu == "📅 Jogos":

    st.title("📅 Jogos por data")

    selected_date = st.date_input("Selecionar data", value=date.today())

    if st.button("🔎 CARREGAR JOGOS", use_container_width=True):
        date_string = selected_date.strftime("%Y-%m-%d")

        with st.spinner("Buscando jogos..."):
            response = cached_matches_by_date(date_string)

        st.session_state.date_matches = extract_matches(response)
        st.session_state.date_response = response

    matches = st.session_state.get("date_matches")

    if matches is not None:
        if not matches:
            st.warning("Nenhum jogo encontrado para essa data.")
            with st.expander("🔧 Resposta da API"):
                st.json(st.session_state.get("date_response", {}))
        else:
            st.success(f"⚽ {len(matches)} jogos encontrados.")
            for match in matches:
                render_match_card(match, key_prefix="date")


# ============================================================
# ANÁLISE
# ============================================================

elif menu == "🔎 Analisar Jogo":

    st.title("🔎 Análise Inteligente")

    selected_id = st.session_state.get("selected_match")
    selected_match = st.session_state.get("selected_match_data") or {}

    if not selected_id:
        st.info("Escolha um jogo primeiro.")
        st.stop()

    home = team_name(team_obj(selected_match, "home"))
    away = team_name(team_obj(selected_match, "away"))
    hs, aws = score(selected_match)

    st.markdown(
        f"""
        <div class="hero">
            <div style="text-align:center; color:#60a5fa; font-size:14px;">
                🏆 {league_name(selected_match)}
            </div>
            <div style="text-align:center; color:#8190a4; margin-top:5px;">
                {fmt_date(selected_match.get("match_date"))}
            </div>
            <br>
            <div style="text-align:center; color:white; font-size:24px; font-weight:800;">
                🏠 {home}
            </div>
            <div style="text-align:center; color:white; font-size:34px; font-weight:900; margin:10px;">
                {hs} - {aws}
            </div>
            <div style="text-align:center; color:white; font-size:24px; font-weight:800;">
                ✈️ {away}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(f"Match ID: {selected_id}")

    with st.spinner("🧠 A IA está analisando os dados..."):
        try:
            detail_response, stats_response, probabilities_response, predictions_response = (
                cached_match_bundle(selected_id)
            )
        except Exception as exc:
            st.error(f"❌ Erro ao obter dados da API: {exc}")
            st.stop()

    analysis = analisar_partida(
        predictions_response,
        probabilities_response,
        stats_response,
    )

    # --- Melhor mercado -----------------------------------------------
    if analysis.get("predictions_plan_gated"):
        st.warning(
            "⚠️ O endpoint de previsões completas (Predictions) exige o "
            "plano Pro da API. Estás a ver apenas os dados disponíveis no "
            "plano atual (probabilidades e estatísticas), por isso alguns "
            "mercados podem aparecer como '—'."
        )

    section_title("🧠 Melhor oportunidade")
    a1, a2 = st.columns(2)

    with a1:
        st.markdown(
            f"""
            <div class="ai-card">
                <div class="ai-title">🎯 MELHOR MERCADO</div>
                <div class="ai-value">{analysis["best_market"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with a2:
        st.markdown(
            f"""
            <div class="ai-card">
                <div class="ai-title">🔥 CONFIANÇA</div>
                <div class="ai-value">{pct(analysis["best_confidence"])}</div>
                <div>{analysis["confidence_label"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # --- Resultado -------------------------------------------------------
    section_title("🏆 Resultado")
    r1, r2, r3 = st.columns(3)
    r1.metric(f"🏠 {home}", pct(analysis["winner"]["home"]))
    r2.metric("🤝 Empate", pct(analysis["winner"]["draw"]))
    r3.metric(f"✈️ {away}", pct(analysis["winner"]["away"]))

    # --- Gols --------------------------------------------------------------
    section_title("⚽ Gols")
    goals = analysis["goals"]
    goal_cols = st.columns(5)
    goal_labels = ["Over 0.5", "Over 1.5", "Over 2.5", "Over 3.5", "Over 4.5"]
    goal_keys = ["over_0_5", "over_1_5", "over_2_5", "over_3_5", "over_4_5"]
    for col, label, gkey in zip(goal_cols, goal_labels, goal_keys):
        col.metric(label, pct(goals[gkey]))

    # --- BTTS --------------------------------------------------------------
    section_title("⚽ Ambas Marcam")
    st.metric("BTTS — SIM", pct(analysis["btts"]))

    # --- Escanteios ----------------------------------------------------
    section_title("🚩 Escanteios")
    corners = analysis["corners"]
    co1, co2, co3, co4 = st.columns(4)
    co1.metric("Potencial", pct(corners["potential"]))
    co2.metric("Over 8.5", pct(corners["over_8_5"]))
    co3.metric("Over 9.5", pct(corners["over_9_5"]))
    co4.metric("Over 10.5", pct(corners["over_10_5"]))

    # --- xG ------------------------------------------------------------
    section_title("📈 xG pré-jogo")
    xg = analysis["xg"]
    x1, x2, x3 = st.columns(3)
    x1.metric(home, xg["home"] if xg["home"] is not None else "—")
    x2.metric(away, xg["away"] if xg["away"] is not None else "—")
    x3.metric("Total", xg["total"] if xg["total"] is not None else "—")

    # --- Palpites --------------------------------------------------------
    section_title("🎯 Palpites sugeridos")
    picks = analysis["picks"]

    if picks:
        for name, value in picks:
            st.success(f"{name}  •  {pct(value)}")
    else:
        st.info("Não há mercados com confiança suficiente para sugerir um palpite.")

    # --- Confiança geral -------------------------------------------------
    section_title("🔥 Confiança geral")
    confidence = analysis["confidence"]

    if confidence is not None:
        st.progress(min(max(int(confidence), 0), 100))
        st.write(f"**{confidence:.1f}%** — {analysis['confidence_label']}")
    else:
        st.info("Dados insuficientes.")

    # --- Debug -------------------------------------------------------------
    with st.expander("🔧 Dados recebidos da API"):
        st.write("### Partida")
        st.json(detail_response)
        st.write("### Estatísticas")
        st.json(stats_response)
        st.write("### Probabilidades")
        st.json(probabilities_response)
        st.write("### Predictions")
        st.json(predictions_response)


# ============================================================
# BUSCAR TIME
# ============================================================

elif menu == "🔍 Buscar Time":

    st.title("🔍 Buscar Time")

    query = st.text_input("Digite o nome do time", placeholder="Barcelona")

    if st.button("🔎 PESQUISAR", use_container_width=True):
        with st.spinner("Pesquisando..."):
            response = api.search(query, search_type="teams")

        data = data_of(response)
        results = data.get("results", {})
        teams = results.get("teams", [])

        if not teams:
            st.warning("Nenhum time encontrado.")

        for team in teams:
            name = team.get("team_name", "?")
            country = team.get("country", "?")
            tid = team.get("team_id")

            st.markdown(
                f"""
                <div class="match-card">
                    <div class="team">⚽ {name}</div>
                    <div class="match-date">🌍 {country} • ID {tid}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# ESTATÍSTICAS
# ============================================================

elif menu == "📊 Estatísticas":

    st.title("📊 Estatísticas do Time")
    st.caption("Não sabes o ID? Usa primeiro '🔍 Buscar Time' para encontrar o ID pelo nome.")

    team_id = st.number_input("ID do time", min_value=1, value=77)

    if st.button("📊 CARREGAR", use_container_width=True):
        with st.spinner("Carregando estatísticas..."):
            response = api.team_stats(int(team_id))
        st.json(response)


# ============================================================
# CLASSIFICAÇÃO
# ============================================================

elif menu == "🏆 Classificação":

    st.title("🏆 Classificação")

    league_id = st.number_input("ID da liga", min_value=1, value=10)

    if st.button("🏆 CARREGAR", use_container_width=True):
        with st.spinner("Carregando classificação..."):
            response = api.standings(int(league_id))
        st.json(response)


# ============================================================
# USO
# ============================================================

elif menu == "💳 Uso da API":

    st.title("💳 Uso da API")
    st.json(api.usage())
