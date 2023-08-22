package com.lilbillbiscuit;

import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.Node;
import com.github.javaparser.ast.body.ClassOrInterfaceDeclaration;
import com.github.javaparser.ast.body.ConstructorDeclaration;
import com.github.javaparser.ast.body.FieldDeclaration;
import com.github.javaparser.ast.body.MethodDeclaration;

import org.json.JSONObject;

import java.io.*;
import java.lang.reflect.Field;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;

public class BundleStructures {

}

class SingleImportClass {
    String name;
    String filePath;

    String processed;

    ClassOrInterfaceDeclaration classDec;
    int lineCount=0, methodCount=0, fieldCount=0;

    public SingleImportClass(String name, String filePath, ClassOrInterfaceDeclaration classDec) {
        this.name = name;
        this.filePath = filePath;
        this.classDec = classDec;
        this.analyze();
    }

    public void analyze() {
        StringBuilder sb = new StringBuilder();
        sb.append("public ").
                append(classDec.isInterface() ? "interface" : "class")
                .append(" ")
                .append(classDec.getNameAsString())
                .append(" {\n");
        lineCount++;
        for (Node childNode : classDec.getChildNodes()) {
//            System.out.println(childNode.getClass());
            if (childNode instanceof MethodDeclaration) {
//                System.out.println(((MethodDeclaration) childNode).getJavadocComment());
                sb.append("    ")
                        .append(((MethodDeclaration) childNode).getDeclarationAsString())
                        .append("\n");
                methodCount++; lineCount++;
            } else if (childNode instanceof ConstructorDeclaration) {
                sb.append("    ")
                        .append(((ConstructorDeclaration) childNode).getDeclarationAsString())
                        .append(";\n");
                methodCount++; lineCount++;
            } else if (childNode instanceof FieldDeclaration temp) {
                sb.append("    ")
                        .append(temp.toString())
                        .append(";\n");
                fieldCount++; lineCount++;
            }
        }
        sb.append("}\n");
        lineCount++;

        processed = sb.toString();
    }

    public JSONObject toJSONObject() {
        return new JSONObject()
                .put("name", name)
                .put("filePath", filePath);

    }

}

class ImportData {
    public String filePath;
    public String className;
    public String methodString;
    public int lineCount;
    public int methodCount;
    public int classCount;

    public int fieldCount;



    public ImportData(String filePath, String methodsOnly, int lineCount, int methodCount, int classCount, int fieldCount) {
        this.filePath = filePath;
        this.methodString = methodsOnly;
        this.lineCount = lineCount;
        this.methodCount = methodCount;
        this.classCount = classCount;
        this.fieldCount = fieldCount;
    }

    public JSONObject toJSONObject() {
        return new JSONObject()
                .put("filePath", filePath)
                .put("methodsOnly", methodString)
                .put("lineCount", lineCount)
                .put("methodCount", methodCount)
                .put("classCount", classCount)
                .put("fieldCount", fieldCount);
    }

    public static ArrayList<SingleImportClass> createImportObjArray(String filePath) throws IOException {
        ArrayList<SingleImportClass> importarr = new ArrayList<>();
        Path path = Path.of(filePath);
        String content = Files.readString(path);
        CompilationUnit cu = StaticJavaParser.parse(content);
        StringBuilder sb = new StringBuilder();
        int lineCount = 0, methodCount = 0, classCount = 0, fieldCount = 0;
        for (Node node : cu.getChildNodes()) {
            if (node instanceof ClassOrInterfaceDeclaration classDec) {
                SingleImportClass sc = new SingleImportClass(classDec.getNameAsString(), filePath, classDec);
                importarr.add(sc);
            }
        }
        return importarr;
    }

    public static ImportData createImportObj(String filePath) throws IOException {
        Path path = Path.of(filePath);
        String content = Files.readString(path);
        CompilationUnit cu = StaticJavaParser.parse(content);
        StringBuilder sb = new StringBuilder();
        int lineCount = 0, methodCount = 0, classCount = 0, fieldCount = 0;
//        System.out.println(cu);
        for (Node node : cu.getChildNodes()) {
            if (node instanceof ClassOrInterfaceDeclaration classDec) {
                sb.append("public ").
                        append(classDec.isInterface() ? "interface" : "class")
                        .append(" ")
                        .append(classDec.getNameAsString())
                        .append(" {\n");
                classCount++; lineCount++;
                for (Node childNode : classDec.getChildNodes()) {
//                    System.out.println(childNode.getClass());
                    if (childNode instanceof MethodDeclaration) {
//                        System.out.println(((MethodDeclaration) childNode).getJavadocComment());
                        sb.append("    ")
                                .append(((MethodDeclaration) childNode).getDeclarationAsString())
                                .append("\n");
                        methodCount++; lineCount++;
                    } else if (childNode instanceof ConstructorDeclaration) {
                        sb.append("    ")
                                .append(((ConstructorDeclaration) childNode).getDeclarationAsString())
                                .append(";\n");
                        methodCount++; lineCount++;
                    } else if (childNode instanceof FieldDeclaration temp) {
                        sb.append("    ")
                                .append(temp.toString())
                                .append(";\n");
                        fieldCount++; lineCount++;
                    }
                }
                sb.append("}\n");
                lineCount++;
            }
        }
        return new ImportData(filePath, sb.toString(),
                lineCount, methodCount, classCount, fieldCount);

    }
}
