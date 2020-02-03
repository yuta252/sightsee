import glob
from logging import StreamHandler, DEBUG, Formatter, FileHandler, getLogger
import os
from os.path import join
import pickle

import numpy as np
import pandas as pd

logger = getLogger(__name__)

def run(result, spotid, path_knn, path_csv):
    log_fmt = Formatter('%(asctime)s %(name)s %(lineno)d [%(levelname)s][%(funcName)s] %(message)s')
    handler = StreamHandler()
    handler.setLevel('INFO')
    handler.setFormatter(log_fmt)
    logger.addHandler(handler)

    path_classification = os.path.dirname(os.path.abspath(__file__))
    handler = FileHandler(os.path.join(path_classification, 'log/classification.py.log'), 'a')
    handler.setLevel('INFO')
    handler.setFormatter(log_fmt)
    logger.setLevel(DEBUG)
    logger.addHandler(handler)

    logger.info('start')

    # spot = User.objects.get(id=spotid)
    # path_knn = spot.knn_model

    with open(path_knn, 'rb') as f:
        neigh = pickle.load(f)
    logger.info('successfully load knn model')

    # reshapeデータ
    result = np.array(result)
    result = result.reshape(1, -1)

    distance_test, neighbors_test = neigh.kneighbors(result)
    distance_test, neighbors_test = distance_test.tolist(), neighbors_test.tolist()

    # 最近傍の4データ取得（学習時に取得データ数調整）
    logger.info('neibors_test:{}'.format(neighbors_test))
    logger.info('neibors_test_type:{}'.format(type(neighbors_test)))

    # columns: Image(ファイル名),Id(クラス名)
    # path_csv = spot.exhibit_csv
    data = pd.read_csv(path_csv)
    logger.info("successfully load csv file")

    train_files = data.Image.values.tolist()

    # result: 4タプル(推測クラス, 距離)の配列
    result_list = []
    preds_class = []
    for distance, neighbor_ in zip(distance_test, neighbors_test):
        for d, n in zip(distance, neighbor_):
            class_train = train_files[n].split(os.sep)[-2]
            result_list.append((class_train, d))

    result_list.sort(key=lambda x: x[1])
    result_list = result_list[:4]
    logger.info('inferrence result: {}'.format(result_list))

    for re in result_list:
        preds_class.append(re[0])
    # 結果の重複防止
    preds_class = set(preds_class)
    logger.info('preds_class: {}'.format(preds_class))

    return preds_class


if __name__ == "__main__":
    # 50次元のテストデータ
    data = [[0.090379998087883, -0.02304992265999317, 0.09324495494365692, 0.03659585490822792,
    -0.08478889614343643, 0.07788155972957611, -0.17538823187351227, -0.09224985539913177, 0.11496009677648544,
    0.059696298092603683, 0.015959976240992546, 0.15123695135116577, 0.1161128357052803, 0.08850878477096558,
    0.04640551283955574, 0.017030833289027214, -0.07481292635202408, 0.04273553937673569, -0.1365722268819809,
    -0.04039325565099716, -0.20203840732574463, 0.1545790582895279, 0.09156696498394012, 0.00681038573384285,
    0.31029212474823, 0.30691465735435486, -0.2853172719478607, 0.06589222699403763, -0.21532975137233734,
    -0.024044442921876907, 0.03281234949827194, 0.24716702103614807, 0.27094537019729614, 0.08241242170333862,
    -0.012147201225161552, 0.057617418467998505, -0.2344937026500702, 0.09834333509206772, -0.11049892753362656,
    0.01781706139445305, -0.03429834917187691, -0.1020512580871582, 0.14464731514453888, -0.1281920075416565,
    0.03599584102630615, 0.00722708972170949, 0.25041672587394714, 0.15752050280570984, -0.22756731510162354, -0.16859398782253265]]

    spotid = '1000000'
    spotid = int(spotid)
    path_knn = '/Users/nakano/webapp/sightsee/sightsee/images/infference/1000000/knn_model_1000000_20200_sVrsM2D.pkl'
    path_csv = '/Users/nakano/webapp/sightsee/sightsee/images/infference/1000000/csv_spot_1000000_202001_4gde1Zj.csv'
    run(data, spotid, path_knn, path_csv)