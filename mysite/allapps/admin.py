from django.contrib import admin

# Register your models here.
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from allapps.models import Client, Carrier, Transporter, Cer, Mission, Fir, Mix_unloading
from allapps.models import Input_App1, Output_App1, Input_App2, Output_App2
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
    list_display = ['plate_number', 'is_trailer', 'carrier_name', 'add_trailer']


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
    list_display = ['date', 'Client_origin', 'Client_destination']
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


class Input_App2Resource(resources.ModelResource):
    class Meta:
        model = Input_App2


class Output_App2Resource(resources.ModelResource):
    class Meta:
        model = Output_App2


admin.site.register(Client, ClientAdmin)
admin.site.register(Carrier, CarrierAdmin)
admin.site.register(Transporter, TransporterAdmin)
admin.site.register(Cer, CerAdmin)
admin.site.register(Mission, MissionAdmin)
admin.site.register(Fir, FirAdmin)
admin.site.register(Mix_unloading, Mix_unloadingAdmin)
admin.site.register(Input_App1)
admin.site.register(Output_App1)
admin.site.register(Input_App2)
admin.site.register(Output_App2)
