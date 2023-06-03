import logging

import pandas as pd
import tensorflow as tf
import os
import json
import numpy as np
import tqdm
from tensorflow.keras import datasets, layers, optimizers, Sequential
from tensorflow.keras.layers import Flatten
#


file_path = 'D:/ts_data_alpha'
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

    X_ = new_p_X.values
    Y_ = p_Y_.values
    train_num = int(len(X_) * 0.95)

    X_train = X_[:train_num]
    Y_train = Y_[:train_num]
    X_val = X_[train_num:]
    Y_val = Y_[train_num:]
    return X_train, X_val, Y_train, Y_val




def preprocess(x, y):
    x = tf.cast(x, dtype=tf.float32)
    y = tf.cast(y, dtype=tf.float32)
    return x, y





class CMLTV():
    def __init__(self, dim):
        logging.info('init CMLTV')
        self.class_num = 5
        self.gamma_w = 0.
        self.cls_w = 1.0
        self.ce_loss_w = 0.5
        self.gamma_loss_w = 0.
        self.cls_loss_w = 1.0
        self.cons_loss_w = 0.
        self.model_sturcture = [512, 256, 128, 64, 32]
        self.base = 2.0
        self.input_dim = dim
        self.model_inner = self._build_model()

    def _build_model(self):
        # r_model = Sequential([
        #     layers.Dense(self.model_sturcture[0], activation=tf.nn.relu),  # [b, 784] => [b, 256]
        #     layers.Dense(self.model_sturcture[1], activation=tf.nn.relu),  # [b, 256] => [b, 128]
        #     layers.Dense(self.model_sturcture[2], activation=tf.nn.relu),  # [b, 128] => [b, 64]
        #     layers.Dense(self.model_sturcture[3], activation=tf.nn.relu),  # [b, 64] => [b, 32]
        # ])
        # r_model.build(input_shape=([None, 28 * 28]))

        input_ = layers.Input(self.input_dim)
        hidden1 = layers.Dense(self.model_sturcture[0], activation=tf.nn.relu, name='hidden1')(input_)
        hidden2 = layers.Dense(self.model_sturcture[1], activation=tf.nn.relu, name='hidden2')(hidden1)
        hidden3 = layers.Dense(self.model_sturcture[2], activation=tf.nn.relu, name='hidden3')(hidden2)
        hidden4 = layers.Dense(self.model_sturcture[3], activation=tf.nn.relu, name='hidden4')(hidden3)
        hidden5 = layers.Dense(self.model_sturcture[4], activation=tf.nn.relu, name='hidden5')(hidden4)
        ziln_output = layers.Dense(3, activation=None)(hidden5)
        cls_logits = layers.Dense(self.class_num, activation=None)(hidden5)
        logits = tf.concat([ziln_output, cls_logits], axis=1)
        model = tf.keras.Model(inputs=[input_], outputs=[logits])
        model.summary()
        return model

    def get_logits(self, features):
        logits = self.model_inner(features)
        ziln_output, cls_logits = tf.split(logits, [3, int(self.class_num)], axis=1)

        pay_prob = tf.sigmoid(ziln_output[:, 0])
        alpha = tf.math.maximum(tf.math.softplus(ziln_output[:, 1]), tf.math.sqrt(tf.keras.backend.epsilon()))
        beta = tf.math.maximum(tf.math.softplus(ziln_output[:, 2]), tf.math.sqrt(tf.keras.backend.epsilon()))
        preds_gamma = pay_prob * (alpha / beta)
        # Compute cls logits
        # preds_cls = pay_prob * tf.reduce_sum(
        #     tf.nn.softmax(cls_logits) * tf.cast(int(self.base)**tf.range(self.class_num), tf.float32), axis=-1)
        preds_cls = pay_prob * tf.reduce_sum(
            tf.nn.softmax(cls_logits) * tf.cast(tf.range(self.class_num), tf.float32), axis=-1)
        proba = tf.reshape(self.gamma_w * preds_gamma + self.cls_w * preds_cls, [-1, 1])
        logits = tf.concat([ziln_output, cls_logits], axis=1)
        pred_dic = {
            'logits': logits,
            'proba': proba
        }
        return pred_dic

    def get_loss(self, logits, labels):
        import tensorflow_probability as tfp
        tfd = tfp.distributions

        # split ziln and logits
        ziln_output, cls_logits = tf.split(logits, [3, int(self.class_num)], axis=1)

        # get prob, alpha, beta
        pay_prob = tf.reshape(tf.math.sigmoid(ziln_output[:, 0]), [-1, 1])
        alpha = tf.math.maximum(tf.math.softplus(ziln_output[:, 1]),
                              tf.math.sqrt(tf.keras.backend.epsilon()))
        beta = tf.math.maximum(tf.math.softplus(ziln_output[:, 2]),
                              tf.math.sqrt(tf.keras.backend.epsilon()))

        # get 0,1 label
        label_01 = tf.cast(labels > 0, tf.float32)
        labels = tf.cast(labels, tf.float32)
        labels = tf.math.maximum(labels, 0.)

        safe_labels = label_01 * labels + (1 - label_01) * tf.ones_like(labels)
        ce_loss = tf.reduce_mean(tf.keras.backend.binary_crossentropy(
            target=label_01, output=pay_prob))

        gamma_loss = -tf.reduce_mean(label_01 * tfd.Gamma(concentration=alpha,
                                                          rate=beta).log_prob(safe_labels))

        # cls_labels = tf.math.minimum(
        #     tf.math.floor(tf.math.log(1 + tf.math.maximum(labels, 0.)) / tf.math.log(self.base)), self.class_num - 1)
        cls_labels = tf.math.minimum(tf.math.floor(labels), self.class_num - 1)

        onehot_cls_labels = tf.one_hot(indices=tf.cast(cls_labels, dtype=tf.int32),
                                       depth=self.class_num, axis=-1, dtype=tf.float32)
        #
        cls_loss = tf.reduce_mean(label_01 * tf.nn.softmax_cross_entropy_with_logits(
            labels=onehot_cls_labels, logits=cls_logits)) * tf.cast(
            tf.reduce_sum(tf.ones_like(labels), keepdims=True),
            tf.float32) / (1e-3 + tf.reduce_sum(label_01, keepdims=True))
        # cls_loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(
        #     labels=onehot_cls_labels, logits=cls_logits))
        # #
        # cls_loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(labels=onehot_cls_labels, logits=cls_logits))

        label_01_flat = tf.reshape(label_01, [-1])
        cons_mask = tf.expand_dims(label_01_flat, axis=1) * tf.expand_dims(1 - label_01_flat, axis=0)
        pred_miner = tf.expand_dims(
            ziln_output[:, 0], axis=1) - tf.expand_dims(ziln_output[:, 0], axis=0)
        cross_pred_miner = 2 * tf.reduce_mean(
            tf.reduce_mean(pred_miner * cons_mask, axis=-1), axis=-1, keepdims=True) \
                           * (tf.cast(tf.reduce_sum(tf.ones_like(label_01_flat), keepdims=True), tf.float32)**2
                              / (tf.cast(tf.reduce_sum(tf.ones_like(label_01_flat), keepdims=True), tf.float32)**2
                                 - tf.reduce_sum(label_01_flat, keepdims=True)**2
                                 - tf.reduce_sum(1 - label_01_flat, keepdims=True)**2))
        cons_loss = -tf.math.log(tf.math.sigmoid(cross_pred_miner))

        # compute loss
        loss = self.ce_loss_w * ce_loss + self.gamma_loss_w * gamma_loss + self.cls_loss_w * cls_loss + self.cons_loss_w * cons_loss
        return loss




def main():
    # (x, y), (x_test, y_test) = datasets.fashion_mnist.load_data()
    # print(x.shape, y.shape)
    # print(type(x), type(y))

    batch_size = 512
    x, x_test, y, y_test = load_data(X_path, Y_path)
    db = tf.data.Dataset.from_tensor_slices((x, y))
    db = db.map(preprocess).shuffle(20000).batch(batch_size)
    db_test = tf.data.Dataset.from_tensor_slices((x_test, y_test))
    db_test = db_test.map(preprocess).shuffle(10000).batch(batch_size)

    cmltv = CMLTV(np.shape(x)[1])
    # forward
    epoch = 30
    opt = tf.keras.optimizers.Adam(lr=1e-5)
    for epoch in tqdm.tqdm(range(epoch)):
        for step, (x, y) in enumerate(db):
            x = tf.reshape(x, [-1, np.shape(x)[1]])
            with tf.GradientTape() as tape:
                result = cmltv.get_logits(x)
                loss = cmltv.get_loss(result['logits'], y)
                y_pred = tf.math.maximum(tf.squeeze(result['proba']), 0.)
                y_label = tf.math.maximum(tf.cast(y, tf.float32), 0.)
                error = y_pred - y_label
                loss_mae = tf.reduce_mean(tf.abs(error))

            grads = tape.gradient(loss, cmltv.model_inner.trainable_variables)
            # # backward
            opt.apply_gradients(zip(grads, cmltv.model_inner.trainable_variables))

            if step % 100 == 0:
                print(epoch, step, "loss:", float(loss), float(loss_mae))

        # for step, (x, y) in enumerate(db_test):
        #     x = tf.reshape(x, [-1, 28*28])
        #     result = cmltv.get_logits(x)
        #     loss = cmltv.get_loss(result['logits'], y)
        #     y_pred = tf.math.maximum(tf.squeeze(result['proba']), 0.)
        #     y_label = tf.math.maximum(tf.cast(y, tf.float32), 0.)
        #     error = y_pred - y_label
        #     loss_mae = tf.reduce_mean(tf.abs(error))

        #
        # x_test = tf.reshape(x_test, [-1, np.shape(x_test)[1]])
        # pred_y = tf.math.maximum(tf.squeeze(cmltv.get_logits(x_test)['proba']), 0.)
        # error = tf.math.maximum(tf.cast(y_test, tf.float32), 0.) - pred_y
        # loss_mae = tf.reduce_mean(tf.abs(error))
        # print(epoch, "loss mae:", float(loss_mae))







if __name__ == '__main__':
    main()
