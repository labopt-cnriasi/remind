from django.contrib import admin

# Register your models here.
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from allapps.models import Client, UnitaLocale, Carrier, Transporter, Truck, Cer, Mission, Fir, Mix_unloading
from allapps.models import Input_App1, Output_App1, Output_App1_detail, Input_App2, Output_App2, Output_App2_detail
from .forms import *


##############################################################################
class ClientResource(resources.ModelResource):
    class Meta:
        model = Client


class ClientAdmin(ImportExportModelAdmin):
    resource_class = ClientResource
    search_fields = ['id_Client', 'kind']
    list_display = ['id_Client', 'kind']


##############################################################################
class CarrierResource(resources.ModelResource):
    class Meta:
        model = Carrier


class CarrierAdmin(ImportExportModelAdmin):
    class Meta:
        model = Carrier

    resource_class = CarrierResource
    list_display = ['id_Carrier', 'address']


##############################################################################
class TransporterResource(resources.ModelResource):
    class Meta:
        model = Transporter


class TransporterAdmin(ImportExportModelAdmin):
    class Meta:
        model = Transporter

    resource_class = TransporterResource
    list_display = ['plate_number', 'trasporter_type', 'carrier_name', 'add_trailer']


##############################################################################

class TruckResource(resources.ModelResource):
    class Meta:
        model = Truck


class TruckAdmin(ImportExportModelAdmin):
    class Meta:
        model = Truck

    resource_class = TruckResource
    list_display = ['head', 'trailer', 'load_capacity', 'is_available']
    search_fields = ['head__plate_number', 'trailer__plate_number']


##############################################################################
class CerResource(resources.ModelResource):
    class Meta:
        model = Cer


class CerAdmin(ImportExportModelAdmin):
    class Meta:
        model = Cer

    resource_class = CerResource
    list_display = ['id_cer', 'description']


##############################################################################
class MissionAdmin(ImportExportModelAdmin):
    class Meta:
        model = Mission

    form = MissionForm
    list_display = ['date', 'Client_origin', 'Client_destination','case_number']
    search_fields = ['Client_origin__id_Client', 'Client_destination__id_Client']
    autocomplete_fields = ['Client_origin', 'Client_destination']


##############################################################################
class FirResource(resources.ModelResource):
    class Meta:
        model = Fir


class FirAdmin(ImportExportModelAdmin):
    class Meta:
        model = Fir

    resource_class = FirResource
    list_display = ['fir_number', 'exit_id', 'cer', 'net_weight', 'id_producer',
                    'id_disposer', 'id_carrier', 'plate_number_truck', 'plate_number_trailer']


##############################################################################
class Mix_unloadingAdmin(ImportExportModelAdmin):
    class Meta:
        model = Mix_unloading

    list_display = ['date', 'id_Client']

    form = MissionForm


##############################################################################
class Input_App1Resource(resources.ModelResource):
    class Meta:
        model = Input_App1


class Input_App1Admin(ImportExportModelAdmin):
    class Meta:
        model = Input_App1

    list_display = ['horizon_LB', 'horizon_UB', 'dailyshifts', 'shift_1_hours',
                    'shift_2_hours', 'shift_3_hours', 'operator_wage', 'max_operators',
                    'min_op_sort1', 'min_op_sort2', 'firstTO2nd_sort', 'setup_sort1',
                    'setup_sort2', 'overfill_treshold', 'finalstock_treshold',
                    'sort1_capacity', 'sort2_capacity', 'sort1_maxstock', 'sort2_maxstock']
    search_fields = ['horizon_LB', 'horizon_UB', 'dailyshifts', 'shift_1_hours',
                     'shift_2_hours', 'shift_3_hours', 'operator_wage', 'max_operators',
                     'min_op_sort1', 'min_op_sort2', 'firstTO2nd_sort', 'setup_sort1',
                     'setup_sort2', 'overfill_treshold', 'finalstock_treshold',
                     'sort1_capacity', 'sort2_capacity', 'sort1_maxstock', 'sort2_maxstock']


##############################################################################
class Output_App1Resource(resources.ModelResource):
    class Meta:
        model = Output_App1

class Output_App1Admin(ImportExportModelAdmin):
    class Meta:
        model = Output_App1

    list_display = ['input_reference', 'first_sorting', 'second_sorting', 'first_sort_operators',
                    'second_sort_operators', 'first_sort_amount', 'second_sort_amount']

##############################################################################
class Output_App1_detailResource(resources.ModelResource):
    class Meta:
        model = Output_App1_detail

class Output_App1_detailAdmin(ImportExportModelAdmin):
    class Meta:
        model = Output_App1_detail

    list_display = ['input_reference', 'is_running']
##############################################################################
class TruckResource(resources.ModelResource):
    class Meta:
        model = Truck

class TruckAdmin(ImportExportModelAdmin):
    class Meta:
        model = Truck

    resource_class = TruckResource
    list_display = ['head', 'trailer', 'load_capacity', 'is_available']
    search_fields = ['head__plate_number', 'trailer__plate_number']


##############################################################################
class Input_App2Resource(resources.ModelResource):
    class Meta:
        model = Input_App2

class Input_App2Admin(ImportExportModelAdmin):
    class Meta:
        model = Input_App2

    resource_class = Input_App2Resource
    list_display = ['date', 'time_cost', 'distance_cost']
    search_fields = ['date']

##############################################################################
class Output_App2Resource(resources.ModelResource):
    class Meta:
        model = Output_App2

class Output_App2Admin(ImportExportModelAdmin):
    class Meta:
        model = Output_App2

    resource_class = Output_App2Resource
    list_display = ['input_reference', 'truck', 'truck_is_used', 'visit_order',
                    'node_name', 'lat', 'long', 'load_unload', 'arrival_time',
                    'departure_time', 'leaving_load']
    search_fields = ['input_reference__date','truck__head__plate_number', 'truck__trailer__plate_number']

    autocomplete_fields = ['input_reference','truck']
##############################################################################
class Output_App2_detailResource(resources.ModelResource):
    class Meta:
        model = Output_App2_detail

class Output_App2_detailAdmin(ImportExportModelAdmin):
    class Meta:
        model = Output_App2_detail

    list_display = ['input_reference', 'is_running']

################
###############################################################
class UnitaLocaleResource(resources.ModelResource):
    class Meta:
        model = UnitaLocale

class UnitaLocaleAdmin(ImportExportModelAdmin):
    class Meta:
        model = UnitaLocale

    # def save_model(self, request, obj, form, change):
    #     instance = form.save(commit=False)
    #     instance.save(request=request)
    #     return instance

    list_display = ['id_Client', 'progressivo_sede', 'nome_sede', 'lat','long', 'timewindow_LB','timewindow_UB', 'service_time']
    search_fields = ['id_Client', 'progressivo_sede','nome_sede']



###############################################################




admin.site.register(Client, ClientAdmin)
admin.site.register(UnitaLocale, UnitaLocaleAdmin)
admin.site.register(Carrier, CarrierAdmin)
admin.site.register(Transporter, TransporterAdmin)
admin.site.register(Truck, TruckAdmin)
admin.site.register(Cer, CerAdmin)
admin.site.register(Mission, MissionAdmin)
admin.site.register(Fir, FirAdmin)
admin.site.register(Mix_unloading, Mix_unloadingAdmin)
admin.site.register(Input_App1, Input_App1Admin)
admin.site.register(Output_App1, Output_App1Admin)
admin.site.register(Output_App1_detail, Output_App1_detailAdmin)
admin.site.register(Input_App2,Input_App2Admin)
admin.site.register(Output_App2,Output_App2Admin)
admin.site.register(Output_App2_detail, Output_App2_detailAdmin)

