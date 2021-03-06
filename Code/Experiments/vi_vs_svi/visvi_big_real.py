import numpy as np
import time
from sklearn.preprocessing import StandardScaler
from sklearn.datasets import load_svmlight_file

from vi_vs_svi_natural import run_methods
from GP.covariance_functions import SquaredExponential

file_name = 'really_big_real'
model_params = np.array([3.0, 2.0, 1.0])
model_covariance_obj = SquaredExponential(model_params)
ind_inputs_num = 1000
# max_iter = 10
batch_size = 2000

x_tr, y_tr = load_svmlight_file('../../../../Programming/DataSets/Regression/yearprediction(463715, 90).txt')
data_name = 'yearprediction'
title = 'Year Prediction, n = 100000, d = 90, m=1000'

# print(x_tr.shape)
x_tr = x_tr.T
x_tr = x_tr.toarray()
scaler = StandardScaler()
x_tr = scaler.fit_transform(x_tr)
y_tr = scaler.fit_transform(y_tr)

# print(x_tr.shape)
num = 100000
test_num = int(num/10)
x_tr = (x_tr + 1) / 2
y_tr = y_tr.reshape((y_tr.size, 1))
x_test = x_tr[:, num:num+test_num]
y_test = y_tr[num:num+test_num, :]
y_tr = y_tr[:num, :]
x_tr = x_tr[:, :num]

print(x_tr.shape)

lbfgsb_options = {'maxiter': 2, 'disp': True, 'mydisp': True}
sg_options = {'maxiter': 20, 'batch_size': batch_size, 'print_freq': 1, 'step0': 1e-6, 'gamma': 0.51}
optimizer_options = [sg_options, lbfgsb_options]

start = time.time()
run_methods(x_tr, y_tr, x_test, y_test, model_params, optimizer_options, file_name, ind_inputs_num, title, True)
print(time.time() - start)