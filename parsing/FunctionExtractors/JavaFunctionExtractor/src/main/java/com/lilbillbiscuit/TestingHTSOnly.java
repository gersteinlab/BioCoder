package com.lilbillbiscuit;

import org.json.JSONObject;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.ArrayList;

public class TestingHTSOnly {
    public static void main(String[] args) throws IOException {
        ArrayList<MethodObj> methods = new ArrayList<>();
        ArrayList<JSONObject> json = new ArrayList<>();
        Main2.parseRepo("/Users/billyqian/temprepos/htsjdk", methods, json);
        System.out.println("Finished Execution");
        System.out.println("Total Methods: " + json.size());

        JSONObject obj = new JSONObject();
        obj.put("methods", json);
        PrintWriter out = new PrintWriter(new BufferedWriter(new FileWriter("methods3.json")));
        out.println(obj.toString(4));
        out.close();
        System.out.println("Finished Writing");
    }

}
