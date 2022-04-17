from urllib import response
from flask import Blueprint, request, render_template, redirect
from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
import sqlalchemy
from environs import Env
import datetime
import psycopg2
import numpy as np

env = Env()
env.read_env()

DATABASE_SERVER='localhost'
DATABASE_PORT='5432'
DATABASE_NAME='postgres'
DATABASE_USERNAME='postgres'
DATABASE_PASSWORD='admin'

imdb_mod = Blueprint('imdb', __name__)

@imdb_mod.route('top-250-movies', methods=['GET'])
@imdb_mod.route('top-250-movies/<msg>', methods=['GET'])
def top_250_movies_page(msg=None):
    
    return render_template('imdb/top_250_movies.html', msg=msg)
    # return render_template('imdb/index.html', msg=msg)

@imdb_mod.route('get-top-250-movies', methods=['GET', 'POST'])
def get_top_250_movies():
    url_path = request.form['url']
    print(url_path)
    
    if url_path is None:
        msg = f"URL is missing"
        url = f'/imdb/top-250-movies/{msg}'
        return redirect(url)

    # Downloading imdb top 250 movie's data
    # url = 'http://www.imdb.com/chart/top'
    url = url_path
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')

    movies = soup.select('td.titleColumn')
    links = [a.attrs.get('href') for a in soup.select('td.titleColumn a')]
    crew = [a.attrs.get('title') for a in soup.select('td.titleColumn a')]

    ratings = [b.attrs.get('data-value')
            for b in soup.select('td.posterColumn span[name=ir]')]

    votes = [b.attrs.get('data-value')
            for b in soup.select('td.ratingColumn strong')]

    list = []

    # create a empty list for storing
    # movie information
    list = []

    # Iterating over movies to extract
    # each movie's details
    for index in range(0, len(movies)):
        # Separating  movie into: 'place',
        # 'title', 'year'
        movie_string = movies[index].get_text()
        movie = (' '.join(movie_string.split()).replace('.', ''))
        movie_title = movie[len(str(index)) + 1:-7]
        year = re.search('\((.*?)\)', movie_string).group(1)
        place = movie[:len(str(index)) - (len(movie))]
        data = {"movie_title": movie_title,
                "year": year,
                "place": place,
                "star_cast": crew[index],
                "rating": ratings[index],
                "vote": votes[index],
                "link": links[index]}
        list.append(data)

    db_setting = f'postgresql+psycopg2://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_SERVER}:{DATABASE_PORT}/{DATABASE_NAME}'

    engine = sqlalchemy.create_engine(db_setting)

    # load data to database
    df = pd.DataFrame(list)
    df['director'] = df['star_cast'].str.split(',').str[0]
    df['genre'] = np.random.choice(['crime', 'Action', 'Adventure', 'Drama', 'Thriller'], size=len(df))
    df.to_sql('imdb_top250_movies', engine, if_exists='replace')
    x = len(list)
    msg = f"{x} total row loaded for IMDB"
    url = f'/imdb/top-250-movies/{msg}'
    return redirect(url)


@imdb_mod.route('db-backup', methods=['GET'])
def exec_db_backup():
    d_backup = str(datetime.datetime.now()).replace('.', '').replace(':', '')
    t_backup_file = str(d_backup) + "-" + 'db_backup'
    t_backup_file += ".sql"
    conn = psycopg2.connect(
        host=DATABASE_SERVER,
        database=DATABASE_NAME,
        user=DATABASE_USERNAME,
        password=DATABASE_PASSWORD,
        port=DATABASE_PORT
    )
    cur = conn.cursor()
    cur.execute('select * from public.imdb_top250_movies')
    file = open(t_backup_file, 'w')
    for row in cur:
        
        row = str(row).replace('None', 'null')
        file.write("insert into imdb_top250_movies values " + row + ";")
        
    msg = f"Database backup successfully"
    url = f'/imdb/top-250-movies/{msg}'
    return redirect(url)


@imdb_mod.route('get-top-10-movies', methods=['GET'])
def get_top_10_movies():
    conn = psycopg2.connect(
        host=DATABASE_SERVER,
        database=DATABASE_NAME,
        user=DATABASE_USERNAME,
        password=DATABASE_PASSWORD,
        port=DATABASE_PORT
    )
    cur = conn.cursor()
    cur.execute('select * from public.imdb_top250_movies order by cast(place as int) limit 10')
    l = []
    for row in cur:
        l.append(row)
    return render_template('imdb/top_250_movies.html', top_10_list=l)

@imdb_mod.route('year-wise-count', methods=['GET'])
def year_wise_count():
    conn = psycopg2.connect(
        host=DATABASE_SERVER,
        database=DATABASE_NAME,
        user=DATABASE_USERNAME,
        password=DATABASE_PASSWORD,
        port=DATABASE_PORT
    )
    cur = conn.cursor()
    cur.execute('SELECT * FROM public.imdb_top250_movies where cast(year as int) =2000 ')
    y = []
    for row in cur:
        y.append(row)
    return render_template('imdb/top_250_movies.html', top_10_list=y)

@imdb_mod.route('action-movies', methods=['GET'])
def action_movies():
    conn = psycopg2.connect(
        host=DATABASE_SERVER,
        database=DATABASE_NAME,
        user=DATABASE_USERNAME,
        password=DATABASE_PASSWORD,
        port=DATABASE_PORT
    )
    cur = conn.cursor()
    cur.execute("SELECT * FROM public.imdb_top250_movies where genre ='Action'")
    action = []
    for row in cur:
        action.append(row)
    return render_template('imdb/top_250_movies.html', top_10_list=action)

@imdb_mod.route('drama-movies', methods=['GET'])
def drama_movies():
    conn = psycopg2.connect(
        host=DATABASE_SERVER,
        database=DATABASE_NAME,
        user=DATABASE_USERNAME,
        password=DATABASE_PASSWORD,
        port=DATABASE_PORT
    )
    cur = conn.cursor()
    cur.execute("SELECT * FROM public.imdb_top250_movies where genre ='Drama'")
    drama = []
    for row in cur:
        drama.append(row)
    return render_template('imdb/top_250_movies.html', top_10_list=drama)

@imdb_mod.route('director-count', methods=['GET'])
def director_count():
    conn = psycopg2.connect(
        host=DATABASE_SERVER,
        database=DATABASE_NAME,
        user=DATABASE_USERNAME,
        password=DATABASE_PASSWORD,
        port=DATABASE_PORT
    )
    cur = conn.cursor()
    cur.execute("SELECT * FROM public.imdb_top250_movies where director ='Christopher Nolan (dir.)'")
    director = []
    for row in cur:
        director.append(row)
    return render_template('imdb/top_250_movies.html', top_10_list=director)


@imdb_mod.route('db-restore', methods=['GET'])
def exec_db_restore():

    conn = psycopg2.connect(
        host=DATABASE_SERVER,
        database=DATABASE_NAME,
        user=DATABASE_USERNAME,
        password=DATABASE_PASSWORD,
        port=DATABASE_PORT
    )
    cur = conn.cursor()
    cur.execute('CREATE DATABASE postgres_restore')
    conn = psycopg2.connect(
        host=DATABASE_SERVER,
        database='postgres_restore',
        user=DATABASE_USERNAME,
        password=DATABASE_PASSWORD,
        port=DATABASE_PORT
    )

    cursor = conn.cursor()
    cursor.execute(
        f'CREATE TABLE IMDB_RESTORE SELECT * FROM public.imdb_top250_movies')

    msg = f"Database Recovered successfully"
    url = f'/imdb/top-250-movies/{msg}'
    return redirect(url)