import explanes as ex

nbFactors = 4
nbModalities = 3

factors = ex.Factors()
for f in range(nbFactors):
  factors.__setattr__('factor'+str(f), [*range(nbModalities)])

for setting in factors(): #
  #print('textureSize %i' % ee.textureSize)
  print(setting.getId())
