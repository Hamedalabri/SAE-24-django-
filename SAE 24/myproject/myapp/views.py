from django.shortcuts import redirect, render
from django.http import JsonResponse, HttpResponse
from .models import Donnee, Capteur
from django.db.models import F
import csv
from datetime import datetime
import plotly.graph_objects as go

def home(request):
    return render(request, 'mqtt/home.html')

def afficher_donnees(request):
    donnees = Donnee.objects.order_by(F('timestamp').desc())[:8]
    serialized_data = [{
        'timestamp': donnee.timestamp,
        'temperature': donnee.temperature,
        'capteur': donnee.capteur.nom,
        'piece': donnee.capteur.piece,
        'emplacement': donnee.capteur.emplacement
    } for donnee in donnees]
    return JsonResponse({'donnees': serialized_data})

def actualiser_donnees(request):
    donnees = Donnee.objects.order_by(F('timestamp').desc())[:10]
    serialized_data = [{
        'timestamp': donnee.timestamp,
        'temperature': donnee.temperature,
        'capteur': donnee.capteur.nom,
        'piece': donnee.capteur.piece,
        'emplacement': donnee.capteur.emplacement
    } for donnee in donnees]
    return JsonResponse({'donnees': serialized_data})

def filtrer_donnees(request):
    noms_capteurs = request.GET.get('noms-capteurs', '').split(',')
    piece = request.GET.get('piece', '')
    date_debut = request.GET.get('date-debut')
    date_fin = request.GET.get('date-fin')

    donnees = Donnee.objects.all()

    if noms_capteurs and noms_capteurs != ['']:
        donnees = donnees.filter(capteur__nom__in=noms_capteurs)

    if piece:
        donnees = donnees.filter(capteur__piece=piece)

    if date_debut and date_fin:
        if date_debut != 'None' and date_fin != 'None':
            date_debut = datetime.strptime(date_debut, '%Y-%m-%d')
            date_fin = datetime.strptime(date_fin, '%Y-%m-%d')
            donnees = donnees.filter(timestamp__range=[date_debut, date_fin])

    donnees = donnees.order_by('-timestamp')

    context = {
        'donnees': donnees,
        'noms_capteurs': request.GET.get('noms-capteurs', ''),
        'piece': piece,
        'date_debut': date_debut,
        'date_fin': date_fin,
        'noms_capteurs_2': request.GET.get('noms-capteurs-2', ''),
        'piece_2': request.GET.get('piece-2', ''),
        'date_debut_2': request.GET.get('date-debut-2', ''),
        'date_fin_2': request.GET.get('date-fin-2', ''),
        'refresh_interval': request.GET.get('refresh-interval', ''),
        'enable_refresh': request.GET.get('enable-refresh', False),
    }

    return render(request, 'mqtt/filtrer_donnees.html', context)

def exporter_donnees(request):
    format_export = request.GET.get('format', 'csv')
    noms_capteurs = request.GET.get('noms-capteurs', '').split(',')
    piece = request.GET.get('piece', '')
    date_debut = request.GET.get('date-debut')
    date_fin = request.GET.get('date-fin')

    donnees = Donnee.objects.all()

    if noms_capteurs and noms_capteurs != ['']:
        donnees = donnees.filter(capteur__nom__in=noms_capteurs)

    if piece:
        donnees = donnees.filter(capteur__piece=piece)

    if date_debut and date_fin:
        if date_debut != 'None' and date_fin != 'None':
            date_debut = datetime.strptime(date_debut, '%Y-%m-%d')
            date_fin = datetime.strptime(date_fin, '%Y-%m-%d')
            donnees = donnees.filter(timestamp__range=[date_debut, date_fin])

    donnees = donnees.order_by(F('timestamp').desc())

    if format_export == 'excel':
        # Code pour exporter en format Excel (à ajouter si nécessaire)
        pass
    else:  # Default to CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="donnees.csv"'

        writer = csv.writer(response)
        writer.writerow(['Capteur', 'Pièce', 'Emplacement', 'Date', 'Heure', 'Température'])

        for donnee in donnees:
            writer.writerow([
                donnee.capteur.nom,
                donnee.capteur.piece,
                donnee.capteur.emplacement,
                donnee.timestamp.strftime('%Y-%m-%d'),
                donnee.timestamp.strftime('%H:%M:%S'),
                donnee.temperature
            ])

        return response

def graph_view(request):
    capteur_nom = request.GET.get('capteur_nom')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')

    if not capteur_nom:
        return render(request, 'mqtt/graph.html', {'error': 'Veuillez spécifier un capteur.'})

    donnees = Donnee.objects.filter(capteur__nom=capteur_nom)

    if date_debut and date_fin:
        if date_debut != 'None' and date_fin != 'None':
            date_debut = datetime.strptime(date_debut, '%Y-%m-%d')
            date_fin = datetime.strptime(date_fin, '%Y-%m-%d')
            donnees = donnees.filter(timestamp__range=[date_debut, date_fin])

    donnees = donnees.order_by('-timestamp')[:50]

    if not donnees:
        return render(request, 'mqtt/graph.html', {'error': f'Aucune donnée trouvée pour le capteur {capteur_nom}.'})

    x_values = [donnee.timestamp for donnee in donnees]
    y_values = [donnee.temperature for donnee in donnees]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_values, y=y_values, mode='lines', name=f'Capteur {capteur_nom}'))
    fig.update_layout(title=f'Température Capteur {capteur_nom}', xaxis_title='Heure', yaxis_title='Température')

    graph_div = fig.to_html(full_html=False)

    return render(request, 'mqtt/graph.html', {
        'graph_div': graph_div,
        'capteur_nom': capteur_nom,
        'date_debut': date_debut.strftime('%Y-%m-%d') if date_debut and date_debut != 'None' else '',
        'date_fin': date_fin.strftime('%Y-%m-%d') if date_fin and date_fin != 'None' else ''
    })


from django.shortcuts import render, redirect
from django.db import IntegrityError, connection, transaction
from .models import Capteur, Donnee


def update_piece(request):
    capteurs = Capteur.objects.all()

    if request.method == 'POST':
        errors = []
        for capteur in capteurs:
            old_nom = capteur.nom
            new_nom = request.POST.get(f'nom_{capteur.nom}')
            new_emplacement = request.POST.get(f'emplacement_{capteur.nom}')

            if new_nom and new_emplacement:
                if new_nom != old_nom:
                    try:
                        with transaction.atomic():
                            # Désactiver les contraintes de clé étrangère
                            with connection.cursor() as cursor:
                                cursor.execute("SET FOREIGN_KEY_CHECKS=0;")

                            # Mettre à jour les enregistrements de la table donnee avec une clé temporaire
                            temp_key = f"{new_nom}_temp"
                            Donnee.objects.filter(capteur_id=old_nom).update(capteur_id=temp_key)

                            # Mettre à jour le capteur avec le nouveau nom
                            Capteur.objects.filter(nom=old_nom).update(nom=new_nom)

                            # Mettre à jour les enregistrements de la table donnee avec le nouveau nom
                            Donnee.objects.filter(capteur_id=temp_key).update(capteur_id=new_nom)

                            # Réactiver les contraintes de clé étrangère
                            with connection.cursor() as cursor:
                                cursor.execute("SET FOREIGN_KEY_CHECKS=1;")

                        capteur.emplacement = new_emplacement
                        capteur.save()
                    except IntegrityError as e:
                        errors.append(f"Erreur d'intégrité lors de la mise à jour du capteur {old_nom}: {str(e)}")
                else:
                    capteur.emplacement = new_emplacement
                    capteur.save()
            else:
                errors.append(f"Tous les champs doivent être remplis pour le capteur {old_nom}.")

        if errors:
            return render(request, 'mqtt/update_piece.html', {'capteurs': capteurs, 'errors': errors})
        return redirect('home')

    return render(request, 'mqtt/update_piece.html', {'capteurs': capteurs})
