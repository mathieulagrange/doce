from explanes import Factors, Metrics
from tqdm import trange
from time import sleep
from pandas import DataFrame
import numpy as np

# simple case where:
#   - the results are stored in memory
#   - no factors affects the size of the results vectors
#   - the metrics operate on the same data

factors = Factors()

factors.dataType = ['float', 'double']
factors.datasetSize = 1000*np.array([1, 2, 4, 8])
factors.meanOffset = 10**np.array([0, 1, 2, 3, 4])

metrics = Metrics()

metrics.mae = ['mean', 'std']
metrics.mse = ['mean', 'std']

nbRuns = 20

settings = factors()
experimentResults = np.zeros((len(settings), len(metrics), nbRuns))

print('computing...')
with trange(len(settings)) as t:
    for s, setting in enumerate(settings):
        # print()
        t.set_description(setting.getId())
        settingResults = np.zeros((len(metrics), nbRuns))

        for r in range(nbRuns):
            data = np.zeros((2, setting.datasetSize), dtype=np.float32)
            offset = setting.meanOffset*np.random.rand(1)
            data[0, :] = 1.0+offset
            data[1, :] = 0.1-offset

            reference = ((data[0, 0]-0.55)**2 + (data[1, 0]-0.55)**2)/2

            if setting.dataType is 'float':
                estimate = np.var(data)
            elif setting.dataType is 'double':
                estimate =  np.var(data, dtype=np.float64)
            settingResults[0, r] = abs(reference - estimate)
            settingResults[1, r] = np.square(reference - estimate)
        sleep(0.1)
        t.update()
        experimentResults[s, :, :] = settingResults

print('done')
# reduce from in memory data
print('Results:')
(table, columns) = metrics.reduce(settings, experimentResults)
df = DataFrame(table, columns=columns)
print(df)
