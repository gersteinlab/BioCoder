package com.lilbillbiscuit;

import org.apache.commons.io.IOUtils;
import org.json.JSONArray;
import org.json.JSONObject;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.nio.*;

public class JSONTesting {

//    public static void recursiveTraverse(JSONObject json) {
//        JSONArray key = json.names ();
//        for (int i = 0; i < key.length (); ++i) {
//            String keys = key.getString (i);
//            JSONObject value = json.getJSONObject(keys);
//            System.out.println(keys);
//            recursiveTraverse(value);
//        }
//    }

    private static void recursiveTraverse(String previousKey, JSONObject currentObject) {
        //iterate each key
        for (String currentKey : currentObject.keySet()) {
            //build the next key
            String nextKey = previousKey == null || previousKey.isEmpty() ? currentKey : previousKey + "-" + currentKey;
            Object value = currentObject.get(currentKey);
            if (value instanceof JSONObject) {
                //if current value is object, call recursively with next key and value
                recursiveTraverse(nextKey, (JSONObject) value);
            } else if (value instanceof JSONArray) {
                //if current value is array, iterate it
                JSONArray array = (JSONArray) value;
                for (int i = 0; i < array.length(); i++) {
                    Object object = array.get(i);
                    if (array.get(i) instanceof JSONObject) {
                        //assuming current array member is object, call recursively with next key + index and current member
                        recursiveTraverse(nextKey + "-" + i, (JSONObject) object);
                    } else {
                        //assuming current array member is not object, print it
//                        System.out.println("LOOKFIR"+nextKey + "-" + i + ", " + object);
                    }
                }
            } else {
                //value is neither object, nor array, so we print and this ends the recursion
                String lastParameter = nextKey.substring(nextKey.lastIndexOf("-") + 1);
                if (lastParameter.equals("filePath")) {
                    String removePrefix = "/Users/billyqian/temprepos/";
                    String filePath = (String) value;
                    filePath = filePath.replace(removePrefix, "");
                    System.out.println(filePath);
                    // put back into json
                    currentObject.put(currentKey, filePath);
                }
//                System.out.println(nextKey + ", " + value);
            }
        }
    }
    public static void main(String[] args) throws IOException {
        File f = new File("methods2.json");
        JSONObject json;
        if (f.exists()){
            InputStream is = new FileInputStream("methods2.json");
            String jsonTxt = IOUtils.toString(is, StandardCharsets.UTF_8);
            json = new JSONObject(jsonTxt);
//            String a = json.getString("1000");
//            System.out.println(a);
        } else {
            json = new JSONObject();
        }

//        JSONArray key = json.names ();
//        // Should only be one methods parameter
//        JSONArray methods = key.getJSONArray(0);
//        for (int i = 0; i < methods.length(); i++) {
//            JSONObject method = methods.getJSONObject(i);
//            System.out.println(method.getString("name"));
//        }
        recursiveTraverse("", json);
//        recursiveTraverse(json);
        // write json to file
        PrintWriter out = new PrintWriter(new BufferedWriter(new FileWriter("methods2_cleaned.json")));
        out.println(json.toString(4));
        out.close();

    }
}
