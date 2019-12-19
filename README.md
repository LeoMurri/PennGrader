# PennGrader
Welcome to the PennGrader!

Here at PennGrader we believe that learning comes from lots of practice...and from making lots of mistakes. 

After many years as a student I found myself very frustrated in the following homework timeline: struggle on a homework assignment for weeks, submit something that may or may not be right and then wait a few more weeks to receive any type of feedback, at which point I had forgotten all about the homework. After many years as a TA, I also found myself very frustrated with the common auto-grading tools, the hours and hours of manual grading and the onslaught of re-grade requests that came thereafter.

From these frustrations, the PennGrader was born!

The PennGrader was built to allow students to get instant feedback and many opportunities for re-submission. After all, programming is about making mistakes and learning from feedback! Moreover, we wanted to allow TAs and Instructors to write their homework in any way they pleased, without having to worry about the structure of a specific auto-grader. The examples below are done using Jupyter Notebooks which is the most common use case, but you can use this for normal Python homework as well. 

Here is what a student sees in his Homework Notebook. All a student has to do is write her solution and run the auto-grading cell.

![Sample Question](https://penngrader-wiki.s3.amazonaws.com/sample_question.gif)

Through the magic of AWS Lambdas, the student's answer (in this case the `addition_function` object) is packaged and shipped to the backend where it is checked against the teacher-defined test case. Finally, a score is returned. All students' scores are saved in the backend and are easily accessible to the instructors. If at first they don't succeed, they can  learn from their mistakes and try again.  (Yes, if you'd like, can set a maximum number of daily submissions to incentivize students to start early). This "grader" function can easily be used from any Jupyter noteboook (even Google Colab), all you have to do is to `pip install penngrader`. See templates below.

Ok, ok, you might be saying to yourself: "That looks easy enough, but what about us TAs, we want something that simple too!" Well, look no further. The TAs/Instructors' experience is just as seamless. All TAs will share a __Teacher_Backend__ notebook, which contains all the test case functions. The logic of how testing is done is simple: whatever Python object gets passed through the `answer` field in the `grade(...)` function (see above) will be the input to the test case function (see below). In the above example, `addition_function` is passed as the answer to a test case named `"test_case_1"`. Therefore, the TAs will need to write a `test_case_1(addition_function)` function in the __Teacher_Backend__ notebook, as follows:

![Sample Question](https://penngrader-wiki.s3.amazonaws.com/sample_update.gif)

As you can see, this function tests that `addition_function(1,2) == 3`, if correct it add 5 points to the `student_score`. The test must then return a integer tuple `(student_score, max_score)`, which is what will be displayed to the student. As you can see this type of test function gives the Instructor complete flexibility on what to test and how much partial credit to give. Remember that the answer that gets passed to the test case could be anything... a function, a class, a dataframe, a list, a picture... anything! The PennGrader automatically serializes it and all its dependencies and ships to AWS for grading.

To create a homework for your class you will need a course `SECRET_KEY`. We will open to the public soon, however for now contact me at leonardo.murri1995@gmail.com if you are intrested in using the PennGrader for your class.

[PennGrader_Homework_Template.ipynb](https://penngrader-wiki.s3.amazonaws.com/PennGrader_Homework_Template.ipynb)

[PennGrader_TeacherBackend.ipynb](https://penngrader-wiki.s3.amazonaws.com/PennGrader_TeacherBackend.ipynb)

Download these two notebooks and launch them via Jupyter. They will show you how to add grading cells in your homework notebook and add write test cases via the teacher backend, as well as view student's grades.

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

The _Grader_ lambda gets triggered from an API Gateway URL from the student's PennGrader client. The student's client as defined above will serialize its answer and make a POST request to the lambda with the following body parameters: 

`{'homework_id' : ______, 'student_id' : ________, 'test_case_id' : ________, 'answer' : _______ }`

The lambda will proceed by downloading the correst test_



#### Grades
coming soon...
#### HomeworkConfig
coming soon...

### DynamoDB Tables & S3 Buckets
As shown in the above schematic we maintain the majority of the data needed for grading and grade storage on DynamoDB. Below we list the information recorded in each table.

**Classes DynamoDB Table**

_Classes_ contains information about all courses currently registered for the PennGrader. The grading protocol is on a per-class basis. Each class that wants to create a course that uses the PennGrader will receive `SECRET_KEY`, this secret key will be passed in the TeacherBackend client to allow instructors to edit test cases. The tables contains the following schema:

`secret_key` : Unique UUID used as secret identifier for a course.

`course_id`  : Human readable identifier representing the course number and semester of the class offered i.e. 'CIS545_Spring_2019'. This ID will be the pre-fix of the `homework_id`, which will be used to identify an homework assignemnt.

**HomeworksMetadata DynamoDB Table**

The _HomeworksMetadata_ is used to maintain updatable information about a specific homework. The information in this table will be editable from the TeacherBackend even after homework release. The tables contains the following schema:

`homework_id` : Unique identifier representing a course + homework number pair. _homeowork_id_ is constructed by taking the _course_id_ defined above and appending the homework number of the assigment in question. For example, given the course id defined above (CIS545_Spring_2019), the _homework_id_ for the first homework will be 'CIS545_Spring_2019_HW1'. This homework_id will be passed into the PennGrader Grader class in the student's homework notebook and will be used to correctly find the correct test cases and store the student scores correctly.

`deadline` : String representing the deadline of the homework in local time i.e. 2019-12-05 11:59 PM (format: YYYY-MM-DD HH:MM A)

`max_daily_submissions` : Number representing the total number of submissions allows per test case per day. For example, if this number is set to 5, it means that all students can submit an answer to a specific test case 5 time a day. Resetting at midnight. 

`max_score` : The total number of points this homework is worth. This number should be equal to the sum of all test case weights. _max_score_ is used to show students how many points they have earned out of the total assignment.

**HomeworksTestCases DynamoDB Table**

The _HomeworksTestCases_ table contains a serialized encoding of the test cases and libraries imports needed to a run a student's answer. The tables contains the following schema:

`homework_id` : Same _homework_id_ from the _HomeworksMetadata_ table.

`test_cases` : This field contains a dill UTF-8 string serialization of the test cases defined in the teacher backend. The teacher backend extract all test case functions from the notebook and creates a dictionary of _name_ -> _function_. This parameter is deserailized when a new grading request is made and the correct test case is extracted and ran. 

`libraries` : Similar to the _test_cases_ field, the libraries is UTF-8 dill serialized list of tuples that contain all libraries and functions imported in the teacher backend notebook and their appropriate shortname. These list is used to import all needed libraries to run a specific test case. 


**Gradebook DynamoDB Table**

The _Gradebook_ table contains all grading submissions and student scores. The tables contains the following schema:

`homework_id` : Same _homework_id_ from the _HomeworksMetadata_ table.

`student_submission_id` : String representing a student submission. This string is create by appending the student's PennID to the test case name i.e. '12345678_test_case_1'.

`max_score` : Maxium points that can be earned for this test case

`student_score` : Points earned by the student on this test case. 

Note: Currently only the last submission is recorded, thus the latest student score will overwrite all previous scores.


