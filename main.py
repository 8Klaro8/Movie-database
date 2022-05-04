from pprint import pprint
from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
import requests
import os
from settingup_DB import Movie, db
from sqlalchemy import desc

''' API keys'''
api_endpoint_movie_db = 'https://api.themoviedb.org/3/movie/550?api_key='
api_key_movie_db = '282a894c237ae72979a5e4f819fc0738'
movie_db_api = api_endpoint_movie_db + api_key_movie_db
movie_db_picture_api = 'https://image.tmdb.org/t/p/w500'


''' Set up base directory - by current file with absolute path'''
basedir = os.path.abspath(os.path.dirname(__file__))
# Set up Flask
app = Flask(__name__)




''' With app, configurate configure keys'''
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app_cont = app.app_context()
db = SQLAlchemy(app)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(), nullable=False)
    year = db.Column(db.Integer(), nullable=False)
    description = db.Column(db.String(), nullable=False)
    rating = db.Column(db.Integer(), nullable=False)
    ranking = db.Column(db.Integer(), nullable=False)
    review = db.Column(db.Integer(), nullable=False)
    img_url = db.Column(db.String(), nullable=False)

    def __repr__(self):
        return f'<Movie {self.title}>'

db.create_all()
''' Config. secret key'''
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
'''calling bootstrap on ap'''
Bootstrap(app)


'''!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!Setting up WTForm !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'''
# TODO - Make the rating entry to accept only float
class MyFormEditPage(FlaskForm):
    rating_entry = StringField('Rating')
    review_entry = StringField('Review')
    submit_button = SubmitField('Save')

class AddMovieForm(FlaskForm):
    movie_title = StringField('Movie Title')
    add_movie_button = SubmitField('Add Movie')

'''----------------------------------------HOME----------------------------------------'''
@app.route("/")
def home():

    '''Sets up a dict and assigns rating to title'''
    counter_dict = {}
    all_saved_moies = db.session.query(Movie).order_by(desc(Movie.rating))
    for movie in all_saved_moies:

        print(movie.title)
        print(movie.rating)
        counter_dict[movie.title] = movie.rating
    '''Sorts the ranking by rating'''
    my_dict = dict(reversed(sorted(counter_dict.items(), key=lambda item: item[1])))
    '''assigns the sorted ranking number inside the created dict: "my_dict"  '''
    increm_num = 0
    for key,value in my_dict.items():
        increm_num += 1
        my_dict[key] = {'rating_num': value, 'ranking_number':increm_num}
    '''Adding the appropriate ranking number to to movie inside: all_saved_moies'''
    for mov in all_saved_moies:
        for each in my_dict:
            if each == mov.title:
                mov.ranking = my_dict[each]['ranking_number']

    # TODO sort movies based on its ranking



    return render_template("index.html", all_saved_moies=all_saved_moies, my_dict=my_dict)

# Set up edit.html
@app.route('/edit/<movie_id>', methods=['GET', 'POST'])
def edit(movie_id):
    # initializing form
    my_form = MyFormEditPage()

    if my_form.validate_on_submit():
        '''Other way of getting the data from WTForm input field'''
        # update_rating_field(current_movie_rating, my_form)
        # update_review_field(current_movie_review, my_form)


        get_current_movie_details_by_id = f"https://api.themoviedb.org/3/movie/{movie_id}" \
                                          f"?api_key={api_key_movie_db}&language=en-US"

        requested_movie_by_id = requests.get(url=get_current_movie_details_by_id)
        pprint(f'json by requested movie id: {requested_movie_by_id.json()}')

        movie_title_result = requested_movie_by_id.json()['original_title']
        movie_overview_result = requested_movie_by_id.json()['overview']

        '''Sometimes the path to the picture returns none and therefoe first I try
        to call by "backdrop_path" and when it doesnt work then it calls "poster_path"'''
        try:
            movie_image_result = requested_movie_by_id.json()['backdrop_path']
            if movie_image_result == None:
                movie_image_result = requested_movie_by_id.json()['poster_path']
        except:
            print('couldnt retrive picture path url')


        movie_rating_result = requested_movie_by_id.json()['vote_average']
        movie_release_date_result = requested_movie_by_id.json()['release_date']

        '''Puts together the usable url to the movies picture, using the moviedb picture api and the
        returned value from movie iamge result'''
        usable_picture = movie_db_picture_api + movie_image_result

        new_model = Movie(title=movie_title_result, year=movie_release_date_result, description=movie_overview_result,
                          rating=my_form.rating_entry.data, ranking=movie_rating_result, review=my_form.review_entry.data,
                          img_url=usable_picture)
        db.session.add(new_model)
        db.session.commit()

        '''updates the rating and review fields. No use anymore -
         I leave it here to see my process later on'''
        # update_rating(current_movie_rating, my_form)
        # update_review(current_movie_review, my_form)

        return redirect(url_for('home'))
    else:
        return render_template('edit.html', my_form=my_form)


    '''This is without WTForms'''
    # current_movie = Movie.query.get_or_404(movie_id)
    # if request.method == 'POST':
    #     rating = request.form['rating']
    #     review = request.form['review']
    #
    #     current_movie.rating = rating
    #     current_movie.review = review
    #
    #     db.session.add(current_movie)
    #     db.session.commit()
    #
    #     return redirect(url_for('home'))
    #
    # return render_template('edit.html', movie_id=movie_id, my_form=my_form)

@app.route('/delete/<movie_title>')
def delete(movie_title):
    # Getting the right model to be deleted by the method below
    movie_to_delete = Movie.query.get_or_404(movie_title)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))

'''This route adds the movie results to select.html so it can dispalys all relevant result'''
@app.route('/add', methods=['POST', 'GET'])
def add():
    '''--------Movie Model Form--------'''
    add_movie_form = AddMovieForm()

    if add_movie_form.validate_on_submit():
        '''get the movie data from the form on add.html'''
        movie_input = add_movie_form.movie_title.data
        '''Replaces space to '+' and removes extra'+' '''
        ready_title = movie_ready_for_api_request(movie_input)

        '''Requests thru the movie db API and gives the results'''
        '''I pass it to select.html to loop thru and display all the movies related to the typed title'''
        search_result = request_given_movie(ready_title)
        return render_template('select.html', search_result=search_result)
    else:
        return render_template('add.html', add_movie_form=add_movie_form)

@app.route('/edit_already_added_movie/<movie_title>', methods=['POST', 'GET'])
def edit_already_added_movie(movie_title):
    my_form = MyFormEditPage()
    all_movie = Movie.query.all()

    for movie in all_movie:
        if movie.title == movie_title and my_form.validate_on_submit():
            movie.rating = my_form.rating_entry.data
            movie.review = my_form.review_entry.data

            db.session.add(movie)
            db.session.commit()

            return redirect(url_for('home'))
        # else:
    current_movie_rating = movie.rating
    current_movie_review = movie.review
    return render_template('edit_already_added_movie.html', my_form=my_form,
                           current_movie_rating=current_movie_rating,
                           current_movie_review=current_movie_review)


'''Used to create a new model based on the chosen movie from the list that select.html rendered.
Now it is not useful as I apply edit immediately when I chose the movie'''
# @app.route('/select/<movie_id>', methods=['GET', 'POST'])
# def select(movie_id):
#     '''Api for getting a specified movide based on its ID. This ID was passed from select.html'''
#     get_current_movie_details_by_id = f"https://api.themoviedb.org/3/movie/{movie_id}" \
#                                       f"?api_key={api_key_movie_db}&language=en-US"
#
#
#     requested_movie_by_id = requests.get(url=get_current_movie_details_by_id)
#     pprint(requested_movie_by_id.json())
#
#     movie_title_result = requested_movie_by_id.json()['original_title']
#     movie_overview_result = requested_movie_by_id.json()['overview']
#     movie_image_result = requested_movie_by_id.json()['backdrop_path']
#     movie_rating_result = requested_movie_by_id.json()['vote_average']
#     movie_release_date_result = requested_movie_by_id.json()['release_date']
#
#     usable_picture = movie_db_picture_api + movie_image_result
#
#     new_model = Movie(title=movie_title_result, year=movie_release_date_result, description=movie_overview_result,
#                       rating=movie_rating_result, ranking=movie_rating_result, review=f'cool',
#                       img_url=usable_picture)
#     db.session.add(new_model)
#     db.session.commit()
#
#     # initializing form
#     my_form = MyFormEditPage()
#     return render_template('edit.html', my_form=my_form)

# !!!!!!!!!!!!!!!!!!!!!!!Working method to update rating and review input !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

'''The two functon below does not have any validation anymore 
but I leave it here to see later on what the process was'''
def update_review_field(current_movie_review, my_form):
    my_movie = db.session.query(Movie).filter_by(review=current_movie_review).first()
    my_movie.review = my_form.review_entry.data
    db.session.add(my_movie)
    db.session.commit()
def update_rating_field(current_movie_rating, my_form):
    my_movie = db.session.query(Movie).filter_by(rating=current_movie_rating).first()
    my_movie.rating = my_form.rating_entry.data
    db.session.add(my_movie)
    db.session.commit()

def request_given_movie(movie):
    '''Pass in to the movide db API the unique api key and the title of the movie'''
    Movie_dB_Search_API = f'https://api.themoviedb.org/3/search/movie?api_key={api_key_movie_db}&query={movie}'
    result = requests.get(url=Movie_dB_Search_API)
    return result
def movie_ready_for_api_request(movie_input):
    new_title = []
    for letter in movie_input:
        if letter == ' ':
            letter = '+'
            new_title.append(letter)
        new_title.append(letter)

    for each_letter in new_title:
        if each_letter == '+':
            new_title.remove(each_letter)
            break
    return ''.join(new_title)



'''-------------Start of process------------------------------------------------------------'''
if __name__ == '__main__':
    app.run(debug=True)

