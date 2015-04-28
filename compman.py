'''
CompMan computation manager.

Creator: Matthew Brown
Started: 2015-04-13
'''

version = '0.1.0'

import os
import inspect
from collections import OrderedDict

class NotCodedYetException(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)

class InvalidMetaparameterError(Exception):
    def __init__(self,compman_metaparameter,*args,**kwargs):
        msg = 'Invalid compman_metaparameter value: {}'.format(compman_metaparameter)
        Exception.__init__(self,msg,*args,**kwargs)

class InvalidStateError(Exception):
    def __init__(self,msg=None):
        if msg is None:
            msg = 'One or more required member objects is set incorrectly'
        Exception.__init__(self,msg)

class InvalidValueError(Exception):
    def __init__(self):
        Exception.__init__(self,msg)

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
    defined by the compman_hashtag returned by getHashTag().

    ----------
    Including a CompMan member variable in a user class's
    __init__() function:
    compman_description   = 'awesome_description'
    compman_codetag       = 'codefile_classname'
    compman_metaparameter = 'config1001'
    compman = CompMan(compman_description,
                      compman_codetag, 
                      compman_metaparameter)
    % set extra domain-specific configuration key-value pairs
    compman.set(key1,val1)
    compman.set(key2,val2)
    compman.set(key3,val3)
    compman.set(key4,val4)
    % set dependencies (other CompMan objects)
    compman.setDep(depkey1,compManDep1)
    compman.setDep(depkey2,compManDep2)
    compman.setDep(depkey3,compManDep3)
    self.compman = compman % store compman as a member variable

    ----------
    When inheriting from CompMan, child classes of CompMan must:
      1. In __init__(), must do:
         1. First, call CompMan.__init__()
         2. Call set(key,value) to add any required configuration
            key-value pairs to self.compman_configdict
         3. Call setDep(depkey,compManInstance) to add any
            required dependencies to self.compman_dependencydict
      2. Implement generateManifestFilesList(), if needed

    ----------
    __init__() input arguments:

    compman_description
      - simple description string to make directory and file lists easier
      to view, eg: 'analysis', 'residuals', 'raw'
      - best not to have spaces in this
      - part of core computation configuration
      - affects the compman_hashtag returned by getHashTag() as well as
      the compman_tagprefix returned by getTagPrefix()

    compman_codetag
      - code tag string
      - should indicate the Python file currently executing (with .py or
      .pyc extension removed) as well as the relevant class of function
      eg: analysiscode_TestMan
      - best not to have spaces in this
      - part of core computation configuration
      - affects the compman_hashtag returned by getHashTag() as well as
      the compman_tagprefix returned by getTagPrefix()

    compman_metaparameter
      - string, used to set many parameters by specifying just one
      metaparameter
      - best not to have spaces in this
      - part of core computation configuration
      - affects the compman_hashtag returned by getHashTag() as well as
      the compman_tagprefix returned by getTagPrefix()

    compman_tagseparator (optional)
      - separator character used in output directory and file names
      - defaults to '.'
      - must be a length 1 string, cannot be a space 
      - part of core computation configuration
      - affects the compman_hashtag returned by getHashTag() as well as
      the compman_tagprefix returned by getTagPrefix()

    compman_basepath (optional)
      - base path where manifest files will be stored, output
      subdirectory name autogenerated and then appended to basepath
      - defaults to None
      - basepath not part of core config (i.e. config that is hashed
      and defines output identity)
      - if no files are to be stored on disk, this can be None
      eg: if the child class just specifies a list of subjects
      - NOT part of core computation configuration
      - does NOT affect the compman_hashtag returned by getHashTag() or
      the compman_tagprefix returned by getTagPrefix()

    ----------
    Core configurable state members:

    compman_configdict
      - core configuration parameters stored in an OrderedDict (from
      collections module)
      - part of core computation configuration
      - affects the compman_hashtag returned by getHashTag()
      - Defines core configuration parameters that identify the
      computation. Does not include incidental parameters that one may
      wish to associate with the computation (eg: date, location of
      scratch directories). Definition of 'core' and 'non-core'
      configuration parameters depends on the application and style
      considerations, in some cases.
      - basic version generated by:
          generateBasicConfigDict()
          generateBasicConfigDictFromMembers()
      - first four keys are always: compman_description,
      compman_codetag, compman_metaparameter, compman_tagseparator
      - values can get get/set with CompMan.get() and CompMan.set()

      compman_dependencydict
      - core dependencies (other CompMan instances) stored in an
      OrderedDict (from collections module)
      - part of core computation configuration
      - affects the compman_hashtag returned by getHashTag()
      - dependencies can get get/set with getDep()/ setDep()

    compman_dependencyDict
      - OrderedDict of other CompMan objects that the current instance
      needs
      - part of core computation configuration
      - affects the compman_hashtag returned by getHashTag() as well as
      the compman_tagprefix returned by getTagPrefix()

    ----------
    Other compman things generated on-the-fly and not stored:

    compman_hashtag
      - from getHashTag()
      - created using compman_configdict as well as certain values
      from each CompMan instance in compman_dependencydict
      - key-value pairs first combined in a CSV string, then hash applied
      to that string

    compman_tagprefix
      - from getTagPrefix()
      - tag prefix used in output directory and file names.
        tagprefix has the form:
        <compman_description tsep compman_codetag tsep \\
         compman_metaparameter tsep compman_hashtag>
        where tsep is the compman_tagseparator (default '.')
        eg: 'analysis.AnalysisCode.test_20150601.123456789'

    compman_manifestpath
      - from getManifestPath()
      - compman_basepath/compman_description/compman_prefix
      - location where delivered manifest files is stored
      - delivered manifest files may be generated by the code in a child
      class or user class or else simply 'pointed to' by that code,
      eg: in the case of raw data

    '''

    def __init__(self,compman_description,
                      compman_codetag,
                      compman_metaparameter,
                      compman_tagseparator   = '.',
                      compman_basepath       = None):
        self.validateTagSeparator(compman_tagseparator)
        self.compman_description    = compman_description
        self.compman_codetag        = compman_codetag 
        self.compman_metaparameter  = compman_metaparameter
        self.compman_tagseparator   = compman_tagseparator
        self.compman_configdict     = self.generateBasicConfigDictFromMembers()
        self.compman_dependencydict = OrderedDict()
        self.compman_basepath       = compman_basepath

    def validateTagSeparator(self,compman_tagseparator):
        if type(compman_tagseparator) is not str:
            raise TypeError('compman_tagseparator must be a length 1 string')
        if compman_tagseparator == ' ':
            raise InvalidValueError('compman_tagseparator cannot be a space')
        if len(compman_tagseparator) != 1:
            raise InvalidValueError('compman_tagseparator must be a length 1 string')

    # --------------------
    # Getters:
    def get(self,key):
        '''
        Returns self.compman_configdict[key]
        '''
        return self.compman_configdict[key]

    def getDep(self,depkey):
        '''
        Returns self.compman_dependencydict[depkey]
        '''
        return self.compman_dependencydict[depkey]

    def getConfigDict(self):
        return self.compman_configdict

    def getDependencyDict(self):
        return self.compman_dependencydict

    def getDescription(self):
        return self.compman_description

    def getCodeTag(self):
        return self.compman_codetag 

    def getMetaParameter(self):
        return self.compman_metaparameter

    def getTagSeparator(self):
        return self.compman_tagseparator

    def getBasePath(self):
        return self.compman_basepath

    def getHashTag(self):
        if self.compman_configdict is None:
            raise InvalidStateError('self.compman_configdict must be an OrderedDict, not None)')
        return self.hashOnString(self.generateCSVConfigString(self.compman_configdict,self.compman_dependencydict))

    # --------------------
    # Setters:
    def set(self,key,value):
        '''
        Sets self.compman_configdict[key] = value
        Note: This changes the compman_hashtag returned by getHashTag()
        '''
        if key in ('compman_description','compman_codetag','compman_metaparameter','compman_tagseparator'):
            raise KeyError("Do not change '{0}' with set(). Use one of the dedicated setter functions.".format(key))
        self.compman_configdict[key] = value

    def setDep(self,depkey,compManInstance):
        '''
        Note: This changes the compman_hashtag returned by getHashTag()
        '''
        self.compman_dependencydict[depkey] = compManInstance

    def setDescription(self,compman_description):
        '''
        Note: This changes the compman_hashtag returned by getHashTag()
        '''
        self.compman_description = compman_description
        self.compman_configdict['compman_description'] = compman_description

    def setCodeTag(self,compman_codetag):
        '''
        Note: This changes the compman_hashtag returned by getHashTag()
        '''
        self.compman_codetag = compman_codetag
        self.compman_configdict['compman_codetag'] = compman_codetag

    def setMetaParameter(self,compman_metaparameter):
        '''
        Note: This changes the compman_hashtag returned by getHashTag()
        '''
        self.compman_metaparameter = compman_metaparameter
        self.compman_configdict['compman_metaparameter'] = compman_metaparameter

    def setTagSeparator(self,compman_tagseparator):
        '''
        Note: This changes the compman_hashtag returned by getHashTag()
        '''
        self.validateTagSeparator(compman_tagseparator)
        self.compman_tagseparator = compman_tagseparator
        self.compman_configdict['compman_tagseparator'] = compman_tagseparator

    def setBasePath(self,compman_basepath):
        self.compman_basepath = compman_basepath

    # --------------------
    # Functions for generating stuff:
    def generateBasicConfigDictFromMembers(self):
        '''
        Calls self.generateBasicConfigDict(...) using members as input:
        Following must be defined:
        self.compman_description
        self.compman_codetag
        self.compman_metaparameter
        self.compman_tagseparator
        '''
        if self.compman_description is None or self.compman_codetag is None or self.compman_metaparameter is None or self.compman_tagseparator is None:
            raise InvalidStateError()
        return self.generateBasicConfigDict(self.compman_description,self.compman_codetag,self.compman_metaparameter,self.compman_tagseparator)

    def generateBasicConfigDict(self,compman_description,compman_codetag,compman_metaparameter,compman_tagseparator):
        '''
        Returns an OrderedDict (from the collections module).

        Child classes must define a generateConfigdict that first calls
        and then extends this function.
        
        First four keys in configDict are always: compman_description,
        compman_codetag, compman_metaparameter, compman_tagseparator

        Basic configDict has these first four keys:
        compman_description
        compman_codetag 
        compman_metaparameter
        compman_tagseparator
        '''
        configDict = OrderedDict()
        configDict['compman_description']   = compman_description
        configDict['compman_codetag']       = compman_codetag 
        configDict['compman_metaparameter'] = compman_metaparameter
        configDict['compman_tagseparator']  = compman_tagseparator
        return configDict

    def generateCSVConfigString(self,compman_configdict,compman_dependencydict=None):
        '''
        Creates CSV string from key-value pairs in compman_configdict
        as well as the following five key-values pairs from each
        element in compman_dependencies:
            compman_description
            compman_codetag
            compman_metaparameter
            compman_tagseparator
            compman_hashtag - returned by getHashTag()

        Used for saving confiuration in a .csv file and generating
        compman_hashtag using hashOnString() - see getHashTag()
        '''
        string = ''
        for (key,val) in self.compman_configdict.viewitems():
            string += (str(key) + ',' + str(val) + '\n')
        if compman_dependencydict is not None:
            for (depkey,man) in self.compman_dependencydict.viewitems():
                for key in ('compman_description','compman_codetag','compman_metaparameter','compman_tagseparator'):
                    compoundKey = '{0}_{1}'.format(depkey,key)
                    string += (str(compoundKey) + ',' + str(man.get(key)) + '\n')
                compoundKey = '{0}_compman_hashtag'.format(depkey)
                string += (str(compoundKey) + ',' + str(man.getHashTag()) + '\n')
        return string

    def hashOnString(self,string,alg='djb2'):
        '''
        Creates a hash number from string.
        Algorithm alg choices:
            'djb2' (default)
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

    def getTagPrefix(self):
        '''
        Return tag prefix used in output directory and file names.
        Prefix has the form:
        compman_description tsep compman_codetag tsep ...
            compman_metaparameter tsep compman_hashtag
        where tsep is the compman_tagseparator (default '.')
        eg: 'analysis.AnalysisCode.test_20150601.123456789'

        Used in cache directory and file names.
        '''
        return self.compman_tagseparator.join([self.compman_description,self.compman_codetag,self.compman_metaparameter,self.compman_hashtag])

    def getManifestPath(self):
        if self.compman_basepath is None:
            raise TypeError('self.compman_basepath must be a string, not None')
        dirname = self.getTagPrefix()
        return os.path.join(self.compman_basepath,self.compman_description,dirname)

    def getManifestFilesList(self):
        '''
        Must be implemented by child class.
        Return a list of filename or filepaths.
        '''
        raise NotImplementedError()

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
            string += '_' + man.getMetaParameter()
        return local_metaparameter + '_' + self.hashOnString(string,alg='short')

# --------------------
def getCurrentCodeFile(keepExtension=False):
    '''
    Supposed to return filename (minus extension) of code. Not fully implmented yet.
    '''
    raise Exception("Not fully implemented - always return 'compman'")
    if keepExtension:
        return os.path.split(inspect.getfile(inspect.currentframe()))[1] # code filename (usually with path)
    else:
        return os.path.splitext(os.path.split(inspect.getfile(inspect.currentframe()))[1])[0] # code filename (usually with path)

if __name__ == '__main__':
    print(getCurrentCodeFile())
