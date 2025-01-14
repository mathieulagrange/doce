import numpy as np
import doce

# define the doce environnment

# define the experiment
experiment = doce.Experiment(
  name = '',
  purpose = '',
  author = '',
  address = '',
)
# set acces paths (here only storage is needed)
experiment.set_path('output', '/tmp/'+experiment.name+'/', force=True)

# set the plan (factor : modalities)
experiment.add_plan('plan',
  
)

experiment.set_metric(
  name = '',
  percent=True,
  higher_the_better= True,
  significance = True,
  precision = 10
  )

def step(setting, experiment):
 
  np.save(experiment.path.output+setting.identifier()+experiment.metric_delimiter+'.npy', )
 
# invoke the command line management of the doce package
if __name__ == "__main__":
  doce.cli.main(experiment = experiment,
                func = step
                )
