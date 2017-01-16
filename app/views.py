# views.py
from __future__ import print_function
from flask import make_response, redirect, render_template, request, send_from_directory
from multiprocessing import Lock, Pipe

import json
import Queue
import re
import requests
import threading
import urllib2 as urllib

from app import app

# @app.route('/')
# def default():
#     return redirect("/lookup", code=302)


@app.route('/', methods=['GET', 'POST'])
def index():
    if not request.args.get('first_name') is None:
        name = request.form['first_name'] if request.method == 'POST' else request.args.get('first_name')
        tag = request.form['last_name'] if request.method == 'POST' else request.args.get('last_name')

        console = request.args.get('console')
        console =  console.lower()
        console = "xbl" if console == "xboxone" else "psn" if console == "ps4" else console

        region = request.args.get('region')
        region = region.lower()

        num_results = request.args.get('num_results')
        num_results = num_results.replace(" heros", "")
        if num_results == 'No':
            num_results = 0
        else:
            num_results = int(num_results)

        print("{} {} {}".format(console, region, num_results))

        content = {
            'player_icon_img' : None,
            'player_portrait_img' : None,
            'player_name': name,
            'player_tag': tag, 
            'player_rank': None,
            'player_star_img' : None,
            'player_level': None,
            'player_rank_emblem_img' : "https://blzgdapipro-a.akamaihd.net/game/rank-icons/season-2/rank-1.png",
            'player_comp_w' : None,
            'player_comp_l' : None,
            'player_win_ratio' : None,
            'player_lost_ratio' : None,
            'player_best_hero' : None,
            'player_hero_win_rate' : None,
            'player_num_quickwins' : None,

            'hero': [
            # hero_img, name, wins, losses, ties, rate, killstreak_best, dmg_most, elims_most,
            # deaths_avg, dmg_avg, elims_avg, playtime_total, total_objtime_total, firetime_total
                ('hero.png', 'name', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                ('hero.png', 'name', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                ('hero.png', 'name', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
            ]
        }

        conn1, conn2 = Pipe()
        lock = Lock()

        t1 = threading.Thread(target=get_gen_data, args = (content, name, tag, console, region, conn1, lock))
        t1.start()

        t2 = threading.Thread(target=fetch_favorite_heros, args = (content, name, tag, console, region, num_results, conn2, lock))
        t2.start()

        resp = None

        t1 = t1.join()
        t2 = t2.join()

        if content['hero'][0][0] == 'hero.png':            
            content = {'name' : name, 'tag' : tag, 'console' : console.upper(), 'region' : region.upper()}
            resp = make_response(render_template("no_user_found.html", **content))
            resp.status_code = 501
        else:
            resp = make_response(render_template("results.html", **content))
            resp.set_cookie('last_login', "{}#{}".format(name, tag), max_age=30*24*60*60) #30 days, or 2592000 seconds
            resp.status_code = 200

        # if app.DEBUG:
            # import logging
            # from logging.handlers import RotatingFileHandler
            # app.logger.info('User attempt: {}#{} {} {}, status: {}'.format(name, tag, console, region, resp.status_code))

        return resp
    else:
        cookie = request.cookies.get("last_login")
        name = ""
        tag = ""

        if cookie != None:
            parts = cookie.split("#")
            name = parts[0]
            tag =  parts[1]

        return render_template("index.html", name=name, tag=tag)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404  

'''
Helper method for converting jsonified time constructs, eg. "1hour", "08:51", etc,
into human legible wording, eg. "1 hour", "08m 51s"
'''
def time_dejsonify(amount):
    if "hour" in amount:
        m = re.search("(.*?)hour", amount)
        m = m.group(1)
        return "~" + m + " hour" + ("s" if int(m) != 1 else "")
    elif ":" in amount:
        pieces = amount.split(":")
        return pieces[0].replace("0", "") + "m " + pieces[1] + "s"

'''
Because the json response has multiple keys with the same name, but in different
heircharchys, this method exists to create a new json dict that uses the full
key heirarchy of each object as a key, for instance there is both
a player_star_img and an player_rank_emblem_img
'''
def populate_user_data(data):
    user_data = {}

    for keys in data.keys():
        if type(data[keys]) is dict:
            for keys2 in data[keys].keys():
                if type(data[keys][keys2]) is dict:
                    for keys3 in data[keys][keys2].keys():
                        user_data[keys + '_' + keys2 + '_' + keys3] = data[keys][keys2][keys3]
                else:
                    user_data[keys + '_' + keys2] = data[keys][keys2]
        else:
            user_data[keys] = data[keys]

    if len(user_data['star']) == 0:
        user_data['star'] = 0

    return user_data


'''
I don't know why, but the API I used is very inconsistent with its naming
conventions. The return value for Torbjoern uses the &#xF6;rn symbol,
but the respective API call url uses Torbjoern.
'''
def hero_lookup(name):
    # print("The hero lookup name is ^" + name + "^")
    if 'Torbj&#xF6;rn' in name:
        return 'Torbjoern'
    elif 'L&#xFA;cio' in name:
        return 'Lucio'
    elif 'Soldier: 76' in name:
        return 'Soldier 76'
    else:
        return name


# called by thread 0A
def get_gen_data(content, name, tag, console, region, conn1, lock):

    #Lock immediately so there's no way in hell for the next process to try to retreive from
    #an empty pipe
    lock.acquire()

    # Retrieve response
    url = 'https://api.lootbox.eu/{}/{}/{}-{}/profile'.format(console, region, name, tag)

    print("Fetching data from ", url,)
    response = requests.get(url)
    # Load response data into a usable variable
    data = response.json()["data"]
    
    # Validate data
    if "no user" in str(data):
        print("Could not find user {} {} {} {}".format(name, tag, console, region))
        # print(str(data))
        return False

    user_data = populate_user_data(data)

    conn1.send(user_data['games_quick_wins'])
    lock.release()

    data_keys = user_data.keys()
    data_keys.sort()

    content['player_icon_img'] = user_data['avatar']
    content['player_portrait_img'] = user_data['levelFrame']
    content['player_rank'] = str(user_data['competitive_rank']) if user_data['competitive_rank'] else '???'

    content['player_name'] = user_data['username']
    content['player_star_img'] = user_data['star'] if user_data['star'] else None
    content['player_level'] = user_data['level']

    # if 'rank_img' in data:
    print("Jello")
    print(user_data.get('competitive_rank_img'))
    print(user_data.get('competitive_rank_img') == "None")
    print(user_data.get('competitive_rank_img') == None)
    if user_data.get('competitive_rank_img'):
        content['player_rank_emblem_img'] = user_data.get('competitive_rank_img') 

    content['player_comp_w'] = user_data['games_competitive_wins']
    content['player_comp_l'] = user_data['games_competitive_lost']

    num_win = int(user_data['games_competitive_wins'])
    num_total = float(user_data['games_competitive_played'])
    comp_perc = int((num_win / num_total) * 100)

    content['player_win_ratio'] = comp_perc
    content['player_lost_ratio'] = 100 - comp_perc

    return True

# called by thread 1A
def fetch_favorite_heros(content, name, tag, console, region, num_results, conn2, lock):
    heroes_details = fetch_favorite_heros_helper(name, tag, console, region, num_results)
    if not heroes_details:
        return False
    content['hero'] = heroes_details

    max_val = 1
    best_name = None
    for i in range(len(heroes_details)):
        tmp_win_rate = int(heroes_details[i][5].replace("%", ""))
        if tmp_win_rate > max_val:
            max_val = tmp_win_rate
            best_name = heroes_details[i][1]


    content['player_best_hero'] = hero_lookup(str(best_name))
    content['player_hero_win_rate'] = max_val

    # Wait until thread 0A has created user_data
    lock.acquire()
    games_quick_wins = conn2.recv()
    lock.release()

    content['player_num_quickwins'] = games_quick_wins

    return True

def thread_work(q, data, i, name, tag):

    hero_details = []
    hero_details.append(data[i]['image'])
        
    hero_name = hero_lookup(data[i]['name'])
    hero_details.append(hero_name)

    # print("Thread {} starting work".format(i))
    results = fetch_hero_info(name, tag, hero_name)
    # print("Thread {} finishing work".format(i))

    # Combine two lists quick and easy
    hero_details = hero_details + results
    q.put(hero_details)

def fetch_hero_info(name, tag, hero):

    url = "https://api.lootbox.eu/pc/us/" + name + '-' + tag + "/competitive/hero/" + hero + "/"

    print("Fetching data from ", url,)

    # Retrieve response
    response = requests.get(url)
    # Load response into a usable variable
    data = response.json()[response.json().keys()[0]]

    data_copy = {}
    for keys in data.keys():
        data_copy[keys] = data[keys]
    data = data_copy

    # Reference of key categories for displaying profile data
    # This doesn't actually affect anything
    info = ["GamesLost", "GamesTied", "GamesWon", "WinPercentage"]
    best = ["KillStreak-Best", "DamageDone-MostinGame", "Eliminations-MostinGame"]
    averages = ["Eliminations-Average", "DamageDone-Average", "Deaths-Average"]
    time = ["TimePlayed", "ObjectiveTime", "TimeSpentonFire"]

    hero_details = []
    hero_details.append(data.get('GamesWon'))
    hero_details.append(data.get('GamesLost'))

    hero_details.append(int(data.get('GamesPlayed')) - ( int(data.get('GamesWon')) + int(data.get('GamesLost')) ))
    hero_details.append(data.get('WinPercentage'))

    win_perc = str(data.get('WinPercentage'))
    win_perc = int(win_perc.replace("%", ""))

    hero_details.append(str(data.get('KillStreak-Best')))
    hero_details.append(str(data.get('DamageDone-MostinGame')))
    hero_details.append(str(data.get('Eliminations-MostinGame')))

    hero_details.append(str(data.get('Deaths-Average')))
    hero_details.append(str(data.get('DamageDone-Average')))
    hero_details.append(str(data.get('Eliminations-Average')))

    hero_details.append(time_dejsonify(str(data.get('TimePlayed'))))
    hero_details.append(time_dejsonify(str(data.get('ObjectiveTime'))))
    hero_details.append(time_dejsonify(str(data.get('TimeSpentonFire'))))

    return hero_details


def fetch_favorite_heros_helper(name, tag, console, region, num_results):
    # Second part
    url = "https://api.lootbox.eu/{}/{}/{}-{}/competitive/heroes".format(console, region, name, tag)
    print("Fetching data from ", url,)

    # Retrieve response
    response = requests.get(url)
    # Load response into a usable variable
    data = response.json()

    if "no user" in str(data):
        print("Could not find user {} {} {} {}".format(name, tag, console, region))
        # print(str(data))
        return False

    heroes = []
    threads = []
    q = Queue.Queue()

    for i in range(num_results):
        t = threading.Thread(target=thread_work, args = (q, data, i, name, tag))
        threads.append(t)
        # t.daemon = True
        t.start()

        # heroes.append(hero_details)

    for t in threads:
        t.join()

    for i in range(num_results):
        heroes.append(q.get())

    return heroes

# q = Queue.Queue()

'''
python regex
regex101
python replace all

boostrap 3 columns
DevNote: just spent ~2 hours debugging how I use class=".col-md-4" instead of just class="col-md-4"

overwatch ranked SR

purple shades hex
red shades hex

python multiprocessing

inline vs inline-block

css image border effects
css selector odd even
css box shadow

two images on top of each other

jinja2 template attribute spot
jinja2 template add strings
jinja2 template cast strings
jinja contatenate strings for attribute
jinja spaces
'''