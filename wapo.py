# !/usr/local/bin/python3
import json
import re 
import string

# imports.
import s_config

#news api
from newsapi import NewsApiClient

# web scrape
from urllib.request import urlopen
from bs4 import BeautifulSoup

# twitter clent
import tweepy

def init_client(key):
	if (key is None):
		print ('blank news api key')
		return null
	return NewsApiClient(api_key = key)

def init_twitter_client(api_key, secret_key, access_token, access_secret):

	if (api_key is None):
		print('twitter api key is null')
		return null

	if (secret_key is None):
		print ('twitter secret is null')
		return null

	if (access_token is None):
		print ('twitter token is null')
		return null

	if (access_secret is None):
		print ('twitter secret is null')
		return null

	auth = tweepy.OAuthHandler(api_key, secret_key)
	auth.set_access_token(access_token, access_secret)
	client = tweepy.API(auth)
	
	return client

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
		return null
	
	## json!
	all_articles = api_client.get_everything(q=search_phrase,
                                      sources=source,
                                      from_param=date_from,
                                      to=date_to,
                                      sort_by=sort_type)
	if (all_articles is None):
		print ('empty json from api')
		return null
	
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
		return null

	articles = article_json["articles"]

	if (articles is None):
		print ('malformed json')
		return null

	titles = []
	urls = []

	for article in articles:
		titles.append(article["title"])
		urls.append(article["url"])

	article_data = dict(zip(titles, urls))

	return article_data

"""
	param: url, article.
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
		return null

	paragraphs = []

	html = urlopen(url)
	soup = BeautifulSoup(html, 'lxml')

	## First part.

	teaser_div = soup.find("div", {"class": "teaser-content"})
	teaser_section = teaser_div.find("section")

	if (teaser_section is None):
		print ('teaser section is null')
		return null

	for div in teaser_section.find_all("div"):
		if (div.find("p")):
			paragraphs.append(div.find("p").getText())

	## Second part.

	remainder_div = soup.find("div", {"class": "remainder-content"})
	remainder_section = remainder_div.find("section")

	# print (remainder_section)

	if (remainder_section is None):
		print ('remainder section is null')
		return null

	for div in remainder_section.find_all("div"):
		if (div.find("p")):
			paragraphs.append(div.find("p").getText())

	if (paragraphs is None):
		print ('paragraphs list is blank.')
		return null

	return paragraphs

# (Disclosure: Amazon chief executive Jeff Bezos owns The Washington Post.)
# (Amazon founder and chief executive Jeff Bezos owns The Washington Post.)
# (Amazon’s founder, Jeff Bezos, owns The Washington Post.)

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
		return null

	## strip punctuation and lowercase.
	for p in paragraphs:

		stripped = p.translate(str.maketrans('', '', string.punctuation))
		lower = stripped.lower()

		## fairly simple regex.
		x = re.search("jeff bezos owns the washington post", lower)

		## its almost always between ()'s, so search for whatevers in that.
		if (x):
			context = re.search('\(.*?Bezos.*?\)', p)
			if (context):
				return context.group(0)
			else:
				return p
		else:
			continue

	return 'not found'

if __name__ == "__main__":

	# initialize client 
	news_client = init_client(s_config.api_key)

	# api call
	article_json = api_call(news_client, "+Bezos", 'the-washington-post', '2020-03-30T00:24:52', '2020-03-31T00:24:52', 'publishedAt')
	# print (article_json)

	# article_dict = get_article_dict(article_json)

	# for every url
	# results = []
	# for url in article_dict.values():
		# paragraphs of that article
	#	paras = get_article_text(url)
	#	results.append(find_note(paras))

	# for every result, check and tweet (or not)

	twitter_client = init_twitter_client(s_config.twitter_api_key, s_config.twitter_secret_key, s_config.twitter_access_token, s_config.twitter_access_secret)
	tweet = twitter_client.update_status("Flight test")

	# api.destroy_status(tweet.id_str)


