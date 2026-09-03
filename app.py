# -*- codificação: utf-8 -*-
"Estatísticas de Futebol com IA — painel Streamlit."

Melhorias face versão original:
- Removida duplicação do "match-card" (agora é uma função reutilizável)
- Chamadas à API com cache (st.cache_data) para evitar pedidos repetidos
- Corrigido o bug em que a barra lateral não refletia a página "Analisar Jogo"
  depois de clicar no botão de um jogo
- Nomes de variáveis ​​mais claras (sem reaproveitar c1/c2/c3 em contextos
  diferentes)
- Exceções tratadas de forma mais específica, com mensagens únicas
"""

Importe data e hora a partir de datetime.

importar streamlit como st

from football_api import FootballAPI
da importação ai_engine analisar_partida


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="Estatísticas de Futebol com IA",
    page_icon="âš½",
    layout="amplo",
)

CSS = """
<style>
.stApp { background:#05080d; }
.block-container { max-width:1400px; padding-top:1.5rem; }
[data-testid="stSidebar"] { background:#080c12; }

.herói {
    fundo:gradiente-linear(135deg, #0c1624, #111e30);
    borda:1px sólida #26374b;
    raio-da-borda:22px;
    preenchimento: 28px;
    margem-inferior:25px;
}
.hero-title { color:white; font-size:34px; font-weight:800; }
.hero-sub { color:#8fa0b5; margin-top:8px; }

.seção {
    cor: branca;
    tamanho da fonte: 22px;
    peso da fonte: 800;
    margem-superior:25px;
    margem-inferior:15px;
}

.match-card {
    fundo:gradiente-linear(135deg, #0b1119, #111b28);
    borda:1px sólida #253449;
    raio-da-borda:18px;
    preenchimento: 20px;
    margem:12px 0;
}
.match-date { color:#8190a4; font-size:13px; }
.equipe { cor:branco; tamanho da fonte:19px; peso da fonte:750; }
.vs { color:#64748b; text-align:center; font-weight:700; padding:8px; }
.score { color:white; font-size:26px; font-weight:800; text-align:center; }
.league { color:#60a5fa; font-size:13px; margin-top:8px; }

.ai-card {
    fundo:#0b1420;
    borda:1px sólida #2d4057;
    raio-da-borda:18px;
    preenchimento: 22px;
    margem:10px 0;
}
.ai-title { color:#60a5fa; font-size:14px; font-weight:700; }
.ai-value { color:white; font-size:25px; font-weight:850; }
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)


# ============================================================
# CHAVE DE API
# ============================================================

API_KEY = st.secrets.get("FOOTBALLDATA_API_KEY", "")

se não for uma API_KEY:
    st.error("â Œ FOOTBALLDATA_API_KEY não encontrado.")
    st.info("No Streamlit Cloud, adicione sua chave em Configurações → Segredos.")
    st.stop()

api = FootballAPI(API_KEY)


# ============================================================
# ESTADO DA SESSÃO
# ============================================================

PADRÕES = {
    "selected_match": Nenhum,
    "selected_match_data": Nenhum,
    "open_analysis": Falso,
    "menu_atual": Nenhum,
}
para _key, _value em DEFAULTS.items():
    st.session_state.setdefault(_key, _value)


# ============================================================
# HELPERS — extração de dados da API
# ============================================================

def data_of(response: dict) -> dict:
    se não isinstance(response, dict):
        retornar {}
    dados = resposta.obter("dados")
    retorna os dados se isinstance(dados, dict) senão {}


def extract_matches(response) -> list:
    se não isinstance(response, dict):
        retornar []

    dados = resposta.get("dados", resposta)

    se isinstance(dados, lista):
        retornar dados
    se não isinstance(data, dict):
        retornar []

    para chave em ("partidas", "confrontos", "jogos"):
        se isinstance(data.get(key), list):
            retornar dados[chave]

    resultados = dados.obter("resultados")
    se isinstance(results, list):
        retornar resultados
    se isinstance(results, dict):
        para chave em ("partidas", "confrontos", "jogos"):
            se isinstance(results.get(key), list):
                retornar resultados[chave]

    retornar []


def team_obj(match: dict, side: str) -> dict:
    se lado == "casa":
        retornar match.get("home_team") ou match.get("homeTeam") ou match.get("home") ou {}
    retornar match.get("away_team") ou match.get("awayTeam") ou match.get("away") ou {}


def team_name(team) -> str:
    se isinstance(team, str):
        equipe de retorno
    se não isinstance(team, dict):
        retornar "?"
    retornar team.get("team_name") ou team.get("name") ou team.get("full_name") ou "?"


def match_id(match: dict):
    retornar match.get("match_id") ou match.get("fixture_id") ou match.get("id")


def nome_da_liga(match: dict) -> str:
    liga = partida.get("liga", {})
    se não isinstance(league, dict):
        retornar "Competição"
    retornar league.get("name") ou league.get("competition_name") ou "Competição"


def score(match: dict):
    s = match.get("score", {})
    se não for uma instância de `s`, `dict`:
        retornar 0, 0
    retornar s.get("home", 0), s.get("away", 0)


FORMATOS_DE_DATA = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d")


def fmt_date(value) -> str:
    se não houver valor:
        retornar "â-"

    valor = str(valor)

    para fmt em DATE_FORMATS:
        tentar:
            dt = datetime.strptime(value, fmt)
            retornar dt.strftime("%d/%m/%Y • %H:%M")
        exceto ValueError:
            continuar

    valor de retorno


def pct(valor) -> str:
    Se o valor for None:
        retornar "â-"
    tentar:
        retornar f"{float(valor):.1f}%"
    exceto (TypeError, ValueError):
        retornar str(valor)


def section_title(text: str) -> None:
    st.markdown(f'<div class="section">{text}</div>', unsafe_allow_html=True)


def select_match(match: dict) -> None:
    """Guarde o jogo selecionado e sinalizando abertura da página de análise."""
    meio = id_da_correspondência(correspondência)

    se não for meio:
        st.error("Não foi possível identificar o ID da partida.")
        retornar

    st.session_state.selected_match = meio
    st.session_state.selected_match_data = match
    st.session_state.open_analysis = True
    st.rerun()


def render_match_card(match: dict, key_prefix: str) -> None:
    """Desenha um cartão de jogo + botão de análise. Usado no Dashboard e em Jogos."""
    casa = nome_da_equipe(objeto_da_equipe(partida, "casa"))
    fora = nome_do_time(objeto_do_time(partida, "fora"))
    meio = id_da_correspondência(correspondência)
    hs, aws = pontuação(correspondência)

    st.markdown(
        f"""
        <div class="match-card">
            <div class="match-date">{fmt_date(match.get("match_date"))}</div>
            <br>
            <div class="team">ðŸ {home div>
            <div class="vs">ðŸ†š</div>
            <div class="team">âœˆï¸ {away disdiv>
            <div class="score">{hs} - {aws}</div>
            <div class="league">ðŸ † {league_name(match)}</div>
        </div>
        "",
        unsafe_allow_html=True,
    )

    se st.botão(
        f"ðŸ“Š Analisar {casa} x {fora}",
        chave=f"{prefixo_chave}_{meio}",
        use_container_width=True,
    ):
        selecionar_correspondência(correspondência)


# ============================================================
# CHAMADAS Ã€ API COM CACHE
# ============================================================

@st.cache_data(ttl=60, show_spinner=False)
def cached_today():
    retornar api.hoje()


@st.cache_data(ttl=30, show_spinner=False)
def cached_live():
    retornar api.live()


@st.cache_data(ttl=60, show_spinner=False)
def cached_upcoming():
    retornar api.upcoming()


@st.cache_data(ttl=300, show_spinner=False)
def cached_matches_by_date(date_string: str):
    retornar api.matches_by_date(date_string)


@st.cache_data(ttl=120, show_spinner=False)
def cached_match_bundle(mid):
    """Agrupa as 4 chamadas necessárias para a página de análise."""
    retornar (
        api.match(mid),
        api.stats(mid),
        api.probabilidades(meio),
        api.predictions(mid),
    )


# ============================================================
# BARRA LATERAL
# ============================================================

OPÇÕES_DE_MENU = [
    "Painel de controle",
    "ðŸ“… Jogos",
    "ðŸ”Ž Analisar Jogo",
    "ðŸ" Buscar Time",
    "ðŸ“Š Estatísticas",
    "ðŸ † Classificação",
    "ðŸ'³ Uso da API",
]

# Decidimos o menu para mostrar ANTES de criar o widget, para que a barra lateral
# reflita corretamente a página atual (isto corrige o bug em que, ao clicar
# em "Analisar", o conteúdo mudou mas a seleção da barra lateral ficou desatualizada).
se st.session_state.open_analysis:
    default_menu = "ðŸ”Ž Analisar Jogo"
    st.session_state.open_analysis = False
outro:
    menu_padrão = st.session_state.current_menu ou MENU_OPTIONS[0]

menu = st.sidebar.radio(
    "MENU",
    OPÇÕES_DE_MENU,
    índice=MENU_OPTIONS.index(menu_padrão),
)
st.session_state.current_menu = menu


# ============================================================
# PAINEL
# ============================================================

if menu == "ðŸ Dashboard":

    st.markdown(
        """
        <div class="hero">
            <div class="hero-title">âš½ IA de Estatísticas de Futebol</div>
            <div class="hero-sub">Estatísticas e análise de futebol baseadas em dados da API</div>
        </div>
        "",
        unsafe_allow_html=True,
    )

    with st.spinner("Carregando jogos..."):
        hoje_correspondências = extrair_correspondências(cached_today())
        partidas_ao_vivo = extrair_partidas(ao_vivo_em_cache())
        próximas_partidas = extrair_partidas(próximas_partidas em cache())

    col_today, col_live, col_upcoming = st.columns(3)
    col_today.metric("ðŸ“… Jogos", len(today_matches))
    col_live.metric("ðŸ”´ Ao vivo", len(live_matches))
    col_upcoming.metric("â Próximos", len(upcoming_matches))

    section_title("ðŸ”¥ Jogos de hoje")

    se não houver partidas hoje:
        st.warning("Nenhum jogo encontrado.")
    outro:
        para a partida em today_matches:
            render_match_card(match, key_prefix="dash")


# ============================================================
# JOGOS
# ============================================================

menu elif == "ðŸ“… Jogos":

    st.title("ðŸ“… Jogos por dados")

    selected_date = st.date_input("Selecionar data", value=date.today())

    if st.button("ðŸ”Ž CARREGAR JOGOS", use_container_width=True):
        string_da_data = data_selecionada.strftime("%Y-%m-%d")

        with st.spinner("Buscando jogos..."):
            resposta = correspondências_em_cache_por_data(string_de_data)

        st.session_state.date_matches = extract_matches(response)
        st.session_state.date_response = resposta

    correspondências = st.session_state.get("date_matches")

    se matches não for None:
        se não houver correspondência:
            st.warning("Nenhum jogo encontrado para esses dados.")
            with st.expander("ðŸ”§ Resposta da API"):
                st.json(st.session_state.get("date_response", {}))
        outro:
            st.success(f"âš½ {len(matches)} jogos encontrados.")
            para partida em partidas:
                render_match_card(match, key_prefix="date")


# ============================================================
# ANÃ LISE
# ============================================================

menu elif == "ðŸ”Ž Analisar Jogo":

    st.title("ðŸ”Ž Análise Inteligente")

    selected_id = st.session_state.get("selected_match")
    selected_match = st.session_state.get("selected_match_data") or {}

    se não selected_id:
        st.info("Escolha um jogo primeiro.")
        st.stop()

    casa = nome_da_equipe(objeto_da_equipe(partida_selecionada, "casa"))
    fora = nome_do_time(objeto_do_time(partida_selecionada, "fora"))
    hs, aws = pontuação(partida_selecionada)

    st.markdown(
        f"""
        <div class="hero">
            <div style="text-align:center; color:#60a5fa; font-size:14px;">
                ðŸ † {league_name(selected_match)}
            </div>
            <div style="text-align:center; color:#8190a4; margin-top:5px;">
                {fmt_date(selected_match.get("match_date"))}
            </div>
            <br>
            <div style="text-align:center; color:white; font-size:24px; font-weight:800;">
                ðŸ {home}
            </div>
            <div style="text-align:center; color:white; font-size:34px; font-weight:900; margin:10px;">
                {hs} - {aws}
            </div>
            <div style="text-align:center; color:white; font-size:24px; font-weight:800;">
                âœˆï¸ {fora}
            </div>
        </div>
        "",
        unsafe_allow_html=True,
    )

    st.caption(f"ID da partida: {selected_id}")

    with st.spinner("ðŸ§ A IA está analisando os dados..."):
        tentar:
            resposta_de_detalhes, resposta_estatísticas, resposta_probabilidades, resposta_previsões = (
                cached_match_bundle(selected_id)
            )
        exceto Exception como exc:
            st.error(f"â Œ Erro ao obter dados da API: {exc}")
            st.stop()

    análise = analisar_partida(
        respostas_previsões,
        probabilidades_resposta,
        resposta_estatísticas,
    )

    # --- Melhor mercado -----------------------------------------------
    section_title("ðŸ§ Melhor oportunidade")
    a1, a2 = st.columns(2)

    com a1:
        st.markdown(
            f"""
            <div class="ai-card">
                <div class="ai-title">ðŸŽ¯ MELHOR MERCADO</div>
                <div class="ai-value">{analysis["best_market"]}</div>
            </div>
            "",
            unsafe_allow_html=True,
        )

    com a2:
        st.markdown(
            f"""
            <div class="ai-card">
                <div class="ai-title">ðŸ”¥ CONFIANÃ‡A</div>
                <div class="ai-value">{pct(analysis["best_confidence"])}</div>
                <div>{analysis["confidence_label"]}</div>
            </div>
            "",
            unsafe_allow_html=True,
        )

    # --- Resultado -------------------------------------------------------
    seção_title("ðŸ † Resultado")
    r1, r2, r3 = st.columns(3)
    r1.metric(f"ðŸ {home}", pct(analysis["winner"]["home"]))
    r2.metric("ðŸ¤ Empate", pct(analysis["winner"]["draw"]))
    r3.metric(f"âœˆï¸ {fora}", pct(analysis["winner"]["fora"]))

    # --- Gols ------------------------------------------------------------------------
    section_title("âš½ Gols")
    metas = análise["metas"]
    coluna_meta = st.colunas(5)
    rótulos_meta = ["Mais de 0,5", "Mais de 1,5", "Mais de 2,5", "Mais de 3,5", "Mais de 4,5"]
    goal_keys = ["over_0_5", "over_1_5", "over_2_5", "over_3_5", "over_4_5"]
    para col, label, gkey em zip(goal_cols, goal_labels, goal_keys):
        col.metric(rótulo, pct(metas[gkey]))

    # --- BTTS --------------------------------------------------------------
    section_title("âš½ Ambas Marcam")
    st.metric("BTTS — SIM", pct(analysis["btts"]))

    # --- Escanteios ----------------------------------------------------
    section_title("ðŸš© Escanteios")
    cantos = análise["cantos"]
    co1, co2, co3, co4 = st.columns(4)
    co1.metric("Potencial", pct(corners["potential"]))
    co2.metric("Acima de 8,5", pct(corners["acima_8_5"]))
    co3.metric("Acima de 9,5", pct(corners["acima_de_9_5"]))
    co4.metric("Acima de 10,5", pct(corners["acima_de_10_5"]))

    # --- xG ------------------------------------------------------------
    section_title("ðŸ“ˆ xG pré-jogo")
    xg = análise["xg"]
    x1, x2, x3 = st.columns(3)
    x1.metric(home, xg["home"] if xg["home"] is not None else "--")
    x2.metric(away, xg["away"] if xg["away"] is not None else "—")
    x3.metric("Total", xg["total"] if xg["total"] is not None else "--")

    # --- Palpites ------------------------------------------------------------
    section_title("ðŸŽ¯ Palpites sugeridos")
    escolhas = análise["escolhas"]

    se escolher:
        Para nome e valor nas escolhas:
            st.success(f"{name} • {pct(value)}")
    outro:
        st.info("Não há mercados com confiança suficiente para sugerir um palpite.")

    # --- Confiança geral -------------------------------------------------
    section_title("ðŸ”¥ Confiança geral")
    confiança = análise["confiança"]

    se a confiança não for nula:
        st.progress(min(max(int(confiança), 0), 100))
        st.write(f"**{confiança:.1f}%** — {análise['confidence_label']}")
    outro:
        st.info("Dados insuficientes.")

    # --- Depuração -------------------------------------------------------------
    with st.expander("ðŸ”§ Dados recebidos da API"):
        st.write("### Partida")
        st.json(resposta_detalhe)
        st.write("### Estatísticas")
        st.json(stats_response)
        st.write("### Probabilidades")
        st.json(probabilidades_resposta)
        st.write("### Previsões")
        st.json(resposta_de_previsões)


# ============================================================
# HORA DO BUSCAR
# ============================================================

elif menu == "ðŸ” Buscar Hora":

    st.title("ðŸ” Buscar Hora")

    query = st.text_input("Digite o nome do tempo", placeholder="Barcelona")

    if st.button("ðŸ”Ž PESQUISAR", use_container_width=True):
        with st.spinner("Pesquisando..."):
            resposta = api.search(consulta, search_type="teams")

        dados = dados_de(resposta)
        resultados = dados.get("resultados", {})
        equipes = resultados.get("equipes", [])

        se não forem equipes:
            st.warning("Hora Nenhum encontrada.")

        para equipe em equipes:
            nome = equipe.get("nome_da_equipe", "?")
            país = equipe.get("país", "?")
            tid = equipe.get("team_id")

            st.markdown(
                f"""
                <div class="match-card">
                    <div class="team">âš½ {name†div>
                    <div class="match-date">ðŸŒ {country} • ID {tid div>
                </div>
                "",
                unsafe_allow_html=True,
            )


# ============================================================
# ESTÁTICAS
# ============================================================

menu elif == "ðŸ“Š Estatísticas":

    st.title("ðŸ“Š Estatísticas do Tempo")
    st.caption("Não sabe o ID? Use primeiro 'ðŸ” Buscar Hora' para encontrar o ID pelo nome.")

    team_id = st.number_input("ID do time", min_value=1, value=77)

    if st.button("ðŸ“Š CARREGAR", use_container_width=True):
        with st.spinner("Carregando estatísticas..."):
            resposta = api.team_stats(int(team_id))
        st.json(resposta)


# ============================================================
# CLASSIFICAÇÃO
# ============================================================

menu elif == "ðŸ † Classificação":

    st.title("ðŸ † Classificaçã§Ã£o")

    league_id = st.number_input("ID da liga", min_value=1, value=10)

    if st.button("ðŸ † CARREGAR", use_container_width=True):
        with st.spinner("Carregando classificação..."):
            resposta = api.standings(int(league_id))
        st.json(resposta)


# ============================================================
# USO
# ============================================================

menu elif == "ðŸ'³ Uso da API":

    st.title("ðŸ'³ Uso da API")
    st.json(api.usage())
