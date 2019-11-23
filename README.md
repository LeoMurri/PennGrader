# PennGrader

AWS Username:
AWS Password: xuhFxwmGYGutqYBWKBKh

## What we believe.
PennGrader was built because we believe learning comes from practice and from making mistakes. We believe that for any skill to be truly mastered one must practice a lot and the key to practice is feedback, at the end of the day that is how humans learn. The issue that we have with the normal, write your code, submit it and wait 2-3 weeks (sometimes 5-6 if the TAs are slacking) is that it does not allow for quick feedback and that we believe is key to fast learning. The PennGrader was built to allow students to get instant feedback in a truly seemless experience. It was made for Jupyter Notebooks in mind but can be outfitted into a non-Jupyter python grading script. We want to be able to tell students if they did it write or wrong right away. I heard a lot of people saying "oh the students knowing if they are getting it correct or not are just going to keep trying until they get it right" as a counterargument for this approach. And let me tell you, I think that is exactly the best argument to be made for this approach of grading. A motivated student will be able to realize he is doing something wrong and then go back study more, practice more, learn more and figure out how to fix it. If a student writes an answer and has no way of checking if it is correct or not it and say is compleltely wrong, that learning opportunity is just going to go to waste. The students will realize a few weeks down the road when he gets the grade back that he did it wrong, but by then he will have 100 more assignemtns and most likely have forgetten what that question was even about. PennGrader wants to give students the opportuntiy to learn from their mistakes and helped them figure out what needs to be studied and learned. And while we are at it, we wanted to make the most seemless grading user experience grading that there is ever been (for students and even more for TAs). 

-Leo

## PennGrader Client
The PennGrader client is a python class that will be what the students will interact with.
First you need to initialize the PennGrader client as follows
Then you can call .grade() or .show_homework_score()

The PennGrader client will send the following JSON payload to the PennGrader lambda
for example:

{
 'homework_id' : 'CIS545_Fall19_HW3', 
 'student_id'  : '12345678',
 'test_case_id': '1.1',
 'answer'      : serialize(answer)
}

## DynamoDB 
The 'PennGradebook' DynamoDB table will maintain the following schema:

homework_id - Unique identifier for a specific homework in a specific class i.e. "CIS545_Fall19_HW3" would be the unique identifier of a specific homework. All homeworks will be treated as standalone projects, which means that PennGradebook has no concept of class. 

student_submission_id - Unique identifier used to represent a student submission for a specific test case. We will be using a student's 8 digit PennID for example "12345678_1_1" where 1_1 represents test case 1.1

The 'PennCheaters' DynamoDB table will be used to identify students that submitted the same exact answer 

hashed_answer

student_submission_id

## API key
If you go to API Key Service you will find the API key for PennGrader Lambda which has a max request per second set to 250 and Burst rate of 25 for safety. Main dashboard to check attacks will be via CloudWatch metrics.

## Cheating
Here at PennGrader we don't take cheating lightly. We understand that we are giving students great power by being able to submit the code while making it and as many times as they want. 
Each student answer will be serialized and then hasked into a separate cheating table. It will raise a flag for review for TAs to actually look at. 

## Glossary
Below I precisely define terms I will be using throughout this documentation to avoid any possible confusions. 

"test case" - Unique identifier for a specfic gradable component of a homework. Points in the homework will be distributed per test case i.e. question. Each test case will have an associated test case function that will take the student's answer as input and return as an output a tuple representing the student score and the maximum question score i.e. (1,4) for example. 
