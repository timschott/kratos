# !/usr/local/bin/python3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json
import datetime
import re   ## only use with malformed html - this is not efficient

# secrets.
import s_config

# news api: https://newsapi.org/docs/client-libraries/python
# they give us a client. cool! 
from newsapi import NewsApiClient

# web scrape
from urllib.request import urlopen
from bs4 import BeautifulSoup

def init_client(key):
	if (key is not None):
		return NewsApiClient(api_key = key)

"""information about the api call
	
	param: api_client 
		the initalized api client 
	param: search_phrase is what we're searching for
		must be url encoded to work
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

"""

def api_call(api_client, search_phrase, source, date_from, date_to,
				sort_type):

	if (api_client is None):
		return null
	
	## json!
	all_articles = api_client.get_everything(q=search_phrase,
                                      sources=source,
                                      from_param=date_from,
                                      to=date_to,
                                      sort_by=sort_type)
	if (all_articles is not None):
		return all_articles

if __name__ == "__main__":

	news_client = init_client(s_config.api_key)
	# api call
	article_json = api_call(news_client, "trump", 'the-washington-post', '2020-03-30T00:24:52', '2020-03-31T00:24:52', 'publishedAt')
	# print (article_json)

	# testing scraping.
	url = "https://www.washingtonpost.com/opinions/2020/03/30/lot-bad-things-got-into-rescue-package-heres-list/"
	html = urlopen(url)
	soup = BeautifulSoup(html, 'lxml')
	title = soup.title
	# print(title)
	## first part 
	'''
	my_div = soup.find("div", {"class": "teaser-content"})

	my_section = my_div.find("section")

	for div in my_section.find_all("div"):
		for p in div.find("p"):
			print (p)
			'''
	## second part
	my_other_div = soup.find("div", {"class": "remainder-content"})

	my_other_section = my_other_div.find("section")

	for div in my_other_section.find_all("div"):
		if (div.find("p")):
			print (div.find("p").getText());
				#print(re.sub("(\<.*?\>)", "",p)
			print ('---------------')

	## teaser-content
	## <div class="remainder-content">




