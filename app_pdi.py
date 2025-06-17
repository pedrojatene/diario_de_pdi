import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from google.oauth2.service_account import Credentials
import vl_convert as vlc

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor


from sheets_api import get_dropdown_options, append_row_to_sheet
from datetime import date
from datetime import datetime
import altair as alt
alt.renderers.set_embed_options(renderer="svg", actions=False)

from altair_saver import save as altair_save
from PIL import Image
import tempfile
import os

from altair_saver import save as altair_save
import altair as alt

def save_altair_chart_as_png(chart, filename="chart.png"):
    chart_dict = chart.to_dict()
    png_data = vlc.vegalite_to_png(chart_dict)
    with open(filename, "wb") as f:
        f.write(png_data)
    return filename

# FUNÇÃO PARA GERAR RELATÓRIO GERAL
def generate_basic_summary_report(start_date, end_date):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    # Page dimensions
    width, height = A4

    # --- Draw logos and title ---
    left_logo_path = os.path.join(os.path.dirname(__file__), "SPFClogo copy.png")
    right_logo_path = os.path.join(os.path.dirname(__file__), "CFA Logo copy.png")  # replace with your actual filename

    logo_width = 60
    rightlogo_width = 50
    logo_height = 60
    margin_left = 40
    margin_right = 30
    top_y = height - 40

    if os.path.exists(left_logo_path):
        left_logo = ImageReader(left_logo_path)
        c.drawImage(left_logo, margin_left, top_y - logo_height, width=logo_width, height=logo_height, mask='auto')

    if os.path.exists(right_logo_path):
        right_logo = ImageReader(right_logo_path)
        right_x = width - margin_right - logo_width
        c.drawImage(right_logo, right_x, top_y - logo_height, width=rightlogo_width, height=logo_height, mask='auto')

    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(HexColor("#E60000"))  # Red color for the title
    c.drawCentredString(width / 2, top_y - 20, "Resumo Geral")

    # Section Name
    c.setFillColor(HexColor("#000000"))  # Reset to black for the athlete name
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 80, "Relatório de Atividades Individuais")

    # Date Range
    date_fmt = "%d/%m/%Y"
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, height - 100, f"{start_date.strftime(date_fmt)} até {end_date.strftime(date_fmt)}")

    # Finalize PDF
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


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
                    .mark_bar(color="#E60000", opacity=0.95, size=24)
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
                    .properties(title="Número de Sessões por Dia \u2014 Média: {:.1f}".format(avg_value),
                        height=400)
                )

                st.altair_chart(chart, use_container_width=True)

            else:
                st.info("Nenhum dado encontrado na planilha.")

            if st.button("📄 Gerar Relatório", key="relatorio_summary"):
                pdf_buffer = generate_basic_summary_report(min_date, max_date)
                st.download_button(
                    label="📥 Download",
                    data=pdf_buffer,
                    file_name=f"Relatório PDI_{max_date}.pdf",
                    mime="application/pdf"
                    )

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
                    f"📄 Sessões de {atleta_escolhido} "
                    f"({periodo[0].strftime('%d/%m/%Y')} – {periodo[1].strftime('%d/%m/%Y')})"
                )
                st.markdown("")
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
                               .mark_bar(size=40, cornerRadiusTopLeft=5, cornerRadiusTopRight=5, opacity=0.95, color="#FF4B4B")
                               .encode(
                                   x=alt.X("Objetivo:N",
                                           sort="-y",
                                           title=None,
                                           axis=alt.Axis(labelAngle=0, grid=False, domain=False)),
                                   y=alt.Y("Sessões:Q",
                                           title=None,
                                           axis=alt.Axis(grid=False, labels=False, domain=False)),
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
                            height=400, width="container",
                            title="Sessões por Objetivo"
                        ).configure_axis(
                            grid=False,
                            domain=False,
                            ticks=False
                        ).configure_view(
                            stroke=None
                        ).configure_title(
                            fontSize=16
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
                            base.mark_arc(innerRadius=40, outerRadius=130, opacity=0.9)
                                .encode(
                                    tooltip=[
                                        alt.Tooltip("Objetivo:N", title="Objetivo"),
                                        alt.Tooltip("Sessões:Q", title="Sessões"),
                                        alt.Tooltip("Percent:Q", title="%", format=".0%")
                                    ]
                                )
                        )

                        # --- text labels inside slices ----------------------------------
                        labels = (
                            base.mark_text(radius=150, size=14, color="000000")      # label layer
                                .encode(text=alt.Text("Percent:Q", format=".0%"))
                        )

                        pie_chart = (pie + labels).properties(
                            width=300, height=400,
                            title="Composição"
                        )
                        st.altair_chart(pie_chart, use_container_width=True)

                    # --- Stacked Bar Chart: Distribuição por Objetivo e Sessão ---
                    st.markdown("")
                    st.markdown("**Detalhamento das Sessões por Objetivo**")

                    stacked_data = (
                        df_player.groupby(["Objetivo", "Sessão"])
                                 .size()
                                 .reset_index(name="Contagem")
                    )

                    stacked_bar = (
                        alt.Chart(stacked_data)
                           .mark_bar(size=60, cornerRadiusTopLeft=5, cornerRadiusTopRight=5, opacity=0.95)
                           .encode(
                               x=alt.X("Objetivo:N", sort="-y", title=None, axis=alt.Axis(grid=False, labelAngle=0)),
                               y=alt.Y("Contagem:Q", stack="zero", title=None, axis=alt.Axis(grid=False, labels=False, ticks=False, domain=False)),
                               color=alt.Color("Sessão:N", title=None),
                               tooltip=["Objetivo:N", "Sessão:N", "Contagem:Q"]
                           )
                           .properties(height=400, width="container")
                    )

                    labels = (
                        alt.Chart(stacked_data)
                            .mark_text(size=13, dy=-2, color="black", baseline="bottom")
                            .encode(
                                x=alt.X("Objetivo:N", sort="-y"),
                                y=alt.Y("Contagem:Q", stack="zero"),
                                detail="Sessão:N",
                                text=alt.Text("Contagem:Q"),
                                color=alt.Color("Sessão:N")
                            )
                    )

                    stacked_bar_with_labels = (stacked_bar + labels).configure_axis(grid=False)
                    st.altair_chart(stacked_bar_with_labels, use_container_width=True)

                st.markdown("")
                st.markdown("**Todas as Sessões**")
                st.dataframe(df_player, use_container_width=True, height=dyn_h)

                # FUNÇÃO PARA GERAR RELATÓRIO BÁSICO POR ATLETA
                def generate_basic_player_report(athlete_name, start_date, end_date, df_player, bar_chart, pie_chart):
                    buffer = BytesIO()
                    c = canvas.Canvas(buffer, pagesize=A4)

                    # Page dimensions
                    width, height = A4

                    # --- Draw logos and title ---
                    left_logo_path = os.path.join(os.path.dirname(__file__), "SPFClogo copy.png")
                    right_logo_path = os.path.join(os.path.dirname(__file__), "CFA Logo copy.png")  # replace with your actual filename

                    logo_width = 60
                    rightlogo_width = 50
                    logo_height = 60
                    margin_left = 40
                    margin_right = 30
                    top_y = height - 40

                    if os.path.exists(left_logo_path):
                        left_logo = ImageReader(left_logo_path)
                        c.drawImage(left_logo, margin_left, top_y - logo_height, width=logo_width, height=logo_height, mask='auto')

                    if os.path.exists(right_logo_path):
                        right_logo = ImageReader(right_logo_path)
                        right_x = width - margin_right - logo_width
                        c.drawImage(right_logo, right_x, top_y - logo_height, width=rightlogo_width, height=logo_height, mask='auto')

                    # Athlete Name
                    c.setFont("Helvetica-Bold", 18)
                    c.setFillColor(HexColor("#E60000"))  # Red color for the title
                    c.drawCentredString(width / 2, top_y - 20, f"{athlete_name}")

                    c.setFillColor(HexColor("#000000"))  # Reset to black for the athlete name
                    c.setFont("Helvetica-Bold", 16)
                    c.drawCentredString(width / 2, height - 80, "Relatório de Atividades Individuais")

                    # Date Range
                    date_fmt = "%d/%m/%Y"
                    c.setFont("Helvetica", 14)
                    c.drawCentredString(width / 2, height - 100, f"{start_date.strftime(date_fmt)} até {end_date.strftime(date_fmt)}")

                    # Space for data insights
                    y_position = height - 150
                    line_spacing = 22

                    # Left Column
                    x_left = 100
                    # Right Column
                    x_right = width / 2 + 25
                    y_start = y_position

                    # Resumo
                    c.setFont("Helvetica-Bold", 12)
                    c.drawString(x_left, y_position, "Resumo")
                    y_position -= line_spacing

                    # Dias de Treino
                    unique_dates = df_player["Data"].nunique()
                    c.setFont("Helvetica", 12)
                    c.drawString(x_left, y_position, "Dias de Treino no Período:")
                    c.setFont("Helvetica-Bold", 12)
                    c.drawString(x_left + 150, y_position, f"{unique_dates:02d}")

                    # Total de Sessões
                    total_sessions = len(df_player)
                    c.setFont("Helvetica", 12)
                    c.drawString(x_right, y_position, "Total de Sessões no Período:")
                    c.setFont("Helvetica-Bold", 12)
                    c.drawString(x_right + 166, y_position, f"{total_sessions:02d}")
                    y_position -= line_spacing

                    # Dias de Folga
                    all_dates = pd.date_range(start=start_date, end=end_date).date
                    registered_dates = set(df_player["Data"])
                    missing_dates = [d for d in all_dates if d not in registered_dates]
                    c.setFont("Helvetica", 12)
                    c.drawString(x_left, y_position, "Dias de Folga no Período:")
                    c.setFont("Helvetica-Bold", 12)
                    c.drawString(x_left + 150, y_position, f"{len(missing_dates):02d}")

                    # Média de sessões
                    media_sessoes = total_sessions / (unique_dates + len(missing_dates)) if (unique_dates + len(missing_dates)) > 0 else 0
                    c.setFont("Helvetica", 12)
                    c.drawString(x_right, y_position, "Média de Sessões por Dia:")
                    c.setFont("Helvetica-Bold", 12)
                    c.drawString(x_right + 156, y_position, f"{media_sessoes:.2f}")

                    # --- Convert charts to images using vl_convert ---
                    bar_chart_dict = bar_chart.to_dict()
                    bar_png_data = vlc.vegalite_to_png(bar_chart_dict)
                    bar_img = ImageReader(BytesIO(bar_png_data))

                    pie_chart_dict = pie_chart.to_dict()
                    pie_png_data = vlc.vegalite_to_png(pie_chart_dict)
                    pie_img = ImageReader(BytesIO(pie_png_data))

                    # TAMANHO DOS GRÁFICOS
                    bar_chart_width = 300
                    bar_chart_height = 300
                    pie_chart_width = 207
                    pie_chart_height = 270

                    bar_y = 320
                    pie_y = bar_y - 300

                    c.drawImage(bar_img, 40, bar_y, width=bar_chart_width, height=bar_chart_height, mask='auto')
                    c.drawImage(pie_img, 60, pie_y, width=pie_chart_width, height=pie_chart_height, mask='auto')

                    # Finalize PDF
                    c.showPage()
                    c.save()
                    buffer.seek(0)
                    return buffer

                st.markdown("---")
                
                if st.button("📄 Gerar Relatório", key="relatorio_player"):
                    pdf_buffer = generate_basic_player_report(
                        atleta_escolhido, periodo[0], periodo[1],
                        df_player, bar_chart, pie_chart)
                    st.download_button(
                        label="📥 Download",
                        data=pdf_buffer,
                        file_name=f"Relatório PDI_{atleta_escolhido.lower().replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )
             
        with tab3:
            st.subheader("🎯 Dados por Objetivo")
            st.write("...")
