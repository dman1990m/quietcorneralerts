from flask import Blueprint, request, render_template, redirect, url_for, jsonify
from new.database.models import User, Calls, Chat, Keys
from flask_jwt_extended import get_jwt_identity, jwt_required
import datetime
import logging
from pytz import timezone
from mongoengine.queryset.visitor import Q
import tweepy
from facebook import GraphAPI
import folium
from geopy.geocoders import Nominatim
import os
import configparser
import json

config = configparser.RawConfigParser()
configFilePath = [r'secret.config', r'QCA.config']
config.read(configFilePath)

geolocator = Nominatim(user_agent='Quiet Corner Alerts')

cad = Blueprint('cad', __name__, template_folder='templates')

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
log = logging.getLogger("cad")

#twitter keys and setup for @quietcorneralrt
twitter_consumer_key = config.get('key','twitter_consumer_key')
twitter_consumer_secret = config.get('key','twitter_consumer_secret')
twitter_access_token = config.get('key','twitter_access_token')
twitter_access_token_secret = config.get('key','twitter_access_secret')
twitauth = tweepy.OAuth1UserHandler(twitter_consumer_key, twitter_consumer_secret)
twitauth.set_access_token(twitter_access_token, twitter_access_token_secret)
api = tweepy.API(twitauth)

#twitter keys and setup for @QCA_National
QCAnational_twitter_consumer_key = config.get('key','QCAnational_twitter_api_key')
QCAnational_twitter_consumer_secret = config.get('key','QCAnational_twitter_api_secret')
QCAnational_twitter_access_token = config.get('key','QCAnational_twitter_access_token')
QCAnational_twitter_access_token_secret = config.get('key','QCAnational_twitter_access_secret')
QCAnational_twitauth = tweepy.OAuth1UserHandler(QCAnational_twitter_consumer_key, QCAnational_twitter_consumer_secret)
QCAnational_twitauth.set_access_token(QCAnational_twitter_access_token, QCAnational_twitter_access_token_secret)
QCAnational_api = tweepy.API(QCAnational_twitauth)

#facebook key and setup
#this token expires on 172sep2!!!
facebook_token = config.get('key','facebook_token')
graph = GraphAPI(access_token=facebook_token)
facebook_page = config.get('key','facebook_page')


#this needs to be redone at somepoint. Baseline times to account for TZ. This may not be needed in AWS
def gettimes():
    global est, dt, current_time, current_date, current_date_time, date_time_minus_one_min, date_time_minus_twentyfour_hr
    est = timezone('US/Eastern')
    dt = datetime.datetime.now(tz=est)
    current_time = dt.strftime('%H:%M:%S') #Current Time
    current_date = dt.strftime('%m/%d/%y')#Current date
    current_date_time = dt.strftime('%m/%d/%y, %H:%M:%S')#current Date and Time
    date_time_minus_twentyfour_hr = dt - datetime.timedelta(hours=29)
    date_time_minus_one_min = dt - datetime.timedelta(hours=6)

@cad.route('/dispatch')
@jwt_required(optional=True)
def dispatch():
    try:
        current_identity= get_jwt_identity()
        if current_identity:
            gettimes()
            #get_keys()
            user = User.objects.get(id=get_jwt_identity())
            que = Calls.objects.filter((Q(active='False') & Q(datetime__gte=str(date_time_minus_twentyfour_hr))))
            #que = Calls.objects.filter(active='False').filter(date=str(yesterday_date))
            que_data = []
            for call in reversed(que):
                incidents = [call.id, call.date, call.times, call.town, call.state, call.roadname, call.incident, call.narrative, call.dispatcher, call.updated,call.secondary_dispatcherid]
                que_data.append(incidents)
            twentyfourhour_data = []
            twentyfourhour = Calls.objects.filter((Q(active='True') & Q(datetime__gte=str(date_time_minus_twentyfour_hr))))
            for call in reversed(twentyfourhour):
                incidents = [call.id, call.date, call.times, call.town, call.state, call.roadname, call.incident,
                             call.narrative, call.dispatcher, user.dispatcherid, call.updated, call.secondary_dispatcherid]
                twentyfourhour_data.append(incidents)
            tweet = 'Test'
            user.lastconnection = current_date_time
            #user.lastconnectiondate = current_date
            #user.lastconnectiontime = current_time
            print("Dispatch Current Time " + str(current_time))
            #print("Current Date " + str(current_date))
            #print("Current Date/Time " + str(current_date_time))
            #print("Minus 24hr Time " + str(date_time_minus_twentyfour_hr))
            #print("Minus 1min Time " + str(date_time_minus_one_min))
            user.save()
            activeuser()
            logging.info('working')
            if user.permission == 'admin':
                return render_template('admin/dispatch.html', que_data=que_data, twentyfourhour_data=twentyfourhour_data, tweet=tweet, activeusers=activeusers, logged=True)
            elif user.permission == 'dispatcher':
                return render_template('dispatcher/dispatch.html', que_data=que_data, twentyfourhour_data=twentyfourhour_data, tweet=tweet, activeusers=activeusers, logged=True)
            elif user.permission == 'baseuser':
                return render_template('baseuser/dispatch.html', que_data=que_data, twentyfourhour_data=twentyfourhour_data, logged=True)
        else:
            gettimes()
            # get_keys()
            que = Calls.objects.filter((Q(active='False') & Q(datetime__gte=str(date_time_minus_twentyfour_hr))))
            # que = Calls.objects.filter(active='False').filter(date=str(yesterday_date))
            que_data = []
            for call in reversed(que):
                incidents = [call.id, call.date, call.times, call.town, call.state, call.roadname, call.incident,
                             call.narrative, call.dispatcher, call.secondary_dispatcherid]
                que_data.append(incidents)
            twentyfourhour_data = []
            twentyfourhour = Calls.objects.filter(
                (Q(active='True') & Q(datetime__gte=str(date_time_minus_twentyfour_hr))))
            for call in reversed(twentyfourhour):
                incidents = [call.id, call.date, call.times, call.town, call.state, call.roadname, call.incident,
                             call.narrative, call.dispatcher]
                twentyfourhour_data.append(incidents)
            tweet = 'Test'
            # user.lastconnectiondate = current_date
            # user.lastconnectiontime = current_time
            print("Dispatch Current Time " + str(current_time))
            # print("Current Date " + str(current_date))
            # print("Current Date/Time " + str(current_date_time))
            # print("Minus 24hr Time " + str(date_time_minus_twentyfour_hr))
            # print("Minus 1min Time " + str(date_time_minus_one_min))
            chat()
            logging.info('working')
            return render_template('baseuser/dispatch.html', que_data=que_data, twentyfourhour_data=twentyfourhour_data, logged=False)
    except OSError as oserror:
        logging.error(oserror)
        return redirect(url_for('auth.login'))
    except Exception as error:
        print(error)
        return render_template('error.html')

#Create a new incident
@cad.route('/newincident', methods=['GET', 'POST'])
@jwt_required()
def newincident():
    fire_incidents = json.loads(config.get('incident_types', 'fire_incidents'))
    police_incidents = json.loads(config.get('incident_types', 'police_incidents'))
    weather_alerts = json.loads(config.get('incident_types', 'weather_alerts'))
    fire_weather_alerts = json.loads(config.get('incident_types', 'fire_weather_alerts'))
    storm_weather_alerts = json.loads(config.get('incident_types', 'storm_weather_alerts'))
    winter_weather_alerts = json.loads(config.get('incident_types', 'winter_weather_alerts'))
    try:
        gettimes()
        user = User.objects.get(id=get_jwt_identity())
        dispatcher = User.objects.filter((Q(permission='admin') | Q(permission='dispatcher')))
        dispatchers = []
        for x in dispatcher:
            dispatchers.append(x.dispatcherid)
        est = timezone('US/Eastern')
        dt = datetime.datetime.now(tz=est)
        time_str = dt.strftime('%H:%M')
        d3 = dt.strftime('%m/%d/%y')
        d4 = dt.strftime('%m/%d/%y, %H:%M:%S')
        todaycalctime = datetime.datetime.now(tz=est) - datetime.timedelta(hours=5)
        if request.method == 'POST':
            call = Calls(**request.form)
            call.town = call.town.title().strip()
            call.state = call.state.strip().upper()
            call.roadname = call.roadname.strip().title().replace('&','').replace('%','').replace('Area Of','')
            full_loc = call.roadname + ', ' + call.town + ', ' + call.state
            '''
            geo_loc = geolocator.geocode(full_loc)
            '''
            call.narrative = call.narrative.strip().replace('&','').replace('%','')
            print(call.public_credit)
            call.dispatcher = user.dispatcherid
            if call.public_credit == "yes":
                if call.secondary_dispatcherid != 'None':
                    secondary = User.objects.get(dispatcherid = call.secondary_dispatcherid)
                    call.dispatcher_credit = user.credit
                    call.dispatcher_credit = secondary.credit
            call.date = str(d3)
            call.times = time_str
            call.active = 'False'
            call.datetime = d4
            call.updated = False
            '''
            try:
                call.lat = geo_loc.latitude
                call.lon = geo_loc.longitude
            except Exception as error:
                print(error)
                pass
                '''
            call.save()
            print("New Incident Current Time " + str(current_time), call)
            return redirect(url_for('cad.dispatch'))
        #print(user.permission)
        if user.permission == 'admin' or user.permission == 'dispatcher':
            #print('3')
            return render_template('newincident.html', fire_incidents=fire_incidents, police_incidents=police_incidents, weather_alerts=weather_alerts, fire_weather_alerts=fire_weather_alerts, storm_weather_alerts=storm_weather_alerts, winter_weather_alerts=winter_weather_alerts, dispatchers=sorted(dispatchers))
        else:
            #print('2')
            return redirect(url_for('cad.dispatch'))
    except Exception as error:
        print(error)
        return redirect(url_for('cad.dispatch'))

#edit an incident. only unconfirmed for eveyone except for admins who can edit confirmed
@cad.route('/edit/<id>', methods=['GET', 'POST'])
@jwt_required()
def edit(id):
    fire_incidents = json.loads(config.get('incident_types', 'fire_incidents'))
    police_incidents = json.loads(config.get('incident_types', 'police_incidents'))
    weather_alerts = json.loads(config.get('incident_types', 'weather_alerts'))
    fire_weather_alerts = json.loads(config.get('incident_types', 'fire_weather_alerts'))
    storm_weather_alerts = json.loads(config.get('incident_types', 'storm_weather_alerts'))
    winter_weather_alerts = json.loads(config.get('incident_types', 'winter_weather_alerts'))
    try:
        gettimes()
        user = User.objects.get(id=get_jwt_identity())
        dispatcher = User.objects.filter((Q(permission='admin') | Q(permission='dispatcher')))
        dispatchers = []
        for x in dispatcher:
            dispatchers.append(x.dispatcherid)
        est = timezone('US/Eastern')
        dt = datetime.datetime.now(tz=est)
        time_str = dt.strftime('%H:%M')
        d3 = dt.strftime('%m/%d/%y')
        todaycalctime = datetime.datetime.now(tz=est) - datetime.timedelta(hours=5)
        if request.method == 'POST':
            original = Calls.objects(id=id).update(**request.form,date=str(d3),times=time_str, datetime=todaycalctime)
            #print(id)
            print("Edit Current Time " + str(current_time), Calls)
            return redirect(url_for('cad.dispatch'))
        elif request.method == 'GET':
            call_data = []
            call = Calls.objects(id=id)
            for incident in call:
                incidents = [incident.id, incident.date, incident.times, incident.town, incident.state, incident.roadname,
                             incident.incident, incident.narrative, incident.active]
                #print(incident.narrative)
                call_data.append(incidents)
            #print(call_data[0])
            return render_template('edit.html', call_data=call_data[0], fire_incidents=fire_incidents, police_incidents=police_incidents, weather_alerts=weather_alerts, fire_weather_alerts=fire_weather_alerts, storm_weather_alerts=storm_weather_alerts, winter_weather_alerts=winter_weather_alerts, dispatchers=sorted(dispatchers) )
    except Exception as error:
        print(error)
        return redirect(url_for('cad.dispatch'))

#Update confirmed incidents
@cad.route('/edit_post', methods=['GET', 'POST'])
@jwt_required()
def edit_post():
    fire_incidents = json.loads(config.get('incident_types', 'fire_incidents'))
    police_incidents = json.loads(config.get('incident_types', 'police_incidents'))
    weather_alerts = json.loads(config.get('incident_types', 'weather_alerts'))
    fire_weather_alerts = json.loads(config.get('incident_types', 'fire_weather_alerts'))
    storm_weather_alerts = json.loads(config.get('incident_types', 'storm_weather_alerts'))
    winter_weather_alerts = json.loads(config.get('incident_types', 'winter_weather_alerts'))
    try:
        gettimes()
        user = User.objects.get(id=get_jwt_identity())
        dispatcher = User.objects.filter((Q(permission='admin') | Q(permission='dispatcher')))
        dispatchers = []
        for x in dispatcher:
            dispatchers.append(x.dispatcherid)
        est = timezone('US/Eastern')
        dt = datetime.datetime.now(tz=est)
        time_str = dt.strftime('%H:%M')
        d3 = dt.strftime('%m/%d/%y')
        d4 = dt.strftime('%m/%d/%y, %H:%M:%S')
        todaycalctime = datetime.datetime.now(tz=est) - datetime.timedelta(hours=5)
        if request.method == 'POST':
            call = Calls(**request.form)
            call.town = call.town.title().strip()
            call.state = call.state.strip().upper()
            call.roadname = call.roadname.strip().title().replace('&','').replace('%','')
            full_loc = call.roadname + ', ' + call.town + ', ' + call.state
            geo_loc = geolocator.geocode(full_loc)
            call.narrative = call.narrative.strip().replace('&','').replace('%','')
            print(call.public_credit)
            call.dispatcher = user.dispatcherid
            if call.public_credit == "yes":
                if call.secondary_dispatcherid != 'None':
                    secondary = User.objects.get(dispatcherid=call.secondary_dispatcherid)
                    call.dispatcher_credit = user.credit
                    call.dispatcher_credit = secondary.credit
            call.date = str(d3)
            call.times = time_str
            call.datetime = d4
            try:
                call.lat = geo_loc.latitude
                call.lon = geo_loc.longitude
            except Exception as error:
                print(error)
                pass
            call.save()
            print("Edit Incident Current Time " + str(current_time), call)
            return redirect(url_for('cad.dispatch'))
        #print(user.permission)
        if user.permission == 'admin' or user.permission == 'dispatcher':
            #print('3')
            return render_template('edit.html', fire_incidents=fire_incidents, police_incidents=police_incidents, weather_alerts=weather_alerts, fire_weather_alerts=fire_weather_alerts, storm_weather_alerts=storm_weather_alerts, winter_weather_alerts=winter_weather_alerts, dispatchers=sorted(dispatchers))
        else:
            #print('2')
            return redirect(url_for('cad.dispatch'))
    except Exception as error:
        print(error)
        return redirect(url_for('cad.dispatch'))

@cad.route('/update/<id>', methods=['GET'])
@jwt_required()
def update(id):
    fire_incidents = json.loads(config.get('incident_types', 'fire_incidents'))
    police_incidents = json.loads(config.get('incident_types', 'police_incidents'))
    weather_alerts = json.loads(config.get('incident_types', 'weather_alerts'))
    fire_weather_alerts = json.loads(config.get('incident_types', 'fire_weather_alerts'))
    storm_weather_alerts = json.loads(config.get('incident_types', 'storm_weather_alerts'))
    winter_weather_alerts = json.loads(config.get('incident_types', 'winter_weather_alerts'))
    try:
        gettimes()
        user = User.objects.get(id=get_jwt_identity())
        dispatcher = User.objects.filter((Q(permission='admin') | Q(permission='dispatcher')))
        dispatchers = []
        for x in dispatcher:
            dispatchers.append(x.dispatcherid)
        est = timezone('US/Eastern')
        dt = datetime.datetime.now(tz=est)
        time_str = dt.strftime('%H:%M')
        d3 = dt.strftime('%m/%d/%y')
        d4 = dt.strftime('%m/%d/%y, %H:%M:%S')
        todaycalctime = datetime.datetime.now(tz=est) - datetime.timedelta(hours=5)
        call_data = []
        call = Calls.objects(id=id)
        for incident in call:
            incidents = [incident.id, incident.date, incident.times, incident.town, incident.state, incident.roadname,
                         incident.incident, incident.narrative]
            #print(incident.narrative)
            call_data.append(incidents)
        #print(call_data[0])
        return render_template('update.html', call_data=call_data[0], fire_incidents=fire_incidents, police_incidents=police_incidents, weather_alerts=weather_alerts, fire_weather_alerts=fire_weather_alerts, storm_weather_alerts=storm_weather_alerts, winter_weather_alerts=winter_weather_alerts, dispatchers=sorted(dispatchers))
    except Exception as error:
        print(error)
        return redirect(url_for('cad.dispatch'))

#Update confirmed incidents
@cad.route('/update_post', methods=['GET', 'POST'])
@jwt_required()
def update_post():
    fire_incidents = json.loads(config.get('incident_types', 'fire_incidents'))
    police_incidents = json.loads(config.get('incident_types', 'police_incidents'))
    weather_alerts = json.loads(config.get('incident_types', 'weather_alerts'))
    fire_weather_alerts = json.loads(config.get('incident_types', 'fire_weather_alerts'))
    storm_weather_alerts = json.loads(config.get('incident_types', 'storm_weather_alerts'))
    winter_weather_alerts = json.loads(config.get('incident_types', 'winter_weather_alerts'))
    try:
        gettimes()
        user = User.objects.get(id=get_jwt_identity())
        dispatcher = User.objects.filter((Q(permission='admin') | Q(permission='dispatcher')))
        dispatchers = []
        for x in dispatcher:
            dispatchers.append(x.dispatcherid)
        est = timezone('US/Eastern')
        dt = datetime.datetime.now(tz=est)
        time_str = dt.strftime('%H:%M')
        d3 = dt.strftime('%m/%d/%y')
        d4 = dt.strftime('%m/%d/%y, %H:%M:%S')
        todaycalctime = datetime.datetime.now(tz=est) - datetime.timedelta(hours=5)
        if request.method == 'POST':
            call = Calls(**request.form)
            call.id = None
            call.town = call.town.title().strip()
            call.state = call.state.strip().upper()
            call.roadname = call.roadname.strip().title().replace('&','').replace('%','')
            full_loc = call.roadname + ', ' + call.town + ', ' + call.state
            geo_loc = geolocator.geocode(full_loc)
            call.narrative = call.narrative.strip().replace('&','').replace('%','')
            call.dispatcher = user.dispatcherid
            if call.public_credit == "yes":
                if call.secondary_dispatcherid != 'None':
                    secondary = User.objects.get(dispatcherid = call.secondary_dispatcherid)
                    call.dispatcher_credit = user.credit
                    call.dispatcher_credit = secondary.credit
            call.date = str(d3)
            call.times = time_str
            call.active = 'False'
            call.datetime = d4
            call.updated = True
            try:
                call.lat = geo_loc.latitude
                call.lon = geo_loc.longitude
            except Exception as error:
                print(error)
                pass
            call.save()
            print("Updated Incident Current Time " + str(current_time), call)
            return redirect(url_for('cad.dispatch'))
        #print(user.permission)
        if user.permission == 'admin' or user.permission == 'dispatcher':
            #print('3')
            return render_template('update.html', fire_incidents=fire_incidents, police_incidents=police_incidents, weather_alerts=weather_alerts, fire_weather_alerts=fire_weather_alerts, storm_weather_alerts=storm_weather_alerts, winter_weather_alerts=winter_weather_alerts, dispatchers=sorted(dispatchers))
        else:
            #print('2')
            return redirect(url_for('cad.dispatch'))
    except Exception as error:
        print(error)
        return redirect(url_for('cad.dispatch'))

#Tweet button for QCA Login. Never needs to check credit because it should always be crediting when button is used
@cad.route('/tweet/<id>')
@jwt_required()
def tweet(id):
    #print(id)
    tweet_data = []
    tweet = Calls.objects.filter(id=id)
    for call in tweet:
        if call.updated == True:
            if call.dispatcher_credit:
                if call.roadname:
                    tweet_data.append('UPDATED INCIDENT | ' + call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.roadname + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
                else:
                    tweet_data.append('UPDATED INCIDENT | ' + call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
            else:
                if call.roadname:
                    tweet_data.append('UPDATED INCIDENT | ' + call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.roadname + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
                else:
                    tweet_data.append('UPDATED INCIDENT | ' + call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
        else:
            if call.dispatcher_credit:
                if call.roadname:
                    tweet_data.append(call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.roadname + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
                else:
                    tweet_data.append(call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
            else:
                if call.roadname:
                    tweet_data.append(call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.roadname + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
                else:
                    tweet_data.append(call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
    link = ('https://twitter.com/intent/tweet?text=' + str(tweet_data[0]))
    return redirect(link)

#Tweet button for dispatchers. check credit levels and format tweets/open twitter
@cad.route('/tweet1/<id>')
@jwt_required()
def tweet1(id):
    #print(id)
    tweet_data = []
    tweet = Calls.objects.filter(id=id)
    user = User.objects.get(id=get_jwt_identity())
    #pull call in
    for call in tweet:
        #Check if there is a credit line for the associated dispatcher
        if call.dispatcher_credit:
            #check if there is a secondary dispatcher that needs to be credited. This may be a redundant line
            if call.secondary_dispatcherid:
                #if the user is the secondary dispatcher
                if call.secondary_dispatcherid == User.dispatcherid:
                    #check if the call is an update
                    if call.updated:
                        #check if there is a roadway
                        if call.roadname:
                            tweet_data.append(
                                'UPDATED INCIDENT | ' + call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.roadname + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
                        else:
                            tweet_data.append(
                                'UPDATED INCIDENT | ' + call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
                    else:
                        # check if there is a roadway
                        if call.roadname:
                            tweet_data.append(
                                call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.roadname + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
                        else:
                            tweet_data.append(
                                call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
                else:
                    # check if the call is an update
                    if call.updated:
                        # check if there is a roadway
                        if call.roadname:
                            tweet_data.append(
                                'UPDATED INCIDENT | ' + call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.roadname + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
                        else:
                            tweet_data.append(
                                'UPDATED INCIDENT | ' + call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
                    else:
                        # check if there is a roadway
                        if call.roadname:
                            tweet_data.append(
                                call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.roadname + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
                        else:
                            tweet_data.append(
                                call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
            else:
                # if the user is the dispatcher
                if call.dispatcher == User.dispatcherid:
                    # check if the call is an update
                    if call.updated:
                        # check if there is a roadway
                        if call.roadname:
                            tweet_data.append(
                                'UPDATED INCIDENT | ' + call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.roadname + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
                        else:
                            tweet_data.append(
                                'UPDATED INCIDENT | ' + call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
                    else:
                        # check if there is a roadway
                        if call.roadname:
                            tweet_data.append(
                                call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.roadname + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
                        else:
                            tweet_data.append(
                                call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
                else:
                    # check if the call is an update
                    if call.updated:
                        # check if there is a roadway
                        if call.roadname:
                            tweet_data.append(
                                'UPDATED INCIDENT | ' + call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.roadname + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
                        else:
                            tweet_data.append(
                                'UPDATED INCIDENT | ' + call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
                    else:
                        # check if there is a roadway
                        if call.roadname:
                            tweet_data.append(
                                call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.roadname + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
                        else:
                            tweet_data.append(
                                call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
        #if there is no credit line on the call use a response w/ generic source
        else:
            #Check if the call is an update
            if call.updated:
                # check if there is a roadway
                if call.roadname:
                    tweet_data.append(
                        'UPDATED INCIDENT | ' + call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.roadname + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
                else:
                    tweet_data.append(
                        'UPDATED INCIDENT | ' + call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
            else:
                # check if there is a roadway
                if call.roadname:
                    tweet_data.append(
                        call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.roadname + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
                else:
                    tweet_data.append(
                        call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
    link = ('https://twitter.com/intent/tweet?text=' + str(tweet_data[0]))
    return redirect(link)

'''
        if user.dispatcherid == call.dispatcher:
            if call.updated == True:
                if call.dispatcher_credit:
                    if call.roadname:
                        tweet_data.append('UPDATED INCIDENT | ' + call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.roadname + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
                    else:
                        tweet_data.append('UPDATED INCIDENT | ' + call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
            else:
                if call.roadname:
                    tweet_data.append(call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.roadname + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
                else:
                    tweet_data.append(call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative)
        else:
            if call.updated == True:
                if call.dispatcher_credit:
                    if call.roadname:
                        tweet_data.append('UPDATED INCIDENT | ' + call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.roadname + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative + '%20%7c%20PER ' + call.dispatcher_credit)
                    else:
                        tweet_data.append('UPDATED INCIDENT | ' + call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative + '%20%7c%20PER ' + call.dispatcher_credit)
                else:
                    if call.roadname:
                        tweet_data.append('UPDATED INCIDENT | ' + call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.roadname + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative + '%20%7c%20PER ' + 'PER QCA Dispatcher')
                    else:
                        tweet_data.append('UPDATED INCIDENT | ' + call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative + '%20%7c%20PER ' + 'PER QCA Dispatcher')
            else:
                if call.dispatcher_credit:
                    if call.roadname:
                        tweet_data.append(call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.roadname + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative + '%20%7c%20PER ' + call.dispatcher_credit)
                    else:
                        tweet_data.append(call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative + '%20%7c%20PER ' + call.dispatcher_credit)
                else:
                    if call.roadname:
                        tweet_data.append(call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.roadname + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative + '%20%7c%20PER ' + 'PER QCA Dispatcher')
                    else:
                        tweet_data.append(call.town + '%20%7c%20' + call.state + '%20%7c%20' + call.incident + '%20%7c%20' + call.narrative + '%20%7c%20PER ' + 'PER QCA Dispatcher')
            #print(tweet_data)
            '''
def tweet_post_local(tweet_data):
    try:
        api.update_status(tweet_data[0])
        print('Local Tweet')
    except Exception as e:
        print(f'QCA_Local Twitter Failed: {e}')

def tweet_post_national(tweet_data):
    try:
        QCAnational_api.update_status(tweet_data[0])
        print(' National Tweet')
    except:
        print('QCA_National Twitter Failer')

def facebook_post(tweet_data):
    try:
        facebook_data = str(tweet_data[0] + ' | Updates at twitter.com/QCA_Local')
        graph.put_object(facebook_page, 'feed', message=facebook_data)
        print('successfull FB post')
    except:
        print('QCA Facebook Failed')

#Automatically Tweet incidents matching QCA criteria to @quietcorneralrt
def autotweet(id):
    tweet_data = []
    tweetable_towns_ct = json.loads(config.get('tweetable_towns','tweetable_towns_CT'))
    tweetable_towns_ma = json.loads(config.get('tweetable_towns','tweetable_towns_MA'))
    tweetable_towns_ri = json.loads(config.get('tweetable_towns','tweetable_towns_RI'))
    non_tweetable_incidents = json.loads(config.get('non_tweetable_incidents','incidents'))
    tweet = Calls.objects.filter(id=id)
    for call in tweet:
        if call.incident not in non_tweetable_incidents:
            if call.state.upper() == 'CT' and call.town.upper() in tweetable_towns_ct or call.state.upper() == 'MA' and call.town.upper() in tweetable_towns_ma or call.state.upper() == 'RI' and call.town.upper() in tweetable_towns_ri:
                if call.dispatcher_credit:
                    if call.roadname:
                        if call.updated:
                            tweet_data.append(
                                'UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative + ' | PER ' + call.dispatcher_credit)
                        else:
                            tweet_data.append(
                                call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative + ' | PER ' + call.dispatcher_credit)
                    else:
                        if call.updated:
                            tweet_data.append(
                                'UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative + ' | PER ' + call.dispatcher_credit)
                        else:
                            tweet_data.append(
                                call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative + ' | PER ' + call.dispatcher_credit)
                    #print('2 ', tweet_data)
                    tweet_post_local(tweet_data)
                    facebook_post(tweet_data)
                else:
                    if call.roadname:
                        if call.updated:
                            tweet_data.append(
                                'UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative)
                        else:
                            tweet_data.append(
                                call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative)
                    else:
                        if call.updated:
                            tweet_data.append(
                                'UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative)
                        else:
                            tweet_data.append(
                                call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative)
                    #print('3 ', tweet_data)
                    tweet_post_local(tweet_data)
                    facebook_post(tweet_data)

                '''
                if call.secondary_dispatcherid != 'None':
                    if call.secondary_dispatcherid == 'QCA001':
                        if call.roadname:
                            if call.updated:
                                tweet_data.append(
                                    'UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative)
                            else:
                                tweet_data.append(
                                    call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative)
                        else:
                            if call.updated:
                                tweet_data.append(
                                    'UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative)
                            else:
                                tweet_data.append(
                                    call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative)
                        print('1 ', tweet_data)
                        #tweet_post_local(tweet_data)
                        #facebook_post(tweet_data)
                    elif call.secondary_dispatcherid != 'QCA001':
                        if call.dispatcher_credit:
                            if call.roadname:
                                if call.updated:
                                    tweet_data.append(
                                        'UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative + ' | PER ' + call.dispatcher_credit)
                                else:
                                    tweet_data.append(
                                        call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative + ' | PER ' + call.dispatcher_credit)
                            else:
                                if call.updated:
                                    tweet_data.append(
                                        'UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative + ' | PER ' + call.dispatcher_credit)
                                else:
                                    tweet_data.append(
                                        call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative + ' | PER ' + call.dispatcher_credit)
                            print('2 ', tweet_data)
                            # tweet_post_local(tweet_data)
                            # facebook_post(tweet_data)
                        else:
                            if call.roadname:
                                if call.updated:
                                    tweet_data.append(
                                        'UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative)
                                else:
                                    tweet_data.append(
                                        call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative)
                            else:
                                if call.updated:
                                    tweet_data.append(
                                        'UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative)
                                else:
                                    tweet_data.append(
                                        call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative)
                            print('3 ', tweet_data)
                            # tweet_post_local(tweet_data)
                            # facebook_post(tweet_data)
                #check if QCA is the disptacher
                elif call.dispatcher == 'QCA001':
                    #
                    if call.roadname:
                        if call.updated:
                            tweet_data.append(
                                'UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative)
                        else:
                            tweet_data.append(
                                call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative)
                    else:
                        if call.updated:
                            tweet_data.append(
                                'UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative)
                        else:
                            tweet_data.append(call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative)
                    print('4 ', tweet_data)
                    # tweet_post_local(tweet_data)
                    # facebook_post(tweet_data)
                else:
                    if call.dispatcher_credit:
                        if call.roadname:
                            if call.updated:
                                tweet_data.append(
                                    'UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | PER ' + call.narrative)
                            else:
                                tweet_data.append(
                                    call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative)
                        else:
                            if call.updated:
                                tweet_data.append(
                                    'UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative)
                            else:
                                tweet_data.append(
                                    call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative)
                        print('5 ', tweet_data)
                        #tweet_post_local(tweet_data)
                        #facebook_post(tweet_data)
                    else:
                        if call.roadname:
                            if call.updated:
                                tweet_data.append(
                                    'UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative)
                            else:
                                tweet_data.append(
                                    call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative)
                        else:
                            if call.updated:
                                tweet_data.append(
                                    'UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative)
                            else:
                                tweet_data.append(
                                    call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative)
                        print('6 ', tweet_data)
                        # tweet_post_local(tweet_data)
                        # facebook_post(tweet_data)
                        '''
'''


        if call.updated == True:
            if call.incident not in non_tweetable_incidents:
                if call.dispatcher == 'QCA001':
                    if call.secondary_dispatcherid != 'QCA001':

                    elif call.state.upper() == 'CT' and call.town.upper() in tweetable_towns_ct  or call.state.upper() == 'MA' and call.town.upper() in tweetable_towns_ma or call.state.upper() == 'RI' and call.town.upper() in tweetable_towns_ri:
                        if call.roadname:
                            tweet_data.append('UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative)
                        else:
                            tweet_data.append(
                                'UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative)
                        print('Acceptable Update Tweet ', tweet_data)
                        api.update_status(tweet_data[0])
                        facebook_data = str(tweet_data[0] + ' | Updates at twitter.com/QCA_Local')
                        graph.put_object(facebook_page, 'feed', message=facebook_data)
                else:
                    try:
                        if call.state.upper() == 'CT' and call.town.upper() in tweetable_towns_ct or call.state.upper() == 'MA' and call.town.upper() in tweetable_towns_ma or call.state.upper() == 'RI' and call.town.upper() in tweetable_towns_ri:
                            if call.dispatcher_credit:
                                if call.roadname:
                                    tweet_data.append('UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative + ' | PER ' + call.dispatcher_credit)
                                else:
                                    tweet_data.append('UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative + ' | PER ' + call.dispatcher_credit)
                            else:
                                if call.roadname:
                                    tweet_data.append('UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative + ' | PER QCA Dispatcher')
                                else:
                                    tweet_data.append('UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative + ' | PER QCA Dispatcher')
                            print('Acceptable Update Tweet ', tweet_data)
                            api.update_status(tweet_data[0])
                            facebook_data = str(
                            tweet_data[0] + ' | Updates at twitter.com/QCA_Local')
                            graph.put_object(facebook_page, 'feed', message=facebook_data)
                    except:
                        pass
                    try:
                        if call.state.upper() == 'CT' and call.town.upper() in tweetable_towns_ct or call.state.upper() == 'MA' and call.town.upper() in tweetable_towns_ma or call.state.upper() == 'RI' and call.town.upper() in tweetable_towns_ri:
                            if call.roadname:
                                tweet_data.append('UPDATED INCIDENT | ' + call.town.upper() + ' | ' + call.state.upper() + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative + ' | PER ' + 'QCA Dispatcher')
                            else:
                                tweet_data.append('UPDATED INCIDENT | ' + call.town.upper() + ' | ' + call.state.upper() + ' | ' + call.incident + ' | ' + call.narrative + ' | PER ' + 'QCA Dispatcher')
                            print('CT Tweet ', tweet_data)
                            api.update_status(tweet_data[0])
                            facebook_data = str(
                            tweet_data[0] + ' | Updates at twitter.com/QCA_Local')
                            graph.put_object(facebook_page, 'feed', message=facebook_data)
                    except:
                        pass
            else:
                pass
        else:
            if call.incident not in non_tweetable_incidents:
                if call.dispatcher == 'QCA001':
                    if call.state.upper() == 'CT' and call.town.upper() in tweetable_towns_ct or call.state.upper() == 'MA' and call.town.upper() in tweetable_towns_ma or call.state.upper() == 'RI' and call.town.upper() in tweetable_towns_ri:
                        if call.roadname:
                            tweet_data.append(call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative)
                        else:
                            tweet_data.append(call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative)
                        print('Acceptable Tweet ', tweet_data)
                        api.update_status(tweet_data[0])
                        facebook_data = str(tweet_data[0] + ' | Updates at twitter.com/quietcorneralrt')
                        graph.put_object(facebook_page, 'feed', message=facebook_data)
                else:
                    try:
                        if call.state.upper() == 'CT' and call.town.upper() in tweetable_towns_ct or call.state.upper() == 'MA' and call.town.upper() in tweetable_towns_ma or call.state.upper() == 'RI' and call.town.upper() in tweetable_towns_ri:
                            if call.dispatcher_credit:
                                if call.roadname:
                                    tweet_data.append(call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative + ' | PER ' + call.dispatcher_credit)
                                else:
                                    tweet_data.append(call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative + ' | PER ' + call.dispatcher_credit)
                            else:
                                if call.roadname:
                                    tweet_data.append(call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative + ' | PER QCA Dispatcher')
                                else:
                                    tweet_data.append(call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative + ' | PER QCA Dispatcher')
                            print('CT Tweet ', tweet_data)
                            api.update_status(tweet_data[0])
                            facebook_data = str(
                            tweet_data[0] + ' | Updates at twitter.com/quietcorneralrt')
                            graph.put_object(facebook_page, 'feed', message=facebook_data)
                    except:
                        pass
                    try:
                        if call.state.upper() == 'CT' and call.town.upper() in tweetable_towns_ct or call.state.upper() == 'MA' and call.town.upper() in tweetable_towns_ma or call.state.upper() == 'RI' and call.town.upper() in tweetable_towns_ri:
                            if call.roadname:
                                tweet_data.append(call.town.upper() + ' | ' + call.state.upper() + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative + ' | PER ' + 'QCA Dispatcher')
                            else:
                                tweet_data.append(call.town.upper() + ' | ' + call.state.upper() + ' | ' + call.incident + ' | ' + call.narrative + ' | PER ' + 'QCA Dispatcher')
                            print('CT Tweet ', tweet_data)
                            api.update_status(tweet_data[0])
                            facebook_data = str(
                            tweet_data[0] + ' | Updates at twitter.com/quietcorneralrt')
                            graph.put_object(facebook_page, 'feed', message=facebook_data)
                    except:
                        pass
            else:
                pass
'''

#Automatically tweet all incidents to @QCA_National
def national_autotweet(id):
    tweet_data = []
    tweetable_towns_ct = json.loads(config.get('tweetable_towns', 'tweetable_towns_CT'))
    tweetable_towns_ma = json.loads(config.get('tweetable_towns', 'tweetable_towns_MA'))
    tweetable_towns_ri = json.loads(config.get('tweetable_towns', 'tweetable_towns_RI'))
    non_tweetable_incidents = json.loads(config.get('non_tweetable_incidents', 'incidents'))
    tweet = Calls.objects.filter(id=id)
    for call in tweet:
        if call.incident not in non_tweetable_incidents:
            if call.secondary_dispatcherid != 'None':
                if call.secondary_dispatcherid == 'QCA001':
                    if call.roadname:
                        if call.updated:
                            tweet_data.append(
                                'UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative)
                        else:
                            tweet_data.append(
                                call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative)
                    else:
                        if call.updated:
                            tweet_data.append(
                                'UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative)
                        else:
                            tweet_data.append(
                                call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative)
                    tweet_post_national(tweet_data)
                elif call.secondary_dispatcherid != 'QCA001':
                    if call.dispatcher_credit:
                        if call.roadname:
                            if call.updated:
                                tweet_data.append(
                                    'UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative + ' | PER ' + call.dispatcher_credit)
                            else:
                                tweet_data.append(
                                    call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative + ' | PER ' + call.dispatcher_credit)
                        else:
                            if call.updated:
                                tweet_data.append(
                                    'UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative + ' | PER ' + call.dispatcher_credit)
                            else:
                                tweet_data.append(
                                    call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative + ' | PER ' + call.dispatcher_credit)
                        tweet_post_national(tweet_data)
                    else:
                        if call.roadname:
                            if call.updated:
                                tweet_data.append(
                                    'UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative)
                            else:
                                tweet_data.append(
                                    call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative)
                        else:
                            if call.updated:
                                tweet_data.append(
                                    'UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative)
                            else:
                                tweet_data.append(
                                    call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative)
                        tweet_post_national(tweet_data)
            # check if QCA is the disptacher
            elif call.dispatcher == 'QCA001':
                #
                if call.roadname:
                    if call.updated:
                        tweet_data.append(
                            'UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative)
                    else:
                        tweet_data.append(
                            call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative)
                else:
                    if call.updated:
                        tweet_data.append(
                            'UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative)
                    else:
                        tweet_data.append(
                            call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative)
                tweet_post_national(tweet_data)
            else:
                if call.dispatcher_credit:
                    if call.roadname:
                        if call.updated:
                            tweet_data.append(
                                'UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative + ' | PER ' + call.dispatcher_credit)
                        else:
                            tweet_data.append(
                                call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative + ' | PER ' + call.dispatcher_credit)
                    else:
                        if call.updated:
                            tweet_data.append(
                                'UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative + ' | PER ' + call.dispatcher_credit)
                        else:
                            tweet_data.append(
                                call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative + ' | PER ' + call.dispatcher_credit)
                    tweet_post_national(tweet_data)
                else:
                    if call.roadname:
                        if call.updated:
                            tweet_data.append(
                                'UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative)
                        else:
                            tweet_data.append(
                                call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative)
                    else:
                        if call.updated:
                            tweet_data.append(
                                'UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative)
                        else:
                            tweet_data.append(
                                call.town + ' | ' + call.state + ' | ' + call.incident + ' | ' + call.narrative)
                    tweet_post_national(tweet_data)


@cad.route('/alert')
def alert():
    tweet_data = []
    tweet = Calls.objects.filter(id=id)
    users = User.objects.find({})
    for user in users:
        print(user)
        print(user.dispatcherid)
    '''
    for call in tweet:
        if call.incident not in non_tweetable_incidents:
            if call.dispatcher == 'QCA001':
                if call.state.upper() == 'CT' and call.town.upper() in tweetable_towns_ct:
                    tweet_data.append(
                        'UPDATED INCIDENT | ' + call.town + ' | ' + call.state + ' | ' + call.roadname + ' | ' + call.incident + ' | ' + call.narrative)
                    print('CT Tweet ', tweet_data)
                    api.update_status(tweet_data[0])
                    facebook_data = str(tweet_data[0] + ' | Updates at twitter.com/quietcorneralrt')
                    graph.put_object(facebook_page, 'feed', message=facebook_data)
                    '''
    return redirect(url_for('cad.dispatch'))

@cad.route('/confirm/<id>')
def confirm(id):
    Calls.objects(id=id).update(active='True')
    autotweet(id=id)
    national_autotweet(id=id)
    return redirect(url_for('cad.dispatch'))

@cad.route('/delete/<id>')
def delete(id):
    call = Calls.objects(id=id)
    logging.info('Incident Deleted:')
    call.delete()
    return redirect(url_for('cad.dispatch'))

def chat():
    global chat_data
    chat = Chat.objects.filter(Q(datetime__gte=str(date_time_minus_twentyfour_hr)))
    chat_data = []
    for msg in reversed(chat):
        user = [msg.date + ' ' + msg.times + ' ' + msg.dispatcher + ' : ']
        info = [user[0], msg.message]
        chat_data.append(info)
        #print('Chat Refreshed' + str(todaycalctime))
    #print(yesterdaycalctime)
    #print(chat_data)
    activeuser()
    return chat_data

def activeuser():
    global activeusers
    users = User.objects.filter(Q(lastconnection__gt=date_time_minus_one_min))
    #users = User.objects.filter((Q(lastconnectiondate__gte=str(currentdate) & Q(lastconnectiontime__gte=str(date_time_minus_one_min))))
    #print("Minus one min time " + str(date_time_minus_one_min))
    activeusers = []
    for boop in users:
        activeusers.append(boop.dispatcherid)
    print("active users " + str(activeusers))
    return activeusers

@cad.route('/newchat', methods=['POST'])
@jwt_required()
def newchat():
    user = User.objects.get(id=get_jwt_identity())
    if request.method == 'POST':
        chat = Chat(**request.form)
        chat.dispatcher = user.dispatcherid
        chat.datetime = current_date_time
        chat.date = current_date
        chat.times = current_time
        chat.save()
    return redirect(url_for('cad.dispatch'))

@cad.route('/_get_data/', methods=['POST'])
@jwt_required()
def _get_data():
    user = User.objects.get(id=get_jwt_identity())
    now = datetime.datetime.now()
    now_z = now - datetime.timedelta(hours=4)
    #print('now ', now)
    #print('now_Z ', now_z)
    now_minus_fifteen_sec = now_z - datetime.timedelta(seconds=30)
    print('now minus 14 sec', now_minus_fifteen_sec)
    calls = Calls.objects.filter(Q(datetime__gte=str(now_minus_fifteen_sec)))
    que = Calls.objects.filter(Q(active='False') & Q(datetime__gte=str(now_minus_fifteen_sec)))
    que_data = []
    for call in que:
        incidents = [call.id, call.date, call.times, call.town, call.state, call.roadname, call.incident,
                     call.narrative, call.dispatcher]
        que_data.append(incidents)
    twentyfourhour_data = []
    twentyfourhour = Calls.objects.filter(Q(active='True') & Q(datetime__gte=str(now_minus_fifteen_sec)))
    for call in twentyfourhour:
        incidents = [call.id, call.date, call.times, call.town, call.state, call.roadname, call.incident,
                     call.narrative, call.dispatcher, user.dispatcherid]
        twentyfourhour_data.append(incidents)
    print(que_data)
    print(twentyfourhour_data)
    return jsonify({'data': render_template('response.html', que_data=que_data, twentyfourhour_data=twentyfourhour_data)})

@cad.route('/map')
@jwt_required()
def map():
    try:
        def key():
            new_key = Keys()
            new_key.key = "test"
            new_key.expiration_date = 'test1'
            new_key.save()
        key()
        gettimes()
        try:
            path = os.path.join('./cad/templates', 'folium_map.html')
            print(path)
            os.remove(path)
        except Exception as error:
            print('0', error)
            pass
        map = folium.Map(location=[41.976060, -71.810070], tiles='openstreetmap', control_scale=True, zoom_start=9)
        folium.TileLayer('cartodbpositron').add_to(map)
        folium.LayerControl().add_to(map)
        twentyfourhour = Calls.objects.filter(Q(datetime__gte=str(date_time_minus_twentyfour_hr)))
        fire_incidents = ["1 ALARM FIRE", "ALARM UPGRADE", "MULTI ALARM FIRE", "ALARM ACTIVATION", "INSIDE FIRE",
                          "MINOR FIRE", "VEHICLE FIRE", "WIRE/TRANSFORMER FIRE"]
        water_incidents = ["WATER/ICE RESCUE"]
        wildfire_incidents = ["BRUSH FIRE","OUTSIDE FIRE"]
        police_incidents = ["BURGLARY","MISSING PERSON", "POLICE ACTIVITY", "PROTEST", "ROBBERY", ]
        violent_police_incidents = ["STABBING/SHOOTING"]
        tornado_incidents = ["TREE/WIRES DOWN", "REPORTED WEATHER EVENT"]
        earthquake_incidents = []
        medical_incidents = ["AIRCRAFT INCIDENT", "HAZMAT", "INDUSTRIAL ACCIDENT", "INJURED PERSON", "SEARCH AND RESCUE"
            , "SERIOUS VEHICLE ACCIDENT", "TECHNICAL RESCUE", "VEHICLE ACCIDENT"]
        explosive_incidents = ["EXPLOSION", "BOMB THREAT", "UNEXPLODED ORDINANCE"]
        try:
            for call in reversed(twentyfourhour):
                print(call.incident)
                try:
                    if str(call.incident) in fire_incidents:
                        print(call.incident)
                    # Icons https://icons8.com/icon/set/crime/material ios glyph
                        fire_icon = folium.features.CustomIcon(
                            icon_image='https://img.icons8.com/ios-glyphs/30/000000/fires.png', icon_size=(24, 24))
                        readout = [call.incident, call.date, call.times, call.roadname + ', ' + call.town + ', ' + call.state,
                                   call.narrative, call.dispatcher_credit]
                        folium.Marker(
                            location=[call.lat, call.lon],
                            popup=readout,
                            icon=fire_icon
                            ).add_to(map)
                    elif str(call.incident) in water_incidents:
                        print(call.incident)
                        water_icon = folium.features.CustomIcon(
                            icon_image="https://img.icons8.com/material/24/000000/small-fishing-boat.png", icon_size=(24, 24))
                        readout = [call.incident, call.date, call.times,
                                   call.roadname + ', ' + call.town + ', ' + call.state, call.narrative,
                                   call.dispatcher_credit]
                        folium.Marker(
                            location=[call.lat, call.lon],
                            popup=readout,
                            icon=water_icon
                        ).add_to(map)
                    elif str(call.incident) in wildfire_incidents:
                        print(call.incident)
                        wildfire_icon = folium.features.CustomIcon(
                            icon_image="https://img.icons8.com/ios-glyphs/30/000000/wildfire.png", icon_size=(24, 24))
                        readout = [call.incident, call.date, call.times,
                                   call.roadname + ', ' + call.town + ', ' + call.state, call.narrative,
                                   call.dispatcher_credit]
                        folium.Marker(
                            location=[call.lat, call.lon],
                            popup=readout,
                            icon=wildfire_icon
                        ).add_to(map)
                    elif str(call.incident) in police_incidents:
                        print(call.incident)
                        police_badge_icon = folium.features.CustomIcon(
                            icon_image='https://img.icons8.com/ios-glyphs/30/000000/police-badge.png', icon_size=(24, 24))
                        readout = [call.incident, call.date, call.times,
                                   call.roadname + ', ' + call.town + ', ' + call.state, call.narrative,
                                   call.dispatcher_credit]
                        folium.Marker(
                            location=[call.lat, call.lon],
                            popup=readout,
                            icon=police_badge_icon
                        ).add_to(map)
                    elif str(call.incident) in violent_police_incidents:
                        print(call.incident)
                        crime_icon = folium.features.CustomIcon(
                            icon_image="https://img.icons8.com/ios-glyphs/30/000000/crime.png", icon_size=(24, 24))
                        readout = [call.incident, call.date, call.times,
                                   call.roadname + ', ' + call.town + ', ' + call.state, call.narrative,
                                   call.dispatcher_credit]
                        folium.Marker(
                            location=[call.lat, call.lon],
                            popup=readout,
                            icon=crime_icon
                        ).add_to(map)
                    elif call.incident in medical_incidents:
                        print('5',call.incident)
                        ambulance_icon = folium.features.CustomIcon(
                            icon_image="https://img.icons8.com/ios-glyphs/30/000000/ambulance.png", icon_size=(24, 24))
                        readout = [call.incident, call.date, call.times,
                                   call.roadname + ', ' + call.town + ', ' + call.state, call.narrative,
                                   call.dispatcher_credit]
                        folium.Marker(
                            location=[call.lat, call.lon],
                            popup=readout,
                            icon=ambulance_icon
                        ).add_to(map)
                        map.save("./cad/templates/folium_map.html")
                    elif str(call.incident) in tornado_incidents:
                        tornado_icon = folium.features.CustomIcon(
                            icon_image="https://img.icons8.com/ios-glyphs/30/000000/tornado.png", icon_size=(24, 24))
                        readout = [call.incident, call.date, call.times,
                                   call.roadname + ', ' + call.town + ', ' + call.state, call.narrative,
                                   call.dispatcher_credit]
                        folium.Marker(
                            location=[call.lat, call.lon],
                            popup=readout,
                            icon=tornado_icon
                        ).add_to(map)
                    elif str(call.incident) in earthquake_incidents:
                        earthquake_icon = folium.features.CustomIcon(
                            icon_image="https://img.icons8.com/ios-glyphs/30/000000/earthquakes.png", icon_size=(24, 24))
                        readout = [call.incident, call.date, call.times,
                                   call.roadname + ', ' + call.town + ', ' + call.state, call.narrative,
                                   call.dispatcher_credit]
                        folium.Marker(
                            location=[call.lat, call.lon],
                            popup=readout,
                            icon=earthquake_icon
                        ).add_to(map)
                    elif str(call.incident) in explosive_incidents:
                        dynamite_icon = folium.features.CustomIcon(
                            icon_image="https://img.icons8.com/ios-glyphs/30/000000/dynamite.png", icon_size=(24, 24))
                        readout = [call.incident, call.date, call.times, call.roadname + ', ' + call.town + ', ' + call.state, call.narrative, call.dispatcher_credit]
                        folium.Marker(
                            location=[call.lat, call.lon],
                            popup=readout,
                            icon=dynamite_icon
                        ).add_to(map)
                    else:
                        print('beep')
                        readout = [call.incident, call.date, call.times,
                                   call.roadname + ', ' + call.town + ', ' + call.state, call.narrative,
                                   call.dispatcher_credit]
                        folium.Marker(
                            location=[call.lat, call.lon],
                            popup=readout,
                        ).add_to(map)
                except Exception as error:
                    print('1',error)
                    pass
        except Exception as error:
            print('2', error)
            pass
        map.save("./cad/templates/folium_map.html")
        return render_template('map.html')
    except Exception as error:
        print(error)
        return redirect(url_for('cad.dispatch'))



@jwt_required()
@cad.route('/data_poll', methods=['GET', 'POST'])
def chat_room():
    return render_template('data_poll.html')

'''
@sock.route('/echo')
def echo(sock):
    while True:
        data = sock.receive()
        sock.send(data)
'''
'''
socketio.on('join', namespace='/chat_room')
def join(message):
    room = session.get('room')
    join_room(room)
    emit('status', {'msg': session.get('username') + 'has entered the room.'}, room=room)

@socketio.on('text', namespace='/chat_room')
def text(message):
    room = session.get('room')
    emit('message',{'msg': session.get('username') + ' : ' + message['msg']}, room=room)

@socketio.on('left', namespace='/chat_room')
def left(message):
    room = session.get('room')
    username = session.get('username')
    leave_room(room)
    session.clear()
    emit('status', {'msg' : username + ' has left the room.'}, room=room)
    '''



