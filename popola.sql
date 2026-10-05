-- *********************************************
-- * Dati minimi di test — Gestione di un Bed & Breakfast
-- *
-- * Da eseguire su Workbench DOPO aver creato lo schema con seed.sql.
-- * Svuota tutte le tabelle (rispettando le chiavi esterne) e inserisce
-- * una situazione di test pensata per coprire i casi principali:
-- *
-- *  - personale con i tre ruoli (receptionist, addetto pulizie, amministratore)
-- *  - ospiti, camere di tipologie diverse, servizi aggiuntivi, due stagioni
-- *  - prenotazioni in tutti gli stati rilevanti:
-- *      * attiva, senza check-in          -> per testare disponibilità/check-in/cancellazione
-- *      * attiva, con check-in già fatto  -> per testare il check-out
-- *      * completata, con pagamento e recensione (x2, voti diversi)   -> per testare statistiche e recensioni
-- *      * cancellata                      -> verifica che non blocchi la disponibilità della camera nello stesso periodo (Ambiguità 6)
-- *  - una camera 'occupata' e due 'da pulire' -> per testare le pulizie
-- *
-- *********************************************

USE bedandbreakfast;

-- --------------------------------------------
-- Svuotamento (disabilito temporaneamente i controlli sulle FK
-- per poter usare TRUNCATE, che resetta anche gli AUTO_INCREMENT)
-- --------------------------------------------

SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE TABLE INCLUDE;
TRUNCATE TABLE OCCUPANTE;
TRUNCATE TABLE PULIZIA;
TRUNCATE TABLE PAGAMENTO;
TRUNCATE TABLE RECENSIONE;
TRUNCATE TABLE PRENOTAZIONE;
TRUNCATE TABLE OSPITE;
TRUNCATE TABLE PERSONALE;
TRUNCATE TABLE CAMERA;
TRUNCATE TABLE STAGIONE;
TRUNCATE TABLE SERVIZIO_AGGIUNTIVO;

SET FOREIGN_KEY_CHECKS = 1;

-- --------------------------------------------
-- Personale
-- --------------------------------------------

INSERT INTO PERSONALE (documentoIdentita, nome, cognome, telefono, e_mail, password, ruolo, attivo) VALUES
('PRS000001', 'Giulia', 'Bianchi', '3331112222', 'giulia.reception@locanda.it', 'test1234', 'receptionist',    TRUE),
('PRS000002', 'Marco',  'Verdi',   '3332223333', 'marco.pulizie@locanda.it',   'test1234', 'addetto_pulizie', TRUE),
('PRS000003', 'Anna',   'Rossi',   '3333334444', 'anna.admin@locanda.it',     'test1234', 'amministratore',  TRUE);

-- --------------------------------------------
-- Ospiti
-- --------------------------------------------

INSERT INTO OSPITE (documentoIdentita, nome, cognome, telefono, e_mail, password) VALUES
('OSP000001', 'Luca',  'Ferrari', '3209876543', 'luca.ferrari@example.com',  'ospite123'),
('OSP000002', 'Sara',  'Colombo', '3401234567', 'sara.colombo@example.com',  'ospite123'),
('OSP000003', 'Paolo', 'Russo',   '3457654321', 'paolo.russo@example.com',   'ospite123');

-- --------------------------------------------
-- Camere
-- 101 e 102 disponibili, 201 e 301 da pulire, 202 occupata
-- --------------------------------------------

INSERT INTO CAMERA (piano, numeroCamera, tipologia, numeroMassimoOspiti, descrizione, stato, prezzoBaseNotte, attivo) VALUES
(1, 101, 'singola',     1, 'Camera singola luminosa con vista giardino.', 'disponibile', 60.00,  TRUE),
(1, 102, 'doppia',      2, 'Camera doppia con bagno privato.',            'disponibile', 90.00,  TRUE),
(2, 201, 'matrimoniale',2, 'Camera matrimoniale con balcone.',            'da pulire',   100.00, TRUE),
(2, 202, 'suite',       4, 'Suite con angolo salotto.',                   'occupata',    160.00, TRUE),
(3, 301, 'doppia',      2, 'Camera doppia mansardata.',                   'da pulire',   85.00,  TRUE);

-- --------------------------------------------
-- Servizi aggiuntivi
-- --------------------------------------------

INSERT INTO SERVIZIO_AGGIUNTIVO (nome, descrizione, costo, attivo) VALUES
('Colazione',           'Colazione continentale in sala.',    10.00, TRUE),
('Transfer aeroporto',  'Transfer da/per l''aeroporto.',       25.00, TRUE),
('Noleggio biciclette', 'Noleggio bici giornaliero.',           8.00, TRUE),
('Late check-out',      'Check-out posticipato alle 14:00.',   15.00, TRUE);

-- --------------------------------------------
-- Stagioni
-- una passata (per gli storici di pagamenti/recensioni) e una che copre
-- le date delle prenotazioni "attive" create sotto
-- --------------------------------------------

INSERT INTO STAGIONE (dataInizio, dataFine, nome, moltiplicatore) VALUES
('2026-06-01', '2026-08-31', 'Alta stagione — estate 2026', 1.30),
('2026-09-01', '2026-11-30', 'Stagione autunnale 2026',     1.10);

-- --------------------------------------------
-- Prenotazione 1: completata, con pagamento, recensione e pulizia successiva
-- --------------------------------------------

INSERT INTO PRENOTAZIONE
    (codicePrenotazione, dataArrivo, dataPartenza, numeroOspiti, stato, dataCheckInEffettivo, documentoIdentitaOspite, piano, numeroCamera, dataInizioStagione)
VALUES
    (1, '2026-07-10', '2026-07-13', 1, 'completata', '2026-07-10', 'OSP000001', 1, 101, '2026-06-01');

INSERT INTO INCLUDE (nomeServizio, codicePrenotazione) VALUES
('Colazione', 1);

INSERT INTO PAGAMENTO (codicePagamento, codicePrenotazione, importoTotale, metodo, data) VALUES
-- 60 (prezzo base) * 1.30 (moltiplicatore) * 3 (notti) + 10 (colazione) = 244.00
(1, 1, 244.00, 'carta', '2026-07-13');

INSERT INTO RECENSIONE (codiceRecensione, codicePrenotazione, voto, commento, data) VALUES
(1, 1, 5, 'Soggiorno fantastico, torneremo sicuramente!', '2026-07-14');

INSERT INTO PULIZIA (piano, numeroCamera, data, documentoIdentitaAddetto) VALUES
(1, 101, '2026-07-13', 'PRS000002');

-- --------------------------------------------
-- Prenotazione 2: completata, pagamento e recensione (voto più basso);
-- la camera 201 resta volutamente 'da pulire' per testare quella parte
-- --------------------------------------------

INSERT INTO PRENOTAZIONE
    (codicePrenotazione, dataArrivo, dataPartenza, numeroOspiti, stato, dataCheckInEffettivo, documentoIdentitaOspite, piano, numeroCamera, dataInizioStagione)
VALUES
    (2, '2026-07-20', '2026-07-22', 2, 'completata', '2026-07-20', 'OSP000002', 2, 201, '2026-06-01');

INSERT INTO PAGAMENTO (codicePagamento, codicePrenotazione, importoTotale, metodo, data) VALUES
-- 100 * 1.30 * 2 notti = 260.00
(2, 2, 260.00, 'contanti', '2026-07-22');

INSERT INTO RECENSIONE (codiceRecensione, codicePrenotazione, voto, commento, data) VALUES
(2, 2, 3, 'Nella media, camera un po'' rumorosa.', '2026-07-23');

-- --------------------------------------------
-- Prenotazione 3: attiva, check-in non ancora effettuato
-- (per testare disponibilità, cancellazione e check-in)
-- --------------------------------------------

INSERT INTO PRENOTAZIONE
    (codicePrenotazione, dataArrivo, dataPartenza, numeroOspiti, stato, dataCheckInEffettivo, documentoIdentitaOspite, piano, numeroCamera, dataInizioStagione)
VALUES
    (3, '2026-10-05', '2026-10-08', 2, 'attiva', NULL, 'OSP000001', 1, 102, '2026-09-01');

INSERT INTO INCLUDE (nomeServizio, codicePrenotazione) VALUES
('Transfer aeroporto', 3);

-- --------------------------------------------
-- Prenotazione 4: attiva, check-in già effettuato, con due occupanti
-- aggiuntivi (per testare il check-out sulla camera 202, già 'occupata')
-- --------------------------------------------

INSERT INTO PRENOTAZIONE
    (codicePrenotazione, dataArrivo, dataPartenza, numeroOspiti, stato, dataCheckInEffettivo, documentoIdentitaOspite, piano, numeroCamera, dataInizioStagione)
VALUES
    (4, '2026-09-25', '2026-09-30', 3, 'attiva', '2026-09-25', 'OSP000003', 2, 202, '2026-09-01');

INSERT INTO OCCUPANTE (codicePrenotazione, nome, cognome, documentoIdentita) VALUES
(4, 'Elena',  'Russo', 'OCC000001'),
(4, 'Davide', 'Russo', 'OCC000002');

-- --------------------------------------------
-- Prenotazione 5: cancellata, stesso periodo/camera della 1 ma più avanti
-- (verifica che una cancellata non vincoli la disponibilità, Ambiguità 6)
-- --------------------------------------------

INSERT INTO PRENOTAZIONE
    (codicePrenotazione, dataArrivo, dataPartenza, numeroOspiti, stato, dataCheckInEffettivo, documentoIdentitaOspite, piano, numeroCamera, dataInizioStagione)
VALUES
    (5, '2026-11-01', '2026-11-03', 1, 'cancellata', NULL, 'OSP000002', 1, 101, '2026-09-01');

-- --------------------------------------------
-- Allineo i contatori AUTO_INCREMENT al prossimo valore libero,
-- dato che qui sopra i codici sono stati inseriti esplicitamente
-- --------------------------------------------

ALTER TABLE PRENOTAZIONE AUTO_INCREMENT = 6;
ALTER TABLE PAGAMENTO    AUTO_INCREMENT = 3;
ALTER TABLE RECENSIONE   AUTO_INCREMENT = 3;