import doce
import numpy as np
import tables as tb
import time

if __name__ == "__main__":
  doce.run.run()

# use case where:
#   - the results are stored on disk in a h5 sink
#   - one factor affects the size of the results vectors
#   - the metric does not operate on the same data, resulting on result vectors with different sizes per metric
#   - thank to the description capabilities of the h5 file format, some information about the metric can be stored

def set(args):
    experiment = doce.experiment.Experiment()
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
  h5 = tb.open_file(experiment.path.output, mode='a')
  sg = experiment.metric.addSettingGroup(h5, setting, metricDimension = {'mae':setting.nbRuns, 'duration':1}, settingEncoding = experiment._settingEncoding)

  tic = time.time()
  for r in range(setting.nbRuns):
    data = np.zeros((2, setting.datasetSize), dtype=np.float32)
    offset = setting.meanOffset*np.random.rand(1)
    data[0, :] = 1.0+offset
    data[1, :] = 0.1-offset

    reference = ((data[0, 0]-0.55)**2 + (data[1, 0]-0.55)**2)/2
    if setting.dataType == 'float':
      estimate = np.var(data)
    elif setting.dataType == 'double':
      estimate =  np.var(data, dtype=np.float64)

    # write to statically allocated array
    sg.mae[r] = [abs(reference - estimate)]
    # write to dynamically allocated array
    sg.mse.append([np.square(reference - estimate)])

  duration = time.time()-tic
  sg.duration[0] = duration
  h5.close()

## uncomment this to fine tune display of metrics
def display(experiment, settings):
    (data, desc, header)  = experiment.metric.get('mae', settings, experiment.path.output, settingEncoding = experiment._settingEncoding)

    print(header)
    print(desc)
    print(len(data))
