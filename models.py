
import datetime
from datetime import date
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator

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


##### Cliente può essere un produttore o uno smaltitore
class Cliente(models.Model):
    id_cliente = models.CharField(max_length=50,primary_key=True)
    lat  = models.DecimalField(verbose_name = "latitudine", max_digits = 15, decimal_places = 10)
    long = models.DecimalField(verbose_name = "longitudine", max_digits = 15, decimal_places = 10)
    timewindow_LB  = models.TimeField(default=datetime.time(9 ,00))
    timewindow_UB  = models.TimeField(default=datetime.time(17,00))
    tempo_servizio = models.IntegerField(validators=[MinValueValidator(0)],default = 30)
    
    
class Trasportatore(models.Model):
    id_trasportatore = models.CharField(max_length=50,primary_key=True) #Innocenti / altri
    indirizzo = models.CharField(max_length=50)
    
class Mezzi(models.Model):
    targa = models.CharField(max_length=50,primary_key=True) 
    is_rimorchio = models.BooleanField(default = False)
    nome_trasportatore = models.ForeignKey(Trasportatore,on_delete=models.PROTECT) # il proprietario 
    
    def val_add_rimorchio(self):
        if self.is_rimorchio == True:
            return False
    add_rimorchio = models.BooleanField(default = False,validators=[val_add_rimorchio],)


class Cer(models.Model):
    id_cer = models.CharField(verbose_name = "CER",max_length=50,primary_key=True)
    descrizione = models.CharField(max_length = 100) ## definifare validator da lista di ammissibili
    
    
class Missione(models.Model): ## programmazione

    def validate_date(self):
        today = date.today()
        if self.data < today:
            raise ValidationError(
                ('data prevista non ammissibile'),
                params={'valore': self.data},)
            
    id_uscita = models.AutoField(primary_key=True)    
    data = models.DateField(auto_now=False,validators=[validate_date],) # giorno ritiro/consegna
    cliente_origine      = models.ForeignKey(Cliente, related_name = 'origine', on_delete=models.PROTECT)
    cliente_destinazione = models.ForeignKey(Cliente, related_name = 'destinazione', on_delete=models.PROTECT)
    numero_casse = models.PositiveIntegerField(validators=[MinValueValidator(1)],)
    


class Fir(models.Model):
    num_fiscale = models.CharField(max_length=50,primary_key=True)
    uscita = models.ForeignKey(Missione, on_delete=models.PROTECT)
    cer = models.ForeignKey(Cer, on_delete=models.PROTECT)
    peso_netto = models.PositiveIntegerField()
    id_produttore = models.ForeignKey(Cliente, related_name = 'produttore', on_delete=models.PROTECT)
    id_smaltitore = models.ForeignKey(Cliente, related_name = 'smaltitore', on_delete=models.PROTECT)
    id_trasportatore = models.ForeignKey(Trasportatore, on_delete=models.PROTECT)
    
    def val_automezzo(self):
        if self.targa_automezzo.is_rimorchio == True:
            raise ValidationError(
                ('La targa inserita non corrisponde ad un automezzo'),
                params={'valore': self.targa_automezzo},)
            
    def val_rimorchio(self):
        if self.targa_rimorchio.is_rimorchio == False:
            raise ValidationError(
                ('La targa inserita non corrisponde ad un rimorchio'),
                params={'valore': self.targa_rimorchio},)      
            
    targa_automezzo = models.ForeignKey(Mezzi, related_name = 'automezzo',on_delete=models.PROTECT,validators = [val_automezzo])
    targa_rimorchio = models.ForeignKey(Mezzi, related_name = 'rimorchio', on_delete=models.PROTECT,validators = [val_rimorchio])
    
    
class Scarico_misti(models.Model): ## programmazione delle attività di selezione
    id_cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    
    def validate_date(self):
        today = date.today()
        if self.data <= today:
            raise ValidationError(
                ('Data prevista non ammissibile'),
                params={'valore': self.data},)
    
    data = models.DateField(verbose_name = "data prevista",validators=[validate_date]) # data in cui si prevede avvenga lo scarico
    turno = models.PositiveSmallIntegerField(verbose_name = "turno previsto") # turno in cui si prevede avvenga lo scarico
    quantità = models.PositiveIntegerField(verbose_name = "quantità prevista")
        

            
    def previsto_in_orizzonte(self,orizzonte):
        now = timezone.now()
        if (now <= self.data) and  (self.data <= now + datetime.timedelta(days=orizzonte)):
            return True
        else:
            return False
        
        
        
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
    
    
# output number according to App_1 output list in document "integrazioni informative REMIND"    
class Output_App1(models.Model):
    input_reference = models.ForeignKey(Input_App1,on_delete=models.CASCADE)
    date = models.DateField(verbose_name = "date in schedule") #1
    shift = models.PositiveIntegerField(verbose_name = "shift #",validators=[MaxValueValidator(3)],) #1
    first_sorting  = models.BooleanField(verbose_name = "first sorting activation")  #1
    second_sorting = models.BooleanField(verbose_name = "second sorting activation") #1
    
    def val_first_op(self):
        if (self.first_sorting == False) and (self.first_sort_operators != 0):
            raise ValidationError(
                ('first sorting has not been scheduled for this working shift'))
        
    def val_second_op(self):
        if (self.second_sorting == False) and (self.second_sort_operators != 0):
            raise ValidationError(
                ('second sorting has not been scheduled for this working shift'))
    
    first_sort_operators  = models.PositiveIntegerField(default = 0,validators=[val_first_op])  #2
    second_sort_operators = models.PositiveIntegerField(default = 0,validators=[val_second_op]) #2
    
    first_sort_amount  = models.PositiveIntegerField(default = 0,validators=[val_first_op])  #3
    second_sort_amount = models.PositiveIntegerField(default = 0,validators=[val_second_op]) #3
    
    
    
# input number according to App_2 input list in document "integrazioni informative REMIND"
class Input_App2(models.Model):
    date = models.DateField() #6
    time_cost     = models.PositiveIntegerField(default = 15) #7
    distance_cost = models.PositiveIntegerField(default = 15) #8
    
    def val_automezzo(self):
        if self.truck_1.is_rimorchio == True:
            raise ValidationError(
                ('La targa inserita non corrisponde ad un automezzo'),
                params={'valore': self.truck_1},)
            
    def val_rimorchio(self):
        if self.truck_1_trailer.is_rimorchio == False:
            raise ValidationError(
                ('La targa inserita non corrisponde ad un rimorchio'),
                params={'valore': self.truck_1_trailer},)    
    
    truck   = models.ForeignKey(Mezzi,related_name = 'truck'  , on_delete=models.PROTECT, validators = [val_automezzo]) #3
    trailer = models.ForeignKey(Mezzi,related_name = 'trailer', on_delete=models.PROTECT, validators = [val_rimorchio],default = "nan") #3
    
    def val_trailer(self):
        if (self.truck_trailer != "nan") and (self.load_capacity != 2):
            raise ValidationError(
                ('Con il rimorchio aggiunto la capacità è pari a 2 cassoni'),
                params={'valore': self.load_capacity},)
            
    load_capacity = models.PositiveIntegerField(default = 1,validators=[val_trailer,MaxValueValidator(2)]) #3
    
    

# output number according to App_2 output list in document "integrazioni informative REMIND"
class Output_App2(models.Model):
    truck = models.ForeignKey(Input_App2,on_delete=models.PROTECT) #1
    mission = models.ForeignKey(Missione,on_delete=models.PROTECT) #1
    origin_visit_order = models.CharField(max_length=100)      #2
    destination_visit_order = models.CharField(max_length=100) #2

        
class Composizione_Scarico(models.Model):
    num_fiscale = models.ForeignKey(Fir, on_delete=models.CASCADE)
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
    descrizione   = models.CharField(max_length=200)
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
    num_fiscale = models.ForeignKey(Fir, on_delete=models.CASCADE)
    
    addeb_smaltimento   = models.BooleanField()
    prezzo_smaltimento  = models.FloatField(validators=[MinValueValidator(0)],)
    costo_smaltimento   = models.FloatField(validators=[MinValueValidator(0)],)
    importo_smaltimento = models.FloatField(validators=[MinValueValidator(0)],)
    
    def get_importo_smaltimento(self):
        return (self.num_fiscale.peso_netto)*(self.prezzo_smaltimento)
        
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
