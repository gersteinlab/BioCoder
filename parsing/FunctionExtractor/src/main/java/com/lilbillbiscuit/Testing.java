package com.lilbillbiscuit;

import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import org.json.JSONObject;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.HashMap;

public class Testing {
    public static void main(String[] args) throws IOException {
        String test_filename = "/Users/billyqian/temprepos/htsjdk/src/main/java/htsjdk/samtools/util/SamRecordTrackingBuffer.java";
        String test_basepath = "/Users/billyqian/temprepos/htsjdk/src/main/java/";
        File file = new File(test_filename);
        ImportData importObj = ImportData.createImportObj(file.getPath());
//        System.out.println(importObj.toJSONObject().toString(4));
        String content = Files.readString(file.toPath());
        CompilationUnit cu = StaticJavaParser.parse(content);
        HashMap<String, ImportData> importCache = new HashMap<>();
        ImportObj test = new ImportObj(cu, test_basepath);
        test.processImports(importCache);

        ArrayList<MethodObj> methods = new ArrayList<>();
        ArrayList<JSONObject> json = new ArrayList<>();
        Main2.getMethodsFromFileV2(test_filename, methods, importCache, test_basepath, json);
    }
}
