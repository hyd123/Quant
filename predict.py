import os
import json
from sklearn.metrics import roc_auc_score
from sklearn.metrics import mean_absolute_error
import matplotlib.pyplot as plt
import numpy as np
import tqdm

file_path = 'D:/ts_data_alpha'


def lr_train(X,Y):
    from sklearn.linear_model import LinearRegression
    lr = LinearRegression()
    lr.fit(X, Y)
    return lr

def xgboost_train(X, Y):
    import xgboost as xgb
    model = xgb.XGBRegressor(max_depth=5, n_estimators=500, min_child_weight=1, subsample=0.8,
                             colsample_bytree=0.8, gamma=0, reg_alpha=0, reg_lambda=1, learning_rate=0.1)
    model.fit(X, Y)
    return model

def load_data(data_path):
    file_list = []
    for root, dirs, files in os.walk(data_path):
        for file in files:
            file_list.append(file)

    # get train data
    X_ = []
    Y_= []
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
    # from sklearn.preprocessing import MinMaxScaler
    # transformer = MinMaxScaler(feature_range=(0, 1))
    # X_ = transformer.fit_transform(X_)
    train_num = int(len(X_) * 0.95)
    X_train = X_[:train_num]
    Y_train = Y_[:train_num]
    X_val = X_[train_num:]
    Y_val = Y_[train_num:]

    return X_train, X_val, Y_train, Y_val

X_train, X_val, Y_train, Y_val = load_data(file_path)

import torch
from torch import nn
import torch.nn.functional as F
from sklearn.metrics import accuracy_score


train_x = torch.tensor(X_train).to(torch.float32)
test_x = torch.tensor(X_val).to(torch.float32)
train_y = torch.tensor(Y_train).to(torch.float32)
test_y = torch.tensor(Y_val).to(torch.float32)


print(train_x.shape, train_y.shape)

from torch.utils.data import TensorDataset
from torch.utils.data import DataLoader

batch = 60000
train_ds = TensorDataset(train_x, train_y)
train_dl = DataLoader(train_ds, batch_size=batch, shuffle=True)

test_ds = TensorDataset(test_x, test_y)
test_dl = DataLoader(test_ds, batch_size=batch * 2)

class Model(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear_1 = nn.Linear(102, 100)
        self.linear_2 = nn.Linear(100, 30)
        self.linear_3 = nn.Linear(30, 3)
    def forward(self, x):
        x = x.view(x.size(0), -1)
        x = torch.relu(self.linear_1(x))
        x = torch.relu(self.linear_2(x))
        logits = self.linear_3(x)
        return logits    # 未激活的输出，叫做logits

def accuracy(out, yb):
    accuracy_score(y_true=yb, y_pred=out.argmax(1))
    return accuracy_score(y_true=yb, y_pred=out.argmax(1))

def get_model():
    model = Model()
    return model, torch.optim.Adam(model.parameters(), lr=1e-4)

loss_fn = torch.nn.CrossEntropyLoss()
model, opt = get_model()
print(model)

train_loss = []
train_acc = []

test_loss = []
test_acc = []

epochs = 30

for epoch in tqdm.tqdm(range(epochs + 1)):
    model.train()
    for xb, yb in train_dl:
        yb = yb.long()
        pred = model(xb)
        loss = loss_fn(pred, yb)

        loss.backward()
        opt.step()
        opt.zero_grad()
    if epoch % 1 == 0:
        model.eval()
        with torch.no_grad():
            train_epoch_loss = sum(loss_fn(model(xb), yb.long()) for xb, yb in train_dl)
            test_epoch_loss = sum(loss_fn(model(xb), yb.long()) for xb, yb in test_dl)
            acc_mean_train = np.mean([accuracy(model(xb), yb.long()) for xb, yb in train_dl])
            acc_mean_val = np.mean([accuracy(model(xb), yb.long()) for xb, yb in test_dl])
        train_loss.append(train_epoch_loss.data.item() / len(test_dl))
        test_loss.append(test_epoch_loss.data.item() / len(test_dl))
        train_acc.append(acc_mean_train)
        test_acc.append(acc_mean_val)
        template = ("epoch:{:2d}, 训练损失:{:.5f}, 训练准确率:{:.1f},验证损失:{:.5f}, 验证准确率:{:.1f}")

        print(template.format(epoch, train_epoch_loss.data.item() / len(test_dl), acc_mean_train * 100,
                              test_epoch_loss.data.item() / len(test_dl), acc_mean_val * 100))
print('训练完成')




#
# xgboost_model = xgboost_train(X_train, Y_train)
# #
# Y_pred = xgboost_model.predict(X_val)


from sklearn.metrics import accuracy_score, average_precision_score,precision_score,f1_score,recall_score

# print('------Accuracy------')
# print('Weighted precision', accuracy_score(Y_val, Y_pred))
#
# print('------Weighted------')
# print('Weighted precision', precision_score(Y_val, Y_pred, average='weighted'))
# print('Weighted recall', recall_score(Y_val, Y_pred, average='weighted'))
# print('Weighted f1-score', f1_score(Y_val, Y_pred, average='weighted'))
# print('------Macro------')
# print('Macro precision', precision_score(Y_val, Y_pred, average='macro'))
# print('Macro recall', recall_score(Y_val, Y_pred, average='macro'))
# print('Macro f1-score', f1_score(Y_val, Y_pred, average='macro'))
# print('------Micro------')
# print('Micro precision', precision_score(Y_val, Y_pred, average='micro'))
# print('Micro recall', recall_score(Y_val, Y_pred, average='micro'))
# print('Micro f1-score', f1_score(Y_val, Y_pred, average='micro'))


# n = range(len(Y_val))
# plt.plot(n, Y_pred, n, Y_val)
# plt.show()
#
# from scipy.stats import *
#
# r = pearsonr(Y_pred, Y_val)
# print('xgb predict')
# print(r[0])
# factor_list = ['pct_change', 'macd_dif', 'macd_dea', 'macd', 'kdj_k', 'kdj_d',
#                'kdj_j', 'rsi_6', 'rsi_12', 'rsi_24', 'boll_upper', 'boll_mid', 'boll_lower', 'cci']
# # factor_list = ['turnover_rate', 'turnover_rate_f', 'volume_ratio', 'pe', 'pe_ttm', 'pb',
# #                'ps', 'ps_ttm', 'dv_ratio', 'dv_ttm']
#
# for i in range(X_train.shape[1]):
#     factor = list(X_train[:,i])
#     print(factor_list[i])
#     r = pearsonr(factor, Y_train)
#     print(r[0])
