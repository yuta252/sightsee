import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import seaborn as sns
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow.python.keras import backend as K
from tensorflow.python.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.python.keras.layers import Input, Dense, Dropout, Lambda, Convolution2D, MaxPooling2D, Flatten
from tensorflow.python.keras.losses import categorical_crossentropy
from tensorflow.python.keras.callbacks import ModelCheckpoint, EarlyStopping
from tensorflow.python.keras.applications import MobileNetV2
from tqdm import tqdm

from collections import defaultdict
import datetime
from logging import StreamHandler, DEBUG, Formatter, FileHandler, getLogger
import os
from os.path import join

logger = getLogger(__name__)

# Define parameter
# TODO: batch_sizeの調整：stetps_per_epochも修正
batch_size = 32
embedding_dim = 50
image_size = 224
# TO DO : ファイルパス変更
path_base = '../input/sightsee/'
path_train = join(path_base, 'train')
path_test = join(path_base, 'test')
path_csv = join(path_base, 'result_tmp/csv', 'train_20200116_125145.csv')

now = datetime.datetime.now()
path_model_checkpoint = join(path_base, 'triplet_chkpt_{}.hdf5'.format(now.strftime('%Y%m%d_%H%M%S')))
# path_model_trip = join(path_base, 'triplet_{}.hdf5'.format(now.strftime('%Y%m%d_%H%M%S')))
path_model_emb = join(path_base, 'result_tmp/hdf5', 'embedding_{}.hdf5'.format(now.strftime('%Y%m%d_%H%M%S')))
# path_tfmodel_trip = join(path_base, 'triplet_{}.tflite'.format(now.strftime('%Y%m%d_%H%M%S')))
path_tfmodel_emb = join(path_base, 'result_tmp/tflite', 'embedding_{}.tflite'.format(now.strftime('%Y%m%d_%H%M%S')))


class sample_gen(object):
    def __init__(self, file_class_mapping):
        # {filepath : class}の辞書配列
        self.file_class_mapping= file_class_mapping
        # {class : filepath}の辞書配列
        self.class_to_list_files = defaultdict(list)
        # filepathの配列
        self.list_all_files = list(file_class_mapping.keys())
        # filepathの総数
        self.range_all_files = list(range(len(self.list_all_files)))

        for file, class_ in file_class_mapping.items():
            self.class_to_list_files[class_].append(file)

        # クラスの配列（重複なし）
        self.list_classes = list(set(self.file_class_mapping.values()))
        # クラス数
        self.range_list_classes= range(len(self.list_classes))
        # 各クラス数の比率配列
        self.class_weight = np.array([len(self.class_to_list_files[class_]) for class_ in self.list_classes])
        self.class_weight = self.class_weight/np.sum(self.class_weight)

    def get_sample(self):
        # クラス数の比率により1つクラスを選択し、クラスの中からランダムにexamples_class_idxを2つ抽出
        class_idx = np.random.choice(self.range_list_classes, 1, p=self.class_weight)[0]
        examples_class_idx = np.random.choice(range(len(self.class_to_list_files[self.list_classes[class_idx]])), 2)

        positive_example_1, positive_example_2 = \
            self.class_to_list_files[self.list_classes[class_idx]][examples_class_idx[0]],\
            self.class_to_list_files[self.list_classes[class_idx]][examples_class_idx[1]]
        positive_class = self.list_classes[class_idx]

        negative_example = None
        while negative_example is None or self.file_class_mapping[negative_example] == \
                self.file_class_mapping[positive_example_1]:
            negative_example_idx = np.random.choice(self.range_all_files, 1)[0]
            negative_example = self.list_all_files[negative_example_idx]
            negative_class = self.file_class_mapping[negative_example]

        # positive_example_1 = os.path.join(self.list_classes[class_idx], positive_example_1)
        # positive_example_2 = os.path.join(self.list_classes[class_idx], positive_example_2)

        return positive_example_1, negative_example, positive_example_2, positive_class, negative_class


def read_and_resize(filepath):
    im = Image.open((filepath)).convert('RGB')
    im = im.resize((image_size, image_size))
    return np.array(im, dtype="float32")


def augment(im_array):
    if np.random.uniform(0, 1) > 0.9:
        im_array = np.fliplr(im_array)
    return im_array

def gen(triplet_gen):
    while True:
        list_positive_examples_1 = []
        list_negative_examples = []
        list_positive_examples_2 = []

        for i in range(batch_size):
            positive_example_1, negative_example, positive_example_2, positive_class, negative_class = triplet_gen.get_sample()
            # path_pos1 = join(path_train, positive_class, positive_example_1)
            # path_neg = join(path_train, negative_class, negative_example)
            # path_pos2 = join(path_train, positive_class, positive_example_2)
            path_pos1 = positive_example_1
            path_neg = negative_example
            path_pos2 = positive_example_2

            positive_example_1_img = read_and_resize(path_pos1)
            negative_example_img = read_and_resize(path_neg)
            positive_example_2_img = read_and_resize(path_pos2)

            positive_example_1_img = augment(positive_example_1_img)
            negative_example_img = augment(negative_example_img)
            positive_example_2_img = augment(positive_example_2_img)

            list_positive_examples_1.append(positive_example_1_img)
            list_negative_examples.append(negative_example_img)
            list_positive_examples_2.append(positive_example_2_img)

        A = np.array(list_positive_examples_1)
        B = np.array(list_positive_examples_2)
        C = np.array(list_negative_examples)

        label = None

        yield ({'anchor_input': A, 'positive_input': B, 'negative_input': C}, label)


# define Triplet loss
def triplet_loss(inputs, dist='sqeuclidean', margin='maxplus'):
    anchor, positive, negative = inputs
    positive_distance = K.square(anchor - positive)
    negative_distance = K.square(anchor - negative)

    if dist == 'euclidean':
        positive_distance = K.sqrt(K.sum(positive_distance, axis=-1, keepdims=True))
        negative_distance = K.sqrt(K.sum(negative_distance, axis=-1, keepdims=True))
    elif dist == 'sqeuclidean':
        positive_distance = K.sum(positive_distance, axis=-1, keepdims=True)
        negative_distance = K.sum(negative_distance, axis=-1, keepdims=True)
    loss = positive_distance - negative_distance
    if margin == 'maxplus':
        loss = K.maximum(0.0, 1 + loss)
    elif margin == 'softplus':
        loss = K.log(1 + K.exp(loss))
    return K.mean(loss)

def triplet_loss_np(inputs, dist='sqeuclidean', margin='maxplus'):
    anchor, positive, negative = inputs
    positive_distance = np.square(anchor - positive)
    negative_distance = np.square(anchor - negative)
    if dist == 'euclidean':
        positive_distance = np.sqrt(np.sum(positive_distance, axis=-1, keepdims=True))
        negative_distance = np.sqrt(np.sum(negative_distance, axis=-1, keepdims=True))
    elif dist == 'sqeuclidean':
        positive_distance = np.sum(positive_distance, axis=-1, keepdims=True)
        negative_distance = np.sum(negative_distance, axis=-1, keepdims=True)

    if margin == 'maxplus':
        loss = np.maximum(0.0, 1 + loss)
    elif margin == 'softplus':
        loss = np.log(1 + K.exp(loss))
    return np.mean(loss)


def GetModel():
    base_model = MobileNetV2(input_shape=(224, 224, 3), weights='imagenet', include_top=False, pooling='max')
    for layer in base_model.layers:
        layer.trainable = False

    x = base_model.output
    x = Dropout(0.6)(x)
    x = Dense(embedding_dim)(x)
    x = Lambda(lambda x: K.l2_normalize(x, axis=1))(x)
    embedding_model = Model(base_model.input, x, name='embedding')

    input_shape = (image_size, image_size, 3)
    anchor_input = Input(input_shape, name='anchor_input')
    positive_input = Input(input_shape, name='positive_input')
    negative_input = Input(input_shape, name='negative_input')
    anchor_embedding = embedding_model(anchor_input)
    positive_embedding = embedding_model(positive_input)
    negative_embedding = embedding_model(negative_input)

    inputs = [anchor_input, positive_input, negative_input]
    outputs = [anchor_embedding, positive_embedding, negative_embedding]

    triplet_model = Model(inputs, outputs)
    triplet_model.add_loss(K.mean(triplet_loss(outputs)))

    return embedding_model, triplet_model


# plot graph
def eva_plot(History, epoch):
    plt.figure(figsize=(20, 10))
    sns.lineplot(range(1, epoch+1), History.history['loss'], label='Train loss')
    sns.lineplot(range(1, epoch+1), History.history['val_loss'], label='Test loss')
    plt.legend(['train', 'validation'], loc='upper left')
    plt.ylabel('loss')
    plt.xlabel('epoch')
    plt.title('Loss Graph')
    plt.show()


def main():
    log_fmt = Formatter('%(asctime)s %(name)s %(lineno)d [%(levelname)s][%(funcName)s] %(message)s')
    handler = StreamHandler()
    handler.setLevel('INFO')
    handler.setFormatter(log_fmt)
    logger.addHandler(handler)

    #handler = FileHandler(path_base + 'result_tmp/train.py.log', 'a')
    #handler.setLevel(DEBUG)
    #handler.setFormatter(log_fmt)
    #logger.setLevel(DEBUG)
    #logger.addHandler(handler)

    logger.info('start')

    # TODO : 変更（ファイル名　ラベル対応表の読み込み）
    data = pd.read_csv(path_csv)
    train, test = train_test_split(data, train_size=0.7, random_state=1337)
    file_id_mapping_train = {k: v for k, v in zip(train.Image.values, train.Id.values)}
    file_id_mapping_test = {k: v for k, v in zip(test.Image.values, test.Id.values)}
    gen_tr = gen(sample_gen(file_id_mapping_train))
    gen_te = gen(sample_gen(file_id_mapping_test))

    checkpoint = ModelCheckpoint(path_model_checkpoint, monitor='loss', verbose=1, save_best_only=True, mode='min')
    early = EarlyStopping(monitor="val_loss", mode="min", patience=2)
    callbacks_list = [checkpoint, early]

    # Installation of Resnet50 weight to keras
    embedding_model, triplet_model = GetModel()
    # show layers
    for i, layer in enumerate(embedding_model.layers):
        print(i, layer.name, layer.trainable)

    # Trainable adjusting
    # for layer in embedding_model.layers[178:]:
    #     layer.trainable = True
    # for layer in embedding_model.layers[:178]:
    #     layer.trainable = False

    # triplet_model.compile(loss=None, optimizer=Adam(0.01))
    # history = triplet_model.fit_generator(gen_tr, validation_data=gen_te, epochs=4, verbose=1, workers=4, \
    #     steps_per_epoch=200, validation_steps=20, use_multiprocessing=True)

    # show train and validation loss plot
    # eva_plot(history, 4)

    # TODO: 凍結する層の調整 徐々に凍結してパラメータ調整
    for layer in embedding_model.layers[72:]:
        layer.trainable = True
    for layer in embedding_model.layers[:72]:
        layer.trainable = False
        # Batch Normalization
        if "bn" in layer.name:
            layer.trainable = True


    triplet_model.compile(loss=None, optimizer=Adam(lr=0.0001))
    # use_multiprocessing=Falseにすることでデッドロック回避
    history = triplet_model.fit_generator(gen_tr, validation_data=gen_te, epochs=4, verbose=1, workers=1, \
        steps_per_epoch=6, validation_steps=2, use_multiprocessing=False)

    logger.info('train_loss:{}'.format(history.history['loss']))
    logger.info('val_loss:{}'.format(history.history['val_loss']))

    # Linux環境では消す
    # eva_plot(history, 4)

    # embedding_modelの保存 各事業所ごとのknnで読み込む
    embedding_model.save(path_model_emb)

    # tensorflow liteのtfliteファイルへの変換
    # tensroflow-gpuの場合、attribute error発生
    # converter2 = tf.lite.TFLiteConverter.from_keras_model(embedding_model)
    # tflite_model2 = converter2.convert()

    # logger.info('before save tfmodel')
    # with open(path_tfmodel_emb, mode="wb") as f:
    #     f.write(tflite_model2)
    # logger.info('tfmodel for embedding saved successfully')

    logger.info('end')
if __name__ == "__main__":
    main()