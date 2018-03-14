import os
import sys
import math
import time
import random
import numpy as np
import pandas as pd
import tensorflow as tf
import matplotlib.pyplot as plt
import lib.dataset as dataset
import lib.network as network
import lib.path as path
import lib.utils as utils
from datetime import datetime

from sklearn.model_selection import train_test_split


if __name__ == '__main__':

    def save_loss(loss_arr, loss_type):
        save_dir = net.get_epoch_dir()
        np.save("{}/{}_loss.npy".format(save_dir, loss_type), loss_arr)
        net.saver.save(net.sess, "{}/model.ckpt".format(save_dir))
        plt.plot(np.array(loss_arr)[-1])
        plt.savefig("{}/plot_{}_loss.png".format(save_dir, loss_type),
                    bbox_inches='tight')
        plt.close()

    # get preprocessed data
    data_all, label_all = dataset.get_preprocessed_dataset()

    # split into training and test set
    X_train, X_test, y_train, y_test = train_test_split(  # shuffled
        data_all, label_all, test_size=0.1)
    # split trainig and  validation set
    X_train, X_val, y_train, y_val = train_test_split(  # shuffled
        X_train, y_train, test_size=0.1)

    # init network
    net = network.Network()

    print("training loop")
    # train network
    train_loss, val_loss, test_loss = [], [], []
    for e in range(net.epoch_count):
        t_start = time.time()  # timer for epoch
        net.create_epoch_dir()

        # training and validaiton loops
        try:
            # split traning and validation set into batchs
            X_train_batchs, y_train_batchs = dataset.get_suffeled_batchs(
                X_train, y_train, net.batch_size)

            X_val_batchs, y_val_batchs = dataset.get_suffeled_batchs(
                X_val, y_val, net.batch_size)

            val_interval = math.ceil(len(X_train_batchs)/len(X_val_batchs))
            print("training: {}({}), validation: {}({}), interval:{})" .format(
                len(X_train), len(X_train_batchs), len(X_val), len(X_val_batchs), val_interval))

            # train step
            counter = 0
            epoch_train_loss, epoch_val_loss = [], []
            while X_train_batchs and y_train_batchs:
                counter += 1
                if X_val_batchs and counter >= val_interval:
                    counter = 0
                    X = X_val_batchs.popleft()
                    y = y_val_batchs.popleft()
                    epoch_val_loss.append(net.step(X, y, 'val'))
                else:
                    X = X_train_batchs.popleft()
                    y = y_train_batchs.popleft()
                    epoch_train_loss.append(net.step(X, y, 'train'))
            train_loss.append(epoch_train_loss)
            val_loss.append(epoch_val_loss)

        except KeyboardInterrupt:
            print("training quit by user after %d seconds" %
                  (time.time()-t_start))
            train_loss.append(epoch_train_loss)
            val_loss.append(epoch_val_loss)
            save_loss(train_loss, 'train')
            save_loss(val_loss, 'val')
            exit()

        print("epoch %d took %d seconds to train" % (e, time.time()-t_start))
        save_loss(train_loss, 'train')
        save_loss(val_loss, 'val')

    # split test set into batchs
    X_test_batchs, y_test_batchs = dataset.get_suffeled_batchs(
        X_test, y_test, net.batch_size)

    print("testing network")
    # test network
    while X_test_batchs and y_test_batchs:
        X = X_test_batchs.popleft()
        y = y_test_batchs.popleft()
        test_loss.append(net.step(X, y, 'test'))
    save_loss(test_loss, 'test')
