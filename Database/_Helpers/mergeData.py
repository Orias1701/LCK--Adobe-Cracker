import logging
import re, os
import pandas as pd
import json, csv, openpyxl

from . import Common

def mergeJsons(file1Path, file2Path, outputPath):

    data1 = Common.readJson(file1Path)
    data2 = Common.readJson(file2Path)

    all_keys = set()
    for item in data1 + data2:
        all_keys.update(item.keys())

    level_keys = [k for k in all_keys if k.startswith('Level')]
    
    def extractLevelNumber(key):

        match = re.search(r'\d+', key)
        return int(match.group()) if match else 0

    sorted_level_keys = sorted(level_keys, key=extractLevelNumber)
    
    other_keys = [k for k in all_keys if k not in sorted_level_keys and k != 'Index']
    final_key_order = ['Index'] + sorted_level_keys + sorted_level_keys + other_keys

    last_index_json1 = data1[-1].get('Index', 0) if data1 else 0
    
    for i, item in enumerate(data2):
        item['Index'] = last_index_json1 + (i + 1)

    merged_data = data1 + data2
    final_json = []

    for item in merged_data:
        new_item = {}
        for key in final_key_order:
            new_item[key] = item.get(key, "")
        final_json.append(new_item)

    Common.writeJson(final_json, outputPath, indent=4)
    print(f"Đã gộp thành công vào file: {outputPath}")

if __name__ == "__main__":
    mergeJsons('data1.json', 'data2.json', 'merged.json')