# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from sqlalchemy import or_

from forms import *
from flask_migrate import Migrate
import sys
import collections

collections.Callable = collections.abc.Callable

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String(130)))
    website_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.Text, nullable=True)
    shows = db.relationship('Show', backref='Venue', lazy=True, cascade='all, delete')

    @property
    def upcoming_shows(self):
        upcoming_shows = [item for item in self.shows if item.start_time > datetime.now()]
        return upcoming_shows

    @property
    def upcoming_shows_count(self):
        return len(self.shows_to_come)

    # @property
    # def past_shows(self):
    #     past_shows = [show for show in self.shows if show.start_time < datetime.now()]
    #     return past_shows
    #
    # @property
    # def num_past_shows(self):
    #     return len(self.past_shows)


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.ARRAY(db.String(130)))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.Text, nullable=True)
    shows = db.relationship('Show', backref='Artist', lazy=True)

    @property
    def upcoming_shows(self):
        upcoming_shows = [show for show in self.shows if show.start_time > datetime.now()]
        return upcoming_shows

    @property
    def upcoming_shows_count(self):
        return len(self.upcoming_shows)

    # @property
    # def past_shows(self):
    #     past_shows = [show for show in self.shows if show.start_time < datetime.now()]
    #
    #     return past_shows
    #
    # @property
    # def num_past_shows(self):
    #     return len(self.past_shows)


class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=True)
    start_time = db.Column(db.DateTime, nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    if isinstance(value, str):
        date = dateutil.parser.parse(value)
    else:
        date = value
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    recent_shows = Show.query.order_by(Show.id.desc()).limit(5)
    artist_list = Artist.query.order_by(Artist.id.desc()).limit(10).all()
    venues_list = Venue.query.order_by(Venue.id.desc()).limit(10).all()

    return render_template('pages/home.html', artists=artist_list, venues=venues_list, shows=recent_shows)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    data = []
    places = Venue.query.with_entities(Venue.city, Venue.state).distinct().all()
    for place in places:
        city = place[0]
        state = place[1]
        venues_list = Venue.query.filter_by(city=city, state=state).all()
        shows_list = [show for show in venues_list[0].shows if show.start_time > datetime.now()]
        data.append({
            "city": city,
            "state": state,
            "venues": venues_list,
            "num_upcoming_shows": len(shows_list)
        })

    return render_template('pages/venues.html', areas=data);


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term', '')
    venues_list = Venue.query.filter(Venue.name.ilike('%' + search_term + '%')).all()
    data = []
    for item in venues_list:
        data.append({
            "id": item.id,
            "name": item.name,
            "upcoming_shows_count": len([show for show in item.shows if show.start_time > datetime.now()])
        })

    response = {
        "count": len(venues_list),
        "data": data
    }
    return render_template('pages/search_venues.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue_item = Venue.query.get(venue_id)
    if not venue_item:
        return render_template('errors/404.html')
    else:
        data = {
            "id": venue_item.id,
            "name": venue_item.name,
            "genres": venue_item.genres,
            "address": venue_item.address,
            "city": venue_item.city,
            "state": venue_item.state,
            "phone": venue_item.phone,
            "website": venue_item.website_link,
            "facebook_link": venue_item.facebook_link,
            "seeking_talent": venue_item.seeking_talent,
            "seeking_description": venue_item.seeking_description,
            "image_link": venue_item.image_link,
            "past_shows": [],
            "upcoming_shows": [],
            "past_shows_count": 0,
            "upcoming_shows_count": 0
        }
        for show in venue_item.shows:
            if show.start_time < datetime.now():
                data['past_shows'].append({
                    "show_id": show.id,
                    "show_name": show.name,
                    "artist_id": show.artist_id,
                    "artist_name": show.Artist.name,
                    "artist_image_link": show.Artist.image_link,
                    "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
                })
                data['past_shows_count'] += 1
            else:
                data['upcoming_shows'].append({
                    "show_id": show.id,
                    "show_name": show.name,
                    "artist_id": show.artist_id,
                    "artist_name": show.Artist.name,
                    "artist_image_link": show.Artist.image_link,
                    "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
                })
                data['upcoming_shows_count'] += 1

        return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm(request.form, meta={'csrf': False})
    if form.validate():
        try:
            new_venue = Venue(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                address=form.address.data,
                phone=form.phone.data,
                genres=form.genres.data,
                facebook_link=form.facebook_link.data,
                image_link=form.image_link.data,
                website_link=form.website_link.data,
                seeking_talent=form.seeking_talent.data,
                seeking_description=form.seeking_description.data
            )
            db.session.add(new_venue)
            db.session.commit()
            flash('Venue ' + request.form['name'] + ' was successfully listed!')
        except:
            db.session.rollback()
            flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
        finally:
            db.session.close()
    else:
        message = []
        for field, err in form.errors.items():
            message.append('|'.join(err))
            flash('Error ' + str(message))
        return redirect(url_for('create_venue_submission'))

    return redirect(url_for('venues'))


@app.route('/venues/<venue_id>', methods=['POST'])
def delete_venue(venue_id):
    try:
        venue_item = Venue.query.get(venue_id)
        db.session.delete(venue_item)
        db.session.commit()
        flash(f'{venue_item.name} is deleted successfully')
        return redirect(url_for('index'))
    except:
        db.session.rollback()
        flash('An error occurred. Venue could not be deleted.')
    finally:
        db.session.close()
    return redirect(url_for('delete_venue', venue_id=venue_id))


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    artist_list = Artist.query.with_entities(Artist.id, Artist.name).order_by('name').all()
    return render_template('pages/artists.html', artists=artist_list)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term', '')
    artist_list = Artist.query.filter(Artist.name.ilike('%' + search_term + '%')).all()
    data = []
    for item in artist_list:
        data.append({
            "id": item.id,
            "name": item.name,
            "upcoming_shows_count": len([show for show in item.shows if show.start_time > datetime.now()])
        })

    response = {
        "count": len(artist_list),
        "data": data
    }
    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist_item = Artist.query.get(artist_id)
    if not artist_item:
        return render_template('errors/404.html')
    else:
        data = {
            "id": artist_item.id,
            "name": artist_item.name,
            "genres": artist_item.genres,
            "city": artist_item.city,
            "state": artist_item.state,
            "phone": artist_item.phone,
            "website": artist_item.website_link,
            "facebook_link": artist_item.facebook_link,
            "seeking_venue": artist_item.seeking_venue,
            "seeking_description": artist_item.seeking_description,
            "image_link": artist_item.image_link,
            "past_shows": [],
            "upcoming_shows": [],
            "past_shows_count": 0,
            "upcoming_shows_count": 0
        }
        for show in artist_item.shows:
            if show.start_time < datetime.now():
                data['past_shows'].append({
                    "show_id": show.id,
                    "show_name": show.name,
                    "venue_id": show.venue_id,
                    "venue_name": show.Venue.name,
                    "venue_image_link": show.Venue.image_link,
                    "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
                })
                data['past_shows_count'] += 1
            else:
                data['upcoming_shows'].append({
                    "show_id": show.id,
                    "show_name": show.name,
                    "venue_id": show.venue_id,
                    "venue_name": show.Venue.name,
                    "venue_image_link": show.Venue.image_link,
                    "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
                })
                data['upcoming_shows_count'] += 1

        return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    model = Artist.query.get(artist_id)
    form = ArtistForm(obj=model)

    return render_template('forms/edit_artist.html', form=form, artist=model)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm(request.form, meta={'csrf': False})
    if form.validate():
        try:
            artist_item = Artist.query.get(artist_id)
            artist_item.name = form.name.data
            artist_item.city = form.city.data
            artist_item.state = form.state.data
            artist_item.phone = form.phone.data
            artist_item.genres = form.genres.data
            artist_item.facebook_link = form.facebook_link.data
            artist_item.image_link = form.image_link.data
            artist_item.website_link = form.website_link.data
            artist_item.seeking_venue = form.seeking_venue.data
            artist_item.seeking_description = form.seeking_description.data
            db.session.commit()
            flash('Artist ' + request.form['name'] + ' was successfully updated!')
        except:
            db.session.rollback()
            flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
        finally:
            db.session.close()
    else:
        message = []
        for field, err in form.errors.items():
            message.append('|'.join(err))
            flash('Error ' + str(message))
        return redirect(url_for('edit_artist_submission', artist_id=artist_id))

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    model = Venue.query.get(venue_id)
    form = VenueForm(obj=model)
    return render_template('forms/edit_venue.html', form=form, venue=model)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm(request.form, meta={'csrf': False})
    if form.validate():
        try:
            venue_item = Venue.query.get(venue_id)
            venue_item.name = form.name.data
            venue_item.city = form.city.data
            venue_item.state = form.state.data
            venue_item.address = form.address.data
            venue_item.phone = form.phone.data
            venue_item.genres = form.genres.data
            venue_item.facebook_link = form.facebook_link.data
            venue_item.image_link = form.image_link.data
            venue_item.website_link = form.website_link.data
            venue_item.seeking_talent = form.seeking_talent.data
            venue_item.seeking_description = form.seeking_description.data
            db.session.commit()
            flash('Venue ' + request.form['name'] + ' was successfully updated!')
        except:
            db.session.rollback()
            flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
        finally:
            db.session.close()
    else:
        message = []
        for field, err in form.errors.items():
            message.append('|'.join(err))
            flash('Error ' + str(message))
        return redirect(url_for('edit_venue_submission', venue_id=venue_id))

    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


# Create an artist
@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm(request.form, meta={'csrf': False})
    if form.validate():
        try:
            artist_item = Artist(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                phone=form.phone.data,
                genres=form.genres.data,
                facebook_link=form.facebook_link.data,
                image_link=form.image_link.data,
                website_link=form.website_link.data,
                seeking_venue=form.seeking_venue.data,
                seeking_description=form.seeking_description.data
            )
            db.session.add(artist_item)
            db.session.commit()
            flash('Artist ' + request.form['name'] + ' was successfully listed!')
        except:
            db.session.rollback()
            flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
        finally:
            db.session.close()
    else:
        message = []
        for field, err in form.errors.items():
            message.append('|'.join(err))
            flash('Error ' + str(message))
        return redirect(url_for('create_artist_submission'))

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    data = []
    show_list = Show.query.join(
        Venue, (Venue.id == Show.venue_id)
    ).join(
        Artist, (Artist.id == Show.artist_id)
    ).with_entities(
        Show.id,
        Show.name,
        Show.venue_id,
        Venue.name.label('venue_name'),
        Show.artist_id,
        Artist.name.label('artist_name'),
        Artist.image_link,
        Show.start_time
    )

    for item in show_list:
        data.append({
            "id": item.id,
            "show_name": item.name,
            "venue_id": item.venue_id,
            "start_time": item.start_time,
            "venue_name": item.venue_name,
            "artist_id": item.artist_id,
            "artist_name": item.artist_name,
            "artist_image_link": item.image_link
        })

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm(request.form, meta={'csrf': False})
    if form.validate():
        try:
            show_item = Show(
                name=form.name.data,
                start_time=form.start_time.data,
                artist_id=form.artist_id.data,
                venue_id=form.venue_id.data
            )
            db.session.add(show_item)
            db.session.commit()
            flash('Show was successfully listed!')
        except:
            db.session.rollback()
            flash('An error occurred. Show could not be listed.')
        finally:
            db.session.close()
    else:
        message = []
        for field, err in form.errors.items():
            message.append('|'.join(err))
            flash('Error ' + str(message))
        return redirect(url_for('create_show_submission'))

    return render_template('pages/home.html')


@app.route('/shows/<int:show_id>/edit', methods=['GET'])
def edit_show(show_id):
    model = Show.query.get(show_id)
    form = ShowForm(obj=model)
    return render_template('forms/edit_show.html', form=form, show=model)


@app.route('/shows/<int:show_id>/edit', methods=['POST'])
def edit_show_submission(show_id):
    form = ShowForm(request.form, meta={'csrf': False})
    if form.validate():
        try:
            show_item = Show.query.get(show_id)
            show_item.name = form.name.data
            show_item.start_time = form.start_time.data
            show_item.artist_id = form.artist_id.data
            show_item.venue_id = form.venue_id.data
            db.session.commit()
            flash('Show was successfully updated!')
        except:
            db.session.rollback()
            flash('An error occurred. Show could not be updated.')
        finally:
            db.session.close()
    else:
        message = []
        for field, err in form.errors.items():
            message.append('|'.join(err))
            flash('Error ' + str(message))
        return redirect(url_for('edit_show_submission', show_id=show_id))

    return redirect(url_for('show_show', show_id=show_id))


@app.route('/shows/search', methods=['POST'])
def search_shows():
    search_term = request.form.get('search_term', '')
    search_result = Show.query.join(
        Venue, (Venue.id == Show.venue_id)
    ).join(
        Artist, (Artist.id == Show.artist_id)
    ).with_entities(
        Show.id,
        Show.name,
        Show.venue_id,
        Venue.name.label('venue_name'),
        Show.artist_id,
        Artist.name.label('artist_name'),
        Artist.image_link,
        Show.start_time
    ).filter(
        Show.start_time >= datetime.now()
    ).filter(
        or_(
            Show.name.ilike('%' + search_term + '%'),
            Artist.name.ilike("%" + search_term + "%"),
            Venue.name.ilike("%" + search_term + "%")
        )
    )

    data = []
    for item in search_result:
        data.append({
            "id": item.id,
            "show_name": item.name,
            "venue_id": item.venue_id,
            "start_time": item.start_time,
            "venue_name": item.venue_name,
            "artist_id": item.artist_id,
            "artist_name": item.artist_name,
            "artist_image_link": item.image_link
        })

    response = {
        "count": len(data),
        "data": data
    }
    return render_template('pages/search_show.html', results=response, search_term=search_term)


@app.route('/shows/<int:show_id>')
def show_show(show_id):
    show_item = Show.query.get(show_id)

    data = {
        "id": show_item.id,
        "show_name": show_item.name,
        "start_time": show_item.start_time,
        "artist_id": show_item.artist_id,
        "artist_name": show_item.Artist.name,
        "artist_city": show_item.Artist.city,
        "artist_state": show_item.Artist.state,
        "artist_phone": show_item.Artist.phone,
        "artist_genres": show_item.Artist.genres,
        "artist_website": show_item.Artist.website_link,
        "artist_facebook_link": show_item.Artist.facebook_link,
        "artist_image_link": show_item.Artist.image_link,

        "venue_id": show_item.venue_id,
        "venue_name": show_item.Venue.name,
        "venue_city": show_item.Venue.city,
        "venue_state": show_item.Venue.state,
        "venue_phone": show_item.Venue.phone,
        "venue_genres": show_item.Venue.genres,
        "venue_website": show_item.Venue.website_link,
        "venue_facebook_link": show_item.Venue.facebook_link,
        "venue_image_link": show_item.Venue.image_link
    }

    return render_template('pages/show_show.html', show=data)


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

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
