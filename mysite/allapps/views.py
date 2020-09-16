# Create your views here.
from django.http import HttpResponse
from django.views.generic import TemplateView
from django.db.models import Sum
from .models import Client, Mix_unloading, Input_App1, Output_App1, Output_App1_detail
from .models import Truck, Mission, Input_App2, Output_App2, Output_App2_detail
from datetime import datetime, timedelta
from .SortingScheduler import sorting_model
from .VRP_OSM_DistTime import OSM
from .RoutePlanner import VRP_model
from .VRP_Heuristics import load_instance, heur01, heuristic_result_interpreter
from .VRP_results_interpreter import VRP_interpreter, matplolib_graph_plot
import pandas as pd


def index(request):
    return HttpResponse("You're at the REMIND project index.")


class HomeView(TemplateView):
    template_name = "front-end/home.html"


class App1_outputView(TemplateView):
    template_name = "front-end/app1_output.html"

    def get_context_data(self, request, **kwargs):
        context = super(TemplateView, self).get_context_data(request=request, **kwargs)
        context['App1_output'] = Output_App1.objects.all()
        context['App1_output_detail'] = Output_App1_detail.objects.all()
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)

        # context['App1_output_result'] = Output_App1.objects.filter(input_reference__horizon_LB=request.POST['horizon_LB'],
        #                                                       input_reference__horizon_UB=request.POST['horizon_UB'])



        get_id = list(Output_App1.objects.filter(input_reference__horizon_LB=request.POST['horizon_LB'],
                                                 input_reference__horizon_UB=request.POST['horizon_UB']))[0].id

        context['App1_output_result_detail'] = Output_App1_detail.objects.filter(id=get_id,
                                                                                 input_reference__horizon_LB=request.POST['horizon_LB'],
                                                                                 input_reference__horizon_UB=request.POST['horizon_UB'])

        result = Output_App1.objects.filter(id=get_id,
                                            input_reference__horizon_LB=request.POST['horizon_LB'],
                                            input_reference__horizon_UB=request.POST['horizon_UB']).first()



        start_date = datetime.strptime(request.POST['horizon_LB'], "%Y-%m-%d")
        end_date = datetime.strptime(request.POST['horizon_UB'], "%Y-%m-%d")

        deltadays = (end_date - start_date).days + 1
        working_shifts = ["mattina  ","pomeriggio"]
        days_list = []
        shifts_list = []
        for i in range(deltadays + 1):
            for shift in working_shifts:
                shifts_list.append(shift)
                days_list.append((start_date + timedelta(days=i)).strftime("%d/%m/%Y"))  #prova "%d %B, %Y"

        solution = {}

        solution["data_turno"] = days_list
        solution["first_sorting"] = eval(result.first_sorting)   #eval "evaluate" the string parsed as a Python expression. in this case turns the sting into a list
        solution["second_sorting"] = eval(result.second_sorting)
        solution["first_sort_operators"] = eval(result.first_sort_operators)
        solution["second_sort_operators"] = eval(result.second_sort_operators)
        solution["first_sort_amount"] = eval(result.first_sort_amount)
        solution["second_sort_amount"] = eval(result.second_sort_amount)

        solution["table_data"] = []
        for i in range(0, len(solution["first_sorting"])):
            # table data e' una lista di liste. ogni "linea" viene visualizzata dentro una row html
            solution["table_data"].append([days_list[i],
                                           shifts_list[i],
                                           solution["first_sorting"][i],
                                           solution["second_sorting"][i],
                                           solution["first_sort_operators"][i],
                                           solution["second_sort_operators"][i],
                                           solution["first_sort_amount"][i],
                                           solution["second_sort_amount"][i]])

        context["App1_output_result"] = solution

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

        first_sorting_new = []
        second_sorting_new = []
        first_sorting = y_opt.iloc[:, 0].to_list()
        second_sorting = y_opt.iloc[:, 1].to_list()
        for i in range(len(first_sorting)):
            if first_sorting[i] == 1:
                first_sorting_new.append("attivata")
            else:
                first_sorting_new.append(" - ")
            if second_sorting[i] == 1:
                second_sorting_new.append("attivata")
            else:
                second_sorting_new.append(" - ")

        output_app1.first_sorting = first_sorting_new
        output_app1.second_sorting = second_sorting_new

        # output_app1.first_sorting = y_opt.iloc[:, 0].to_list()
        # output_app1.second_sorting = y_opt.iloc[:, 1].to_list()

        output_app1.first_sort_operators = x_opt.iloc[:, 0].to_list()
        output_app1.second_sort_operators = x_opt.iloc[:, 1].to_list()

        output_app1.first_sort_amount = u_opt.iloc[:, 0].to_list()
        output_app1.second_sort_amount = u_opt.iloc[:, 1].to_list()

        output_app1.save()

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
        context['missioni_prev'] = Mission.objects.filter(date=request.POST['date'])

        # save to context last input "is_running" info for html print
        context['model_running'] = Output_App2_detail.objects.filter(input_reference__date=request.POST['date']).first

        input_post = request.POST

        input_app2 = Input_App2()
        input_app2.date = datetime.strptime(input_post['date'], "%Y-%m-%d")
        input_app2.time_cost = int(input_post['time_cost'])
        input_app2.distance_cost = int(input_post['distance_cost'])
        input_app2.save()

        missioni_previste = Mission.objects.filter(date=request.POST['date'])

        if missioni_previste.exists():
            # query_df = pd.DataFrame(list(missioni_previste.values('Client_origin', 'Client_destination', 'case_number')))
            query_list = list(missioni_previste)

            ID = 0
            description = 0

            Inno = list(Client.objects.filter(id_Client="Innocenti"))[0]
            time_info = [[Inno.timewindow_LB, Inno.timewindow_UB, Inno.service_time]]
            instance = [["Innocenti", ID, description, 41.9555, 12.7641, 0, 0]]

            for mission in query_list:
                ID += 1
                description += 1
                instance.append([str(mission.Client_origin), ID, description, float(mission.Client_origin.lat),
                                 float(mission.Client_origin.long), float(mission.case_number),
                                 int(mission.Client_origin.service_time)])
                time_info.append([mission.Client_origin.timewindow_LB, mission.Client_origin.timewindow_UB,
                                  mission.Client_origin.service_time])

            for mission in query_list:
                ID += 1
                description += 1
                instance.append(
                    [str(mission.Client_destination), ID, description, float(mission.Client_destination.lat),
                     float(mission.Client_destination.long), - float(mission.case_number),
                     int(mission.Client_destination.service_time)])
                time_info.append([mission.Client_destination.timewindow_LB, mission.Client_destination.timewindow_UB,
                                  mission.Client_destination.service_time])

            ID += 1
            description += 1
            instance.append(["Innocenti", ID, description, 41.9555, 12.7641, 0, 0])
            time_info.append([Inno.timewindow_LB, Inno.timewindow_UB, Inno.service_time])

            instance = pd.DataFrame(instance,
                                    columns=['node_name', "ID", "description", "lat", "long", "demand", "service time"])
            instance = instance.astype(
                {'node_name': str, 'ID': int, 'description': int, 'lat': float, 'long': float, 'demand': int,
                 'service time': int})

            demand = instance["demand"].to_list()
            instance_toOSM = instance[["ID", "description", "lat", "long"]]

            distance, duration = OSM(instance_toOSM)

            ## For debug purposes
            # instance_toOSM.to_excel("input_test.xlsx")
            # distance.to_excel("distance_test.xlsx")
            # duration.to_excel("duration_test.xlsx")

            trucks_info = []
            trucks_plates = []
            available_trucks = list(Truck.objects.filter(is_available=True))
            for truck in available_trucks:
                trucks_info.append(truck.load_capacity)
                trucks_plates.append([truck.head, truck.trailer])

            trucks_plates = pd.DataFrame(trucks_plates, columns=['head', "trailer"])
            trucks_plates = trucks_plates.astype({'head': str, 'trailer': str})

            solver = "GRB"  # GRB o CBC
            gap = 1e-4
            time_limit = 100

            output_app2_detail = Output_App2_detail(input_reference=input_app2)
            output_app2_detail.save()

            ### TO DO LIST
            # 1) Come permettere la scelta fra più solutori: una tabella che contiene quelli disponibili ? ==> selezione a tendina tra gli acquistati
            # 2) Come aggiungere come output dell'euristica le informazioni temporarli di visita dei nodi: arrivo e ripartenza
            # 3) Creare tabella anagrafica unità locali clienti con dati di lat e long + numerazione unità locale
            # 4) Usare  django-tables2 per il rendere delle tabelle di output della prima e seconda app ( link:  https://django-tables2.readthedocs.io/en/latest/pages/tutorial.html)
            # usare alternativamente result[2].to_html('df_result_table_'+str(count)+'.html')

            ## VRP_model
            status, performances, var_results, x_opt, t_opt, l_opt = VRP_model(distance, duration, demand, time_info,
                                                                               trucks_info, solver, gap, time_limit)
            VRP_results = VRP_interpreter(instance, trucks_plates, x_opt, t_opt, l_opt, distance, duration)

            ## VRP_heuristic
            data_instance = load_instance(distance, duration, demand, time_info, trucks_info)
            tours = heur01(data_instance)
            HEUR_results = heuristic_result_interpreter(instance, trucks_plates, tours, distance, duration)

            output_app2_detail.is_running = "completato"
            output_app2_detail.save()

            count = 0
            for result in VRP_results:

                # check if truck considered does not pull a trailer to properly query DB
                if result[1] == str(None):
                    truck_object = Truck.objects.filter(head__plate_number=result[0])[0]
                else:
                    truck_object = Truck.objects.filter(head__plate_number=result[0],
                                                        trailer__plate_number=result[1])[0]

                if isinstance(result[2], str) == True:

                    output_app2 = Output_App2(input_reference=input_app2)
                    output_app2.truck = Truck.objects.get(id=truck_object.id)
                    output_app2.truck_is_used = False

                    output_app2.visit_order = []
                    output_app2.node_name = []
                    output_app2.lat = []
                    output_app2.long = []
                    output_app2.load_unload = []
                    output_app2.arrival_time = []
                    output_app2.departure_time = []
                    output_app2.leaving_load = []

                    output_app2.save()
                    count += 1

                else:
                    output_app2 = Output_App2(input_reference=input_app2)
                    output_app2.truck = Truck.objects.get(id=truck_object.id)
                    output_app2.truck_is_used = True

                    output_app2.visit_order = result[2]["visit order"].to_list()
                    output_app2.node_name = result[2]["node name"].to_list()
                    output_app2.lat = result[2]["lat"].to_list()
                    output_app2.long = result[2]["long"].to_list()
                    output_app2.load_unload = result[2]["load_unload"].to_list()
                    output_app2.arrival_time = result[2]["arrival time"].to_list()
                    output_app2.departure_time = result[2]["departure time"].to_list()
                    output_app2.leaving_load = result[2]["leaving load"].to_list()

                    output_app2.save()

                    count += 1

        else:
            context['missioni_prev'] = "non sono previste missioni per la data selezionata"
            return self.render_to_response(context)

        return self.render_to_response(context)


class App2_outputView(TemplateView):
    template_name = "front-end/app2_output.html"

    def get_context_data(self, request, **kwargs):
        context = super(TemplateView, self).get_context_data(request=request, **kwargs)
        context['App2_output'] = Output_App2.objects.all()
        context['App2_output_detail'] = Output_App2_detail.objects.all()
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)

        # select input_reference id for selected date: selected id correspond to last input_reference id
        id = list(Output_App2.objects.filter(input_reference__date=request.POST['date']))[0].input_reference_id
        result = Output_App2.objects.filter(input_reference__date=request.POST['date'], input_reference__id=id)
        data = []
        for r in result:
            truck = {}
            if r.truck_is_used == True:

                truck["truck_is_used"] = True
                truck["visit_order"] = eval(r.visit_order)
                truck["node_name"] = eval(r.node_name)
                truck["lat"] = eval(r.lat)
                truck["long"] = eval(r.long)
                truck["load_unload"] = eval(r.load_unload)
                truck["arrival_time"] = eval(r.arrival_time)
                truck["departure_time"] = eval(r.departure_time)
                truck["leaving_load"] = eval(r.leaving_load)

                truck["table_data"] = []
                for i in range(0, len(truck["visit_order"])):
                    # table data e' una lista di liste. ogni "linea" viene visualizzata dentro una row html
                    truck["table_data"].append([truck["visit_order"][i],
                                                truck["node_name"][i],
                                                truck["lat"][i],
                                                truck["long"][i],
                                                truck["load_unload"][i],
                                                truck["arrival_time"][i],
                                                truck["departure_time"][i],
                                                truck["leaving_load"][i]])
                truck["truck"] = r.truck

            else:
                truck["truck_is_used"] = False
                truck["truck"] = r.truck
            data.append(truck)

        context["App2_output_result"] = data
        context['App2_output_result_detail'] = Output_App2_detail.objects.filter(
            input_reference__date=request.POST['date']).first

        return self.render_to_response(context)
