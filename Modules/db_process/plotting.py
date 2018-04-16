import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import mysql_interact as dbi
import numpy as np

matplotlib.rc('font', family='NanumBarunGothic')

F_naver_file_path = 'F_naver.txt'
naver_dict = {}
with open(F_naver_file_path, 'r') as naver_file:
    for line in naver_file:
        [key, val] = line.strip().split()
        naver_dict[key] = val
keys = naver_dict.keys()

F_NN_file_path = 'F_NN.txt'
nn_dict = {}
with open(F_NN_file_path, 'r') as nn_file:
    for line in nn_file:
        [key, val] = line.strip().split(':')
        key = key.replace(' ', '')
        nn_dict[key] = val if val != 'null' else None

dbi.init_db_conn()

whole_data = []
cnt = 0
missing_cnt = 0
for i in range (0, 10, 1):
    searches = dbi.select_columns_where(\
            'search', columns=['keyword', 'F_action', 'F_naver'], chopping=True)
    if searches == ():
        break

    for search in searches:
        if search[1] is not None:
            if search[1] != 'None' and search[2] != 'None':
                f_naver = 0
                f_nn = 0
                if search[0] in keys:
                    f_naver = naver_dict[search[0]]
                    try:
                        f_nn = nn_dict[search[0]]
                    except KeyError:
                        missing_cnt += 1
                        f_nn = None
                    f_nn = float(f_nn) if f_nn != None else None
                else:
                    f_naver = search[2]
                whole_data.append((search[0], float(search[1]), float(f_naver), f_nn))
                cnt += 1

dbi.exit_db_conn()

sorted_data = sorted(whole_data, key=lambda x: x[2])
words = [val for (val, _, _, _) in sorted_data]
F_action = [val for (_, val, _, _) in sorted_data]
F_naver = [val for (_, _, val, _) in sorted_data]
F_nn = [val for (_, _, _, val) in sorted_data]
#  F_nn, 'bo', 
plt.plot(range(len(words)), F_naver, 'go', F_action, 'ro', ms=2, alpha = 0.15)
plt.xticks(range(len(words)), words, rotation=50)
plt.savefig('{}_action.png'.format(F_NN_file_path[:-4]))

print('total: {}  | missing: {}'.format(cnt, missing_cnt))
