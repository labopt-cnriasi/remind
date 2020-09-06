#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 19 13:13:03 2020

@author: diego
"""

import pandas as pd
import requests as rq

##########################################################################################
##########################################################################################
##########################################################################################
##########################################################################################
##########################################################################################
#########################  DOCKER SERVER on PORT 5000  ###################################
##########################################################################################
##########################################################################################
##########################################################################################
##########################################################################################
##########################################################################################

# before to go please start the map service on docker with the following command (for centro)
# docker run -t -i -p 5000:5000 -v $(pwd):/data osrm/osrm-backend osrm-routed --algorithm mld /data/centro-latest.osrm
# tipo di servizio: 'OPENROUTESERVICE' si collega a https://openrouteservice.org/
# 'LOCAL' si collega al server locale installato tramite osrm-backend project
route_service = 'LOCAL'
# Inserire qui la propria api key ottenuta da https://openrouteservice.org/
# serve solo se il tipo di servizio è 'OPENROUTESERVICE
myApyKey = '5b3ce3597851110001cf62488cc89bf95d4b4c019b17589365548095'

# funzione che richiede il calcolo del percorso tra due punti al servizio selezionato,
# definito tramite la variabile globale 'route_service
# Args:
#     long1 (float): longitudine della sorgente
#     lat1 (float): latitudine della sorgente
#     long2 (float): longitudine della destinazione
#     lat2 (float): latitudine della destinazione

DEBUG = False

def getPath(long1, lat1, long2, lat2):
    if route_service == 'OPENROUTESERVICE':
        headers = {
            'Accept': 'application/json; charset=utf-8'
        }
        myurl = 'https://api.openrouteservice.org/directions?api_key=' + myApyKey + '&coordinates=' + str(
            long1) + ',' + str(lat1) + '%7C' + str(long2) + ',' + str(lat2) + '&profile=driving-car'
        response = rq.request(url=myurl, headers=headers, method='GET')
        return response
    elif route_service == 'LOCAL':
        myurl = 'http://127.0.0.1:5000/route/v1/driving/'
        myurl += str(long1) + ',' + str(lat1) + ';' + str(long2) + ',' + str(lat2)
        params = (
            ('steps', 'false'),
        )
        response = rq.get(myurl, params=params)
        return response
    else:
        return 'ERROR'


def getDistance(response):
    a = dict(response.json())
    if DEBUG:
        print(a)
    if route_service == 'OPENROUTESERVICE':
        return a['routes'][0]['summary']['duration']
    elif route_service == 'LOCAL':
        dist = a['routes'][0]['distance']
        return dist
    else:
        return 'ERROR'


def getTime(response):
    a = dict(response.json())
    if DEBUG:
        print(a)
    if route_service == 'OPENROUTESERVICE':
        return a['routes'][0]['summary']['duration']
    elif route_service == 'LOCAL':
        duration = a['routes'][0]['duration']
        return duration
    else:
        return 'ERROR'


##############################################################################################

def OSM(instance):

    df = instance

    print(df)
    n = len(df.index)

    print("number of rows: ", n)

    A = df.values  # matrice n * 4

    df_dis = df.copy()
    df_dur = df.copy()

    for i in range(n):
        new_col_dis = []
        new_col_dur = []
        id_from = A[i][0]
        for j in range(n):
            id_to = A[j][0]
            if i != j:
                long2 = A[i][3]
                lat2 = A[i][2]
                long1 = A[j][3]
                lat1 = A[j][2]
                print("distance from {},{} to {},{}".format(long1, lat1, long2, lat2))
                response = getPath(long1, lat1, long2, lat2)
                dis = getDistance(response) / 1000
                dur = (getTime(response) / 3600) / (0.7)
            else:
                dis = 0
                dur = 0
            print("distance from {} to {}: {}".format(id_from, id_to, dis))
            new_col_dis.append(dis)
            print("duration from {} to {}: {}".format(id_from, id_to, dur))
            new_col_dur.append(dur)

        df_dis[str(int(id_from))] = new_col_dis
        df_dur[str(int(id_from))] = new_col_dur

    distance = df_dis.iloc[:, 4:]
    duration = df_dur.iloc[:, 4:]

    return distance, duration




