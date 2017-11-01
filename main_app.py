# An application about recording favorite songs & info

import os
from flask import Flask, render_template, session, redirect, url_for, flash
from flask_script import Manager, Shell
# from flask_moment import Moment # requires pip/pip3 install flask_moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Required
from flask_sqlalchemy import SQLAlchemy
# from flask_sqlalchemy import Table, Column, Integer, ForeignKey, String, DateTime, Date, Time
# from flask_sqlalchemy import relationship, backref

# from flask_migrate import Migrate, MigrateCommand # needs: pip/pip3 install flask-migrate
##finish tempalte and finish the view function
## template to show all the artists and the number of songs they've written
## the rest of the view function necessary for the /all_songs route (but we've provided the all_song.html template)
# Configure base directory of app
basedir = os.path.abspath(os.path.dirname(__file__))

# Application configurations
app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'hard to guess string from si364 (thisisnotsupersecure)'
# app.config['SQLALCHEMY_DATABASE_URI'] =\
    # 'sqlite:///' + os.path.join(basedir, 'data.sqlite') # Determining where your database file will be stored, and what it will be called, with SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://localhost/songs_data" #TODO: Database URI that's been created - need to create a database called songs_data to make this work OR create a new database and edit the URL to have its name!
## database called songs_data
## this URI specifies the URI you're using.
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Set up Flask debug stuff
manager = Manager(app)
# moment = Moment(app) # For time # Later
db = SQLAlchemy(app) # For database use
## when you use SQLAlchemy, can use SQLAlchemy
## if using SQLAlchemy, can use db command

#########
######### Everything above this line is important/useful setup, not problem-solving.
#########

##### Set up Models #####
##more complicated than section. set up association table, skip past that for now

# Set up association Table between artists and albums for many-many relationship
collections = db.Table('collections',db.Column('album_id',db.Integer, db.ForeignKey('albums.id')),db.Column('artist_id',db.Integer, db.ForeignKey('artists.id')))
##association table between albums and artists possible called collections. now want another table definining the relationship between the two. one row for every unique artists and album combination.
##table variable called collections, db.Table declares relationship table. one column is album id (foreign key from albums table), album id (foreign key), in either one of the tables you're referring to, need to set up relationship
## set up album model, artist model, song model, each one model, each representing one table. album where each row is one album, table called artist where each row is one artist and song where each song is one song.
## songs can only have one artist but an artist can have many songs. artists  can be on many albums, and an artist could have many artists (many to many)

class Album(db.Model):
    __tablename__ = "albums"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    artists = db.relationship('Artist',secondary=collections,backref=db.backref('albums',lazy='dynamic'),lazy='dynamic')
    ## creates association table as long as you have correct set up in table up here.
    songs = db.relationship('Song',backref='Album') ## one to many relationship. with song table that references that album table.
    ##albums have many songs, so we have one to many relationship

class Artist(db.Model):
    __tablename__ = "artists"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    songs = db.relationship('Song',backref='Artist')

    def __repr__(self):
        return "{} (ID: {})".format(self.name,self.id)

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64),unique=True) # Only unique title songs
    album_id = db.Column(db.Integer, db.ForeignKey("albums.id"))
    artist_id = db.Column(db.Integer, db.ForeignKey("artists.id"))
    genre = db.Column(db.String(64))

    def __repr__(self):
        return "{} by {} | {}".format(self.title,self.artist, self.genre)

##### Set up Forms #####

class SongForm(FlaskForm):
    song = StringField("What is the title of your favorite song?", validators=[Required()])
    artist = StringField("What is the name of the artist who performs it?",validators=[Required()])
    genre = StringField("What is the genre of that song?", validators
        =[Required()])
    album = StringField("What is the album this song is on?", validators
        =[Required()])
    submit = SubmitField('Submit')

##### Helper functions

## For database additions / get_or_create functions

def get_or_create_artist(db_session,artist_name):
    artist = db_session.query(Artist).filter_by(name=artist_name).first()
    if artist:
        return artist
    else:
        artist = Artist(name=artist_name)
        db_session.add(artist)
        db_session.commit()
        return artist

    ## even if you have a unique constraint, if you try to add a title that has same title as new song, you'll get an error. i must decide to make sure that if i try to enter a song with the same title, it'll give me the other song i already saved. 

def get_or_create_album(db_session, album_name, artists_list=[]):
    album = db_session.query(Album).filter_by(name=album_name).first() # by name filtering for album
    if album:
        return album
    else:
        album = Album(name=album_name)
        for artist in artists_list:
            artist = get_or_create_artist(db_session,artist)
            album.artists.append(artist)
        db_session.add(album)
        db_session.commit()
    return album

def get_or_create_song(db_session, song_title, song_artist, song_album, song_genre):
    song = db_session.query(Song).filter_by(title=song_title).first()
    if song:
        return song
    else:
        artist = get_or_create_artist(db_session, song_artist)
        album = get_or_create_album(db_session, song_album, artists_list=[song_artist]) # list of one song artist each time -- check out get_or_create_album and get_or_create_artist!
        song = Song(title=song_title,genre=song_genre,artist_id=artist.id)
        db_session.add(song)
        db_session.commit()
        return song




##### Set up Controllers (view functions) #####

## Error handling routes
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

## Main route

@app.route('/', methods=['GET', 'POST'])
def index():
    songs = Song.query.all()
    num_songs = len(songs)
    form = SongForm()
    if form.validate_on_submit():
        if db.session.query(Song).filter_by(title=form.song.data).first(): # If there's already a song with that title, though...nvm, can't. Gotta add something like "(covered by..)" in the title, or whatever
            flash("You've already saved a song with that title!") # Sends to get_flashed_messages where this is redirecting to!
        get_or_create_song(db.session,form.song.data, form.artist.data, form.album.data, form.genre.data)
        return redirect(url_for('see_all'))
    return render_template('index.html', form=form,num_songs=num_songs)

@app.route('/all_songs')
def see_all():
    all_songs = [] # To be tuple list of title, genre
    songs = Song.query.all()
    for item in songs:
        songs[]
        all_songs_tuple = Song.query.filter_by(item.title), Song.query.filter_by(item.artist.id), Song.query.filter_by(item.genre)
        all_songs.append(all_songs_tuple)
    return render_template('all_songs.html', all_songs = all_songs)


    # Complete this view function...
    # Iterate over the songs from the query
    # For each one, query for the artist object
    # Append tuples to the all_songs list: the song title and the artist's name and the song's genre
    # Return appropriate data for template with render_template
    return "Fill in the rest of this route to render a template!"

@app.route('/all_artists')
def see_all_artists():
    artists = Artist.query.all()
    names = [(a.name, len(Song.query.filter_by(artist_id=a.id).all())) for a in artists]
    return render_template('all_artists.html',artist_names=names)

if __name__ == '__main__':
    db.create_all()
    app.run() # NEW: run with this: python main_app.py runserver
    # Also provides more tools for debugging
