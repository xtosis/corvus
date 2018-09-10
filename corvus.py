from os import walk
from os.path import join
import pandas as pd


def drawLine():
    print '-------------------------------------------------------------------'


def getFile(ROOT, DF, ID, SHOW=False):
	directory = ROOT+DF.loc[ID, 'DIR']
	if SHOW:
		print 'C0RVUS| Directory:\n {}'.format(directory)
	with open(directory, 'r') as file:
		return file.read()


def getExtension(BASENAME):
	extension = '.'.join(BASENAME.split('.')[1:])
	return '.' + extension if extension else 'UNK'


def extensionSummary(DF):
	summary = DF.groupby('EXT').count().reset_index()

	summary.columns = ['Extension', 'Count']
	summary = pd.Series(data=summary['Count'].values,
						index=summary['Extension'].values).sort_values(ascending=False)
	return summary


def inspectExtension(DF, EXT):
	directories = DF[DF['EXT']==EXT]
	directories = directories['DIR'].values.tolist()
	for directory in directories:
		print '\t  {}'.format(directory)
	return None


def stringSearch(ROOT, DIRS, STR, EXT='.js', VERBOSE=0, OUT=False, CLEAN=False):
	ids = DIRS[DIRS['EXT']==EXT].index.values.astype(int)
	directories = DIRS[DIRS['EXT']==EXT].DIR.values
	file_count = 0
	inst_ch = []
	inst_id = []

	for i, directory in enumerate(directories):

		# Importing the text from file
		with open(ROOT+directory, 'r') as file:
			text = file.read()

		# Finding the string
		start = 0
		first_time = True
		while(text.find(STR[0], start) > -1):

			found = text.find(STR[0], start)

			if first_time:
				file_count = file_count+1
				first_time = False
				if VERBOSE == 1:
					print 'C0RVUS| {:03}: {}'.format(ids[i], directory)
				elif VERBOSE == 2:
					print '\nC0RVUS| {:03}: {}'.format(ids[i], directory)
			end = text.find(STR[1], found)
			temp = text[found:end]

			# Cleaning
			if CLEAN:
				temp = temp.replace('\n','')
				temp = temp.replace('\t','')
				temp = temp.replace('  ',' ')

			inst_ch = inst_ch + [temp]
			inst_id = inst_id + [ids[i]]
			start = end
			if VERBOSE == 2:
				print '  [{:6}:{:6}]\t{}'.format(start, end, temp)

	print 'C0RVUS| [{:3}] instances found in [{:3}] files out of [{}]'.format(len(inst_id), file_count, len(DIRS))
	if OUT:
		return pd.Series(data=inst_ch, index=inst_id)


def generateCorvus(ROOT, FIX=None, DROP_EXT=None, VERBOSE=0, DROP_UNK=True):
	df = []
	# getting all files (and folders) within ROOT
	for r, d, f in walk(ROOT):
		for file in f:
			# Outputs extension if a file
			df.append([getExtension(file), join(r, file).replace(ROOT,'').replace('\\','/')])
	df = pd.DataFrame(df, columns=['EXT', 'DIR'])

	# reporting raw
	drawLine()
	if VERBOSE > 0:
		print 'C0RVUS| {:03} directories to be tracked'.format(len(df)),
		print 'with {:02} unique extensions'.format(len(extensionSummary(df)))

	# reporting all UNK extensions
	if VERBOSE > 1:
		print '\t> UNK extensions:'
		inspectExtension(df, 'UNK')

	# removing UNK extentions
	if DROP_UNK:
		df = df[df.EXT != 'UNK']
		if VERBOSE > 0:
			print 'C0RVUS| removed UNK extensions'
 			print 'C0RVUS| {:03} directories to be tracked'.format(len(df)),
			print 'with {:02} unique extensions'.format(len(extensionSummary(df)))
			if VERBOSE > 1:
				summary = extensionSummary(df) 
				for i in summary.index:
					print '{:5} | {}'.format(summary[i], i)
				drawLine()

    # fixing some extensions
	if FIX != None:
		df.replace(FIX, inplace=True)
		if VERBOSE > 0:
			print 'C0RVUS| fixed extentions'
			print 'C0RVUS| {:03} directories to be tracked'.format(len(df)),
			print 'with {:02} unique extensions'.format(len(extensionSummary(df)))
		if VERBOSE > 1:
			summary = extensionSummary(df) 
			for i in summary.index:
				print '{:5} | {}'.format(summary[i], i)
			drawLine()

	# dropping some extensions
	if DROP_EXT != None:
		if VERBOSE > 1:
			print 'C0RVUS| extensions to drop:'
		for extension in DROP_EXT:
			if VERBOSE > 1:
				print '\t> *{}'.format(extension)
				inspectExtension(df, extension)
			df = df[df.EXT != extension]
		
		# reporting dropped extensions
		if VERBOSE > 0:        
			print 'C0RVUS| dropped specified extensions'
			print 'C0RVUS| {:03} directories to be tracked'.format(len(df)),
			print 'with {:02} unique extensions'.format(len(extensionSummary(df)))
			summary = extensionSummary(df) 
			for i in summary.index:
				print '{:5} | {}'.format(summary[i], i)

	# sorting df
	df = df.append({'EXT':'YOU', 'DIR':'YOU'}, ignore_index=True)
	df = df.sort_values(['DIR'], ascending=False).reset_index(drop=True)

	# creating new columns
	n_files = df.shape[0]
	for col in ['DEP', 'CALL', 'FUNC', 'CHAR', 'DESC']:
		df[col] = ['None']*n_files

	# counting characters within each file
	for _id, directory in enumerate(df.DIR.values):
		if directory != 'YOU':
			text = getFile(ROOT, df, _id)
			df.loc[_id, 'CHAR'] = len(text)

	if VERBOSE == 0:
		print 'C0RVUS| generated raw corvus'
	drawLine()
	return df


def logError(LEVEL, ID, C, STR):
	return pd.Series([LEVEL,ID,C,STR], index = ['E','ID','INS','TEXT'])


def directoryRoutine(TEXT, END, CURRENT_DIR, ID, C):
	text = TEXT[:END]
	error = False
	for char in ('{','}','[',']','(',')',';','\n','\t'):
		if text.find(char) > -1:
			error = True
			break 

	if error:
		return logError(6, ID, C, text) # illegal characters in directory !! 6
	else:
		if len(text) == 0:
			return logError(0, ID, C, 'ZERO LENGTH')# zero length !!!!!!!!!! 0

		elif text[0] == '/':
			return text

		elif text[0:2] == './':
			END = 0
			while(CURRENT_DIR.find('/', END)>-1):
				END = CURRENT_DIR.find('/', END) + 1
			return text.replace('.', CURRENT_DIR[:END-1], 1)

		elif text[0:2] == '..':
			start = 0
			back = 1
			while(text.find('..', start)>-1):
				start = text.find('..', start) + 2
				back = back + 1
			END = 0
			locs = []
			while(CURRENT_DIR.find('/', END)>-1):
				locs = locs + [CURRENT_DIR.find('/', END)]
				END = CURRENT_DIR.find('/', END) + 1
			return CURRENT_DIR[:locs[-back]]+text[start:]

		else:
			return text # implies cloud based import


def saveData(COL, DATA, DF, ID, i, C):
    error7 = False
    if COL == 'DIR':
        dep_id = []
        for n, sample in enumerate(DF.DIR.values):
            if sample.find(DATA) == 0:
                if DATA == sample:
                    error7 = False
                    dep_id = [n];break
                elif DATA+'.js' == sample:
                    error7 = False
                    dep_id = [n];break
                elif DATA[-1] == '/':
                    error7 = False
                    dep_id = dep_id + [n]
                elif (DATA.find('.') == -1) and (sample.find('.js') > -1):
                    error7 = False
                    dep_id = dep_id + [n]
                else:
                    error7 = True
                    dep_id = dep_id + [n]
        if error7:
            for match in dep_id:
                DATA = '{}\n  {}'.format(DATA, DF.loc[match, 'DIR'])
            return logError(7, ID[i], C, DATA) # unknown case !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 7
        elif len(dep_id) == 0:
            if (DATA[0] != '/') and (DATA.find('.') == -1):
                new_dir = pd.Series(['cloud', DATA, 'None',[ID[i]],'None','None', 'None'], index = DF.columns.values)
                return DF.append(new_dir, ignore_index=True) # new cloud based dependacy ###############
            else:
                return logError(9, ID[i], C, DATA) # typo in directory string or file does not exist !! 9
        else:
            for dep in dep_id:
            	if DF.loc[ID[i], 'DEP'] == 'None':
                    DF.loc[ID[i], 'DEP'] = [dep]
                elif dep not in DF.loc[ID[i], 'DEP']:
                	DF.loc[ID[i], 'DEP'].append(dep)
                else:
                	return logError(10, ID[i], C, DATA) # duplicate entry !!!!!!!!!!!!!!!!!!!!!!!!!!!!! 10
                if DF.loc[dep, 'CALL'] == 'None':
                    DF.loc[dep, 'CALL'] = [ID[i]]
                else:
                    DF.loc[dep, 'CALL'].append(ID[i])
            return DF # new directory based dependecies ################################################
    else:
        if DF.loc[ID[i], COL] == 'None':
            DF.loc[ID[i], COL] = [DATA]
        elif DATA not in DF.loc[ID[i], COL]:
            DF.loc[ID[i], COL].append(DATA)
        else:
        	return logError(10, ID[i], C, DATA) # duplicate entry !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 10
        return DF # saving all other types of data #####################################################


def decodeID(ID, DIR):
	return DIR[DIR==ID].index.values[0]


def searchCorvus(ROOT, CORVUS, MIN_CHARS):

    ids = CORVUS[CORVUS['EXT']=='.js'].index.values.astype(int)
    directories = CORVUS[CORVUS['EXT']=='.js'].DIR.values
    errorLog = pd.DataFrame(columns = ['E','ID','INS','TEXT'])
    idir, fdir, func, streak = 0, 0, 0, 0

    for i, directory in enumerate(directories):

        # importing the text from file
        with open(ROOT+directory, 'r') as js_file:
            file = js_file.read()
        first = True
        c = 0 # ith instance of import that program broke at
        
        # making sure the file is not too small
        if len(file) < MIN_CHARS:
            search = False
            errorLog = errorLog.append(logError(-1, ids[i], c, 'TOO SHORT'), ignore_index=True)# too short !!!!!!!! -1
        else:
            search = True
        
        # Cleaning
        file = file.replace('\n','')
        file = file.replace('\t','')
        file = file.replace('  ',' ')
        file = file.replace('///','//')
        
        while((file.find('import') != -1) and (search)):
            
            fName = [] # Function name
            c = c + 1
            _find = file.find('import')
            file = file[_find+6:]
            
            if file[:2] in (" \'", ' \"'): ################################################### Import directory

                if (file[:2] == " \'") and (file.find("\'", 2) > -1):
                    file = file[2:]
                    _find = file.find("\'")
                elif (file[:2] == '\"') and (file.find('\"', 2) > -1):
                    file = file[2:]
                    _find = file.find('\"')
                else:
                    errorLog = errorLog.append(logError(8, ids[i], c, file), ignore_index=True)
                    break # no ending quot!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 8
                
                text = directoryRoutine(file, _find, directory, ids[i], c)
                
                if type(text) == type(pd.Series):
                    errorLog = errorLog.append(text, ingore_index=True)
                    break # zero length !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 0
                    # illegal characters in directory !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 6
                else:
                    temp = saveData('DIR', text, CORVUS, ids, i, c)
                    if type(temp) == type(pd.Series()):
                        errorLog = errorLog.append(temp, ignore_index=True)
                        # unknown case !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 7
                        # typo in dirctory string !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 9
                    else:
                        file = file[_find+1:]
                        CORVUS = temp.copy()
                        
                        #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ DIA
                        idir = idir + 1
            elif file[:2] == ' {': ########################################################### Function name
                file = file[2:]
                _find = file.find('}')
                
                if _find != -1: # Error 2
                    text = file[:_find].replace(' ','')
                    file = file[_find+1:]
                    
                    if text.find(';') == -1: # Error 3
                        # Removing commas
                        while(text.find(',') != -1):
                            _comma = text.find(',')
                            fName = fName + [text[:_comma]]
                            text = text[_comma+1:]
                        fName = fName + [text]
                        CORVUS = saveData('FUNC', fName, CORVUS, ids, i, c)
                        
                        #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ Dia                 
                        func = func + 1
                        
                        if len(CORVUS.loc[ids[i],'FUNC']) > streak:
                            streak = len(CORVUS.loc[ids[i],'FUNC'])

                        ############################################# From directory V
                        if file[:6] == ' from ': # Error 4
                            
                            file = file[6:]
                            if (file[0] == "\'") and (file.find("\'",1) > -1):
                                file = file[1:]
                                _find = file.find("\'")
                            elif (file[0] == '\"') and (file.find('\"',1) > -1):
                                file = file[1:]
                                _find = file.find('\"')
                            else: 
                                text = ' from '+file[:file.find(';')+1]
                                errorLog = errorLog.append(logError(5, ids[i], c, text),
                                                 ignore_index=True)
                                break# no qoutes found after ' from ' !!!!!!!!!!!!!!! 5
                            
                            text = directoryRoutine(file, _find, directory, ids[i],c)
                            
                            if type(text) == type(pd.Series):
                                errorLog = errorLog.append(text, ingore_index=True)
                                break# zero length !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 0
                                # illegal characters in directory !!!!!!!!!!!!!!!!!!! 6
                            else:
                                temp = saveData('DIR',text,CORVUS,ids,i,c)
                                
                                if type(temp) == type(pd.Series()):
                                    errorLog = errorLog.append(temp, ignore_index=True)
                                    break
                                    # unknown case !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 7
                                    # typo in dirctory string !!!!!!!!!!!!!!!!!!!!!!! 9
                                else:
                                    file = file[_find+1:]
                                    CORVUS = temp.copy()
                                    
                                    #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ Dia
                                    fdir = fdir + 1
                        else: 
                            errorLog = errorLog.append(logError(4, ids[i], c, file),
                                             ignore_index=True)
                            break# no ' from ' found after 'import {' !!!!!!!!!!!!!!! 4
                    else: 
                        errorLog = errorLog.append(logError(3, ids[i], c, text),
                                         ignore_index=True)
                        break# ; found in functions text !!!!!!!!!!!!!!!!!!!!!!!!!!!! 3
                else: 
                    errorLog = errorLog.append(logError(2, ids[i], c, file), ignore_index=True)
                    break# no ending } found in file !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 2
            else: 
                _find = file.find(';')
                text = 'import' + file[:_find+1]
                errorLog = errorLog.append(logError(1, ids[i], c, text), ignore_index=True)
                break# New type of syntax with import detected !!!!!!!!!!!!!!!!!!!!!! 1

    report = [idir, fdir, func, streak]
    dirs = CORVUS.DIR.values
    dirs = pd.Series(range(len(dirs)), index=dirs)
    return CORVUS, dirs, errorLog, report


def decodeID(ID, DIRS):
	return DIRS[DIRS==ID].index.values[0]


def showReport(CORVUS, DIRS, LOG, REPORT, DESCRIPTION, PARTS=[False, True, True]):

	no_dep = CORVUS[CORVUS['DEP'] == 'None']
	no_call = CORVUS[CORVUS['CALL'] == 'None']
	neither = no_dep[no_dep['CALL'] == 'None']
		
	dep = CORVUS[CORVUS['DEP'] != 'None']
	call = CORVUS[CORVUS['CALL'] != 'None']
	both = dep[dep['CALL'] != 'None']
		
	only_dep = dep[dep['CALL'] == 'None']
	only_call = call[call['DEP'] == 'None']
	only_one = pd.concat([only_dep, only_call]).sort_index()

	stats = {'no_dep':no_dep,
			 'no_call':no_call,
			 'neither':neither,
			 'dep':dep,
			 'call':call,
			 'both':both,
			 'only_dep':only_dep,
			 'only_call':only_call,
			 'only_one': only_one}

	# showing detected clouds
	if PARTS[0]:
		print '\t> cloud dependecies:'
		first_cloud = CORVUS[CORVUS['EXT'] == 'cloud'].index[0]
		for cloud in DIRS.index[first_cloud:]:
			print '\t  {}'.format(cloud)
		drawLine()

	# overall report stats
	if PARTS[1]:
		print '\t> overall stats:'
		print '\t  successful \'import\' method:  {:4}'.format(REPORT[0])
		print '\t  successful  \'from\'  method:  {:4}'.format(REPORT[1])
		print '\t  successful function import:  {:4}\n'.format(REPORT[2])
		print '\t  function maximum streak:     {:4}\n'.format(REPORT[3])
		print '\t  files with dependencies:     {:4}'.format(len(dep))
		print '\t  files with only dependencies:{:4}'.format(len(only_dep))
		print '\t  files with no dependencies:  {:4}\n'.format(len(no_dep))
		print '\t  files with calls:            {:4}'.format(len(call))
		print '\t  files with only calls:       {:4}'.format(len(only_call))
		print '\t  files with no calls:         {:4}\n'.format(len(no_call))
		print '\t  files with both:             {:4}'.format(len(both))
		print '\t  files with only one:         {:4}'.format(len(only_one))
		print '\t  files with neither:          {:4}\n'.format(len(neither))
		print '\t  files total:                 {:4}'.format(len(CORVUS))
		drawLine()

	# summary of error types
	if PARTS[2]:
		print '\t> errors:'
		for i,n in enumerate(LOG.E.value_counts()):
			_id = LOG.E.value_counts().index[i]
			print '\t  [{:02}] {:3} {}'.format(_id, n, DESCRIPTION[_id])
		drawLine()
		
	return stats


def getLine(ID, LOG, DIRS, ROOT):
    case = LOG.loc[ID, ['ID', 'INS', 'TEXT']]
    directory = decodeID(case.ID, DIRS)
    with open(ROOT + directory, 'r') as some_file:
        file = some_file.read()
    c = 0
    start = 0
    while(file.find('import', start) > -1):
        c = c + 1
        start = file.find('import')
        if c == case.INS:
            text = file[start:file.find(';') + 1]
            if text == '':
                return 'EMPTY'
            elif text == '\n':
                return 'NEW LINE'
            else:
                return text
        file = file[file.find(';') + 1:]
    return 'NOT FOUND!'


def exportErrors(ROOT, DIRS, LOG, DESCRIPTION, IGNORE=[]):
    file = open('logs/errors.txt', 'w')
    for _type in LOG.E.unique():
        if _type not in IGNORE:
            temp = LOG[LOG.E==_type]
            file.write('###################################################################\n')
            file.write('### ERROR[{:2}]: {}\n'.format(_type, DESCRIPTION[_type]))
            file.write('###################################################################\n')
            for ID in temp.index:
                file.write(' D[{:03}] |{:}\n E[{:03}] |{}\n I[{:03}] |\n'.format(
                    temp.ID[ID], decodeID(temp.ID[ID], DIRS), ID, 
                    getLine(ID, LOG, DIRS, ROOT).replace('\n','\n        |'), temp.INS[ID]))            
                if _type in (7,9):
                    file.write(' *{}\n'.format(temp.TEXT[ID]))
                file.write('-----------------------------------------------------\n')
    file.close()

    with open('logs/errors.txt', 'r') as file:
        error_log = file.read()

    with open('logs/issues.txt', 'w') as file:
        file.write(error_log)













