# desync

*desync* desynchronises functions, making statements in the function body asynchronous.

## Desynchronisation

The following block opf code will take roughly 4 seconds to complete.

```python
import time


def inner():
    time.sleep(2)

def outer():
    inner()
    inner()

if __name__ == '__main__':
    start = time.time()
    outer()
    print(time.time() - start)
```

Add the `desync` decorator to the `outer` function and the block will take about 2 seconds to complete. 

```python
import time

from desync import desync


def inner():
    time.sleep(2)

@desync
def outer():
    inner()
    inner()

if __name__ == '__main__':
    start = time.time()
    outer()
    print(time.time() - start)
```

## Versioning

Desynchronised functions have versions.

```python
from desync import desync

def inner(value):
    return value + 1

@desync
def outer(value):
    return inner(value)

version = outer.get_version()
assert str(version) == '1.0'
with open('version.txt', 'w') as filobj:
    filobj.write(f'{{version.major_hash}\n",".join(version.minor_hash)}\n{version.major_version}\n{version.minor_version}\n')
```

If the function changes, or called functions change, then the version gets updated when the old version is provided.
If the version of the `outer` function in the following block is saved, then it can be used as a base version to track changes.
Below a called function changes, changing the minor version.

```python
from desync import desync
from desync.version import Version

def inner(value):
    return value + 2

@desync
def outer(value):
    return inner(value)

with open('version.txt') as filobj:
    major_hash, minor_hash, major_version, minor_version = filobj
    minor_hash = minor_hash.split(',')
    outer.set_version(Version(
        int(major_hash),
        tuple(int(hash_) for hash_ in minor_hash),
        major_version=int(major_version),
        minor_version=int(minor_version),
    ))
    assert str(outer.get_version()) == '1.1'
```

Below the desynchronised function changes, changing the major version.

```python
from desync import desync
from desync.version import Version

def inner(value):
    return value + 2

@desync
def outer(value):
    return str(inner(value))

with open('version.txt') as filobj:
    major_hash, minor_hash, major_version, minor_version = filobj
    minor_hash = minor_hash.split(',')
    outer.set_version(Version(
        int(major_hash),
        tuple(int(hash_) for hash_ in minor_hash),
        major_version=int(major_version),
        minor_version=int(minor_version),
    ))
    assert str(outer.get_version()) == '2.0'
```

## Caching

Desynchronised function will not run a called function if the function's hash does not change and the inputs do not change.
The `outer` function below runs faster when called the second time.

```python
import time

from desync import desync


def inner(value):
    time.sleep(2)
    return value + 1

@desync
def outer(value):
    return inner(inner(value))

start = time.time()
outer(0)
print(time.time() - start)

outer.set_cache(outer.get_cache())

start = time.time()
outer(0)
print(time.time() - start)
```
