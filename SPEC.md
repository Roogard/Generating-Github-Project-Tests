This projects end to end goal is to be able to take any project from github and generate unit test cases for every single function in that github repository. 


The project has many parts, I will now go over them one by one and state what I expect for each one. 

1. Getting functions from a github repository.

For this part, I want to make use of an AST parser. Specifically, I want to use tree-sitter to get a different file for every function in the github desktop. After this, the files will be sent to step 2. 

I also have an idea about sending a little more than the function to step 2. It would be cool if I could get additional information about the functions, and then also send that information on. I only want to do this if it's actually helpful to the agents in part 2.

I want this to also be able to get functions of multiple different coding languages.

2. Generating unit tests for each function. For every passed function, I want to be able to get the following unit tests for each function: BVA (boundary value analysis), EPC, dataflow, and CFG tests. In order to do this, I am thinking of using a langgraph like system. Specifically, I want to have four subagents who all specialize in their own unit test specialty (BVA, EPC, dataflow, CFG), and then merge them into one test case for that file. 

3. I need to output a folder that for every function. I want each folder to contain the file itself, and all the different test cases for each function. For now I will use 5 files, one for each unit test case and one for the function. 

4. This code should be able to be sent to my teacher. I was thinking of using a docker container to take all the code and ship it off to my professor, so he can run it himself on his computer.


