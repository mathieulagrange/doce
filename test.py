


import explanes as exp
import numpy as np

factors = exp.Factors()

factors.task = ['id', 'time', 'vec', 'idBaseline', 'timeBaseline', 'vecBaseline']
factors.computeType = ['none', 'train', 'test']
factors.doing = 10*np.arange(10)
# factors.textureSize = 200
# factors.embeddingSize = 128
# factors.batchSize = 2

print(factors.getFactorNames())

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