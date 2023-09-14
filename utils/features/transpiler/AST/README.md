# Syntax for the Abstract Syntax Tree (AST)

The idea is to allow the user to more generically create the means to web-scrape any website (on their own behalf) if they so choose to.
The transpiler will use this pre-defined AST to parse and convert the user/s YAML file into python code.
There will be another AST created later on to allow a User Interface allowing the user to create this "YAML" file through the web-ui instead of creating it manually
The AST converting to python code will more specifically create the code to create gradio components i.e. the user creating their own custom UI to browse with, in addition to the code that provides details of how to browse, parse, navigate, & download from a website.

If/When the user chooses to create that YAML file they will need to "already" understand how to use the web-inspector tool on their browser to look at different elements of the website they want to use.
The details of which the user needs will be further elaborated on in a future created wiki document.


