
from datetime import date

from django.contrib import messages
from django.db import transaction
from django.db.models import Avg, Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import (
    Camera,
    Include,
    Occupante,
    Ospite,
    Pagamento,
    Personale,
    Prenotazione,
    Pulizia,
    Recensione,
    ServizioAggiuntivo,
    Stagione,
)


# ---------------------------------------------------------------------------
# Decoratori di accesso (basati sulla sessione, si veda nota in cima al file)
# ---------------------------------------------------------------------------

def ospite_richiesto(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('ospite_pk'):
            messages.error(request, "Devi effettuare il login come ospite.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def personale_richiesto(*ruoli_ammessi):
    """Decoratore parametrico: personale_richiesto('receptionist', 'amministratore')."""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            ruolo = request.session.get('ruolo_personale')
            if not ruolo or (ruoli_ammessi and ruolo not in ruoli_ammessi):
                messages.error(request, "Accesso non autorizzato.")
                return redirect('login')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# OSPITE — O1-O6
# ---------------------------------------------------------------------------

def registrazione_ospite(request):
    """O1 - Registra un nuovo ospite nel sistema."""
    if request.method == 'POST':
        documento_identita = request.POST.get('documento_identita')
        nome = request.POST.get('nome')
        cognome = request.POST.get('cognome')
        telefono = request.POST.get('telefono')
        e_mail = request.POST.get('e_mail')
        password = request.POST.get('password')

        # L'unicità della e-mail va controllata su ENTRAMBE le tabelle,
        # perché il vincolo UNIQUE del database copre solo la singola tabella
        # (si veda la discussione sul collasso verso il basso di 'Utente').
        if Ospite.objects.filter(e_mail=e_mail).exists() or Personale.objects.filter(e_mail=e_mail).exists():
            messages.error(request, "L'indirizzo e-mail è già registrato.")
            return render(request, 'ospiti/registrazione.html')

        if Ospite.objects.filter(documentoidentita=documento_identita).exists() or Personale.objects.filter(documentoidentita=documento_identita).exists():
            messages.error(request, "Documento d'identità già registrato.")
            return render(request, 'ospiti/registrazione.html')

        Ospite.objects.create(
            documentoidentita=documento_identita,
            nome=nome,
            cognome=cognome,
            telefono=telefono,
            e_mail=e_mail,
            password=password,
        )
        messages.success(request, "Registrazione completata: ora puoi accedere.")
        return redirect('login')

    return render(request, 'ospiti/registrazione.html')


def verifica_disponibilita(request):
    """O2 - Elenca le camere con capienza sufficiente e libere nel periodo indicato."""
    camere_disponibili = None

    if request.GET.get('data_arrivo') and request.GET.get('data_partenza'):
        data_arrivo = request.GET['data_arrivo']
        data_partenza = request.GET['data_partenza']
        numero_ospiti = int(request.GET.get('numero_ospiti', 1))

        candidate = Camera.objects.filter(numeromassimoospiti__gte=numero_ospiti, attivo=True)

        # Ambiguità 6: una camera è occupata per il periodo se esiste una
        # prenotazione ATTIVA le cui date si sovrappongono a quelle richieste.
        # Le prenotazioni completate riguardano soggiorni passati, quelle
        # cancellate non vincolano la camera: entrambe vengono ignorate qui.
        prenotazioni_sovrapposte = Prenotazione.objects.filter(
            stato='attiva',
            dataarrivo__lt=data_partenza,
            datapartenza__gt=data_arrivo,
        ).values_list('piano', 'numerocamera')
        camere_occupate = set(prenotazioni_sovrapposte)

        camere_disponibili = [
            c for c in candidate if (c.piano, c.numerocamera) not in camere_occupate
        ]

    return render(request, 'ospiti/verifica_disponibilita.html', {
        'camere': camere_disponibili,
    })


@ospite_richiesto
def effettua_prenotazione(request, piano, numero_camera):
    """O3 - Crea una prenotazione (con eventuali servizi aggiuntivi) per la camera indicata."""
    camera = get_object_or_404(Camera, piano=piano, numerocamera=numero_camera, attivo=True)

    if request.method == 'POST':
        data_arrivo = request.POST.get('data_arrivo')
        data_partenza = request.POST.get('data_partenza')
        numero_ospiti = int(request.POST.get('numero_ospiti'))
        nomi_servizi = request.POST.getlist('servizi')  # nomi dei ServizioAggiuntivo selezionati

        # Ambiguità 8: capienza della camera
        if numero_ospiti > camera.numeromassimoospiti:
            messages.error(request, "Il numero di ospiti supera la capienza della camera.")
            return redirect('effettua_prenotazione', piano=piano, numero_camera=numero_camera)

        # Ambiguità 6: nessuna sovrapposizione con prenotazioni attive
        sovrapposta = Prenotazione.objects.filter(
            piano=piano, numerocamera=numero_camera, stato='attiva',
            dataarrivo__lt=data_partenza, datapartenza__gt=data_arrivo,
        ).exists()
        if sovrapposta:
            messages.error(request, "La camera non è più disponibile per queste date.")
            return redirect('verifica_disponibilita')

        # Ambiguità 2/9: la stagione applicabile è quella in cui ricade
        # la data di arrivo (se nessuna la copre, si applica il prezzo base).
        stagione = Stagione.objects.filter(
            datainizio__lte=data_arrivo, datafine__gte=data_arrivo,
        ).first()

        with transaction.atomic():
            prenotazione = Prenotazione.objects.create(
                dataarrivo=data_arrivo,
                datapartenza=data_partenza,
                numeroospiti=numero_ospiti,
                stato='attiva',
                datacheckineffettivo=None,
                documentoidentitaospite_id=request.session['ospite_pk'],
                piano=piano,
                numerocamera=numero_camera,
                datainiziostagione=stagione if stagione else None,
            )
            for nome_servizio in nomi_servizi:
                Include.objects.create(
                    codiceprenotazione=prenotazione,
                    nomeservizio_id=nome_servizio,
                )

        messages.success(request, "Prenotazione effettuata con successo.")
        return redirect('le_mie_prenotazioni')

    servizi = ServizioAggiuntivo.objects.filter(attivo=True)
    return render(request, 'ospiti/effettua_prenotazione.html', {
        'camera': camera,
        'servizi': servizi,
    })


@ospite_richiesto
def cancella_prenotazione(request, codice_prenotazione):
    """O4 - Cancella una prenotazione attiva, solo se il check-in non è ancora avvenuto."""
    prenotazione = get_object_or_404(
        Prenotazione,
        codiceprenotazione=codice_prenotazione,
        documentoidentitaospite_id=request.session['ospite_pk'],
    )

    # Ambiguità 7: dopo il check-in la prenotazione non è più cancellabile
    if prenotazione.stato != 'attiva' or prenotazione.datacheckineffettivo is not None:
        messages.error(request, "La prenotazione non può più essere cancellata.")
    else:
        prenotazione.stato = 'cancellata'
        prenotazione.save()
        messages.success(request, "Prenotazione cancellata.")

    return redirect('le_mie_prenotazioni')


@ospite_richiesto
def le_mie_prenotazioni(request):
    """O5 - Elenca le prenotazioni effettuate dall'ospite loggato."""
    prenotazioni = Prenotazione.objects.filter(
        documentoidentitaospite_id=request.session['ospite_pk'],
    ).order_by('-dataarrivo')

    return render(request, 'ospiti/le_mie_prenotazioni.html', {
        'prenotazioni': prenotazioni,
    })


@ospite_richiesto
def lascia_recensione(request, codice_prenotazione):
    """O6 - Lascia una recensione per un soggiorno completato (al più una per prenotazione)."""
    prenotazione = get_object_or_404(
        Prenotazione,
        codiceprenotazione=codice_prenotazione,
        documentoidentitaospite_id=request.session['ospite_pk'],
        stato='completata',
    )

    if Recensione.objects.filter(codiceprenotazione=prenotazione).exists():
        messages.error(request, "Hai già lasciato una recensione per questo soggiorno.")
        return redirect('le_mie_prenotazioni')

    if request.method == 'POST':
        voto = int(request.POST.get('voto'))
        commento = request.POST.get('commento') or None  # facoltativo

        Recensione.objects.create(
            codiceprenotazione=prenotazione,
            voto=voto,
            commento=commento,
            data=timezone.now().date(),
        )
        messages.success(request, "Recensione inviata, grazie!")
        return redirect('le_mie_prenotazioni')

    return render(request, 'ospiti/lascia_recensione.html', {'prenotazione': prenotazione})


# ---------------------------------------------------------------------------
# RECEPTIONIST — R1-R5
# ---------------------------------------------------------------------------

@personale_richiesto('receptionist')
def check_in(request, codice_prenotazione):
    """R1 - Registra l'arrivo dell'ospite: la camera passa a 'occupata'."""
    prenotazione = get_object_or_404(Prenotazione, codiceprenotazione=codice_prenotazione, stato='attiva')

    if prenotazione.datacheckineffettivo is not None:
        messages.error(request, "Check-in già registrato per questa prenotazione.")
        return redirect('arrivi_partenze')

    with transaction.atomic():
        prenotazione.datacheckineffettivo = timezone.now().date()
        prenotazione.save()

        camera = Camera.objects.get(piano=prenotazione.piano, numerocamera=prenotazione.numerocamera)
        camera.stato = 'occupata'
        camera.save()

        # eventuali occupanti aggiuntivi indicati dalla receptionist (oltre all'ospite)
        for nome, cognome, documento in zip(
            request.POST.getlist('occupante_nome'),
            request.POST.getlist('occupante_cognome'),
            request.POST.getlist('occupante_documento'),
        ):
            if documento:
                Occupante.objects.get_or_create(
                    codiceprenotazione=prenotazione,
                    documentoidentita=documento,
                    defaults={'nome': nome, 'cognome': cognome},
                )

    messages.success(request, "Check-in registrato.")
    return redirect('arrivi_partenze')


@personale_richiesto('receptionist')
def check_out(request, codice_prenotazione):
    """R2/R3 - Registra la partenza, genera il pagamento, la camera passa a 'da pulire'."""
    prenotazione = get_object_or_404(Prenotazione, codiceprenotazione=codice_prenotazione, stato='attiva')

    if prenotazione.datacheckineffettivo is None:
        messages.error(request, "Impossibile effettuare il check-out: check-in non ancora registrato.")
        return redirect('arrivi_partenze')

    if request.method == 'POST':
        metodo = request.POST.get('metodo')  # 'contanti' | 'carta' | 'bonifico'

        notti = (prenotazione.datapartenza - prenotazione.dataarrivo).days
        camera = Camera.objects.get(piano=prenotazione.piano, numerocamera=prenotazione.numerocamera)

        # Ambiguità 1: il moltiplicatore stagionale si applica solo al prezzo
        # base della camera, non ai servizi aggiuntivi.
        moltiplicatore = prenotazione.datainiziostagione.moltiplicatore if prenotazione.datainiziostagione_id else 1

        totale_servizi = Include.objects.filter(codiceprenotazione=prenotazione).aggregate(
            s=Sum('nomeservizio__costo'),
        )['s'] or 0

        importo_totale = camera.prezzobasenotte * moltiplicatore * notti + totale_servizi

        with transaction.atomic():
            Pagamento.objects.create(
                codiceprenotazione=prenotazione,
                importototale=importo_totale,
                metodo=metodo,
                data=timezone.now().date(),
            )
            prenotazione.stato = 'completata'
            prenotazione.save()

            camera.stato = 'da pulire'
            camera.save()

        messages.success(request, f"Check-out registrato. Totale addebitato: {importo_totale} €.")
        return redirect('arrivi_partenze')

    return render(request, 'receptionist/check_out.html', {'prenotazione': prenotazione})


@personale_richiesto('receptionist')
def arrivi_partenze(request):
    """R4 - Mostra gli arrivi e le partenze previsti per una data (default: oggi)."""
    data_selezionata = request.GET.get('data') or timezone.now().date().isoformat()

    arrivi = Prenotazione.objects.filter(dataarrivo=data_selezionata, stato='attiva')
    partenze = Prenotazione.objects.filter(datapartenza=data_selezionata, stato='attiva')

    return render(request, 'receptionist/arrivi_partenze.html', {
        'arrivi': arrivi,
        'partenze': partenze,
        'data': data_selezionata,
    })


# R5 (receptionist) e P1 (addetto pulizie) condividono la stessa vista:
# entrambi i ruoli possono consultare la lista delle camere da pulire.
@personale_richiesto('receptionist', 'addetto_pulizie')
def lista_camere_da_pulire(request):
    """R5 / P1 - Elenca le camere nello stato 'da pulire'."""
    camere = Camera.objects.filter(stato='da pulire')
    return render(request, 'pulizie/lista_camere_da_pulire.html', {'camere': camere})


# ---------------------------------------------------------------------------
# ADDETTO PULIZIE — P2 (P1 è sopra, condivisa con R5)
# ---------------------------------------------------------------------------

@personale_richiesto('addetto_pulizie')
def camera_pulita(request, piano, numero_camera):
    """P2 - Segna una camera come pulita: la camera torna 'disponibile'."""
    camera = get_object_or_404(Camera, piano=piano, numerocamera=numero_camera, stato='da pulire')

    with transaction.atomic():
        # id: (piano, numeroCamera, data) — si assume una sola pulizia al
        # giorno per camera, come motivato nella progettazione concettuale.
        Pulizia.objects.get_or_create(
            piano=piano,
            numerocamera=numero_camera,
            data=timezone.now().date(),
            defaults={'documentoidentitaaddetto_id': request.session['personale_pk']},
        )
        camera.stato = 'disponibile'
        camera.save()

    messages.success(request, "Camera segnata come pulita.")
    return redirect('lista_camere_da_pulire')


# ---------------------------------------------------------------------------
# AMMINISTRATORE — A1-A9
# ---------------------------------------------------------------------------

@personale_richiesto('amministratore')
def aggiungi_camera(request):
    """A1.1 - Aggiunge una nuova camera."""
    if request.method == 'POST':
        Camera.objects.create(
            piano=request.POST.get('piano'),
            numerocamera=request.POST.get('numero_camera'),
            tipologia=request.POST.get('tipologia'),
            numeromassimoospiti=request.POST.get('numero_massimo_ospiti'),
            descrizione=request.POST.get('descrizione'),
            stato='disponibile',
            prezzobasenotte=request.POST.get('prezzo_base_notte'),
            attivo=True,
        )
        messages.success(request, "Camera aggiunta.")
        return redirect('gestione_camere')

    return render(request, 'admin/aggiungi_camera.html')


@personale_richiesto('amministratore')
def elimina_camera(request, piano, numero_camera):
    """A1.2 - Disattiva una camera (soft delete tramite 'attivo': si veda la nota su
    PROTECT/storico discussa per la relazione con Prenotazione e Pulizia)."""
    camera = get_object_or_404(Camera, piano=piano, numerocamera=numero_camera)
    camera.attivo = False
    camera.save()
    messages.success(request, "Camera disattivata.")
    return redirect('gestione_camere')


@personale_richiesto('amministratore')
def modifica_camera(request, piano, numero_camera):
    """A1.3 - Modifica i dettagli di una camera."""
    camera = get_object_or_404(Camera, piano=piano, numerocamera=numero_camera)

    if request.method == 'POST':
        camera.tipologia = request.POST.get('tipologia')
        camera.numeromassimoospiti = request.POST.get('numero_massimo_ospiti')
        camera.descrizione = request.POST.get('descrizione')
        camera.prezzobasenotte = request.POST.get('prezzo_base_notte')
        camera.save()
        messages.success(request, "Camera modificata.")
        return redirect('gestione_camere')

    return render(request, 'admin/modifica_camera.html', {'camera': camera})


@personale_richiesto('amministratore')
def aggiungi_personale(request):
    """A2.1 - Aggiunge un nuovo membro del personale."""
    if request.method == 'POST':
        e_mail = request.POST.get('e_mail')
        documento_identita = request.POST.get('documento_identita')

        # stesso controllo incrociato di unicità e-mail usato in O1
        if Ospite.objects.filter(e_mail=e_mail).exists() or Personale.objects.filter(e_mail=e_mail).exists():
            messages.error(request, "L'indirizzo e-mail è già registrato.")
            return render(request, 'admin/aggiungi_personale.html')

        if Personale.objects.filter(documentoidentita=documento_identita).exists() or Ospite.objects.filter(documentoidentita=documento_identita).exists():
            messages.error(request, "Documento d'identità già registrato.")
            return render(request, 'admin/aggiungi_personale.html')

        Personale.objects.create(
            documentoidentita=request.POST.get('documento_identita'),
            nome=request.POST.get('nome'),
            cognome=request.POST.get('cognome'),
            telefono=request.POST.get('telefono'),
            e_mail=e_mail,
            password=request.POST.get('password'),
            ruolo=request.POST.get('ruolo'),
            attivo=True,
        )
        messages.success(request, "Membro del personale aggiunto.")
        return redirect('gestione_personale')

    return render(request, 'admin/aggiungi_personale.html')


@personale_richiesto('amministratore')
def elimina_personale(request, documento_identita):
    """A2.2 - Disattiva un membro del personale (soft delete tramite 'attivo')."""
    persona = get_object_or_404(Personale, documentoidentita=documento_identita)
    persona.attivo = False
    persona.save()
    messages.success(request, "Membro del personale disattivato.")
    return redirect('gestione_personale')


@personale_richiesto('amministratore')
def modifica_personale(request, documento_identita):
    """A2.3 - Modifica i dati (es. contatti/ruolo) di un membro del personale."""
    persona = get_object_or_404(Personale, documentoidentita=documento_identita)

    if request.method == 'POST':
        persona.telefono = request.POST.get('telefono')
        persona.ruolo = request.POST.get('ruolo')
        persona.save()
        messages.success(request, "Dati aggiornati.")
        return redirect('gestione_personale')

    return render(request, 'admin/modifica_personale.html', {'persona': persona})


@personale_richiesto('amministratore')
def aggiungi_servizio(request):
    """A3.1 - Aggiunge un nuovo servizio aggiuntivo."""
    if request.method == 'POST':
        ServizioAggiuntivo.objects.create(
            nome=request.POST.get('nome'),
            descrizione=request.POST.get('descrizione'),
            costo=request.POST.get('costo'),
            attivo=True,
        )
        messages.success(request, "Servizio aggiunto.")
        return redirect('gestione_servizi')

    return render(request, 'admin/aggiungi_servizio.html')


@personale_richiesto('amministratore')
def elimina_servizio(request, nome):
    """A3.2 - Disattiva un servizio aggiuntivo (soft delete tramite 'attivo')."""
    servizio = get_object_or_404(ServizioAggiuntivo, nome=nome)
    servizio.attivo = False
    servizio.save()
    messages.success(request, "Servizio disattivato.")
    return redirect('gestione_servizi')


@personale_richiesto('amministratore')
def modifica_servizio(request, nome):
    """A3.3 - Modifica descrizione/costo di un servizio aggiuntivo."""
    servizio = get_object_or_404(ServizioAggiuntivo, nome=nome)

    if request.method == 'POST':
        servizio.descrizione = request.POST.get('descrizione')
        servizio.costo = request.POST.get('costo')
        servizio.save()
        messages.success(request, "Servizio modificato.")
        return redirect('gestione_servizi')

    return render(request, 'admin/modifica_servizio.html', {'servizio': servizio})


@personale_richiesto('amministratore')
def aggiungi_stagione(request):
    """A4 - Definisce un nuovo periodo stagionale (nessuna modifica/eliminazione prevista,
    coerentemente con l'Ambiguità 9: ogni stagione è definita una tantum)."""
    if request.method == 'POST':
        data_inizio = request.POST.get('data_inizio')
        data_fine = request.POST.get('data_fine')

        # Ambiguità 2: le stagioni non possono sovrapporsi
        sovrapposta = Stagione.objects.filter(
            datainizio__lte=data_fine, datafine__gte=data_inizio,
        ).exists()
        if sovrapposta:
            messages.error(request, "Il periodo indicato si sovrappone a una stagione esistente.")
            return render(request, 'admin/aggiungi_stagione.html')

        Stagione.objects.create(
            datainizio=data_inizio,
            datafine=data_fine,
            nome=request.POST.get('nome'),
            moltiplicatore=request.POST.get('moltiplicatore'),
        )
        messages.success(request, "Stagione aggiunta.")
        return redirect('gestione_stagioni')

    return render(request, 'admin/aggiungi_stagione.html')


@personale_richiesto('amministratore')
def tasso_occupazione(request):
    """A5 - Tasso di occupazione di ogni camera in un intervallo di date."""
    risultati = None
    data_inizio = request.GET.get('data_inizio')
    data_fine = request.GET.get('data_fine')

    if data_inizio and data_fine:
        d_inizio = date.fromisoformat(data_inizio)
        d_fine = date.fromisoformat(data_fine)
        notti_totali = (d_fine - d_inizio).days or 1

        risultati = []
        for camera in Camera.objects.filter(attivo=True):
            prenotazioni = Prenotazione.objects.filter(
                piano=camera.piano, numerocamera=camera.numerocamera,
                stato__in=['attiva', 'completata'],
                dataarrivo__lt=data_fine, datapartenza__gt=data_inizio,
            )
            notti_occupate = 0
            for p in prenotazioni:
                inizio_sovrapposizione = max(p.dataarrivo, d_inizio)
                fine_sovrapposizione = min(p.datapartenza, d_fine)
                notti_occupate += (fine_sovrapposizione - inizio_sovrapposizione).days

            risultati.append({
                'camera': camera,
                'tasso_percentuale': round(notti_occupate / notti_totali * 100, 1),
            })

    return render(request, 'admin/tasso_occupazione.html', {'risultati': risultati})


@personale_richiesto('amministratore')
def fatturato_mensile(request):
    """A6 - Fatturato totale di un mese, suddiviso per tipologia di camera."""
    anno = int(request.GET.get('anno', timezone.now().year))
    mese = int(request.GET.get('mese', timezone.now().month))

    pagamenti = Pagamento.objects.filter(
        data__year=anno, data__month=mese,
    ).select_related('codiceprenotazione')

    fatturato_per_tipologia = {}
    for pagamento in pagamenti:
        prenotazione = pagamento.codiceprenotazione
        camera = Camera.objects.get(piano=prenotazione.piano, numerocamera=prenotazione.numerocamera)
        fatturato_per_tipologia[camera.tipologia] = (
            fatturato_per_tipologia.get(camera.tipologia, 0) + pagamento.importototale
        )

    return render(request, 'admin/fatturato_mensile.html', {
        'fatturato': fatturato_per_tipologia,
        'anno': anno,
        'mese': mese,
    })


@personale_richiesto('amministratore')
def servizi_piu_richiesti(request):
    """A7 - I 3 servizi aggiuntivi più richiesti in un dato periodo."""
    risultati = None
    data_inizio = request.GET.get('data_inizio')
    data_fine = request.GET.get('data_fine')

    if data_inizio and data_fine:
        risultati = (
            Include.objects
            .filter(
                codiceprenotazione__dataarrivo__gte=data_inizio,
                codiceprenotazione__dataarrivo__lte=data_fine,
            )
            .values('nomeservizio')
            .annotate(richieste=Count('nomeservizio'))
            .order_by('-richieste')[:3]
        )

    return render(request, 'admin/servizi_piu_richiesti.html', {'risultati': risultati})


@personale_richiesto('amministratore')
def recensioni_estreme(request):
    """A8 - Per ogni tipologia di camera, la camera con media recensioni più alta e più bassa.

    NOTA: la traversata 'codiceprenotazione__camera__tipologia' passa per il
    ForeignObject a chiave composta definito in Prenotazione verso Camera;
    verificare che si comporti come atteso nella vostra versione di Django,
    in caso contrario sostituire con una seconda query su Camera per id.
    """
    medie_per_camera = (
        Recensione.objects
        .values(
            'codiceprenotazione__piano',
            'codiceprenotazione__numerocamera',
            'codiceprenotazione__camera__tipologia',
        )
        .annotate(media_voto=Avg('voto'))
    )

    per_tipologia = {}
    for riga in medie_per_camera:
        tipologia = riga['codiceprenotazione__camera__tipologia']
        per_tipologia.setdefault(tipologia, []).append(riga)

    estremi_per_tipologia = {
        tipologia: {
            'migliore': max(righe, key=lambda r: r['media_voto']),
            'peggiore': min(righe, key=lambda r: r['media_voto']),
        }
        for tipologia, righe in per_tipologia.items()
    }

    return render(request, 'admin/recensioni_estreme.html', {'estremi': estremi_per_tipologia})


@personale_richiesto('amministratore')
def servizi_sotto_soglia(request):
    """A9 - Servizi aggiuntivi il cui fatturato in una data stagione non supera una soglia.

    Si controllano TUTTI i servizi (non solo quelli con almeno una richiesta),
    così da individuare anche quelli con fatturato pari a zero nella stagione.
    """
    risultati = None
    data_inizio_stagione = request.GET.get('stagione')  # PK di Stagione = dataInizio
    soglia = request.GET.get('soglia')

    if data_inizio_stagione and soglia:
        soglia = float(soglia)
        risultati = {}
        for servizio in ServizioAggiuntivo.objects.filter(attivo=True):
            totale = Include.objects.filter(
                nomeservizio=servizio,
                codiceprenotazione__datainiziostagione=data_inizio_stagione,
            ).aggregate(s=Sum('nomeservizio__costo'))['s'] or 0

            if totale < soglia:
                risultati[servizio.nome] = totale

    return render(request, 'admin/servizi_sotto_soglia.html', {'risultati': risultati})


# ---------------------------------------------------------------------------
# Login / logout minimali (necessari per popolare la sessione usata sopra)
# ---------------------------------------------------------------------------

def login_view(request):
    """Login unico per ospiti e personale: prova prima su Ospite, poi su Personale."""
    if request.method == 'POST':
        e_mail = request.POST.get('e_mail')
        password = request.POST.get('password')  # confronto in chiaro, vedi nota in cima al file

        ospite = Ospite.objects.filter(e_mail=e_mail, password=password).first()
        if ospite:
            request.session['ospite_pk'] = ospite.documentoidentita
            return redirect('le_mie_prenotazioni')

        persona = Personale.objects.filter(e_mail=e_mail, password=password, attivo=True).first()
        if persona:
            request.session['personale_pk'] = persona.documentoidentita
            request.session['ruolo_personale'] = persona.ruolo
            return redirect('home')

        messages.error(request, "Credenziali non valide.")

    return render(request, 'login.html')


def logout_view(request):
    request.session.flush()
    return redirect('home')