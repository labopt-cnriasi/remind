import datetime
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
    tempo_servizio = models.TimeField(default=datetime.time(0,30))
    
class fir(models.Model):
    num_fiscale = models.CharField(max_length=50,primary_key=True)
    cer = models.PositiveIntegerField(verbose_name = "CER")
    peso_netto = models.PositiveIntegerField()
    id_produttore = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    id_smaltitore = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    id_trasportatore = models.CharField(max_length=50)
    targa_automezzo = models.CharField(max_length=10)
    targa_rimorchio = models.CharField(max_length=10)
    
    
class Missione(models.Model):
    #id_uscita è la chiave della Tab Missioni in WinWaste
    #verificarne il fild type con Grillo
    id_uscita = models.AutoField(primary_key=True)    
    data = models.DateField(auto_now=False)
    cliente_origine = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    cliente_destinazione = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    numero_casse = models.PositiveIntegerField(validators=[MinValueValidator(1),MaxValueValidator(2)],)
    
    # NB: il fir della missione sarà disponibile solo al suo completamento?
    num_fiscale = models.ForeignKey(fir, on_delete=models.PROTECT)
    
class Scarico(models.Model):
    id_cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    data_ora = models.DateTimeField(verbose_name = "orario previsto",validators=[validate_date]) 
    turno = models.PositiveSmallIntegerField(verbose_name = "turno previsto") # turno in cui avviene lo scarico
    cer = models.PositiveIntegerField(verbose_name = "CER")
    quantità = models.PositiveIntegerField(verbose_name = "quantità prevista")
    
    # NB: il fir della missione sarà disponibile solo al suo completamento?
    num_fiscale = models.ForeignKey(fir, on_delete=models.PROTECT)
    
    def validate_date(self):
        now = timezone.now()
        if self.data_ora <= now:
            raise ValidationError(
                ('Orario previsto non ammissibile'),
                params={'valore': self.data_ora},)
    
    def previsto_in_orizzonte(self,orizzonte):
        now = timezone.now()
        return now <= self.data_ora <= now + datetime.timedelta(days=orizzonte)

class Composizione_Scarico(models.Model):
    num_fiscale = models.ForeignKey(fir, on_delete=models.CASCADE)
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
    descriione   = models.CharField(max_length=200)
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
        super(Subject, self).save(*args, **kwargs) # il vero metodo save
        
    
class Profit_tab(models.Model):
    num_fiscale = models.ForeignKey(fir, on_delete=models.CASCADE)
    
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
    

    

    
    
""" 
### Classi del tutorial ###

class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')
    def __str__(self):
        return self.question_text
    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now
    was_published_recently.admin_order_field = 'pub_date'
    was_published_recently.boolean = True
    was_published_recently.short_description = 'Published recently?'

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
    def __str__(self):
        return self.choice_text

"""

