## imports.
import s_config
import os

## twitter clent
import tweepy

## date
from datetime import datetime, date, time, timedelta

## csv
import csv

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

	start_date = datetime.utcnow() - timedelta(days=1, hours=9)
	end_date = datetime.utcnow() - timedelta(days=50)
	tweet_list = []

	for status in tweepy.Cursor(twitter_client.user_timeline, username, tweet_mode="extended").items():
		tweet = []
		if status.created_at > start_date:
			continue	
		tweet.append(status.full_text)
		tweet.append(status.retweet_count)
		tweet.append(status.favorite_count)
		tweet.append(status.id)

		text = status.full_text
		if ("https://t.co/" in text):
			tweet.append('qt')
		elif (text[0:4] == "RT @"):
			tweet.append('rt')
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

'''
	returns x number of top tweets sorted by rts and favs
'''
def aggregate_tweets(tweet_list, limit):
	if (tweet_list is None):
		return 'empty tweet list'

	sorted_list = sorted(tweet_list, key=lambda x: (x[2], x[1]), reverse=True)

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
		stats.append(id)
		agg.append('|'.join(stats))

	return agg

def search_tweets(twitter_client, query, start_date, end_date):
	tweet_list = []
	tweet_count = 0
	
	for status in tweepy.Cursor(twitter_client.search, q=query, result_type="recent",lang="en", tweet_mode="extended", since = start_date, until=end_date).items(0):
		tweet = []

		if (status.full_text[0:4] == "RT @"):
			continue

		tweet.append(status.user.screen_name)
		tweet.append(status.retweet_count)
		tweet.append(status.favorite_count)
		tweet.append(status.full_text.replace('\n', ''))
		tweet.append(str(status.created_at))

		tweet_list.append(tweet)

		tweet_count+=1
		if (tweet_count > 100):
			break

	sorted_list = sorted(tweet_list, key=lambda x: (x[2], x[1]), reverse=True)

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

	'''
	booker_tweets =read_tweets(twitter_client, '@Booker4KY')
	mcgrath_tweets =read_tweets(twitter_client, '@AmyMcGrathKY')

	mcgrath_agg = aggregate_tweets(mcgrath_tweets, 5)
	booker_agg = aggregate_tweets(booker_tweets, 5)

	print(mcgrath_agg[1])
	'''

	## can we look at search results and see who is hot. 
	start_date = '2020-06-21'
	end_date = '2020-06-22'

	booker_dossier = search_tweets(twitter_client, "charles booker|Charles Booker", start_date, end_date)
	write_csv(booker_dossier, 'bookertest')


