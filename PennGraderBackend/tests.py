def test_case_0_1(answer):
	'''
	This is an example of what a test case should look like.  
	You need to take in a single object, which can be anything
	you want, i.e. a list, a function, a dataframe, a puppy, 
	you get the point. The test case function will then need 
	to return a tuple containing the student score and the
    maximum score for this specific test case. See example below:
	'''
	student_score = 0
	max_score     = 2

	if answer == 'Correct answer':
		student_score = 2
	if answer == 'Not so correct answer':
		student_score = 1
	else:
		student_score = 0

	return (student_score, max_score)


def grade(test_case_id, answer):
	# Fill in configuration parameters
	COURSE    = ''  # i.e CIS545
	SEMESTER  = ''  # i.e Fall, Spring or Summer
	HW_NUMBER = ''  # i.e. 1, 2, 3,...

	# Import all libraries you need for grading here
	import numpy  as np
	
	# Define a test case id to function dictionary
	test_cases = {
		'0.1' : test_case_0_1
	}

	# Grade question
	return test_cases[test_case_id](answer)







