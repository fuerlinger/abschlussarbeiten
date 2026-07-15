# -*- coding: utf-8 -*-
import sqlite3
import os
import markdown
from datetime import datetime
from flask import Flask, render_template, request, g, redirect, make_response

app = Flask(__name__)
DATABASE = 'mnm.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    if not os.path.exists(DATABASE):
        with app.app_context():
            db = get_db()
            with app.open_resource('schema.sql', mode='r') as f:
                db.cursor().executescript(f.read())
            db.commit()

@app.template_filter('datetime_de')
def datetime_de_filter(s):
    if not s: return ""
    try:
        dt = datetime.strptime(s, '%Y-%m-%dT%H:%M')
        return dt.strftime('%d.%m.%Y, %H:%M Uhr')
    except ValueError:
        return s

@app.template_filter('markdown')
def render_markdown(text):
    if not text: return ""
    return markdown.markdown(text)

@app.route('/')
def index():
    return render_template('index.html')

# Generic route to fetch tabs
@app.route('/tab/<name>')
def tab(name):
    db = get_db()
    edit_id = request.args.get('edit', type=int)

    if name == 'status':

        status_data = {
            "aufgabensteller_gesamt" : 0
        }
        result = db.execute('SELECT COUNT(*) FROM aufgabensteller WHERE archiviert=0').fetchone()
        status_data["aufgabensteller_gesamt"] = result[0]
    
        
        return render_template('status.html')
    
    elif name == 'aufgabensteller':
        rows = db.execute('SELECT * FROM aufgabensteller WHERE archiviert=0').fetchall()
        edit_item = db.execute('SELECT * FROM aufgabensteller WHERE id=?', (edit_id,)).fetchone() if edit_id else None
        return render_template('aufgabensteller.html', rows=rows, edit_item=edit_item)
        
    elif name == 'betreuer':
        rows = db.execute('SELECT * FROM betreuer WHERE archiviert=0').fetchall()
        edit_item = db.execute('SELECT * FROM betreuer WHERE id=?', (edit_id,)).fetchone() if edit_id else None
        return render_template('betreuer.html', rows=rows, edit_item=edit_item)

    elif name == 'studenten':
        rows = db.execute('SELECT * FROM studenten WHERE archiviert=0').fetchall()
        edit_item = db.execute('SELECT * FROM studenten WHERE id=?', (edit_id,)).fetchone() if edit_id else None
        return render_template('studenten.html', rows=rows, edit_item=edit_item)
        
    elif name == 'oberseminare':
        rows = db.execute('SELECT * FROM oberseminare WHERE archiviert=0 ORDER BY dt').fetchall()
        edit_item = db.execute('SELECT * FROM oberseminare WHERE id=?', (edit_id,)).fetchone() if edit_id else None
        # Fetch presentations for each oberseminar
        seminare = []
        for r in rows:
            sem = dict(r)
            # Find presentations assigned to this seminar (Antritts or Abschluss) 
            # joined with manual sorting order
            pres = db.execute('''
                SELECT a.id, a.titel, s.name as student_name, a.abschlussvortrag_id, a.antrittsvortrag_id, a.typ
                FROM abschlussarbeiten a
                LEFT JOIN studenten s ON a.student_id = s.id
                LEFT JOIN oberseminar_presentations op ON a.id = op.arbeit_id AND op.oberseminar_id = ?
                WHERE (a.antrittsvortrag_id = ? OR a.abschlussvortrag_id = ?)
                ORDER BY op.sort_order ASC, a.id ASC
            ''', (r['id'], r['id'], r['id'])).fetchall()
            sem['presentations'] = pres
            seminare.append(sem)
        return render_template('oberseminare.html', rows=seminare, edit_item=edit_item)
        
    elif name == 'themen':
        rows = db.execute('''SELECT t.*, a.name as aufgabensteller_name 
                             FROM themen t LEFT JOIN aufgabensteller a ON t.aufgabensteller_id = a.id 
                             WHERE t.archiviert=0''').fetchall()
        edit_item = None
        edit_betreuer_ids = []
        if edit_id:
            edit_item = db.execute('SELECT * FROM themen WHERE id=?', (edit_id,)).fetchone()
            edit_betreuer_ids = [b['betreuer_id'] for b in db.execute('SELECT betreuer_id FROM themen_betreuer WHERE thema_id=?', (edit_id,))]
            
        aufgabensteller = db.execute('SELECT * FROM aufgabensteller').fetchall()
        betreuer = db.execute('SELECT * FROM betreuer WHERE archiviert=0').fetchall()
        
        # Hydrate betreuer names for display
        themen_list = []
        for r in rows:
            t = dict(r)
            b_names = db.execute('''SELECT b.name FROM betreuer b 
                                    JOIN themen_betreuer tb ON b.id = tb.betreuer_id 
                                    WHERE tb.thema_id=?''', (t['id'],)).fetchall()
            t['betreuer_names'] = ", ".join([b['name'] for b in b_names])
            themen_list.append(t)
            
        return render_template('themen.html', rows=themen_list, edit_item=edit_item, 
                               aufgabensteller=aufgabensteller, betreuer=betreuer, edit_betreuer_ids=edit_betreuer_ids)
                               
    elif name == 'abschlussarbeiten':
        rows = db.execute('''SELECT a.*, auf.name as aufgabensteller_name, s.name as student_name,
                             o1.dt as antritts_dt, o2.dt as abschluss_dt
                             FROM abschlussarbeiten a 
                             LEFT JOIN aufgabensteller auf ON a.aufgabensteller_id = auf.id
                             LEFT JOIN studenten s ON a.student_id = s.id
                             LEFT JOIN oberseminare o1 ON a.antrittsvortrag_id = o1.id
                             LEFT JOIN oberseminare o2 ON a.abschlussvortrag_id = o2.id
                             WHERE a.archiviert=0''').fetchall()
        edit_item = None
        edit_betreuer_ids = []
        if edit_id:
            edit_item = db.execute('SELECT * FROM abschlussarbeiten WHERE id=?', (edit_id,)).fetchone()
            edit_betreuer_ids = [b['betreuer_id'] for b in db.execute('SELECT betreuer_id FROM arbeiten_betreuer WHERE arbeit_id=?', (edit_id,))]
            
        aufgabensteller = db.execute('SELECT * FROM aufgabensteller').fetchall()
        studenten = db.execute('SELECT * FROM studenten WHERE archiviert=0').fetchall()
        betreuer = db.execute('SELECT * FROM betreuer WHERE archiviert=0').fetchall()
        oberseminare = db.execute('SELECT * FROM oberseminare WHERE archiviert=0 ORDER BY dt').fetchall()
        
        arbeiten_list = []
        for r in rows:
            ar = dict(r)
            b_names = db.execute('''SELECT b.name FROM betreuer b 
                                    JOIN arbeiten_betreuer ab ON b.id = ab.betreuer_id 
                                    WHERE ab.arbeit_id=?''', (ar['id'],)).fetchall()
            ar['betreuer_names'] = ", ".join([b['name'] for b in b_names])
            arbeiten_list.append(ar)

        return render_template('abschlussarbeiten.html', rows=arbeiten_list, edit_item=edit_item,
                               aufgabensteller=aufgabensteller, studenten=studenten, 
                               betreuer=betreuer, oberseminare=oberseminare, edit_betreuer_ids=edit_betreuer_ids)

    elif name == 'archiv':
        aufgabensteller = db.execute('SELECT * FROM aufgabensteller WHERE archiviert=1').fetchall()
        betreuer = db.execute('SELECT * FROM betreuer WHERE archiviert=1').fetchall()
        studenten = db.execute('SELECT * FROM studenten WHERE archiviert=1').fetchall()
        
        themen = db.execute('SELECT * FROM themen WHERE archiviert=1').fetchall()
        seminare = db.execute('SELECT * FROM oberseminare WHERE archiviert=1').fetchall()
        arbeiten = db.execute('SELECT * FROM abschlussarbeiten WHERE archiviert=1').fetchall()
        return render_template('archiv.html', themen=themen, seminare=seminare, arbeiten=arbeiten,
                               aufgabensteller=aufgabensteller, betreuer=betreuer, studenten=studenten)

# POST Handlers for Add / Edit
@app.route('/api/aufgabensteller', methods=['POST'])
def save_aufgabensteller():
    db = get_db()
    id, name, email, web = request.form.get('id'), request.form.get('name'), request.form.get('email'), request.form.get('web')
    if id:
        db.execute('UPDATE aufgabensteller SET name=?, email=?, web=? WHERE id=?', (name, email, web, id))
    else:
        db.execute('INSERT INTO aufgabensteller (name, email, web) VALUES (?, ?, ?)', (name, email, web))
    db.commit()
    return tab('aufgabensteller')

@app.route('/api/betreuer', methods=['POST'])
def save_betreuer():
    db = get_db()
    id, name, email, web = request.form.get('id'), request.form.get('name'), request.form.get('email'), request.form.get('web')
    if id:
        db.execute('UPDATE betreuer SET name=?, email=?, web=? WHERE id=?', (name, email, web, id))
    else:
        db.execute('INSERT INTO betreuer (name, email, web) VALUES (?, ?, ?)', (name, email, web))
    db.commit()
    return tab('betreuer')

@app.route('/api/studenten', methods=['POST'])
def save_studenten():
    db = get_db()
    id, name, email = request.form.get('id'), request.form.get('name'), request.form.get('email')
    if id:
        db.execute('UPDATE studenten SET name=?, email=? WHERE id=?', (name, email, id))
    else:
        db.execute('INSERT INTO studenten (name, email) VALUES (?, ?)', (name, email))
    db.commit()
    return tab('studenten')

@app.route('/api/oberseminare', methods=['POST'])
def save_oberseminare():
    db = get_db()
    id, dt, loc = request.form.get('id'), request.form.get('dt'), request.form.get('location')
    sichtbar = 1 if request.form.get('sichtbar') else 0
    if id:
        db.execute('UPDATE oberseminare SET dt=?, location=?, sichtbar=? WHERE id=?', (dt, loc, sichtbar, id))
    else:
        db.execute('INSERT INTO oberseminare (dt, location, sichtbar) VALUES (?, ?, ?)', (dt, loc, sichtbar))
    db.commit()
    return tab('oberseminare')

@app.route('/api/themen', methods=['POST'])
def save_themen():
    db = get_db()
    id = request.form.get('id')
    ba = 1 if request.form.get('ba') else 0
    ma = 1 if request.form.get('ma') else 0
    sichtbar = 1 if request.form.get('sichtbar') else 0
    vergeben = 1 if request.form.get('vergeben') else 0
    aufg_id = request.form.get('aufgabensteller_id')
    titel = request.form.get('titel')
    beschr = request.form.get('beschreibung')
    betreuer_ids = request.form.getlist('betreuer_ids')

    if id:
        db.execute('''UPDATE themen SET ba=?, ma=?, sichtbar=?, vergeben=?, aufgabensteller_id=?, 
                      titel=?, beschreibung=? WHERE id=?''', (ba, ma, sichtbar, vergeben, aufg_id, titel, beschr, id))
    else:
        cur = db.execute('''INSERT INTO themen (ba, ma, sichtbar, vergeben, aufgabensteller_id, titel, beschreibung) 
                            VALUES (?, ?, ?, ?, ?, ?, ?)''', (ba, ma, sichtbar, vergeben, aufg_id, titel, beschr))
        id = cur.lastrowid
        
    db.execute('DELETE FROM themen_betreuer WHERE thema_id=?', (id,))
    for b_id in betreuer_ids:
        db.execute('INSERT INTO themen_betreuer (thema_id, betreuer_id) VALUES (?, ?)', (id, b_id))
    db.commit()
    return tab('themen')

@app.route('/api/abschlussarbeiten', methods=['POST'])
def save_abschlussarbeiten():
    db = get_db()
    id = request.form.get('id')
    typ = request.form.get('typ')
    anmeld_dt = request.form.get('anmeldedatum')
    abgabe_dt = request.form.get('abgabedatum') 
    aufg_id = request.form.get('aufgabensteller_id') or None
    stud_id = request.form.get('student_id') or None
    titel = request.form.get('titel')
    antritt = request.form.get('antrittsvortrag_id') if typ == 'MA' else None
    antritt = antritt if antritt else None
    abschluss = request.form.get('abschlussvortrag_id') or None
    betreuer_ids = request.form.getlist('betreuer_ids')

    if id:
        db.execute('''UPDATE abschlussarbeiten SET typ=?, anmeld_dt=?, abgab_dt=?,
                      aufgabensteller_id=?, student_id=?, titel=?, antrittsvortrag_id=?,
                      abschlussvortrag_id=? WHERE id=?''', 
                      (typ, anmeld_dt, abgabe_dt, aufg_id, stud_id, titel, antritt, abschluss, id))
    else:
        cur = db.execute('''INSERT INTO abschlussarbeiten (typ, anmeld_dt, abgabe_dt, aufgabensteller_id, student_id, 
                            titel, antrittsvortrag_id, abschlussvortrag_id) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                            (typ, anmeld_dt, abgabe_dt, aufg_id, stud_id, titel, antritt, abschluss))
        id = cur.lastrowid
        
    db.execute('DELETE FROM arbeiten_betreuer WHERE arbeit_id=?', (id,))
    for b_id in betreuer_ids:
        db.execute('INSERT INTO arbeiten_betreuer (arbeit_id, betreuer_id) VALUES (?, ?)', (id, b_id))
    db.commit()
    return tab('abschlussarbeiten')

# Reorder Presentations
@app.route('/api/reorder_oberseminar/<int:os_id>', methods=['POST'])
def reorder_oberseminar(os_id):
    db = get_db()
    arbeit_ids = request.form.getlist('arbeit_id')
    db.execute('DELETE FROM oberseminar_presentations WHERE oberseminar_id=?', (os_id,))
    for index, a_id in enumerate(arbeit_ids):
        db.execute('INSERT INTO oberseminar_presentations (oberseminar_id, arbeit_id, sort_order) VALUES (?, ?, ?)',
                   (os_id, a_id, index))
    db.commit()
#    return "" # HTMX doesn't need to swap anything if UI is already sorted
    return tab('oberseminare')

# Delete / Archive routes
@app.route('/api/delete/<table_name>/<int:id>', methods=['DELETE'])
def delete_item(table_name, id):
    db = get_db()
    allowed_tables = ['aufgabensteller', 'betreuer', 'studenten', 'oberseminare', 'themen', 'abschlussarbeiten']
    if table_name in allowed_tables:
        db.execute(f'DELETE FROM {table_name} WHERE id=?', (id,))
        db.commit()
    return tab(table_name)

@app.route('/api/archive/<table_name>/<int:id>', methods=['POST'])
def archive_item(table_name, id):
    db = get_db()
    allowed_tables = ['aufgabensteller', 'betreuer', 'studenten', 'oberseminare', 'themen', 'abschlussarbeiten']
    if table_name in allowed_tables:
        db.execute(f'UPDATE {table_name} SET archiviert=1 WHERE id=?', (id,))
        db.commit()
    return tab(table_name)

@app.route('/api/dearchive/<table_name>/<int:id>', methods=['POST'])
def dearchive_item(table_name, id):
    db = get_db()
    allowed_tables = ['aufgabensteller', 'betreuer', 'studenten', 'oberseminare', 'themen', 'abschlussarbeiten']
    if table_name in allowed_tables:
        db.execute(f'UPDATE {table_name} SET archiviert=0 WHERE id=?', (id,))
        db.commit()
    return ""

@app.route('/api/publish/<table_name>', methods=['POST'])
def publish(table_name):
    db = get_db()
    allowed_tables = ['oberseminare', 'themen']
    if table_name in allowed_tables:
        return os.popen('uptime').read()
    return "Not allowed"

@app.route('/api/mailto/<table_name>/<int:id>', methods=['POST'])
def mailto(table_name, id):
    db = get_db()
    allowed_tables = ['oberseminare', 'themen']

    response = make_response()
    response.headers['HX-Redirect'] = 'mailto:oberseminar@example.com?bcc=stude1@example.com&subject=Oberseminar%20am%205.11.2024&body=Einladung%20zum%20oberseminar%20am'
    response.status_code = 200
    return response
    
    
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', debug=True)
