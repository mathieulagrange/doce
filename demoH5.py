import explanes as ex
import tqdm as tq
import numpy as np
import pandas as pd
import os

resultPath = '/tmp/results/'
if not os.path.exists(resultPath):
    os.makedirs(resultPath)

factors = ex.Factors()

factors.method = ['estFloat', 'estDouble']
factors.datasetSize = 1000*np.array([1, 2, 4, 8])
factors.meanOffset = 10**np.array([0, 1, 2, 3, 4])

metrics = ex.Metrics()

metrics.mae = ['mean', 'std']
metrics.mse = ['mean', 'std']

nbRuns = 20

settings = factors()
experimentResults = np.zeros((len(settings), len(metrics), nbRuns))

for s, setting in enumerate(settings):
    print(setting.getId())
    settingResults = np.zeros((len(metrics), nbRuns))

    for r in range(nbRuns):
        data = np.zeros((2, setting.datasetSize), dtype=np.float32)
        offset = setting.meanOffset*np.random.rand(1)
        data[0, :] = 1.0+offset
        data[1, :] = 0.1-offset

        reference = ((data[0, 0]-0.55)**2 + (data[1, 0]-0.55)**2)/2


        if setting.method is 'estFloat':
            estimate = np.var(data)
        elif setting.method is 'estDouble':
            estimate =  np.var(data, dtype=np.float64)
        settingResults[0, r] = abs(reference - estimate)
        settingResults[1, r] = np.square(reference - estimate)

        np.save(resultPath+setting.getId('hash'), settingResults)

    experimentResults[s, :, :] = settingResults

# reduce from in memory data
(table, columns) = metrics.reduce(settings, experimentResults)
df = pd.DataFrame(table, columns=columns)
print(df)
