"""
Created on Mon Mar 23 17:06:41 2020

@author: diego
"""

import os
os.environ['GRB_LICENSE_FILE'] = '/home/diego/gurobi.lic'
import gurobi as GRB
from gurobipy import *
import pandas as pd
import numpy as np

cwd = os.getcwd()  # Get the current working directory (cwd)
files = os.listdir(cwd)  # Get all the files in that directory

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



def sorting_model(input_app,scarichi_previsti):

    GapTol = 1e-3
    TimeLimit = 600

    deltadays = (input_app.horizon_UB - input_app.horizon_LB).days + 1
    TH = deltadays*P

    J = 2 #two default sorting stages
    P = input_app.dailyshifts
    sigma = [input_app.shift_1_hours,input_app.shift_2_hours,input_app.shift_3_hours]
    sigma = sigma[:P]

    T = [[]] * P
    for p in range(P):
        T[p] = np.arange(p, TH, P)
        p = p + 1

    alpha = [1,input_app.firstTO2nd_sort]
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


    # VARIABLES

    # workforce to be employed on selection stag j
    if C_prod == True:
        x = {(j, t): m.addVar(lb=0, vtype=GRB.INTEGER, obj=C_t[t], name="x[{},{}]".format(j, t)) for j in range(J) for t
             in range(TH)}
    else:
        x = {(j, t): m.addVar(lb=0, vtype=GRB.INTEGER, name="x[{},{}]".format(j, t)) for j in range(J) for t in
             range(TH)}

    # quantity preoccesed in a shift
    u = {(j, t): m.addVar(lb=0, vtype=GRB.CONTINUOUS, name="u[{},{}]".format(j, t)) for j in range(J) for t in
         range(TH)}

    # selection stage start
    if C_prod == True:
        y = {(j, t): m.addVar(lb=0, ub=1, obj = setup_cost[j], vtype=GRB.BINARY, name="y[{},{}]".format(j, t)) for j in range(J) for
             t in range(TH)}
    else:
        y = {(j, t): m.addVar(lb=0, ub=1, vtype=GRB.BINARY, name="y[{},{}]".format(j, t)) for j in range(J) for t in
             range(TH)}
    # These are the stock variables regarding the j-th selection stage
    if C_stock == True:
        I = {(j, t): m.addVar(lb=0, ub=S[j], vtype=GRB.CONTINUOUS, name="I_[{}_{}]".format(j, t)) for j in range(J) for
             t in range(TH)}  # stock quantity
        I_1 = {(j, t): m.addVar(lb=0, ub=LC[j], vtype=GRB.CONTINUOUS, obj=dh[j, 0], name="I_1_[{}_{}]".format(j, t)) for
               j in range(J) for t in range(TH)}  # stock quantity below critical level
        I_2 = {(j, t): m.addVar(lb=0, vtype=GRB.CONTINUOUS, obj=dh[j, 1], name="I_2_[{}_{}]".format(j, t)) for j in
               range(J) for t in range(TH)}  # stock quantity above critical level
    else:
        I = {(j, t): m.addVar(lb=0, ub=S[j], vtype=GRB.CONTINUOUS, name="I_[{}_{}]".format(j, t)) for j in range(J) for
             t in range(TH)}  # stock quantity

    # binary variable concerning the overcoming of critical level
    if C_stock == True:
        w = {(j, t): m.addVar(lb=0, ub=1, vtype=GRB.BINARY, name="w[{},{}]".format(j, t)) for j in range(J) for t in
             range(TH)}

    # CONSTRAINTS

    # ( 2 ) #######################################################################################
    for j in range(J):
        for t in range(TH):
            # Planned workforce must not exceed the maximum number of available workforce
            m.addConstr(x[j, t] <= M * y[j, t], name="bigM_{}_{}".format(j, t))
            # For each period there is a minimum fixed number of workers for selection stage j
            m.addConstr(x[j, t] >= E[j] * y[j, t], name='minWF_{}_{}'.format(j, t))
    ###############################################################################################

    # ( 3 ) #######################################################################################
    for t in range(TH):
        m.addConstr(quicksum(x[j, t] for j in range(J)) <= M, name="Wforce_bound_{}".format(t))
    ###############################################################################################

    # ( 4 ) #######################################################################################
    # These constraints bound the processed quantity to the maximum production capacity
    # over the corresponding shift as a function of the workforce allocation
    for j in range(J):
        for t in range(TH):
            if t in T[0]:
                m.addConstr(u[j, t] <= SK[j, 0] * x[j, t], name="prod_{}_{}".format(j, t))
            if t in T[1]:
                m.addConstr(u[j, t] <= SK[j, 1] * x[j, t], name="prod_{}_{}".format(j, t))
    ###############################################################################################

    # not included in paper formulation ###########################################################
    # Starting level of the first storage
    for j in range(J):
        if j == 0:
            m.addConstr(I[j, 0] == a[0] - u[0, 0], name="initializzation_{}".format(j))
        else:
            m.addConstr(I[j, 0] == alpha[j] * u[j - 1, 0], name="initializzation_{}".format(j))
    ###############################################################################################

    # ( 5 ) & ( 6 ) ################################################################################
    # Flow balance equation for 1st and 2nd selection
    for j in range(J):
        for t in range(1, TH):
            if j == 0:
                m.addConstr(I[j, t] == I[j, t - 1] + a[t] - u[j, t], name="balance_{}_{}".format(j, t))
            else:
                m.addConstr(I[j, t] == I[j, t - 1] + alpha[j] * u[j - 1, t] - u[j, t],
                            name="balance_{}_{}".format(j, t))
    ###############################################################################################

    if C_stock == True:
        # ( 7 ) #######################################################################################
        # The constraints below are needed to linearize the stock costs relating to selection stages
        for j in range(J):
            for t in range(TH):
                m.addConstr(I[j, t] == I_1[j, t] + I_2[j, t], name="linear_stock_{}_{}".format(j, t))
            ###############################################################################################

            # ( 8 ) & ( 9 ) ###############################################################################
            for t in range(TH):
                m.addConstr(I_1[j, t] >= LC[j] * w[j, t], name="v1_{}_{}".format(j, t))
                m.addConstr(I_2[j, t] <= (S[j] - LC[j]) * w[j, t], name="v2_{}_{}".format(j, t))
        ###############################################################################################

    # ( 10 ) ######################################################################################
    # These two constraints set the stock level over the last period below a decided level both for the first and second stock level
    for j in range(J):
        m.addConstr(I[j, TH - 1] <= np.floor(ro[j] * LC[j]), name="end_{}_{}".format(j, TH - 1))
    ###############################################################################################

    m.modelSense = GRB.MINIMIZE
    m.update()

    # m.Params.ConcurrentMIP = 1
    m.Params.MIPGap = GapTol
    m.Params.Threads = 4  # thread = m.setParam(GRB.Param.Threads, 1)
    m.Params.timelimit = TimeLimit  # timelimit = m.setParam(GRB.Param.TimeLimit, 3600.0)
    m.optimize()
    status = m.status
    Runtime = m.Runtime
    print('Runtime was ', Runtime)

    ################################################# RESULTS #################################################

    if status == 2:  # OPTIMAL
        name_lp = "WFA_test_" + str(TH) + '_' + type_A + '_' + cost_labels[3] + " storage costs.lp"
        m.write(name_lp)
        optObjVal = m.ObjVal
        bestObjBound = m.ObjBound
        IterCount = m.IterCount
        NodeCount = m.NodeCount
        NumConstrs = m.NumConstrs
        NumVars = m.NumVars
        NumBinVar = m.NumBinVars
        NumIntVar = m.NumIntVars
        gap = m.MIPGap
        status = "optimal"
        m.write('WFA_Diego.lp')
    elif status == 3:  # INFEASIBLE
        m.computeIIS()
        name_ilp = "WFA_test_IIS_" + str(TH) + '_' + type_A + '_' + cost_labels[3] + " storage costs.ilp"
        m.write(name_ilp)
        optObjVal = "Infeasible"
        bestObjBound = "Infeasible"
        Runtime = "Infeasible"
        IterCount = "Infeasible"
        NodeCount = "Infeasible"
        NumQConstrs = "Infeasible"
        NumVars = "Infeasible"
        NumBinVar = "Infeasible"
        NumIntVar = "Infeasible"
        gap = "Infeasible"
        status = "Infeasible"
        return "Infeasible", "Infeasible", "Infeasible", "Infeasible", "Infeasible", "Infeasible", "Infeasible", "Infeasible", "Infeasible", "Infeasible", "Infeasible", "Infeasible"
    elif status == 9:  # TIME-LIMIT
        optObjVal = m.getAttr(GRB.Attr.ObjVal)
        bestObjBound = m.getAttr(GRB.Attr.ObjBound)
        IterCount = m.getAttr(GRB.Attr.IterCount)
        NodeCount = m.getAttr(GRB.Attr.NodeCount)
        NumConstrs = m.getAttr(GRB.Attr.NumConstrs)
        NumVars = m.getAttr(GRB.Attr.NumVars)
        NumBinVar = m.getAttr(GRB.Attr.NumBinVars)
        NumIntVar = m.getAttr(GRB.Attr.NumIntVars)
        gap = m.MIPGap
        status = "Time limit reached"
        m.write('WFA_Diego.lp')
    else:
        altern_status = status
        print("Optimization stopped with status = {}".format(altern_status))

    #################################################

    ############# Uncomment if you want to save excel files for graphs  #############

    if status == "optimal":

        a = pd.Series(a)

        I = pd.Series(I)

        if C_stock == True:
            I_1 = pd.Series(I_1)
            I_2 = pd.Series(I_2)
            w = pd.Series(w)
            I_1_opt = []
            I_2_opt = []
            w_opt = []

        y = pd.Series(y)
        x = pd.Series(x)
        u = pd.Series(u)

        I_opt = []
        y_opt = []
        x_opt = []
        u_opt = []

        for j in range(J):

            I_opt.append(I[j].apply(lambda x: x.X))

            if C_stock == True:
                I_1_opt.append(I_1[j].apply(lambda x: x.X))
                I_2_opt.append(I_2[j].apply(lambda x: x.X))
                w_opt.append(w[j].apply(lambda x: x.X))

            y_opt.append(y[j].apply(lambda x: x.X))
            x_opt.append(x[j].apply(lambda x: x.X))
            u_opt.append(u[j].apply(lambda x: x.X))

        a = pd.DataFrame(a)

        I_opt = pd.DataFrame(I_opt).transpose()

        if C_stock == True:
            I_1_opt = pd.DataFrame(I_1_opt).transpose()
            I_2_opt = pd.DataFrame(I_2_opt).transpose()
            w_opt = pd.DataFrame(w_opt).transpose()

        y_opt = pd.DataFrame(y_opt).transpose()
        x_opt = pd.DataFrame(x_opt).transpose()
        u_opt = pd.DataFrame(u_opt).transpose()

        opt_values_list = [a]
        opt_val_columns = ["arrivals"]
        for j in range(J):
            # I
            opt_values_list.append(I_opt.iloc[:, j])
            opt_val_columns.append("I_j=" + str(j + 1))
            # I_1
            # opt_values_list.append(I_1_opt.iloc[:,j])
            # opt_val_columns.append("I_1_j="+str(j+1))
            # I_2
            # opt_values_list.append(I_2_opt.iloc[:,j])
            # opt_val_columns.append("I_2_j="+str(j+1))
            # y
            opt_values_list.append(y_opt.iloc[:, j])
            opt_val_columns.append("y_j=" + str(j + 1))
            # x
            opt_values_list.append(x_opt.iloc[:, j])
            opt_val_columns.append("x_j=" + str(j + 1))
            # u
            opt_values_list.append(u_opt.iloc[:, j])
            opt_val_columns.append("u_j=" + str(j + 1))
            # w
            opt_values_list.append(w_opt.iloc[:, j])
            opt_val_columns.append("w_j=" + str(j + 1))

        opt_values = pd.concat(opt_values_list, axis=1)
        opt_values = round(opt_values, 2)
        opt_values.columns = opt_val_columns
        opt_values.to_excel(
            "Output WFA" + "_J = " + str(J) + "_TH = " + str(TH) + '_' + type_A + '_' + cost_labels[3] + ".xlsx")

    else:
        opt_values = "no output values found"

    #################################################
    m.update()

    return status, gap, optObjVal, bestObjBound, Runtime, IterCount, NodeCount, NumConstrs, NumVars, NumBinVar, NumIntVar, opt_values


##################################################################################################




