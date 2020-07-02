#!/usr/bin/env python3

import sys
import pandas as pd
import argparse
import ast
import importlib



def __main__():
  parser = argparse.ArgumentParser()
  parser.add_argument('-e', '--experiment', type=str, help='name of the experiment')
  parser.add_argument('-m', '--mask', type=str, help='mask of the experiment to run', default='[]')
  parser.add_argument('-M', '--mail', help='send email at the end of the computation', action='store_true')
  parser.add_argument('-s', '--server', type=int, help='running server side')
  parser.add_argument('-d', '--display', help='display metrics', action='store_true')
  parser.add_argument('-r', '--run', type=int, help='perform computation (integer parameter sets the number of jobs computed in parallel)', nargs='?', const=1)
  parser.add_argument('-D', '--debug', help='debug mode', action='store_true')
  parser.add_argument('-v', '--version', help='print version', action='store_true')
  args = parser.parse_args()
  print(args)
  if args.version:
    print("Experiment version "+experiment.project.version)
    exit(1)

  if args.server:
    # copy code

    # launch command
    
  sys.path.append('explanes/demo/')

  mask = ast.literal_eval(args.mask)

  if args.experiment:
    config = importlib.import_module(args.experiment)
  else:
    print('Please provide a valid project name')
    exit(1)
  experiment = config.set(args)
  print(experiment)

  if args.run:
    experiment.do(mask, config.step, jobs=args.run)
  elif not args.display:
    experiment.do(mask, show, tqdmDisplay=False)

  if args.mail or args.display:
    (table, columns, header) = experiment.metric.reduce(experiment.factor.settings(mask), experiment.path.output, naming='hash')
    df = pd.DataFrame(table, columns=columns).round(decimals=2)
    print(header)
    print(df)
    if args.mail:
      experiment.sendMail('<div> '+header+' </div><br>'+df.to_html()) #

def show(setting, config):
  print(setting.describe())

if __name__ == "__main__":
    __main__()
