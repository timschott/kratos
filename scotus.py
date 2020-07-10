import numpy as np
import os
import pandas as pd

import re

def read_data(directory):
	info = []
	for filename in os.listdir(directory):
		with open(os.path.join(directory, filename), 'r') as f: # open in readonly mode
			info.append(f.read())
	return info

def clean_data(case_list):

	# line = re.sub(r"</?\[\d+>", "", line)
	cleaned_cases = []
	for case in case_list:
		case = re.sub('[0-9]+', '', case)
		case = re.sub('&amp;', '', case)
		case = re.sub('\\.US\\._', '', case)
		case = re.sub('\\*(.*)\\*(.*)\\*', '', case)
		case = re.sub('[§]+', '', case)
		cleaned_cases.append(case)

	return cleaned_cases



if __name__ == '__main__':

	path = '/Users/tim/Documents/7thSemester/freeSpeech/repos/cases/text/federal/SC/1910s'
	files = read_data(path)
	cleaned_cases = clean_data(files)
	print(files[0])
	print(cleaned_cases[0])
    
	