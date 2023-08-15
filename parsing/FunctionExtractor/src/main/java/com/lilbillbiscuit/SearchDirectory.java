package com.lilbillbiscuit;

import java.io.File;
import java.util.ArrayList;
import java.util.List;

public class SearchDirectory {

    public static ArrayList<String> search(String path) {
        File directory = new File(path);
        String pattern = "/src/main";
        ArrayList<String> temp = new ArrayList<>(searchDirectory(directory, pattern));
        // filter result to only include unique paths
        ArrayList<String> filteredResult = new ArrayList<>();
        for (String s : temp) {
            // check if string is already in filteredResult
            boolean found = false;
            for (String s2 : filteredResult) {
                if (s.equals(s2)) {
                    found = true;
                    break;
                }
            }
            if (!found) {
                filteredResult.add(s);
            }
        }

        return filteredResult;
    }

    public static List<String> searchDirectory(File directory, String pattern) {
        List<String> result = new ArrayList<>();
        if (directory == null || !directory.isDirectory()) {
            return result;
        }

        searchDirectoryRecursively(directory, pattern, result);
        return result;
    }

    private static void searchDirectoryRecursively(File directory, String pattern, List<String> result) {
        if (directory == null || !directory.isDirectory()) {
            return;
        }

        File[] files = directory.listFiles();
        if (files != null) {
            for (File file : files) {
                if (file.isDirectory()) {
                    // check if file ends with pattern
                    if (file.getPath().contains(pattern)) {
                        // add path with everything after pattern removed
                        result.add(file.getPath().substring(0, file.getPath().indexOf(pattern)));
                    }
                    searchDirectoryRecursively(file, pattern, result);
                }
            }
        }
    }
}
