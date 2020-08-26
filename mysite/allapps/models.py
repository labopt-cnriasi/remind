
import datetime
from datetime import date
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, int_list_validator


# Useful links:
# https://django-book.readthedocs.io/en/latest/chapter05.html
# https://developer.mozilla.org/en-US/docs/Learn/Server-side/Django/Models
# Models https://docs.djangoproject.com/en/3.0/topics/db/models/#relationships
# Models fields https://docs.djangoproject.com/en/3.0/ref/models/fields/#django.db.models.Field.verbose_name
# Validators https://docs.djangoproject.com/en/3.0/ref/validators/#minvaluevalidator
# Model instance reference https://docs.djangoproject.com/en/3.0/ref/models/instances/#validating-objects

# NB: If you make changes to a Django model, you’ll need to make the same 
# changes inside your database to keep your database consistent with the model. 
# We’ll discuss some strategies for handling this problem later in this chapter.
#==> https://django-book.readthedocs.io/en/latest/chapter05.html

# Django provides an easy way of committing the SQL to the database:
# the syncdb command:
# python manage.py syncdb


##### Client può essere un produttore o uno smaltitore
class Client(models.Model):
    id_Client = models.CharField("ID Cliente",max_length=50,primary_key=True)
    
    KIND_CHOICHES =  [("produttore", "Produttore"),("smaltitore", "Smaltitore"),]
    kind = models.CharField("Tipologia",max_length=20,choices = KIND_CHOICHES)
    
    lat  = models.DecimalField("latitudine", max_digits = 15, decimal_places = 10)
    long = models.DecimalField("longitudine", max_digits = 15, decimal_places = 10)
    timewindow_LB  = models.TimeField("Apertura",default=datetime.time(9 ,00))
    timewindow_UB  = models.TimeField("Chiusura",default=datetime.time(17,00))
    service_time = models.IntegerField("Tempo di servizio stimato [mm]",validators=[MinValueValidator(0)],default = 30)
    
    def __str__(self):
        return self.id_Client
    
    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clienti'
    
    
class Carrier(models.Model):
    id_Carrier = models.CharField("ID Trasportatore",max_length=50,primary_key=True) #Innocenti / altri
    address = models.CharField("indirizzo",max_length=50)
    
    class Meta:
        verbose_name = 'Trasportatore'
        verbose_name_plural = 'Trasportatori'
    
class Transporter(models.Model):
    plate_number = models.CharField("Targa",max_length=50,primary_key=True)

    TYPE_CHOICHES = [("motrice", "motrice"), ("rimorchio", "rimorchio"), ]
    trasporter_type = models.CharField("Tipologia mezzo",max_length=50, default = False,choices = TYPE_CHOICHES)
    carrier_name = models.ForeignKey(Carrier,on_delete=models.PROTECT,verbose_name = "Trasportatore proprietario")
    add_trailer = models.BooleanField("può agganciare un rimorchio",default = False)

    def __str__(self):
        return self.plate_number

    class Meta:
        verbose_name = 'mezzo di trasporto'
        verbose_name_plural = 'mezzi di trasporto'

class Truck(models.Model):
    head    = models.ForeignKey(Transporter,related_name='head', verbose_name="Motrice", on_delete=models.PROTECT,limit_choices_to={'trasporter_type': "motrice"},)
    trailer = models.ForeignKey(Transporter,related_name='trailer', verbose_name="Rimorchio", blank=True, null=True, on_delete=models.PROTECT,limit_choices_to={'trasporter_type': "rimorchio"},)
    load_capacity = models.PositiveIntegerField("Casse trasportabili",default = 1,validators=[MaxValueValidator(2)])
    is_available = models.BooleanField("disponibilità al servizio",default = True)


    class Meta:
        verbose_name = 'Automezzo'
        verbose_name_plural = 'Automezzi'

class Cer(models.Model):
    id_cer = models.CharField(verbose_name = "codice CER",max_length=50,primary_key=True)
    description = models.CharField("descrizione CER",max_length = 100) ## definire validator da lista di ammissibili
    
    class Meta:
        verbose_name = 'CER'
        verbose_name_plural = 'Codici CER'
    
    
class Mission(models.Model): ## programmazione

    id_exit= models.AutoField("ID uscita",primary_key=True)    
    date = models.DateField("data prevista",auto_now=False) # giorno ritiro/consegna
    Client_origin      = models.ForeignKey(Client, related_name = 'origin', on_delete=models.PROTECT,verbose_name = "Origine trasporto")
    Client_destination = models.ForeignKey(Client, related_name = 'destination', on_delete=models.PROTECT,verbose_name = "Destinazione trasporto")
    case_number = models.PositiveIntegerField("numero casse",validators=[MinValueValidator(1)],)
    # is_scheduled = ....

    class Meta:
        verbose_name = 'Missione'
        verbose_name_plural = 'Missioni'

class Fir(models.Model):
    fir_number = models.CharField("Numero FIR",max_length=50,primary_key=True)
    exit_id = models.ForeignKey(Mission, on_delete=models.PROTECT,verbose_name = "ID_uscita")
    cer = models.ForeignKey(Cer, on_delete=models.PROTECT,verbose_name = "CER")
    net_weight = models.PositiveIntegerField("peso netto")
    id_producer = models.ForeignKey(Client, related_name = 'producer', on_delete=models.PROTECT,verbose_name = "Produttore")
    id_disposer = models.ForeignKey(Client, related_name = 'disposer', on_delete=models.PROTECT,verbose_name = "Smaltitore")
    id_carrier = models.ForeignKey(Carrier, on_delete=models.PROTECT,verbose_name = "Trasportatore")
    
    def val_truck(self):
        if self.plate_number_truck.is_trailer == True:
            raise ValidationError(
                ('La targa inserita non corrisponde ad un automezzo'),
                params={'valore': self.plate_number_truck},)
            
    def val_trailer(self):
        if self.plate_number_trailer.is_trailer == False:
            raise ValidationError(
                ('La targa inserita non corrisponde ad un rimorchio'),
                params={'valore': self.plate_number_trailer},)      
            
    plate_number_truck = models.ForeignKey(Transporter, related_name = 'truck_plate',on_delete=models.PROTECT,validators = [val_truck],verbose_name = "Targa motrice")
    plate_number_trailer = models.ForeignKey(Transporter, related_name = 'trailer_plate', on_delete=models.PROTECT,validators = [val_trailer],verbose_name = "Targa rimorchio")
    
    class Meta:
        verbose_name = 'Fir'
        verbose_name_plural = 'Formulari'
    
    
class Mix_unloading(models.Model): ## programmazione delle attività di selezione
    id_Client = models.ForeignKey(Client, on_delete=models.CASCADE,verbose_name = "ID Cliente")
        
    date = models.DateField(verbose_name = "data prevista") # data in cui si prevede avvenga lo scarico
    working_shift = models.PositiveSmallIntegerField(verbose_name = "turno previsto",validators=[MinValueValidator(1),MaxValueValidator(2)]) # turno in cui si prevede avvenga lo scarico
    quantity = models.PositiveIntegerField(verbose_name = "quantità prevista")
            
    def horizon_included(self,orizzonte):
        now = timezone.now()
        if (now <= self.date) and  (self.date <= now + datetime.timedelta(days=orizzonte)):
            return True
        else:
            return False
        
    class Meta:
        verbose_name = 'Scarico 150106'
        verbose_name_plural = 'Scarico misti'
        
        
# input number according to App_1 input list in document "integrazioni informative REMIND"
class Input_App1(models.Model):
    horizon_LB = models.DateField() #1
    horizon_UB = models.DateField() #1
    dailyshifts = models.PositiveIntegerField(validators=[MinValueValidator(1)],default = 2) #2
    shift_1_hours = models.PositiveIntegerField(default = 6)  #3
    shift_2_hours = models.PositiveIntegerField(default = 3)  #3
    shift_3_hours = models.PositiveIntegerField(default = 0)  #3
    operator_wage = models.PositiveIntegerField(default = 15) #4
    max_operators = models.PositiveIntegerField(default = 8)  #5
    min_op_sort1 = models.PositiveIntegerField(default = 3)   #6
    min_op_sort2 = models.PositiveIntegerField(default = 6)   #6
    firstTO2nd_sort = models.PositiveIntegerField(validators=[MaxValueValidator(100)],default = 5) #7
    setup_sort1 = models.IntegerField(validators=[MinValueValidator(0)],default = 7)  #8
    setup_sort2 = models.IntegerField(validators=[MinValueValidator(0)],default = 15) #8
    overfill_treshold = models.PositiveIntegerField(validators=[MaxValueValidator(100)],default = 50)   #9
    finalstock_treshold = models.PositiveIntegerField(validators=[MaxValueValidator(100)],default = 10) #10
    sort1_capacity = models.PositiveIntegerField(default = 260)   #11
    sort2_capacity = models.PositiveIntegerField(default = 220)   #11
    sort1_maxstock = models.PositiveIntegerField(default = 60000) #12
    sort2_maxstock = models.PositiveIntegerField(default = 10000) #12
    
    class Meta:
        verbose_name = 'Input App 1'
        verbose_name_plural = 'Inputs App 1'
    
    
# output number according to App_1 output list in document "integrazioni informative REMIND"    
class Output_App1(models.Model):
    input_reference = models.ForeignKey(Input_App1,on_delete=models.CASCADE)

    first_sorting = models.CharField(verbose_name="first sorting activation", max_length=300, validators= [int_list_validator])    # 1
    second_sorting = models.CharField(verbose_name="second sorting activation", max_length=300, validators= [int_list_validator])  # 1

    first_sort_operators = models.CharField(default=0, max_length=300, validators= [int_list_validator])    # 2
    second_sort_operators = models.CharField(default=0, max_length=300, validators= [int_list_validator])  # 2

    first_sort_amount = models.CharField(default=0, max_length=300, validators= [int_list_validator])    # 3
    second_sort_amount = models.CharField(default=0, max_length=300, validators= [int_list_validator])  # 3

    class Meta:
        verbose_name = 'Output App 1'
        verbose_name_plural = 'Outputs App 1'


class Output_App1_detail(models.Model):
    input_reference = models.ForeignKey(Input_App1,on_delete=models.CASCADE)

    KIND_CHOICHES =  [("in esecuzione", "in esecuzione"),("completato", "completato"),]
    is_running = models.CharField("stato",max_length=40,choices = KIND_CHOICHES, default= "in esecuzione")

    class Meta:
        verbose_name = 'Output App 1 - dettaglio'
        verbose_name_plural = 'Outputs App 1 - dettagli'


# input number according to App_2 input list in document "integrazioni informative REMIND"
class Input_App2(models.Model):
    date = models.DateField() #6
    time_cost     = models.PositiveIntegerField(default = 15) #7
    distance_cost = models.PositiveIntegerField(default = 15) #8

    class Meta:
        verbose_name = 'Input App 2'
        verbose_name_plural = 'Inputs App 2'
    
    

# output number according to App_2 output list in document "integrazioni informative REMIND"
class Output_App2(models.Model):
    truck = models.ForeignKey(Input_App2,on_delete=models.PROTECT) #1
    mission = models.ForeignKey(Mission,on_delete=models.PROTECT) #1
    origin_visit_order = models.CharField(max_length=100)      #2
    destination_visit_order = models.CharField(max_length=100) #2
    
    class Meta:
        verbose_name = 'Output App 2'
        verbose_name_plural = 'Outputs App 2'

"""
        
class Composizione_Scarico(models.Model):
    fir_number = models.ForeignKey(Fir, on_delete=models.CASCADE)
    foglia = models.FloatField(validators=[MinValueValidator(0),MaxValueValidator(1)],)
    ferro = models.FloatField(validators=[MinValueValidator(0),MaxValueValidator(1)],)
    cartone = models.FloatField(validators=[MinValueValidator(0),MaxValueValidator(1)],)
    carta = models.FloatField(validators=[MinValueValidator(0),MaxValueValidator(1)],)
    pet = models.FloatField(validators=[MinValueValidator(0),MaxValueValidator(1)],)
    plastica_dura = models.FloatField(validators=[MinValueValidator(0),MaxValueValidator(1)],)
    legno = models.FloatField(validators=[MinValueValidator(0),MaxValueValidator(1)],)
    minuteria = models.FloatField(validators=[MinValueValidator(0),MaxValueValidator(1)],)
    sovvallo = models.FloatField(validators=[MinValueValidator(0),MaxValueValidator(1)],)
    ## Aggiungere Check Constraints for the Sum of Percentage Fields
    ## Come spiegato al link:
    ## https://adamj.eu/tech/2020/03/10/django-check-constraints-sum-percentage-fields/
    
    # validare questa funzione
    def validate_percentuali(self):
        somma = self.foglia + self.ferro + self.cartone + self.carta + self.pet + self.plastica_dura + self.legno + self.minuteria + self.sovvallo 
        if somma != 1:
            raise ValidationError(
                ('Somma delle percentuali di materiali diversa da 1'),
                params={'Somma delle percentuali inserite': somma},)
       
class venditaMPS(models.Model):
    id_fattura   = models.CharField(max_length=50,primary_key=True)
    mese_vendita = models.PositiveIntegerField(validators=[MinValueValidator(1),MaxValueValidator(12)],)
    description   = models.CharField(max_length=200)
    massa =  models.PositiveIntegerField(verbose_name = "quantità venduta")
    unità_misura = models.CharField(max_length=200)
    prezzo_unitario = models.FloatField(validators=[MinValueValidator(0)],)
    sconto = models.FloatField(validators=[MinValueValidator(0),MaxValueValidator(1)],)
    imponibile_riga = models.FloatField(validators=[MinValueValidator(0)],)
    
    ## ottenere valore campoimponibile_riga come prodotto di massa*prezzo_unitario*(1-sconto)
    ## per farlo bisogna sovrascrivere il metodo save() della classe
    ## nel nuovo metodo si possono fare i cambiamenti necessari
    ## quindi chiamare il metodo superclass per fare il vero salvataggio
    ## https://docs.djangoproject.com/en/3.0/topics/db/models/#overriding-model-methods
    
    def get_ricavo(self):
        return (self.massa)*(self.prezzo_unitario)*(1-self.sconto)
    
    def save(self, *args, **kwargs):
        if not self.imponibile_riga:
            self.imponibile_riga = self.get_ricavo()
        super(self).save(*args, **kwargs) # il vero metodo save
        
    
class Profit_tab(models.Model):
    fir_number = models.ForeignKey(Fir, on_delete=models.CASCADE)
    
    addeb_smaltimento   = models.BooleanField()
    prezzo_smaltimento  = models.FloatField(validators=[MinValueValidator(0)],)
    costo_smaltimento   = models.FloatField(validators=[MinValueValidator(0)],)
    importo_smaltimento = models.FloatField(validators=[MinValueValidator(0)],)
    
    def get_importo_smaltimento(self):
        return (self.fir_number.net_weight)*(self.prezzo_smaltimento)
        
    addeb_trasporto	  = models.BooleanField()
    importo_trasporto = models.FloatField(validators=[MinValueValidator(0)],)
    distanza_percorsa = models.FloatField(validators=[MinValueValidator(0)],)
    costo_trasporto   = models.FloatField(validators=[MinValueValidator(0)],)
    
    def get_costo_trasporto(self):
        return (self.distanza_percorsa)*0.9 # altrimenti specifica da input esterno
    
    addeb_selezione = models.BooleanField()
    costo_selezione = models.FloatField(validators=[MinValueValidator(0)],)
    ## valutare come ottenere il costo
    tempo_impiegato   = models.TimeField(default=datetime.time(0,30))
    
    ricavo_vendita    = models.FloatField(validators=[MinValueValidator(0)],)
    
    profitto_totale   = models.FloatField(validators=[MinValueValidator(0)],)
    
    def get_profitto(self):
        return self.ricavo_vendita + self.importo_trasporto + self.importo_smaltimento 
        -self.costo_selezione -self.costo_trasporto -self.costo_smaltimento
    
    def save(self, *args, **kwargs):
        if not self.importo_smaltimento:
            self.importo_smaltimento = self.get_importo_smaltimento()
        if not self.costo_trasporto:
            self.costo_trasporto = self.get_costo_trasporto()
        if not self.profitto_totale:
            self.profitto_totale = self.get_profitto()
        super(self).save(*args, **kwargs) # il vero metodo save
        
"""