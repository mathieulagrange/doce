import explanes

factors = Factors()

factors.method = ['method1', 'method2', 'method3']
factors.parameter1 = [0, 1, 2, 3, 4]*10
factors.parameter2 = [0, 1, 2]*1000

nbRuns = 100

for setting in factors(): #
  #print('textureSize %i' % ee.textureSize)
  print(setting.getId())


def method1(p1, p2):
    return pow(p1, p2)+rand(1)

def method2(p1, p2):
    return p1**p2+rand(1)

def method3(p1, p2):
    n = 1
    for i in range(p2):
        n=p1*n
    return n+rand(1)
