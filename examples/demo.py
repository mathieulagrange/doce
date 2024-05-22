import numpy as np
import doce

# define the doce environnment

# define the experiment
experiment = doce.Experiment(
  name = 'demo',
  purpose = 'hello world of the doce package',
  author = 'john doe',
  address = 'john.doe@no-log.org',
)
# set acces paths (here only storage is needed)
experiment.set_path('output', '/tmp/'+experiment.name+'/', force=True)
experiment.set_path('output2', '/tmp/'+experiment.name+'/output2/', force=True)
experiment.set_path('archive', '/tmp/'+experiment.name+'_archive/', force=True)
# set some non varying parameters (here the number of cross validation folds)
experiment.n_cross_validation_folds = 10

experiment._display.export_pdf = 'latex'
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

# custom metric function shall input an np.nd_array and output a scalar
def my_metric(data):
  return np.sum(data)

experiment.set_metric(
  name = 'acc_my_metric',
  output = 'accuracy',
  func = my_metric,
  percent=True
  )

experiment.set_metric(
  name = 'duration',
  path = 'output2',
  lower_the_better= True,
  precision = 2
  )

def step(setting, experiment):
  while 1:
    # the accuracy  is a function of cnn_type, and use of dropout
    accuracy = (len(setting.nn_type)+setting.dropout+np.random.random_sample(experiment.n_cross_validation_folds))/6
    # duration is a function of cnn_type, and n_layers
    duration = len(setting.nn_type)+setting.n_layers+np.random.randn(experiment.n_cross_validation_folds)
    # storage of outputs (the string between _ and .npy must be the name of the metric defined in the set function)
    np.save(experiment.path.output+setting.identifier()+'_accuracy.npy', accuracy)
    np.save(experiment.path.output2+setting.identifier()+'_duration.npy', -duration)

# invoke the command line management of the doce package
if __name__ == "__main__":
  doce.cli.main(experiment = experiment,
                func = step
                )
