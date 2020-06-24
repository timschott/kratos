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
	end_date = datetime.utcnow() - timedelta(days=1)
	tweet_list = []
	for status in tweepy.Cursor(twitter_client.user_timeline, username).items():
		tweet = []
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

		tweet_list.append(tweet)

	## if i really want the full text i can grab the id. 
		tweet_count+=1
		# if (tweet_count > 2):
		#	break

		if status.created_at < end_date:
			break	

	return tweet_list

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
	# mcgrath_tweets =read_tweets(twitter_client, '@AmyMcGrathKY')
	# print('mcgrath is this big of a poster ' + str(len(mcgrath_tweets)))
















