import explanes as ex
import tqdm as tq
import numpy as np
import pandas as pd

factors = ex.Factors()

factors.method = ['estFloat', 'estDouble']
factors.datasetSize = np.array([1, 2, 4, 8])*10#0000
factors.meanOffset = np.array([0, 1, 2, 3, 4])*10

metrics = ex.Metrics()

metrics.mae = ['mean', 'std']
metrics.mse = ['mean', 'std']

nbRuns = 20

settings = factors([0, -1, 0])
results = np.zeros((len(settings), len(metrics), nbRuns))

for s, setting in enumerate(settings):
    print(setting.getId())

    for r in range(nbRuns):
        data = np.zeros((2, setting.datasetSize), dtype=np.float32)
        data[0, :] = 1.0+setting.meanOffset*np.random.rand(1)
        data[1, :] = 0.1-setting.meanOffset*np.random.rand(1)

        reference = ((data[0, 0]-0.55)**2 + (data[1, 0]-0.55)**2)/2


        if setting.method is 'estFloat':
            estimate = np.var(data)
        elif setting.method is 'estDouble':
            estimate =  np.var(data, dtype=np.float64)

        results[s, 0, r] = abs(reference - estimate)
        results[s, 1, r] = np.square(reference - estimate)


(table, columns) = metrics.reduce(settings, results)
df = pd.DataFrame(table, columns=columns)
print(df)
