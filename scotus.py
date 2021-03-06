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

# ingest rest
import urllib.request as request
import json

'''
	reads in case files, separated into paragraphs. could be configured to sweep through every sub directory.
'''
def read_data(directory):
	info = []
	for filename in os.listdir(directory):
		with open(os.path.join(directory, filename), 'r') as f: # open in readonly mode
			info.append(f.readlines())
			break
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
		## I have no cases before 1950 or after 2005 so quite old + new-ish justices are out. (BKavanaugh is not even in this dataframe).
		elif justice in ('FMurphy', 'WBRutledge', 'JGRoberts', 'SAAlito', 'SSotomayor', 'EKagan', 'NMGorsuch'):
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
	respects a per justice setup (refactor.)
	todo - why is this chopping off the first word of each sentence????
	probably the last outstanding thing i care about. 
	e.g.
	# I mean, if you're watering it down to say that the only reason it's okay 
	is it sends nothing but a secular message, I can't agree with you.
	# gets sent to
	## mean, if youre watering it down to say that the only reason it okay is 
	## it sends nothing but a secular message cant agree with you
	## all capital I's are getting merced. and first letter of sentences. hm. 
'''
def clean_and_normalize_data(case_list, stopwords):

	justice_list = []
	for justice in case_list:
		justice_speak = []
		for paragraph in justice:
			## this really annoying citation
			paragraph = re.sub('L\\.Ed\\.2d', '', paragraph)
			paragraph = re.sub('[0-9]+', '', paragraph)
			## amps from xml
			paragraph = re.sub('&amp;', '', paragraph)
			## some u s print
			paragraph = re.sub('U\\.S\\.|\\.US\\._|U\\. S\\.|S\\. C\\.|L\\. ed\\.|Sup\\.|U\\.S\\.C\\.|S\\.Ct\\.|L\\.Ed\\.|e\\.g\\.|v\\.|i\\.e\\.', '', paragraph)
			## stars
			paragraph = re.sub('\\*(.*)\\*(.*)\\*', '', paragraph)
			## sections
			paragraph = re.sub('[§]+', '', paragraph)
			## quotes longer than three words, out of here. 
			paragraph = quote_kill(paragraph, "double")
			## also when they're enclosed with single ticks. 
			paragraph = quote_kill(paragraph, "single")
			## justice names
			paragraph = re.sub('Mr. Justice [A-Z]+', '', paragraph)
			paragraph = re.sub('CHIEF JUSTICE [A-Z]+', '', paragraph)
			## case jargon like Court to court
			paragraph = re.sub("I'm", "im", paragraph)
			paragraph = re.sub("Co\\.", "Co", paragraph)
			paragraph = re.sub("Ltd\\.", "Ltd", paragraph)
			paragraph = re.sub("Inc\\.", "Inc", paragraph)
			paragraph = re.sub("\bI\b|I\b", "i", paragraph)
			paragraph = re.sub('Court', 'court', paragraph)
			paragraph = re.sub('Amendment', "amendment", paragraph)
			paragraph = re.sub('State', "state", paragraph)
			paragraph = re.sub('President', "president", paragraph)
			paragraph = re.sub('Secretary', "secretary", paragraph)
			paragraph = re.sub('State', "state", paragraph)
			paragraph = re.sub('Government', "government", paragraph)
			paragraph = re.sub('Constitution', "constitution", paragraph)
			paragraph = re.sub('Law', "law", paragraph)
			paragraph = re.sub('Act', "act", paragraph)
			paragraph = re.sub('Clause', "clause", paragraph)
			paragraph = re.sub('Amendment', "amendment", paragraph)
			paragraph = re.sub("Supra|supra", "", paragraph)
			paragraph = re.sub("at -", "", paragraph)
			paragraph = re.sub("Ibid", "", paragraph)
			paragraph = re.sub("\bit'\b", "it's", paragraph)
			paragraph = re.sub("\\(T\\)he", "The", paragraph)
			paragraph = re.sub("-,", "", paragraph)

			## ordinals
			paragraph = re.sub('First', "first", paragraph)
			paragraph = re.sub('Second', "second", paragraph)
			paragraph = re.sub('Third', "third", paragraph)
			paragraph = re.sub('Fourth', "fourth", paragraph)
			paragraph = re.sub('Fifth', "fifth", paragraph)
			paragraph = re.sub('Sixth', "sixth", paragraph)
			paragraph = re.sub('Seventh', "sevent", paragraph)
			paragraph = re.sub('Eight', "eight", paragraph)
			paragraph = re.sub('Ninth', "ninth", paragraph)
			paragraph = re.sub('Tenth', "tenth", paragraph)
			paragraph = re.sub('Eleventh', "eleventh", paragraph)
			paragraph = re.sub('Twelfth', "twelfth", paragraph)
			paragraph = re.sub('Thirteenth', "thirteenth", paragraph)
			paragraph = re.sub('Fourteenth', "fourteenth", paragraph)
			paragraph = re.sub('Fifteenth', "fifteenth", paragraph)
			paragraph = re.sub('Sixteenth', "sixteenth", paragraph)
			paragraph = re.sub('Seventeenth', "seventeeth", paragraph)
			paragraph = re.sub('Eighteenth', "eighteenth", paragraph)
			paragraph = re.sub('Nineteeth', "Nineteeth", paragraph)
			paragraph = re.sub('Twentieth', "twentieth", paragraph)
			paragraph = re.sub('Twenty-First', "twenty-first", paragraph)
			paragraph = re.sub('Twenty-Second', "twenty-second", paragraph)
			paragraph = re.sub('Twenty-Third', "twenty-third", paragraph)
			paragraph = re.sub('Twenty-Fourth', "twenty-fourth", paragraph)
			paragraph = re.sub('Twenty-Fifth', "twenty-fifth", paragraph)
			paragraph = re.sub('Twenty-Sixth', "twenty-sixth", paragraph)
			paragraph = re.sub('Twenty-Seventh', "twenty-seventh", paragraph)

			## ordinals
			## paragraph = re.sub("FIRST, SECOND, THIRD, FOURTH, FIFTH, SIXTH, SEVENTH, EIGHTH, NINTH, TENTH	")
			## no new lines 
			paragraph = re.sub('\\n|\\n\\n', '', paragraph)
			paragraph = paragraph.strip()
			## filter empties
			if (paragraph == '' or paragraph == '.' or paragraph == "END_OF_OPINIONS" or len(paragraph) < 1):
				continue

			## get rid of citations.
			paragraph = re.sub('See (.*?) \\(\\)\\.', '', paragraph)
			paragraph = re.sub('See ante\\, at (.*)\\.', '', paragraph)
			paragraph = re.sub('ante, at', '', paragraph)
			## lowercase first word in each paragraph
			## "If second arg is a function, it is called for every non-overlapping occurrence of pattern.""
			## https://docs.python.org/3/library/re.html
			## so replacement is called on that match. handy!
			## use {0,} to capture I (rather than +)
			paragraph = re.sub('(?<!.)[A-Z][a-z]{0,}', replacement, paragraph) 
			## remove any uppercased leading sentence words
			## need to be more clever
			## i can remove the upper cases, after i lowercase the first word in each sentence. 
			paragraph = re.sub('(\\w{2,}|([^A-Z]))(\\.\\s+)(\\w+)', replacement_dupe, paragraph) 
			## remove extra uppers now.
			paragraph = re.sub('[A-Z][a-z]+', '', paragraph)
			## straggling abbrevs
			paragraph = re.sub('[A-Z]', '', paragraph)
			## loose quote paren
			paragraph = re.sub('\\(|\\)', '', paragraph)
			## empty parens
			paragraph = re.sub('\\(\\)', '', paragraph)
			## brackets 
			paragraph = re.sub('\\[|\\]', '', paragraph)
			## thatshall
			paragraph = re.sub("thatshall", "that shall", paragraph)
			## em dash
			paragraph = re.sub("--", "", paragraph)
			## citation artifacts
			paragraph = re.sub('v\\.', '', paragraph)
			## more artifications
			paragraph = re.sub('v\\.\\W{2,}|\\,\\W{2,}|\\. \\. \\.', ' ', paragraph)
			## et al
			paragraph = re.sub('et al\\.', '', paragraph)
			## more arficats 
			paragraph = re.sub('\\. \\.| \\. \\.  \\.', '', paragraph)
			## parties 
			paragraph = re.sub("\\s's\\s", "", paragraph)
			## floating comma
			paragraph = re.sub(' , ', '', paragraph)
			## c. c).
			paragraph = re.sub('c\\.|c\\)\\.', '', paragraph)
			## vs
			paragraph = re.sub('\\svs\\s', '', paragraph)
			## any remaining tick marks
			paragraph = re.sub("'","", paragraph)
			## extra spaces
			paragraph = re.sub(' +', ' ', paragraph)
			## extra things i'm seeing now
			paragraph = re.sub(' ; | d |-;| n | id |at at', '', paragraph)
			## extra lower case d
			paragraph = re.sub(' d ', '', paragraph)
			## split into sentences
			sentences = paragraph.split('.')
			paragraph = paragraph.replace("*", "")
			for sentence in sentences:
				## filter sentences. 
				punctuation_count = len(re.findall('\\.|\\,|\\;|\\:', sentence))
				word_count = len(re.findall('[\\w-]+', sentence))
				# condition 1: if there is more punctuation in a sentence than words
				# condition 2: if there are less than 4 words in a sentence
				if (punctuation_count > word_count or word_count < 4):
					continue
				sentence = sentence.strip()
				justice_speak.append(sentence)
			
		justice_list.append(justice_speak)

	return justice_list
 
def extract_justice_speak_from_xml(case_list, justice_dict, chief_dict):
	# list of 31 empty lists.
	justices_output = [[] for i in range(31)]
	case_count = 0
	hits = []
	for case in case_list:
		## track down what justices speak in that particular case.
		## then slide that input within the appropriate index of justices_output.
		## get the root
		root = case.getroot()

		## if this look up fails it means the case is just a denial of writ of certiorari
		if (root.attrib.get('id') not in chief_dict):
			# print('denied', root.attrib.get('id'))
			continue
		else:
			## who was chief:
			chief = chief_dict[root.attrib.get('id')]
			hits.append(root.attrib.get('id'))
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
				## otherwise, prevents tracking useless front matter e.g.
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

		case_count +=1

	print('case count', case_count)
	return justices_output, hits

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
	lowercases all of a regex match. (group0 is everything)
'''
def replacement(match):
	return match.group(0).lower()
'''
	lowercase the first word of an interior sentence
'''
def replacement_dupe(match):
	return match.group(1) + match.group(3) + " " + match.group(4).lower()

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

'''
	make a dict that has what a year a decisions' term is and what the docket # is
'''
def generate_year_and_docket_dict(case_filename, data_filename):
	text_file = open(case_filename, "r")
	cases = text_file.read().split('\n')[:-1]
	dataframe = pd.read_csv(data_filename, encoding= 'unicode_escape')

	filtered = dataframe.loc[dataframe['usCite'].isin(cases)]
	u = filtered.drop_duplicates(subset=['usCite'])

	## zip up the year and the docket
	return dict(zip(u.docket, u.term))

'''
	first API call to gather the hrefs for the transcripts per case.
	cf https://github.com/walkerdb/supreme_court_transcripts#oyez-api
'''
def get_argument_hrefs(docket_dict):
	argument_ids = []
	good_count = 0
	bad_count = 0
	## to track the cases we're also getting args for. 
	sc_citations = []
	## recall docket dict is docket : year
	oyez = 'https://api.oyez.org/cases/'
	for docket in docket_dict:

		url_docket = docket
		if len(docket.split(' '))>1:
			url_docket = '_'.join(docket.split(' '))
		url = oyez + str(docket_dict[docket]) + '/' + str(url_docket)
		with request.urlopen(url) as response:
			if response.getcode() != 200:
				continue
			else:
				source = response.read()
				data = json.loads(source)
				## analagous to instanceOf
				if isinstance(data, dict):
					## they're all the same so we really shouldn't have to fuss too much..
					## let's dig. 
					## get the sc citation
					if (data['citation'] is None or data['citation']['volume'] is None or data['citation']['page'] is None):
						bad_count+=1
						continue

					good_count +=1
					citation = data['citation']['volume'] + " U.S. " + data['citation']['page']
					sc_citations.append(citation)
					## what's annoying is that data['oral_argument_audio'] might be a list of dicts
					## or it might be a dict. need to handle both cases.
					argument_block = data['oral_argument_audio'] 
					if argument_block is not None:
						## if it's a dict grab the single URLs.
						if (isinstance(argument_block, dict)):
							argument_ids.append('href')
						## if it's a list of dicts, grab the series of URLs.
						else:
							for d in argument_block:
								argument_ids.append(d['href'])
				else:
					## should really track the cases that aren't oralized....
					bad_count +=1

				## we need to skip over api calls that don't need us useful data (aka a list of lists to start.)
	print(good_count)
	print(bad_count)
	## i think itd helpful to return a dict with the ref and the case id 
	## so then we can just loop through the keys	
	return argument_ids, sc_citations

def traverse_arguments(href_filename, justices_dict, justices_names_dict, justices_container):
	href_file = open(href_filename, "r")
	caselinks = href_file.read().split('\n')[:-1]
	## add a break so we know where to stop manipulating
	for case in justices_container:
		case.append('END_OF_OPINIONS')
	print('calling api 2')

	for link in caselinks:
		## call api
		with request.urlopen(link) as response:
			if (response.getcode() != 200):
				print('invalid url' + link)
			else:
				print ('calling ' + link)
				source = response.read()
				data = json.loads(source)
				## transcript should be non null.
				if (data['transcript'] is None):
					continue
				else:
					sections = data['transcript']['sections']
					if sections is not None:
					## for each section 
						for section in sections:
							turns = section['turns']
							if turns is not None and isinstance(turns, list):
								for turn in turns:
							## find the speaker
									if turn is not None and isinstance (turn, dict):
									
										speaker = turn['speaker']
									
										if speaker is not None:
											name = speaker['name']
											name = re.sub("'", '', name)
											name = re.sub(', Jr.', '', name).split(" ")
											## do some gentle cleanup.
 											# print(name.split(" "))
											first_name = name[0].upper()
											last_name = name[-1].upper()
											## if ginsburg - ruth 
											## dict lookup - is this a justice? have to check first + last
											## this prevents a lawyer w/ the last name of "CLARK" from masquerading as scotus justice
											## c.f. https://apps.oyez.org/player/#/burger6/oral_argument_audio/17755
											## where KISSINGER's attorney... is surnamed GINSBURG.
											## todo - test.
											if last_name in justices_dict.keys() and justices_names_dict[last_name] == first_name:
												## party time
												blocks = turn['text_blocks']
												if blocks is not None and isinstance(blocks, list):
													for block in blocks:
														speech = block['text']
														## print (last_name + ' ' + speech)
														author_value = justices_dict[last_name]
														if block['text'] not in ['(Inaudible)', '[Laughter]']:
															justices_container[author_value].append(block['text'])
														## the only thing i'm going to prevent against is 
														## (Inaudible)
														## everything else is fair game!
	return justices_container

def break_apart_justice_paragraphs(case_directory):
	info = []
	justices = []
	for filename in os.listdir(case_directory):
		if not filename.endswith('.txt'): 
			continue
		with open(os.path.join(case_directory, filename), 'r') as f: # open in readonly mode
			info.append(f.readlines())
			justices.append(re.sub('paragraphs.txt', '', filename))
	return info, justices

'''
	removes any quotes of 4 words or longer
'''
def quote_kill(string, type):
	if (type == 'double'):
		quote_pattern = re.compile(r'"(.*?)"')
	else:
		quote_pattern = re.compile(r"'(.*?)'")
	kill_dict = {}
	for m in re.finditer(quote_pattern, string):
		if (m.group(1) is not None and len(m.group(1).split(' ')) > 3):
			kill_dict[m.group(1)] = ""
	
	for i, j in kill_dict.items():
		string = string.replace(i, j)

	string = string.replace('""', '')
	string = string.replace("''", "")
	
	return string

if __name__ == '__main__':

	## where files live
	## path = '/Users/tim/Documents/7thSemester/freeSpeech/repos/cases/text/federal/SC/1950s'
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
	justices, chief_justices_dict = generate_justice_data('/Users/tim/Documents/postgrad/python_projects/kratos/justice_data/voteList.csv')
	## probably just going to manually make this other dict.
	justices_last_first = {'BURTON':'HAROLD', 'JACKSON':'ROBERT', 'DOUGLAS':'WILLIAM',
		'FRANKFURTER':'FELIX', 'REED':'STANLEY', 'BLACK':'HUGO', 'VINSON':'FRED',
		'CLARK':'TOM', 'MINTON':'SHERMAN', 'WARREN':'EARL', 'HARLAN':'MARSHALL',
		'BRENNAN':'WILLIAM', 'WHITTAKER': 'CHARLES', 'STEWART':'POTTER', 'WHITE':'BYRON',
		'GOLDBERG':'ARTHUR', 'FORTAS':'ABE', 'MARSHALL':'THURGOOD', 'BURGER':'WARREN',
		'BLACKMUN':'HARRY', 'POWELL':'LEWIS', 'REHNQUIST':'WILLIAM', 'STEVENS':'JOHN',
		'OCONNOR':'SANDRA', 'SCALIA':'ANTONIN', 'KENNEDY':'ANTHONY', 'SOUTER':'DAVID',
		'THOMAS':'CLARENCE', 'GINSBURG':'RUTH', 'BREYER':'STEPHEN'}

	## list(dict) returns the keys. 
	## print(list(chief_justices_dict)[1:10])

	## print position (key) and output (value) for every element in the dict (well, first 10)
	## print({k: chief_justices_dict[k] for k in list(chief_justices_dict)[:100]})

	## create a dict of justices i.e. ({'BURTON': 1, 'JACKSON': 2,...})
	counts = list(range(0,31))
	justices_dict = dict(zip(justices, counts))
	iv_justices_dict = {v: k for k, v in justices_dict.items()}

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
	## tiny_files = read_xml('/Users/tim/Desktop/tmp_cases')

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
	## justice_output, hits= extract_justice_speak_from_xml(xml_files, justices_dict, chief_justices_dict)

	# print(len(stuff))
	# print(len(cont))
	## write hits to a file ... 
	## in between i search and replaced in sublime to go from 501.US.663 to 501 U.S. 663, the format in the dataframe.
	# with open('case_list.txt', 'w') as f:
	# 	for item in hits:
	# 		f.write("%s\n" % item)
	
	
	## think this block still needs tweaking. (can aggregate it later, who care)
	'''
	for i in range(len(cont)):
		if (i == 1):
			for l in cont[i]:
				char_count=0
				word_count=0
				for p in l:
					print(p)
					word_count += len(p.split(' '))
					for w in p:
						char_count+=len(w)

			print('AMT', iv_justices_dict, len(cont[i]))
			## chars per opinion
			print('CPO', iv_justices_dict[i], char_count/len(cont[i]))
			## words per opinion
			print('WPO', iv_justices_dict[i], word_count/len(cont[i]))
	'''
	
	## okay, great! now, can we pull out the justice data from old oral arguments?
	## it's going to be reliably labeled, and i think it would be a helpful addition
	## to each justices word list
	## for each case we used: things of interest -> docket, term. 
	
	## API CALL 1
	## https://api.oyez.org/cases/1990/90-634
	## go to the (top level!) oral_argument_audio node.
	## should have at least one id + href pair to audio.

	## docket_dict = generate_year_and_docket_dict('/Users/tim/Documents/postgrad/python_projects/kratos/justice_data/case_list.txt', '/justice_data/voteList.csv')
	## links, transcript_cases = get_argument_hrefs(docket_dict)
	## for 30 cases, we have 54 links. so it turns out most of the cases have 2 piece arguments.
	## going to write them to a text file because this api call is expesnive 
	## also write out what cases are included in this bunch

	'''
	
	with open('/Users/tim/Documents/postgrad/python_projects/kratos/justice_data/href_list.txt', 'w') as f:
		for link in links:
			f.write("%s\n" % link)

	with open('/Users/tim/Documents/postgrad/python_projects/kratos/justice_data/transcript_case_list.txt', 'w') as f:
		for transcripted in transcript_cases:
			f.write("%s\n" % transcripted)

	'''
	
	## found a transcript for 639 cases out of 723
	## this resulted in 705 href's (some cases have "part1" and "part2")

	## API CALL 2
	## https://api.oyez.org/case_media/oral_argument_audio/20680
	## using our generated hrefs
	## top level transcript bucket.
	## for each section -> 
	## for each "turn" -> 
	## grab the speaker 
	## speaker -> name.
	## make sure they're in our list of justices! --> grab + cap last string.split(' ') portion, look up in dict
	## grab what they say
	## text blocks -> text. 
	## add to their justice list
	## keep cruising
	## need to save this 
	'''
	d_list = traverse_arguments('/justice_data/href_list.txt', justices_dict, justices_last_first, justice_output)
	
	for i in range(len(d_list)):
		justice_name = iv_justices_dict[i]
		with open('/Users/tim/Documents/postgrad/python_projects/kratos/justice_data/' + justice_name + 'paragraphs.txt', 'w') as f:
			for item in d_list[i]:
				if (isinstance (item, list)):
					f.write("%s\n" % str(re.sub("\\'s", "'s", item[0])))
				else:
					f.write("%s\n" % str(re.sub("\\'s", "'", item)))
	print('fin!')
	'''
	## this is a good start. but we need to break the paragraphs into individual sentences and do it again.
	## we can play around w/ the results of my text cleaning method from the original implementation, since
	## that's kind of where we're at with those.
	## overall, though, we have our data from cases and opinions in a stable format.
	## very good!
	'''
	speech, speakers = break_apart_justice_paragraphs('/Users/tim/Documents/postgrad/python_projects/kratos/justice_data/paragraphs/')
	## okay thanks
	test = clean_and_normalize_data(speech, None)

	## lets write this information out to a file. 
	for i in range(len(test)):
		justice_name = speakers[i]
		with open('/Users/tim/Documents/postgrad/python_projects/kratos/justice_data/sents/' + justice_name + 'sents.txt', 'w') as f:
			for item in test[i]:
				f.write("%s\n" % str(re.sub("\\'s", "'s", item)))

	print('donezo')
	'''
	## for each justices sentences, train gpt2! lol. 

	## alright, i'm back. this time, just to do only the top part w/o the api work. 

	'''

	justice_output, hits= extract_justice_speak_from_xml(xml_files, justices_dict, chief_justices_dict)
	
	for i in range(len(justice_output)):
		justice_name = iv_justices_dict[i]
		with open('/Users/tim/Documents/postgrad/python_projects/kratos/justice_data/paragraphs_just_opinions/' + justice_name + 'paragraphs_just_opinions.txt', 'w') as f:
			for item in justice_output[i]:
				if (isinstance (item, list)):
					f.write("%s\n" % str(re.sub("\\'s", "'s", item[0])))
				else:
					f.write("%s\n" % str(re.sub("\\'s", "'", item)))
	print('fin!')

	speech, speakers = break_apart_justice_paragraphs('/Users/tim/Documents/postgrad/python_projects/kratos/justice_data/paragraphs_just_opinions/')
	## okay thanks
	test = clean_and_normalize_data(speech, None)

	## lets write this information out to a file. 
	for i in range(len(test)):
		justice_name = speakers[i]
		with open('/Users/tim/Documents/postgrad/python_projects/kratos/justice_data/sents_just_opinions/' + justice_name + 'sents_just_opinions.txt', 'w') as f:
			for item in test[i]:
				f.write("%s\n" % str(re.sub("\\'s", "'s", item)))

	print('done with that')
	'''

	## it might be helpful to have them separate so ill actually do the merging on the command lines. 
	## join via unix $ cat * > merged-file





