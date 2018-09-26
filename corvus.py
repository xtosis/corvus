from os import walk
from os.path import join
import pandas as pd
pd.set_option('display.max_colwidth', 200)


def drawLine():
    print '-------------------------------------------------------------------'


def getFile(ROOT, DF, ID, SHOW=False):
    directory = ROOT + DF.loc[ID, 'DIR']
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
    data = summary['Count'].values
    index = summary['Extension'].values
    summary = pd.Series(data=data, index=index).sort_values(ascending=False)
    return summary


def inspectExtension(DF, EXT):
    directories = DF[DF['EXT'] == EXT]
    directories = directories['DIR'].values.tolist()
    for directory in directories:
        print '\t  {}'.format(directory)
    return None


def generateCorvus(ROOT, FIX=None, DROP_EXT=None, VERBOSE=0, DROP_UNK=True):
    df = []
    for r, d, f in walk(ROOT):  # getting all files within ROOT
        for file in f:
            df.append([getExtension(file),
                       join(r, file).replace(ROOT, '').replace('\\', '/')])

    df = pd.DataFrame(df, columns=['EXT', 'DIR'])
    drawLine()

    # reporting raw
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
            length = len(extensionSummary(df))
            print 'C0RVUS| removed UNK extensions'
            print 'C0RVUS| {:03} directories to be tracked'.format(len(df)),
            print 'with {:02} unique extensions'.format(length)
            if VERBOSE > 1:
                summary = extensionSummary(df)
                for i in summary.index:
                    print '{:5} | {}'.format(summary[i], i)
                drawLine()

    # fixing some extensions
    if FIX is not None:
        df.replace(FIX, inplace=True)
        if VERBOSE > 0:
            length = len(extensionSummary(df))
            print 'C0RVUS| fixed extentions'
            print 'C0RVUS| {:03} directories to be tracked'.format(len(df)),
            print 'with {:02} unique extensions'.format(length)
        if VERBOSE > 1:
            summary = extensionSummary(df)
            for i in summary.index:
                print '{:5} | {}'.format(summary[i], i)
            drawLine()

    # dropping some extensions
    if DROP_EXT is not None:
        if VERBOSE > 1:
            print 'C0RVUS| extensions to drop:'

        for extension in DROP_EXT:
            if VERBOSE > 1:
                print '\t> *{}'.format(extension)
                inspectExtension(df, extension)
            df = df[df.EXT != extension]

        # reporting dropped extensions
        if VERBOSE > 0:
            length = len(extensionSummary(df))
            print 'C0RVUS| dropped specified extensions'
            print 'C0RVUS| {:03} directories to be tracked'.format(len(df)),
            print 'with {:02} unique extensions'.format(length)
            summary = extensionSummary(df)
            for i in summary.index:
                print '{:5} | {}'.format(summary[i], i)

    # sorting df
    df = df.append({'EXT': 'YOU', 'DIR': 'YOU'}, ignore_index=True)
    df = df.sort_values(['DIR'], ascending=False).reset_index(drop=True)

    # creating new columns
    n_files = df.shape[0]
    for col in ['DEP', 'CALL', 'FUNC', 'CHAR', 'DESC']:
        df[col] = ['None'] * n_files

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
    return pd.Series([LEVEL, ID, C, STR], index=['E', 'ID', 'INS', 'TEXT'])


def directoryRoutine(TEXT, END, CURRENT_DIR, ID, C):
    text = TEXT[:END]
    error = False
    for char in ('{', '}', '[', ']', '(', ')', ';', '\n', '\t'):
        if text.find(char) > -1:
            error = True
            break

    if error:
        return logError(5, ID, C, text)
        # illegal characters in directory !!!!!!!!!!!!!!!!!!!!!!!!!! 5 [UPDATE]
    else:
        if len(text) == 0:
            return logError(0, ID, C, 'ZERO LENGTH')
            # zero length !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 0 [UPDATE]

        elif text[0] == '/':
            return text

        elif text[0:2] == './':
            END = 0
            while(CURRENT_DIR.find('/', END) > -1):
                END = CURRENT_DIR.find('/', END) + 1
            return text.replace('.', CURRENT_DIR[:END - 1], 1)

        elif text[0:2] == '..':
            start = 0
            back = 1
            while(text.find('..', start) > -1):
                start = text.find('..', start) + 2
                back = back + 1
            END = 0
            locs = []
            while(CURRENT_DIR.find('/', END) > -1):
                locs = locs + [CURRENT_DIR.find('/', END)]
                END = CURRENT_DIR.find('/', END) + 1
            return CURRENT_DIR[:locs[-back]] + text[start:]

        else:
            return text  # implies cloud based import


def saveData(COL, DATA, DF, ID, i, C, mode='all'):
    error7 = False
    if COL == 'DIR':
        dep_id = []
        for n, sample in enumerate(DF.DIR.values):
            if sample.find(DATA) == 0:
                if DATA == sample:
                    error7 = False
                    dep_id = [n]
                    break
                elif DATA + '.js' == sample:
                    error7 = False
                    dep_id = [n]
                    break
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
            return logError(6, ID[i], C, DATA)
            # unknown case !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 6 [UPDATE]
        elif len(dep_id) == 0:
            if (DATA[0] != '/') and (DATA.find('.') == -1):
                if mode == 'cond':
                    data = ['cloud', DATA, 'None', [ID[i]],
                            'None', 'None', 'None']
                else:
                    data = ['cloud', DATA, 'None', ['*{}'.format(ID[i])],
                            'None', 'None', 'None']
                new_dir = pd.Series(data, index=DF.columns.values)
                return DF.append(new_dir, ignore_index=True)
                # new cloud based dependacy ########################## [UPDATE]
            else:
                return logError(8, ID[i], C, DATA)
                # typo in directory string or file does not exist !! 8 [UPDATE]
        else:
            for dep in dep_id:
                if DF.loc[ID[i], 'DEP'] == 'None':
                    if mode == 'cond':
                        DF.loc[ID[i], 'DEP'] = ['*{}'.format(dep)]
                    else:
                        DF.loc[ID[i], 'DEP'] = [dep]
                elif dep not in DF.loc[ID[i], 'DEP']:
                    if mode == 'cond':
                        DF.loc[ID[i], 'DEP'].append('*{}'.format(dep))
                    else:
                        DF.loc[ID[i], 'DEP'].append(dep)
                else:
                    return logError(9, ID[i], C, DATA)
                    # duplicate entry !!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 9 [UPDATE]
                if DF.loc[dep, 'CALL'] == 'None':
                    if mode == 'cond':
                        DF.loc[dep, 'CALL'] = ['*{}'.format(ID[i])]
                    else:
                        DF.loc[dep, 'CALL'] = [ID[i]]
                else:
                    if mode == 'cond':
                        DF.loc[dep, 'CALL'].append('*{}'.format(ID[i]))
                    else:
                        DF.loc[dep, 'CALL'].append(ID[i])
            return DF
            # new directory based dependecies ######################## [UPDATE]
    else:
        if DF.loc[ID[i], COL] == 'None':
            if mode == 'cond':
                DF.loc[ID[i], COL] = ['*{}'.format(DATA)]
            else:
                DF.loc[ID[i], COL] = [DATA]
        else:
            if COL == 'FUNC':
                # !!! going to have a problem here for multiple functions
                # !!! that are called by the require method
                if DATA not in DF.loc[ID[i], COL]:
                    if mode == 'cond':
                        DF.loc[ID[i], COL].append('*{}'.format(DATA))
                    else:
                        DF.loc[ID[i], COL].append(DATA)
                else:
                    return logError(9, ID[i], C, DATA)
                    # duplicate entry !!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 9 [UPDATE]
            else:
                DF.loc[ID[i], COL].append(DATA)
        return DF
        # saving all other types of data ############################# [UPDATE]


def decodeID(ID, DIRS):
    return DIRS[DIRS == ID].index.values[0]


def searchCorvus(ROOT, CORVUS, MIN_CHARS, CLEAN=True):
    ids = CORVUS[CORVUS['EXT'] == '.js'].index.values.astype(int)
    directories = CORVUS[CORVUS['EXT'] == '.js'].DIR.values
    errorLog = pd.DataFrame(columns=['E', 'ID', 'INS', 'TEXT'])
    idir, fdir, func, ireq, freq, streak = 0, 0, 0, 0, 0, 0

    for i, directory in enumerate(directories):
        # importing the text from file
        with open(ROOT + directory, 'r') as js_file:
            backup = js_file.read()

        c = 0  # ith instance of an import or require that program broke at

        if len(backup) < MIN_CHARS:
            log = logError(-1, ids[i], c, 'TOO SHORT')
            errorLog = errorLog.append(log, ignore_index=True)
            search = False  # too short !!!!!!!!!!!!!!!!!!!!!!!!!!! -1 [UPDATE]
        else:
            search = True

        if CLEAN and search:  # Cleaning

            sin_com, start = 0, 0
            while backup.find('//', start) > -1:
                start = backup.find('//', start)
                end = backup.find('\n', start)
                comment = backup[start:end].replace('\t', '')
                comment = comment.replace('  ', ' ')
                while comment.find('///') > -1:
                    comment = comment.replace('///', '//')
                put = '//[{:05}]'.format(sin_com)
                if start < 2:
                    backup = put + backup[end:]
                else:
                    backup = backup[:start - 1] + put + backup[end:]
                start = start + 2
                sin_com = sin_com + 1
                CORVUS = saveData('DESC', comment, CORVUS, ids, i, c)
                # saving single line comment ######################### [UPDATE]

            blk_com, start = 0, 0
            while backup.find('/*', start) > -1:
                start = backup.find('/*', start)
                end = backup.find('*/', start)
                if backup.find('*/', end + 2) > -1:
                    _find = backup.find('*/', end + 2)
                    temp = backup[end + 2: _find]
                    if temp.find('/*') == -1:
                        end = _find
                comment = backup[start + 2:end].replace('\t', '')
                comment = comment.replace('  ', ' ')
                while comment.find('///') > -1:
                    comment = comment.replace('///', '//')
                put = '/*[{:05}]'.format(blk_com)
                if start < 2:
                    backup = put + backup[end:]
                else:
                    backup = backup[:start - 1] + put + backup[end:]
                start = start + 2
                blk_com = blk_com + 1
                CORVUS = saveData('DESC', comment, CORVUS, ids, i, c)
                # block comment ###################################### [UPDATE]

            name = directory.replace('/', '_')
            name = name.replace('.js', '.txt')
            name = 'backup/no_com/{}'.format(name[1:])
            with open(name, 'w+') as sample:
                sample.write(backup)

            backup = backup.replace('\n', '')
            backup = backup.replace('\t', '')
            backup = backup.replace('  ', ' ')
            backup = backup.replace('///', '//')

        # =========================== I M P O R T =============================
        file = backup.replace('require(\'/import', '')
        while(search and (file.find('import') != -1)):
            c = c + 1
            case = file[file.find('import'):]
            case = case[:case.find(';') + 1]

            # direct import directory ------------------------------- [SECTION]
            _find = file.find('import')  # !!! shorten
            file = file[_find + 6:]
            f_name = []  # stores function name

            if file[:2] in (" \'", ' \"'):
                if (file[:2] == " \'") and (file.find("\'", 2) > -1):
                    file = file[2:]
                    _find = file.find("\'")
                elif (file[:2] == '\"') and (file.find('\"', 2) > -1):
                    file = file[2:]
                    _find = file.find('\"')
                else:
                    log = logError(7, ids[i], c, file)
                    errorLog = errorLog.append(log, ignore_index=True)
                    break  # no ending quot!!!!!!!!!!!!!!!!!!!!!!!!! 7 [UPDATE]

                text = directoryRoutine(file, _find, directory, ids[i], c)

                if isinstance(text, type(pd.Series())):
                    errorLog = errorLog.append(text, ingore_index=True)
                    break  # zero length !!!!!!!!!!!!!!!!!!!!!!!!!!! 0 [UPDATE]
                    # illegal characters in directory !!!!!!!!!!!!!! 5 [UPDATE]
                else:
                    temp = saveData('DIR', text, CORVUS, ids, i, c)
                    if isinstance(temp, type(pd.Series())):
                        errorLog = errorLog.append(temp, ignore_index=True)
                        break  # unknown case !!!!!!!!!!!!!!!!!!!!!! 6 [UPDATE]
                        # duplicate entry !!!!!!!!!!!!!!!!!!!!!!!!!! 9 [UPDATE]
                # typo in directory string or file does not exist !! 8 [UPDATE]
                    else:
                        file = file[_find + 1:]
                        CORVUS = temp.copy()
                        # new directory based dependecies ############ [UPDATE]
                        idir = idir + 1  # $$$$$$$$$$$$$$$$$$$$$$$$ [DIAGNOSIS]

            # function name ----------------------------------------- [SECTION]
            elif file[0] == ' ':
                file = file[1:]
                _find = file.find(' from ')

                if _find != -1:  # else error 2
                    text = file[:_find].replace(' ', '')
                    text = text.replace('{', '')
                    text = text.replace('}', '')
                    file = file[_find + 6:]

                    if text.find(';') == -1:  # else error 3
                        while(text.find(',') != -1):  # removing commas
                            _comma = text.find(',')
                            f_name = f_name + [text[:_comma]]
                            text = text[_comma + 1:]

                        f_name = f_name + [text]
                        temp = saveData('FUNC', f_name, CORVUS, ids, i, c)

                        if isinstance(temp, type(pd.Series())):
                            errorLog = errorLog.append(temp, ignore_index=True)
                            break  # duplicate entry !!!!!!!!!!!!!!! 9 [UPDATE]
                        else:
                            CORVUS = temp.copy()
                            # new function call detected ############# [UPDATE]
                            func = func + 1  # $$$$$$$$$$$$$$$$$$$$ [DIAGNOSIS]
                            if len(CORVUS.loc[ids[i], 'FUNC']) > streak:
                                streak = len(CORVUS.loc[ids[i], 'FUNC'])
                                # $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ [DIAGNOSIS]

                        # import directory with from method --------- [SECTION]
                        if file[0] == "\'" and file.find("\'", 1) > -1:
                            file = file[1:]
                            _find = file.find("\'")
                        elif file[0] == '\"' and file.find('\"', 1) > -1:
                            file = file[1:]
                            _find = file.find('\"')
                        else:
                            text = ' from ' + file[:file.find(';') + 1]
                            log = logError(4, ids[i], c, text)
                            log.name = len(errorLog)
                            errorLog = errorLog.append(log)
                            break
                            # no qoutes found after ' from ' !!!!!!! 4 [UPDATE]

                        text = directoryRoutine(file, _find, directory, ids[i],
                                                c)

                        if isinstance(text, type(pd.Series())):
                            text.name = len(errorLog)
                            errorLog = errorLog.append(text)
                            break  # zero length !!!!!!!!!!!!!!!!!!! 0 [UPDATE]
                            # illegal characters in directory !!!!!! 5 [UPDATE]
                        else:
                            temp = saveData('DIR', text, CORVUS, ids, i, c)
                            if isinstance(temp, type(pd.Series())):
                                temp.name = len(errorLog)
                                errorLog = errorLog.append(temp)
                                break  # unknown case !!!!!!!!!!!!!! 6 [UPDATE]
                                # duplicate entry !!!!!!!!!!!!!!!!!! 9 [UPDATE]
                # typo in directory string or file does not exist !! 8 [UPDATE]
                            else:
                                file = file[_find + 1:]
                                CORVUS = temp.copy()
                                # new directory based dependecies #### [UPDATE]
                                fdir = fdir + 1  # $$$$$$$$$$$$$$$$ [DIAGNOSIS]
                    else:
                        # log = logError(3, ids[i], c, text)
                        log = logError(3, ids[i], c, case)
                        errorLog = errorLog.append(log, ignore_index=True)
                        break  # ; found in functions text !!!!!!!!! 3 [UPDATE]
                else:
                    # log = logError(2, ids[i], c, file)
                    log = logError(2, ids[i], c, case)
                    errorLog = errorLog.append(log, ignore_index=True)
                    break  # no ' from ' found after 'import ' !!!!! 2 [UPDATE]
            else:
                # end = file.find(';')
                # text = 'import' + file[:end + 1]
                log = logError(1, ids[i], c, case)
                errorLog = errorLog.append(log, ignore_index=True)
                break  # New type of syntax with import detected !!! 1 [UPDATE]

        # ========================== R E Q U I R E ============================
        c, file = 0, backup
        while(search and (file.find('require(\'') != -1)):
            c = c + 1
            case = file[file.find('require(\''):]
            case = case[:case.find(';') + 1].replace('\n', '\n\t       |')

            # require import directory ------------------------------ [SECTION]
            file = file[file.find('require(\'') + 9:]
            _find = file.find('\')')

            temp = directoryRoutine(file, _find, directory, ids[i], c)

            if isinstance(temp, type(pd.Series())):
                errorLog = errorLog.append(temp, ingore_index=True)
                break  # zero length !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 0 [UPDATE]
                # illegal characters in directory !!!!!!!!!!!!!!!!!! 5 [UPDATE]
            else:
                temp = saveData('DIR', temp, CORVUS, ids, i, c, mode='cond')
                if isinstance(temp, type(pd.Series())):
                    errorLog = errorLog.append(temp, ignore_index=True)
                    break  # unknown case !!!!!!!!!!!!!!!!!!!!!!!!!! 6 [UPDATE]
                    # duplicate entry !!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 9 [UPDATE]
                # typo in directory string or file does not exist !! 8 [UPDATE]
                else:
                    # CORVUS = temp.copy()
                    ireq = ireq + 1
                    # new directory based dependecy ################## [UPDATE]

            # require import function ------------------------------- [SECTION]
            text = file[_find:file.find(';')]
            f_name = []

            if len(text) > 2:
                # print '> {}'.format(text)
                text = text[2:]
                # print '    {}'.format(text)
                if text[0] == '.':
                    text = text[1:]
                    if text.find('.') != -1:
                        text = text[:text.find('.')]
                    elif text.find('(') != -1:
                        text = text[:text.find('(')]
                    # print '     {}'.format(text)

                    f_name = f_name + [text]
                    temp = saveData('FUNC', f_name, CORVUS, ids, i, c,
                                    mode='cond')

                    if isinstance(temp, type(pd.Series())):
                        errorLog = errorLog.append(temp, ignore_index=True)
                        break  # duplicate entry !!!!!!!!!!!!!!!!!!! 9 [UPDATE]
                    else:
                        # CORVUS = temp.copy()
                        freq = freq + 1
                        # new function call detected ################# [UPDATE]
                else:
                    print '\tD[{:03}] |{}'.format(ids[i], directory)
                    print '\tI[{:03}] |{}'.format(c, case)
                    drawLine()
            else:
                pass  # !!! func not detected with import

    print '\t> dircs', ireq
    print '\t> funcs', freq
    drawLine()
    report = [idir, fdir, func, streak]
    dirs = CORVUS.DIR.values
    dirs = pd.Series(range(len(dirs)), index=dirs)
    return CORVUS, dirs, errorLog, report


def showReport(CORVUS, DIRS, LOG, REPORT, DESC, PARTS=[False, True, True]):
    no_dep = CORVUS[CORVUS['DEP'] == 'None']
    no_call = CORVUS[CORVUS['CALL'] == 'None']
    neither = no_dep[no_dep['CALL'] == 'None']
    dep = CORVUS[CORVUS['DEP'] != 'None']
    call = CORVUS[CORVUS['CALL'] != 'None']
    both = dep[dep['CALL'] != 'None']
    only_dep = dep[dep['CALL'] == 'None']
    only_call = call[call['DEP'] == 'None']
    only_one = pd.concat([only_dep, only_call]).sort_index()

    stats = {'no_dep': no_dep, 'no_call': no_call, 'neither': neither,
             'dep': dep, 'call': call, 'both': both,
             'only_dep': only_dep, 'only_call': only_call,
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
        for i, n in enumerate(LOG.E.value_counts()):
            _id = LOG.E.value_counts().index[i]
            print '\t  [{:02}] {:3} {}'.format(_id, n, DESC[_id])
        drawLine()

    return stats


def getLine(ID, LOG, DIRS, ROOT):
    case = LOG.loc[ID, ['ID', 'INS', 'TEXT']]
    directory = decodeID(case.ID, DIRS)
    with open(ROOT + directory, 'r') as some_file:
        file = some_file.read()

    if case.TEXT == 'TOO SHORT':
        if file == '':
            return 'EMPTY'
        else:
            return file
    else:
        c, start, pre = 0, 0, 0

        if file.find(';') != -1:
            pre = file.find(';') + 1
            if file[pre] == '\n':
                pre = pre + 1

        while(file.find('import', start) != -1):  # !!! include require cases
            c = c + 1
            start = file.find('import')

            while (file[start - 1] != ';') and (start > 0):
                start = start - 1

            if c == case.INS:
                text = file[start:file.find(';', start) + 1]
                if text == '':
                    return 'EMPTY'
                elif text == '\n':
                    return 'NEW LINE'
                else:
                    return text
            file = file[file.find(';') + 1:]
        return 'NOT FOUND!'


def exportErrors(ROOT, DIRS, LOG, DESC, IGNORE=[], ISSUES=True):
    file = open('logs/errors.txt', 'w')
    for _type in LOG.E.unique():
        if _type not in IGNORE:
            temp = LOG[LOG.E == _type]
            file.write('#####################################################')
            file.write('##########\n')
            file.write('### ERROR[{:2}]: {}\n'.format(_type, DESC[_type]))
            file.write('#####################################################')
            file.write('##########\n')
            for ID in temp.index:
                _id = temp.ID[ID]

                line = getLine(ID, LOG, DIRS, ROOT).replace('\n\n', '\n')
                if line[0] == '\n':
                    line = line[1:]
                line = line.replace('\n', '\n        |')

                file.write(' D[{:03}] |{}\n'.format(_id, decodeID(_id, DIRS)))
                file.write(' E[{:03}] |{}\n'.format(ID, line))
                file.write(' I[{:03}] |\n'.format(temp.INS[ID]))
                if _type in (7, 9):
                    file.write(' *{}\n'.format(temp.TEXT[ID]))
                file.write('-------------------------------------------------')
                file.write('--------------\n')
    file.close()

    if ISSUES:
        with open('logs/errors.txt', 'r') as file:
            error_log = file.read()

        with open('logs/issues.txt', 'w') as file:
            file.write(error_log)
