from scipy.io import loadmat
import numpy as np

data = loadmat("C:\\Users\\dfial\\Documents\\_university\\3rd year 2\\PMA\\graph 360v 70t a0.001 estimulo2 prom_weight links 180.mat")
sorted(data.keys())
n = 360
val_matrix = np.zeros((n, n, 3))
link_matrix = np.zeros((n, n, 3))


val_matrix[:, :, 0] = data['vallag0']
val_matrix[:, :, 1] = data['vallag1']
val_matrix[:, :, 2] = data['vallag2']


link_matrix[:, :, 0] = data['linkLag0']
link_matrix[:, :, 1] = data['linkLag1']
link_matrix[:, :, 2] = data['linkLag2']


def links(matrix):
    for a in range(0, 3):
        for i in range(0, n):
            for j in range(0, n):
                if matrix[i, j, a] == 1:
                    print(i, j, a)

links(link_matrix)


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

# val_m= make_list(val_matrix)
# link_m= make_list(link_matrix)

# save_matrix( 'C:\\Users\\dfial\\Documents\\_university\\3rd year 2\\PMA\\val_m.txt', val_m)
# save_matrix( 'C:\\Users\\dfial\\Documents\\_university\\3rd year 2\\PMA\\link_m.txt', link_m)