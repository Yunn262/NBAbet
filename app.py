import streamlit as st
from datetime import date
import pandas as pd

from sportradar_api import (
    get_daily_schedule,
    extract_games,
    get_game_summary
)

from prediction_engine import (
    calculate_prediction,
    choose_best_prediction
)

from ticket import gerar_bilhete


# =========================================================
# CONFIGURAÇÃO
# =========================================================

st.set_page_config(
    page_title="BasketballAI Predictor",
    page_icon="🏀",
    layout="wide"
)


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
<style>

.main {
    background-color: #05070a;
}

.block-container {
    padding-top: 1rem;
}

.title {
    font-size: 42px;
    font-weight: 800;
}

.subtitle {
    color: #9ca3af;
}

.game-card {

    background: linear-gradient(
        145deg,
        #111827,
        #070b12
    );

    border: 1px solid #263244;

    border-radius: 18px;

    padding: 20px;

    margin-bottom: 18px;

    box-shadow:
        0 10px 30px
        rgba(0,0,0,.25);
}

.team {

    font-size: 22px;

    font-weight: 700;

    text-align: center;
}

.vs {

    text-align: center;

    font-size: 18px;

    color: #9ca3af;
}

.prediction {

    background: #0b1220;

    border-radius: 14px;

    padding: 15px;

    margin-top: 15px;

    border: 1px solid #273449;
}

.confidence {

    font-size: 30px;

    font-weight: 800;
}

.market {

    font-size: 20px;

    font-weight: 700;
}

</style>
""",
    unsafe_allow_html=True
)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="title">🏀 BasketballAI Predictor</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Análise estatística de jogos de basquete'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("⚙️ Configurações")

access_level = st.sidebar.selectbox(
    "Nível da API",
    [
        "trial",
        "production"
    ]
)

language = st.sidebar.selectbox(
    "Idioma",
    [
        "br",
        "en"
    ]
)

selected_date = st.sidebar.date_input(
    "📅 Data",
    value=date.today()
)

st.sidebar.divider()

st.sidebar.info(
    "A chave da Sportradar deve estar "
    "configurada nos Secrets do Streamlit."
)


# =========================================================
# ABAS
# =========================================================

tab1, tab2, tab3 = st.tabs(
    [
        "🏀 Jogos",
        "🔥 Bilhete do Dia",
        "📊 Estatísticas"
    ]
)


# =========================================================
# CARREGAR JOGOS
# =========================================================

with tab1:

    if st.button(
        "🔄 CARREGAR JOGOS",
        use_container_width=True
    ):

        with st.spinner(
            "Consultando Sportradar..."
        ):

            data = get_daily_schedule(
                selected_date,
                access_level,
                language
            )

        if "error" in data:

            st.error(
                f"Erro da API: "
                f"{data.get('error')}"
            )

            if data.get("details"):
                st.code(
                    data["details"]
                )

            st.stop()

        games = extract_games(data)

        if not games:

            st.warning(
                "Nenhum jogo encontrado para esta data."
            )

            st.stop()

        st.session_state["games"] = games

        st.success(
            f"{len(games)} jogos encontrados."
        )


    games = st.session_state.get(
        "games",
        []
    )


    # =====================================================
    # JOGOS
    # =====================================================

    for game in games:

        prediction = calculate_prediction()

        best = choose_best_prediction(
            prediction
        )

        game["prediction"] = {
            "data": prediction,
            "best": best
        }

        scheduled = game.get(
            "scheduled",
            ""
        )

        st.markdown(
            '<div class="game-card">',
            unsafe_allow_html=True
        )

        col1, col2, col3 = st.columns(
            [4, 1, 4]
        )

        with col1:

            st.markdown(
                f'<div class="team">'
                f'{game["away_name"]}'
                f'</div>',
                unsafe_allow_html=True
            )

        with col2:

            st.markdown(
                '<div class="vs">VS</div>',
                unsafe_allow_html=True
            )

        with col3:

            st.markdown(
                f'<div class="team">'
                f'{game["home_name"]}'
                f'</div>',
                unsafe_allow_html=True
            )


        st.caption(
            f"🕒 {scheduled} | "
            f"Status: {game.get('status')}"
        )


        p = prediction


        st.markdown(
            '<div class="prediction">',
            unsafe_allow_html=True
        )

        st.markdown(
            "🔥 **PALPITE PRINCIPAL**"
        )

        st.markdown(
            f'<div class="market">'
            f'{best["market"]}'
            f'</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            f'<div class="confidence">'
            f'{best["confidence"]}%'
            f'</div>',
            unsafe_allow_html=True
        )

        st.progress(
            best["confidence"] / 100
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )


        c1, c2, c3 = st.columns(3)

        with c1:

            st.metric(
                "Casa",
                f'{p["home_probability"]}%'
            )

        with c2:

            st.metric(
                "Fora",
                f'{p["away_probability"]}%'
            )

        with c3:

            st.metric(
                "Total esperado",
                p["expected_total"]
            )


        with st.expander(
            "📊 Ver análise"
        ):

            st.write(
                f"🏠 Pontos esperados "
                f"**{game['home_name']}**: "
                f"{p['expected_home']}"
            )

            st.write(
                f"🚀 Pontos esperados "
                f"**{game['away_name']}**: "
                f"{p['expected_away']}"
            )

            st.write(
                f"Over 200.5: "
                f"**{p['over_200']}%**"
            )

            st.write(
                f"Over 210.5: "
                f"**{p['over_210']}%**"
            )

            st.write(
                f"Over 220.5: "
                f"**{p['over_220']}%**"
            )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )


# =========================================================
# BILHETE
# =========================================================

with tab2:

    st.header(
        "🔥 Bilhete Inteligente"
    )

    games = st.session_state.get(
        "games",
        []
    )

    if not games:

        st.info(
            "Primeiro carregue os jogos."
        )

    else:

        for game in games:

            prediction = calculate_prediction()

            game["prediction"] = {
                "data": prediction,
                "best":
                    choose_best_prediction(
                        prediction
                    )
            }


        bilhete = gerar_bilhete(
            games,
            minimo=10
        )


        if len(bilhete) < 10:

            st.warning(
                f"A análise encontrou apenas "
                f"{len(bilhete)} seleções com "
                f"confiança suficiente."
            )

            st.caption(
                "O sistema não inventa jogos "
                "para completar o bilhete."
            )

        else:

            st.success(
                f"🎯 {len(bilhete)} seleções encontradas"
            )


        for i, item in enumerate(
            bilhete,
            1
        ):

            st.markdown(
                f"""
### {i:02d}. {item['away']} × {item['home']}

🔥 **{item['market']}**

🎯 Confiança: **{item['confidence']}%**

---
"""
            )


# =========================================================
# ESTATÍSTICAS
# =========================================================

with tab3:

    st.header(
        "📊 Estatísticas"
    )

    games = st.session_state.get(
        "games",
        []
    )

    if games:

        rows = []

        for game in games:

            p = calculate_prediction()

            rows.append({

                "Visitante":
                    game["away_name"],

                "Casa":
                    game["home_name"],

                "Casa %":
                    p["home_probability"],

                "Fora %":
                    p["away_probability"],

                "Total esperado":
                    p["expected_total"],

                "Over 200.5":
                    p["over_200"],

                "Over 210.5":
                    p["over_210"],

                "Over 220.5":
                    p["over_220"]
            })


        df = pd.DataFrame(rows)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "Carregue os jogos primeiro."
        )
