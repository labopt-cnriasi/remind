# -*- coding: utf-8 -*-
"""
Created on Wed Dec 30 18:07:56 2020

@author: Fabio
"""

import pandas as pd
import matplotlib.pyplot as plt


def df_filterbydate(df, dataLB, dataUB):
    df['Data_Registrazione'] = pd.to_datetime(df['Data_Registrazione'], infer_datetime_format=True).dt.date
    df = df[(df['Data_Registrazione'] >= dataLB) & (df['Data_Registrazione'] <= dataUB)]
    return df


def get_df_classi(df, soglia=180):
    # creo df delle classi non prof == 0/ prof == 1/ molto prof == 2 """
    df0 = df[df['profitto'] <= 0]
    df1 = df[(df['profitto'] > 0) & (df['profitto'] <= soglia)]
    df2 = df[df['profitto'] > soglia]
    return df0, df1, df2


def get_classi_cliente(cliente, df, soglia):
    # estraggo il df del singolo cliente considerando tutti i suoi produttori
    df_cliente = df[df['Produttore'] == cliente]
    visit_num = len(df_cliente.index)
    df0, df1, df2 = get_df_classi(df_cliente,soglia)

    class_0c = len(df0.index)  # conto il totale degli ordini non prof
    class_1c = len(df1.index)  # conto il totale degli ordini prof
    class_2c = len(df2.index)  # conto il totale degli ordini max prof
    class_c = [class_0c, class_1c, class_2c]

    class_0p = class_0c / visit_num
    class_1p = class_1c / visit_num
    class_2p = class_2c / visit_num
    class_p = [class_0p, class_1p, class_2p]

    class_0s = df0['profitto'].sum()  # sommo il totale degli ordini non prof
    class_1s = df1['profitto'].sum()  # sommo il totale degli ordini prof
    class_2s = df2['profitto'].sum()  # sommo il totale degli ordini max prof
    class_s = [class_0s, class_1s, class_2s]

    if (class_0s >= class_1s + class_2s) or (class_0p > class_1p and class_0p > class_2p):
        color = 'red'  # se non profittevole
        classe = 0
    elif (class_1p >= class_0p) and (class_1p >= class_2p):
        color = 'lightblue'  # se profittevole
        classe = 1
    elif (class_2p >= class_0p) and (class_2p >= class_1p):
        color = 'blue'  # se ottimo profitto
        classe = 2

    return class_c, class_p, class_s, color, classe


def get_classi_produttore(cliente, lat, long, df, soglia):
    # creo un df per singolo cliente con le coordinate di tutti i suoi produttori
    df_produttore = df[(df['Produttore'] == cliente) & (df['lat_P'] == lat) & (df['long_P'] == long)]
    visit_num = len(df_produttore.index)
    df0, df1, df2 = get_df_classi(df_produttore, soglia)

    class_0c = df0['profitto'].count()  # conto il totale degli ordini non prof
    class_1c = df1['profitto'].count()  # conto il totale degli ordini prof
    class_2c = df2['profitto'].count()  # conto il totale degli ordini max prof
    class_c = [class_0c, class_1c, class_2c]

    class_0p = class_0c / visit_num
    class_1p = class_1c / visit_num
    class_2p = class_2c / visit_num
    class_p = [class_0p, class_1p, class_2p]

    class_0s = df0['profitto'].sum()  # sommo il totale degli ordini non prof
    class_1s = df1['profitto'].sum()  # sommo il totale degli ordini prof
    class_2s = df2['profitto'].sum()  # sommo il totale degli ordini max prof
    class_s = [class_0s, class_1s, class_2s]

    if (class_0s >= class_1s + class_2s) or (class_0p > class_1p and class_0p > class_2p):
        color = 'red'  # se non profittevole
        classe = 0
    elif (class_1p >= class_0p) and (class_1p >= class_2p):
        color = 'blue'  # se profittevole
        classe = 1
    elif (class_2p >= class_0p) and (class_2p >= class_1p):
        color = 'darkblue'  # se ottimo profitto
        classe = 2

    return class_c, class_p, class_s, color, classe


def filtro_ordine_peggiore(df,df2):  # restituisce i peggiori ordini dei singoli clienti nella classe specificata dal df in input, df2 è il df totale
    produttori = df['Produttore'].drop_duplicates().tolist()
    ordini_peggiori = []
    for produttore in produttori:
        """ seleziono i peggiori ordini del produttore sulla base del profitto"""
        peggiore = min(df[df['Produttore'] == produttore]['profitto'])
        """ estraggo gli indici dei peggiori ordini"""
        peggiore_index = df[df['profitto'] == peggiore].index
        """ ne estraggo il num fiscale"""
        num_ordine = df2.iloc[peggiore_index]['NumFiscale'].values
        """ creo una lista con produttore, num ficale e profitto dei peggiori ordini"""
        ordini_peggiori.append([produttore, num_ordine, peggiore])
        """ creo un df dalla lista"""
    df_ordini = pd.DataFrame(data=ordini_peggiori, columns=['Produttore', 'NumFiscale', 'profitto'])
    return df_ordini


def filtro_classifica(
        df):  # da usare con i dataframe df_non_prof\df_prof\df_max_prof, restituisce la classifica dei clienti sulla base del profitto totale
    """ creo un df ordinato in modo decrescente sulla base del profitto"""
    classifica = df.sort_values(by='profitto', ascending=False)
    profitto = classifica['profitto']
    produttori = classifica['Produttore']
    df_classifica = pd.DataFrame()
    df_classifica['Produttore'] = produttori
    df_classifica['profitto'] = profitto
    return df_classifica


def best_n(df, n):
    df_best = df.nlargest(n, 'profitto')
    produttori_list = df_best['Produttore'].tolist()
    return df_best, produttori_list


def worst_n(df, n):
    df_worst = df.nsmallest(n, 'profitto')
    produttori_list = df_worst['Produttore'].tolist()
    return df_worst, produttori_list


def grafici(df, df2, dfn, dfp, dfo, hist, pie, best,
            worst):  # dare in input df, dfpneg, dfp, dfpmax e df2 è il df_produttori
    """ per scegliere il tipo di grafico inserire un valore al posto di hist/pie (o entrambi) e None su quello non richiesto, stessa cosa per scegliere se peggiori o migliori, ma non entrambi"""
    ax_i = []
    ax_t = []
    """blocco di if/elif per verificare la scelta del tipo di grafico """
    if (pd.isna(hist) == False) & (pd.isna(pie) == False):
        """blocco di if/elif per verificare la scelta tra peggiori e migliori """
        if pd.isna(best) == False:
            produttori = best_n(df2, 10)
        elif pd.isna(worst) == False:
            produttori = worst_n(df2, 10)
        else:
            produttori = []
        """blocco di if/elif per verificare la scelta del tipo di grafico """
        for produttore in produttori:
            """ per l'istogramma seleziono il produttore e estraggo la serie delle commesse nel df ed eseguo il plot"""
            serie = df[df['Produttore'] == produttore]['profitto']
            figure, axes = plt.subplots(1, 1)
            plt.title(produttore)
            ax = serie.plot.hist()
            plt.ylabel('numero commesse')
            ax_i.append([produttore, ax])
            """ per la torta seleziono il produttore ed estraggo la serie delle commesse in df_pneg, df_p e df_pmax"""
            serie_neg = dfn[dfn['Produttore'] == produttore]['profitto']
            serie_prof = dfp[dfp['Produttore'] == produttore]['profitto']
            serie_max = dfo[dfo['Produttore'] == produttore]['profitto']
            """ eseguo il plot sul numero di volte che il produttore compare nelle singole classi """
            y = [len(serie_neg), len(serie_prof), len(serie_max)]
            label = ['non profittevoli', 'profittevoli', 'ottimo profitto']
            figure, ax = plt.subplots()
            plt.title(produttore)
            ax.pie(y)
            plt.legend(label, loc="best")
            ax_t.append([produttore, ax])
    elif pd.isna(hist) == False:
        if pd.isna(best) == False:
            produttori = best_n(df2, 10)
        elif pd.isna(worst) == False:
            produttori = worst_n(df2, 10)
        else:
            produttori = []
        for produttore in produttori:
            serie = df[df['Produttore'] == produttore]['profitto']
            figure, axes = plt.subplots(1, 1)
            plt.title(produttore)
            ax = serie.plot.hist()
            plt.ylabel('numero commesse')
            ax_i.append([produttore, ax])
    elif pd.isna(pie) == False:
        if pd.isna(best) == False:
            produttori = best_n(df2, 10)
        elif pd.isna(worst) == False:
            produttori = worst_n(df2, 10)
        else:
            produttori = []
        for produttore in produttori:
            serie_neg = dfn[dfn['Produttore'] == produttore]['profitto']
            serie_prof = dfp[dfp['Produttore'] == produttore]['profitto']
            serie_max = dfo[dfo['Produttore'] == produttore]['profitto']
            y = [len(serie_neg), len(serie_prof), len(serie_max)]
            label = ['non profittevoli', 'profittevoli', 'ottimo profitto']
            figure, ax = plt.subplots()
            plt.title(produttore)
            ax.pie(y)
            plt.legend(label, loc="best")
            ax_t.append([produttore, ax])
    else:
        ax_i = []
        ax_t = []
    return ax_i, ax_t














