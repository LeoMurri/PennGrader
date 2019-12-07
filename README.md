# PennGrader
Welcome to the PennGrader!

Here at PennGrader we believe that learning comes from lots of practice...and from making lots of mistakes. 

After many years as a student I found myself very frustrated in the following homework timeline: struggle on a homework assignment for weeks, submit something that may or may not be right and then wait a few more weeks to receive any type of feedback, at which point I had forgotten all about the homework. After many years as a TA, I also found myself very frustrated with the common auto-grading tools, the hours and hours of manual grading and the onslaught of re-grade requests that came thereafter.

From these frustrations, the PennGrader was born!

The PennGrader was built to allow students to get instant feedback and many opportunities for re-submission. After all, programming is about making mistakes and learning from feedback! Moreover, we wanted to allow TAs and Instructors to write their homework in any way they pleased, without having to worry about the structure of a specific auto-grader. The examples below are done using Jupyter Notebooks which is the most common use case, but you can use this for normal Python homework as well. 

Here is what a student sees in his Homework Notebook. All a student has to do is write her solution and run the auto-grading cell.

![Sample Question](https://penngrader-wiki.s3.amazonaws.com/sample_question.gif)

Through the magic of AWS Lambdas, the student's answer (in this case the `addition_function` object) is packaged and shipped to the backend where it is checked against the teacher-defined test case. Finally, a score is returned. All students' scores are saved in the backend and are easily accessible to the instructors. If at first they don't succeed, they can  learn from their mistakes and try again.  (Yes, if you'd like, can set a maximum number of daily submissions to incentivize students to start early). This "grader" function can easily be used from any Jupyter noteboook (even Google Colab), all you have to do is to `pip install penngrader`. See template Colab notebooks below.

Ok, ok, you might be saying to yourself: "That looks easy enough, but what about us TAs, we want something that simple too!" Well, look no further. The TAs/Instructors' experience is just as seamless. All TAs will share a __Teacher_Backend__ notebook, which contains all the test case functions. The logic of how testing is done is simple: whatever Python object gets passed through the `answer` field in the `grade(...)` function (see above) will be the input to the test case function (see below). In the above example, `addition_function` is passed as the answer to a test case named `"test_case_1"`. Therefore, the TAs will need to write a `test_case_1(answer)` function in the __Teacher_Backend__ notebook, as follows:

![Sample Question](https://penngrader-wiki.s3.amazonaws.com/sample_test.gif)

As you can see, this function tests that `answer(1,2) == 3` i.e. `addition_function(1,2) == 3`. The test must then return a integer tuple `(student_score, max_score)`, which is what will be displayed to the student. As you can see this type of test function gives the Instructor complete flexibility on what to test and how much partial credit to give. Remember that the answer that gets passed to the test case could be anything... a function, a class, a dataframe, a list, a picture... anything! The PennGrader automatically serializes it and all its dependencies and ships to AWS for grading.

To create a homework for your class you will need a course `SECRET_KEY`. We will have a website open to register soon...

Then open the following Google Colab Jupyter Notebook:

Teacher_Backend_Template.ipynb #TO UPLOAD 

Student_Homework_Notebook_Template.ipynb #TO UPLOAD

Also, make sure to watch THIS #TODO# video on how to write your first PennGrader homework.

## Behind the scenes...
In the following section I will go into details about the system implementation. Below is the system design overview we will go into.

![Architecture Design](https://penngrader-wiki.s3.amazonaws.com/design.png)

### Clients
#### Student's Client: PennGrader
coming soon...
#### Teacher's Client: PennGraderBackend
coming soon...

### Lambdas
#### Grader
coming soon...
#### Grades
coming soon...
#### HomeworkConfig
coming soon...

### DynamoDB Tables & S3 Buckets
coming soon...



