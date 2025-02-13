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

# widok z kolejnego arkusza
# Tworzenie tabeli przestawnej
pivot_table = df.pivot_table(
    index=["Id Materiału", "Nazwa Materiału"], 
    columns="Rodzaj Promocji", 
    values="Rabat Promocyjny", 
    aggfunc="max"
)

# Resetowanie indeksu dla lepszej czytelności
pivot_table = pivot_table.reset_index()
pivot_table

# Pobranie dzisiejszej daty w formacie YYYY-MM-DD
today = datetime.datetime.today().strftime('%Y-%m-%d')

# Tworzenie pliku Excel w pamięci
excel_file1 = io.BytesIO()

with pd.ExcelWriter(excel_file1, engine='xlsxwriter') as writer:
    # Zapisanie DataFrame do arkusza o nazwie "dane"
    df.to_excel(writer, index=False, sheet_name='dane')

    # Pobranie obiektu workbook i worksheet
    workbook = writer.book
    worksheet = writer.sheets["dane"]

    # Definiowanie formatu liczbowego z przecinkiem dziesiętnym
    #format_percent = workbook.add_format({"num_format": "0,00"})  # Dwa miejsca po przecinku

    # Ustalenie szerokości kolumn i zastosowanie formatu (dla całego zakresu kolumn)
    #worksheet.set_column("B:Z", None, format_percent)  # Dostosuj zakres kolumn do swojego pliku

# Resetowanie wskaźnika do początku pliku
excel_file1.seek(0)

# Umożliwienie pobrania pliku Excel
st.download_button(
    label='Pobierz porównanie rabatów',
    data=excel_file1,
    file_name=f'Porównanie_rabatów_{today}.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)



