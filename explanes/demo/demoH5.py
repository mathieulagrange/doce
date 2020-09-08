import numpy as np
import tables as tb
import time

# more complex case where:
#   - the results are stored on disk in a h5 sink
#   - one factor affects the size of the results vectors
#   - the metric does not operate on the same data, resulting on result vectors with different sizes per metric
#   - thank to the description capabilities of the h5 file format, some information about the metric can be stored
def set(experiment, args):
    experiment.project.name = 'demoH5'
    experiment.project.description = 'demonstration of explanes using H5'
    experiment.project.author = 'mathieu Lagrange'
    experiment.project.address = 'mathieu.lagrange@ls2n.fr'
    experiment.path.output = '/tmp/results.h5'

    experiment.factor.dataType = ['float', 'double']
    experiment.factor.datasetSize = 1000*np.array([1, 2, 4, 8])
    experiment.factor.meanOffset = 10**np.array([0, 1, 2, 3, 4])
    experiment.factor.nbRuns = [20, 40]

    experiment.metric.mae = ['mean', 'std']
    experiment.metric._description.mae = 'Mean absolute error'
    experiment.metric.mse = ['mean', 'std']
    experiment.metric._description.mse = 'Mean square error'
    experiment.metric.duration = ['']
    experiment.metric._unit.duration = 'seconds'
    experiment.metric._description.duration = 'time used to compute'

    return experiment

def step(setting, experiment):
    h5 = tb.open_file(experiment.path.processing, mode='a')
    sg = experiment.metric.h5addSetting(h5, setting,
        metricDimensions = [setting.nbRuns, setting.nbRuns, 1])

    tic = time.time()
    for r in range(setting.nbRuns):
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
        sg.mse[r] = np.square(reference - estimate)

    duration = time.time()-tic
    # in case of dynamic allocation
    # sg.duration.append([duration])
    sg.duration[0] = duration
    h5.close()

# def display(experiment, settings):
#     h5 = tb.open_file(experiment.path.processing, mode='a')
#     print(h5)
#     h5.close()
