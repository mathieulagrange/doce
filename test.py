# from tqdm import tqdm
# from math import sqrt
# from joblib import Parallel, delayed
# Parallel(n_jobs=1)(delayed(sqrt)(i**2) for i in tqdm(range(10)))



import explanes as exp
import numpy as np

config = exp.Config()

config.factor.task = ['id', 'time', 'vec', 'idBaseline', 'timeBaseline', 'vecBaseline']
config.factor.computeType = ['none', 'train', 'test']
config.factor.doing = [8]*3
# factors.textureSize = 200
# factors.embeddingSize = 128
# factors.batchSize = 2
print(config)

def show(setting, config):
  i=1
  size = np.power(10, config.factor.doing)
  print(size)
  a = np.zeros(size)
  a = a**a
  print(setting.describe())
  return 1

config.do([], show, jobs=1)

#
# for f in factors.settings():
#     print(f.describe())
#
#     previous = f.alternative('computeType', 'train', relative=False)
#     if previous:
#         print('     '+previous.getId(singleton=False))

# config = exp.Config()
# config.project.name = 'censeDaTOTO'
# config.project.description = 'domain adaptation part of the cense project'
# config.project.author = 'mathieu Lagrange'
# config.project.address = 'mathieu.lagrange@ls2n.fr'
#
# rootPath = '/Users/lagrange/drive/experiments/data/'
# config.path.input = rootPath+'local/'
# config.path.output = config.path.input
#
# config.path.input += config.project.name+'/'
# config.path.output += config.project.name+'/'
# config.path.processing = '/tmp/'+config.project.name+'/'
# config.makePaths()
