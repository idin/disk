# *Disk*

Disk is a Python library for interacting with the file system in an object oriented manner. 
I know you can use os and os.path to do all of these but I find their usage hard to remember 
and true to object oriented principles. 

# Installation

You can use pip to install Disk:

```bash
pip install disk
```

# Usage

All files and directories (folders) are considered *Path* objects. 
Any path except the root, has a parent: the directory it is in. 
Directories have children, some of them are files and some are subdirectories.


## Path

The *Path* object points to an existing or non-existing file or directory.
```python
from disk import Path
path = Path('C:\\')
```


### *get_current_directory*

Usually we want to start in the current working directory:
```python
path = Path.get_current_directory()
```


### *list*, *dir*, *ls* 

All of the above methods do the same thing; 
*ls* is for linux people, *dir* is for windows people, and *list* is for literal people.

```python
print(path.list())
```


### *directories*

To get the sub-directories of a directory use the *directories* attribute which returns a list of *Paths*:
```python
subdirectories = path.directories
```


### *files*

To get the files inside a directory use the *files* attribute which returns a list of *Paths*:
```python
files = path.files
```

### *parent_directory*

The parent directory is the directory a *Path* (either file or directory) is inside of.
```python
parent_directory = path.parent_directory
```


### *make_directory*

To create a new directory **inside** a *Path* that is also a directory, use *make_directory* 
with the name of the new directory as the *name* argument:
```python
path.make_directory(name='new_directory')
```


You can also create a directory at the location of the *Path* object by letting the *name* 
argument take its default value of *None*:
```python
path.make_directory()
```


### *make_parent_directory*

Sometimes you need to create a new file at a *Path* that doesn't already exist, *i.e.* the directory
of the file location doesn't exist. This is when *make_parent_directory* becomes handy:
```python
path.make_parent_directory(ignore_if_exists=True)
```
The default value of *ignore_if_exists* is *True*.


### *delete*

The *delete* function moves a file or directory to the trash. If the *name* argument is provided
the file or directory inside the *Path* with that name will be deleted:
```python
path.delete(name='new_directory')
```


If the *name* argument is not provided the file or directory the *Path* points to will be deleted:
```python
path.delete()
```


### *save*

To save a Python object as a **Pickle** file using the *pickle* or *dill* library you can just use the
*save* function of the *Path* which saves the object right at the location of *Path*.
```python
my_list = [1, 2, 3]
Path('my_list.pickle').save(my_list, method='pickle')
Path('my_list.dill').save(my_list, method='dill')
```


### *load*

To load an object from a **Pickle** file located at a *Path* you can run the *load* function of the *Path*.
```python
list_from_pickle = Path('my_list.pickle').load(method='pickle')
list_from_dill = Path('my_list.dill').load(method='dill')
```
