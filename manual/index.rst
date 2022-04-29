
.. image:: img/logo.png
  :width: 400

********
doce
********
`doce` is a python package for handling numerical experiments using a design-of-experiment (DOE) approach. It is geared towards research in machine learning and data science but also be useful for other fields.

For a quick introduction to using doce, please refer to the :doc:`tutorial`.

********
What for ?
********

Experimentation and testing are a fundamental part of scientific research. They're also extremely time-consuming, tedious, and error-prone unless properly managed. `doce` is here to help you with the management, running and reporting of your experiments, letting you focus more on the creative part of your research work.

What can `doce`  can help you to do?

 - Set up an experimental protocol once, and re-run it as often as needed with minimum hassle using new data, modified code, or alternative hypotheses.
 - Systematically explore many combinations of operational parameters in a system.
 - Re-use earlier results to only compute the later stages of a process, thus cutting down the running time.
 - Automatically produce analysis tables.
 - Ease the production of paper-ready displays.
 - Keep experimental code, data and results organized in a standardized way, to ease cooperation with others and allow you to go back painlessly on months-old or years-old work.

 .. image:: img/workflow.png
   :width: 400

.. toctree::
  :caption: Getting started
  :maxdepth: 1

  install
  tutorial

.. toctree::
  :caption: API documentation
  :maxdepth: 1

  cli
  experiment
  plan
  setting
  metric
  util

.. toctree::
  :caption: Reference
  :maxdepth: 1

  changelog
  genindex
  glossary
