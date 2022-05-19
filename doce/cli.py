import doce
import sys
import argparse
import ast
import importlib
import os
import copy
import subprocess
import numpy as np
import shutil
import time
import re

def main():
  """This method shall be called from the main script of the experiment to control the experiment using the command line.

  This method provides a front-end for running a doce experiment. It should be called from the main script of the experiment. The main script must define a **set** function that will be called before processing and a **step** function that will be processed for each setting. It may also define a **display** function that will used to monitor the results. This main script can define any functions that can be used within the **set**, **step**, and **display** functions.

  Examples

  Assuming that the file experiment_run.py contains:

  >>> import doce
  >>> if __name__ == "__main__":
  ...   doce.experiment.run() # doctest: +SKIP
  >>> def set(experiment, args=None):
  ...   experiment._plan.factor1=[1, 3]
  ...   experiment._plan.factor2=[2, 4]
  ...   return experiment
  >>> def step(setting, experiment):
  ...   print(setting.identifier())

  Executing this file with the --run option gives:

  $ python experiment_run.py -r
   factor1_1_factor2_2
   factor1_1_factor2_4
   factor1_3_factor2_2
   factor1_3_factor2_4

  Executing this file with the --help option gives:

  $ python experiment_run.py -h

  """

  parser = argparse.ArgumentParser()
  parser.add_argument('-A', '--archive', type=str, help='archive the selected  settings from a given path. If the argument does not have / or \, the argument is interpreted as a member of the experiments path. The files are copied to the path experiment.path.archive if set.', nargs='?', const='')
  parser.add_argument('-c', '--compute', type=int, help='perform computation. Integer parameter sets the number of jobs computed in parallel (default to one core).', nargs='?', const=1)
  parser.add_argument('-C', '--copy', help='copy codebase to the host defined by the host (-H) argument.', action='store_true')
  parser.add_argument('-d', '--display', type=str, help='display metrics. If no parameter is given, consider the default display and show all metrics. If the str parameter contain a list of integers, use the default display and show only the selected metrics defined by the integer list. If the str parameter contain a name, run the display method with this name.', nargs='?', default='-1')
  parser.add_argument('-D', '--detached', help='Perform the computation in a detached mode, meaning that if one setting fails, doce continues to loop over the remaining settings to be computed.', action='store_true')
  # parser.add_argument('-e', '--experiment', type=str, help='select experiment. List experiments if empty.', nargs='?', default='all')
  parser.add_argument('-E', '--export', type=str, help='Export the display of reduced metrics among different file types (html, png, pdf). If parameter is empty, all exports are made. If parameter has a dot, interpreted as a filename which should be of support type. If parameter has nothing before the dot, interpreted as file type, and experiment.name is used. If parameter has no dot, interpreted as file name with no extension, and all exports are made.', nargs='?', default='none')
  parser.add_argument('-f', '--files', help='list files.', action='store_true')
  parser.add_argument('-H', '--host', type=int, help='running on specified HOST. Integer defines the index in the host array of config. -2 (default) runs attached on the local host, -1 runs detached on the local host through a screen, -3 is a flag meaning that the experiment runs in server mode (no stop at failing settings).', default=-2)
  parser.add_argument('-i', '--information', help='show information about the experiment.', action='store_true')
  parser.add_argument('-K', '--keep', type=str, help='keep only the selected settings from a given path. If the argument does not have / or \, the argument is interpreted as a member of the experiments path. Unwanted files are moved to the path experiment.path.archive if set, deleted otherwise.', nargs='?', const='')
  parser.add_argument('-l', '--list', help='list settings.', action='store_true')
  parser.add_argument('-M', '--mail', help='send email at the beginning and end of the computation. If a positive integer value x is provided, additional emails are sent every x hours.', nargs='?', default='-1')
  parser.add_argument('-p', '--plan', help='show the active plan of the experiment.', action='store_true')
  parser.add_argument('-P', '--progress', help='display progress bar. Argument controls the display of the current setting: d alphanumeric description, s numeric selector, ds combination of both (default d).', nargs='?', const='d')
  parser.add_argument('-R', '--remove', type=str, help='remove the selected  settings from a given path. If the argument does not have / or \, the argument is interpreted as a member of the experiments path. Unwanted files are moved to the path experiment.path.archive if set, deleted otherwise.', nargs='?', const='')
  parser.add_argument('-s', '--select', type=str, help='selection of settings', default='[]')
  parser.add_argument('-S', '--skip', help='check availability of any metric of a given setting and skip computation if available.', action='store_true')
  # parser.add_argument('-S', '--server_default', help='augment the command line with the content of the dict experiment._default_server_run_argument.', action='store_true')
  parser.add_argument('-u', '--user_data', type=str, help='a dict specified as str (for example, \'{\"test\": 1}\') that will be available in experiment.user_data (user_data.test=1).', default='{}')
  parser.add_argument('-v', '--version', help='print version', action='store_true')
  parser.add_argument('-V', '--verbose', help='level of verbosity (default 0: silent).', action='store_true')
  args = parser.parse_args()

  if args.mail is None:
    args.mail = 0
  else:
    args.mail = float(args.mail)

  if args.export is None:
    args.export = 'all'
  if args.progress is None:
    args.progress = ''

  selector = re.sub(r"[\n\t\s]*", "", args.select)
  try:
    selector = ast.literal_eval(selector)
  except:
    pass

  user_data = ast.literal_eval(args.user_data)

  module = sys.argv[0][:-3]
  try:
    config = importlib.import_module(module)
  except:
   print(sys.argv[0]+' should implement a valid python module.')
   raise value_error


  # experiment = doce.experiment.Experiment()
  # if isinstance(user_data, dict):
  #   experiment.user_data = user_data
  if hasattr(config, 'set'):
    experiment = config.set(args)
  else:
    experiment = doce.Experiment()

  if args.version:
    print("Experiment version "+experiment.version)
    exit(1)

  experiment.status.verbose = args.verbose
  experiment._resume = args.skip

  experiment.select(selector, show=args.plan)

  # if experiment_id != 'all':
  #   if experiment_id is None:
  #     for e in :
  #       if isinstance(getattr(self, e), doce.Plan):
  #         print('Selecting plan '+e+': ')
  #         print(getattr(experiment, e))
  #       else:
  #         print('There is only one experiment. Please do not consider the -e (--experiment) option and use -i for information about the factors.')
  #         break
  #   elif hasattr(experiment._plan, experiment_id):
  #     experiment._plan = getattr(experiment._plan, experiment_id)
  #   else:
  #     print('Unrecognized experiment: '+experiment_id)
  # elif len(experiment.plans())>0:

  # if args.server_default:
  #   args.server_default = False
  #   for key in experiment._default_server_run_argument:
  #     # args[key] =
  #     args.__setattr__(key, experiment._default_server_run_argument[key])

  if args.information:
      print(experiment)
  # if args.plan:
  #     print('Main')
  #     print(experiment._plan.as_panda_frame())
  if args.list:
    experiment.perform(experiment.selector, progress='', function= lambda s, e: print(s))
  if args.files:
    experiment.perform(experiment.selector, progress='', function= lambda s, e: print(s.identifier()))

  if args.remove:
    experiment.clean_data_sink(args.remove, experiment.selector, archive_path=experiment.path.archive, verbose=experiment.status.verbose)
  if args.keep:
    experiment.clean_data_sink(args.keep, experiment.selector, reverse=True, archive_path=experiment.path.archive, verbose=experiment.status.verbose)
  if args.archive:
    if experiment.path.archive:
      experiment.clean_data_sink(args.archive, experiment.selector, keep=True, setting_encoding=experiment._setting_encoding, archive_path=experiment.path.archive, verbose=experiment.status.verbose)
    else:
      print('Please set the path.archive path before issuing an archive command.')

  log_file_name = ''
  if args.host>-2:

    import argunparse

    unparser = argunparse._argument_unparser()
    kwargs = copy.deepcopy(vars(args))
    kwargs['host'] = -3
    command = unparser.unparse(**kwargs).replace('\'', '\"').replace('\"', '\\\"')
    if args.verbose:
      command += '; bash '
    command = 'screen -dm bash -c \'python3 '+experiment.name+'.py '+command+'\''
    message = 'experiment launched on local host'
    if args.host>-1:
      if args.copy:
        sync_command = 'rsync -r '+experiment.path.code+'* '+experiment.host[args.host]+':'+experiment.path.code_raw
        print('Sycing code repository to host: '+experiment.host[args.host])
        print(sync_command)
        os.system(sync_command)
        print('')
      command = 'ssh '+experiment.host[args.host]+' "cd '+experiment.path.code_raw+'; '+command+'"'
      message = 'Experiment launched.'
    print('Sending experiment to host: '+experiment.host[args.host])
    print('')
    print(command)
    os.system(command)
    print('')
    print(message)
    exit()
  print()
  if args.host == -3 or args.detached:
    log_file_name = '/tmp/doce_'+experiment.name+'_'+experiment.status.run_id+'.txt'
  if args.mail>-1:
    experiment.send_mail(args.select+' has started.', '<div> Selector = '+args.select+'</div>')
  if args.compute and hasattr(config, 'step'):
    experiment.perform(experiment.selector, config.step, nb_jobs=args.compute, log_file_name=log_file_name, progress=args.progress, mail_interval = float(args.mail))


  select_display = []
  select_factor = ''
  display_method = ''
  display = True
  if args.display == '-1':
    display = False
  elif args.display is not None:
    if  '[' in args.display:
      select_display = ast.literal_eval(args.display)
    elif ':' in args.display:
      s = args.display.split(':')
      select_display = [int(s[0])]
      select_factor = s[1]
    else:
      select_display = [int(args.display)]


  body = '<div> Selector = '+args.select+'</div>'
  if display:
    if hasattr(config, display_method):
      getattr(config, display_method)(experiment, experiment._plan.select(experiment.selector))
    else:
      (df, header, styler) = data_frame_display(experiment, args, config, select_display, select_factor)
      if df is not None:
        print(header)
        # pd.set_option('precision', 2)
        print(df)
      if args.export != 'none' and styler is not None:
        export_data_frame(experiment, args, df, styler, header)
      if args.mail>-1:
        body += '<div> '+header+' </div><br>'+styler.render()

  if args.host == -3 or args.detached:
    log_file_name = '/tmp/doce_'+experiment.name+'_'+experiment.status.run_id+'.txt'
    if os.path.exists(log_file_name):
      print('Some settings have failed. Log available at: '+log_file_name)
      with open(log_file_name, 'r') as file:
        log = file.read()
        if log:
          body+= '<h2> Error log </h2>'+log.replace('\n', '<br>')

  if args.mail>-1:
    experiment.send_mail(args.select+' is over.', body) #

def data_frame_display(experiment, args, config, select_display, select_factor):

  import pandas as pd

  selector = experiment.selector
  ma=copy.deepcopy(selector)
  if select_factor:
    fi = experiment._plan.factors().index(select_factor)

    selector = experiment._plan.expand_selector(selector, select_factor)

    ms = selector[fi]
    # print(ms)
    selector[fi] = [0]
    experiment._plan.select(selector).__set_settings__()
    settings = experiment._plan._settings
    # print(settings)
    # print(fi)
    for s in settings:
      s[fi] = ms
    # print(settings)
    # ma=copy.deepcopy(selector)
    # ma[fi]=0
  (table, columns, header, nb_factor_columns, modification_time_stamp, significance) = experiment.metric.reduce(experiment._plan.select(selector), experiment.path.output, factor_display=experiment._display.factor_format_in_reduce, metric_display=experiment._display.metric_format_in_reduce, factor_display_length=experiment._display.factor_format_in_reduce_length, metric_display_length=experiment._display.metric_format_in_reduce_length, verbose=args.verbose, reduction_directive_module=config)

  if len(table) == 0:
      return (None, '', None)
  if select_factor:
    modalities = getattr(experiment._plan, select_factor)[ms]
    header = 'metric: '+columns[nbFactorColumns+select_display
    [0]]+' for factor '+header.replace(select_factor+': '+str(modalities[0])+' ', '')+' '+select_factor

    columns = columns[:nb_factor_columns]
    for m in modalities:
      columns.append(str(m))

    significance = np.zeros((len(settings), len(modalities)))
    for s in range(len(table)):
      table[s] = table[s][:nb_factor_columns]
    # print(settings)
    for sIndex, s in enumerate(settings):
      (sd, ch, csd, nb, md, si)  = experiment.metric.reduce(experiment._plan.select(s), experiment.path.output, factor_display=experiment._display.factor_format_in_reduce, metric_display=experiment._display.metric_format_in_reduce, factor_display_length=experiment._display.factor_format_in_reduce_length, metric_display_length=experiment._display.metric_format_in_reduce_length, verbose=args.verbose, reduction_directive_module=config)
      modification_time_stamp += md
      # import pdb; pdb.set_trace()
      significance[sIndex, :] = si[:, select_display[0]]
      # print(s)
      # print(sd)
      for ssd in sd:
        table[sIndex].append(ssd[1+select_display[0]])

  if len(significance):
    best = significance == -1
    significance = significance>experiment._display.pValue
    significance = significance.astype(float)
    significance[best] = -1
    if select_display and not select_factor:
      significance = significance[:, select_display]

  if experiment._display.pValue == 0:
    for ti, t in enumerate(table):
      table[ti][-len(significance[ti]):]=significance[ti]

  if modification_time_stamp:
    print('Displayed data generated from '+ time.ctime(min(modification_time_stamp))+' to '+ time.ctime(max(modification_time_stamp)))
  df = pd.DataFrame(table, columns=columns) #.fillna('-')

  if select_display and not select_factor and  len(columns)>=max(select_display)+nb_factor_columns:
    columns = [columns[i] for i in [*range(nb_factor_columns)]+[s+nb_factor_columns for s in select_display]]
    df = df[columns]

  d = dict(selector="th", props=[('text-align', 'center'), ('border-bottom', '.1rem solid')])

  # Construct a selector of which columns are numeric
  numeric_col_selector = df.dtypes.apply(lambda d: issubclass(np.dtype(d).type, np.number))
  c_percent = []
  c_no_percent = []
  cMinus = []
  c_no_minus = []
  cMetric = []
  cInt = {}
  precision_format = {}
  for ci, c in enumerate(columns):
    if ci >= nb_factor_columns:
      cMetric.append(c)
      if '%' in c:
        precision_format[c] = '{0:.'+str(experiment._display.metric_precision-2)+'f}'
        c_percent.append(c)
      else:
        precision_format[c] = '{0:.'+str(experiment._display.metric_precision)+'f}'
        c_no_percent.append(c)
      if c[-1] == '-' :
        cMinus.append(c)
      else:
        c_no_minus.append(c)
    # else:
    #   if isinstance(df[c][0], float):
    #     is_integer = True
    #     for x in df[c]:
    #       if not x.is_integer():
    #         is_integer = False
    #     if is_integer:
    #       cInt[c] = 'int32'

  dPercent = pd.Series([experiment._display.metric_precision-2]*len(c_percent), index=c_percent, dtype = np.intc)
  d_no_percent = pd.Series([experiment._display.metric_precision]*len(c_no_percent), index=c_no_percent, dtype = np.intc)
  dInt = pd.Series([0]*len(cInt), index=cInt, dtype = np.intc)
  df=df.round(dPercent).round(d_no_percent)

  for ci, c in enumerate(columns):
    if isinstance(df[c][0], float):
      is_integer = True
      for x in df[c]:
        if not x.is_integer():
          is_integer = False
      if is_integer:
        cInt[c] = 'int32'

  df=df.astype(cInt)

  # df['mean_offset'].map(lambda x: 0)

  # if c_no_percent:
  #   form = '%.'+str(experiment._display.metric_precision)+'f'
  # else:
  #   form = '%.'+str(experiment._display.metric_precision-2)+'f'
  # pd.set_option('display.float_format', lambda x: '%.0f' % x
  #                     if (x == x and x*10 % 10 == 0)
  #                     else form % x)

  styler = df.style.set_properties(subset=df.columns[numeric_col_selector], # right-align the numeric columns and set their width
        **{'width':'10em', 'text-align':'right'})\
        .set_properties(subset=df.columns[~numeric_col_selector], # left-align the non-numeric columns and set their width
        **{'width':'10em', 'text-align':'left'})\
        .set_properties(subset=df.columns[nb_factor_columns], # left-align the non-numeric columns and set their width
        **{'border-left':'.1rem solid'})\
        .set_table_styles([d])\
        .format(precision_format).applymap(lambda x: 'color: white' if pd.isnull(x) else '')
  if not experiment._display.show_row_index:
    styler.hide_index()
  if experiment._display.bar:
    styler.bar(subset=df.columns[nb_factor_columns:], align='mid', color=['#d65f5f', '#5fba7d'])
  if experiment._display.highlight:
    styler.apply(highlight_stat, subset=cMetric, axis=None, **{'significance':significance})
    styler.apply(highlight_best, subset=cMetric, axis=None, **{'significance':significance})

  return (df.fillna('-'), header, styler)

def highlight_stat(s, significance):
  import pandas as pd
  df = pd.DataFrame('', index=s.index, columns=s.columns)
  if len(significance):
    # print(df)
    # print(significance)
    df = df.where(significance<=0, 'color: blue')
  return df

def highlight_best(s, significance):
  import pandas as pd
  df = pd.DataFrame('', index=s.index, columns=s.columns)
  if len(significance):
    df = df.where(significance>-1, 'font-weight: bold')
  return df

def export_data_frame(experiment, args, df, styler, header):
  if not os.path.exists(experiment.path.export):
    os.makedirs(experiment.path.export)
  if args.export == 'all':
    export_file_name = experiment.name
  else:
    a = args.export.split('.')
    # print(a)
    if a[0]:
      export_file_name = a[0]
    else:
      export_file_name = experiment.name
    if len(a)>1:
      args.export = '.'+a[1]
    else:
      args.export = 'all'
  export_file_name = experiment.path.export+'/'+export_file_name
  reload_header =  '<script> window.onblur= function() {window.onfocus= function () {location.reload(true)}}; </script>'
  with open(export_file_name+'.html', "w") as out_file:
    out_file.write(reload_header)
    out_file.write('<br><u>'+header+'</u><br><br>')
    out_file.write(styler.render())
  if 'csv' in args.export or 'all' == args.export:
    df.to_csv(path_or_buf=export_file_name+'.csv', index=experiment._display.show_row_index)
    print('csv export: '+export_file_name+'.csv')
  if 'xls' in args.export or 'all' == args.export:
    df.to_excel(excel_writer=export_file_name+'.xls', index=experiment._display.show_row_index)
    print('excel export: '+export_file_name+'.xls')

  if 'tex' in args.export or 'all' == args.export:
    df.to_latex(buf=export_file_name+'.tex', index=experiment._display.show_row_index, bold_rows=True)
    print('tex export: '+export_file_name+'.tex')
    print('please add to the preamble: \\usepackage{booktabs}')

  if 'png' in args.export or 'all' == args.export:
      print('Creating image...')
      if shutil.which('wkhtmltoimage') is not None:
        subprocess.call(
        'wkhtmltoimage -f png --width 0 '+export_file_name+'.html '+export_file_name+'.png', shell=True)
        print('png export: '+export_file_name+'.png')
      else:
        print('generation of png is handled by converting the html generated from the result dataframe using the wkhtmltoimage tool. This tool must be installed and reachable from you path.')
  if 'pdf' in args.export or 'all' == args.export:
    print('Creating pdf...')
    if shutil.which('wkhtmltopdf'):
      subprocess.call(
      'wkhtmltopdf '+export_file_name+'.html '+export_file_name+'.pdf', shell=True)
    else:
      print('Generation of pdf is handled by converting the html generated from the result dataframe using the wkhtmltoimage tool which must be installed and reachable from you path.')

    print('Cropping '+export_file_name+'.pdf')
    if shutil.which('pdfcrop') is not None:
      subprocess.call(
      'pdfcrop '+export_file_name+'.pdf '+export_file_name+'.pdf', shell=True)
      print('pdf export: '+export_file_name+'.pdf')
    else:
      print('Crop of pdf is handled using the pdfcrop tool. This tool must be installed and reachable from you path.')

  if 'html' not in args.export and 'all' != args.export:
    os.remove(export_file_name+'.html')
  else:
    print('html export: '+export_file_name+'.html')

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
