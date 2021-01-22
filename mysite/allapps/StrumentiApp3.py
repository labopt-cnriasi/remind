#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 11 16:38:47 2021

@author: diego
"""
import pandas as pd

import matplotlib.pyplot as plt
import pandas as pd
import folium
import webbrowser
from .APP3_functions import get_classi_produttore,get_classi_cliente, best_n, worst_n


# 1) Seleziona la soglia _____
# il valore della soglia per le classi di profitto è definito
# 2) Seleziona il periodo di riferimento DataLB _____ e DataUB ____
# usa la funzione filterbydate per estrarre il dataframe da usare da i dati disponibili (anni 18-19-20)
# 3) Seleziona lo strumento:

def strumento_1(df, benchmark, cliente):
    df_cliente = df[df['Produttore'] == cliente]

    class_c, class_p, class_s, color, classe = get_classi_cliente(cliente, df_cliente, benchmark)

    class_p = [round(num * 100, 2) for num in class_p]

    fig, (ax1, ax2) = plt.subplots(1, 2)
    # fig.suptitle('Performance nel periodo selezionato')

    # grafico a torta
    labels = [str(class_p[0]) + '% non profittevoli', str(class_p[1]) + '% profittevoli',
              str(class_p[2]) + '% elevato profitto']
    colors = ['red', 'royalblue', 'blue']
    ax1.set_title(str(cliente), fontweight='bold')
    ax1.pie(class_p, labels=labels, colors=colors, shadow=True)

    # istogramma
    # ax2.set_title(str(cliente))
    ax2 = df_cliente['profitto'].plot.hist(bins=10)
    ax2.set(xlabel='profitto missioni', ylabel='numero missioni')

    ricavo_medio = str(round(df_cliente['ricavo'].mean(),2))+" €"
    costo_selezione_medio = str(round(df_cliente['costo_selezione'].mean(),2))+" €"
    costo_trasporto_medio = str(round(df_cliente['costo trasporto'].mean(),2))+" €"
    profitto_medio = str(round(df_cliente['profitto'].mean(),2))+" €"
    distanza_media = str(round(df_cliente["dist[km]"].mean(),2))+" km"
    distanza_max = str(round(max(df_cliente["dist[km]"]),2))+" km"
    totale_km = str(round(sum(df_cliente["dist[km]"]),2))+" km"
    numero_commesse = len(df_cliente.index)
    profitto_totale = str(round(sum(class_s),2))+" €"

    info_list = [ricavo_medio, costo_selezione_medio, costo_trasporto_medio,
                 profitto_medio, distanza_media, distanza_max, totale_km, numero_commesse, profitto_totale]

    columns = ["Ricavo medio", "Costo selezione medio", "Costo trasporto medio",
                  "Profitto medio", "Distanza media", "Distanza max", "Totale km", "Numero missioni", "Profitto totale"]

    df_info = pd.DataFrame([info_list], columns=columns)

    return fig, df_info.to_html(columns = columns, index = False, justify = "center", border=3)


def strumento_2(df, numero, ordine):
    # Seleziona il numero ____ di clienti ____ che vuoi visualizzare
    # menù a tendina per seleziona esclusivamente "migliori" o "peggiori"
    if ordine == "migliori":
        df, produttori_list = best_n(df, numero)
    elif ordine == "peggiori":
        df, produttori_list = worst_n(df, numero)

    df = df[["Data_Registrazione", "C.E.R.", "Produttore", "Smaltitore", "Trasportatore", "profitto"]]
    df.rename(columns={'Data_Registrazione': 'Data'}, inplace=True)
    df['Data'] = pd.to_datetime(df['Data'], infer_datetime_format=True).dt.date
    df.reset_index(inplace = True)
    columns = ["Data", "C.E.R.", "Produttore", "Smaltitore", "Trasportatore", "profitto"]
    return df.to_html(columns = columns, index = False, justify = "center", border=3)


def mappa_produttori_Django(df_produttori, soglia, colore_profitto=False):
    """ estraggo le coordinate di Innocenti"""

    Lat_inno = 41.95708655552737
    Long_inno = 12.764607802039071
    """ creo la mappa centrata su Innocenti"""
    mappa = folium.Map(location=[Lat_inno, Long_inno], zoom_start=7)
    """ inserisco il marker per le coordinate di Innocenti"""
    folium.Marker(
        location=[Lat_inno, Long_inno],
        popup='INNOCENTI SRL',
        icon=folium.Icon(color='purple', icon='industry', prefix='fa')
    ).add_to(mappa)
    """ creo un df dei produttori con nome e coordinate"""
    produttori = df_produttori.drop_duplicates(subset=['Produttore', 'lat_P', 'long_P'])
    """ creo una lista dal df_produttori, serve per il ciclo for"""
    listaProduttori = produttori[['Produttore', 'lat_P', 'long_P']].values.tolist()
    for produttore in listaProduttori:
        produttore_name = produttore[0]
        lat = produttore[1]
        long = produttore[2]
        location = ([lat, long])
        if colore_profitto == True:
            """ ottengo il colore in base alla classe"""
            _, _, _, colore, _ = get_classi_produttore(produttore_name, lat, long, df_produttori, soglia)
        else:
            """ se non voglio la suddivisione in classi di profitto ottengo tutti i marcatori blu"""
            colore = 'blue'
        """ aggiungo i marker dei produttori"""
        folium.Marker(
            location=location,
            popup=produttore_name,
            icon=folium.Icon(color=colore, icon='user', prefix='fa')
        ).add_to(mappa)
    """ salvo la mappa in formato html per farla aprire tramite webbrowser, se si lavora in Jupiter posso eliminare queste istruzioni"""
    mappa.save('mappa.html')

    return mappa._repr_html_()


