import explanes

e = explanes.Factors()


nFactors = 4
nModalities = 4

e = Factors()
for f in range(nFactors):
  e.__setattr__('factor'+str(f), [*range(nModalities)])


for ee in e(): #
  #print('textureSize %i' % ee.textureSize)
  print(ee.getId())
