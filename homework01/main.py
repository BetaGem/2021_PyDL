from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField

from pandas import read_table
from datetime import datetime

import data   

app = Flask(__name__) 
bootstrap = Bootstrap(app)

# A secret key is required to use CSRF.
app.config['SECRET_KEY'] = 'a_secret_key'

# Constants
pollutant = '0'
update_time = 'Null'
url = 'http://www.pm25.in/'

class Form(FlaskForm):
    # Select pollutant type to plot
    pollute = SelectField('',
                          choices=[('0','AQI'),
                                   ('1','PM2.5'),
                                   ('2','PM10'),
                                   ('3','CO'),
                                   ('7','SO2'),
                                   ('4','NO2'),
                                   ('5','O3')],
                          render_kw = { 'style':'width:155px;' })
    # Bottons
    submit = SubmitField('Plot')
    update = SubmitField('Update data')
    
@app.route('/',methods=['GET', 'POST'])
def index():
    global pollutant, update_time
    
    airmap = data.PlotFromURL(url)
    form = Form()
    if form.validate_on_submit():
        if form.submit.data:
            pollutant = form.pollute.data
        if form.update.data:
            update_time = airmap.update_local_file()  

    # List of city names and coordinates from China_city.csv
    city_list, latitude, longitude = get_city_map()
    # List of air quality values from data.json
    values, is_out_of_date, update_time = get_data(airmap,city_list)
    
    fig = airmap.plot_map(latitude,longitude,values,is_out_of_date,pollutant)
    return render_template('index.html',
                           form=form, 
                           fig=fig,
                           time=update_time)

def get_city_map():
    '''read city list from local file'''   
    
    cities = read_table("China_city.csv",',')
    city_list = cities['city'].values.tolist()
    longitude = cities['lo'].values.tolist()
    latitude = cities['la'].values.tolist()
    
    return city_list, latitude, longitude

def get_data(airmap,city_list):
    '''get data from downloaded file'''
    
    values = []
    is_out_of_date = []
    for cty in city_list:
        value, date = airmap.local_data(cty,pollutant)
        values.append(value)
        
        # Check if the data has been updated within one day
        if date:
            d = datetime(int(date[:4]),int(date[5:7]),int(date[8:10]),int(date[11:13]))
            if (datetime.now() - d).days:
                is_out_of_date.append(6)
            else:
                is_out_of_date.append(45)
        else:
            is_out_of_date.append(0)
            
    return values, is_out_of_date, date

@app.errorhandler(404)
def page_not_found(e):
    '''page not found error'''
    return render_template('404.html')
