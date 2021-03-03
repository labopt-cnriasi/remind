"""
@author: G.Stecca, D.Pinto
"""

import pandas as pd
import numpy as np
import datetime

np.random.seed(0)

class DataInst:
    distance = np.ndarray
    duration = np.ndarray
    l = np.ndarray  # demand
    travel_cost = np.ndarray
    n = 0  # numero di clienti totali
    k = 0  # numero veicoli
    K = []  # lista dei veicoli
    Cap = []  # capacità dei k veicoli

    N = []  # crea un array di tutti i possibili nodi di pickup e delivery partendo
    # da 1 fino al doppio dei clienti, tolist: trasforma l'array in lista

    P = []  # insieme nodi pickup
    D = []  # insieme nodi delivery

    Or = []  # deposito innocenti origine
    Dest = []  # deposito innocenti destinazione

    ##################### Insiemi secondo la formulazione di Vigo ############
    Nod = []

    Po = []
    Pd = []

    No = []
    Nd = []

    Do = []
    Dd = []

    Od = []
    ##########################################################################

    a = []  # timewindow left
    b = []  # timewindows right

    ##########################################################################

    s = []
    M = 1000
    M2 = 10
    max_turno = 8.5
    group_id = {}  # id of the same physical node belong to the same group_id


class Tour:
    """
    @maxCap max vehicle capacity
    @Tmax max duration
    @inst Data instance of type @DataInst
    """

    def __init__(self, maxCap, Tmax, inst: DataInst):
        self.maxCap = 2
        self.Tmax = 0
        self.time = 0
        self.distance = 0
        self.cost = 0
        self.hops = []  # tour sequence
        self.load = []  # load profile
        self.orders = []
        self.maxCap = maxCap
        self.Tmax = Tmax
        origin = inst.Or[0]
        destination = inst.Dest[0]
        self.hops.append(origin)
        self.load.append(0)
        self.hops.append(destination)
        self.load.append(0)
        self.time += inst.duration[origin, destination]

    """
    Insert with no check pickup in position i and delivery in position j
    """

    def insertij(self, pickup: int, delivery: int, i: int, j: int, inst: DataInst):
        loadplus = inst.l[pickup]
        # pre_pick = self.hops[i-1]
        # post_pick = self.hops[i+1]
        # pre_del = self.hops[j-1]
        # post_del = self.hops[j+1]
        self.hops.insert(i, pickup)
        preload = self.load[i - 1]
        self.load.insert(i, preload + loadplus)

        addedTime = inst.duration[self.hops[i - 1], self.hops[i]] + inst.duration[self.hops[i], self.hops[i + 1]]
        addedTime -= inst.duration[self.hops[i - 1], self.hops[i + 1]]

        addedDist = inst.distance[self.hops[i - 1], self.hops[i]] + inst.distance[self.hops[i], self.hops[i + 1]]
        addedDist -= inst.distance[self.hops[i - 1], self.hops[i + 1]]

        addedCost = inst.travel_cost[self.hops[i - 1], self.hops[i]] + inst.travel_cost[self.hops[i], self.hops[i + 1]]
        addedCost -= inst.travel_cost[self.hops[i - 1], self.hops[i + 1]]

        self.hops.insert(j, delivery)
        self.load.insert(j, preload)

        addedTime += inst.duration[self.hops[j - 1], self.hops[j]] + inst.duration[self.hops[j], self.hops[j + 1]]
        addedTime -= inst.duration[self.hops[j - 1], self.hops[j + 1]]
        self.time += addedTime

        addedDist += inst.distance[self.hops[j - 1], self.hops[j]] + inst.distance[self.hops[j], self.hops[j + 1]]
        addedDist -= inst.distance[self.hops[j - 1], self.hops[j + 1]]
        self.distance += addedDist

        addedCost += inst.travel_cost[self.hops[j - 1], self.hops[j]] + inst.travel_cost[self.hops[j], self.hops[j + 1]]
        addedCost -= inst.travel_cost[self.hops[j - 1], self.hops[j + 1]]
        self.cost += addedCost

        self.orders.append(pickup)
        return

    def insert(self, order: int, inst: DataInst):
        # insert in first available position
        lentour = len(self.hops)
        c = -1
        order_dest = order + inst.n
        loadplus = inst.l[order]
        if loadplus > self.maxCap:
            print("capacity constraint violated")
            return -1
        for i in self.hops:
            c += 1
            if c <= 0:
                continue
            # if inst.group_id[i] != inst.group_id[order]:
            addedTime = inst.duration[self.hops[c - 1], order] + inst.duration[order, order_dest] + inst.duration[
                order_dest, self.hops[c]]
            addedTime -= inst.duration[self.hops[c - 1], self.hops[c]]
            if self.time + addedTime > self.Tmax:
                # print("time constraint violated")
                continue
            if self.load[c - 1] > self.maxCap - loadplus:
                # print("capacity not available after node " + str(self.hops[c-1]))
                continue
            self.insertij(order, order_dest, c, c + 1, inst)

            # self.hops.insert(c, order)
            # preload = self.load[c-1]
            # self.load.insert(c, preload + loadplus)
            # self.hops.insert(c+1, order_dest)
            # self.load.insert(c+1, preload)
            # self.time += addedTime
            # self.orders.append(order)

            return 1
            # else:
            # manage situation in which pickup node of order is the same of node i
            # pass
        return -1

    def getCost(self, inst: DataInst):

        return 1


def load_instance(distance,duration,demand,time_info, trucks_info):
    di = DataInst

    l = demand

    distance = distance.values
    travel_cost = distance * (0.9)

    duration = duration.values

    # dfgroup = pd.read_excel('Instance_'+str(instance)+'_group.xlsx')
    di.group_id = {}  # {int(row['ID']): int(row['group_id']) for index, row in dfgroup.iterrows()}

    n = int((len(distance) - 2) / 2)  # numero di clienti totali
    k = len(trucks_info)
    K = np.arange(0, k).tolist()  # lista dei veicoli
    Cap = trucks_info  # capacità dei k veicoli random int tra 1 e 2

    # crea un array di tutti i possibili nodi di pickup e delivery partendo da 1 fino al doppio dei clienti, tolist: trasforma l'array in lista
    N = np.arange(1, (2 * n) + 1, 1).tolist()
    P = N[:n]  # insieme clienti su cui fare pickup
    D = N[n:]  # insieme di clienti su cui fare delivery

    Or = [0]  # deposito innocenti origine
    Dest = [len(N) + 1]  # deposito innocenti destinazione

    ##################### Insiemi secondo la formulazione di Vigo ############
    Nod = Or + N + Dest

    Po = Or + P
    Pd = P + Dest

    No = Or + N
    Nd = N + Dest

    Do = Or + D
    Dd = D + Dest

    Od = Or + Dest
    ##########################################################################

    a = []
    b = []
    for i in time_info:
        a.append(i[0].hour + i[0].minute/60)
        b.append(i[1].hour + i[1].minute/60)

    ##########################################################################

    s = []
    for i in Nod:
        if l[i] == 0:
            s.append(0)
        elif l[i] == 1:
            s.append(time_info[i][2]/60)  # quando carico un'unità ci metto 15 minuti
        elif l[i] == -1:
            s.append(time_info[i][2]/60 - 5/60)  # quando scarico un'unità ci metto 10 minuti
        elif l[i] == -2:
            s.append(time_info[i][2]*2/60 - 10/60)  # quando scarico due unità ci metto 20 minuti
        else:
            s.append(time_info[i][2]*2/60)  # quando carico due unità ci metto 30 minuti

    M = 1000
    M2 = 10

    max_turno = 8.5

    di.distance = distance
    di.duration = duration
    di.l = l  # demand
    di.travel_cost = travel_cost
    di.n = n
    di.k = k
    di.K = K
    di.Cap = Cap
    di.N = N
    di.P = P
    di.D = D
    di.Or = Or
    di.Dest = Dest
    di.Po = Po
    di.Pd = Pd
    di.No = No
    di.Nd = Nd
    di.Do = Do
    di.Dd = Dd
    di.Od = Od
    di.Nod = Nod

    di.a = a
    di.b = b
    di.s = s
    di.M = M
    di.M2 = M2
    di.max_turno = max_turno

    return di


def heur01(inst: DataInst):
    # sort on arrival time / duration (Or, i)
    a = []
    c = 0
    for i in inst.a:
        dur = inst.duration[inst.Or, c][0]
        if dur == 0:
            dur = 1
        c += 1
        if c > inst.n + 1:  # greater id stand for delivery nodes.
            break
        a.append(i / dur)
    la = [i for i in zip(a, inst.Nod)]  # list of tuples (twa/duration, node index)
    la = sorted(la)  # sorted
    tours = []
    aTour = Tour(2, inst.max_turno, inst)
    tours.append(aTour)
    for (a, i) in la:
        if i == inst.Or[0] or i == inst.Dest[0]:
            continue
        print("inserting node ", i)
        ret = aTour.insert(i, inst)
        if ret < 0:
            newTour = Tour(2, inst.max_turno, inst)
            tours.append(newTour)
            newTour.insert(i, inst)
            aTour = newTour
    #### Print tours ####
    totalCost = 0
    for t in tours:
        print("**************************")
        print("hops")
        s = ''
        for h in t.hops:
            s += str(h) + '->'
        print(s[:len(s) - 2])
        print("loads")
        print(t.load)
        print("Time: ", t.time)
        print("Distance ", t.distance)
        print("Cost ", t.cost)
        totalCost += t.cost
    print("total cost:************** ", totalCost)
    return tours


def heuristic_result_interpreter(instance,trucks_plates, tours, distance, duration, time_info):

    N = len(instance)
    K = len(trucks_plates)
    paths = [[]]*K
    VRP_results = trucks_plates.values.tolist()

    for k in np.arange(1,K):
        paths[k] = "truck not used"
        VRP_results[k].append(paths[k])

    tour = tours[0]
    node_list = tour.hops

    k = 0
    for i in node_list:
        visit_order = i
        node_name   = instance.loc[instance['ID'] == i, 'node_name'].iloc[0]
        node_lat    = instance.loc[instance['ID'] == i, 'lat'].iloc[0]
        node_long   = instance.loc[instance['ID'] == i, 'long'].iloc[0]
        load_unload = instance.loc[instance['ID'] == i, 'demand'].iloc[0]
        paths[k].append([0, visit_order, node_name, i, node_lat, node_long, load_unload])

    ### this loop adds time info to path of truck k ###
    for i in range(len(paths[k])):

        node = paths[k][i][3]

        if i == 0:
            arrival_time = 0
            departure_time = time_info[1][0].hour - duration.iloc[0,1]
            hours = int(departure_time)
            minutes = int((departure_time - int(departure_time)) * 60)
            departure_time_datetime = datetime.time(hour=hours, minute=minutes)
            arrival_time_datetime = departure_time_datetime # later will be corrected and set as an emtpy string " "
        elif i == 1:
            arrival_time = time_info[i][0]
            node_demand = instance.loc[instance['ID'] == node, 'demand'].iloc[0]
            service_time = instance.loc[instance['ID'] == node, 'service time'].iloc[0] * node_demand
            departure_time = arrival_time.hour + arrival_time.minute + service_time / 60
            arrival_time_datetime = arrival_time
            hours = int(departure_time)
            minutes = int((departure_time - int(departure_time)) * 60)
            departure_time_datetime = datetime.time(hour=hours, minute=minutes)
        else:
            previous_node = paths[k][i-1][3]
            arrival_time = departure_time + duration.iloc[previous_node, node]
            node_demand = instance.loc[instance['ID'] == node, 'demand'].iloc[0]
            if node_demand >= 0:
                service_time = instance.loc[instance['ID'] == node, 'service time'].iloc[0] * node_demand
                departure_time = arrival_time + service_time / 60
            if node_demand < 0:
                service_time = instance.loc[instance['ID'] == node, 'service time'].iloc[0] * abs(node_demand) - abs(node_demand) * (5 / 60)
                departure_time = arrival_time + service_time / 60

        ################## datetime translation####################################
        if i > 1:
            hours = int(arrival_time)
            minutes = int((arrival_time - int(arrival_time)) * 60)
            arrival_time_datetime = datetime.time(hour=hours, minute=minutes)

            hours = int(departure_time)
            minutes = int((departure_time - int(departure_time)) * 60)
            departure_time_datetime = datetime.time(hour=hours, minute=minutes)

        #############################################################################
        if i == 0:
            leaving_load = 0
        else:
            leaving_load = leaving_load + node_demand

        paths[k][i].append(arrival_time_datetime)
        paths[k][i].append(departure_time_datetime)
        paths[k][i].append(leaving_load)

    paths[k] = pd.DataFrame(paths[k], columns=['truck #', "visit order", "node name", "node number", "lat", "long", "load_unload","arrival time", "departure time", "leaving load"])
    paths[k] = paths[k].astype({'truck #': int, 'visit order': int, 'node name': str, 'node number': int, 'lat': float, 'long': float,'load_unload': int, 'arrival time': str, 'departure time': str, 'leaving load': int})

    # if last 2 nodes visited correspond to the depot, drop one
    if paths[k].iloc[-1]["node name"] == paths[k].iloc[-2]["node name"]:
        paths[k] = paths[k].iloc[:-1]

    # set first arrival time as " "
    paths[k].loc[0, 'arrival time'] = " "

    # set last departure time as " "
    paths[k].loc[paths[k].index[-1], 'departure time'] = " "
    paths[k].loc[paths[k].index[-1], 'leaving load'] = " "
    ############################################################



    VRP_results[k].append(paths[k])

    return VRP_results

