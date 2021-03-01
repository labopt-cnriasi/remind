"""
Created on Mon Mar 23 17:06:41 2020

@author: diego
"""
from mip import *
import os
import pandas as pd
import numpy as np
import subprocess

# from .Configurations import Gurobi_license_path
# os.environ['GRB_LICENSE_FILE'] = Gurobi_license_path


#list_of_inputs
#
# P : number of working shifts
# T : time horizon partitioned in time shifts [int]
# C : hourly cost of each operator [int]
# sigma_t : working hours for time t determined by the corresponding shift p [..list..]
# C_t = C*sigma_t : cost of each operator at time t [..list..]
# f_j : set-up cost of sorting stage j [..list..]
# a_t : quantity of material in kg unloaded from trucks at time t [..list..]
# alpha_j : percentage of waste processed in stage j-1, received in input by buffer j [..list..]
# S_j : maximum inventory capacity of the sorting stage buffer j [..list..]
# LC_j : critical stock level threshold of buffer j [..list..]
# rho_j : fraction of material allowed to be left at buffer j at the end of time horizon [..list..]
# K_j : single operator hourly production capacity [kg/h] of sorting stage j [..list..]
# SK_{j,t} = K_j*\sigma_t : operator sorting capacity in sorting stage j, at time t [..list..]
# M : maximum number of operators available in each time shift [int]
# E_j : minimum number of operators to be employed in each time shift of stage j [..list..]
# h_j^i : slope of the i-th part of linearization of the buffer j stock cost curve [..list..]


def sorting_model(input_app,arrivals):

    GapTol = 1e-3
    TimeLimit = 600

    deltadays = (input_app.horizon_UB - input_app.horizon_LB).days + 1

    J = 2 #two default sorting stages
    P = input_app.dailyshifts
    TH = deltadays * P
    sigma = [input_app.shift_1_hours,input_app.shift_2_hours,input_app.shift_3_hours]
    sigma = sigma[:P]

    T = [[]] * P
    for p in range(P):
        T[p] = np.arange(p, TH, P)
        p = p + 1

    alpha = [1,input_app.firstTO2nd_sort/100]
    S = [input_app.sort1_maxstock,input_app.sort2_maxstock]
    K = [input_app.sort1_capacity,input_app.sort2_capacity]
    SK = np.zeros((J,P)) #Selection single worker's shiftly productive capacity
    for j in range(J):
        for p in range(P):
            SK[j,p] = K[j] * sigma[p]

    ro = [input_app.finalstock_treshold] * J

    LC = []
    for j in range(J):
        LC.append((input_app.overfill_treshold/100) * S[j])

    C = input_app.operator_wage  # single worker's hourly cost (euro/h)
    C_t = np.zeros(TH)  # single worker's cost for the whole shift p (euro/shift)
    for t in range(TH):
        if t in T[0]:
            C_t[t] = C * sigma[0]
        else:
            C_t[t] = C * sigma[1]

    E = [input_app.min_op_sort1,input_app.min_op_sort2]
    M = input_app.max_operators

    setup_cost = [input_app.setup_sort1,input_app.setup_sort1]

    # Arrivals
    a = np.zeros(TH)
    i = 0
    j = 0
    for t in range(TH):
        if t in T[0]:
            a[t] = arrivals[0][i]
            i += 1

        if t in T[1]:
            a[t] = arrivals[1][j]
            j += 1
    base = 20
    prec = 2

    def rounding(a, prec, base):
        return base * (a / base).round().round(prec)

    a = rounding(a, prec, base)
    a = dict(enumerate(a))



    # Storage costs
    cost_labels = ['null', 'under balance', 'balanced', 'over balance']
    dh = np.zeros((J, 2))

    dh[0, 0] = 0.009  # over the balance point between production and storage costs
    dh[0, 1] = 0.4
    dh[1, 0] = 0.005
    dh[1, 1] = 0.2
    for j in range(2, J):
        dh[j, 0] = 0.005
        dh[j, 1] = 0.2

    C_prod = True
    C_stock = True

    ######## Model ###########################################################

    # Gurobi_cl_path in Configurations.py obtained by "which gurobi_cl" in terminal prompt.
    from .Configurations import Gurobi_cl_path

    solver = 'GRB'
    if solver == 'GRB':
        try:
            # gurobi_cl path to include in Configurations.py can be retrieved
            # by entering "which gurobi_cl" in a command/terminal prompt. Please take a look to Configurations.py
            subprocess.run(Gurobi_cl_path, stdout=subprocess.PIPE).stdout.decode('utf-8')
            m = Model("WFA", sense=MINIMIZE, solver_name=solver)
        except Exception as e:
            print(e)
            solver = 'CBC'
            m = Model("WFA", sense=MINIMIZE, solver_name=solver)
    else:
        solver = 'CBC'
        m = Model("WFA", sense=MINIMIZE, solver_name=solver)

    # VARIABLES

    # workforce to be employed on selection stag j
    if C_prod == True:
        x = {(j, t): m.add_var(lb=0, var_type=INTEGER, obj=C_t[t], name="x_{}_{}".format(j, t)) for j in range(J) for t in range(TH)}
    else:
        x = {(j, t): m.add_var(lb=0, var_type=INTEGER, name="x_{}_{}".format(j, t)) for j in range(J) for t in range(TH)}

    # quantity preoccesed in a shift
    u = {(j, t): m.add_var(lb=0, var_type=CONTINUOUS, name="u_{}_{}".format(j, t)) for j in range(J) for t in range(TH)}

    # selection stage start
    if C_prod == True:
        y = {(j, t): m.add_var(lb=0, ub=1, obj=setup_cost[j], var_type=BINARY, name="y_{}_{}".format(j, t)) for j in range(J) for t in range(TH)}
    else:
        y = {(j, t): m.add_var(lb=0, ub=1, var_type=BINARY, name="y_{}_{}".format(j, t)) for j in range(J) for t in range(TH)}
    # These are the stock variables regarding the j-th selection stage
    if C_stock == True:
        I = {(j, t): m.add_var(lb=0, ub=S[j], var_type=CONTINUOUS, name="I_{}_{}".format(j, t)) for j in range(J) for t in range(TH)}  # stock quantity
        I_1 = {(j, t): m.add_var(lb=0, ub=LC[j], var_type=CONTINUOUS, obj=dh[j, 0], name="I_1_{}_{}".format(j, t)) for j in range(J) for t in range(TH)}  # stock quantity below critical level
        I_2 = {(j, t): m.add_var(lb=0, var_type=CONTINUOUS, obj=dh[j, 1], name="I_2_{}_{}".format(j, t)) for j in range(J) for t in range(TH)}  # stock quantity above critical level
    else:
        I = {(j, t): m.add_var(lb=0, ub=S[j], var_type=CONTINUOUS, name="I_{}_{}".format(j, t)) for j in range(J) for t in range(TH)}  # stock quantity

    # binary variable concerning the overcoming of critical level
    if C_stock == True:
        w = {(j, t): m.add_var(lb=0, ub=1, var_type=BINARY, name="w_{}_{}".format(j, t)) for j in range(J) for t in range(TH)}

    # CONSTRAINTS

    # ( 2 ) #######################################################################################
    for j in range(J):
        for t in range(TH):
            # Planned workforce must not exceed the maximum number of available workforce
            m += x[j, t] <= M * y[j, t], "bigM_{}_{}".format(j, t)
            # For each period there is a minimum fixed number of workers for selection stage j
            m += x[j, t] >= E[j] * y[j, t], 'minWF_{}_{}'.format(j, t)
    ###############################################################################################

    # ( 3 ) #######################################################################################
    for t in range(TH):
        m += xsum(x[j, t] for j in range(J)) <= M, "Wforce_bound_{}".format(t)
    ###############################################################################################

    # ( 4 ) #######################################################################################
    # These constraints bound the processed quantity to the maximum production capacity
    # over the corresponding shift as a function of the workforce allocation
    for j in range(J):
        for t in range(TH):
            if t in T[0]:
                m += u[j, t] <= SK[j, 0] * x[j, t], "prod_{}_{}".format(j, t)
            if t in T[1]:
                m += u[j, t] <= SK[j, 1] * x[j, t], "prod_{}_{}".format(j, t)
    ###############################################################################################

    # not included in paper formulation ###########################################################
    # Starting level of the first storage
    for j in range(J):
        if j == 0:
            m += I[j, 0] == a[0] - u[0, 0], "initializzation_{}".format(j)
        else:
            m += I[j, 0] == alpha[j] * u[j - 1, 0], "initializzation_{}".format(j)
    ###############################################################################################

    # ( 5 ) & ( 6 ) ################################################################################
    # Flow balance equation for 1st and 2nd selection
    for j in range(J):
        for t in range(1, TH):
            if j == 0:
                m += I[j, t] == I[j, t - 1] + a[t] - u[j, t], "balance_{}_{}".format(j, t)
            else:
                m += I[j, t] == I[j, t - 1] + alpha[j] * u[j - 1, t] - u[j, t], "balance_{}_{}".format(j, t)


###############################################################################################

    if C_stock == True:
        # ( 7 ) #######################################################################################
        # The constraints below are needed to linearize the stock costs relating to selection stages
        for j in range(J):
            for t in range(TH):
                m += I[j, t] == I_1[j, t] + I_2[j, t], "linear_stock_{}_{}".format(j, t)
            ###############################################################################################

            # ( 8 ) & ( 9 ) ###############################################################################
            for t in range(TH):
                m += I_1[j, t] >= LC[j] * w[j, t], "v1_{}_{}".format(j, t)
                m += I_2[j, t] <= (S[j] - LC[j]) * w[j, t], "v2_{}_{}".format(j, t)
        ###############################################################################################

    # ( 10 ) ######################################################################################
    # These two constraints set the stock level over the last period below a decided level both for the first and second stock level
    for j in range(J):
        m += I[j, TH - 1] <= np.floor(ro[j] * LC[j]), "end_{}_{}".format(j, TH - 1)
    ###############################################################################################

    m.objective = minimize(xsum(C_t[t] * x[j, t] for j in range(J) for t in range(TH)) +
                           xsum(setup_cost[j] * y[j, t] for j in range(J) for t in range(TH)) +
                           xsum(dh[j, 0] * I_1[j, t] + dh[j, 1] * I_2[j, t] for j in range(J) for t in range(TH)))

    m.max_gap = GapTol
    status = m.optimize(max_seconds=TimeLimit)

    var_results = []
    y_opt = []
    x_opt = []
    u_opt = []

    if status == OptimizationStatus.NO_SOLUTION_FOUND:
        status = "infeasible"
        performances = [m.objective_value, m.objective_bound, m.gap]

    if status == OptimizationStatus.OPTIMAL or status == OptimizationStatus.FEASIBLE:
        status = "optimal"
        performances = [m.objective_value, m.objective_bound, m.gap]

        for v in m.vars:
            var_results.append([v.name, v.x])

        var_results = pd.DataFrame.from_records(var_results, columns=["variable", "value"])

        y_opt = var_results[var_results['variable'].str.contains("y", na=False)]
        x_opt = var_results[var_results['variable'].str.contains("x", na=False)]
        u_opt = var_results[var_results['variable'].str.contains("u", na=False)]

        y_opt['value'] = y_opt['value'].apply(pd.to_numeric).astype(int)
        x_opt['value'] = x_opt['value'].apply(pd.to_numeric).astype(int)
        u_opt['value'] = u_opt['value'].apply(pd.to_numeric).astype(int)

        y_opt_1t = y_opt[y_opt['variable'].str.contains("y_0", na=False)]['value'].tolist()
        y_opt_2t = y_opt[y_opt['variable'].str.contains("y_1", na=False)]['value'].tolist()
        y_opt = pd.DataFrame.from_records([y_opt_1t,y_opt_2t]).T

        x_opt_1t = x_opt[x_opt['variable'].str.contains("x_0", na=False)]['value'].tolist()
        x_opt_2t = x_opt[x_opt['variable'].str.contains("x_1", na=False)]['value'].tolist()
        x_opt = pd.DataFrame.from_records([x_opt_1t,x_opt_2t]).T

        u_opt_1t = u_opt[u_opt['variable'].str.contains("u_0", na=False)]['value'].tolist()
        u_opt_2t = u_opt[u_opt['variable'].str.contains("u_1", na=False)]['value'].tolist()
        u_opt = pd.DataFrame.from_records([u_opt_1t,u_opt_2t]).T


    if status == OptimizationStatus.INFEASIBLE:
        performances = "INFEASIBLE"
        var_results = "INFEASIBLE"
        x_opt = "INFEASIBLE"
        T_opt = "INFEASIBLE"
        L_opt = "INFEASIBLE"

    return status, y_opt, x_opt, u_opt



##################################################################################################




