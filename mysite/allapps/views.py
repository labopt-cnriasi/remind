# Create your views here.
from django.http import HttpResponse
from django.views.generic import TemplateView
from django.db.models import Sum
from .models import Mission, Mix_unloading, Input_App1, Output_App1, Output_App1_detail
from datetime import datetime, timedelta
from .SortingScheduler import sorting_model
from .tables import Output_App1Table
from django.shortcuts import render



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

    # def output_list(self, request):
    #
    #     queryset = Output_App1.objects.filter(input_reference__horizon_LB=request.POST['horizon_LB'],
    #                                           input_reference__horizon_UB=request.POST['horizon_UB'])
    #     table = Output_App1Table(queryset)
    #
    #     return render(request, "app1_output.html", {
    #         "table": table
    #     })

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
