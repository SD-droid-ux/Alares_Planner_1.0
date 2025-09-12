import streamlit as st
import googlemaps
import time

GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

st.title("Geocodificação reversa com Google Maps API")

show_street = st.checkbox("Rua", value=True)
show_neighborhood = st.checkbox("Bairro", value=True)
show_city = st.checkbox("Cidade", value=True)

input_text = st.text_area("Cole latitudes e longitudes (ex: -22.57285025800945 -47.401019785207 ou -22.57285025800945, -47.401019785207)", height=150)

if st.button("Buscar endereços"):

    if not input_text.strip():
        st.error("Por favor, insira pelo menos uma latitude e longitude.")
    else:
        coords_list = input_text.strip().split('\n')
        total = len(coords_list)
        progress_bar = st.progress(0)

        for i, coord in enumerate(coords_list, start=1):
            try:
                # Aceita vírgula ou espaço como separador
                parts = coord.replace(",", " ").split()
                if len(parts) != 2:
                    st.warning(f"{i}. Entrada inválida: **{coord}**. Use o formato correto: `latitude longitude` ou `latitude, longitude`")
                    continue

                lat = float(parts[0].strip())
                lng = float(parts[1].strip())

                results = gmaps.reverse_geocode((lat, lng))

                if results:
                    address_components = results[0]["address_components"]

                    street = bairro = cidade = cep = ""

                    for comp in address_components:
                        types = comp["types"]
                        if "route" in types:
                            street = comp["long_name"]
                        if "sublocality" in types or "neighborhood" in types:
                            bairro = comp["long_name"]
                        if "locality" in types:
                            cidade = comp["long_name"]
                        elif "administrative_area_level_2" in types and not cidade:
                            cidade = comp["long_name"]
                        if "postal_code" in types:
                            cep = comp["long_name"]

                    if street == "" or street.lower() == "unnamed road":
                        street = "Rua sem nome"

                    parts = []
                    if show_street and street:
                        parts.append(street)
                    if show_neighborhood and bairro:
                        parts.append(bairro)
                    if cep:
                        parts.append(f"CEP: {cep}")
                    if show_city and cidade:
                        parts.append(cidade)

                    display_address = ", ".join(parts)
                    if display_address == "":
                        display_address = results[0]["formatted_address"]

                    st.write(f"{i}. {display_address}")
                else:
                    st.write(f"{i}. Endereço não encontrado para: {lat}, {lng}")

            except Exception as e:
                st.error(f"{i}. Erro inesperado ao processar: **{coord}**. Erro: {e}")

            progress_bar.progress(i / total)
            time.sleep(1)
