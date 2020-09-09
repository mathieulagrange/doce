#!/usr/bin/env python3

import sys
import pandas as pd
import argparse
import argunparse
import ast
import importlib
import os
import explanes as exp

def __main__():
  parser = argparse.ArgumentParser()
  parser.add_argument('-e', '--experiment', type=str, help='name of the experiment')
  parser.add_argument('-i', '--information', help='show information about the the experiment', action='store_true')
  parser.add_argument('-m', '--mask', type=str, help='mask of the experiment to run', default='[]')
  parser.add_argument('-M', '--mail', help='send email at the beginning and end of the computation', action='store_true')
  parser.add_argument('-S', '--sync', help='sync to server defined', action='store_true')
  parser.add_argument('-s', '--server', type=int, help='running server side. Integer defines the index in the host array of config. -2 (default) runs attached on the local host, -1 runs detached on the local host, -3 is a flag meaning that the experiment runs serverside', default=-2)
  parser.add_argument('-d', '--display', help='display metrics', action='store_true')
  parser.add_argument('-r', '--run', type=int, help='perform computation. Integer parameter sets the number of jobs computed in parallel (default to one core).', nargs='?', const=1)
  parser.add_argument('-D', '--debug', help='debug mode', action='store_true')
  parser.add_argument('-v', '--version', help='print version', action='store_true')
  parser.add_argument('-P', '--progress', help='display progress bar', action='store_true')
  args = parser.parse_args()

  if args.version:
    print("Experiment version "+experiment.project.version)
    exit(1)

  sys.path.append('explanes/demo/')

  mask = ast.literal_eval(args.mask)

  if args.experiment:
    config = importlib.import_module(args.experiment)
  else:
    print('Please provide a valid project name')
    raise ValueError
  experiment = exp.Config()
  experiment = config.set(experiment, args)
  if args.information:
      print(experiment)
  logFileName = ''
  if args.server>-2:
    unparser = argunparse.ArgumentUnparser()
    kwargs = vars(parser.parse_args())
    kwargs['server'] = -3
    command = unparser.unparse(**kwargs).replace('\'', '\"').replace('\"', '\\\"')
    if args.debug:
      command += '; bash '
    command = 'screen -dm bash -c \'python3 run.py '+command+'\''
    message = 'experiment launched on local host'
    if args.server>-1:
      if args.sync:
        syncCommand = 'rsync -r '+experiment.path.code+'/* '+experiment.host[args.server]+':'+experiment.path.code
        print(syncCommand)
        os.system(syncCommand)
      command = 'ssh '+experiment.host[args.server]+' "cd '+experiment.path.code+'; '+command+'"'
      message = 'experiment launched on host: '+experiment.host[args.server]
    print(command)
    os.system(command)
    print(message)
    exit()

  if args.server == -3:
    logFileName = '/tmp/test'
  if args.mail:
    experiment.sendMail('has started.', '<div> Mask = '+args.mask+'</div>')
  if args.run and hasattr(config, 'step'):
    experiment.do(mask, config.step, jobs=args.run, logFileName=logFileName, tqdmDisplay=args.progress)
  elif not args.display:
    experiment.do(mask, tqdmDisplay=False)

  if args.mail or args.display:
    if hasattr(config, 'display'):
      config.display(experiment, experiment.factor.settings(mask))
    else:
      (table, columns, header) = experiment.metric.reduce(experiment.factor.settings(mask), experiment.path.output, factorDisplayStyle=experiment._factorFormatInReduce, **experiment._idFormat)
      df = pd.DataFrame(table, columns=columns).round(decimals=2)
      print(header)
      print(df)
    if args.mail:
      experiment.sendMail('is over.', '<div> Mask = '+args.mask+'</div>'+'<div> '+header+' </div><br>'+df.to_html()) #

if __name__ == "__main__":
    __main__()
