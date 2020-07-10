import numpy as np
import os
import pandas as pd

import re

from nltk import tokenize

'''
	reads in case files. could be configured to sweep through every sub directory.
'''
def read_data(directory):
	info = []
	for filename in os.listdir(directory):
		with open(os.path.join(directory, filename), 'r') as f: # open in readonly mode
			info.append(f.read())
	return info

'''
	removes some basic dead weight from the cases
	and split it into a list of lists case = list of its sentneces. 
'''
def clean_and_normalize_data(case_list, stopwords):

	cleaned_cases = []
	for case in case_list:
		## remove stuff
		case = re.sub('[0-9]+', '', case)
		case = re.sub('&amp;', '', case)
		case = re.sub('\\.US\\._', '', case)
		case = re.sub('\\*(.*)\\*(.*)\\*', '', case)
		case = re.sub('[§]+', '', case)
		case = re.sub('Mr. Justice [A-Z]+', '', case)
		case = re.sub('CHIEF JUSTICE [A-Z]+', '', case)
		case = re.sub('\n\n', '', case)

		case = case.strip()

		# split into sentences 
		sentences = tokenize.sent_tokenize(case)
		new_sents = []

		for sent in sentences:
			for start in re.findall('(?<!.\s)[A-Z][a-z]+', sent):
				# lower case the first word of each sentence
				s = sent.replace(start, start.lower())
				# then remove proper nouns
				s = re.sub('[A-Z][a-z]+', '', s)
				# and straggling abbrev's.
				s = re.sub('[A-Z]', '', s)
				punc = len(re.findall('\.|\,|\;|\:', s))
				w = len(re.findall('[\w-]+', s))
				# condition 1: if there is more punctuation in a sentence than words
				# condition 2: if there are less than 5 words in a sentence
				if (punc > w or w < 5):
					continue
				# remove punctuation
				s = re.sub('\.|\,|\;|\:', '', s)
				# get rid of extra spaces between words
				s = ' '.join(s.split())
				# split up the sentence
				split_sentence = s.split()
				# remove stop words 
				output = [w for w in split_sentence if not w in stopwords]
				# join the output (a list of words) back into a string
				clean_sentence = ' '.join(output)
				# add cleaned sentence to container
				new_sents.append(clean_sentence)

		# add cleaned lines to case container
		cleaned_cases.append(new_sents)

	return cleaned_cases


if __name__ == '__main__':

	# where my files live
	path = '/Users/tim/Documents/7thSemester/freeSpeech/repos/cases/text/federal/SC/1910s'
	# read data
	files = read_data(path)

	stopwords = ["i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", 
	"yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", 
	"it", "its", "itself", "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom", "this", 
	"that", "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", 
	"does", "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", 
	"with", "about", "against", "between", "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", 
	"out", "on", "off", "over", "under", "again", "further", "th", "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", "both", 
	"each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", 
	"will", "just", "don", "should", "now", '\n\n', '']
	# clean data
	cleaned_cases = clean_and_normalize_data(files, stopwords)
    
	