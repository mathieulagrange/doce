import explanes as exp
from tqdm import trange
from time import sleep
from pandas import DataFrame
import time
import numpy as np
import tables as tb

# TODO partial write
# check rewrite unlink metrics

# more complex case where:
#   - the results are stored on disk in a h5 sink
#   - one factor affects the size of the results vectors
#   - the metrics does not operate on the same data, resulting on result vectors with different sizes per metric
#   - thank to the description capabilities of the h5 file format, some information about the metrics can be stored
def main():

    config = exp.Config()
    config.project.name = 'demoH5'
    config.project.description = 'demonstration of explanes using H5'
    config.project.author = 'mathieu Lagrange'
    config.project.address = 'mathieu.lagrange@ls2n.fr'
    config.path.processing = '/tmp/results.h5'
    
    factors = exp.Factors()

    factors.dataType = ['float', 'double']
    factors.datasetSize = 1000*np.array([1, 2, 4, 8])
    factors.meanOffset = 10**np.array([0, 1, 2, 3, 4])
    factors.nbRuns = [20, 40]

    metrics = exp.Metrics()
    metrics.mae = ['mean', 'std']
    metrics._description.mae = 'Mean absolute error'
    metrics.mse = ['mean', 'std']
    metrics._description.mse = 'Mean square error'
    metrics.duration = ['']
    metrics._unit.duration = 'seconds'
    metrics._description.duration = 'time used to compute'


    reDo = True
    compute = True

    if compute:
        if reDo:
            writeMode = 'w'
        else:
            writeMode = 'a'
        settings = factors([1, 0])
        doComputing(settings, metrics, config.path.processing, writeMode)
        settings = factors([-1, 0])
        doComputing(settings, metrics, config.path.processing)

    print('Stored results:')
    h5 = tb.open_file(config.path.processing, mode='r')
    print(h5)
    h5.close()
    # reduce from h5 file
    print('Results:')
    (table, columns) = metrics.reduce(factors(), config.path.processing)
    # print(columns)
    # print(table)
    df = DataFrame(table, columns=columns)
    print(df)
    d = df.to_html()
    config.sendMail(d)

def doComputing(settings, metrics, resultPath, writeMode='a'):
    print('computing...')
    h5 = tb.open_file(resultPath, mode=writeMode)
    with trange(len(settings)) as t:
        for sIndex, setting in enumerate(settings):
            t.set_description(setting.getId())
            # set metricDimensions = [] to get dynamic allocation (will lead to file size expansion in case of repeated recomputation, use h5repack periodically in that case)
            sg = metrics.h5addSetting(h5, setting,
                metricDimensions = [settings.nbRuns, settings.nbRuns, 1])

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
                # in case of dynamic allocation
                # sg.mae.append([abs(reference - estimate)])
                # sg.mse.append([np.square(reference - estimate)])
                sg.mae[r] = abs(reference - estimate)
                sg.mse[t] = np.square(reference - estimate)

            duration = time.time()-tic
            # in case of dynamic allocation
            # sg.duration.append([duration])
            sg.duration[0] = duration
            # sleep(0.1-duration)
            t.update()
    h5.close()
    print('done')

if __name__ == '__main__':
    main()
