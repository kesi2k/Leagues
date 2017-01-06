from flask import Flask, render_template, request, redirect, jsonify, url_for
from flask import flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, League, Team, Players, User
from flask import session as login_session
import random
import string
import os

# Flow object from clients secret JSON file. Stores client ID and other
# Oauth parameters
from oauth2client.client import flow_from_clientsecrets

# For handling errors trying get client authentication
from oauth2client.client import FlowExchangeError
import httplib2

# API in python for converting in memory Python objects to JSON
import json

# Convert return value from function to response we can send
from flask import make_response

# HTTP library similar to URLlib2, with improvements
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Soccer Leagues"


# Connect to Database and create database session
# engine = create_engine('sqlite:///restaurantmenu.db')
engine = create_engine('sqlite:///soccerleagues.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# User functions
def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


# Login user with their Google credentials
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps
                                 ('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: \
    150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# Logout. Revoke user's token and reset login_session
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user
    access_token = login_session['access_token']
    print 'Access token in disconnect is %s', access_token
    print 'User name is: '
    print login_session['username']
    if access_token is None:
        response = make_response(json.dumps('Current user not connected.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % \
        login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = 'Successfully disconnected.'
        return render_template('logout.html', response=response)
    else:
        response = 'Failed to revoke token for given user.'
        return render_template('logout.html', response=response)


# JSON APIs to view info on the DB
# Show all the teams in a league
@app.route('/league/<int:league_id>/teams/JSON')
def teamsJSON(league_id):
    teams = session.query(Team).filter_by(league_id=league_id).all()
    return jsonify(Teams=[i.serialize for i in teams])


# Show all teams in the DB
@app.route('/leagues/teams/JSON')
def allTeamsJSON():
    teams = session.query(Team).all()
    return jsonify(Teams=[i.serialize for i in teams])


# Show all players in all leagues
@app.route('/leagues/players/JSON')
def playersJSON():
    players = session.query(Players).all()
    return jsonify(Players=[i.serialize for i in players])


# Show all leagues
@app.route('/')
@app.route('/leagues')
def leaguesPage():
    leagues = session.query(League).order_by(asc(League.name))
    return render_template('league.html', leagues=leagues,
                           login_session=login_session)


# Create a new league
@app.route('/leagues/new', methods=['GET', 'POST'])
def newLeague():
    # Check that user is logged in
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    if request.method == 'POST':
        if request.form['name']:
            newLeague = League(name=request.form['name'],
                               user_id=login_session['user_id'])
            session.add(newLeague)
            flash('New League %s Successfully Created' % newLeague.name)
            session.commit()
            return redirect(url_for('leaguesPage'))
        else:
            return redirect(url_for('leaguesPage'))
    else:
        return render_template('newLeague.html', login_session=login_session)


# Edit a league
@app.route('/leagues/<int:league_id>/edit', methods=['GET', 'POST'])
def editLeague(league_id):
    # Check that user is logged in
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    editedleague = session.query(League).filter_by(id=league_id).one()
    user = getUserID(login_session['email'])
    print 'this is the current user id: ', user
    print 'This is the id of league creator: ', editedleague.user_id
    # Check current user to see if they are authorized
    if editedleague.user_id != user:
        response = 'You are not authorized for this'
        return render_template('unauth.html', response=response)
    if request.method == 'POST':
        if request.form['name']:
            editedleague.name = request.form['name']
            flash('Successfully Edited %s' % editedleague.name)
            return redirect(url_for('leaguesPage'))
    else:
        return render_template('editLeague.html', league=editedleague,
                               login_session=login_session)


# Delete a specific league
@app.route('/leagues/<int:league_id>/delete', methods=['GET', 'POST'])
def delLeague(league_id):
    # Check that user is logged in
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    deleteLeague = session.query(League).filter_by(id=league_id).one()
    user = getUserID(login_session['email'])
    # Check current user to see if they are authorized
    if deleteLeague.user_id != user:
        response = 'You are not authorized for this'
        return render_template('unauth.html', response=response)
    if request.method == 'POST':
        # Delete the associated teams, and associated players with the teams
        players = session.query(Players).filter_by(league_id=league_id).all()
        for i in players:
            session.delete(i)
        teams = session.query(Team).filter_by(league_id=league_id).all()
        for i in teams:
            session.delete(i)
        session.delete(deleteLeague)
        flash('Successfully deleted %s' % deleteLeague.name)
        session.commit()
        return redirect(url_for('leaguesPage'))
    else:
        return render_template('deleteLeague.html', league=deleteLeague,
                               login_session=login_session)


# Show teams in a specific league
@app.route('/leagues/<int:league_id>/')
@app.route('/leagues/<int:league_id>/teams/')
def teams(league_id):
    league = session.query(League).filter_by(id=league_id).one()
    teams = session.query(Team).filter_by(
                                          league_id=league_id).order_by(
                                          Team.pts.desc()).all()
    user = session.query(User).filter_by(id=league.user_id).one()
    return render_template('teams.html', league=league, teams=teams,
                           user=user, login_session=login_session)


# Add a new team to the league
@app.route('/leagues/<int:league_id>/new', methods=['GET', 'POST'])
def newTeam(league_id):
    # Check that user is logged in
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    # Adding the team to this league
    league = session.query(League).filter_by(id=league_id).one()
    if request.method == 'POST':
        if request.form['name']:
            newTeam = Team(league_id=league.id, name=request.form['name'],
                           pts=0, win=0, lose=0, draw=0,
                           user_id=login_session['user_id'])
            session.add(newTeam)
            session.commit()
            return redirect(url_for('teams', league_id=league_id))
        else:
            return redirect(url_for('teams', league_id=league_id))
    else:
        return render_template('newTeam.html', league=league,
                               login_session=login_session)


# Edit a specific team in a league
@app.route('/leagues/<int:league_id>/teams/<int:team_id>/edit',
           methods=['GET', 'POST'])
def editTeam(league_id, team_id):
    # Check that user is logged in
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    editedTeam = session.query(Team).filter_by(league_id=league_id).filter_by(
                                               id=team_id).one()
    user = getUserID(login_session['email'])
    # Check current user to see if they are authorized
    if editedTeam.user_id != user:
        response = 'You are not authorized for this'
        return render_template('unauth.html', response=response)
    if request.method == 'POST':
        if request.form['name']:
            editedTeam.name = request.form['name']
        if request.form['points']:
            editedTeam.pts = request.form['points']
        if request.form['win']:
            editedTeam.win = request.form['win']
        if request.form['lose']:
            editedTeam.lose = request.form['lose']
        session.add(editedTeam)
        session.commit()
        flash('Team successfully edited')
        return redirect(url_for('teams', league_id=editedTeam.league_id))
    else:
        return render_template('editTeam.html', editedTeam=editedTeam,
                               login_session=login_session)


# Delete a team in a specific league
@app.route('/leagues/<int:league_id>/teams/<int:team_id>/delete',
           methods=['GET', 'POST'])
def deleteTeam(league_id, team_id):
    # Check that user is logged in
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    deletedTeam = session.query(Team).filter_by(
                                                league_id=league_id).filter_by(
                                                id=team_id).one()
    user = getUserID(login_session['email'])
    # Check current user to see if they are authorized
    if deletedTeam.user_id != user:
        response = 'You are not authorized for this'
        return render_template('unauth.html', response=response)
    if request.method == 'POST':
        # Delete players associated with team
        deletePlayers = session.query(
                                      Players).filter_by(
                                      league_id=league_id).filter_by(
                                      team_id=team_id).all()
        for i in deletePlayers:
            print 'This player was deleted: ', i.name
            session.delete(i)
        # Delete team
        print 'This team was deleted: ', deletedTeam
        session.delete(deletedTeam)
        session.commit()
        return redirect(url_for('teams', league_id=deletedTeam.league_id))
    else:
        return render_template('deleteTeam.html',
                               deletedTeam=deletedTeam,
                               login_session=login_session)


# Show players in a specific team
@app.route('/league/<int:league_id>/teams/<int:team_id>')
def players(league_id, team_id):
    team = session.query(Team).filter_by(id=team_id).one()
    players = session.query(Players).filter_by(team_id=team_id).all()
    user = session.query(User).filter_by(id=team.user_id).one()
    return render_template('players.html',
                           team=team, players=players, user=user,
                           login_session=login_session)


# Edit players in a specific team
@app.route('/league/<int:league_id>/teams/<int:team_id>/edit\
    Player/<int:player_id>', methods=['GET', 'POST'])
def editPlayer(league_id, team_id, player_id):
    # Check that user is logged in
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    team = session.query(Team).filter_by(league_id=league_id).filter_by(
                                         id=team_id).one()
    player = session.query(Players).filter_by(
                                            league_id=league_id).filter_by(
                                            team_id=team_id).filter_by(
                                            id=player_id).one()
    user = getUserID(login_session['email'])
    # Check current user to see if they are authorized
    if player.user_id != user:
        response = 'You are not authorized for this'
        return render_template('unauth.html', response=response)
    if request.method == 'POST':
        if request.form['name']:
            player.name = request.form['name']
        if request.form['position']:
            player.position = player.position = request.form['position']
        session.add(player)
        session.commit()
        flash('Player successfully edited')
        return redirect(url_for('players',
                                league_id=player.league_id,
                                team_id=player.team_id))
    else:
        return render_template('editPlayer.html', team=team, player=player,
                               login_session=login_session)


# Delete a player in a specific league
@app.route('/league/<int:league_id>/teams/<int:team_id>/deletePlayer/\
    <int:player_id>', methods=['GET', 'POST'])
def deletePlayer(league_id, team_id, player_id):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    player = session.query(Players).filter_by(
                                            league_id=league_id).filter_by(
                                            team_id=team_id).filter_by(
                                            id=player_id).one()
    user = getUserID(login_session['email'])
    # Check current user to see if they are authorized
    if player.user_id != user:
        response = 'You are not authorized for this'
        return render_template('unauth.html', response=response)
    if request.method == 'POST':
        session.delete(player)
        flash('Player successfully deleted')
        return redirect(url_for('players', league_id=player.league_id,
                                team_id=player.team_id))
    else:
        return render_template('deletePlayer.html', player=player,
                               login_session=login_session)


# Create a new player in a specific team
@app.route('/league/<int:league_id>/teams/<int:team_id>/newplayer',
           methods=['GET', 'POST'])
def newPlayer(league_id, team_id):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    team = session.query(Team).filter_by(
                                         league_id=league_id).filter_by(
                                         id=team_id).one()
    if request.method == 'POST':
        if request.form['name']:
            newPlayer = Players(name=request.form['name'],
                                position=request.form['position'],
                                league_id=league_id, team_id=team_id,
                                user_id=login_session['user_id'])
            session.add(newPlayer)
            session.commit()
        return redirect(url_for('players', league_id=team.league_id,
                                team_id=team.id))
    else:
        return render_template('newPlayer.html', team=team,
                               login_session=login_session)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 33507))
    app.secret_key = 'super_secret_key'
    #app.run(host='0.0.0.0', port=8080)
    app.run(host='0.0.0.0', 
            port=port)
