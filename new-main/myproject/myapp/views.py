from django.shortcuts import redirect, render
from django.http import JsonResponse, HttpResponse
from .models import Donnee, Capteur
from django.db.models import F
import csv
from datetime import datetime

# Create your views here.

def home(request):
    return render(request, 'mqtt/home.html')

def afficher_donnees(request):
    donnees = Donnee.objects.order_by(F('date').desc(), F('heure').desc())[:8]
    serialized_data = [{
        'date': donnee.date,
        'heure': donnee.heure,
        'temperature': donnee.temperature,
        'capteur': donnee.capteur.nom
    } for donnee in donnees]
    return JsonResponse({'donnees': serialized_data})

def actualiser_donnees(request):
    donnees = Donnee.objects.order_by(F('date').desc(), F('heure').desc())[:10]
    serialized_data = [{
        'date': donnee.date,
        'heure': donnee.heure,
        'temperature': donnee.temperature,
        'capteur': donnee.capteur.nom
    } for donnee in donnees]
    return JsonResponse({'donnees': serialized_data})

def filtrer_donnees(request):
    nom_capteur = request.GET.get('nom-capteur')
    date_debut = request.GET.get('date-debut')
    date_fin = request.GET.get('date-fin')
    
    donnees = Donnee.objects.all()
    
    if nom_capteur:
        donnees = donnees.filter(capteur__nom=nom_capteur)
    
    if date_debut and date_fin:
        date_debut = datetime.strptime(date_debut, '%Y-%m-%d')
        date_fin = datetime.strptime(date_fin, '%Y-%m-%d')
        donnees = donnees.filter(date__range=[date_debut, date_fin])
    
    donnees = donnees.order_by('-date', '-heure')
    context = {'donnees': donnees}
    return render(request, 'mqtt/filtrer_donnees.html', context)

def exporter_donnees(request):
    donnees = Donnee.objects.order_by(F('date').desc(), F('heure').desc())
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="donnees.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Capteur', 'Date', 'Heure', 'Température'])
    
    for donnee in donnees:
        writer.writerow([donnee.capteur.nom, donnee.date.strftime('%Y-%m-%d'), donnee.heure.strftime('%H:%M:%S'), donnee.temperature])
    
    return response

def graph_view(request):
    donnees1 = Donnee.objects.filter(capteur__nom='A72E3F6B79BB').order_by('-date', '-heure')[:50]
    donnees2 = Donnee.objects.filter(capteur__nom='B8A5F3569EFF').order_by('-date', '-heure')[:50]
    
    x_values1 = [donnee.heure for donnee in donnees1]
    y_values1 = [donnee.temperature for donnee in donnees1]
    
    x_values2 = [donnee.heure for donnee in donnees2]
    y_values2 = [donnee.temperature for donnee in donnees2]
    
    # Utilisez Plotly pour créer les graphiques
    import plotly.graph_objects as go
    
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=x_values1, y=y_values1, mode='lines', name='Capteur A72E3F6B79BB'))
    fig1.update_layout(title='Température Capteur A72E3F6B79BB', xaxis_title='Heure', yaxis_title='Température')
    
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=x_values2, y=y_values2, mode='lines', name='Capteur B8A5F3569EFF', line=dict(color='firebrick')))
    fig2.update_layout(title='Température Capteur B8A5F3569EFF', xaxis_title='Heure', yaxis_title='Température')
    
    graph_div1 = fig1.to_html(full_html=False)
    graph_div2 = fig2.to_html(full_html=False)
    
    return render(request, 'mqtt/graph.html', {'graph_div1': graph_div1, 'graph_div2': graph_div2})

def update_piece(request, capteur_id):
    capteur = Capteur.objects.get(id=capteur_id)
    
    if request.method == 'POST':
        piece = request.POST.get('piece')
        capteur.piece = piece
        capteur.save()
        return redirect('home')  
    
    return render(request, 'mqtt/update_piece.html', {'capteur': capteur})

