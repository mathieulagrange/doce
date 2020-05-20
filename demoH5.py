from explanes import Factors, Metrics
from tqdm import trange
from time import sleep
from pandas import DataFrame
import time
import numpy as np
import tables as tb


# more complex case where:
#   - the results are stored on disk in a h5 sink
#   - one factor affects the size of the results vectors
#   - the metrics does not operate on the same data, resulting on result vectors with different sizes per metric
#   - thank to the description capabilities of the h5 file format, some information about the metrics can be stored

resultPath = '/tmp/results.h5'

factors = Factors()

factors.dataType = ['float', 'double']
factors.datasetSize = 1000*np.array([1, 2, 4, 8])
factors.meanOffset = 10**np.array([0, 1, 2, 3, 4])
factors.nbRuns = [20, 40]

metrics = Metrics()
metrics.mae = ['mean', 'std']
metrics._description.mae = 'Mean absolute error'
metrics.mse = ['mean', 'std']
metrics._description.mse = 'Mean square error'
metrics.duration = ['']
metrics._unit.duration = 'seconds'
metrics._description.duration = 'time used to compute'

settings = factors([1, 0])

compute = True
if compute:
    print('computing...')
    h5 = tb.open_file(resultPath, mode='w')
    with trange(len(settings)) as t:
        for s, setting in enumerate(settings):
            t.set_description(setting.getId())
            sg = metrics.h5addSetting(h5, setting)

            tic = time.time()
            for r in range(settings.nbRuns):
                data = np.zeros((2, setting.datasetSize), dtype=np.float32)
                offset = setting.meanOffset*np.random.rand(1)
                data[0, :] = 1.0+offset
                data[1, :] = 0.1-offset

                reference = ((data[0, 0]-0.55)**2 + (data[1, 0]-0.55)**2)/2

                if setting.dataType is 'float':
                    estimate = np.var(data)
                elif setting.dataType is 'double':
                    estimate =  np.var(data, dtype=np.float64)
                sg.mae.append([abs(reference - estimate)])
                sg.mse.append([np.square(reference - estimate)])

            duration = time.time()-tic
            sg.duration.append([duration])
            # sleep(0.1-duration)
            t.update()
    h5.close()
    print('done')

print('Stored results:')
h5 = tb.open_file(resultPath, mode='r')
print(h5)
h5.close()
# reduce from h5 file
print('Results:')
(table, columns) = metrics.reduce(factors(), resultPath)
# print(columns)
# print(table)
df = DataFrame(table, columns=columns)
print(df)
