import time
import numpy as np
from pathlib import Path
import doce

# invoke the command line management of the doce package
if __name__ == "__main__":
  doce.cli.main()

# define the doce environnment
def set():
  # define the experiment
  experiment = doce.Experiment(
    name = 'demo',
    purpose = 'hello world of the doce package',
    author = 'john doe',
    address = 'john.doe@no-log.org',
  )
# set acces paths (here only storage is needed)
  experiment.set_path('output', '/tmp/'+experiment.name+'/', force=True)
  experiment.set_path('archive', '/tmp/'+experiment.name+'_archive/', force=True)
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
    precision = 10
    )

  experiment.set_metric(
    name = 'acc_std',
    output = 'accuracy',
    func = np.std,
    percent=True
    )

  experiment.set_metric(
    name = 'duration',
    lower_the_better= True
    ) 

  return experiment

def step(setting, experiment):
  # the accuracy  is a function of cnn_type, and use of dropout
  accuracy = (len(setting.nn_type)+setting.dropout+np.random.random_sample(experiment.n_cross_validation_folds))/6
  # duration is a function of cnn_type, and n_layers
  duration = len(setting.nn_type)+setting.n_layers+np.random.randn(experiment.n_cross_validation_folds)
  # storage of outputs (the string between _ and .npy must be the name of the metric defined in the set function)
  np.save(experiment.path.output+setting.identifier()+'_accuracy.npy', accuracy)
  np.save(experiment.path.output+setting.identifier()+'_duration.npy', duration)
