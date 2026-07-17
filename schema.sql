CREATE TABLE IF NOT EXISTS aufgabensteller (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    web TEXT,
    archiviert INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS betreuer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    web TEXT,
    archiviert INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS studenten (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    archiviert INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS oberseminare (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dt TEXT NOT NULL,
    location TEXT NOT NULL,
    sichtbar INTEGER DEFAULT 1,
    archiviert INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS themen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ba INTEGER DEFAULT 0,
    ma INTEGER DEFAULT 0,
    sichtbar INTEGER DEFAULT 1,
    vergeben INTEGER DEFAULT 0,
    aufgabensteller_id INTEGER,
    titel TEXT NOT NULL,
    beschreibung TEXT,
    archiviert INTEGER DEFAULT 0,
    FOREIGN KEY(aufgabensteller_id) REFERENCES aufgabensteller(id)
);

CREATE TABLE IF NOT EXISTS themen_betreuer (
    thema_id INTEGER,
    betreuer_id INTEGER,
    FOREIGN KEY(thema_id) REFERENCES themen(id),
    FOREIGN KEY(betreuer_id) REFERENCES betreuer(id)
);

CREATE TABLE IF NOT EXISTS abschlussarbeiten (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    typ TEXT NOT NULL,
    anmeldetag TEXT,
    abgabetag TEXT,
    aufgabensteller_id INTEGER,
    student_id INTEGER,
    titel TEXT NOT NULL,
    notiz TEXT,
    antrittsvortrag_id INTEGER,
    abschlussvortrag_id INTEGER,
    archiviert INTEGER DEFAULT 0,
    FOREIGN KEY(aufgabensteller_id) REFERENCES aufgabensteller(id),
    FOREIGN KEY(student_id) REFERENCES studenten(id),
    FOREIGN KEY(antrittsvortrag_id) REFERENCES oberseminare(id),
    FOREIGN KEY(abschlussvortrag_id) REFERENCES oberseminare(id)
);

CREATE TABLE IF NOT EXISTS arbeiten_betreuer (
    arbeit_id INTEGER,
    betreuer_id INTEGER,
    FOREIGN KEY(arbeit_id) REFERENCES abschlussarbeiten(id),
    FOREIGN KEY(betreuer_id) REFERENCES betreuer(id)
);

-- Stores the manual sorting order of presentations for each oberseminar
CREATE TABLE IF NOT EXISTS oberseminar_presentations (
    oberseminar_id INTEGER,
    arbeit_id INTEGER,
    sort_order INTEGER,
    FOREIGN KEY(oberseminar_id) REFERENCES oberseminare(id),
    FOREIGN KEY(arbeit_id) REFERENCES abschlussarbeiten(id)
);
