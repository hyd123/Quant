import logging

import pandas as pd
import tensorflow as tf
import os
import json
import numpy as np
import tqdm


file_path = 'D:/ts_data_alpha'
X_path = 'D:/ts_data_alpha/X.csv'
Y_path = 'D:/ts_data_alpha/Y.csv'



def json2csv(data_path, X_path, Y_path):
    file_list = []
    for root, dirs, files in os.walk(data_path):
        for file in files:
            file_list.append(file)

    # get train data
    X_ = []
    Y_ = []
    for file in tqdm.tqdm(file_list):
        with open(os.path.join(data_path, file), 'r') as f:
            json_dic = json.load(f)
        for key in json_dic.keys():
            one_stock_feature = []
            one_stock_dic = json_dic[key]
            for stock_key in one_stock_dic.keys():
                if np.isnan(one_stock_dic[stock_key]).any():
                    value = 0
                else:
                    value = one_stock_dic[stock_key]
                if stock_key == 'label':
                    Y_.append(value)
                else:
                    one_stock_feature.append(value)
            X_.append(one_stock_feature)
    X_ = np.array(X_)
    Y_ = np.array(Y_)
    p_X_ = pd.DataFrame(X_)
    p_X_.replace([np.inf, -np.inf], np.nan, inplace=True)
    p_X_.fillna(p_X_.mean(), inplace=True)
    p_Y_ = pd.DataFrame(Y_)
    X_ = p_X_.values
    from sklearn.preprocessing import MinMaxScaler
    transformer = MinMaxScaler(feature_range=(0, 1))
    X_ = transformer.fit_transform(X_)
    p_X_ = pd.DataFrame(X_)
    p_X_.to_csv(X_path, index=False)
    p_Y_.to_csv(Y_path, index=False)


json2csv(file_path, X_path, Y_path)