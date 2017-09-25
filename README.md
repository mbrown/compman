# compman

A Python library for handling / keeping track of pipeline-style computations
with different parameters values, input data, etc. at different steps in the
pipeline.

Original author: Matthew R G Brown

## Usage and Documentation

See CompMan.__doc__ in compman.py file.

Example:
```Python

from compman import *

tm = TestMan('testparam','a/b/c')
print(tm)
print('\n\nhashtag WITHOUT extra: {0}'.format(tm.getHashTag(True)))
print('\n\nhashtag WITH extra   : {0}'.format(tm.getHashTag(False)))
```

## License

Copyright © 2015 Matthew R G Brown

Distributed under the Eclipse Public License either version 1.0 or (at
your option) any later version.
