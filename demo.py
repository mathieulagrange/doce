import explanes as ex
import tqdm as tq
import numpy as np

import inspect

factors = ex.Factors()

factors.method = ['estFloat', 'estDouble', 'method3']
factors.datasetSize = np.array([1, 2, 4, 8])*100000
factors.meanOffset = np.array([0, 1, 2, 3, 4])*10

if type(inspect.getattr_static(factors, 'meanOffset')) is np.ndarray:
    print('true')
else:
    print('false')

nbRuns = 20
for setting in factors(): #
    nb=1
    print(setting.getId())

    # for _ in range(nbRuns):
    #     data = np.zeros((2, setting.datasetSize), dtype=np.float32)
    #     data[0, :] = 1.0+meanOffset*rand(1)
    #     data[1, :] = 0.1+meanOffset*rand(1)
    #
    #     reference = ((1-0.55)**2 + (0.1-0.55)**2)/2
    #
    #     if setting.method is 'estFloat':
    #         estimate = np.var(a)
    #     elif setting.method is 'estDouble':
    #         estimate =  np.var(data, dtype=np.float64)
