import explanes

nbFactors = 4
nbModalities = 3

factors = Factors()
for f in range(nbFactors):
  e.__setattr__('factor_'+str(f), [*range(nbModalities)])


for factor in factors(): #
  #print('textureSize %i' % ee.textureSize)
  print(factor.getId())
