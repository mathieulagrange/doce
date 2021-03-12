import explanes as el

table = [['a', 'b', 1, 2], ['a', 'c', 2, 2], ['a', 'b', 2, 2]]
header = ['factor_1', 'factor_2', 'metric_1', 'metric_2']
(settingDescription, columnHeader, constantSettingDescription, nbColumnFactor) = el.util.pruneSettingDescription(table, header, 2)
print(nbColumnFactor)
print(constantSettingDescription)
print(columnHeader)
print(settingDescription)
