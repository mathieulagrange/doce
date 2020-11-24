import explanes as el

f = el.Factor()

f.f1 = ['a', 'b']
f.f2 = [1, 2, 3]

print(f)
for setting in f.mask():
  print(setting.id())

f.default('f2', 2)

for setting in f:
  print(setting.id())

f.f2 = [0, 1, 2, 3]
print(f)

f.default('f2', 2)

for setting in f:
  print(setting.id())
