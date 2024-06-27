from django.db import models

class Capteur(models.Model):
    nom = models.CharField(max_length=255, primary_key=True)
    piece = models.CharField(max_length=255)

    class Meta:
        db_table = 'capteur'


class Donnee(models.Model):
    id = models.AutoField(primary_key=True)
    capteur = models.ForeignKey(Capteur, on_delete=models.CASCADE, db_column='capteur_id')
    date = models.DateField()
    heure = models.TimeField()
    temperature = models.FloatField()

    class Meta:
        db_table = 'donnee'
