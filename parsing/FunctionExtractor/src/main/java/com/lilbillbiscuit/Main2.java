package com.lilbillbiscuit;

import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.ImportDeclaration;
import com.github.javaparser.ast.Node;
import com.github.javaparser.ast.PackageDeclaration;
import com.github.javaparser.ast.body.ClassOrInterfaceDeclaration;
import com.github.javaparser.ast.body.FieldDeclaration;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.body.VariableDeclarator;
import com.github.javaparser.ast.expr.Name;
import com.github.javaparser.ast.expr.NameExpr;
import com.github.javaparser.ast.expr.ObjectCreationExpr;
import com.github.javaparser.ast.expr.SimpleName;
import com.github.javaparser.ast.type.ClassOrInterfaceType;
import com.github.javaparser.ast.visitor.VoidVisitorAdapter;

import org.checkerframework.checker.units.qual.A;
import org.json.JSONObject;

import java.io.*;
import java.lang.reflect.Array;
import java.lang.reflect.Method;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;

import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Consumer;

public class Main2 {
    public static void listClasses(String filePath) {
        new VoidVisitorAdapter<Object>() {
            @Override
            public void visit(MethodDeclaration n, Object arg) {
                super.visit(n, arg);
                printAboveProgressBar(" * " + n.getJavadocComment());
                printAboveProgressBar(" ? " + n.getDeclarationAsString());
            }
        }.visit(StaticJavaParser.parse(filePath), null);
        printAboveProgressBar();
    }

    private static void printAboveProgressBar(String message) {
        // Move the cursor up two lines and back to the beginning of the line
        System.out.print("\033[2A\r");

        // Print the message followed by a new line
        System.out.print(message+"\n");

        // Move the cursor back down to the primary progress bar
        System.out.print("\033[2B\r");
    }

    private static void printAboveProgressBar() {
        // Move the cursor up two lines and back to the beginning of the line
        System.out.print("\033[2A\r");

        // Print the message followed by a new line
        System.out.print("\n");

        // Move the cursor back down to the primary progress bar
        System.out.print("\033[2B\r");
    }

    public static void getMethodsFromFileV2(String filename, ArrayList<MethodObj> methods, HashMap<String, ImportData> importCache, String baseString, ArrayList<JSONObject> jsons, String repoName) throws IOException {
        Path filepath = Path.of(filename);
        String content = Files.readString(filepath);
        CompilationUnit cu = StaticJavaParser.parse(content);

        String packageName = "";
        ImportObj importObj = new ImportObj(cu, baseString);
        importObj.processImports(importCache);
        String className = "";
        for (Node node : cu.getChildNodes()) {
            if (node.getClass() == ClassOrInterfaceDeclaration.class) {
                className = ((ClassOrInterfaceDeclaration) node).getNameAsString();
                ClassOrInterfaceDeclaration md = (ClassOrInterfaceDeclaration) node;
                for (Node node2 : md.getChildNodes()) {
                    if (node2.getClass() == MethodDeclaration.class) {
                        MethodDeclaration md2 = (MethodDeclaration) node2;
                        MethodObj obj = new MethodObj(null/*cu*/, md2, filename, importObj, repoName);
                        obj.analyzeIntraClassMethods(cu, className);
                        obj.setPackageName(packageName);
//                        methods.add(obj);
                        jsons.add(obj.toJSON());
                    }
//                    else if (node2.getClass() == ConstructorDeclaration.class) {
//                        ConstructorDeclaration md2 = (ConstructorDeclaration) node2;
//                        obj. = md2;
//                    }
                    //TODO: Add support for constructors

                }
            } else if (node.getClass() == PackageDeclaration.class) {
                PackageDeclaration md = (PackageDeclaration) node;
                packageName = md.getNameAsString();
            }
        }
        return;
    }
    public static void getMethodsFromFile(String filename, ArrayList<MethodObj> methods, String repoName) throws IOException {
        Path filepath = Path.of(filename);
        String content = Files.readString(filepath);
        CompilationUnit cu;
        cu = StaticJavaParser.parse(content);

        ImportObj importObj = new ImportObj(cu, null);

        for (Node node : cu.getChildNodes()) {
//            System.out.println(node.getClass());
            if (node.getClass() == ClassOrInterfaceDeclaration.class) {
                ClassOrInterfaceDeclaration md = (ClassOrInterfaceDeclaration) node;
                for (Node node2 : md.getChildNodes()) {
//                    System.out.println(node2.getClass());
                    if (node2.getClass() == MethodDeclaration.class) {
                        MethodDeclaration md2 = (MethodDeclaration) node2;
                        MethodObj obj = new MethodObj(null, md2, filename, importObj, repoName);
                        methods.add(obj);
                    }
//                    else if (node2.getClass() == ConstructorDeclaration.class) {
//                        ConstructorDeclaration md2 = (ConstructorDeclaration) node2;
//                        obj. = md2;
//                    }
                }
            } else if (node.getClass() == PackageDeclaration.class) {
                PackageDeclaration md = (PackageDeclaration) node;
                printAboveProgressBar(md.getNameAsString());
            }
//            else if (node.getClass() == ImportDeclaration.class) {
//                ImportDeclaration md = (ImportDeclaration) node;
//                String importName = md.getNameAsString();
//                if (importName.contains("java.")) {
//                    System.out.println("Found java.*, don't copy");
//                } else {
////                    importName = importName.replace(".", "/");
////                    imports.add(importName);
//
//                }
//            }
        }
        return;
    }

    public static String hasCustomImport(String fileName) throws IOException {
        Path filepath = Path.of(fileName);
        String content = Files.readString(filepath);
        CompilationUnit cu = StaticJavaParser.parse(content);
        for (ImportDeclaration importDeclaration : cu.getImports()) {
            String importName = importDeclaration.getNameAsString();
            if (!importName.contains("java.")) {
                return importName;
            }
        }
        cu = null;
        return null;
    }

    public static String getRepoBaseString(String repoPath, ArrayList<MethodObj> methods) throws IOException {
        //repoPath should also be the base path of the repository
        // Once we find a non-java import statement
        // try to import the following directories:
        // repo/src/main/java
        // repo/src/main
        // repo/src

        String[] suffixes = {"/src/main/java/", "/src/main/", "/src/"};
        String[] pathsbase = new String[3];
        for (int i = 0; i < 3; i++) {
            pathsbase[i] = repoPath+suffixes[i];
        }
        ArrayList<String> paths2 = SearchDirectory.search(repoPath);

        // Add all paths in paths2 to paths
        String[] paths = new String[pathsbase.length + suffixes.length*paths2.size()];
        System.arraycopy(pathsbase, 0, paths, 0, pathsbase.length);
        int index = pathsbase.length;
        for (String path : paths2) {
            for (String suffix : suffixes) {
                paths[index++] = path + suffix;
            }
        }


        ArrayList<String> fileNames = new ArrayList<>();
        listJavaFilesProxy(repoPath, fileNames);

        HashMap<String, Integer> importCount = new HashMap<>();

        for (String path : fileNames) {
            String importName = hasCustomImport(path);
            if (importName == null) {
                continue;
            } else {
                // Try to find the import in the repo directory
                // Check if the mentioned files exist
                for (String tempPath : paths) {
                    String temp = tempPath + importName.replace(".", "/") + ".java";
                    if (new File(temp).exists()) {
                        importCount.put(tempPath, importCount.getOrDefault(tempPath, 0) + 1);
                    }
                }
            }
        }
        String maxKey = null;
        int maxVal = 0;
        for (String key : importCount.keySet()) {
            if (importCount.get(key) > maxVal) {
                maxKey = key;
                maxVal = importCount.get(key);
            }
        }
        System.gc();
        return maxKey;
    }

    public static void listJavaFiles(File[] files, ArrayList<String> fileNames) {
        for (File filename : files) {
            if (filename.isDirectory()) {
                listJavaFiles(Objects.requireNonNull(filename.listFiles()), fileNames);
            } else {
                // Getting the file name
                if (filename.getName().endsWith(".java")) {
                    fileNames.add(filename.getPath());
                }
            }
        }
    }
    public static void listJavaFilesProxy(String path, ArrayList<String> fileNames) {
        File[] files = new File(path).listFiles();
        assert files != null;
        listJavaFiles(files, fileNames);
    }

    public static boolean parseRepo(String repoPath, ArrayList<MethodObj> methods, ArrayList<JSONObject> jsons) throws IOException {
        return parseRepo(repoPath, methods, jsons, null);
    }

    public static boolean parseRepo(String repoPath, ArrayList<MethodObj> methods, ArrayList<JSONObject> jsons, Consumer<Double> progressUpdate) throws IOException {
        String baseString = getRepoBaseString(repoPath, methods);
        if (baseString == null) {
            printAboveProgressBar("No custom import found, skipping repo ("+ repoPath +")");
            return false;
        }
        printAboveProgressBar("Guessing repo import path: \"" + baseString + "\"");
        ArrayList<String> fileNames = new ArrayList<>();
        HashMap<String, ImportData> importCache = new HashMap<>();

        String repoName = repoPath.substring(repoPath.lastIndexOf("/")+1);
        listJavaFilesProxy(baseString, fileNames);
        int i=0;
        for (String filename : fileNames) {
            i++;
//            System.out.println("Parsing file: " + i + "/" + fileNames.size());
//            System.out.println("Parsing file: " + filename);
            getMethodsFromFileV2(filename, methods, importCache, baseString, jsons, repoName);
            progressUpdate.accept((double) i / fileNames.size());
            System.gc();
        }
        return true;
    }

    private static final AtomicInteger completedTasks = new AtomicInteger(0);
    private static final List<Double> taskProgress = Collections.synchronizedList(new ArrayList<>());
    private static final List<Boolean> taskResults = Collections.synchronizedList(new ArrayList<>());
    public static void main(String[] args) throws IOException {
        File file = new File("/home/ubuntu/repos/");
        File[] files = file.listFiles();

        List<MethodObj> methods = Collections.synchronizedList(new ArrayList<>());
        List<JSONObject> json = Collections.synchronizedList(new ArrayList<>());

        assert files != null;

        int numThreads = Runtime.getRuntime().availableProcessors();
        ExecutorService executor = Executors.newFixedThreadPool(numThreads);
        List<Future<Boolean>> futures = new ArrayList<>();

        // Initialize taskResults to all true
        for (int i = 0; i < files.length; i++) {
            taskResults.add(true);
        }

        AtomicInteger totalTasks = new AtomicInteger(0);
        for (File f : files) {
            if (f.isDirectory()) {
                int taskIndex = totalTasks.getAndIncrement();
                taskProgress.add(0.0);
                futures.add(executor.submit(new Callable<Boolean>() {
                    @Override
                    public Boolean call() {
                        try {
                            ArrayList<MethodObj> localMethods = new ArrayList<>();
                            ArrayList<JSONObject> localJson = new ArrayList<>();

                            Consumer<Double> progressUpdate = progress -> {
                                taskProgress.set(taskIndex, progress);
                                updateProgressBar(completedTasks.get(), totalTasks.get(), taskResults, taskProgress);
                            };

                            boolean result = parseRepo(f.getPath(), localMethods, localJson, progressUpdate);
                            taskResults.set(taskIndex, result);

                            synchronized (methods) {
                                methods.addAll(localMethods);
                            }
                            synchronized (json) {
                                json.addAll(localJson);
                            }

                            completedTasks.incrementAndGet();
                            updateProgressBar(completedTasks.get(), totalTasks.get(), taskResults, taskProgress);

                            return result;
                        } catch (Throwable e) {
                            printAboveProgressBar("Error in repo: " + f.getName());
                            taskResults.set(taskIndex, false);
                            return false;
                        }
                    }
                }));
            }
        }

        // Wait for all tasks to complete
        for (Future<Boolean> future : futures) {
            try {
                future.get();
            } catch (InterruptedException | ExecutionException e) {
                e.printStackTrace();
            }
        }

        executor.shutdown();
        updateProgressBar(taskResults.size(), taskResults.size(), taskResults, taskProgress);

        System.out.println("Finished Extraction");
        System.out.println("Total functions: " +json.size());

        System.out.println("Starting Categorization");

        HashMap<String, ArrayList<JSONObject>> map = new HashMap<>();
        for (JSONObject obj : json) {
            String repo = (String) obj.get("repoName");
            if (!map.containsKey(repo)) {
                map.put(repo, new ArrayList<>());
            }
            map.get(repo).add(obj);
        }

        System.out.println("Finished Categorization");
        System.out.println("Size: " + map.size());
        System.out.println("Starting Writing");

        // Write to file for each repo
        for (String repo : map.keySet()) {
            System.out.println("Writing " + repo);
            JSONObject obj = new JSONObject();
            obj.put("methods", map.get(repo));
            PrintWriter out = new PrintWriter(new BufferedWriter(new FileWriter("data/parsing/languages/Java/methods_data/methods_" + repo + ".json")));
            out.println(obj);
            out.close();
        }
        System.out.println("Finished Writing");
    }

    private static void updateProgressBar(int completed, int total, List<Boolean> taskResults, List<Double> taskProgress) {
        int width = 50; // Width of the primary progress bar
        double progress = (double) completed / total;
        int filledBars = (int) (progress * width);

        StringBuilder progressBar = new StringBuilder("\r[");
        for (int i = 0; i < width; i++) {
            if (i < filledBars) {
                progressBar.append("#");
            } else {
                progressBar.append(" ");
            }
        }
        progressBar.append("] ").append(String.format("%.2f", progress * 100)).append("%");

        progressBar.append("\n"); // Move to the next line to print secondary progress indicators

        String[] progressChars = {"▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"};

        for (int i = 0; i < taskProgress.size(); i++) {
            double taskProgressValue = taskProgress.get(i);
            boolean taskResult = taskResults.get(i);
            int progressIndex = (int) (taskProgressValue * progressChars.length);
            if (progressIndex >= progressChars.length) {
                progressIndex = progressChars.length - 1;
            }

            if (taskResult) {
                progressBar.append(progressChars[progressIndex]);
            } else {
                progressBar.append("X");
            }
//            progressBar.append(" ").append(String.format("%.2f", taskProgressValue * 100)).append("%");
//            progressBar.append("\n");
        }
        progressBar.append("\033[1A\r");
        System.out.print(progressBar.toString());

        // Move the cursor up to the primary progress bar and use carriage return
//        progressBar.append("\033[1A\r");
//

    }
}

interface FunctionObj {
    public void analyzeMethod();

    public String toJSONString();
    public JSONObject toJSON();
}

class MethodObj implements FunctionObj{
    ImportObj imports;
    public String signature, comment, methodString, packageName, returnType;

    public MethodDeclaration method;
//    CompilationUnit cu;
    int numParams, numLines, numCommentLines, numChars, numCommentChars, lineStart, lineEnd;
    ArrayList<String> params;
    String parentClass;
    String filePath;

    String repoName;

    ArrayList<String> intraClassFieldsUsed;

    ArrayList<String> customClassesUsed;

    public MethodObj(CompilationUnit cu, MethodDeclaration method, String filePath, ImportObj imports, String repoName) {
//        this.cu = cu;
        this.method = method;
        this.filePath = filePath;
        this.imports = imports;
        this.repoName = repoName;
        analyzeMethod();
    }
    public MethodObj(CompilationUnit cu, MethodDeclaration method, String filePath) {
//        this.cu = cu;
        this.method = method;
        this.filePath = filePath;
        analyzeMethod();
    }

    public void analyzeIntraClassMethods(CompilationUnit cu, String currentClass) {
        for (Node node : cu.getChildNodes()) {
            if (node instanceof ClassOrInterfaceDeclaration classOrInterfaceDeclaration) {
                if (!Objects.equals(classOrInterfaceDeclaration.getNameAsString(), currentClass)) {
//                    System.out.println("Skipping class: " + classOrInterfaceDeclaration.getNameAsString());
                    continue;
                }
                for (Node node2 : classOrInterfaceDeclaration.getChildNodes()) {
                    if (node2 instanceof MethodDeclaration methodDeclaration) {
//                        System.out.println(methodDeclaration.getSignature().toString());
                        if (!Objects.equals(methodDeclaration.getSignature().toString(), this.method.getSignature().toString())) {
                            intraClassFieldsUsed.add(methodDeclaration.getDeclarationAsString()+";");
                        }
                    } else if (node2 instanceof FieldDeclaration fieldDeclaration) {
//                        System.out.println(fieldDeclaration.toString());
                        intraClassFieldsUsed.add(fieldDeclaration.toString());
                    }
                }
            }
        }

        int hi=1;
    }

    public void setImportObj(ImportObj imports) {
        this.imports = imports;
    }
    public void setPackageName(String packageName) {
        this.packageName = packageName;
    }

    public void analyzeMethod() {
        this.intraClassFieldsUsed = new ArrayList<>();
        methodString = this.method.toString();
        signature = this.method.getDeclarationAsString();
        numParams = this.method.getParameters().size();
        numLines = this.method.getRange().get().end.line - this.method.getRange().get().begin.line;
        numChars = this.method.getRange().get().end.column - this.method.getRange().get().begin.column;
        lineStart = this.method.getRange().get().begin.line;
        lineEnd = this.method.getRange().get().end.line;
        returnType = this.method.getTypeAsString();
        params = new ArrayList<>();
        for (int i = 0; i < numParams; i++) {
            params.add(this.method.getParameter(i).toString());
        }
        if (this.method.getJavadocComment().isPresent()) {
            StringBuilder sb = new StringBuilder();
            sb.append("/**");
            sb.append(this.method.getJavadocComment().get().getContent());
            sb.append("*/");
            comment = sb.toString();
            numCommentLines = this.method.getJavadocComment().get().getRange().get().end.line - this.method.getJavadocComment().get().getRange().get().begin.line;
            numCommentChars = this.method.getJavadocComment().get().getRange().get().end.column - this.method.getJavadocComment().get().getRange().get().begin.column;

        } else {
            comment = "";
        }

        if (this.method.getParentNode().isPresent()) parentClass = this.method.getParentNode().get().getParsed().name();
        else parentClass = "null";
        this.getCustomClassesUsed();
    }

    public void getCustomClassesUsed() {
        customClassesUsed = new ArrayList<>();
        if (imports == null) return;
        method.walk(Node.TreeTraversal.POSTORDER, node -> {
//            if (Objects.equals(method.getNameAsString(), "query")) {
//                System.out.println(node.getClass());
//                System.out.println(node);
//                System.out.println("===================================");
//            }
            if (node instanceof ClassOrInterfaceType) {
                String name = ((ClassOrInterfaceType) node).getNameAsString();
//                if (Objects.equals(method.getNameAsString(), "query")) {
//                    System.out.println(node);
//                    System.out.println("===================================");
//
//                }
                if (name.contains("<")) {
                    name = name.substring(0, name.indexOf("<"));

                    String name2 = name.substring(name.indexOf("<")+1, name.length()-1);
                    customClassesUsed.add(name2);
                }
                customClassesUsed.add(name);
            }
//            if (node instanceof ObjectCreationExpr) {
//                String name = ((ObjectCreationExpr) node).getTypeAsString();
//                if (Objects.equals(method.getNameAsString(), "query")) {
//                    System.out.println(name);
//                    System.out.println("===================================");
//
//                }
//            }
        });

//        System.out.println(customClassesUsed);
//        for (String name : customClassesUsed) {
//            if (imports.getImport(name) != null) {
//
//                System.out.println(name + " " + imports.getImport(name).processed);
//            }
//        }
    }

    public JSONObject getCustomClassesUsedJSON() {
        JSONObject obj = new JSONObject();
        for (String name : customClassesUsed) {
            if (imports.getImport(name) != null) {
                obj.put(name, imports.getImport(name).processed);
            }
        }
        return obj;
    }
    public String toJSONString() {
        JSONObject obj = this.toJSON();
        return obj.toString();
    }

    public JSONObject toJSON() {
        JSONObject obj = new JSONObject();
        obj.put("function_id", signature.hashCode());
        obj.put("numParams", numParams);
        obj.put("numLines", numLines);
        obj.put("numChars", numChars);
        obj.put("lineStart", lineStart);
        obj.put("lineEnd", lineEnd);
        obj.put("returnType", returnType);
        obj.put("params", params);
        obj.put("parentClass", parentClass);
        obj.put("filePath", filePath);
        obj.put("signature", signature);
        obj.put("content", methodString);
        obj.put("comment", comment);
        obj.put("numCommentLines", numCommentLines);
        obj.put("numCommentChars", numCommentChars);
        obj.put("packageName", packageName);
        obj.put("repoName", repoName);
        if (imports != null) obj.put("imports", imports.toJSONObject());
        else {
            System.out.println("No imports found for " + signature + " in " + filePath);
            obj.put("imports", new JSONObject());
        }
        obj.put("additionalImports", getCustomClassesUsedJSON());
        StringBuilder sb = new StringBuilder();
        for (String s : intraClassFieldsUsed) {
            sb.append(s);
            sb.append("\n");
        }
        obj.put("intraClassFieldsUsed", sb.toString());
        return obj;
    }

}
class ImportObj {
    public ArrayList<ImportData> imports;
    public ArrayList<String> customImportStrings;
    public ArrayList<String> javaImports;
    public HashMap<String, SingleImportClass> definedImports, packageImports;
    int importCount =0, javaImportCount = 0, asteriskCount = 0, classCount = 0;

    String basePath;
    public String packageName;
    public ImportObj(CompilationUnit cu, String basePath) {
        imports = new ArrayList<>();
        javaImports = new ArrayList<>();
        customImportStrings = new ArrayList<>();
        definedImports = new HashMap<>();
        packageImports = new HashMap<>();
        for (ImportDeclaration importDeclaration : cu.getImports()) {
            if (importDeclaration.isAsterisk()) {
//                imports.add(importDeclaration.getNameAsString() + ".*"); //TODO: disabled asterisks for now, make sure to recurse directories later
            } else if (!importDeclaration.getNameAsString().startsWith("java")) {
                customImportStrings.add(importDeclaration.getNameAsString());
            } else {
                javaImports.add(importDeclaration.getNameAsString());
                javaImportCount++;
            }
        }
        this.basePath = basePath;

        if (cu.getPackageDeclaration().isPresent()) {
            packageName = cu.getPackageDeclaration().get().getNameAsString();
        } else {
            packageName = "";
        }
        try {
            this.processPackageFiles();
        } catch (IOException e) {
            e.printStackTrace();
        }
        cu = null;
    }
    public void processPackageFiles() throws IOException {
        // basePath should have a trailing slash
        // Get list of files in package
        File packageDir = new File(basePath + packageName.replace(".", "/"));
        File[] packageFiles = packageDir.listFiles();
        assert packageFiles != null;
        for (File packageFile : packageFiles) {
            if (packageFile.getName().endsWith(".java")) {
//                String className = packageFile.getName().substring(0, packageFile.getName().length() - 5);
                ArrayList<SingleImportClass> singleImportClasses = ImportData.createImportObjArray(packageFile.getAbsolutePath());
                for (SingleImportClass singleImportClass : singleImportClasses) {
                    packageImports.put(singleImportClass.name, singleImportClass);
                }
            }
        }
        int hi=5;
    }

    void processImports(HashMap<String, ImportData> importCache) throws IOException {
        // basePath should have a trailing slash

        for (String s : customImportStrings) {
            s = s.replace(".", "/");
            if (importCache.containsKey(s)) {
                imports.add(importCache.get(s));

            } else {
                try {
                    ImportData importData = ImportData.createImportObj(basePath + s + ".java");
                    importCount++;
                    classCount += importData.classCount;
                    importCache.put(s, importData);
                    imports.add(importData);

                    ArrayList<SingleImportClass> singleImportClasses = ImportData.createImportObjArray(basePath + s + ".java");
                    for (SingleImportClass singleImportClass : singleImportClasses) {
                        definedImports.put(singleImportClass.name, singleImportClass);
                    }


                } catch (Exception e) {
//                    System.out.println("Error processing import: " + s); //TODO: deal with imports that are classes instead of files
                }
            }
        }
    }

    public SingleImportClass getImport(String name) {
        if (definedImports.containsKey(name)) return definedImports.get(name);
        if (packageImports.containsKey(name)) return packageImports.get(name);
        return null;
    }

    public JSONObject toJSONObject() {
        JSONObject obj = new JSONObject();
        obj.put("importCount", importCount);
        obj.put("javaImportCount", javaImportCount);
        obj.put("asteriskCount", asteriskCount);
        obj.put("classCount", classCount);
        JSONObject[] importObjs = new JSONObject[imports.size()];
        for (int i = 0; i < imports.size(); i++) {
            importObjs[i] = imports.get(i).toJSONObject();
        }
        obj.put("imports", importObjs);
        return obj;
    }
}