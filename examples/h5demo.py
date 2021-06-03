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

def set(userData):
  experiment = doce.Experiment(
    name = 'npyDemo',
    purpose = 'demonstration of npy storage of metrics',
    author = 'mathieu Lagrange',
    address = 'mathieu.lagrange@ls2n.fr',
    version = '0.1',
    host = ['pc-lagrange.irccyn.ec-nantes.fr']
  )

  experiment.setPath('output', '/tmp/'+experiment.name+'.h5')

  experiment.addPlan('plan',
    dataType= ['float', 'double'],
    datasetSize = 1000*np.array([1, 2, 4, 8], dtype=np.intc),
    meanOffset = 10.0**np.array([0, 1, 2]),
    nbRuns = 2000
    )

  experiment.setMetrics(
    mae = ['sqrt|mean-0*', 'std%-'],
    mse = ['mean*', 'std%'],
    duration = ['mean']
  )

  experiment._display.metricPrecision = 10
  experiment._display.highlight = True

  return experiment

def step(setting, experiment):
  h5 = tb.open_file(experiment.path.output, mode='a')
  sg = experiment.metric.addSettingGroup(h5, setting, metricDimension = {'mae':setting.nbRuns, 'duration':1})

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
# def display(experiment, settings):
#     (data, desc, header)  = experiment.metric.get('mae', settings, experiment.path.output, settingEncoding = experiment._settingEncoding)
#
#     print(header)
#     print(desc)
#     print(len(data))
