# your experiment file shall be in the current directory or in the python path
import demo

experiment = demo.set()
selector = {"nn_type":["cnn", "lstm"],"n_layers":2,"learning_rate":0.001}

(data, settings, header) = experiment.metric.get(
  'accuracy',
  experiment.plan.select(selector),
  experiment.path.output
  )

import numpy as np
import matplotlib.pyplot as plt

settingIds = np.arange(len(settings))

fig, ax = plt.subplots()
ax.barh(settingIds, np.mean(data, axis=1), xerr=np.std(data, axis=1), align='center')
ax.set_yticks(settingIds)
ax.set_yticklabels(settings)
ax.invert_yaxis()  # labels read top-to-bottom
ax.set_xlabel('Accuracy')
ax.set_title(header)

fig.tight_layout()
plt.show()
