-- *********************************************
-- * Standard SQL generation                   
-- *--------------------------------------------
-- * DB-MAIN version: 11.0.2              
-- * Generator DATE: Sep 14 2021              
-- * Generation DATE: Wed Sep  2 18:06:05 2026 
-- * LUN file: C:\Users\fedep\Desktop\Gestione di un B&B\Gestione di un Bed & Breakfast.lun 
-- * Schema: Schema Logico/SQL1 
-- ********************************************* 
-- Database Section
-- ________________ 
-- CREATE database Schema Logico; (creato in automatico da db-main)

CREATE DATABASE IF NOT EXISTS bedandbreakfast;

-- DBSpace Section
-- _______________

-- TABLES Section
-- _____________ 

USE bedandbreakfast; -- dice in quale DataBase creare le tabelle

CREATE TABLE CAMERA (
tipologia CHAR(15) NOT NULL,
numeroMassimoOspiti NUMERIC(2) NOT NULL,
piano NUMERIC(2) NOT NULL,
descrizione VARCHAR(200) NOT NULL,
stato CHAR(12) NOT NULL,
prezzoBaseNotte NUMERIC(8,2) NOT NULL,
numeroCamera NUMERIC(3) NOT NULL,
attivo BOOLEAN NOT NULL,
CONSTRAINT ID_CAMERA_ID PRIMARY KEY (piano, numeroCamera)
);
    
CREATE TABLE INCLUDE (
    nomeServizio VARCHAR(20) NOT NULL,
    codicePrenotazione INT NOT NULL,
    CONSTRAINT ID_INCLUDE_ID PRIMARY KEY (codicePrenotazione, nomeServizio)
);

CREATE TABLE OCCUPANTE (
    codicePrenotazione INT NOT NULL,
    nome VARCHAR(25) NOT NULL,
    cognome VARCHAR(25) NOT NULL,
    documentoIdentita CHAR(9) NOT NULL,
    CONSTRAINT ID_OCCUPANTE_ID PRIMARY KEY (codicePrenotazione, documentoIdentita)
);
    
CREATE TABLE OSPITE (
    nome VARCHAR(25) NOT NULL,
    cognome VARCHAR(25) NOT NULL,
    telefono CHAR(15) NOT NULL,
    e_mail VARCHAR(50) NOT NULL,
    password VARCHAR(16) NOT NULL,
    documentoIdentita CHAR(9) NOT NULL,
    CONSTRAINT ID_OSPITE_ID PRIMARY KEY (documentoIdentita),
    CONSTRAINT SID_OSPITE_ID UNIQUE (e_mail)
);
    
CREATE TABLE PAGAMENTO (
    codicePagamento INT NOT NULL AUTO_INCREMENT,
    codicePrenotazione INT NOT NULL,
    importoTotale NUMERIC(8,2) NOT NULL,
    metodo VARCHAR(20) NOT NULL,
    data DATE NOT NULL,
    CONSTRAINT ID_PAGAMENTO_ID PRIMARY KEY (codicePagamento),
    CONSTRAINT SID_PAGAM_PRENO_ID UNIQUE (codicePrenotazione)
);
    
CREATE TABLE PERSONALE (
    nome VARCHAR(25) NOT NULL,
    cognome VARCHAR(25) NOT NULL,
    telefono CHAR(15) NOT NULL,
    e_mail VARCHAR(50) NOT NULL,
    password VARCHAR(16) NOT NULL,
    documentoIdentita CHAR(9) NOT NULL,
    ruolo CHAR(25) NOT NULL,
    attivo BOOLEAN NOT NULL,
    CONSTRAINT ID_PERSONALE_ID PRIMARY KEY (documentoIdentita),
    CONSTRAINT SID_PERSONALE_ID UNIQUE (e_mail)
);
    
CREATE TABLE PRENOTAZIONE (
    codicePrenotazione INT NOT NULL AUTO_INCREMENT,
    dataArrivo DATE NOT NULL,
    dataPartenza DATE NOT NULL,
    numeroOspiti NUMERIC(2) NOT NULL,
    stato CHAR(12) NOT NULL,
    dataCheckInEffettivo DATE,
    documentoIdentitaOspite CHAR(9) NOT NULL,
    piano NUMERIC(2) NOT NULL,
    numeroCamera NUMERIC(3) NOT NULL,
    dataInizioStagione DATE,
    CONSTRAINT ID_PRENOTAZIONE_ID PRIMARY KEY (codicePrenotazione)
);
    
CREATE TABLE PULIZIA (
    piano NUMERIC(2) NOT NULL,
    numeroCamera NUMERIC(3) NOT NULL,
    data DATE NOT NULL,
    documentoIdentitaAddetto CHAR(9) NOT NULL,
    CONSTRAINT ID_PULIZIA_ID PRIMARY KEY (piano, numeroCamera, data)
);
    
CREATE TABLE RECENSIONE (
    codiceRecensione INT NOT NULL AUTO_INCREMENT,
    codicePrenotazione INT NOT NULL,
    voto NUMERIC(2) NOT NULL,
    commento VARCHAR(300),
    data DATE NOT NULL,
    CONSTRAINT ID_RECENSIONE_ID PRIMARY KEY (codiceRecensione),
    CONSTRAINT SID_RECEN_PRENO_ID UNIQUE (codicePrenotazione)
);
    
CREATE TABLE SERVIZIO_AGGIUNTIVO (
    nome VARCHAR(20) NOT NULL,
    descrizione VARCHAR(200) NOT NULL,
    costo NUMERIC(5,2) NOT NULL,
    attivo BOOLEAN NOT NULL,
    CONSTRAINT ID_SERVIZIO_AGGIUNTIVO_ID PRIMARY KEY (nome)
);
    
CREATE TABLE STAGIONE (
    nome VARCHAR(20) NOT NULL,
    moltiplicatore NUMERIC(3,2) NOT NULL,
    dataInizio DATE NOT NULL,
    dataFine DATE NOT NULL,
    CONSTRAINT ID_STAGIONE_ID PRIMARY KEY (dataInizio)
);
    
-- CONSTRAINTs Section
-- ___________________ 

ALTER TABLE INCLUDE ADD CONSTRAINT REF_INCLU_PRENO
FOREIGN KEY (codicePrenotazione)
REFERENCES PRENOTAZIONE(codicePrenotazione);

ALTER TABLE INCLUDE ADD CONSTRAINT REF_INCLU_SERVI_FK
FOREIGN KEY (nomeServizio)
REFERENCES SERVIZIO_AGGIUNTIVO(nome);

ALTER TABLE OCCUPANTE ADD CONSTRAINT REF_OCCUP_PRENO
FOREIGN KEY (codicePrenotazione)
REFERENCES PRENOTAZIONE(codicePrenotazione);

ALTER TABLE PAGAMENTO ADD CONSTRAINT SID_PAGAM_PRENO_FK
FOREIGN KEY (codicePrenotazione)
REFERENCES PRENOTAZIONE(codicePrenotazione);

ALTER TABLE PRENOTAZIONE ADD CONSTRAINT REF_PRENO_OSPIT_FK
FOREIGN KEY (documentoIdentitaOspite)
REFERENCES OSPITE(documentoIdentita);

ALTER TABLE PRENOTAZIONE ADD CONSTRAINT REF_PRENO_CAMER_FK
FOREIGN KEY (piano, numeroCamera)
REFERENCES CAMERA(piano, numeroCamera);

ALTER TABLE PRENOTAZIONE ADD CONSTRAINT REF_PRENO_STAGI_FK
FOREIGN KEY (dataInizioStagione)
REFERENCES STAGIONE(dataInizio);

ALTER TABLE PULIZIA ADD CONSTRAINT REF_PULIZ_PERSO_FK
FOREIGN KEY (documentoIdentitaAddetto)
REFERENCES PERSONALE(documentoIdentita);

ALTER TABLE PULIZIA ADD CONSTRAINT REF_PULIZ_CAMER
FOREIGN KEY (piano, numeroCamera)
REFERENCES CAMERA(piano, numeroCamera);

ALTER TABLE RECENSIONE ADD CONSTRAINT SID_RECEN_PRENO_FK
FOREIGN KEY (codicePrenotazione)
REFERENCES PRENOTAZIONE(codicePrenotazione);

-- INDEX Section
-- _____________ 

CREATE UNIQUE INDEX ID_CAMERA_IND
ON CAMERA (piano, numeroCamera);

CREATE UNIQUE INDEX ID_INCLUDE_IND
ON INCLUDE (codicePrenotazione, nomeServizio);

CREATE INDEX REF_INCLU_SERVI_IND
ON INCLUDE (nomeServizio);

CREATE UNIQUE INDEX ID_OCCUPANTE_IND
ON OCCUPANTE (codicePrenotazione, documentoIdentita);

CREATE UNIQUE INDEX ID_OSPITE_IND
ON OSPITE (documentoIdentita);

CREATE UNIQUE INDEX SID_OSPITE_IND
ON OSPITE (e_mail);

CREATE UNIQUE INDEX ID_PAGAMENTO_IND
ON PAGAMENTO (codicePagamento);

CREATE UNIQUE INDEX SID_PAGAM_PRENO_IND
ON PAGAMENTO (codicePrenotazione);

CREATE UNIQUE INDEX ID_PERSONALE_IND
ON PERSONALE (documentoIdentita);

CREATE UNIQUE INDEX SID_PERSONALE_IND
ON PERSONALE (e_mail);

CREATE UNIQUE INDEX ID_PRENOTAZIONE_IND
ON PRENOTAZIONE (codicePrenotazione);

CREATE INDEX REF_PRENO_OSPIT_IND
ON PRENOTAZIONE (documentoIdentitaOspite);

CREATE INDEX REF_PRENO_CAMER_IND
ON PRENOTAZIONE (piano, numeroCamera);

CREATE INDEX REF_PRENO_STAGI_IND
ON PRENOTAZIONE (dataInizioStagione);

CREATE UNIQUE INDEX ID_PULIZIA_IND
ON PULIZIA (piano, numeroCamera, data);

CREATE INDEX REF_PULIZ_PERSO_IND
ON PULIZIA (documentoIdentitaAddetto);

CREATE UNIQUE INDEX ID_RECENSIONE_IND
ON RECENSIONE (codiceRecensione);

CREATE UNIQUE INDEX SID_RECEN_PRENO_IND
ON RECENSIONE (codicePrenotazione);

CREATE UNIQUE INDEX ID_SERVIZIO_AGGIUNTIVO_IND
ON SERVIZIO_AGGIUNTIVO (nome);

CREATE UNIQUE INDEX ID_STAGIONE_IND
ON STAGIONE (dataInizio);