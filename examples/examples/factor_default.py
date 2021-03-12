import explanes as el

f = el.Factor()
f.f1 = ['a', 'b']
f.f2 = [1, 2, 3]

print(f)
for setting in f.mask():
  print(setting.id())
# set the default value
f.default('f2', 2)
for setting in f:
  print(setting.id())

# add a 0 which
f.f2 = [0, 1, 2, 3]
print(f)

f.default('f2', 2)
for setting in f:
  print(setting.id())

for setting in f:
  print(setting.id(hideNoneAndZero=False))
