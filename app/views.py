# views.py
from __future__ import print_function

from flask import redirect, render_template, send_from_directory
from flask import request

import json
import re
import urllib

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
            'player_name': 'jpezninjo', 
            'player_rank': '2302',
            'player_star_img' : "https://blzgdapipro-a.akamaihd.net/game/playerlevelrewards/0x0250000000000922_Rank.png",
            'player_level': '102',
            'player_rank_emblem_img' : "https://blzgdapipro-a.akamaihd.net/game/rank-icons/season-2/rank-4.png",
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



        return render_template("results.html", **content)
            # ow_api_call(first_name, last_name))
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
    if name == 'Torbj&#xF6;rn':
        return 'Torbjoern'
    elif name == 'L&#xFA;cio':
        return Lucio
    elif name == 'Soldier: 76':
        return 'Soldier76'
    else:
        return name

def ow_api_call(name, id_num):

    # Build the targetted API request url
    url = 'https://api.lootbox.eu/pc/us/' + name + '-' + id_num + '/profile'
    print("Fetching data from ", url,)

    # Retrieve response
    response = urllib.urlopen(url)
    print("Received response, code: " + str(response.getcode()) + "\n")

    # Load response into a usable variable
    data = response.read().decode("utf-8")
    data = json.loads(data)
    data = data[data.keys()[0]]
    
    # Validate data
    no_user_error = "Found no user with the BattleTag:"
    if no_user_error in str(data):
        return "<p>" + str(data[data.keys()[0]]) + "</p>"


    # TODO: Don't like this
    html_data = """
    <style>body{text-align:center}
    .special{display: inline-block;width: 250px;text-align: right;}
    .right{display: inline-block; padding-left: 5px; text-align: left; width: 160px;}
    h2{margin: 0;}

    .container{margin-top: 50px;}
    .row{background-color: rgb(214, 214, 214); border: 3px solid black}
    .col-md-4{border: 1px solid black; padding: 10px 15px; overflow: hidden;}

    .SR-p{
        background-color: #2E0854;
        display: inline;
        padding: 5px 10px 13px 11px;
        border-radius: 15px;
    }

    .SR-num, .SR-SR{
        font-weight: bold;
        vertical-align: text-top;
    }

    .SR-num{
        font-size: 24px;
        color: white;
    }

    .SR-SR{
        font-size: 17px;
        color: #9A32CD;
        padding-left: 7.5px;
    }

    </style>
    """

    html_start = ''
    html_end = '<div style="position:relative">'

    user_data = populate_user_data(data)
    data_keys = user_data.keys()
    data_keys.sort()

    html_data += str(user_data['username']) + "<br>"
    html_data += "Level "+ str(user_data['level']) + "<br>"
    # if not user_data['star'] is None:
        # html_data += "<img src=" + str(user_data['star']) + " style='position: absolute; clip: rect(64px,256px,128px,0px); left: 50%; margin-left: -128px;'><br>"
    
    html_data += "<p class='SR-p'><span class='SR-num'>" + str(user_data['competitive_rank']) + "</span><span class='SR-SR'>SR</span></p>"

    # html_data += "Competitive-" + str(user_data['games_competitive_wins']) + "W " + str(user_data['games_competitive_lost']) + " L<br>"
    
    comp_perc = int(user_data['games_competitive_wins']) / (int(user_data['games_competitive_played']))

    html_data += "<div class='c100 p55 small green'>"
    html_data += "<span>45%</span>"
    html_data += "<div class='slice'>"
    html_data += "<div class='bar'></div>"
    html_data += "<div class='fill'></div>"
    html_data += "</div>"
    html_data += "</div>"

    html_data += "Total quickplay wins: " + str(user_data['games_quick_wins'])

    html_data += fetch_favorite_heros(name, id_num)

    html_end += '</div>'

    html_data = html_start + html_data + html_end
    
    
    return html_data

def fetch_favorite_heros(name, id_num):
    # Second part
    url = "https://api.lootbox.eu/pc/us/"  + name + '-' + id_num + "/competitive/heroes"
    print("Fetching data from ", url,)

    # Retrieve response
    response = urllib.urlopen(url)
    print("Received response, code: " + str(response.getcode()) + "\n")

    # Load response into a usable variable
    data = response.read().decode("utf-8")
    data = json.loads(data)

    html_data  = ""
    html_data += "<div class='container'>"
    html_data += "<div class='row'>"
    for i in range(3):
        # print(data[i])

        
        html_data += "<div class='col-md-4'>"
        html_data += "<img src=" + data[i]['image'] + "><br>"
        html_data += "<h2>" + data[i]['name'] + "</h2>"

        hero = data[i]['name']
        # print("Hero-", hero)
        html_data += fetch_hero_info(name, id_num, hero)
        html_data += "</div>"
    
    html_data += "</div>"
    html_data += "</div>"
    html_data += "\n\n\n"

    return html_data

'''
Helper method for converting jsonified time constructs, eg. "1hour", "08:51", etc,
into human legible wording, eg. "1 hour", "08m 51s"
'''
def time_dejsonify(amount):
    if "hour" in amount:
        m = re.search("(.*?)hour", amount)
        m = m.group(1)
        return "~" + m + " hour"
    if ":" in amount:
        pieces = amount.split(":")
        return pieces[0].replace("0", "") + "m " + pieces[1] + "s"
        # return amount.replace(":", "m ") + "s"

def fetch_hero_info(name, id_num, hero):
    url = "https://api.lootbox.eu/pc/us/" + name + '-' + id_num + "/competitive/hero/" + hero_lookup(hero) + "/"
    print("Fetching data from ", url,)

    # Retrieve response
    response = urllib.urlopen(url)
    print("Received response, code: " + str(response.getcode()) + "\n")

    # Load response into a usable variable
    data = response.read().decode("utf-8")
    data = json.loads(data)
    data = data[data.keys()[0]]

    data_copy = {}
    for keys in data.keys():
        data_copy[keys] = data[keys]
    data = data_copy

    #Reference of key categories for displaying profile data
    info = ["GamesLost", "GamesTied", "GamesWon", "WinPercentage"]
    best = ["KillStreak-Best", "DamageDone-MostinGame", "Eliminations-MostinGame"]
    averages = ["Eliminations-Average", "DamageDone-Average", "Deaths-Average"]
    time = ["TimePlayed", "ObjectiveTime", "TimeSpentonFire"]

    html = ""
    # html += "<p>"
    html += "<span style='color: green'>" + str(data['GamesWon']) + "W</span>"
    html += " <span style='color: red'>" + str(data['GamesLost']) + "L</span>"
    html += " <span style='color: grey'>" + str( int(data['GamesPlayed']) - ( int(data['GamesWon']) + int(data['GamesLost']) )  )  + "T</span><br>"

    win_perc = str(data['WinPercentage'])
    win_perc = int(win_perc.replace("%", ""))
    
    html += "<span style='color: "
    if win_perc < 50:
        html += "#879292"
    elif win_perc <= 60:
        html += "#2daf7f"
    elif win_perc <= 68:
        html += "#1f8ecd"
        # html += "orange"
    else:
        html += "#c6443e" 

    html += "'>(" + str(data['WinPercentage']) + " win ratio)</span><br>"
    # html += "</p>"

    # html += "<p>"
    html += "<span class='special'>Best killstreak:</span><span class='right'>" + str(data['KillStreak-Best']) + "</span><br>"
    html += "<span class='special'>Most damage done in one game:</span><span class='right'>" + str(data['DamageDone-MostinGame']) + "</span><br>"
    html += "<span class='special'>Most eliminations:</span><span class='right'>" + str(data['Eliminations-MostinGame']) + "</span><br>"
    # html += "</p>"

    # html += "<p>"
    html += "<span class='special'>Average amount of deaths:</span><span class='right'>" + str(data['Deaths-Average']) + "/game</span><br>"
    html += "<span class='special'>Average damage:</span><span class='right'>" + str(data['DamageDone-Average']) + "/game</span><br>"
    html += "<span class='special'>Average number of eliminations:</span><span class='right'>" + str(data['Eliminations-Average']) + "/game</span><br>"
    # html += "</p>"

    # html += "<p>"
    html += "<span class='special'>Total play time this season:</span><span class='right'>" + time_dejsonify(str(data['TimePlayed'])) + "</span><br>"
    html += "<span class='special'>Total objective time:</span><span class='right'>" + time_dejsonify(str(data['ObjectiveTime'])) + "</span><br>"
    html += "<span class='special'>Total time spent on fire:</span><span class='right'>" + time_dejsonify(str(data['TimeSpentonFire'])) + "</span><br>"
    # html += "</p>"

    return html



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
'''