#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys
# from flask_wtf.csrf import CSRFProtect
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
SQLALCHEMY_TRACK_MODIFICATIONS = False
db = SQLAlchemy(app)
# csrf = CSRFProtect(app)

# TODO: connect to a local postgresql database

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Show(db.Model):
    __tablename__ = 'shows'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)
    start_time = db.Column(db.DateTime(), nullable=False)

    artist = db.relationship('Artist', back_populates='art_shows')
    venue = db.relationship('Venue', back_populates='ven_shows')


class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(120))

    ven_shows = db.relationship('Show', back_populates='venue')

class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(120))

    art_shows = db.relationship('Show', back_populates='artist')


# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  data=[]
  locations = Venue.query.with_entities(Venue.city, Venue.state).distinct().group_by(Venue.city, Venue.state).all()

  for location in locations:
    shows = Venue.query.filter(Venue.state == location.state).filter(Venue.city == location.city).all()

    for show in shows:
      venue_data = {
        'id': show.id,
        'name': show.name,
        'num_upcoming_shows': len(db.session.query(Show).filter(Show.start_time > datetime.now()).all())
      }

      location_data = {
        'city': location.city,
        'state': location.state,
        'venues': []
      }

      location_data['venues'].append(venue_data)
      print(venue_data)

    data.append(location_data)
    print(data)

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term', '')

    venue_search = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()

    response = {
      "count": len(venue_search),
      "data": venue_search
    }

    # print(response)

    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  data = Venue.query.get(venue_id)
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm(request.form, meta={"csrf": False})
  if form.validate():
      try:
        create_venue = Venue(name=request.form['name'], city=request.form['city'], state=request.form['state'], address=request.form['address'], phone=request.form['phone'], image_link=request.form['image_link'], genres=request.form.getlist('genres'), facebook_link=request.form['facebook_link'], website_link=request.form['website_link'], seeking_talent = request.form.get('seeking_talent', type=bool), seeking_description=request.form['seeking_description'])
        db.session.add(create_venue)
        db.session.commit()

        flash('Venue '+form.name.data+' was successfully Created!')  

      except:
        
        flash('An error occurred. Venue '+ form.name.data + ' could not be Created!.')
      
      finally:

        db.session.close()

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    Venue.query.filter(Venue.id == venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.order_by(Artist.id).all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term', '')

  artist_venue = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()

  response = {
    "count": len(artist_venue),
    "data": artist_venue
  }

  # print(response)

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  data = Artist.query.get(artist_id)
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.filter(Artist.id == artist_id).first()
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm(request.form)
  
  if form.validate():

    try:
      artist = Artist.query.get(artist_id)
      artist.name = request.form['name']
      artist.city = request.form['city']
      artist.state = request.form['state'] 
      artist.phone = request.form['phone'] 
      artist.genres = request.form['genres'] 
      artist.image_link = request.form['image_link'] 
      artist.facebook_link = request.form['facebook_link'] 
      artist.website_link = request.form['website_link'] 
      artist.seeking_venue = request.form.get('seeking_venue', type=bool)
      artist.seeking_description = request.form['seeking_description']

      db.session.commit()
    except:
      db.session.rollback()
      print(sys.exc_info())
    finally:
      db.session.close()

  else:
    print(form.errors)

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.filter(Venue.id == venue_id).first()
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

  form = VenueForm(request.form)

  if form.validate():

    try:
      venue = Venue.query.get(venue_id)

      venue.name = request.form['name']
      venue.city = request.form['city']
      venue.state = request.form['state']
      venue.address = request.form['address']
      venue.phone = request.form['phone']
      venue.image_link = request.form['image_link']
      venue.genres = request.form['genres']
      venue.facebook_link = request.form['facebook_link']
      venue.website_link = request.form['website_link']
      venue.seeking_talent = request.form.get('seeking_talent', type=bool)
      venue.seeking_description = request.form['seeking_description']

      db.session.commit()

    except:
      db.session.rollback()
      print(sys.exc_info())
    finally:
      db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm(request.form, meta={"csrf": False})
  if form.validate():
      try:
        create_artist = Artist(name=request.form['name'], city=request.form['city'], state=request.form['state'], phone=request.form['phone'], genres=request.form['genres'], image_link=request.form['image_link'], facebook_link=request.form['facebook_link'], website_link=request.form['website_link'], seeking_venue = request.form.get('seeking_venue', type=bool), seeking_description=request.form['seeking_description'] )
        db.session.add(create_artist)
        db.session.commit()

        flash('Artist '+form.name.data+' was successfully Created!')  

      except:
        db.session.rollback()
        flash('An error occurred. Artist '+ form.name.data + ' could not be Created!.')
      
      finally:

        db.session.close()
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():

  data=[]
  shows = Show.query.all()

  for show in shows:
    show_data = {
      'venue_id': show.venue_id,
      'venue_name': show.venue.name,
      'artist_id': show.artist_id,
      'artist_name': show.artist.name,
      'artist_image_link': show.artist.image_link,
      'start_time': str(show.start_time)
    }
    data.append(show_data)

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:
    create_show = Show(artist_id=request.form['artist_id'], venue_id=request.form['venue_id'], start_time=request.form['start_time'])
    db.session.add(create_show)
    db.session.commit()
    flash('Show was successfully added')
  except:
    db.session.rollback()
  finally:
    db.session.close()

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
