'''
CompMan computation manager.

Creator: Matthew Brown
Started: 2015-04-13
Last update: 2017-09-24
'''

version = '0.1.0'

import os
import inspect
import types
from collections import OrderedDict

# --------------------
# Exceptions:
class NotCodedYetException(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)

class InvalidMetaparameterError(Exception):
    def __init__(self,cmMetaParam='not provided',*args,**kwargs):
        msg = 'Invalid cmMetaParam value: {}'.format(cmMetaParam)
        Exception.__init__(self,msg,*args,**kwargs)

class InvalidStateError(Exception):
    def __init__(self,msg=None):
        if msg is None:
            msg = 'One or more required member objects is set incorrectly'
        Exception.__init__(self,msg)

class InvalidValueError(Exception):
    def __init__(self):
        Exception.__init__(self,msg)

class CMDuplicateNameError(Exception):
    def __init__(self,name):
        msg = ('Attempt to set name {0} simultaneously in two or '
               'more of self.__dict__, self.cmConfigDict, '
               'self.cmExConfigDict'.format(name))
        Exception.__init__(self,msg)

# --------------------
class CompMan(object):
    '''
    CompMan computation manager:

    Stores configuration parameters and optional dependencies (other
    CompMan instances) that define the identity of a computation.
    
    Provides unique hash string to define computation identity as well
    as cache directories and file names.

    Easiest to treat as immutable - i.e. do not change anything after
    initial creation. If you do change things, make sure you
    understand how those changes affect the computation identity
    defined by the cmHashTag returned by getHashTag().

    ----------
    When inheriting from CompMan, child classes of CompMan must:
      1. In __init__(), must call CompMan.__init__()
      2. Implement getOutput()
      3. Implement getOutputFilesList(), if needed

    ----------
    Core configurable state members, which are also __init__() input arguments:

    cmDesc
      - simple description string to make directory and file lists easier
      to view, eg: 'analysis', 'residuals', 'raw'
      - best not to have spaces in this
      - part of core computation configuration
      - affects the cmHashTag returned by getHashTag() as well as
      the cmTagPrefix returned by getTagPrefix()

    cmCodeTag
      - code tag string
      - should indicate the Python file currently executing (with .py or
      .pyc extension removed) as well as the relevant class of function
      eg: analysiscode_TestMan
      - best not to have spaces in this
      - part of core computation configuration
      - affects the cmHashTag returned by getHashTag() as well as
      the cmTagPrefix returned by getTagPrefix()

    cmMetaParam
      - string, used to set many parameters by specifying just one
      metaparameter
      - best not to have spaces in this
      - part of core computation configuration
      - affects the cmHashTag returned by getHashTag() as well as
      the cmTagPrefix returned by getTagPrefix()

    cmSep (optional)
      - separator character used in output directory and file names
      - defaults to '.'
      - must be a length 1 string, cannot be a space 
      - part of core computation configuration
      - affects the cmHashTag returned by getHashTag() as well as
      the cmTagPrefix returned by getTagPrefix()

    ----------
    Non-core configurable state members:

    cmBasePath (optional)
      - base path where output files will be stored, output
      subdirectory name autogenerated and then appended to basepath
      - defaults to None
      - basepath not part of core config (i.e. config that is hashed
      and defines output identity)
      - if no files are to be stored on disk, this can be None
      eg: if the child class just specifies a list of subjects
      - NOT part of core computation configuration
      - does NOT affect the cmHashTag returned by getHashTag() or
      the cmTagPrefix returned by getTagPrefix()

    ----------
    Other compman things generated on-the-fly and not stored:

    cmHashTag
      - from getHashTag()
      - created using compman_configlist, optionally
      compman_extraconfiglist as well as certain values from each CompMan
      instance in compman_dependencydict
      - key-value pairs first combined in a CSV string, then hash applied
      to that string

    cmTagPrefix
      - from getTagPrefix()
      - tag prefix used in output directory and file names.
        tagprefix has the form:
        <cmDesc tsep cmCodeTag tsep \\
         cmMetaParam tsep cmHashTag>
        where tsep is the cmSep (default '.')
        eg: 'analysis.AnalysisCode.test_20150601.123456789'
      - may be computed with or WITHOUT extra config attributes

    cmOutputPath
      - location where output files are stored:
      cmBasePath/cmDesc/compman_prefix
      - NOTE: compman_prefix is computed WITHOUT extra config
      attributes
      - output files may be generated by the code in a child
      class or user class or else simply 'pointed to' by that code,
      eg: in the case of raw data

    ----------
    Internal configuration dictionaries (cmConfigDict and
    cmExConfigDict):

    NOTE: Use setConfig() and setExConfig() to set name,value pairs in
    the internal configuration dictionaries. Do not access them directly.

    cmConfigDict
      - OrderedDict of core configuration variables
      - affects the cmHashTag returned by getHashTag()
      - Defines core configuration parameters that identify the
      computation. Does not include incidental parameters that one may
      wish to associate with the computation (eg: date, location of
      scratch directories) or extra config variables that affect file
      names and instance hash tags but not directory hash tags  (see
      cmExConfigDict). Definition of 'core' and 'non-core' configuration
      parameters depends on the application and style considerations, in
      some cases.

    cmExConfigDict
      - OrderedDict of extra configuration variables used for file and
      instance hashtag but not directory hashtag
      - affects the cmHashTag returned by getHashTag()
      - Defines extra core configuration parameters that identify the
      computation. Does not include incidental parameters that one may
      wish to associate with the computation (eg: date, location of
      scratch directories). Definition of 'core' and 'non-core'
      configuration parameters depends on the application and style
      considerations, in some cases.

    '''

    def __init__(self,cmDesc,
                      cmCodeTag,
                      cmMetaParam,
                      cmSep          = '.',
                      cmBasePath     = None,
                      cmConfigDict   = None,
                      cmExConfigDict = None):
        self.validateSep(cmSep)
        self.cmDesc         = cmDesc
        self.cmCodeTag      = cmCodeTag
        self.cmMetaParam    = cmMetaParam
        self.cmSep          = cmSep
        self.cmBasePath     = cmBasePath
        self.cmHashTagWithExtraConfig    = None
        self.cmHashTagWithoutExtraConfig = None
        if cmConfigDict is not None:
            self.cmConfigDict = cmConfigDict
        else:
            self.cmConfigDict = OrderedDict()
        if cmExConfigDict is not None:
            self.cmExConfigDict = cmExConfigDict
        else:
            self.cmExConfigDict = OrderedDict()

    def validateSep(self,cmSep):
        if type(cmSep) is not str:
            raise TypeError('cmSep must be a length 1 string')
        if cmSep == ' ':
            raise InvalidValueError('cmSep cannot be a space')
        if len(cmSep) != 1:
            raise InvalidValueError('cmSep must be a length 1 string')

    # --------------------
    # Getters:
    def getDesc(self):
        return self.cmDesc

    def getCodeTag(self):
        return self.cmCodeTag 

    def getMetaParam(self):
        return self.cmMetaParam

    def getSep(self):
        return self.cmSep

    def getConfigDict(self):
        return self.cmConfigDict

    def getExtraConfigDict(self):
        return self.cmExConfigDict

    def getBasePath(self):
        return self.cmBasePath

    def getHashTag(self,includeExtraConfig):
        if includeExtraConfig and self.cmHashTagWithExtraConfig is not None:
            return self.cmHashTagWithExtraConfig
        if not includeExtraConfig and self.cmHashTagWithoutExtraConfig is not None:
            return self.cmHashTagWithoutExtraConfig
        return self.hashOnString(self.generateHashString(includeExtraConfig))

    # --------------------
    # Setters:
    def setDesc(self,cmDesc):
        '''
        Note: This changes the cmHashTag returned by getHashTag()
        '''
        self.cmDesc = cmDesc

    def setCodeTag(self,cmCodeTag):
        '''
        Note: This changes the cmHashTag returned by getHashTag()
        '''
        self.cmCodeTag = cmCodeTag

    def setMetaParam(self,cmMetaParam):
        '''
        Note: This changes the cmHashTag returned by getHashTag()
        '''
        self.cmMetaParam = cmMetaParam

    def setSep(self,cmSep):
        '''
        Note: This changes the cmHashTag returned by getHashTag()
        '''
        self.validateSep(cmSep)
        self.cmSep = cmSep

    def setBasePath(self,cmBasePath):
        self.cmBasePath = cmBasePath

    def setConfig(self,name,value):
        '''
        Sets self.cmExConfigDict[name]=value after checking that
        name is not in self.__dict__ of self.cmExConfigDict. Use
        this in preference to directly accesslying self.cmConfigDict
        to avoid potentially problematic duplication between
        self.__dict__, self.cmConfigDict, and self.cmExConfigDict.
        '''
        if name in self.__dict__ or name in self.cmExConfigDict:
            raise CMDuplicateNameError(name)
        self.cmConfigDict[name] = value

    def setExConfig(self,name,value):
        '''
        Sets self.cmExConfigDict[name]=value after checking that
        name is not in self.__dict__ of self.cmConfigDict. Use
        this in preference to directly accesslying self.cmConfigDict
        to avoid potentially problematic duplication between
        self.__dict__, self.cmConfigDict, and self.cmExConfigDict.
        '''
        if name in self.__dict__ or name in self.cmConfigDict:
            raise CMDuplicateNameError(name)
        self.cmExConfigDict[name] = value

    def cacheHashTag(self):
        '''
        Stores hash tags with and without extraconfig to speed things up.
        '''
        self.cmHashTagWithExtraConfig    = self.getHashTag(True)
        self.cmHashTagWithoutExtraConfig = self.getHashTag(False)

    # --------------------
    def __getattribute__(self,name):
        '''
        If name is not in self, look for it in self.cmConfigDict or
        self.cmExConfigDict.
        Allows use of compManObject.foo instead of
        compManObject.cmConfigDict['foo']
        '''
        if ('cmConfigDict' in object.__getattribute__(self,'__dict__') and
            name in object.__getattribute__(self,'cmConfigDict')):
            return object.__getattribute__(self,'cmConfigDict')[name]
        elif ('cmExConfigDict' in object.__getattribute__(self,'__dict__') and
              name in object.__getattribute__(self,'cmExConfigDict')):
            return object.__getattribute__(self,'cmExConfigDict')[name]
        else:
            return object.__getattribute__(self,name)

    def __setattr__(self,name,value):
        '''
        Prevents duplication of name in self.__dict__, self.cmConfigDict,
        and self.cmExConfigDict.
        '''
        if (('cmConfigDict' in self.__dict__ and name in self.cmConfigDict) or 
            ('cmExConfigDict' in self.__dict__ and name in self.cmExConfigDict)):
            raise CMDuplicateNameError(name)
        object.__setattr__(self,name,value)

    # --------------------
    # Functions for generating stuff:
    def __str__(self,includeHashTag=True,includeExtraConfig=True):
        className = self.__class__.__name__
        string = '<' + className + '>\n'
        attrList = ('cmDesc','cmCodeTag','cmMetaParam','cmSep')
        template = className + ',{0},{1}\n'
        for attrName in attrList:
            string += template.format(attrName, self._getStringValue(getattr(self,attrName),includeExtraConfig))
        if includeHashTag:
            string += template.format('cmHashTag', self.getHashTag(includeExtraConfig))
        for (key,val) in self.cmConfigDict.iteritems():
            string += template.format(key, self._getStringValue(val,includeExtraConfig))
        if includeExtraConfig:
            for (key,val) in self.cmExConfigDict.iteritems():
                string += template.format(key, self._getStringValue(val,includeExtraConfig))
        if string[-1:] == '\n':
            string = string[:-1]
        return string

    def __repr__(self,includeExtraConfig=True):
        return '<{0} object, hashtag {1}>'.format(self.__class__.__name__,self.getHashTag(includeExtraConfig))

    def _getStringValue(self,val,includeExtraConfig):
        '''
        Internal function
        '''
        if type(val) in (types.FunctionType,types.MethodType,types.UnboundMethodType,types.BuiltinFunctionType,types.BuiltinMethodType):
            strVal = val.__name__
        elif issubclass(val.__class__,CompMan):
            strVal = val.__str__(True,includeExtraConfig)
        else:
            strVal = str(val)
        return strVal


    def prettyPrint(self):
        raise Exception('Not coded yet')
        '''
        string = '<Core Configuration>\n'
        attrList = ('cmDesc','cmCodeTag','cmMetaParam','cmSep')
        nameLen = max((max([len(x) for x in attrList]),
                       max([len(x) for x in self.dmConfigDict.keys()]),
                       max([len(x) for x in self.dmExConfigDict.keys()])))
        template = '    {0:>' + str(nameLen) + '} : {1}\n'
        for attrName in attrList:
            string += template.format(attrName, str(getattr(self,attrName)))
        for (key,val) in self.cmConfigDict.iteritems():
            string += template.format(key, __strHelper__(val,offset+7))
        for (key,val) in self.cmExConfigDict.iteritems():
            string += template.format(key, __strHelper__(val,offset+7))
        return string
        '''

    def generateHashString(self,includeExtraConfig):
        '''
        Creates CSV string from key-value pairs in cmConfigDict
        as well as the following five key-values pairs from each
        element in any CompMan dependency:
            cmDesc
            cmCodeTag
            cmMetaParam
            cmSep
            cmHashTag - returned by getHashTag()

        Used for saving configuration in a .csv file and generating
        cmHashTag using hashOnString() - see getHashTag()
        '''
        return self.__str__(includeHashTag=False,includeExtraConfig=includeExtraConfig)

    '''
    def _getStringPiece(self,depAttrName,depMan,includeExtraConfig,index=None):
        string = ''
        for attrName in ('cmDesc','cmCodeTag','cmMetaParam','cmSep'):
            if index is None:
                compoundKey = '{0}_{1}'.format(depAttrName,attrName)
            else:
                compoundKey = '{0}[{1}]_{2}'.format(depAttrName,index,attrName)
            val = 'not_defined' if depMan is None else self._getStringValue(depMan,attrName)
            string += (compoundKey + ',' + val + '\n')
        if index is None:
            compoundKey = '{0}_cmHashTag'.format(depAttrName)
        else:
            compoundKey = '{0}[{1}]_cmHashTag'.format(depAttrName,index)
        val = 'not_defined' if depMan is None else depMan.getHashTag(includeExtraConfig)
        string += (compoundKey + ',' + val + '\n')
        return string
    '''


    # --------------------
    def hashOnString(self,string,alg='djb2'):
        '''
        Creates a hash number from string.
        Algorithm alg choices:
            'djb2' (default)
            'short'
            'sdbm'
        Returns hash string
        '''
        if alg == 'djb2':
            hashnum = 5381
            modulus = 2**32-1
            for c in string:
                hashnum = (hashnum * 33 + ord(c)) % modulus
            hashstr = '{0:010}'.format(hashnum)
        elif alg == 'short':
            hashnum = 5381
            modulus = 2**16-1
            for c in string:
                hashnum = (hashnum * 33 + ord(c)) % modulus
            hashstr = '{0:05}'.format(hashnum)
        elif alg == 'sdbm':
            hashnum = 0
            modulus = 2**32-1
            for c in string:
                hashnum = (hashnum * 65599 + ord(c)) % modulus
            hashstr = '{0:010}'.format(hashnum)
        else:
            raise Exception('Invalid hash algorith: {}'.format(alg))
        return hashstr

    def getTagPrefix(self,includeExtraConfig):
        '''
        Return tag prefix used in output directory and file names.
        Prefix has the form:
        cmDesc tsep cmCodeTag tsep ...
            cmMetaParam tsep cmHashTag
        where tsep is the cmSep (default '.')
        eg: 'analysis.AnalysisCode.test_20150601.123456789'

        Used in cache directory and file names.
        '''
        return self.cmSep.join([self.cmDesc,self.cmCodeTag,self.cmMetaParam,self.getHashTag(includeExtraConfig)])

    def getTagPrefixHashSep(self,includeExtraConfig):
        '''
        Returns (first_part_of_prefix,separator,hashtag)
        '''
        return (self.cmSep.join([self.cmDesc,self.cmCodeTag,self.cmMetaParam]),self.cmSep,self.getHashTag(includeExtraConfig))

    def getOutput(self):
        '''
        Must be implemented by child class.
        Returns the output.
        '''
        raise NotImplementedError('Must be implemented by child class.')

    def getOutputPath(self):
        if self.cmBasePath is None:
            raise TypeError('self.cmBasePath must be a string, not None')
        dirname = self.getTagPrefix(includeExtraConfig=False)
        return os.path.join(self.cmBasePath,self.cmDesc,dirname)

    def getOutputFilesList(self):
        '''
        Must be implemented by child class.
        Returns a list of filename or filepaths.
        '''
        raise NotImplementedError('Must be implemented by child class.')

    def getConfigCSVFilePath(self):
        fileName = 'compman_config.{}.csv'.format(self.getTagPrefix(includeExtraConfig=True))
        return os.path.join(self.getOutputPath(),fileName)

    def generateCompoundMetaParameter(self,local_metaparameter,dependenciesList):
        '''
        Used for combining local metaparameter and dependency
        metaparameters into a short compound_metaparameter,
        while avoiding arbitrary growth in metaparameter length that
        would happen if we simply concatenated all dependency
        metaparameters.
        local_metaparameter : string
        dependenciesList    : list of CompMan objects
        Returns compound_metaparameter
        '''
        string = ''
        for man in dependenciesList:
            string += '_' + man.getMetaParam()
        return local_metaparameter + '_' + self.hashOnString(string,alg='short')

    # --------------------
    def makeOutputPath(self):
        outputPath = self.getOutputPath()
        if not os.path.isdir(outputPath):
            os.makedirs(outputPath)

    def saveConfigCSVFile(self,forceRebuild=False):
        self.makeOutputPath()
        filePath = self.getConfigCSVFilePath()
        if not os.path.isfile(filePath) or forceRebuild:
            string = self.generateHashString(includeExtraConfig=True)
            with open(filePath,'w') as f:
                f.write(string)

    # --------------------
    def configure(self,metaParam=None):
        '''
        Dispatches configuration to
        configure_<self.cmMetaParam> function,
        which child class must implement.
        '''
        if metaParam == None:
            metaParam = self.cmMetaParam
        funcName   = 'configure_{}'.format(metaParam)
        func       = getattr(self,funcName,None)
        if func == None:
            raise InvalidMetaparameterError(metaParam)
        func() # configure self in-place
        self.cacheHashTag()

# --------------------
class TemplateMan(CompMan):
    '''
    Template child class of CompMan.
    '''
    def __init__(self,cmMetaParam,cmBasePath):
        cmDesc        = 'TemplateMan example class'
        cmCodeTag     = os.path.splitext(os.path.split(inspect.getfile(inspect.currentframe()))[1])[0] + '_' + type(self).__name__
        CompMan.__init__(self,cmDesc,cmCodeTag,cmMetaParam=cmMetaParam,cmBasePath=cmBasePath)

# --------------------
class TestMan(CompMan):
    '''
    Template child class of CompMan.
    '''
    def __init__(self,cmMetaParam,cmBasePath):
        cmDesc        = 'TestMan test class'
        cmCodeTag     = os.path.splitext(os.path.split(inspect.getfile(inspect.currentframe()))[1])[0] + '_' + type(self).__name__
        CompMan.__init__(self,cmDesc,cmCodeTag,cmMetaParam=cmMetaParam,cmBasePath=cmBasePath)
        self.configure(self.cmMetaParam)

    def configure_testparam(self):
        if self.cmMetaParam != 'testparam':
            raise InvalidMetaparameterError(self.cmMetaParam)
        self.cmConfigDict['field1'] = 100
        self.cmConfigDict['field2'] = 200
        self.cmConfigDict['field3'] = 'a string field'
        self.cmConfigDict['templateMan1'] = TemplateMan('p1',self.cmBasePath)
        self.cmConfigDict['templateMan2'] = TemplateMan('p2',self.cmBasePath)
        self.cmExConfigDict['templateMan3'] = TemplateMan('p2',self.cmBasePath)

# --------------------
def getCurrentCodeFile(keepExtension=False):
    '''
    Supposed to return filename (minus extension) of code. Not fully implmented yet.
    '''
    raise Exception("Not fully implemented - always returns 'compman'")
    if keepExtension:
        return os.path.split(inspect.getfile(inspect.currentframe()))[1] # code filename (usually with path)
    else:
        return os.path.splitext(os.path.split(inspect.getfile(inspect.currentframe()))[1])[0] # code filename (usually with path)

# --------------------
def main():
    tm = TestMan('testparam','a/b/c')
    print(tm)
    print('\n\nhashtag WITHOUT extra: {0}'.format(tm.getHashTag(True)))
    print('\n\nhashtag WITH extra   : {0}'.format(tm.getHashTag(False)))

# --------------------
if __name__ == '__main__':
    print(getCurrentCodeFile())
