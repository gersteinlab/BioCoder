# Java Function Parser

This is a Java program that parses Java repositories and extracts functions from them. It is a maven project that depends on the JavaParser and JSONObject libraries.

## Running the program
First, install maven. Then, run the following commands:
```
mvn clean
mvn package
```

This will create a jar file in the target directory. To run the program, run the following command:
```
java -jar target/FunctionExtractor-1.0-SNAPSHOT.jar <path to directory containing repositories>
```

This will generate a file called `methods.json` in the current directory. This file contains all the parsed functions from the repositories, along with the file they were found in and the repository they were found in. The full list of fields is as follows:

* `function_id`: A unique identifier for the function. This is the hashcode of the function's signature.
* `numParams`: The number of parameters the function has.
* `numLines`: The number of lines the function spans.
* `numChars`: The number of characters the function spans.
* `lineStart`: The line number the function starts on.
* `lineEnd`: The line number the function ends on.
* `returnType`: The return type of the function.
* `params`: A list of the function's parameters.
* `parentClass`: The class the function is in.
* `filePath`: The path to the file the function is in.
* `signature`: The function's signature.
* `content`: The function's content.
* `comment`: The function's comment.
* `numCommentLines`: The number of lines the function's comment spans.
* `numCommentChars`: The number of characters the function's comment spans.
* `packageName`: The package the function is in.
* `repoName`: The repository the function is in.
* `imports`: A list of the function's imports.
* `additionalImports`: A list of the function's additional imports.
* `intraClassFieldsUsed`: A list of the function's intra-class fields used.
* `intraClassFieldsUsed`: A list of the function's intra-class fields used.

