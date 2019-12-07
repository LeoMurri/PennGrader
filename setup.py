import setuptools
with open("README.md", "r") as fh:
    long_description = fh.read()
setuptools.setup(
     name='penngrader',  
     version='0.3.1',
     scripts=[],
     author="Leonardo Murri",
     author_email="leonardo.murri1995@gmail.com",
     description="In-line python grader client.",
     long_description=long_description,
   long_description_content_type="text/markdown",
     url="https://github.com/LeoMurri/PennGrader",
     packages=['penngrader'],
     classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent",
     ],
 )
