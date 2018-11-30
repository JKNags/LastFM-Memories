import config
import sys
import requests
import datetime
from datetime import datetime as dt_utc
import calendar
import json
from dateutil import tz

# Ensure api key is set
if config.config['api_key'] == '':
	print 'Config api key must be set'
	sys.exit()

# Get username
if len(sys.argv) > 1:
    username = sys.argv[1]
elif config.config['debug'] == 'True':
	username = 'JKNags'
else:
    print 'Usage: %s username' % (sys.argv[0],)
    sys.exit()

lastfm_url = 'https://ws.audioscrobbler.com/2.0/'

# Get user data
payload = {'api_key': config.config['api_key'],
			'method': 'user.getInfo',
			'user': username,
			'format': 'json'}

r = requests.get(lastfm_url, params = payload)

r_json = json.loads(r.text)['user']

user_registered_utc = r_json['registered']['unixtime']
user_registered_year = int(dt_utc.utcfromtimestamp(user_registered_utc).strftime('%Y'))

# Get song data
def output_track(song_number, limit, utc_from, utc_to):
	payload = {'api_key': config.config['api_key'], 
				'method': 'user.getRecentTracks',
				'user': username,
				'limit': limit,
				'from': utc_from,
				'to': utc_to,
				'format': 'json'}
	
	r = requests.get(lastfm_url, params = payload)

	r_json = json.loads(r.text)['recenttracks']

	for track in r_json['track']:
		print '\t', song_number,
		track_dt = None

		try:
			# Print track that is currently playing
			if (track['@attr']['nowplaying']):
				print '\t' + track['artist']['#text'] + ' ~ ' + track['name'] + '  (Now Playing)'
		except KeyError, e:
			# Print other track
			track_dt = datetime.datetime.fromtimestamp(int(track['date']['uts']), tz=utc_tz)
			track_dt = track_dt.astimezone(local_tz)

			print '\t' + track['artist']['#text'] + ' ~ ' + track['name'] + '  (' + str(track_dt.strftime('%I:%M %p')) + ')'

		song_number += 1

	# Fetch more tracks if limit reached
	if (len(r_json['track']) == limit):
		track_dt = track_dt.astimezone(utc_tz)
		output_track(song_number, limit, utc_from, calendar.timegm((track_dt).utctimetuple()))

# Global Variables
utc_tz = tz.tzutc()
local_tz = tz.tzlocal()
year = datetime.datetime.now().year
month = datetime.datetime.now().month
day = datetime.datetime.now().day
dt_today = datetime.datetime(year, month, day)
dt_today = dt_today.replace(tzinfo=local_tz)
dt_tomorrow = datetime.datetime(year, month, day + 1)
dt_tomorrow = dt_tomorrow.replace(tzinfo=local_tz)
utc_today = calendar.timegm((dt_today).utctimetuple())
utc_tomorrow = calendar.timegm((dt_tomorrow).utctimetuple())
current_year = dt_today.year
limit = 20
print dt_today.year,dt_today.month,dt_today.day

while (current_year >= user_registered_year):

	print 'Year: ', current_year

	output_track(1, limit, utc_today, utc_tomorrow)

	# Increment utc by a year, accounting for leap years
	utc_today -= 31622400 if (current_year % 4 == 0) else 31536000
	utc_tomorrow -= 31622400 if (current_year % 4 == 0) else 31536000
	current_year -= 1
