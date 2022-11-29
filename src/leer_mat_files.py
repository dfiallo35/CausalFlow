from scipy.io import loadmat
import numpy as np
from os import getcwd
from os.path import join


def make_list(input_matrix):
    matrix=[]
    for a in input_matrix:
        temp=[]
        for b in a:
            temp.append(list(b))
        matrix.append(temp)
    return matrix


def save_matrix(output_file, matrix):
    file = open(output_file, 'w')
    file.write(str(matrix))


def links(matrix, n):
    for a in range(0, 3):
        for i in range(0, n):
            for j in range(0, n):
                if matrix[i, j, a] == 1:
                    yield (i, j, a)


def load_matrix(input_file):
    data = loadmat(input_file)
    sorted(data.keys())

    # print(list(data['vallag0']))

    n = 360
    val_matrix = np.zeros((n, n, 3))
    link_matrix = np.zeros((n, n, 3))
    

    val_matrix[:, :, 0] = data['vallag0']
    val_matrix[:, :, 1] = data['vallag1']
    val_matrix[:, :, 2] = data['vallag2']


    link_matrix[:, :, 0] = data['linkLag0']
    link_matrix[:, :, 1] = data['linkLag1']
    link_matrix[:, :, 2] = data['linkLag2']

    return val_matrix, link_matrix


vl, lm= load_matrix(join(getcwd(), 'src', 'graphs', '100307detrend_estimulo2_Correlation.mat'))
# save_matrix(join(getcwd(),'src', 'graphs', 'ml.txt'), make_list(lm))
# save_matrix(join(getcwd(),'src', 'graphs', 'vl.txt'), make_list(vl))

# count=0
# for a in links(lm, 360):
#     count+=1
# print(count/2)

for a in links(lm, 360):
    print(lm[a[0], a[1]])



d= [[1,2,3,4], [5,6,7,8], [9,10,11,12], [13,14,15,16]]



