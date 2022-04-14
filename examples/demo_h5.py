import doce
import time
import numpy as np
import tables as tb
from pathlib import Path

# invoke the command line management of the doce package
if __name__ == "__main__":
  doce.cli.main()

# define the doce environnment
def set(args=None):
  # define the experiment
  experiment = doce.Experiment(
    name = 'demo_h5',
    purpose = 'hello world of the doce package',
    author = 'mathieu Lagrange',
    address = 'mathieu.lagrange@ls2n.fr',
  )

# set acces paths (here only storage is needed)
  experiment.setPath('output', '/tmp/'+experiment.name+'.h5')
  # set some non varying parameters (here the number of cross validation folds)
  experiment.n_cross_validation_folds = 10
  # set the plan (factor : modalities)
  experiment.addPlan('plan',
    nn_type = ['cnn', 'lstm'],
    n_layers = np.arange(2, 10, 3),
    learning_rate = [0.001, 0.0001, 0.00001],
    dropout = [0, 1]
  )
  # set the metrics
  experiment.setMetrics(
    # the average and the standard deviation of the accuracy are expressed in percents (+ specifies a higher-the-better metric)
    accuracy = ['mean%+', 'std%'],
    # the duration is averaged over folds (* requests statistical analysis, - specifies a lower-the-better metric)
    duration = ['mean*-']
  )
  return experiment

def step(setting, experiment):
  # the accuracy  is a function of cnn_type, and use of dropout
  accuracy = (len(setting.nn_type)+setting.dropout+np.random.random_sample(experiment.n_cross_validation_folds))/6
  # duration is a function of cnn_type, and n_layers

  duration = len(setting.nn_type)+setting.n_layers+np.random.randn(experiment.n_cross_validation_folds)
  # storage of outputs (the string between _ and .npy must be the name of the metric defined in the set function)

  h5 = tb.open_file(experiment.path.output, mode='a')
  sg = experiment.metric.addSettingGroup(h5, setting, metricDimension = {'accuracy':experiment.n_cross_validation_folds})

  # write to statically allocated array
  for ai, a in enumerate(accuracy):
    sg.accuracy[ai] = a
  # write to dynamically allocated array
  sg.duration.append(duration)

  h5.close()
