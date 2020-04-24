# !/usr/local/bin/python3

## parse blob
import json

## regex
import re 
import string

## imports.
import s_config
import os

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


def env_vars():
	keys = []

	keys.append(os.environ.get('NEWS_API_KEY'))
	keys.append(os.environ.get('TWITTER_API_KEY'))
	keys.append(os.environ.get('TWITTER_BEARER_TOKEN'))
	keys.append(os.environ.get('TWITTER_SECRET_KEY'))
	keys.append(os.environ.get('TWITTER_ACCESS_TOKEN'))
	keys.append(os.environ.get('TWITTER_ACCESS_SECRET'))

	return keys

"""	param: key for news api -- https://newsapi.org
	initializes news api cleint
	return: instantiated NewsApiClient. 

"""

def init_client(key):
	if (key is None):
		print ('blank news api key')
		return None
	return NewsApiClient(api_key = key)

"""	
	creates a twitter client using the tweepy library - https://www.tweepy.org/.
	param: api_key - generic twitter api key
	param: secret_key - twitter secret key
	param: access_token - twitter access token
	param: access_secret - twitter access secret
	intializes twitter client
	return: client, the authorized twitter client 

"""

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
	get today's date and yesterday's date, fomratted for the api call.
	(today's date, at 6:00)
	(yesterday's date, at 6:01)
	return: date_list, list with both dates. 

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
	sleep(1)

	soup = BeautifulSoup(html, 'lxml')
  
	## First part.

	teaser_div = soup.find("div", {"class": "teaser-content"})

	if (teaser_div is not None):
		teaser_section = teaser_div.find("section")
		if (teaser_section is not None):
			for div in teaser_section.find_all("div"):
				if (div.find("p")):
					paragraphs.append(div.find("p").getText())

	## Second part.

	remainder_div = soup.find("div", {"class": "remainder-content"})

	if (remainder_div is not None):
		remainder_section = remainder_div.find("section")
		if (remainder_section is not None):
			for div in remainder_section.find_all("div"):
				if (div.find("p")):
					paragraphs.append(div.find("p").getText())

	## Going out Guide, with amazon callout at the end.

	extra_div = soup.find("div", {"class": "extra"})

	if (extra_div is not None):
		if (extra_div.find("p")):
			paragraphs.append(extra_div.find("p").getText())


	## Exclude free covid updates (BS can't parse these)

	if (len(paragraphs) == 0):
		meta_tag = soup.find("meta", {"property": "article:content_tier"})

		if (meta_tag is not None):
			free = meta_tag['content']
			if (free is not None):
				return None

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
		return 'not found'

	print('-------------------------')
	print('-------------------------')
	print('-------------------------')


	## strip punctuation and lowercase.
	for p in paragraphs:

		stripped = p.translate(str.maketrans('', '', string.punctuation))
		lower = stripped.lower()

		## fairly simple regex. can capture things like "Jeff Bezos owns the Washington Post" and "Jeff Bezos is the owner of the Washington Post"
		x = re.search("jeff bezos(.*)post", lower)

		## its almost always between ()'s, so search for whatevers in that.
		## search original paragraphs, we want the original form
		if (x):
			parentheticals = re.search('\(([^()]*)\)', p)
			parens = re.findall(r'\(([^()]*)\)', p)

			for m in parens:
				if ("Bezos" in m):
					return '(' + m + ')'
			
			amazon_appositive = re.search('(Amazon.*)(\,)(.*)(\,)', p)
			if (amazon_appositive):
				print (amazon_appositive.group(1))
				return amazon_appositive.group(1) + "..."

			else:
				## need to cut the down the parts of the paragraph after Jeff Bezos..
				## search for Amazon\’s(.*)
				no_parens = re.search('Amazon\’s(.*)', p)
				if (no_parens):
					return no_parens.group(0)
				else:
					print('this paragraph has a weird match')
					print(p)
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

			formatted_tweet = result + " " + value
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

def cloud_call(request):
	## load env vars
		key_array = env_vars()

		## news api creds
		news_api_key = key_array[0]

		## twitter creds
		twitter_api_key = key_array[1]
		twitter_secret_key = key_array[2]
		twitter_bearer_token = key_array[3]
		twitter_access_token = key_array[4]
		twitter_access_secret = key_array[5]

		## init news client
		news_client = init_client(news_api_key)

		## generate dates
		dates = get_dates()

		## hit news api for fresh article data.
		article_json = api_call(news_client, "+Bezos", 'the-washington-post', dates[0], dates[1], 'publishedAt')
	
		## put article title and url into dict 
		article_dict = get_article_dict(article_json)
	
		## send through article vals to parser methods
		tweet_list = get_tweets(article_dict)

		if (tweet_list is None):
			return 'Could not send tweets.'

		else:
			## init twitter client
			twitter_client = init_twitter_client(twitter_api_key, twitter_secret_key, twitter_access_token, twitter_access_secret)

			## publish tweets
			send_tweets(tweet_list, twitter_client)

			return 'Sent tweets!'

"""
	this application is deployed via a Google cloud function, so 
	this file is meant as a reference for the implementation. in the full
	version of the file (which I didn't commit) i actually call the #send_tweet method

	the only difference with that file is that the function is triggered from an HTTP request
	from the google cloud function endpoint

	it runs once daily via a cronjob.

"""
if __name__ == "__main__":

	debug = True

	if (debug):
		news_client = init_client(s_config.api_key)

		dates = get_dates()
		# plug in date range to debug. 
		article_json = api_call(news_client, "+Bezos", 'the-washington-post', '2020-04-22T18:05:01', '2020-04-23T18:05:00', 'publishedAt')
		
		print (article_json)

		article_dict = get_article_dict(article_json)

		print (article_dict)

		tweet_list = get_tweets(article_dict)
		for tweet in tweet_list:
			print(tweet_list)
	else: 
		print ('local!')