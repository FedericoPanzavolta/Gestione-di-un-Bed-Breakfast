from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = 'BedAndBreakfast'

urlpatterns = [

    # -----------------------------------------------------------------
    # Comuni a tutti gli utenti
    # -----------------------------------------------------------------

    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),


    # -----------------------------------------------------------------
    # Ospite
    # -----------------------------------------------------------------

    path('registrazione/', views.registrazione_ospite, name='registrazione_ospite'),
    path('camere/disponibilita/', views.verifica_disponibilita, name='verifica_disponibilita'),
    path('camere/<int:piano>/<int:numero_camera>/prenota/', views.effettua_prenotazione, name='effettua_prenotazione'),
    path('prenotazioni/', views.le_mie_prenotazioni, name='le_mie_prenotazioni'),
    path('prenotazioni/<int:codice_prenotazione>/cancella/', views.cancella_prenotazione, name='cancella_prenotazione'),
    path('prenotazioni/<int:codice_prenotazione>/recensione/', views.lascia_recensione, name='lascia_recensione'),


    # -----------------------------------------------------------------
    # Receptionist
    # -----------------------------------------------------------------

    path('reception/arrivi-partenze/', views.arrivi_partenze, name='arrivi_partenze'),
    path('reception/check-in/<int:codice_prenotazione>/', views.check_in, name='check_in'),
    path('reception/check-out/<int:codice_prenotazione>/', views.check_out, name='check_out'),

    # -----------------------------------------------------------------
    # Pulizie:
    # -----------------------------------------------------------------

    path('pulizie/', views.lista_camere_da_pulire, name='lista_camere_da_pulire'),
    path('pulizie/<int:piano>/<int:numero_camera>/pulita/', views.camera_pulita, name='camera_pulita'),


    # -----------------------------------------------------------------
    # Amministratore — gestione (A1-A4)
    # -----------------------------------------------------------------

    # Camere
    path('gestione/camere/', views.gestione_camere, name='gestione_camere'),
    path('gestione/camere/aggiungi/', views.aggiungi_camera, name='aggiungi_camera'),
    path('gestione/camere/<int:piano>/<int:numero_camera>/modifica/', views.modifica_camera, name='modifica_camera'),
    path('gestione/camere/<int:piano>/<int:numero_camera>/elimina/',  views.elimina_camera, name='elimina_camera'),

    # Personale (chiave: documento d'identità)
    path('gestione/personale/', views.gestione_personale, name='gestione_personale'),
    path('gestione/personale/aggiungi/', views.aggiungi_personale, name='aggiungi_personale'),
    path('gestione/personale/<str:documento_identita>/modifica/', views.modifica_personale, name='modifica_personale'),
    path('gestione/personale/<str:documento_identita>/elimina/', views.elimina_personale, name='elimina_personale'),

    # Servizi aggiuntivi (chiave: nome). Si usa <path:...> perché il nome
    # potrebbe contenere una barra (es. "transfer aeroporto/stazione");
    # per questo il nome sta in fondo all'URL.
    path('gestione/servizi/', views.gestione_servizi, name='gestione_servizi'),
    path('gestione/servizi/aggiungi/', views.aggiungi_servizio, name='aggiungi_servizio'),
    path('gestione/servizi/modifica/<path:nome>/', views.modifica_servizio, name='modifica_servizio'),
    path('gestione/servizi/elimina/<path:nome>/', views.elimina_servizio, name='elimina_servizio'),

    # Stagioni (solo elenco e aggiunta)
    path('gestione/stagioni/', views.gestione_stagioni, name='gestione_stagioni'),
    path('gestione/stagioni/aggiungi/', views.aggiungi_stagione, name='aggiungi_stagione'),

    # -----------------------------------------------------------------
    # Amministratore — statistiche
    # -----------------------------------------------------------------
    
    path('statistiche/occupazione/', views.tasso_occupazione, name='tasso_occupazione'),
    path('statistiche/fatturato/', views.fatturato_mensile, name='fatturato_mensile'),
    path('statistiche/servizi-richiesti/', views.servizi_piu_richiesti, name='servizi_piu_richiesti'),
    path('statistiche/recensioni-estreme/', views.recensioni_estreme, name='recensioni_estreme'),
    path('statistiche/servizi-sotto-soglia/', views.servizi_sotto_soglia, name='servizi_sotto_soglia'),
]