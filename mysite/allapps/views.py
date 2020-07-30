# Create your views here.
from django.http import HttpResponse
from django.views.generic import TemplateView
from allapps.models import Mission, Mix_unloading, Output_App1, Input_App1
from allapps.SortingScheduler import sorting_model

def index(request):
    return HttpResponse("You're at the REMIND project index.")

class HomeView(TemplateView):
    template_name = "front-end/home.html"
    
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
        context['scarichi_prev'] = Mix_unloading.objects.filter(date__gte=request.POST['horizon_LB'], date__lte=request.POST['horizon_UB'])
        
        scarichi_previsti = context['scarichi_prev']
        input_post = request.POST

        input_app1 = Input_App1()
        input_app1.horizon_LB = input_post['horizon_LB']
        input_app1.horizon_UB = input_post['horizon_UB']
        input_app1.dailyshifts   = input_post['dailyshifts']#.to_int()
        input_app1.shift_1_hours = input_post['shift_1_hours']
        input_app1.shift_2_hours = input_post['shift_2_hours']
        input_app1.shift_3_hours = input_post['shift_3_hours']
        input_app1.operator_wage = input_post['operator_wage']
        input_app1.max_operators = input_post['max_operators']
        input_app1.min_op_sort1 = input_post['min_op_sort1']
        input_app1.min_op_sort2 = input_post['min_op_sort2']
        input_app1.firstTO2nd_sort = input_post['firstTO2nd_sort']
        input_app1.setup_sort1 = input_post['setup_sort1']
        input_app1.setup_sort2 = input_post['setup_sort2']
        input_app1.overfill_treshold = input_post['overfill_treshold']
        input_app1.finalstock_treshold = input_post['finalstock_treshold']
        input_app1.sort1_capacity = input_post['sort1_capacity']
        input_app1.sort2_capacity = input_post['sort2_capacity']
        input_app1.sort1_maxstock = input_post['sort1_maxstock']
        input_app1.sort2_maxstock = input_post['sort2_maxstock']
        input_app1.save()

        #output_app1 = sorting_model(input_app1,scarichi_previsti)

        #context['results'] = output_app1
        #
        # output = Output_App1(first_sorting = True)
        # output_app1 = Output_App1(input_reference = input_app1)
        # output_app1.first_sort_operators = context['results']['x_operatori 1']
        # #le altre assegnazioni
        # output_app1.save()
        
        return self.render_to_response(context)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    