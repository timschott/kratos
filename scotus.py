import numpy as np
import os
import pandas as pd

import re

from nltk import tokenize

'''
	reads in case files, separated into paragraphs. could be configured to sweep through every sub directory.
'''
def read_data(directory):
	info = []
	for filename in os.listdir(directory):
		with open(os.path.join(directory, filename), 'r') as f: # open in readonly mode
			info.append(f.readlines())
	return info

def justice_list(filename):
	dataframe = pd.read_csv(filename, encoding= 'unicode_escape')
	justices = dataframe.justiceName.unique()
	clean_justices = []
	## do a little cleaning
	## return the last name, all caps. 
	for justice in justices:
		## John Marshall Harlan (1899–1971)
		if justice == 'JHarlan2':
			justice = 'HARLAN'
		## I have no cases after 2005 so these new-ish justices are out. (BKavanaugh is not even in this dataframe).
		elif justice in ('SAAlito', 'SSotomayor', 'EKagan', 'NMGorsuch'):
			continue
		else:
			if (is_upper(justice) == 2):
				justice = justice[1:]
			else:
				justice = justice[2:]

		clean_justices.append(justice.upper())

	return clean_justices

'''
	removes some basic dead weight from the cases
	returns a list of all the sentences from the cases in case_list
	does not respect per-justice setup. 
'''
def clean_and_normalize_data(case_list, stopwords):

	sentence_list = []
	for raw_case in case_list:
		for paragraph in raw_case:
			## numbers	
			paragraph = re.sub('[0-9]+', '', paragraph)
			## amps from xml
			paragraph = re.sub('&amp;', '', paragraph)
			## some u s print
			paragraph = re.sub('\\.US\\._|U\\. S\\.|S\\. C\\.|L\\. ed\\.|Sup\\.|', '', paragraph)
			## stars
			paragraph = re.sub('\\*(.*)\\*(.*)\\*', '', paragraph)
			## sections
			paragraph = re.sub('[§]+', '', paragraph)
			## justice names
			paragraph = re.sub('Mr. Justice [A-Z]+', '', paragraph)
			paragraph = re.sub('CHIEF JUSTICE [A-Z]+', '', paragraph)
			## no new lines 
			paragraph = re.sub('\\n|\\n\\n', '', paragraph)
			paragraph = paragraph.strip()
			## filter empties
			if (paragraph == '' or paragraph == '.'):
				continue
			## lowercase first word in each paragraph
			## "If second arg is a function, it is called for every non-overlapping occurrence of pattern.""
			## https://docs.python.org/3/library/re.html
			## so replacement is called on that match. handy!
			paragraph = re.sub('(?<!.)[A-Z][a-z]+', replacement, paragraph) 
			## lowercase whole thing
			paragraph = re.sub('[A-Z][a-z]+', '', paragraph)
			## straggling abbrevs
			paragraph = re.sub('[A-Z]', '', paragraph)
			## empty parens
			paragraph = re.sub('\\(\\)', '', paragraph)
			## citation artifacts
			paragraph = re.sub('v\\.', '', paragraph)
			## more artifications
			paragraph = re.sub('v\\.\\W{2,}|\\,\\W{2,}|\\. \\. \\.', '', paragraph)
			## et al
			paragraph = re.sub('et al\\.', '', paragraph)
			## more arficats 
			paragraph = re.sub('\\. \\.| \\. \\.  \\.', '', paragraph)
			## parties 
			paragraph = re.sub("\\s's\\s", "", paragraph)
			## floating comma
			paragraph = re.sub(' , ', '', paragraph)
			## empty quote
			paragraph = re.sub("\\s'\\s'", '', paragraph)
			## empty quote
			paragraph = re.sub("\\s'\\s", '', paragraph)
			## c. c).
			paragraph = re.sub('c\\.|c\\)\\.', '', paragraph)
			## vs
			paragraph = re.sub('\\svs\\s', '', paragraph)
			## extra spaces
			paragraph = re.sub(' +', ' ', paragraph)
			## split into sentences
			sentences = paragraph.split('.')
			for sentence in sentences:
				## filter sentences. 
				punctuation_count = len(re.findall('\\.|\\,|\\;|\\:', sentence))
				word_count = len(re.findall('[\\w-]+', sentence))
				# condition 1: if there is more punctuation in a sentence than words
				# condition 2: if there are less than 5 words in a sentence
				if (punctuation_count > word_count or word_count < 5):
					continue
				sentence = sentence.strip()
				sentence_list.append(sentence)

	return sentence_list

def is_upper(string):
	return sum(1 for c in string if c.isupper())

def replacement(match):
	return match.group(0).lower()

if __name__ == '__main__':

	## where my files live
	path = '/Users/tim/Documents/7thSemester/freeSpeech/repos/cases/text/federal/SC/1950s'
	## read data
	files = read_data(path)
	
	## stopworks from nltk
	stopwords = ["i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", 
	"yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", 
	"it", "its", "itself", "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom", "this", 
	"that", "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", 
	"does", "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", 
	"with", "about", "against", "between", "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", 
	"out", "on", "off", "over", "under", "again", "further", "th", "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", "both", 
	"each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", 
	"will", "just", "don", "should", "now"]

	## for now, not using stop words, will play around with that later. 
	# sentences = clean_and_normalize_data(files, stopwords)

	## going to implement the next set of functions at the *sentence* level
	## because that's how word2vec splits up units of study. 

	## writing a function to pull out a list of who was on the court between 50 and 05.

	justices = justice_list('voteList.csv')
	










  
	