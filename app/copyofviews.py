# views.py
from __future__ import print_function

from flask import redirect, render_template, send_from_directory
from flask import request

import json
import re
import urllib2 as urllib
import requests

from app import app

@app.route('/')
def default():
    return redirect("/lookup", code=302)


@app.route('/lookup', methods=['GET'])
def index():
    if not request.args.get('first_name') is None:
        first_name = request.form['first_name'] if request.method == 'POST' else request.args.get('first_name')
        last_name = request.form['last_name'] if request.method == 'POST' else request.args.get('last_name')

        content = {
            'player_icon_img' : "https://blzgdapipro-a.akamaihd.net/game/unlocks/0x025000000000069F.png",
            'player_portrait_img' : "https://blzgdapipro-a.akamaihd.net/game/playerlevelrewards/0x0250000000000922_Border.png",
            'player_name': first_name,
            'player_id_num': last_name, 
            'player_rank': '2302',
            'player_star_img' : None,
            'player_level': '102',
            'player_rank_emblem_img' : "https://blzgdapipro-a.akamaihd.net/game/rank-icons/season-2/rank-1.png",
            'player_comp_w' : None,
            'player_comp_l' : None,
            'player_win_ratio' : 55,
            'player_lost_ratio' : 45,
            'player_best_hero' : None,
            'player_hero_win_rate' : None,
            'player_num_quickwins' : None,

            # hero_img, name, wins, losses, ties, rate, killstreak_best, dmg_most, elims_most, deaths_avrg, dmg_avrg, elims_avrg, playtime_total, total_objtime_total, firetime_total
            'hero': [
                ("https://blzgdapipro-a.akamaihd.net/game/heroes/small/0x02E0000000000065.png",
                "George1", 1, 2, 3, 25,
                15, 25, 35,
                25, 35, 45,
                35, 45, 55
                ),
                ("https://blzgdapipro-a.akamaihd.net/game/heroes/small/0x02E0000000000065.png",
                "George2", 1, 2, 3, 25,
                15, 25, 35,
                25, 35, 45,
                35, 45, 55
                ),
                ("https://blzgdapipro-a.akamaihd.net/game/heroes/small/0x02E0000000000065.png",
                "George3", 1, 2, 3, 25,
                15, 25, 35,
                25, 35, 45,
                35, 45, 55
                ),   
            ]
        }


        if not ow_api_call(first_name, last_name, content):
            return "Could not find a profile matching " + first_name + " " + last_name

        return render_template("results.html", **content)
    else:       
        return render_template("index.html")

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404  

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

def ow_api_call(name, id_num, content):

    # Build the targetted API request url
    # urllib.install_opener(urllib.build_opener(urllib.ProxyHandler({'http': 'proxy.server:3128'})))
    url = 'https://api.lootbox.eu/pc/us/' + name + '-' + id_num + '/profile'
    print("Fetching data from ", url,)

    # Retrieve response
    response = requests.get(url)
    # Load response data into a usable variable
    data = response.json()["data"]

    # Validate data
    if "no user" in str(data):
        print("Could not find user")
        print(str(data))
        return False

    user_data = populate_user_data(data)
    data_keys = user_data.keys()
    data_keys.sort()

    print(data_keys)

    content['player_icon_img'] = user_data['avatar']
    content['player_portrait_img'] = user_data['levelFrame']
    content['player_rank'] = str(user_data['competitive_rank']) if user_data['competitive_rank'] else '???'

    content['player_name'] = user_data['username']
    content['player_star_img'] = user_data['star'] if user_data['star'] else None
    content['player_level'] = user_data['level']

    if 'rank_img' in data:
        content['player_rank_emblem_img'] = user_data['competitive_rank_img']

    content['player_comp_w'] = user_data['games_competitive_wins']
    content['player_comp_l'] = user_data['games_competitive_lost']

    num_win = int(user_data['games_competitive_wins'])
    num_total = float(user_data['games_competitive_played'])
    comp_perc = int((num_win / num_total) * 100)

    content['player_win_ratio'] = comp_perc
    content['player_lost_ratio'] = 100 - comp_perc


    heroes_details = fetch_favorite_heros(name, id_num)
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
    content['player_num_quickwins'] = user_data['games_quick_wins']

    return True

def fetch_favorite_heros(name, id_num):
    # Second part
    url = "https://api.lootbox.eu/pc/us/"  + name + '-' + id_num + "/competitive/heroes"
    print("Fetching data from ", url,)

    # Retrieve response
    response = requests.get(url)
    # Load response into a usable variable
    data = response.json()

    heroes = []
    num_results = 5

    for i in range(num_results):
        hero_details = []
        hero_details.append(data[i]['image'])   #[0]
        
        hero = hero_lookup(data[i]['name'])
        hero_details.append(hero)    #[1]

        hero_details = hero_details + fetch_hero_info(name, id_num, hero)

        heroes.append(hero_details)

    return heroes

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
Fetch hero info for a given @hero for user @name @id_num
'''
def fetch_hero_info(name, id_num, hero):

    url = "https://api.lootbox.eu/pc/us/" + name + '-' + id_num + "/competitive/hero/" + hero + "/"

    print("Fetching data from ", url,)

    # Retrieve response
    response = requests.get(url)
    # Load response into a usable variable
    data = response.json()[response.json().keys()[0]]

    data_copy = {}
    for keys in data.keys():
        data_copy[keys] = data[keys]
    data = data_copy

    #Reference of key categories for displaying profile data
    info = ["GamesLost", "GamesTied", "GamesWon", "WinPercentage"]
    best = ["KillStreak-Best", "DamageDone-MostinGame", "Eliminations-MostinGame"]
    averages = ["Eliminations-Average", "DamageDone-Average", "Deaths-Average"]
    time = ["TimePlayed", "ObjectiveTime", "TimeSpentonFire"]


    hero_details = []
    hero_details.append(data['GamesWon'])
    hero_details.append(data['GamesLost'])

    hero_details.append(int(data['GamesPlayed']) - ( int(data['GamesWon']) + int(data['GamesLost']) ))
    hero_details.append(data['WinPercentage'])

    win_perc = str(data['WinPercentage'])
    win_perc = int(win_perc.replace("%", ""))
    
    # if win_perc < 50:
    #     html += "#879292"
    # elif win_perc <= 60:
    #     html += "#2daf7f"
    # elif win_perc <= 68:
    #     html += "#1f8ecd"
    # else:
    #     html += "#c6443e" 

    hero_details.append(str(data['KillStreak-Best']))
    hero_details.append(str(data['DamageDone-MostinGame']))
    hero_details.append(str(data['Eliminations-MostinGame']))

    hero_details.append(str(data['Deaths-Average']))
    hero_details.append(str(data['DamageDone-Average']))
    hero_details.append(str(data['Eliminations-Average']))

    hero_details.append(time_dejsonify(str(data['TimePlayed'])))
    hero_details.append(time_dejsonify(str(data['ObjectiveTime'])))
    hero_details.append(time_dejsonify(str(data['TimeSpentonFire'])))

    return hero_details



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