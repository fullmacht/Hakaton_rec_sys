from flask import Flask, render_template, session, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms import TextField, SubmitField
import pickle
import os
import json
from datetime import datetime
from datetime import timedelta

PATH = 'data/'

with open(os.path.join(PATH, 'activities_clusters.pickle'), 'rb') as f:
    activities_clusters = pickle.load(f)

with open(os.path.join(PATH, 'books_clusters.pickle'), 'rb') as f:
    books_clusters = pickle.load(f)

with open(os.path.join(PATH, 'courses_clusters.pickle'), 'rb') as f:
    courses_clusters = pickle.load(f)

with open(os.path.join(PATH, 'readers_clusters.pickle'), 'rb') as f:
    readers_clusters = pickle.load(f)

with open(os.path.join(PATH, 'pupils_clusters.pickle'), 'rb') as f:
    pupils_clusters = pickle.load(f)

# with open(os.path.join(PATH, 'average_pupils_ratios.pickle'), 'rb') as f:
#     average_pupils_ratios = pickle.load(f)

# with open(os.path.join(PATH, 'average_readers_ratios.pickle'), 'rb') as f:
#     average_readers_ratios = pickle.load(f)

with open(os.path.join(PATH, 'last_book_predictor.pickle'), 'rb') as f:
    last_book_predictor = pickle.load(f)

with open(os.path.join(PATH, 'last_course_predictor.pickle'), 'rb') as f:
    last_course_predictor = pickle.load(f)

with open(os.path.join(PATH, 'clusters_mapper.pickle'), 'rb') as f:
    clusters_mapper = pickle.load(f)

with open(os.path.join(PATH, 'collaborative_predictor_NOT_FULL.pickle'), 'rb') as f: #to create
    collaborative_predictor = pickle.load(f)

with open(os.path.join(PATH, 'readers_books_set.pickle'), 'rb') as f: #to create
    readers_books_set = pickle.load(f)

with open(os.path.join(PATH, 'idbook_booktitle.pickle'), 'rb') as f: #to create
    id_book_map = pickle.load(f)
########################################################################################
users = list(readers_clusters.keys())
pupils = list(pupils_clusters.keys())
# skip SVD
# skip age constraints (needed to be adjusted in databases)
def predict(user_id):
    if user_id in users:
        user_genres = readers_clusters[user_id]['book_ratios']
        dominant_cluster = str()
        max_ratio = int()
        for key, value in user_genres.items():
            if value > max_ratio:
                max_ratio = value
                dominant_cluster = key
        user_age = readers_clusters[user_id]['age']
        
        # top 10 last item
        last_item = readers_clusters[user_id]['last_book']
        last_item_top_10 = set(last_book_predictor[last_item])
        
        # top 10 collaborative
        the_closest = collaborative_predictor[user_id][0][0]
        user_set = readers_books_set[user_id]
        the_closest_set = readers_books_set[the_closest]
        collaborative_top_10 = the_closest_set - user_set
        
        top_5_books = []
        both_predict = last_item_top_10 & collaborative_top_10
        if both_predict:
            top_5_books = list(both_predict)[:5]
    
        diff = 5 - len(top_5_books)
        if diff > 0:
            top_5_books = top_5_books + list(last_item_top_10)[:diff]
        
        top_5_titles = []
        for id_ in top_5_books:
            top_5_titles.append(id_book_map[id_])

        # courses
        recommended_course = ''
        try:
            course_cluster, event_cluster = clusters_mapper['books'][dominant_cluster] # adhoc
        except KeyError:
            course_cluster, event_cluster = '', ''

        if course_cluster:
            recommended_course = courses_clusters[course_cluster][0]['title'] # assume storaging popularity sorted
            
        # events
        recommended_event = ''
        # today = datetime.today()
        # time_related_events = activities_clusters['time_related']
        # for time_rel in time_related_events:
        #     delta = (time_rel['event_date'] - today).days #check types, mistake
        #     if delta <= 7: #a week before
        #         recommended_event = time_rel['title']
        #         break
                
        if not recommended_event:
            if event_cluster:
                recommended_event = activities_clusters[event_cluster][0]['title']
          
        return top_5_titles, recommended_course, recommended_event
    
    else:
        user_courses = pupils_clusters[user_id]['course_ratios']
        dominant_cluster = str()
        max_ratio = int()
        for key, value in user_courses.items():
            if value > max_ratio:
                max_ratio = value
                dominant_cluster = key
#         user_age = pupils_clusters[user_id]['age_cat']
        
        # top 10 last item
        last_item = pupils_clusters[user_id]['last_service']
        last_item_top_10 = set(last_course_predictor[last_item])
        
        top_5_courses = list(last_item_top_10)[:5]
        
        # books
        recommended_book = ''
        book_cluster, event_cluster = clusters_mapper['courses'][dominant_cluster]
        if book_cluster:
            recommended_book = books_clusters[book_cluster][0]['title'] # assume storaging popularity sorted
            
        # events
        recommended_event = ''
        # today = datetime.today()
        # time_related_events = activities_clusters['time_related']
        # for time_rel in time_related_events:
        #     delta = (time_rel['event_date'] - today).days # check types
        #     if delta <= 7: #a week before
        #         recommended_event = time_rel['title']
        #         break
                
        if not recommended_event:
            if event_cluster:
                try:
                    top_book = list(books_clusters[event_cluster][0].keys())[0] #! adjust
                    recommended_event = books_clusters[event_cluster][0][top_book]['title']
                except IndexError:
                    pass
                
        return top_5_courses, recommended_book, recommended_event

class UserForm(FlaskForm):
    user_id = TextField('ID пользователя')
    submit = SubmitField('Получить рекомендации')



app = Flask(__name__)
app.config['SECRET_KEY'] = 'culture_secretkey'

@app.route('/', methods=['GET', 'POST'])
def index():
    form = UserForm()
    if form.validate_on_submit():
        session['user_id'] = form.user_id.data
        return redirect(url_for('prediction'))
    return render_template('home.html', form=form)

@app.route('/prediction')
def prediction():
    try:
        user_id = int(session['user_id'])
    except ValueError:
        return redirect(url_for('index'))
    
    if user_id in users or user_id in pupils:
        top_5, book_course, event = predict(user_id)
        return render_template('prediction.html', top_5=top_5, book_course=book_course, event=event)
    else:
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
