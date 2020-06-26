## imports.
import s_config
import os

## twitter clent
import tweepy

## date
from datetime import datetime, date, time, timedelta

## csv
import csv

## schleep
from time import sleep

import pandas as pd
import pandas.io.formats.style

def env_vars():
	keys = []

	keys.append(s_config.twitter_api_key)
	keys.append(s_config.twitter_secret_key)
	keys.append(s_config.twitter_bearer_token)
	keys.append(s_config.twitter_access_token)
	keys.append(s_config.twitter_access_secret)
	return keys

def init_twitter_client(api_key, secret_key, access_token, access_secret):

	if (api_key is None):
		print('twitter api key is null')
		return None

	if (secret_key is None):
		print ('twitter secret is null')
		return None

	if (access_token is None):
		print ('twitter token is null')
		return None

	if (access_secret is None):
		print ('twitter secret is null')
		return None

	auth = tweepy.OAuthHandler(api_key, secret_key)
	auth.set_access_token(access_token, access_secret)
	client = tweepy.API(auth, wait_on_rate_limit=True)

	return client

def read_tweets(twitter_client, username):

	## need to paginate. artificially? 
	tweet_count = 0

	start_date = datetime.utcnow() - timedelta(days=3, hours=9)
	end_date = datetime.utcnow() - timedelta(days=53, hours=9)
	tweet_list = []

	for status in tweepy.Cursor(twitter_client.user_timeline, username, tweet_mode="extended").items():
		tweet = []
		if status.created_at > start_date or status.full_text[0:4] == "RT @":
			continue	

		tweet.append(status.full_text.replace('\n', ' '))
		tweet.append(status.retweet_count)
		tweet.append(status.favorite_count)
		tweet.append(status.id)

		text = status.full_text
		if ("https://t.co/" in text):
			tweet.append('qt')
		else:
			tweet.append('nt')

		tweet.append(status.created_at)

		tweet_list.append(tweet)

		## if i really want the full text i can grab the id. 
		tweet_count+=1
		# if (tweet_count > 2):
		#	break

		if status.created_at < end_date:
			break

	return tweet_list

def write_to_html_file(df, title='', filename='out.html'):
    '''
    Write an entire dataframe to an HTML file with nice formatting.
    '''

    result = '''
<html>
<head>
<style>

    h2 {
        text-align: center;
        font-family: Helvetica, Arial, sans-serif;
    }
    table { 
        margin-left: auto;
        margin-right: auto;
    }
    table, th, td {
        border: 1px solid blue;
        border-collapse: collapse;
    }
    th, td {
        padding: 5px;
        text-align: center;
        font-family: Helvetica, Arial, sans-serif;
        font-size: 90%;
    }
    th
     {
      color: blue;
    }
    table tbody tr:hover {
        background-color: #dddddd;
    }
    .wide {
        width: 90%; 
    }

</style>
</head>
<body>
    '''
    result += '<h2> %s </h2>\n' % title
    if type(df) == pd.io.formats.style.Styler:
        result += df.render()
    else:
        result += df.to_html(classes='wide', escape=False, index=False)
    result += '''
</body>
</html>
'''
    with open(filename, 'w') as f:
        f.write(result)

    return 'done'

'''
	returns x number of top tweets sorted by rts and favs
'''
def aggregate_tweets(tweet_list, limit):
	if (tweet_list is None):
		return 'empty tweet list'

	## sorted by retweets
	sorted_list = sorted(tweet_list, key=lambda x: (x[1], x[2]), reverse=True)

	sorted_list = sorted_list[0:limit]

	agg = []

	for tweet in sorted_list:
		text = tweet[0]
		rt = str(tweet[1])
		fav = str(tweet[2])
		id = str(tweet[3])
		date = str(tweet[5])
		stats = []
		stats.append(text)
		stats.append(rt)
		stats.append(fav)
		stats.append(date)
		# stats.append(id)
		agg.append(stats)

	return agg

def search_tweets(twitter_client, query, start_date, end_date):
	tweet_list = []
	tweet_count = 1

	print ('lets search.')
	sleep(5)
	
	for status in tweepy.Cursor(twitter_client.search, q=query, result_type="recent",lang="en", tweet_mode="extended", since = start_date, until=end_date).items():
		tweet = []

		## some sort of cutoff to make this go faster
		# if (status.retweet_count < 10 or status.favorite_count < 10):
		# 	continue

		## don't care about retweets
		if (status.full_text[0:4] == "RT @"):
			continue

		print('processed ' + str(tweet_count) + ' tweets')

		tweet.append(status.user.screen_name)
		tweet.append(status.retweet_count)
		tweet.append(status.favorite_count)
		## replace new lines, not really important
		tweet.append(status.full_text.replace('\n', ' '))
		tweet.append(str(status.created_at))
		tweet.append(status.id)

		tweet_list.append(tweet)

		tweet_count+=1

		if (tweet_count > 10000):
			break
		sleep(5)

	# sort by retweets
	sorted_list = sorted(tweet_list, key=lambda x: (x[1], x[2]), reverse=True)

	print('processed this many tweets', tweet_count)
	
	return sorted_list

def write_csv(tweets, filename):

	with open(filename+'.csv','w') as result_file:
		wr = csv.writer(result_file, dialect='excel')
		for item in tweets:
			wr.writerow([item[0], item[1], item[2], item[3], item[4]])
	return 'wrote csv'

if __name__ == "__main__":

	key_array = env_vars()

	## twitter creds
	twitter_api_key = key_array[0]
	twitter_secret_key = key_array[1]
	twitter_bearer_token = key_array[2]
	twitter_access_token = key_array[3]
	twitter_access_secret = key_array[4]

	twitter_client = init_twitter_client(twitter_api_key, twitter_secret_key, twitter_access_token, twitter_access_secret)

	## use `user_timeline` and wild out. 

	# print('booker is this big of a poster ' + str(len(booker_tweets)))
	
	booker_tweets =read_tweets(twitter_client, '@Booker4KY')
	mcgrath_tweets =read_tweets(twitter_client, '@AmyMcGrathKY')

	booker_agg = aggregate_tweets(booker_tweets, 10)
	mcgrath_agg = aggregate_tweets(mcgrath_tweets, 10)

	bowman_tweets =read_tweets(twitter_client, '@JamaalBowmanNY')
	engel_tweets =read_tweets(twitter_client, '@RepEliotEngel')

	bowman_agg = aggregate_tweets(bowman_tweets, 10)
	engel_agg = aggregate_tweets(engel_tweets, 10)

	columns = ['text', 'retweets', 'favorites', 'date']

	booker_df = pd.DataFrame(booker_agg, columns=columns)
	mcgrath_df = pd.DataFrame(mcgrath_agg, columns=columns)

	bowman_df = pd.DataFrame(bowman_agg, columns=columns)
	engel_df = pd.DataFrame(engel_agg, columns=columns)

	## try this html func. 

	write_to_html_file(bowman_df, "Jamaal Bowman's Top 10 Tweets", 'bowman.html')
	write_to_html_file(engel_df, "Eliot Engel's Top 10 Tweets", 'engel.html')

	write_to_html_file(booker_df, "Charles Booker's Top 10 Tweets", 'booker.html')
	write_to_html_file(mcgrath_df, "Amy McGrath's Top 10 Tweets", 'mcgrath.html')

	
	## make a data frame?
	

	## can we look at search results and see who is hot. 

	'''
	start_date = '2020-06-19'
	end_date = '2020-06-20'

	## this search picks up a quote tweet of a
	## news article that mentions "Booker" in the lede caption 
	## eg https://twitter.com/BlackBernieBabe/status/1274849294101680129?s=20
	## this is very helpful because it pulls in a very germane tweet
	## that doesn't directly mention Booker. 
	booker_dossier = search_tweets(twitter_client, "charles booker|Charles Booker", start_date, end_date)
	write_csv(booker_dossier, 'booker_buzz_19and20')

	mcgrath_dossier = search_tweets(twitter_client, "amy mcgrath|Amy McGrath", start_date, end_date)
	write_csv(mcgrath_dossier, 'mcgrath_buzz19and20')
	'''

