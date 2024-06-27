# models.py
from django.db import models

class Capteur(models.Model):
    nom = models.CharField(max_length=255, primary_key=True)
    piece = models.CharField(max_length=255)
    emplacement = models.CharField(max_length=255)

    def __str__(self):
        return self.nom

class Donnee(models.Model):
    capteur = models.ForeignKey(Capteur, on_delete=models.CASCADE, db_column='capteur_id')
    timestamp = models.DateTimeField()
    temperature = models.FloatField()

    def __str__(self):
        return f"{self.capteur.nom} - {self.timestamp}"
