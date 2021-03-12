import time
import random
import explanes as el

e=el.experiment.Experiment()
e.factor.factor1=[1, 3]
e.factor.factor2=[2, 5]

# this function displays the sum of the two modalities of the current setting
def myFunction(setting, experiment):
  time.sleep(random.uniform(0, 2))
  print('{}+{}={}'.format(setting.factor1, setting.factor2, setting.factor1+setting.factor2))

# sequential execution of settings
e.do([], myFunction, nbJobs=1, progress=False)
# arbitrary order execution of settings due to the parallelization
e.do([], myFunction, nbJobs=3, progress=False)
