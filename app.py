#! /usr/bin/python3.5
# -*- coding:utf-8 -*-
from passlib.hash import argon2
from flask import Flask, render_template, url_for, request, g, redirect, session
import mysql.connector
import atexit
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

app = Flask(__name__)
app.config.from_object('config')
app.config.from_object('secret_config')



def get_status(url):
    status_code = 999
    try:
        r = requests.get(url, timeout=3)
        r.raise_for_status()
        status_code = r.status_code
    except requests.exceptions.HTTPError as errh:
        status_code = r.status_code
    except requests.exceptions.ConnectionError as errc:
        pass
    except requests.exceptions.Timeout as errt:
        pass
    except requests.exceptions.RequestException as err:
        pass
    return str(status_code)

def insert_histo(etat, id_site):
    db = get_db()
    donnees = {'status': etat, 'website_id': id_site}
    db.execute('INSERT INTO logs (etats, website_id) VALUES (%(status)s, %(website_id)s)',donnees)

def check_status():
    with app.app_context():
        db = get_db()
        db.execute('SELECT id, link FROM website_list')
        urls = db.fetchall()

        for url in urls:
            id = url[0]
            link = url[1]
            status_code = get_status(link)

            insert_histo(status_code, id)

        g.mysql_connection.commit()

scheduler = BackgroundScheduler()
scheduler.start()
scheduler.add_job(
    func=check_status,
    trigger=IntervalTrigger(seconds=120),
    id='check_status',
    name='Insert website status',
    replace_existing=True)
atexit.register(lambda: scheduler.shutdown())


def connect_db () :
    g.mysql_connection = mysql.connector.connect(
        host = app.config['DATABASE_HOST'],
        user = app.config['DATABASE_USER'],
        password = app.config['DATABASE_PASSWORD'],
        database = app.config['DATABASE_NAME']
    )   

    g.mysql_cursor = g.mysql_connection.cursor()
    return g.mysql_cursor

def get_db () :
    if not hasattr(g, 'db') :
        g.db = connect_db()
    return g.db

@app.teardown_appcontext
def close_db (error) :
    if hasattr(g, 'db') :
        g.db.close()

@app.route('/')
def index () :
    db = get_db()
    requete = 'SELECT w.id, link, etats, site_name, date FROM logs l, website_list w WHERE l.website_id = w.id AND date = (SELECT MAX(date) from logs l2 where l2.website_id = w.id) GROUP BY link, site_name, w.id, etats, date '
    db.execute(requete)
    sites_etat = db.fetchall()
    return render_template('index.html', sites_etat=sites_etat)


@app.route('/site/<int:id>/')
def site(id):
	db = get_db()
	requete = 'SELECT site_name, link, date, etats FROM website_list w JOIN logs l ON w.id = l.website_id WHERE w.id = %(id_site)s ORDER BY date DESC'
	db.execute(requete, {'id_site': id})
	logs = db.fetchall()
	return render_template('site.html', logs=logs)

@app.route('/login/', methods = ['GET', 'POST'])
def login () :
    pseudo = str(request.form.get('pseudo'))
    password = str(request.form.get('password'))

    db = get_db()
    db.execute('SELECT pseudo, password, is_admin FROM user WHERE pseudo = %(pseudo)s', {'pseudo' : pseudo})
    users = db.fetchall()

    valid_user = False
    for user in users :
        if argon2.verify(password, user[1]) :
            valid_user = user

    if valid_user :
        session['user'] = valid_user
        return redirect(url_for('admin'))

    return render_template('login.html')

@app.route('/admin/')
def admin () :
    if not session.get('user') or not session.get('user')[2] :
        return redirect(url_for('login'))

    db = get_db()
    requete = 'SELECT w.id, link, etats, site_name, date FROM logs l, website_list w WHERE l.website_id = w.id AND date = (SELECT MAX(date) from logs l2 where l2.website_id = w.id) GROUP BY link, site_name, w.id, etats, date '
    db.execute(requete)
    sites_etat = db.fetchall()

    return render_template('admin.html', user = session['user'], sites_etat = sites_etat)

@app.route('/admin/add/', methods=['POST', 'GET'])
def add () :
    if not session.get('user') or not session.get('user')[2] :
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = str(request.form.get('name'))
        website = str(request.form.get('url'))
        db = get_db()
        db.execute('INSERT INTO website_list (site_name, link) VALUES(%(name)s, %(website)s)',{'name' : name,'website' : website})
        g.mysql_connection.commit()
    return render_template('add_website.html')

@app.route('/admin/edit/<int:id>', methods=['POST', 'GET'])
def edit (id) :
    if not session.get('user') or not session.get('user')[2] :
        return redirect(url_for('login'))
    
    db = get_db()
    db.execute('SELECT link, site_name FROM website_list WHERE id = %(id)s',{'id' : id})
    site = db.fetchall()

    if request.method == 'POST':
        name = str(request.form.get('name'))
        website = str(request.form.get('url'))
        db.execute('UPDATE website_list SET site_name = %(name)s, link = %(website)s WHERE id = %(id)s', {'name' : name, 'website' : website, 'id' : id})
        g.mysql_connection.commit()
        return redirect(url_for('admin'))
    return render_template('edit_website.html', site = site)


@app.route('/admin/delete/<int:id>')
def delete (id) :
    if not session.get('user') or not session.get('user')[2] :
        return redirect(url_for('login'))

    db = get_db()
    requete = 'DELETE FROM website_list WHERE id = %(id)s'
    db.execute(requete, {'id': id})
    g.mysql_connection.commit()
    return redirect(url_for('admin'))

@app.route('/admin/logout/')
def logout () :
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')