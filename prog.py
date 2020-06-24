## imports.
import s_config
import os

## twitter clent
import tweepy

## date
from datetime import datetime, date, time, timedelta

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
	client = tweepy.API(auth)

	return client

def read_tweets(twitter_client, username):

	## need to paginate. artificially? 
	tweet_count = 0

	start_date = datetime.utcnow() - timedelta(days=1, hours=9)
	end_date = datetime.utcnow() - timedelta(days=50)
	tweet_list = []

	for status in tweepy.Cursor(twitter_client.user_timeline, username).items():
		tweet = []
		if status.created_at > start_date:
			continue	
		tweet.append(status.text)
		tweet.append(status.retweet_count)
		tweet.append(status.favorite_count)
		tweet.append(status.id)

		text = status.text
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
		id = str(tweet[3])
		rt = str(tweet[1])
		fav = str(tweet[2])
		date = str(tweet[5])
		stats = []
		stats.append(text)
		stats.append(rt)
		stats.append(fav)
		stats.append(date)
		stats.append(id)
		agg.append('|'.join(stats))

	return agg

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

	sorted_mcgrath_list = sorted(mcgrath_tweets, key=lambda x: (x[2], x[1]), reverse=True)
	sorted_booker_list = sorted(booker_tweets, key=lambda x: (x[2], x[1]), reverse=True)

	print(len(sorted_mcgrath_list))
	print(len(sorted_booker_list))

	print("amy's tweets.")
	mcgrath_agg = aggregate_tweets(mcgrath_tweets, 5)
	booker_agg = aggregate_tweets(booker_tweets, 5)

	print(mcgrath_agg[1])

	## can we get the full text of a tweet, using beautiful soup and just requesting that ID?

	## can we look at search results and see who is hot. 

	

