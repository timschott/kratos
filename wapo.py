# !/usr/local/bin/python3

## parse blob
import json

## regex
import re 
import string

## imports.
import s_config

##news api
from newsapi import NewsApiClient

## scrape
from urllib.request import urlopen
from bs4 import BeautifulSoup

## twitter clent
import tweepy

## date 
from datetime import date, datetime, timedelta

## schleep
from time import sleep

def init_client(key):
	if (key is None):
		print ('blank news api key')
		return None
	return NewsApiClient(api_key = key)

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

"""
	get todays date and yesterdays date, fomratted for the api call.
	todays date, at 6:00
	yesterdays date, at 6:01
	return list with both dates. 

"""

def get_dates():

	today = datetime.today().strftime('%Y-%m-%d')
	yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')

	date_list = []
	date_list.append(today + 'T18:00:00') 
	date_list.append(yesterday + 'T18:01:00')

	return date_list

"""
	information about the api call
	
	param: api_client 
		the initalized api client 
	param: search_phrase is what we're searching for
		to shrink down the target set, we can easily search for Bezos' (distinct) last name.
		the leading '+' means its required.
		key - q
	param: source is the entity we're pulling from
		for us, we'll use the-washington-post
		key - sources
	param: date_from, starting date, in this format
		2020-04-02T00:24:52
		key - from_param
	param: date_to, ending dat, in same format as above
		key - to
	param: sort_type, what order to output data in
		we'll use publishedAt (most recent first)
		key - sort_by
	client method we'll hit is
	newsapi#get_everything
	return: all_articles, the big api response

"""

def api_call(api_client, search_phrase, source, date_from, date_to,
				sort_type):

	if (api_client is None):
		print ('null client')
		return None
	
	## json!
	all_articles = api_client.get_everything(q=search_phrase,
                                      sources=source,
                                      from_param=date_from,
                                      to=date_to,
                                      sort_by=sort_type)
	if (all_articles is None):
		print ('empty json from api')
		return None
	
	return all_articles

"""
	param: article_json, raw news api response blob
		will return just the urls from these articles
		(graphql would be great, here)
	return: article_data, dict of article titles and urls

"""

def get_article_dict(article_json):

	if (article_json is None):
		print ('article json is null in #get_article_urls')
		return None

	articles = article_json["articles"]

	if (articles is None):
		print ('malformed json')
		return None

	titles = []
	urls = []

	for article in articles:
		titles.append(article["title"])
		urls.append(article["url"])

	article_data = dict(zip(titles, urls))

	return article_data

"""
	param: url, link to article.
	return: article body - everything inside the body p tags.
		now, the reason its important to capture this information programmatically
		via bs4 is so we have the ability to comb through the entire article body
		which is not possible using the news API (there is a character limit in the API response)
		this tees up a forthcoming, simple regex for the "disclaimer".
		i think this approach is preferable to relying on the news api's search because its
		more transparent and i can continually update the regex should the disclaimer ever change.
		plus if i want to do things like print out the context of the disclaimer, i have all the paras.

"""

def get_article_text(url):

	if (url is None):
		print ('broken url')
		return None

	paragraphs = []

	html = urlopen(url)
	soup = BeautifulSoup(html, 'lxml')

	## First part.

	teaser_div = soup.find("div", {"class": "teaser-content"})

	if (teaser_div is None):
		print('teaser div is null')
		return None

	teaser_section = teaser_div.find("section")

	if (teaser_section is None):
		print ('teaser section is null')
		return None

	for div in teaser_section.find_all("div"):
		if (div.find("p")):
			paragraphs.append(div.find("p").getText())

	## Second part.

	remainder_div = soup.find("div", {"class": "remainder-content"})

	if (remainder_div is None):
		print('remain_div is null')
		return None

	remainder_section = remainder_div.find("section")

	# print (remainder_section)

	if (remainder_section is None):
		print ('remainder section is null')
		return None

	for div in remainder_section.find_all("div"):
		if (div.find("p")):
			paragraphs.append(div.find("p").getText())

	if (paragraphs is None):
		print ('paragraphs list is blank.')
		return None

	return paragraphs

"""
	param: paragraphs, list of paragraphs for the article (usually around 35-40)
	return: string, 
		positive case: ideally the clinching "disclaimer", but in the odd case its not enclosed in parentheses, the paragraph
		the disclaimer is found in. 
		negative case: 'not found'

"""

def find_note(paragraphs):

	if (paragraphs is None):
		return ('blank paragraphs supplied to #find_note')
		return None

	## strip punctuation and lowercase.
	for p in paragraphs:

		stripped = p.translate(str.maketrans('', '', string.punctuation))
		lower = stripped.lower()

		## fairly simple regex.
		x = re.search("jeff bezos(.*)own(.*)washington post", lower)

		## its almost always between ()'s, so search for whatevers in that.
		## search original paragraphs, we want the original form
		if (x):
			context = re.search('\(.*?Bezos.*?\)', p)
			if (context):
				return context.group(0)
			else:
				return p
		else:
			continue

	return 'not found'

"""
	param: article_dict, struct for article titles and urls
		calls #get_article_text and #find_note, that scrape text out of url and determine if it contains our interest string.
		formats the tweet
	return: tweet_list, list of tweets to send

"""

def get_tweets(article_dict):

	if (article_dict is None):
		print('empty article dict')
		return None

	tweet_list = []

	for key, value in article_dict.items():

		# paragraphs of that article
		paras = get_article_text(value)

		result = find_note(paras)
			
		if (result != 'not found'):

			formatted_tweet = result + value
			tweet_list.append(formatted_tweet)

	return tweet_list

"""
	param: tweet_list, struct for tweets
	param: client, twitter client. 
		uses tweepy#update_status method to post new tweets to timeline
	return: tweet_count, number of successful posts. 

"""

def send_tweets(tweet_list, client):

	if (tweet_list is None):
		print ('empty results list')
		return None

	if (client is None):
		print ('null twitter client')
		return None

	tweet_count = 0

	for tweet in tweet_list:
		# client.update_status(tweet) -- debug mode
		sleep(0.5)
		print(tweet)
		tweet_count +=1

	return tweet_count

if __name__ == "__main__":

	## initialize client 
	news_client = init_client(s_config.api_key)

	# dates = get_dates()

	## api call: happens daily.
	## article_json = api_call(news_client, "+Bezos", 'the-washington-post', dates[0], dates[1], 'publishedAt')
	
	# catch up call, the past two weeks
	article_json = api_call(news_client, "+Bezos", 'the-washington-post', '2020-03-05T20:05:01', '2020-04-02T20:05:00', 'publishedAt')

	## put article title and url into dict 
	article_dict = get_article_dict(article_json)
	
	## send through title and url to parser methods
	## return our formatted tweets. 
	tweet_list = get_tweets(article_dict)

	## init client
	twitter_client = init_twitter_client(s_config.twitter_api_key, s_config.twitter_secret_key, s_config.twitter_access_token, s_config.twitter_access_secret)
	
	num = send_tweets(tweet_list, twitter_client)

	print (num)
	