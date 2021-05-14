Glossary
========

.. glossary::

  system:
    A system is a computational process that can be controled by a fixed set of parameters, whose execution can be reliably replicated.

  experiment:
    An experiment is the environnement within which the system is operated. It comprises the data, the experimental code, and the set of factors required to operate the system.

  factor
    A factor is a degree of freedom in the design of the system. In doce, it is implemented as a list of modalities.

  modality
    A modality is an instantiation of a factor in a setting.

  setting
    A setting is a list of modalities, that fully describes the parameters of the system, where each modality is issued from each factor of the experiment.

  selector
    A selector is a convenient way to define a set of settings. In doce, it is alternatively expressed as a list of dict or a list of list. In the former, each list is composed of dict, each with the following syntax: {factor: modality or list of modalities, ...}. In the latter, each list is composed of integer values or list of integer values. For example, the selector [0, -1, [1, 2]] defines the set of setting with the first modality of the first factor, all the modalities of the second factor, and the  second and third modality of the third factor.

  metric
    A metric is a set of data that results from the execution of the system given a setting. Each metric can de reduced in order to produce quantities that will be useful for monitoring the behaviour of the system.
