import logging

import pandas as pd
import tensorflow as tf
import os
import json
import numpy as np
import tqdm


X_path = 'D:/ts_data_alpha/X.csv'
Y_path = 'D:/ts_data_alpha/Y.csv'

def load_data(X_path, Y_path):
    p_X_ = pd.read_csv(X_path)
    p_Y_ = pd.read_csv(Y_path)
    new_p_X = pd.DataFrame()
    for key in p_X_.keys():
        values = p_X_[key]
        stdvalue = np.std(list(values))
        if stdvalue > 0.02:
            new_p_X[key] = values

    print(len(list(new_p_X.keys())))

    # X_ = p_X_.values[:, :35]
    # Y_ = p_Y_.values
    # train_num = int(len(X_) * 0.95)
    #
    # X_train = X_[:train_num]
    # Y_train = Y_[:train_num]
    # X_val = X_[train_num:]
    # Y_val = Y_[train_num:]
    # return X_train, X_val, Y_train, Y_val

load_data(X_path, Y_path)