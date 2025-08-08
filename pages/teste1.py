import streamlit as st
import pandas as pd
from geopy.distance import geodesic

st.set_page_config(page_title="CTOs Próximas e Disponíveis", layout="wide")

@st.cache_data
def carregar_dados():
    df = pd.read_excel("pages/base_de_dados/base.xlsx")

    # Padronizar colunas
    df.columns = df.columns.str.lower().str.strip()

    # Criar coluna caminho_rede
    df["caminho_rede"] = (
        df["pop"].astype(str) + "_" +
        df["olt"].astype(str) + "_" +
        df["slot"].astype(str) + "_" +
        df["pon"].astype(str)
    )

    # Tratar LAT e LONG
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    # Remover coordenadas inválidas
    df = df.dropna(subset=["latitude", "longitude"])
    df = df[(df["latitude"].between(-90, 90)) & (df["longitude"].between(-180, 180))]

    return df

df = carregar_dados()

st.title("📍 Buscar CTOs Próximas e Disponíveis")

cto_invalidas = st.text_area("Insira os nomes das CTOs que **NÃO podem ser trocadas** (uma por linha):")

if st.button("🔍 Buscar CTOs Disponíveis em até 200m"):
    if not cto_invalidas.strip():
        st.warning("⚠️ Por favor, insira ao menos uma CTO inválida.")
    else:
        # Lista de CTOs inválidas em maiúsculo
        lista_ctos = [cto.strip().upper() for cto in cto_invalidas.splitlines() if cto.strip()]
        df["cto"] = df["cto"].astype(str).str.strip().str.upper()

        # Total de portas por caminho
        portas_por_caminho = df.groupby("caminho_rede")["portas"].sum().to_dict()

        # CTOs inválidas (input)
        df_invalidas = df[df["cto"].isin(lista_ctos)].copy()

        # Candidatas: 8 portas e caminho com menos de 128 portas
        df_candidatas = df[(df["portas"] == 8)].copy()
        df_candidatas["total_portas_caminho"] = df_candidatas["caminho_rede"].map(portas_por_caminho)
        df_candidatas = df_candidatas[df_candidatas["total_portas_caminho"] < 128]

        # 🔹 NOVA REGRA → excluir candidatas que estão na lista de inválidas
        df_candidatas = df_candidatas[~df_candidatas["cto"].isin(lista_ctos)]

        # Pré-filtragem para melhorar desempenho: limitar por cidade
        cidades_invalidas = df_invalidas["cid_rede"].unique()
        df_candidatas = df_candidatas[df_candidatas["cid_rede"].isin(cidades_invalidas)]

        resultados = []

        # Busca de CTOs próximas
        for _, inv in df_invalidas.iterrows():
            coord_inv = (inv["latitude"], inv["longitude"])
            nome_cto_inv = inv["cto"]
    
            for _, cand in df_candidatas.iterrows():
                coord_cand = (cand["latitude"], cand["longitude"])
                distancia = geodesic(coord_inv, coord_cand).meters
                if distancia <= 200:  # Corrigido para 200 m
                    cand_copy = cand.copy()
                    cand_copy["possível_troca"] = f"{nome_cto_inv}  --->  {cand_copy['cto']}"
                    cand_copy["distancia_m"] = round(distancia, 1)  # Mostrar distância no resultado
                    resultados.append(cand_copy)

        if resultados:
            df_resultado = pd.DataFrame(resultados).drop_duplicates(subset=["cto"])
            st.success(f"✅ Foram encontradas {len(df_resultado)} CTOs disponíveis a até 200m.")
            cidade_filtro = st.selectbox("Filtrar por cidade (opcional):", ["Todas"] + sorted(df_resultado["cid_rede"].unique()))
            if cidade_filtro != "Todas":
                df_resultado = df_resultado[df_resultado["cid_rede"] == cidade_filtro]
            st.dataframe(df_resultado)
        else:
            st.info("❌ Nenhuma CTO com 8 portas e caminho < 128 encontrada a até 200m das CTOs inválidas.")
