import os
import tqdm
import json
file_path = 'D:/ts_data'

def change_label(data_path):
    file_list = []
    for root, dirs, files in os.walk(data_path):
        for file in files:
            file_list.append(file)

    for file in tqdm.tqdm(file_list):
        with open(os.path.join(data_path, file), 'r') as f:
            json_dic = json.load(f)
        for key in json_dic.keys():
            one_stock_dic = json_dic[key]
            one_stock_dic['label'] = one_stock_dic['label'] * 100
            json_dic[key] = one_stock_dic
        with open(os.path.join(data_path, file), 'w') as f:
            json.dump(json_dic, f)

change_label(file_path)