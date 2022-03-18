import doce
import time
import numpy as np
from pathlib import Path

# invoke the command line managment of the doce package
if __name__ == "__main__":
  doce.cli.main()

# define the doce environnment
def set(args):
  # define the experiment
  experiment = doce.Experiment(
    name = 'hello',
    purpose = 'hello world of the doce package',
    author = 'mathieu Lagrange',
    address = 'mathieu.lagrange@ls2n.fr',
  )
  # set acces paths (here only storage is needed)
  experiment.setPath('output', '/tmp/'+experiment.name+'/')
  # set the plan (factor : modalities)
  experiment.addPlan('plan',
    dnn_type = ['cnn', 'lstm'],
    n_layers = np.arange(2, 10, 3),
    learning_rate = [0.001, 0.0001],
    dropout = [0, 1]
    )
  # set some non varying parameters (here the number of cross validation folds)
  experiment.n_cross_validation_folds = 10
  # set the metrics
  experiment.setMetrics(
    # the average and the standard deviation of the accuracy are expressed in percents
    accuracy = ['mean%', 'std%'],
    # the likelihood is measured by considering the root mean square
    classification_error = ['sqrt|mean|square*-'],
    duration = ['mean*']
  )

  return experiment

def step(setting, experiment):
  accuracy = np.zeros((experiment.n_cross_validation_folds))
  classification_error = np.zeros((experiment.n_cross_validation_folds))
  duration = np.zeros((experiment.n_cross_validation_folds))

  np.save(experiment.path.output+setting.id()+'_accuracy.npy', accuracy)
  np.save(experiment.path.output+setting.id()+'classification_error.npy', classification_error)
  np.save(experiment.path.output+setting.id()+'_duration.npy', duration)
