import pandas as pd
from train_v1_0_2 import GetModel
import numpy as np
from os.path import join
import os
# from tqdm import tqdm
# from tensorflow.python.keras.models import load_model
# from PIL import Image

from logging import StreamHandler, DEBUG, Formatter, FileHandler, getLogger
import glob
import pickle


# TODO: 訓練によりknnモデル、csvファイルは変更する
FILENAME = "./train/knn_model.pkl"
PATH_CSV = './input/train.csv'

logger = getLogger(__name__)


def run(result):
    log_fmt = Formatter('%(asctime)s %(name)s %(lineno)d [%(levelname)s][%(funcName)s] %(message)s')
    handler = StreamHandler()
    handler.setLevel('INFO')
    handler.setFormatter(log_fmt)
    logger.addHandler(handler)

    logger.info('start')

    with open(FILENAME, 'rb') as f:
        neigh = pickle.load(f)

    result = np.array(result)

    distance_test, neighbors_test = neigh.kneighbors(result)
    distance_test, neighbors_test = distance_test.tolist(), neighbors_test.tolist()

    # 最近傍の4データが入っているはず。学習時に近傍数は調整
    logger('neibors_test:{}'.format(neighbors_test))
    logger('neibors_test_type:{}'.format(type(neighbors_test)))

    # TODO: 調整
    logger.debug("train.csv読み込み開始")
    # columns: Image(ファイル名),Id(クラス名)
    data = pd.read_csv(PATH_CSV)
    logger.debug("train.csv読み込み完了")

    file_id_mapping = {k: v for k, v in zip(data.Image.values, data.Id.values)}

    preds_str = []
    for distance, neighbor_ in zip(distance_test, neighbors_test):
        sample_result = []
        sample_classes = []
        for d, n in zip(distance, neighbor_):
            # ファイルパスからファイル名を取得、辞書マップによりクラス名を取得
            # train_filesファイル（trainのときのファイル構成パスリスト）をpickleするか
            # ファイルの順番とファイル名さえわかればマッピングできる
            train_file = train_files[n].split(os.sep)[-1]
            class_train = file_id_mapping[train_file]
            sample_classes.append(class_train)
            sample_result.append((class_train, d))

        sample_result.sort(key=lambda x: x[1])
        sample_result = sample_result[:5]
        preds_str.append(" ".join(x[0] for x in sample_result))

    return preds_str[0]



if __name__ == "__main__":
    # 50次元のテストデータ
    data = [[ 3.95560324e-01, -3.32569405e-02,  1.51777402e-01,
        -1.21975750e-01, -9.69380364e-02, -6.25947565e-02,
        -1.19426154e-01,  9.19620022e-02,  2.29892910e-01,
        -4.54800278e-02, -1.66264288e-02, -2.26741750e-02,
        -6.67407736e-02,  4.42054421e-02, -1.22564390e-01,
         4.46661152e-02,  2.07357839e-01,  1.09907813e-01,
         1.83392633e-02,  2.75023937e-01,  1.65000651e-02,
        -3.90385580e-03, -1.75637081e-01,  1.39454808e-02,
        -1.79190651e-01, -1.25446573e-01,  5.48238307e-02,
        -1.88904762e-01,  1.20141599e-02,  8.56271684e-02,
        -2.69792795e-01, -1.37547851e-01, -1.19984902e-01,
        -9.63136554e-02,  1.00750942e-02,  8.97271484e-02,
         6.51583076e-02, -3.38751465e-01,  2.06905544e-01,
        -9.55970678e-03, -1.78422719e-01, -7.07809851e-02,
        -9.33320001e-02,  1.22171663e-01, -1.11689575e-01,
        -1.49035111e-01, -1.30135253e-01,  3.95974591e-02,
        -1.83908418e-01, -4.65764105e-03]]
    run(data)