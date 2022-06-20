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
  # set some non varying parameters (here the number of cross validation folds)
  experiment.n_cross_validation_folds = 10
  # set the plan (factor : modalities)
  experiment.add_plan('plan',
    a = [True, False],
    b = [True, False],
    c = [True, False]
  )
  # set the metrics
  experiment.set_metric(name='m')
  return experiment

def step(setting, experiment):
    np.save(experiment.path.output+setting.identifier()+'_m.npy', np.random.random_sample(1))
