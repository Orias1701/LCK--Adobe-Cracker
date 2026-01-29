import logging
import re, os
import pandas as pd
import json, csv, openpyxl

from . import Common

def process(input_path, schema_path, output_path):
    if not os.path.exists(input_path) or not os.path.exists(schema_path):
        print("Lỗi: Không tìm thấy file dữ liệu hoặc file schema.")
        return

    try:
        schema = Common.readJson(schema_path)
        inputs = Common.readJson(input_path)
        
        df = pd.DataFrame(inputs)
        print("✅ Đã đọc Data thành công.")
        
        for field_name, field_type in schema.items():
            if field_name in df.columns:
                if field_type == 'array':
                    print(f"   -> Đang xử lý cột '{field_name}' theo kiểu ARRAY (gộp dòng)...")
                    df[field_name] = df[field_name].apply(
                        lambda x: '\n'.join([str(item) for item in x]) if isinstance(x, list) else x
                    )
                elif field_type == 'number':
                    df[field_name] = pd.to_numeric(df[field_name], errors='coerce')
                elif field_type == 'string':
                    df[field_name] = df[field_name].astype(str)
                    df[field_name] = df[field_name].replace('nan', '')

        df.to_excel(output_path, index=False)
        print(f"✅ Thành công! File Excel đã được tạo tại: {output_path}")

    except Exception as e:
        print(f"❌ Có lỗi xảy ra: {e}")

def mainProcess(FOLDER_DATA, NEEDED_DATA):
    inputs_file = f'{FOLDER_DATA}/{FOLDER_DATA}_{NEEDED_DATA}_Segment.json'
    schema_file = f'{FOLDER_DATA}/{FOLDER_DATA}_{NEEDED_DATA}_Schema.json'
    output_file = f'{FOLDER_DATA}/{FOLDER_DATA}_{NEEDED_DATA}_Sheet.xlsx'
    process(inputs_file, schema_file, output_file)

if __name__ == "__main__":
    FOLDER_DATA = 'HNMU'
    NEEDED_DATA = 'Chunks'
    mainProcess(FOLDER_DATA)