import doce
import time
import numpy as np
import tables as tb
from pathlib import Path

  # define the experiment
experiment = doce.Experiment(
  name = 'demo_h5',
  purpose = 'hello world of the doce package',
  author = 'john doe',
  address = 'john.doe@no-log.org',
)

# set acces paths (here only storage is needed)
experiment.set_path('output', '/tmp/'+experiment.name+'.h5')
experiment.set_path('archive', '/tmp/'+experiment.name+'archive.h5')
# set some non varying parameters (here the number of cross validation folds)
experiment.n_cross_validation_folds = 10
# set the plan (factor : modalities)
experiment.add_plan('plan',
  nn_type = ['cnn', 'lstm'],
  n_layers = np.arange(2, 10, 3),
  learning_rate = [0.001, 0.0001, 0.00001],
  dropout = [0, 1]
)
  # set the metrics
experiment.set_metric(
  name = 'accuracy',
  percent=True,
  higher_the_better= True,
  significance = True,
  precision = 4
  )

experiment.set_metric(
  name = 'acc_std',
  output = 'accuracy',
  func = np.std,
  percent=True,
  precision = 4
  )

experiment.set_metric(
  name = 'duration',
  higher_the_better= False
  ) 

def step(setting, experiment):
  # the accuracy  is a function of cnn_type, and use of dropout
  accuracy = (len(setting.nn_type)+setting.dropout+np.random.random_sample(experiment.n_cross_validation_folds))/6
  # duration is a function of cnn_type, and n_layers

  duration = len(setting.nn_type)+setting.n_layers+np.random.randn(experiment.n_cross_validation_folds)
  # storage of outputs (the string between _ and .npy must be the name of the metric defined in the set function)

  h5 = tb.open_file(experiment.path.output, mode='a')
  sg = experiment.add_setting_group(h5, setting, output_dimension = {'accuracy':experiment.n_cross_validation_folds})

  # write to statically allocated array
  for ai, a in enumerate(accuracy):
    sg.accuracy[ai] = a
  # write to dynamically allocated array
  sg.duration.append(duration)
  h5.close()

# invoke the command line management of the doce package
if __name__ == "__main__":
  doce.cli.main(experiment = experiment, func=step)