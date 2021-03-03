"""
Created on Mon Aug 31 12:56:16 2020
@author: Diego Maria Pinto
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime

def get_node(x):

    i = 0
    j = 0
    k = 0

    count = 0
    for s in x.split():
        if s.isdigit():
            if count == 0:
                i = int(s)
                count += 1
                continue
            if count == 1:
                j = int(s)
                count += 1
                continue
            if count == 2:
                k = int(s)
                count += 1
                continue

    return [i,j,k]

def get_node_TL(x):

    i = 0
    k = 0

    count = 0
    for s in x.split():
        if s.isdigit():
            if count == 0:
                i = int(s)
                count += 1
                continue
            if count == 1:
                k = int(s)
                count += 1
                continue

    return [i,k]


def VRP_interpreter(instance, trucks_plates, x_opt, t_opt, l_opt, distance, duration):

    N = len(instance)
    K = len(trucks_plates)
    paths = [[]]*K
    VRP_results = trucks_plates.values.tolist()
    for k in range(K):

        x_k = x_opt.loc[x_opt["variable"].str.endswith(str(k))]
        t_k = t_opt.loc[t_opt["variable"].str.endswith(str(k))]
        l_k = l_opt.loc[l_opt["variable"].str.endswith(str(k))]

        x_k = x_k.loc[x_opt["value"] == 1]
        if len(x_k.index) == 0:
            paths[k] = "truck not used"
            VRP_results[k].append(paths[k])
        else:
            x_k["node i"]  = x_k["variable"].apply(lambda x: get_node(x)[0])
            x_k["node j"]  = x_k["variable"].apply(lambda x: get_node(x)[1])
            x_k["truck k"] = x_k["variable"].apply(lambda x: get_node(x)[2])

            t_k["node i"]  = t_k["variable"].apply(lambda x: get_node_TL(x)[0])
            t_k["truck k"] = t_k["variable"].apply(lambda x: get_node_TL(x)[1])

            l_k["node i"]  = l_k["variable"].apply(lambda x: get_node_TL(x)[0])
            l_k["truck k"] = l_k["variable"].apply(lambda x: get_node_TL(x)[1])

            visit_order = 0

            paths[k] = [[k,visit_order,"Innocenti",0,41.9555,12.7641,0]]

            departure_node = 0

            ### this loop creates path info for truck k ###
            for i in range(len(x_k)):

                if departure_node == N-1:
                    break

                arrival_node = x_k.loc[x_k['node i'] == departure_node, 'node j'].iloc[0]

                arrival_node_name   = instance.loc[instance['ID'] == arrival_node, 'node_name'].iloc[0]
                arrival_node_lat    = instance.loc[instance['ID'] == arrival_node,       'lat'].iloc[0]
                arrival_node_long   = instance.loc[instance['ID'] == arrival_node,      'long'].iloc[0]
                arrival_node_demand = instance.loc[instance['ID'] == arrival_node,    'demand'].iloc[0]

                visit_order += 1

                paths[k].append([k,visit_order,arrival_node_name,arrival_node,arrival_node_lat,arrival_node_long,arrival_node_demand])

                departure_node = arrival_node

            ### this loop adds time info to path of truck k ###
            for i in range(len(paths[k])):

                node = paths[k][i][3]

                arrival_time = t_k.loc[t_k["node i"] == node, "value"].iloc[0] + 1/60
                node_demand    = instance.loc[instance['ID'] == node,  'demand'].iloc[0]
                if node_demand >= 0:
                    departure_time = instance.loc[instance['ID'] == node, 'service time'].iloc[0]*node_demand
                    departure_time = arrival_time + departure_time/60
                if node_demand < 0:
                    departure_time = instance.loc[instance['ID'] == node, 'service time'].iloc[0]*abs(node_demand)-abs(node_demand)*(5/60)
                    departure_time = arrival_time + departure_time/60

                hours = int(arrival_time)
                minutes = int((arrival_time - int(arrival_time))*60)
                arrival_time = datetime.time(hour=hours, minute=minutes)

                hours = int(departure_time)
                minutes = int((departure_time - int(departure_time))*60)
                departure_time = datetime.time(hour=hours, minute=minutes)

                leaving_load = l_k.loc[l_k["node i"] == node, "value"].iloc[0]


                paths[k][i].append(arrival_time)
                paths[k][i].append(departure_time)
                paths[k][i].append(leaving_load)

            # save complete path info as a dataframe
            paths[k] = pd.DataFrame(paths[k],columns =['truck #',"visit order","node name","node number","lat","long","load_unload","arrival time","departure time","leaving load"])
            paths[k] = paths[k].astype({'truck #': int, 'visit order': int, 'node name': str, 'node number': int,'lat':float, 'long':float, 'load_unload': int,'arrival time':str,'departure time':str,'leaving load': int})


            # if last 2 nodes visited correspond to the depot, drop one
            if paths[k].iloc[-1]["node name"] == paths[k].iloc[-2]["node name"]:
                paths[k] = paths[k].iloc[:-1]


            #####################  some time fixes ######################

            # set first departure time according to duration matrix info
            first_visit_node = int(paths[k].loc[1,'node number'])
            first_duration = duration.iloc[0,first_visit_node]

            first_arrival = paths[k].loc[paths[k]["node number"] == first_visit_node, "arrival time"].iloc[0]
            first_arrival = datetime.datetime.strptime(first_arrival, '%H:%M:%S').time()
            first_arrival_time = first_arrival.hour + first_arrival.minute/60

            first_departure = first_arrival_time - first_duration
            hours = int(first_departure)
            minutes = int((first_departure - int(first_departure))*60)
            first_departure = str(datetime.time(hour=hours, minute=minutes))

            paths[k].loc[paths[k].index[0],'departure time'] = first_departure


            # set first arrival time as " "
            paths[k].loc[0,'arrival time'] = " "

            # set last departure time as " "
            paths[k].loc[paths[k].index[-1],'departure time'] = " "
            paths[k].loc[paths[k].index[-1], 'leaving load'] = " "
            ############################################################

            VRP_results[k].append(paths[k])

    return VRP_results



# visualization : plotting with matplolib

def matplolib_graph_plot(vrp_results):

    df = vrp_results
    customer_count = len(df)

    plt.figure(figsize=(12, 12))
    for i in range(customer_count):
        if i == 0:
            plt.scatter(df.lat[i], df.long[i], c='green', s=200)
            plt.text(df.lat[i], df.long[i], "depot", fontsize=12)
        else:
            plt.scatter(df.lat[i], df.long[i], c='orange', s=200)
            plt.text(df.lat[i], df.long[i], str(df.load_unload[i]), fontsize=12)

    for i in range(customer_count-1):
        j = i + 1
        plt.plot([df.lat[i], df.lat[j]], [df.long[i], df.long[j]], c="black")

    plt.show()

    return