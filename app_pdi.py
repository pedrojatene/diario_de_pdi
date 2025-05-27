import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from google.oauth2.service_account import Credentials

from sheets_api import get_dropdown_options, append_row_to_sheet
from datetime import date
from datetime import datetime
import altair as alt

st.set_page_config(
    page_title="Diário de PDI",
    page_icon="📕",  # You can use any emoji or a custom image URL
    layout="wide"    # Optional: makes the layout use full width
)

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

name, auth_status, username = authenticator.login(
    location='main',
    fields={
        'Form name': 'Login',
        'Username': 'Usuário',
        'Password': 'Senha',
        'Login': 'Entrar'
    }
)

if auth_status:
    authenticator.logout('Logout', 'sidebar')
    st.sidebar.write(f"*Bem-vindo, {name}*")

    page = st.sidebar.radio("Navegar para:", ["Registrar Treino", "Visualizar Dados"])
    if page == "Registrar Treino":


        ####🔽 your main app starts here


        # Apply custom CSS for Helvetica Neue font
        st.markdown("""
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Helvetica+Neue&display=swap');

            html, body, [class*="css"] {
                font-family: 'Helvetica Neue', sans-serif;
            }

            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
                padding-left: 2rem;
                padding-right: 2rem;
                max-width: none;
            }

            h1 {
                text-align: left;
                width: 100%;
            }
            </style>
            """, unsafe_allow_html=True)

        st.header("🗓️ Registro de Atividades Individuais")

        # Load dropdown options
        players, goals, sessions = get_dropdown_options()

        # Player Name
        player = st.selectbox("Nome do Atleta", options=players + ["Adicionar novo..."])
        if player == "Adicionar novo...":
            col1, col2, col3 = st.columns([1, 1, 2])
            with col2:
                st.markdown(
                    """
                    <div style='display: flex; align-items: center; justify-content: flex-end; height: 38px;'>
                        <span style='color: red;'>Insira o novo Atleta</span>
                    </div>
                    """, unsafe_allow_html=True)
            with col3:
                player = st.text_input("", key="new_player")

        # Training Goal
        goal = st.selectbox("Objetivo do Treino", options=goals + ["Adicionar novo..."])
        if goal == "Adicionar novo...":
            col1, col2, col3 = st.columns([1, 1, 2])
            with col2:
                st.markdown(
                    """
                    <div style='display: flex; align-items: center; justify-content: flex-end; height: 38px;'>
                        <span style='color: red;'>Insira o novo Objetivo</span>
                    </div>
                    """, unsafe_allow_html=True)
            with col3:
                goal = st.text_input("", key="new_goal")

        # Session Type
        session_type = st.selectbox("Tipo de Sessão", options=sessions + ["Adicionar novo..."])
        if session_type == "Adicionar novo...":
            col1, col2, col3 = st.columns([1, 1, 2])
            with col2:
                st.markdown(
                    """
                    <div style='display: flex; align-items: center; justify-content: flex-end; height: 38px;'>
                        <span style='color: red;'>Insira o novo Tipo de Sessão</span>
                    </div>
                    """, unsafe_allow_html=True)
            with col3:
                session_type = st.text_input("", key="new_session_type")

        # Data e submissão
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1]) 

        with col1:
            session_date = st.date_input("Data", value=date.today())

        with col4:
            st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)  # vertical spacer
            submit = st.button("Registrar Treino")

        if submit:
            if all([player, goal, session_type, session_date]):
        # ✅ format as DD/MM/YYYY so Sheets (Brazilian locale) recognises the date
                locale_date = session_date.strftime("%d/%m/%Y")
                append_row_to_sheet(player, goal, session_type, locale_date)
                st.success("Treino registrado com sucesso!")
            else:
                st.error("Preencha todos os campos.")

    elif auth_status is False:
        st.error("Usuário ou senha incorretos")
    elif auth_status is None:
        st.warning("Insira seu login e senha para continuar")

    # Visualizar Registros
    elif page == "Visualizar Dados":
        st.header("📊 Visualização de Dados")
        
        tab1, tab2, tab3 = st.tabs(["Todos os Dados", "Por Atleta", "Por Objetivo"])

        with tab1:
                        # --- constants for date limits ---
            from datetime import date, timedelta
            min_date = date(2025, 5, 5)
            max_date = date.today()

            # --- load sheet into DataFrame ---
            creds = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
            client = gspread.authorize(creds)
            ws = client.open_by_url(st.secrets["gcp_service_account"]["private_gsheets_url"]).sheet1
            records = ws.get_all_records()
            df = pd.DataFrame(records)

            # remove legacy ID column if present
            if "ID" in df.columns:
                df = df.drop(columns=["ID"])

            if not df.empty:
                # --- harmonise column names -------------------------------------------------
                rename_map = {
                    "playerName": "Nome",
                    "trainingGoal": "Objetivo",
                    "sessionType": "Sessão",
                    "date": "Data"  # in case the header is lowercase
                }
                df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

                # --- parse date column -------------------------------------------------------
                df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y", errors="coerce")
                df = df.dropna(subset=["Data"])
                df["Data"] = df["Data"].dt.date
                df = df.sort_values(by="Data", ascending=False)

                # --- add weekday name --------------------------------------------------------
                dias_semana = {
                    0: "Segunda", 1: "Terça", 2: "Quarta", 3: "Quinta",
                    4: "Sexta", 5: "Sábado", 6: "Domingo"
                }
                df["Dia da Semana"] = df["Data"].apply(lambda x: dias_semana[x.weekday()])

                
            # --- 📊 SUMMARY ANTES DA LISTA DINÂMICA -------------------------------------------
                # df_clean contém todos os dados de min_date até hoje (sem filtros de atleta/objetivo)
                df_clean = df.copy()
                summary = (
                    df_clean.groupby(["Nome", "Objetivo"]).size().unstack(fill_value=0)
                )
                summary["Total"] = summary.sum(axis=1)
                grand_total = summary.sum(axis=0).to_frame().T
                grand_total.index = ["TOTAL"]
                summary = pd.concat([summary, grand_total])

                st.subheader("📌 Resumo Geral ({} a {})".format(min_date.strftime('%d/%m/%Y'),
                    max_date.strftime('%d/%m/%Y')))

                numeric_cols = summary.select_dtypes("number").columns
                idx = pd.IndexSlice

                # Apply gradient per column, exclude the TOTAL row
                def highlight_grand_total(row):
                    return ['background-color: #D9D9D9' if row.name == 'TOTAL' else '' for _ in row]

                styled_summary = (
                    summary.style
                           .background_gradient(cmap="Reds", subset=idx[summary.index != "TOTAL", numeric_cols], axis=0)
                           .apply(highlight_grand_total, axis=1)
                )

                row_px = 36
                header_px = 56
                buffer_px = 12
                dyn_height = header_px + row_px * (len(summary)+1) + buffer_px

                st.dataframe(styled_summary, use_container_width=True, height=dyn_height)


                # LISTA DINÂMICA
                # --- dynamic filter choices --------------------------------------------------
                atletas = sorted(df["Nome"].unique())
                objetivos = sorted(df["Objetivo"].unique())
                sessoes = sorted(df["Sessão"].unique())

                st.subheader("📋 Lista Dinâmica")

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    atleta_filter = st.selectbox("Filtrar por Atleta", ["Todos"] + atletas)
                with col2:
                    objetivo_filter = st.selectbox("Filtrar por Objetivo", ["Todos"] + objetivos)
                with col3:
                    sessao_filter = st.selectbox("Filtrar por Sessão", ["Todos"] + sessoes)
                with col4:
                    date_range = st.date_input(
                        "Período",
                        value=(min_date, max_date),
                        min_value=min_date,
                        max_value=max_date,
                    )

                # --- apply filters ------------------------------------------------------------
                if atleta_filter != "Todos":
                    df = df[df["Nome"] == atleta_filter]
                if objetivo_filter != "Todos":
                    df = df[df["Objetivo"] == objetivo_filter]
                if sessao_filter != "Todos":
                    df = df[df["Sessão"] == sessao_filter]
                if date_range and all(date_range):
                    df = df[(df["Data"] >= date_range[0]) & (df["Data"] <= date_range[1])]

                # --- make Streamlit's index a descending counter -----------------------------
                df = df.reset_index(drop=True)
                df.index = range(len(df), 0, -1)  # index column will show N → 1

                # --- column order: Nome, Data first -----------------------------------------
                cols = df.columns.tolist()
                priority = [c for c in ["Nome", "Data"] if c in cols]
                remaining = [c for c in cols if c not in priority]
                df = df[priority + remaining]

                st.dataframe(df, use_container_width=True, height=400)

                # --- Gráfico de sessões por dia ------------------------------------------
                # Conta quantas linhas restam por data
                daily_counts = (
                    df.groupby("Data")
                    .agg(Sessões=("Nome","size"),
                         Atletas=("Nome", lambda x: ", ".join(sorted(x.unique()))))
                    .reset_index()
                    .sort_values("Data")          # datas em ordem cronológica
                )

                bar = (
                    alt.Chart(daily_counts)
                    .mark_bar(color="#D30000", opacity=0.95, size=24)
                    .encode(
                        x=alt.X("Data:T", title="Data"),
                        y=alt.Y("Sessões:Q", title=None),
                        tooltip=[alt.Tooltip("Data:T", title="Data"),
                                 alt.Tooltip("Sessões:Q", title="Sessões"),
                                 alt.Tooltip("Atletas:N", title="Atletas")]
                    )
                )

                # --- average line -----------------------------------------------------------
                avg_value = float(daily_counts["Sessões"].mean())
                avg_df = pd.DataFrame({"MÉDIA": [avg_value]})
                avg_line = (
                    alt.Chart(avg_df)
                       .mark_rule(color="#000000", opacity=0.9, size=2, strokeDash=[4,4])
                       .encode(y="MÉDIA:Q")
                )

                chart = (
                    (bar + avg_line)
                    .properties(title="Número de Sessões por Dia \u2014 Média: {:.1f}".format(avg_value))
                )

                st.altair_chart(chart, use_container_width=True)

            else:
                st.info("Nenhum dado encontrado na planilha.")


        with tab2:
            # --- pick athlete & date‑range side by side -----------------
            colA, colB = st.columns(2)

            with colA:
                atleta_escolhido = st.selectbox(
                    "Selecione o atleta",
                    sorted(df_clean["Nome"].unique())
                )

            with colB:
                periodo = st.date_input(
                    "Período",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                    key="periodo_atleta"
                )

            if atleta_escolhido and periodo and all(periodo):

                # --- filter by athlete & chosen dates -------------------
                df_player = df_clean[
                    (df_clean["Nome"] == atleta_escolhido) &
                    (df_clean["Data"] >= periodo[0]) &
                    (df_clean["Data"] <= periodo[1])
                ].copy().sort_values("Data", ascending=False)

                # --- reorder columns: Nome, Data first ------------------
                cols_p     = df_player.columns.tolist()
                priority_p = [c for c in ["Nome", "Data"] if c in cols_p]
                df_player  = df_player[priority_p + [c for c in cols_p if c not in priority_p]]

                # --- dynamic height so no scroll ------------------------
                row_px    = 30
                header_px = 48
                buffer_px = 12
                dyn_h     = header_px + row_px * len(df_player) + buffer_px

                st.subheader(
                    f"📄 Registros de {atleta_escolhido} "
                    f"({periodo[0].strftime('%d/%m/%Y')} – {periodo[1].strftime('%d/%m/%Y')})"
                )

                # --- charts side‑by‑side: sessões por objetivo ----------------------
                if not df_player.empty:
                    goal_counts = (
                        df_player.groupby("Objetivo", dropna=False)
                                 .size()
                                 .reset_index(name="Sessões")
                                 .sort_values("Sessões", ascending=False)
                    )

                    colC, colD = st.columns(2)

                    my_palette = alt.Scale(range=[
                        "#E60000", "#CCCCCC", "#656565", "#151515", "#1E90FF",
                        "#8A2BE2", "#FF69B4", "#FF1493", "#00CED1", "#20B2AA"
                    ])

                    color_encoding = alt.Color("Objetivo:N", scale=my_palette, legend=None)

                    with colC:
                        bar = (
                            alt.Chart(goal_counts)
                               .mark_bar(size=40, opacity=0.9, color="#FF4B4B")
                               .encode(
                                   x=alt.X("Objetivo:N",
                                           sort="-y",
                                           title=None,
                                           axis=alt.Axis(labelAngle=0, grid=False)),
                                   y=alt.Y("Sessões:Q",
                                           title=None,
                                           axis=alt.Axis(grid=False)),
                                   color=color_encoding,
                                   tooltip=["Objetivo:N", "Sessões:Q"]
                               )
                        )

                        labels = (
                            alt.Chart(goal_counts)
                               .mark_text(dy=-9, color="#333", fontSize=13)
                               .encode(
                                   x=alt.X("Objetivo:N", sort="-y"),
                                   y="Sessões:Q",
                                   text="Sessões:Q"
                               )
                        )

                        bar_chart = (bar + labels).properties(
                            height=350, width="container",
                            title="Sessões por Objetivo (bar)"
                        )
                        st.altair_chart(bar_chart, use_container_width=True)

                    # ---- prepare percentages in pandas ---------------------------------
                    goal_counts["Percent"] = (
                        goal_counts["Sessões"] / goal_counts["Sessões"].sum()
                    )

                    with colD:
                        base = (
                            alt.Chart(goal_counts)
                            .encode(
                                theta=alt.Theta("Sessões:Q", stack=True),  # cumulative angles
                                color=color_encoding
                            )
                        )

                        # Actual pie slices
                        pie = (
                            base.mark_arc(innerRadius=40, outerRadius=120, opacity=0.9)
                                .encode(
                                    tooltip=[
                                        alt.Tooltip("Objetivo:N", title="Objetivo"),
                                        alt.Tooltip("Sessões:Q", title="Sessões"),
                                        alt.Tooltip("Percent:Q", title="%", format=".0%")
                                    ]
                                )
                        )

                        # Text labels (white) positioned inside each slice
                        labels = (
                            base.mark_text(radius=80, size=14, color="white")
                                .encode(
                                    text=alt.Text("Percent:Q", format=".0%")
                                )
                        )

                        pie_chart = (pie + labels).properties(
                            width=300, height=300,
                            title="Sessões por Objetivo (pie)"
                        )

                        st.altair_chart(pie_chart, use_container_width=True)

                st.dataframe(df_player, use_container_width=True, height=dyn_h)

        with tab3:
            st.subheader("🎯 Dados por Objetivo")
            st.write("Em breve: filtros, tabelas e gráficos personalizados por atleta.")
