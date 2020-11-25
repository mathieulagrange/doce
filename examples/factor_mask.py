import explanes as el

f = el.factor.Factor()
f.f1=['a', 'b', 'c']
f.f2=[1, 2, 3]

# select the settings with the second modality of the first factor, and with the first modality of the second factor
for setting in f.mask([1, 0]):
  print(setting)

# select the settings with the second modality of the first factor, and all the modalities of the second factor
for setting in f.mask([1, -1]):
  print(setting)

# the selection of all the modalities of the remaining factors can be conveniently expressed
for setting in f.mask([1]):
  print(setting)

# select the settings using 2 mask, where the first selects the settings with the first modality of the first factor and with the second modality of the second factor, and the second mask selects the settings with the second modality of the first factor, and with the third modality of the second factor
for setting in f.mask([[0, 1], [1, 2]]):
  print(setting)

# the latter expression may be interpreted as the selection of the settings with the first and second modalities of the first factor and with second and third modalities of the second factor. In that case, one needs to add a -1 at the end the mask (even if by doing so the length of the mask is larger than the number of factors)
for setting in f.mask([[0, 1], [1, 2], -1]):
  print(setting)
