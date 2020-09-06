from mip import *

import pandas as pd
import numpy as np


def VRP_model(distance,duration,demand,time_info, trucks_info, solver, gap, time_limit):

    l = demand

    distance = distance.values
    travel_cost = distance * (0.9)

    duration = duration.values

    m = Model('VRP')

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

    ######## Model ###########################################################

    m = Model("VRP", sense=MINIMIZE, solver_name = solver)  # CBC or GRB for Gurobi

    # Variables

    x = {(i, j, k): m.add_var(lb=0, ub=1, var_type = BINARY, obj=travel_cost[i, j], name='x {} {} {}'.format(i, j, k))
         for i in Nod for j in Nod for k in K}

    T = {(i, k): m.add_var(lb=0, var_type=CONTINUOUS, name='T {} {}'.format(i, k)) for i in Nod for k in K}

    L = {(i, k): m.add_var(lb=0, ub=2, var_type=INTEGER, name='L {} {}'.format(i, k)) for i in Nod for k in K}

    # VINCOLI

    ###############################################################################################
    #########  1  ### IL CARICO QUANDO ESCO DALL'ORIGINE E QUANDO TORNO ALLA DEST DEVE ESSERE PARI A ZERO
    for k in K:
        m += xsum(L[i, k] for i in Od) == 0, 'Inizio_fine_0({})'.format(k)

    ###############################################################################################
    #########  2  ### OGNI NODO DEVE ESSERE SERVITO DA UN SOLO VEICOLO
    for i in P:
        m += xsum(x[i, j, k] for k in K for j in Nd if j != i) == 1, 'Servizio_nodo_({})'.format(i)

    ###############################################################################################
    #########  3  ### DEVO VISITARE PRIMA IL NODO DI PICKUP E POI IL RISPETTIVO DELIVERY
    for k in K:
        for i in P:
            m += (xsum(x[i, j, k] for j in N if j != i)) == (
                xsum(x[j, n + i, k] for j in N if j != (n + i))), 'pick_deliv({}_{})'.format(k, i)

    # NB : con i vincoli 4 e 5 old la f.o. cresce all'aumentare del parametro k, con i vincoli 4 e 5 new non varia.
    ###############################################################################################
    #########  4 new ### Tutti i veicoli che sono utilizzati partono da Innocenti
    for k in K:
        m += (xsum(x[0, j, k] for j in P)) <= 1, 'or_Inno({})'.format(k)
    ###############################################################################################
    #########  4 old ### Tutti i veicoli sono utilizzati e partono da Innocenti
    # for k in K:
    #    m += (xsum( x[0,j,k] for j in P ) == 1 , 'or_Inno({})'.format(k)

    ###############################################################################################
    #########  5 new ### Tutti i veicoli che sono usciti allora toranano ad Innocenti
    for k in K:
        m += (xsum(x[i, Dest[0], k] for i in D if i != Dest[0])) == (
            xsum(x[0, j, k] for j in P)), 'dest_Inno({})'.format(k)

    ###############################################################################################
    #########  5 old ### Tutti i veicoli tornando ad Innocenti
    # for k in K:
    #     m += (xsum(x[i,Dest[0],k] for i in D if i != Dest[0])) == 1 ,'dest_Inno({})'.format(k)

    ###############################################################################################
    #########  6  ### OGNI VEICOLO CHE ENTRA IN UN NODO DEVE USCIRE DALLO STESSO
    for k in K:
        for j in N:
            m += xsum(x[i, j, k] for i in No if i != j) == xsum(
                x[j, i, k] for i in Nd if i != j), 'Visita_nodo({}_{})'.format(k, j)

    ################################################################################################
    #########  7  ### VINCOLI TEMPORALI
    for k in K:
        for i in Nod:
            for j in Nod:
                if i == j:
                    continue
                m += (T[i, k] + s[i] + duration[i, j] - T[j, k]) <= M * (
                            1 - x[i, j, k]), 'Vinc_temp1({}_({},{}))'.format(k, i, j)
    ################################################################################################
    ########  8  ### VINCOLI FINESTRE TEMPORALI NODI
    for k in K:
        for i in N:
            m += a[i] <= T[i, k], 'Vinc_fines1({}_{})'.format(k, i)

    for k in K:
        for i in N:
            m += T[i, k] <= b[i], 'Vinc_fines2({}_{})'.format(k, i)

    ################################################################################################
    #########  9  ### VINCOLI TEMPORALI TRA PICKUP E DELIVERY
    for k in K:
        for i in P:
            m += T[i, k] + duration[i, n + i] + s[i] <= T[n + i, k], 'Pick_Deliv-Route({}_{})'.format(k, i)

    ################################################################################################
    ########  10  ### VINCOLI CARICO CON BIG M
    for k in K:
        for i in N:
            for j in N:
                if i == j:
                    continue
                m += ((L[i, k] + l[j] - L[j, k]) <= M2 * (1 - x[i, j, k])), 'Vinc_cap({}_({},{}))'.format(k, i, j)

    ################################################################################################
    #########  11  ### VINCOLI ATTIVAZIONE CARICO E RISPETTO CAPACITA VEICOLO PER PICKUP
    for k in K:
        for i in P:
            m += L[i, k] >= (l[i] * (xsum(x[i, j, k] for j in N if j != i))), 'Pickup_coerenza({}_{})'.format(k, i)
            m += (L[i, k] <= Cap[k]), 'Pickup_coerenza2({}_{})'.format(k, i)

    ################################################################################################
    ########  12  ### VINCOLI ATTIVAZIONE CARICO E RISPETTO CAPACITA VEICOLO PER DELIVERY
    for k in K:
        for i in D:
            m += L[i, k] <= (Cap[k] - l[i]) * (
                xsum(x[i, j, k] for j in N if j != i)), 'Pickup_limite_capacita({}_{})'.format(k, i)

    ################################################################################################
    ########  13  ### VINCOLI LIMITAZIONE ORARIO GIORNALIERO
    for k in K:
        m += xsum((s[i] + duration[i, j]) * x[i, j, k] for i in Nod for j in Nod if
                  i != j) <= max_turno, 'Vinc_turno({})'.format(k)

    ################################################################################################
    ########  14  ### DAL NODO ORIGINE NON POSSO ANDARE DIRETTAMENTE AD UN NODO DI DELIVERY
    for k in K:
        for j in Dd:
            m += x[Or[0], j, k] == 0, 'Vinc_no_Or_Node_Delivery({}_{})'.format(k, j)

    ################################################################################################
    ########  15  ### EVITO CICLO SU STESSO NODO SENZA FARE ROUTING
    for k in K:
        for i in Nod:
            m += x[i, i, k] == 0, 'Ciclo_nodo({}_{})'.format(k, i)

    ################################################################################################
    ########  16  ### NESSUN VEICOLO DEVE TORNARE ALL'ORIGINE
    for k in K:
        for i in N:
            m += x[i, 0, k] == 0, 'No_ritorno_origine({}_{})'.format(k, i)

    ################################################################################################
    ################################################################################################

    ################################################################################################
    ################################################################################################

    m.objective = minimize(xsum(travel_cost[i, j] * x[i, j, k] for i in Nod for j in Nod for k in K))

    m.max_gap = gap

    status = m.optimize(max_seconds=time_limit)

    var_results = []
    x_opt = []
    T_opt = []
    L_opt = []


    if status == OptimizationStatus.NO_SOLUTION_FOUND:
        status = "Nessuna soluzione trovata"
        performances = [m.objective_value, m.objective_bound, m.gap]

    if status == OptimizationStatus.OPTIMAL or status == OptimizationStatus.FEASIBLE:
        status = "problema risolto"
        performances = [m.objective_value, m.objective_bound, m.gap]

        # for t in x:
        #
        #     i = t[0]
        #     j = t[1]
        #     k = t[2]
        #     value = t.x


        for v in m.vars:
            var_results.append([v.name, v.x])

        var_results = pd.DataFrame.from_records(var_results, columns=["variable", "value"])

        x_opt = var_results[var_results['variable'].str.contains("x", na=False)]
        T_opt = var_results[var_results['variable'].str.contains("T", na=False)]
        L_opt = var_results[var_results['variable'].str.contains("L", na=False)]

        x_opt['value'] = x_opt['value'].apply(pd.to_numeric).astype(int)
        L_opt['value'] = L_opt['value'].apply(pd.to_numeric).astype(int)


    if status == OptimizationStatus.INFEASIBLE:
        performances = "INFEASIBLE"
        var_results = "INFEASIBLE"
        x_opt = "INFEASIBLE"
        T_opt = "INFEASIBLE"
        L_opt = "INFEASIBLE"

    return status, performances, var_results, x_opt, T_opt, L_opt


