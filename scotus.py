# for csvs and dfs
import numpy as np
import pandas as pd

# read files 
import os

# munging
import re

# XML
import xml.etree.ElementTree as ET
from lxml.etree import fromstring

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
		# don't read in .DS_store
		if not filename.endswith('.xml'): 
			continue
		fullname = os.path.join(directory, filename)
		xmlstring = open(fullname, 'r').read()
		## get rid of interrupting characs. 
		no_italics = re.sub('<i>|<\\/i>|<b>|<\\/b>', '', xmlstring)
		no_ref = re.sub('<ref(.*)\\/>', '', no_italics)
		no_milestones = re.sub('<milestone(.*)\\/>', '', no_ref)
		no_bad_chars = re.sub('\xa0(.*)\xa0','', no_milestones)
		# no_certiorari = re.sub('<p n="x">CERTIORARI(.*)<p n="x" type="author">', '<p n="x" type="author">',no_bad_chars, flags=re.S)
		## parse it from string and turn it into a tree.
		roots.append(ET.ElementTree(ET.fromstring(no_bad_chars)))
	return roots

'''
	extracts the justices names in order of their tenure
	also returns a dict of case id's + chief justices to track who was presiding when
'''
def generate_justice_data(filename):
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
	clean_justices.append('PERCURIAM')

	## return the justice list
	## as well as a dict containing the case id (in the format 329.US.29)
	## and the chief justice at the time (uppercased)
	return clean_justices, dict(zip(dataframe.usCite
		.str.replace(' +', '', regex=True)
		.str.replace('U.S.', '.US.', regex=True),
		dataframe.chief.apply(lambda x: x.upper())))


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
 
def extract_justice_speak_from_xml(case_list, justice_dict, chief_dict):
	# list of 34 empty lists.
	justices_output = [[] for i in range(34)]
	for case in case_list:
		## track down what justices speak in that particular case.
		## then slide that input within the appropriate index of justices_output.
		## get the root
		root = case.getroot()
		print('processing...', root.attrib.get('id'))

		## if this look up fails it means the case is just a denial of writ of certiorari
		if (root.attrib.get('id') not in chief_dict):
			print('denied', root.attrib.get('id'))
		else:
			## who was chief:
			chief = chief_dict[root.attrib.get('id')]
		## recall how xml works
		## the tag is USCase; 
		## <USCase id="523.US.574" date="1998-05-04">
		## it has a dictionary of attributes (id & date) that have values.
		body = root.find("body")
		## per case container 
		case_container = []
		for div in body:
			paragraphs = div.findall("p")
			for p in list(paragraphs):				
				## case0.0: (skip an empty string)
				text = justice_sub(p.text)
				## add either the author or text of a paragraph to this list each time.
				content_bucket = []
				if text == 'break':
					break
				## skip over non numbered, non x'd paras. 
				##  <p n="">II</p>
				elif (len(p.attrib.values())==1 and 'n' in p.attrib.keys() and p.attrib['n'] == ''):
					break

				## case0.25: per curiam needs two checks... 
				## once if its well formed in the text itself (with an author tag or something. )
				elif ('PERCURIAM' in text):
					content_bucket.append('PERCURIAM')
				## another if its found outside the text in the intro.
				## prevents tracking useless front matter e.g.
				## <p n="x">Amicus Curiae Information from page 307 intentionally omitted</p>
				elif ('author' not in p.attrib.values() and 'x' in p.attrib.values() and 'opinion:majority' not in p.attrib.values()):
					if ('Opinion' == text):
						content_bucket.append('PERCURIAM')
					else:
						## perhaps there is an author with the author tag. 
						if (justice_helper(text, chief, justice_dict, content_bucket)) == 'continue':
							continue

				## case1: a well formed, <p n="x" type="author"> or <p n="19" type="author"
				## make sure it has a n ="x" value and type="author" value. 
				elif ('author' in p.attrib.values()):
					## the author ought to be the first capitalized word. 
					justice_helper(text, chief, justice_dict, content_bucket)

				## make sure we aren't losing a majority at the top of a case that lacks author tags or opinion;majority values
				## has only been an edge case for pacific gas 475 us 1
				## which incidentally has an extremely broken wikipedia page
				## https://en.wikipedia.org/wiki/Pacific_Gas_%26_Electric_Co._v._Public_Utilities_Commission
				elif ('n' in p.attrib.keys() and 'Justice' in text and 'judgment' in text):
					justice_helper(text, chief, justice_dict, content_bucket)
				## ideally, run of the mill <p n="23">The text goes here.</p>
				## but could be a fake paragraph...
				## evaluates to true if it is legitimately text.
				## case 2:
				elif conditional_helper(text, justice_dict):
					content_bucket.append(text)
				## try to detect if we have capital justice name first in the paragraph
				## alongside the word dissenting or concurring.
				## case3: 
				elif conditional_helper_2(text, justice_dict) != 'not found':
					content_bucket.append(conditional_helper_2(text, justice_dict))
				else:
					## probably just a note that they weren't participating or they had nothing to say. who care!
					continue

				if (len(content_bucket) > 0):
					case_container.append(content_bucket)

		## for i in content:
		## if all caps, find that in the dict and pop into the big list of lists, ... 
		## do stuff.
		author = ""
		for block in case_container:
			## we have reached an author marker
			if (is_upper(block[0]) == len(block[0]) or author  == ""):
				author = block[0]
			## find their spot in the array, and add the proceeding pragraphs to it
			else:
				author_value = justice_dict[author]
				justices_output[author_value].append(block)

	return case_container, justices_output

'''
	counts the number of uppercase letters in a string
'''
def is_upper(string):
	return sum(1 for c in string if c.isupper())

''' 
	returns first fully-uppercase word in a sentence, or the sentence itself if nothing found
'''
def first_upper(string):
	if (string is not None):
		return next((word for word in string.split() if word.isupper()), string)

'''
	lowercases the regex results
'''
def replacement(match):
	return match.group(0).lower()

'''
	gentle preprocessing
'''
def justice_sub(string):
	if (string is None):
		return 'break'
	else:
		## various justice subs
		mr = re.sub('MR. JUSTICE', 'Mr. Justice', string)
		ms = re.sub('MS. JUSTICE', 'Ms. Justice', mr)
		none = re.sub("JUSTICE", "Justice", ms)
		## various per curiam cases
		pc = re.sub('(.*)PER CURIAM(.*)', 'PERCURIAM', none)
		## whatever the first case she was on
		sandra = re.sub("O'CONNOR|O'Connor", "OCONNOR", pc)
		## 517.US.484
		stevens = re.sub("Stevens", "STEVENS", sandra)
		## 523.US.740
		rehnquist = re.sub("CHIEF Justice REHNQUIST|Chief Justice Rehnquist", "THE CHIEF Justice", stevens)
		## 525 US 471
		opinion = re.sub("OPINION", "Opinion", rehnquist)
		## 518 US 712
		kennedy = re.sub("Kennedy", "KENNEDY", opinion)
		## 533 US 194
		breyer = re.sub("Breyer", "BREYER", kennedy)
		## 528 US 377
		souter = re.sub("Souter", "SOUTER", breyer)
		## 530 US 567
		scalia = re.sub("Scalia", "SCALIA", souter)
		## 533 US 98
		thomas = re.sub("Thomas", "THOMAS", scalia)
		## 531 US 278
		ginsburg = re.sub("Ginsburg", "GINSBURG", thomas)
		## clean up for consistent spacing and line wraps.
		breaks = re.sub('\n', ' ', ginsburg)
		spaces = re.sub(' +', ' ', breaks)
		return spaces

## will ignore if we don't have a justice
def justice_helper(sentence, chief, justice_dict, content_bucket):
	if (sentence is None):
		return 'break'
	else:
		primary_author = re.sub('\\.|\\,|\\;|\\:', '', first_upper(sentence))
		primary_list = primary_author.split(' ')
		## if there is no entirely capitalized word, there's a formatting issue in this paragraph.	
		if (len(primary_list) > 1 or len(primary_list[0])== 1):
			return 'continue'
		## we have encountered a chief justice (when they are first).
		elif (len(primary_author) > 1 and 'THE' in primary_author):
			content_bucket.append(chief)

		## base case; should be able to handle (should make sure they're in the dict.)
		else:
			if (primary_author in justice_dict):
				content_bucket.append(primary_author)

'''
	helper method for case 2
'''
def conditional_helper(string, justice_dict):

	first_fully_upper = re.sub('\\.|\\,|\\;|\\:', '', first_upper(string))
	## we don't care if it's a random capitalized letter like A
	## or some abbreviation like U.S.A.
	## or if it is a normal sentence.
	if (len(first_fully_upper) == 1 or len(first_fully_upper.split(' ')) > 1 or first_fully_upper.split(' ')[0] not in justice_dict):
		return True

def conditional_helper_2(text, justice_dict):
	first_fully_upper = re.sub('\\.|\\,|\\;|\\:', '', first_upper(text))
	possible = first_fully_upper.split(' ')
	## we have a loose justice. 
	floating_justice = possible[0].strip()
	## search to make sure they are participating. 
	## we want to match:
	## Mr. Justice BRENNAN, with whom THE CHIEF JUSTICE, Mr. Justice BLACK and Mr. Justice DOUGLAS join, dissenting.
	## Mr. Justice MINTON, with whom Mr. Justice REED joins, dissenting.
	## but we do not want to match:
	## I disagree with Mr. Justice SCALIA's dissent.
	## Mr. Justice MINTON joins in so much of this opinion as applies to Emspak v. United  States.
	## they are quite consistent in using a gerund to identify someone that's going to start writing

	pattern = 'M(.*)Justice ' + floating_justice + ', (.*)concur|M(.*)Justice ' + floating_justice + ', (.*)dissent'
	result = re.search(pattern, text)
	if (result):
		return floating_justice
	else:
		return 'not found'

if __name__ == '__main__':

	## where files live
	path = '/Users/tim/Documents/7thSemester/freeSpeech/repos/cases/text/federal/SC/1950s'
	## read data
	## files = read_data(path)
	
	## stopworks from nltk
	## for now, not using stop words, will play around with that later. 
	'''
	stopwords = ["i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", 
	"yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", 
	"it", "its", "itself", "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom", "this", 
	"that", "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", 
	"does", "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", 
	"with", "about", "against", "between", "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", 
	"out", "on", "off", "over", "under", "again", "further", "th", "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", "both", 
	"each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", 
	"will", "just", "don", "should", "now"]
	'''

	# sentences = clean_and_normalize_data(files, stopwords)

	## going to implement the next set of functions at the *sentence* level
	## because that's how word2vec splits up units of study. 

	## writing a function to pull out a list of who was on the court between 50 and 05.
	justices, chief_justices_dict = generate_justice_data('voteList.csv')
	## list(dict) returns the keys. 
	## print(list(chief_justices_dict)[1:10])

	## print position (key) and output (value) for every element in the dict (well, first 10)
	## print({k: chief_justices_dict[k] for k in list(chief_justices_dict)[:100]})

	## create a dict of this i.e. ({'BURTON': 1, 'JACKSON': 2,...})
	counts = list(range(0,34))
	justices_dict = dict(zip(justices, counts))
	iv_justices_dict = {v: k for k, v in justices_dict.items()}
	## print(justices_dict['GINSBURG'])
	## let's go big......???
	fifties = '/Users/tim/Documents/7thSemester/freeSpeech/repos/cases/xml/federal/SC/1950s'
	sixties = '/Users/tim/Documents/7thSemester/freeSpeech/repos/cases/xml/federal/SC/1960s'	
	seventies = '/Users/tim/Documents/7thSemester/freeSpeech/repos/cases/xml/federal/SC/1970s'	
	eighties = '/Users/tim/Documents/7thSemester/freeSpeech/repos/cases/xml/federal/SC/1980s'	
	nineties = '/Users/tim/Documents/7thSemester/freeSpeech/repos/cases/xml/federal/SC/1990s'	
	two_thousands = '/Users/tim/Desktop/2000s_culled'	
	## root objects. 
	fifties_f = read_xml(fifties)
	sixties_f = read_xml(sixties)
	seventies_f = read_xml(seventies)
	eighties_f = read_xml(eighties)
	nineties_f = read_xml(nineties)
	two_thousands_f = read_xml(two_thousands)

	xml_files = fifties_f + sixties_f + seventies_f + eighties_f + nineties_f + two_thousands_f
	tiny_files = read_xml('/Users/tim/Desktop/tmp_cases')

	## write a function to treat each justice as a novel; fill up w/ their dictums. 
	## the .txt files don't have any author data baked in, but the xml does.
	## any text in the <body> that's contained between an author's tag. 
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
	## we need to reduce chief justices to only match for the cases in our corpus.
	## quick dict lookup in the method takes care of that, no culling needed
	stuff, cont= extract_justice_speak_from_xml(xml_files, justices_dict, chief_justices_dict)
	# print(len(stuff))
	# print(len(cont))
	for i in range(len(cont)):
		if (len(cont[i]) > 0):
			print(iv_justices_dict[i], len(cont[i]))











  
	