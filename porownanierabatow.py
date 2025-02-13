# -*- coding: utf-8 -*-
"""Soczyste rabaty.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1bfU5lwdNa2GOPWmQ9-URaf30VnlBzQC0
"""

#importowanie potrzebnych bibliotek
import os
import openpyxl
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
from urllib.request import urlopen
import json
import io
import datetime



st.set_page_config(page_title='Porównanie rabatów - IPRA vs P+', layout='wide')



tabs_font_css = """
<style>
div[class*="stTextInput"] label {
  font-size: 26px;
  color: black;
}
div[class*="stSelectbox"] label {
  font-size: 26px;
  color: black;
}
</style>
"""



df = st.file_uploader(
    label = "Wrzuć Raport promocyjny"
)
if df:
    df = pd.read_csv(df, sep=';')
    st.write(df.head())

# Wybieranie tylko określonych kolumn z DataFrame
kolumny = [
    'Id Materiału', 'Nazwa Materiału','Nr producenta sprzedażowego', 'Nazwa producenta sprzedażowego', 
    'identyfikator promocji', 'Nazwa Promocji', 'Nr zlecenia', 'Data obowiązywania promocji od','Data obowiązywania promocji do',  
    'Skład (SPR,SGL)', 'Czy dopuszcza rabat kontraktowy','Rodzaj warunku płatności',
    'Rabat Promocyjny'

]

# Filtruj kolumny w DataFrame
df = df[kolumny]

# Czy dopuszcza rabat kontraktowy = 1 - tylko promocje WHA
df = df[df["Czy dopuszcza rabat kontraktowy"] == 1]


# Rodzaj promocji
df["Rodzaj promocji"] = ""  # Inicjalizacja kolumny
df.loc[df["Nr zlecenia"] == 61114, "Rodzaj promocji"] = "ŚZ/P"
df.loc[df["Nazwa Promocji"].str.contains("ZGZ", na=False), "Rodzaj promocji"] = "ZGZ"
df.loc[df["Nazwa Promocji"].str.contains("BKS", na=False), "Rodzaj promocji"] = "sieci"
df.loc[df["Nr zlecenia"] == 27001, "Rodzaj promocji"] = "centralne"
df.loc[df["Nazwa Promocji"].str.contains("RPM", na=False), "Rodzaj promocji"] = "RPM"
df.loc[df["Nazwa Promocji"].str.contains("IPRA", na=False), "Rodzaj promocji"] = "IPRA"
df.loc[df["Nazwa Promocji"].str.contains("RPM_HIT|RPM HIT", na=False, regex=True), "Rodzaj promocji"] = "EO"

# Oczyszczanie kolumny 'Rabat Promocyjny'
df['Rabat Promocyjny'] = df['Rabat Promocyjny'].fillna(0)
df = df[df["Rabat Promocyjny"] != 0]
df['Rabat Promocyjny'] = df['Rabat Promocyjny'].str.replace(',', '.')  # Zastąp przecinki kropkami, jeśli są
df['Rabat Promocyjny'] = df['Rabat Promocyjny'].str.strip()  # Usuwanie białych znaków
# Konwersja na typ numeryczny (float), w przypadku problemów, zamienia wartości na NaN
df['Rabat Promocyjny'] = pd.to_numeric(df['Rabat Promocyjny'])
df['Rabat Promocyjny'] = df['Rabat Promocyjny'].abs()
df['Rabat Promocyjny'] = df['Rabat Promocyjny'] / 100
# Zaokrąglenie do 2 miejsc po przecinku (opcjonalnie)
df['Rabat Promocyjny'] = df['Rabat Promocyjny'].round(4)
df = df[df["Rabat Promocyjny"] != 0]



# Sprawdzenie wartości po konwersji
st.write("Typ danych w kolumnie 'Rabat Promocyjny':", df['Rabat Promocyjny'].dtype)

# Sprawdzenie wartości po konwersji
st.write("Przykładowe wartości w 'Rabat Promocyjny':", df['Rabat Promocyjny'].head())

df1 = df.copy()
# Usunięcie spacji i zamiana pustych stringów na NaN
df1 = df1.dropna(subset=["Rodzaj promocji"])
df1["Rabat Promocyjny"] = pd.to_numeric(df1["Rabat Promocyjny"], errors="coerce")


# widok z kolejnego arkusza
# Tworzenie tabeli przestawnej
pivot_table = df1.pivot_table(
    index=["Nazwa producenta sprzedażowego", "Id Materiału", "Nazwa Materiału"], 
    columns="Rodzaj promocji", 
    values="Rabat Promocyjny", 
    aggfunc="max"
)

# Resetowanie indeksu dla lepszej czytelności
pivot_table1 = pivot_table.reset_index()
# Wybór tylko konkretnych kolumn (np. "Promocja A" i "Promocja B")
selected_columns = ["Nazwa producenta sprzedażowego", "Id Materiału", "Nazwa Materiału", "IPRA", "EO", "ŚZ/P", "RPM", "ZGZ", "sieci", "centralne"]
pivot_table1 = pivot_table1[selected_columns]

pivot_table1


# Tylko IPRA, EO i ŚZ/P
selected2 = ["Nazwa producenta sprzedażowego", "Id Materiału", "Nazwa Materiału", "IPRA", "EO", "ŚZ/P"]
pivot_table2 = pivot_table1[selected2]
pivot_table2 = pivot_table2.dropna(subset=["IPRA", "EO", "ŚZ/P"], how="all")



# Są w IPRA, nie ma w ŚZ/P
# Krok 1: Wybieramy produkty, które są w "IPRA", ale nie ma ich w "ŚZ/P"
df_ipra = pivot_table2[pivot_table2["IPRA"].notna()]  # Wybieramy tylko te wiersze, gdzie w kolumnie "IPRA" jest wartość (nie NaN)
df_szp = pivot_table2[pivot_table2["ŚZ/P"].notna()]  # Wybieramy tylko te wiersze, gdzie w kolumnie "ŚZ/P" jest wartość (nie NaN)
# Krok 2: Usuwamy produkty z df_ipra, które występują w df_szp
# Zakładając, że "Id Materiału" set difference na Id materiału
products_in_ipra_not_in_szp = df_ipra[~df_ipra["Id Materiału"].isin(df_szp["Id Materiału"])]
# Krok 3: Tworzymy tabelę z produktami, które są w IPRA, ale nie w ŚZ/P
# Możesz dodać dowolne kolumny, które chcesz w tej tabeli, np.:
products_ipra_not_szp = products_in_ipra_not_in_szp[["Nazwa producenta sprzedażowego", "Id Materiału", "Nazwa Materiału", "IPRA"]]


# Są w EO, nie ma w ŚZ/P
df_eo = pivot_table2[pivot_table2["EO"].notna()]
products_in_eo_not_in_szp = df_eo[~df_eo["Id Materiału"].isin(df_szp["Id Materiału"])]
products_eo_not_szp = products_in_eo_not_in_szp[["Nazwa producenta sprzedażowego", "Id Materiału", "Nazwa Materiału", "EO"]]

# Są w ŚZ/P, nie ma w IPRA
products_in_szp_not_in_ipra = df_szp[~df_szp["Id Materiału"].isin(df_ipra["Id Materiału"])]
products_szp_not_ipra = products_in_szp_not_in_ipra[["Nazwa producenta sprzedażowego", "Id Materiału", "Nazwa Materiału", "ŚZ/P"]]

# Są w ŚZ/P, nie ma w EO
products_in_szp_not_in_eo = df_szp[~df_szp["Id Materiału"].isin(df_eo["Id Materiału"])]
products_szp_not_eo = products_in_szp_not_in_eo[["Nazwa producenta sprzedażowego", "Id Materiału", "Nazwa Materiału", "ŚZ/P"]]




# Pobranie dzisiejszej daty w formacie YYYY-MM-DD
today = datetime.datetime.today().strftime('%d-%m-%Y')

# Tworzenie pliku Excel w pamięci
excel_file1 = io.BytesIO()

with pd.ExcelWriter(excel_file1, engine='xlsxwriter') as writer:
    # Zapisywanie arkuszy
    df.to_excel(writer, index=False, sheet_name='dane')
    pivot_table1.to_excel(writer, index=False, sheet_name='porównanie rabatów')
    pivot_table2.to_excel(writer, index=False, sheet_name='IPRA vs ŚZP')
    products_ipra_not_szp.to_excel(writer, index=False, sheet_name='są w IPRA - nie w ŚZP')
    products_eo_not_szp.to_excel(writer, index=False, sheet_name='są w EO - nie w ŚZP')
    products_szp_not_ipra.to_excel(writer, index=False, sheet_name='są w ŚZP - nie w IPRA')
    products_szp_not_eo.to_excel(writer, index=False, sheet_name='są w ŚZP - nie w EO')

    # Pobranie workbooka i arkuszy
    workbook = writer.book
    worksheet1 = writer.sheets["dane"]
    worksheet2 = writer.sheets["porównanie rabatów"]
    worksheet3 = writer.sheets["IPRA vs ŚZP"]
    worksheet4 = writer.sheets["są w IPRA - nie w ŚZP"]
    worksheet5 = writer.sheets["są w EO - nie w ŚZP"]
    worksheet6 = writer.sheets["są w ŚZP - nie w IPRA"]
    worksheet7 = writer.sheets["są w ŚZP - nie w EO"]

    # 🎨 Ustawienie kolorów zakładek
    worksheet1.set_tab_color('#0000FF')  # 🔵 Niebieski dla "dane"
    worksheet2.set_tab_color('#008000')  # 🟢 Zielony dla "porównanie rabatów"
    worksheet3.set_tab_color('#008000')  # 🟢 Zielony dla "IPRA vs ŚZP"
    
    pomaranczowy = '#FFA500'  # 🟠 Pomarańczowy dla arkuszy "są w ... - nie w ..."
    worksheet4.set_tab_color(pomaranczowy)
    worksheet5.set_tab_color(pomaranczowy)
    worksheet6.set_tab_color(pomaranczowy)
    worksheet7.set_tab_color(pomaranczowy)

    # 🎨 Definiowanie formatów kolorów dla rabatów
    green_format = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})  # Zielony
    red_format = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})  # Czerwony
    orange_format = workbook.add_format({'bg_color': '#FFA500', 'font_color': '#000000'})  # Pomarańczowy

    # Pobranie rozmiaru tabeli
    num_rows = len(pivot_table2)
    rabat_range = f"D2:F{num_rows+1}"  # Kolumny D, E, F (IPRA, EO, ŚZ/P)

    # 🔹 Formatowanie: Najwyższy rabat → zielony
    for col in ['D', 'E', 'F']:
        worksheet3.conditional_format(rabat_range, {
            'type': 'formula',
            'criteria': f'={col}2=MAX(IF($D2:$F2<>"", $D2:$F2))',
            'format': green_format
        })

    # 🔻 Formatowanie: Najniższy rabat → czerwony
    for col in ['D', 'E', 'F']:
        worksheet3.conditional_format(rabat_range, {
            'type': 'formula',
            'criteria': f'={col}2=MIN(IF($D2:$F2<>"", $D2:$F2))',
            'format': red_format
        })

    # 🟠 Formatowanie: Brak rabatu → pomarańczowy
    worksheet3.conditional_format(rabat_range, {
        'type': 'blanks',
        'format': orange_format
    })

    # 📏 Ustawienie szerokości kolumn
    max_length = pivot_table1['Nazwa Materiału'].apply(lambda x: len(str(x))).max()
    max_length1 = pivot_table1['Nazwa producenta sprzedażowego'].apply(lambda x: len(str(x))).max()
    
    for ws in [worksheet2, worksheet3, worksheet4, worksheet5, worksheet6, worksheet7]:
        ws.set_column('C:C', max_length + 2)  # Kolumna C - Nazwa Materiału
        ws.set_column('A:A', max_length1 + 2)  # Kolumna A - Nazwa producenta sprzedażowego

# Resetowanie wskaźnika do początku pliku
excel_file1.seek(0)

# Pobranie pliku w Streamlit
st.download_button(
    label='Pobierz porównanie rabatów',
    data=excel_file1,
    file_name=f'Porównanie_rabatów_{today}.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)

