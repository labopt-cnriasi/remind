# Create your views here.
from django.http import HttpResponse
from django.views.generic import TemplateView
from django.db.models import Sum
from .models import Client, Mission, Mix_unloading, Input_App1, Output_App1, Output_App1_detail
from .models import Truck, Input_App2, Output_App2
from datetime import datetime, timedelta
from .SortingScheduler import sorting_model
from .VRP_OSM_DistTime import OSM
from .RoutePlanner import VRP_model
import pandas as pd


def index(request):
    return HttpResponse("You're at the REMIND project index.")


class HomeView(TemplateView):
    template_name = "front-end/home.html"



class App1_outputView(TemplateView):
    template_name = "front-end/app1_output.html"

    def get_context_data(self, request, **kwargs):
        context = super(TemplateView, self).get_context_data(request=request, **kwargs)
        context['app1_output'] = Output_App1.objects.all()
        context['app1_output_detail'] = Output_App1_detail.objects.all()
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)

        context['output_result'] = Output_App1.objects.filter(input_reference__horizon_LB=request.POST['horizon_LB'],
                                                              input_reference__horizon_UB=request.POST['horizon_UB'])

        context['output_result_detail'] = Output_App1_detail.objects.filter(input_reference__horizon_LB=request.POST['horizon_LB'],
                                                                            input_reference__horizon_UB=request.POST['horizon_UB'])
        return self.render_to_response(context)



class App1View(TemplateView):
    template_name = "front-end/app1.html"

    def get_context_data(self, request, **kwargs):
        context = super(TemplateView, self).get_context_data(request=request, **kwargs)
        context['missioni'] = Mission.objects.all()
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)
        print(request.POST)
        context['scarichi_prev'] = Mix_unloading.objects.filter(date__gte=request.POST['horizon_LB'],
                                                                date__lte=request.POST['horizon_UB'])

        input_post = request.POST

        input_app1 = Input_App1()
        input_app1.horizon_LB = datetime.strptime(input_post['horizon_LB'], "%Y-%m-%d")
        input_app1.horizon_UB = datetime.strptime(input_post['horizon_UB'], "%Y-%m-%d")
        input_app1.dailyshifts = int(input_post['dailyshifts'])
        input_app1.shift_1_hours = int(input_post['shift_1_hours'])
        input_app1.shift_2_hours = int(input_post['shift_2_hours'])
        input_app1.shift_3_hours = int(input_post['shift_3_hours'])
        input_app1.operator_wage = int(input_post['operator_wage'])
        input_app1.max_operators = int(input_post['max_operators'])
        input_app1.min_op_sort1 = int(input_post['min_op_sort1'])
        input_app1.min_op_sort2 = int(input_post['min_op_sort2'])
        input_app1.firstTO2nd_sort = int(input_post['firstTO2nd_sort'])
        input_app1.setup_sort1 = int(input_post['setup_sort1'])
        input_app1.setup_sort2 = int(input_post['setup_sort2'])
        input_app1.overfill_treshold = int(input_post['overfill_treshold'])
        input_app1.finalstock_treshold = int(input_post['finalstock_treshold'])
        input_app1.sort1_capacity = int(input_post['sort1_capacity'])
        input_app1.sort2_capacity = int(input_post['sort2_capacity'])
        input_app1.sort1_maxstock = int(input_post['sort1_maxstock'])
        input_app1.sort2_maxstock = int(input_post['sort2_maxstock'])
        input_app1.save()

        scarichi_previsti = Mix_unloading.objects.filter(date__gte=request.POST['horizon_LB'],
                                                         date__lte=request.POST['horizon_UB'])

        scarichi_previsti_shift_1 = scarichi_previsti.filter(working_shift=1)
        scarichi_previsti_shift_2 = scarichi_previsti.filter(working_shift=2)

        scarichi_previsti_shift_1 = scarichi_previsti_shift_1.order_by('date')
        scarichi_previsti_shift_2 = scarichi_previsti_shift_2.order_by('date')

        start_date = input_post['horizon_LB']
        end_date = input_post['horizon_UB']

        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

        deltadays = (end_date - start_date).days + 1
        P = 2
        TH = deltadays * P
        days_list = []
        for i in range(deltadays + 1):
            days_list.append(start_date + timedelta(days=i))

        Arrivals = [[], []]
        # for p in range(P):
        #     Arrivals[p] = np.arange(p, TH, P)
        #     p = p + 1

        for day in days_list:
            sum_shift_1 = 0
            query_1 = Mix_unloading.objects.filter(date=day, working_shift=1)
            if query_1.exists():
                sum_shift_1 = query_1.aggregate(Sum('quantity'))['quantity__sum']

            sum_shift_2 = 0
            query_2 = Mix_unloading.objects.filter(date=day, working_shift=2)
            if query_2.exists():
                sum_shift_2 = query_2.aggregate(Sum('quantity'))['quantity__sum']

            Arrivals[0].append(sum_shift_1)
            Arrivals[1].append(sum_shift_2)

        output_app1_detail = Output_App1_detail(input_reference=input_app1)
        output_app1_detail.save()

        y_opt, x_opt, u_opt = sorting_model(input_app1, Arrivals)

        output_app1_detail.is_running = "completato"
        output_app1_detail.save()

        output_app1 = Output_App1(input_reference=input_app1)

        output_app1.first_sorting = y_opt.iloc[:, 0].to_list()
        output_app1.second_sorting = y_opt.iloc[:, 1].to_list()

        output_app1.first_sort_operators = x_opt.iloc[:, 0].to_list()
        output_app1.second_sort_operators = x_opt.iloc[:, 1].to_list()

        output_app1.first_sort_amount = u_opt.iloc[:, 0].to_list()
        output_app1.second_sort_amount = u_opt.iloc[:, 1].to_list()

        output_app1.save()

        # result = [y_opt, x_opt, u_opt]
        # context['result'] = result

        return self.render_to_response(context)



class App2View(TemplateView):
    template_name = "front-end/app2.html"

    def get_context_data(self, request, **kwargs):
        context = super(TemplateView, self).get_context_data(request=request, **kwargs)
        context['missioni'] = Mission.objects.all()
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)
        print(request.POST)
        context['missioni_prev'] = Mission.objects.filter(date = request.POST['date'])

        input_post = request.POST

        input_app2 = Input_App2()
        input_app2.date = datetime.strptime(input_post['date'], "%Y-%m-%d")
        input_app2.time_cost = int(input_post['time_cost'])
        input_app2.distance_cost = int(input_post['distance_cost'])
        input_app2.save()

        missioni_previste = Mission.objects.filter(date=request.POST['date'])

        if missioni_previste.exists():
            query_df = pd.DataFrame(list(missioni_previste.values('Client_origin', 'Client_destination', 'case_number')))
            query_list = list(missioni_previste)

        ID = 0
        description = 0

        Inno = list(Client.objects.filter(id_Client = "Innocenti"))[0]
        time_info = [[Inno.timewindow_LB, Inno.timewindow_UB, Inno.service_time]]
        instance = [["Innocenti",ID,description,41.9555,12.7641,0]]
        for mission in query_list:
            ID += 1
            description +=1
            instance.append([str(mission.Client_origin), ID, description, float(mission.Client_origin.lat), float(mission.Client_origin.long), float(mission.case_number)])
            time_info.append([mission.Client_origin.timewindow_LB,mission.Client_origin.timewindow_UB,mission.Client_origin.service_time])

        for mission in query_list:
            ID += 1
            description +=1
            instance.append([str(mission.Client_destination), ID, description, float(mission.Client_destination.lat), float(mission.Client_destination.long), - float(mission.case_number)])
            time_info.append([mission.Client_destination.timewindow_LB,mission.Client_destination.timewindow_UB,mission.Client_destination.service_time])

        ID += 1
        description += 1
        instance.append(["Innocenti",ID,description,41.9555,12.7641,0])
        time_info.append([Inno.timewindow_LB, Inno.timewindow_UB, Inno.service_time])

        instance = pd.DataFrame(instance,columns =['node_name',"ID","description","lat","long","demand"])
        instance = instance.astype({'node_name': str, 'ID': int, 'description': int, 'lat':float, 'long':float, 'demand': int})

        demand = instance["demand"].to_list()
        instance_toOSM = instance[["ID","description","lat","long"]]

        instance_toOSM.to_excel("input_test.xlsx")

        distance, duration = OSM(instance_toOSM)

        trucks_info = []
        available_trucks = list(Truck.objects.filter(is_available = True))
        for truck in available_trucks:
            trucks_info.append(truck.load_capacity)

        solver = "GRB"  # GRB o CBC
        gap = 1e-4
        time_limit = 100

        status, performances, var_results, x_opt, T_opt, L_opt = VRP_model(distance,duration,demand,time_info,trucks_info, solver, gap, time_limit)

        print("ciao")

        return self.render_to_response(context), x_opt, T_opt, L_opt


class App2_outputView(TemplateView):
    template_name = "front-end/app2_output.html"

    def get_context_data(self, request, **kwargs):
        context = super(TemplateView, self).get_context_data(request=request, **kwargs)
        context['app1_output'] = Output_App1.objects.all()
        context['app1_output_detail'] = Output_App1_detail.objects.all()
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)

        context['output_result'] = Output_App2.objects.all()

        return self.render_to_response(context)


