import doce
import numpy as np

# define the experiment
experiment = doce.Experiment(
  name = 'demo_multiple_plan',
  purpose = 'using multple plans using the doce package',
  author = 'mathieu Lagrange',
  address = 'mathieu.lagrange@ls2n.fr',
)
# set acces paths (here only storage is needed)
experiment.set_path('output', '/tmp/'+experiment.name+'/', force=True)

# optionally have shared factors
shared_factors = {'dataset': ['d1', 'd2', 'd3']}

# set the "svm" plan
experiment.add_plan('svm',
  **shared_factors,
  classifier = ['svm'],
  c = [1., 0.1, 0.01]
)
# set the "deep" plan
experiment.add_plan('deep',
  **shared_factors,
  classifier = ['cnn', 'lstm'],
  n_layers = [2, 4, 8],
  dropout = [False, True]
)
experiment.set_metric(
  name = 'accuracy',
  percent=True,
  higher_the_better= True,
  significance = True
)


def step(setting, experiment):
  # the accuracy  is a function of cnn_type, and use of dropout
  if setting.classifier == 'svm':
    accuracy = setting.c*np.random.random_sample(10)/6
  else:
    accuracy = (len(setting.classifier)+setting.dropout+np.random.random_sample(10))/6
  np.save(experiment.path.output+setting.identifier()+'_accuracy.npy', accuracy)

# invoke the command line management of the doce package
if __name__ == "__main__":
  doce.cli.main(experiment = experiment, func=step)
