import doce
import time
import numpy as np
from pathlib import Path

# invoke the command line management of the doce package
if __name__ == "__main__":
  doce.cli.main()

# define the doce environnment
def set(args=None):
  # define the experiment
  experiment = doce.Experiment(
    name = 'factor_addition',
    purpose = 'factor addition demo of the doce package',
    author = 'mathieu Lagrange',
    address = 'mathieu.lagrange@ls2n.fr',
  )
  # set acces paths (here only storage is needed)
  experiment.setPath('output', '/tmp/'+experiment.name+'/')
  # set some non varying parameters (here the number of cross validation folds)
  experiment.n_cross_validation_folds = 10
  # set the plan (factor : modalities)
  experiment.addPlan('plan',
    nn_type = ['cnn', 'lstm'],
    dropout = [0, 1]
  )
  experiment.default(plan='plan', factor='dropout', modality=0)
  # set the metrics
  experiment.setMetrics(
    accuracy = ['mean'],
  )
  return experiment

def step(setting, experiment):
  np.save(experiment.path.output+setting.id()+'_accuracy.npy', 0)
