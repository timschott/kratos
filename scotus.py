# for csvs and dfs
import numpy as np
import pandas as pd

# read files 
import os

# munging
import re

# XML
import xml.etree.ElementTree as ET

# baseline for comparison. note: this function is quite useless. 
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

def read_xml(directory):
	roots = []
	for filename in os.listdir(directory):
		if not filename.endswith('.xml'): 
			continue
		fullname = os.path.join(directory, filename)
		roots.append(ET.parse(fullname))
	return roots

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
 
## weird situation -- if "CHIEF JUSTICE" is first in line... we have to know 
## who that person is at that moment in time.......
def extract_justice_speak_from_xml(case_list, justice_dict):
	# list with 33 spots. 
	justices_output = [None] * 33
	for case in case_list:
		## track down what justices speak in that particular case.
		## then slide that input within the appropriate index of justices_output.
		## get the body. 
		## body is the third child of the root. 
		root = case.getroot()
		## recall how xml works
		## <USCase id="523.US.574" date="1998-05-04">
		print('processing...', root.attrib.get('id'))
		## the tag is USCase; 
		## it has a dictionary of attributes (id & date) that have values.
		body = root.find("body")
		authors = []
		case_container = []
		for div in body:
			paragraphs = div.findall("p")
			for p in paragraphs:
				content_bucket = []
				## just in case there is some front matter e.g.
				## <p n="x">Amicus Curiae Information from page 307 intentionally omitted</p>
				if ('author' not in p.attrib.values() and 'x' in p.attrib.values()):
					continue
				## a well formed, <p n="x" type="author">
				## make sure it has a n ="x" value and type="author" value. 
				elif ('author' in p.attrib.values() and 'x' in p.attrib.values()):
					## the author ought to be the first capitalized word. 
					primary_author = re.sub('\\.|\\,|\\;|\\:', '', first_upper(p.text))
					primary_list = primary_author.split(' ')

					## if there is no entirely capitalized word, there's a formatting issue in this paragraph.	
					if (len(primary_list) > 1):
						print("something weird happpened")
						print(primary_list)

					## we have encountered a chief justice.
					if (len(primary_author) > 1 and 'THE' in primary_author):
						## todo, match making
						print("fuck")

					## base case; should be able to handle (should make sure they're in the dict.)
					else:
						if (primary_author in justice_dict):
							# authors.append(primary_author)
							content_bucket.append(primary_author)
				## ideally, run of the mill <p n="23">The text goes here.</p>
				## but could be a fake paragraph...
				## evaluates to true if it is legitimately text.
				elif conditional_helper(p.text, justice_dict):
					content_bucket.append(re.sub('\n    ', ' ', p.text))
				else:
					## try to detect if we have capital justice name first in the paragraph
					## alongside the word dissenting or concurring.
					first_fully_upper = re.sub('\\.|\\,|\\;|\\:', '', first_upper(p.text))
					possible = first_fully_upper.split(' ')
					## we have a loose justice. 
					floating_justice = possible[0]
					## search to make sure they are participating. 
					pattern = floating_justice + ', concurring' + '|' + floating_justice + ', dissenting'
					result = re.search(pattern, p.text)
					if (result):
						## we don't care what they're doing, just want to track their participation.
						content_bucket.append(floating_justice)
					else:
						print('funky.')

				if (len(content_bucket) > 0):
					case_container.append(content_bucket)

		## need to tweak this, but good POC.
		## then we do some look up stuff once we have content bucket. 
		## for i in content:
		## if all caps, find that in the dict and pop into the big list of lists, ... 
		break

	return case_container

def is_upper(string):
	return sum(1 for c in string if c.isupper())

def first_upper(string):
	return next((word for word in string.split() if word.isupper()), string)

def replacement(match):
	return match.group(0).lower()

def conditional_helper(string, justice_dict):
	first_fully_upper = re.sub('\\.|\\,|\\;|\\:', '', first_upper(string))
	## we don't care if it's a random capitalized letter like A
	## or some abbreviation like U.S.A.
	## or if it is a normal sentence.
	if (len(first_fully_upper) == 1 or len(first_fully_upper.split(' ')) > 1 or first_fully_upper.split(' ')[0] not in justice_dict):
		return True

if __name__ == '__main__':

	## where my files live
	path = '/Users/tim/Documents/7thSemester/freeSpeech/repos/cases/text/federal/SC/1950s'
	## read data
	## files = read_data(path)
	
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
	## create a dict of this i.e. ({'BURTON': 1, 'JACKSON': 2,...})
	counts = list(range(1,34))
	justices_dict = dict(zip(justices, counts))
	xml_path = '/Users/tim/Documents/7thSemester/freeSpeech/repos/cases/xml/federal/SC/1950s'
	
	## root objects. 
	xml_files = read_xml(xml_path)

	stuff= extract_justice_speak_from_xml(xml_files, justices_dict)

	for s in stuff:
		print(stuff)
	## ['ginsburg', 'para1', 'para2'; 'other guy', 'para3', 'para4']

	## so now how can we tell the boundaries? 

	## write a function to treat each justice as a novel; fill up w/ their dictums. 
	## the .txt files don't have any author data baked in, but the xml does.
	## any text in the <body> that's contained in an author tag. 
	## <p n="x" type="author">Justice STEVENS delivered the opinion of the Court.</p>
	## <p n="x" type="author">Justice KENNEDY, concurring.</p>
	## <p n="x" type="author">Chief Justice REHNQUIST, with whom Justice O'CONNOR joins, dissenting.</p>
	## if justices join, throw them out. (ie keep first name to appear in the list). 
	## end goal of this will be a list of lists, each spot containing one justice.
	## i don't think the association of what case it is matters....
	## except for perhaps verification? but for the most part, having them just
	## by what documents they contributed to should be enough.
	## could very easily do tf-idf, things like that on this data prior to
	## running it through an advanced pipeilne. 













  
	