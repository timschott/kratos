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

## sleep
from time import sleep

## mails
import yagmail

import smtplib, ssl

"""
	wapo.py - powers twitter.com/WashingtonBezos
	this application is deployed via a Google Cloud function, so 
	this file is meant as a reference.

	the difference with that file is that the execution is triggered from an HTTP request
	from the google cloud function endpoint. and it actually invokes the send_tweet function

	it runs once every hour via a cronjob.

"""


"""	
	gets environment vars from .env file
	return: keys, list filled with credentials for the News API and Twitter API 
"""
def env_vars():
	keys = []

	keys.append(os.environ.get('NEWS_API_KEY'))
	keys.append(os.environ.get('TWITTER_API_KEY'))
	keys.append(os.environ.get('TWITTER_BEARER_TOKEN'))
	keys.append(os.environ.get('TWITTER_SECRET_KEY'))
	keys.append(os.environ.get('TWITTER_ACCESS_TOKEN'))
	keys.append(os.environ.get('TWITTER_ACCESS_SECRET'))

	return keys

"""	
	initializes news api cleint
	param: key for news api -- https://newsapi.org
	return: instantiated NewsApiClient. 

"""

def init_client(key):
	if key is None:
		print ('blank news api key')
		return None

	# call and return a NewsApiClient
	return NewsApiClient(api_key = key)

"""	
	creates a twitter client using the tweepy library - https://www.tweepy.org/.
	tweepy is a just a wrapper that provides easy hooks for `send_tweets` etc.
	param: api_key - generic twitter api key
	param: secret_key - twitter secret key
	param: access_token - twitter access token
	param: access_secret - twitter access secret
	intializes twitter client
	return: client, the authorized twitter client 

"""

def init_twitter_client(api_key, secret_key, access_token, access_secret):

	if api_key is None:
		print('twitter api key is null')
		return None

	if secret_key is None:
		print ('twitter secret is null')
		return None

	if access_token is None:
		print ('twitter token is null')
		return None

	if access_secret is None:
		print ('twitter secret is null')
		return None

	auth = tweepy.OAuthHandler(api_key, secret_key)
	auth.set_access_token(access_token, access_secret)
	# create a Twitter API client with Tweepy, which is just a wrapper
	client = tweepy.API(auth)

	return client

"""
	helper method to retrieve the current date and time, and 1 hour prior to that
	that's the window of granularity we search through
	since the cron-job runs every every hour.
	the time zone doesn't matter because we are consistently using the same call
	this helps ensure we don't double-post any tweets
	return: date_list, list with both dates. 

"""

def get_dates():

	## present time
	present = datetime.now() - timedelta(hours=4)

	## 1 hours prior. 
	previous = present - timedelta(hours=1)

	x = present.strftime('%Y-%m-%d%H:%M:%S')
	y = previous.strftime('%Y-%m-%d%H:%M:%S')

	pres_formatted = x[0:10] + 'T' + x[10:18]
	prev_formatted = y[0:10] + 'T' + y[10:18]

	date_list = []
	date_list.append(pres_formatted) 
	date_list.append(prev_formatted)

	return date_list

"""
	calls the news api's everything endpoint (https://newsapi.org/docs/endpoints/everything)
	information about the api call:
	
	param: api_client 
		the initalized api client 
	param: search_phrase is what we're searching for
		to shrink down the target set, we can easily search for Bezos' (distinct) last name.
		the leading '+' means its required.
		key - q
	param: source is the entity we're pulling from
		for us, we'll use the-washington-post
		(key - sources)
	param: date_from, starting date, in this format
		2020-04-02T00:24:52
		(key - from_param)
	param: date_to, ending date, in same format as above
		(key - to)
	param: sort_type, what order to output data in
		we'll use publishedAt (most recent first)
		(key - sort_by)
	return: all_articles, the big api response

"""

def api_call(api_client, search_phrase, source, date_from, date_to,
				sort_type):

	if api_client is None:
		print ('null client')
		return None
	
	## pull in json from news api
	all_articles = api_client.get_everything(q=search_phrase,
                                      sources=source,
                                      from_param=date_from,
                                      to=date_to,
                                      sort_by=sort_type)
	if all_articles is None:
		print ('empty json from api')
		return None
	
	return all_articles

"""
	parses the response from the news api and returns the urls from matched articles
	(great banner ad for graphql -- would be nice if we could just ask for that field!)
	param: article_json, raw news api response blob
	return: article_data, dict of article titles and urls

"""

def get_article_dict(article_json):

	if article_json is None:
		print ('article json is null in #get_article_urls')
		return None

	articles = article_json["articles"]

	if articles is None:
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
	uses Beatiful Soup (b.s) to parse the DOM of a given article and extract
	the "content" (text contained in story <p> tags).
	now, the reason it's important to capture this information programmatically
	via B.S. is so we have the ability to comb through the entire article body
	which is not possible using the news API (there is a character limit in the API response).
	this tees up a forthcoming, fairly simple regex-search for the "disclaimer".
	this approach is preferable to relying on the news api's search because it's
	more transparent and i can continually update the regex should the disclaimer ever change.
	plus if i want to do things like print out the context of the disclaimer, i have all the paras.
	this method continues to grow as i observe new DOM structures across the Post's different web silos.
	param: url, link to article.
	return: article body - the relevant content one would expect to see inside body <p> tags.

"""

def get_article_text(url):

	if url is None:
		print ('broken url')
		return None

	paragraphs = []

	html = urlopen(url)
	sleep(1)

	soup = BeautifulSoup(html, 'lxml')
  
	## First part.

	teaser_div = soup.find("div", {"class": "teaser-content"})

	if teaser_div is not None:
		teaser_section = teaser_div.find("section")
		if teaser_section is not None:
			for div in teaser_section.find_all("div"):
				if div.find("p"):
					paragraphs.append(div.find("p").getText())

	## Second part.

	remainder_div = soup.find("div", {"class": "remainder-content"})

	if remainder_div is not None:
		remainder_section = remainder_div.find("section")
		if remainder_section is not None:
			for div in remainder_section.find_all("div"):
				if div.find("p"):
					paragraphs.append(div.find("p").getText())

	## Going out Guide, with amazon callout at the end.

	extra_div = soup.find("div", {"class": "extra"})

	if extra_div is not None:
		if extra_div.find("p"):
			paragraphs.append(extra_div.find("p").getText())

	## Interactives (with a "/graphics/" permalink)

	graphics_div = soup.find("div", {"class": "story relative"})
	if graphics_div is not None:
		print ('graphics')
		for para in graphics_div.find_all("p"):
			paragraphs.append(para.getText())

	## Exclude free covid updates (B.S. can't parse these)

	if len(paragraphs) == 0:
		meta_tag = soup.find("meta", {"property": "article:content_tier"})

		if meta_tag is not None:
			free = meta_tag['content']
			if free is not None:
				return None

	if paragraphs is None:
		print ('paragraphs list is blank.')
		return None

	return paragraphs

"""
	helper function to find the disclaimer given a list of paragraphs
	in general: use a regex to find the match and then return the entire capture group
	param: paragraphs, list of paragraphs for the article (usually around 35-40)
	return: string...
		positive case: ideally the clinching "disclaimer" sentence
		but in the odd case its not enclosed in parentheses,
		instead hand back the entire paragraph the disclaimer is found in. 
		negative case: return 'not found'

"""

def find_note(paragraphs):

	if paragraphs is None:
		return 'not found'

	for p in paragraphs:

		## strip punctuation
		stripped = p.translate(str.maketrans('', '', string.punctuation))
		## lowercase
		lower = stripped.lower()

		## base regex
		## fairly simple, can capture things like "Jeff Bezos owns the Washington Post" and "Jeff Bezos is the owner of the Washington Post"
		## in theory, this should *always* return a match for at least one paragraph
		## or else it means the article contains a mention of Bezos
		## but does not have the disclaimer
		x = re.search("bezos(.*)post|post(.*)bezos", lower)

		## with each potential regex, we will search against p
		## because we want the original form (casing/punctuation)
		## that way the tweet is consistent w/ what is in the text
		if x:

			## look for parenthetical usage, the most common
			## (Amazon founder Jeff Bezos owns the Washington Post.)
			## (Bezos owns the Washington Post.)
			parentheticals = re.search('\(([^()]*)\)', p)

			parens = re.findall(r'\(([^()]*)\)', p)

			for m in parens:
				if "Bezos" in m:
					return '(' + m + ')'
			
			## now look for appositive usage. 
			## Amazon's founder, Jeff Bezos, owns the Washington Post
			amazon_appositive = re.search('(Amazon[^\\.]*)(\,)(.*Bezos)(\,)(.*Post)', p)

			if amazon_appositive:
				print('appositive match')
				return amazon_appositive.group(0) + "..."

			## look for possessive usage.
			## Amazon's founder, Jeff Bezos, owns the Post
			possessive = re.search('(Amazon\’s)(.*)(Bezos)(\,)(.*)(.*Post)', p)
			if possessive:
				print('possessive match')
				return possessive.group(0) + '...'

			## look for no punc.
			## Amazon founder and chief exec. Jeff Bezos owns the Washington Post
			## Amazon founder Jeff Bezos owns the Washington Post
			no_punctuation = re.search('(Amazon .*?Bezos.*?Post)', p)
			if no_punctuation:
				print('no punctuation match')
				return no_punctuation.group(0)
			
			## look for passive voice.
			## The Post is owned by Jeff Bezos, Amazon's owner
			reverse = re.search('The(.*?)Post(.*?)Bezos(.*?)Amazon[\.\,]', p)
			
			if reverse:
				print ('reverse match')
				print (reverse.group(0))
				return reverse.group(0)

			## look for trailing-post
			## Jeff Bezos, who owns the Post
			postlast = re.search('Jeff Bezos(.*?)Post', p)

			if postlast:
				print ('post last')
				print (postlast.group(0))
				return postlast.group(0)
			else:
				## some other match, just grab the whole thing
				## Amazon founder Jeff Bezos, with an estimated net worth of $201 billion, 
				## topped the list for the fourth year in a row, Forbes said. 
				## He also owns Blue Origin, an aerospace company, and The Washington Post
				print(p)
				return p
		else:
			continue

	return 'not found'

"""
	calls #get_article_text and #find_note that scrape text out of url 
	and determine if it contains our interest string. formats the tweet
	as well

	param: article_dict, struct for article titles and urls

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
			
		if result != 'not found':

			formatted_tweet = result + " " + value
			tweet_list.append(formatted_tweet)

	return tweet_list

"""
	uses tweepy#update_status method to post new tweets to timeline

	param: tweet_list, struct for tweets
	param: client, twitter client. 
	return: tweet_count, number of successful posts. 

"""

def send_tweets(tweet_list, client):

	if tweet_list is None:
		print ('empty results list')
		return None

	if client is None:
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

	# maintain this, so we don't accidentally tweet while debugging
	debug = True

	if debug:
		news_client = init_client(s_config.api_key)

		article_json = api_call(news_client, "+Bezos", 'the-washington-post', '2021-10-24T18:05:01', '2021-10-23T18:55:00', 'publishedAt')

		article_dict = get_article_dict(article_json)

		print (article_dict)

		tweet_list = get_tweets(article_dict)

		print (tweet_list)
	else:
		# initialize News API client
		news_client = init_client(s_config.api_key)
		# get dates for interval
		dates = get_dates()
		# call news API
		article_json = api_call(news_client, "+Bezos", 'the-washington-post', dates[0], dates[1], 'publishedAt')
		# break out response and extract the mention
		article_dict = get_article_dict(article_json)
		# package into tweets
		tweet_list = get_tweets(article_dict)
		# initialize Twitter API client
		twitter_client = init_twitter_client(twitter_api_key, twitter_secret_key, twitter_access_token, twitter_access_secret)
		# publish tweets
		tweet_count = send_tweets(tweet_list, twitter_client)

"""
	this is what's called in the version of the code hosted on Google Cloud. 
	Not used in the debug version.

"""
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

		if tweet_list is None:
			return 'Could not send tweets.'

		else:
			## init twitter client
			twitter_client = init_twitter_client(twitter_api_key, twitter_secret_key, twitter_access_token, twitter_access_secret)

			## publish tweets
			send_tweets(tweet_list, twitter_client)

			return 'Sent tweets!'

"""
	alert account owner about an issue parsing the dom

	param: email_password, from .env file
	param: sender, the designated email address the mail should be from
	param: receiver, the designated email address to deliver the mail to
	param: article_dict, dict containing titles and links for articles themselves
	param: tweet_list, whatever did make it through

"""
def send_email(email_password, sender, receiver, article_dict, tweet_list):
	port = 465  
	password = email_password
	context = ssl.create_default_context()

	links = []
	for key in article_dict.keys():
		links.append(key)

	if tweet_list is None:
		return

	big_list = links + tweet_list

	concat = (';'.join())

	full = "We have a disparity: " + concat

	formatted_message = 'Subject: {}\n\n{}'.format("Cron Alert!", full)

	with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
		server.login(sender, password)
		server.sendmail(sender, receiver, formatted_message)
