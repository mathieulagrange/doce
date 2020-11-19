import explanes as el

f = el.factor.Factor()
f.one=['a', 'b']
f.two=[1]*10

print(f.nbModalities('one'))
print(f.nbModalities(1))

f2 = el.factor.Factor()
f2.two=[1]*10
f2.one=['a', 'b']
print(f2.nbModalities(1))
