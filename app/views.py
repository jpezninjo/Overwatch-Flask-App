# views.py
from __future__ import print_function

from flask import redirect, render_template, send_from_directory
from flask import request

import json
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

		return render_template("results.html", content=ow_api_call(first_name, last_name))
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

def ow_api_call(name, id_num):

    # Build the targetted API request url
    url = 'https://api.lootbox.eu/pc/us/' + name + '-' + id_num + '/profile'
    print("Fetching data from ", url,)

    # Retrieve response
    response = urllib.urlopen(url)
    print("Received response, code: " + str(response.getcode()))

    # Load response into a usable variable
    data = response.read().decode("utf-8")
    data = json.loads(data)
    data = data[data.keys()[0]]
    
    # Validate data
    no_user_error = "Found no user with the BattleTag:"
    if no_user_error in str(data):
        return "<p>" + str(data[data.keys()[0]]) + "</p>"


    html_data = """
    <style>table,td,tr,th{border: 1px solid black;}body{text-align:center}th,td{padding: 5px;text-align: left;}</style>
    <table>
    """

    html_start = ''
    html_end = '<div style="position:relative">'

    user_data = populate_user_data(data)
    data_keys = user_data.keys()
    data_keys.sort()

    html_data += str(user_data['username']) + "<br>"
    html_data += "Level "+ str(user_data['level']) + "<br>"
    if not user_data['star'] is None:
        html_data += "<img src=" + str(user_data['star']) + "><br>"
    html_data += "SR " + str(user_data['competitive_rank']) + "<br>"

    html_data += "Competitive-" + str(user_data['games_competitive_wins']) + "W " + str(user_data['games_competitive_lost']) + " L<br>"
    html_data += "Total quickplay wins: " + str(user_data['games_quick_wins'])

    # Second part
    url = "https://api.lootbox.eu/pc/us/"  + name + '-' + id_num + "/competitive/heroes"
    print("Fetching data from ", url,)

    # Retrieve response
    response = urllib.urlopen(url)
    print("Received response, code: " + str(response.getcode()))

    # Load response into a usable variable
    data = response.read().decode("utf-8")
    data = json.loads(data)

    # print(data)
    
    # Validate data
    no_user_error = "Found no user with the BattleTag:"
    if no_user_error in str(data):
        return "<p>" + str(data[data.keys()[0]]) + "</p>"

    for i in range(3):
        print(data[i])
        html_data += "<img src=" + data[i]['image'] + "><br>"
        html_data += data[i]['name'] + "<br>"
        # html_data += data[i]['playtime'] + "<br>"

    # Deprecated code
    # for keys in data_keys:
    #     # Check for img url
    #     if 'https' in str(user_data[keys]):
    #         if 'avatar' in keys:
    #             html_start += "<img src='" + user_data[keys] + "'>"
    #         else:
    #             if '<' in html_end:
    #                 html_end += '<img src=' + user_data[keys] + ' style="position: absolute; top: 0; left: 0;"/>'
    #             else:
    #                 html_end += '<img src=' + user_data[keys] + ' style="position: absolute; top: 0; left: 0;"/>'    
    #     else:
    #         html_data += '<tr><td>' + str(keys) + '</td><td>' + str(user_data[keys]) + '</td></tr>'
   
    html_data += '</table>'
    html_end += '</div>'

    html_data = html_start + html_data + html_end
    
    
    return html_data
