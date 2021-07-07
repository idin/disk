from .pickle_function import pickle as _pickle
from .pickle_function import unpickle as _unpickle
from .individual_functions import *
from .zip import zip_file
from .zip import zip_directory
from .zip import unzip
from .get_creation_date import get_creation_date
from .get_creation_date import get_modification_date
from .exceptions import DiskError
from .exceptions import RenameError
from .exceptions import PathDoesNotExistError
from .exceptions import PathExistsError
from .exceptions import NotAFileError
from .exceptions import DirectoryNotFoundError


import re
from zipfile import ZIP_DEFLATED
from zipfile import is_zipfile
from pathlib import Path as _Path
import warnings
import os
import shutil
from filecmp import cmp as compare_files


def get_parent_directory(path):
	return str(_Path(path).parent.absolute())


class Path:
	def __init__(self, path, show_size=False):
		"""
		:type path: str or Path
		:type show_size: bool
		"""
		path = path or '.'

		if isinstance(path, self.__class__) or not isinstance(path, str):
			path = path.path
		self._path = path
		self._size = None
		self._show_size = show_size

	def rename(self, new_name):
		"""
		:type new_name: str or Path
		:rtype: Path
		"""
		return self.move_and_rename(new_name=new_name, new_directory=self.parent_directory)

	def move(self, new_directory):
		"""
		:type new_directory: str or Path
		:rtype: Path
		"""
		return self.move_and_rename(new_name=self.name_and_extension, new_directory=new_directory)

	def rename_and_move(self, **kwargs):
		return self.move_and_rename(**kwargs)

	def move_and_rename(self, new_name=None, new_directory=None, new_path=None):
		"""
		:type new_name: str or Path
		:type new_directory: str or Path
		:type new_path: str or Path
		:rtype: Path
		"""
		if not self.exists():
			raise PathDoesNotExistError(f'"{self.absolute}" does not exist to be renamed!')

		if new_name is None and new_directory is None and new_path is None:
			raise RenameError('at least one of new_name, new_directory, new_path should be provided!')

		if new_path is not None and (new_name is not None or new_directory is not None):
			raise RenameError('providing both new_path and either of new_directory or new_name is ambiguous!')

		if new_path is not None:
			new_path = Path(new_path)
			new_directory = new_path.parent_directory

		else:
			if new_name is None:
				new_name = self.name_and_extension
			elif isinstance(new_name, Path):
				new_name = new_name.name_and_extension

			if new_directory is None:
				new_directory = self.parent_directory

			new_directory = Path(new_directory)
			new_path = new_directory / new_name

		if not new_directory.exists():
			new_directory.make_dir()

		old_path = str(self.absolute)

		if new_path.exists():
			raise PathExistsError(f'"{old_path}" cannot be renamed to "{new_path.absolute}" because it already exists!')

		shutil.move(self.absolute_path, new_path.absolute_path)
		self._path = new_path.absolute_path
		if not self.exists():
			raise RenameError(f'could not rename "{old_path}" to "{self.absolute}"')
		return self

	def copy(self, new_path=None, new_directory=None, clean_copy=True, echo=0):
		"""
		:type new_path str or Path
		:type echo: int or bool
		:param bool clean_copy: if True, first delete destination
		:rtype: Path
		"""
		if not self.exists():
			raise FileNotFoundError(self)

		if new_path is None and new_directory is not None:
			new_directory = Path(new_directory)
			if not new_directory.exists():
				raise DirectoryNotFoundError(new_directory)
			new_path = new_directory / self.name_and_extension

		elif new_path is not None and new_directory is None:
			new_path = Path(new_path)

		elif new_path is None and new_directory is None:
			raise TypeError('new_path and new_directory are both None!')

		elif new_path is not None and new_directory is not None:
			raise TypeError('Please make up your mind and provide only one of new_path or new_directory')

		if self.is_file():
			if new_path.exists() and new_path.is_directory():
				raise IsADirectoryError(new_path)
			if echo:
				print(f'Copying "{self.absolute_path}" to "{new_path.absolute_path}"')
			if clean_copy and new_path.exists():
				new_path.delete(echo=echo)
			shutil.copy2(self.path, new_path.path)

		elif self.is_directory():
			if new_path.exists() and new_path.is_file():
				raise NotADirectoryError(new_path)
			if echo:
				print(f'Copying "{self.absolute_path}" to "{new_path.absolute_path}"')
			if not new_path.exists():
				new_path.make_dir()
			elif clean_copy:
				new_path.delete()
				new_path.make_dir()

			for path in self.list():
				path.copy(new_directory=new_path, clean_copy=clean_copy)

		return new_path

	def __str__(self):
		return self.__repr__()

	def __repr__(self):
		name_and_ext = self.name_and_extension
		if self._show_size:
			size, unit = self.get_size()
			return f'{self.type}: {name_and_ext} - {round(size, 3)} {unit}'
		else:
			return f'{self.type}: {name_and_ext}'

	def __getstate__(self):
		return {
			'string': self._path,
			'size': self._size,
			'show_size': self._show_size
		}

	def __setstate__(self, state):
		self._path = state['string']
		self._size = state['size']
		self._show_size = state['show_size']

	def __hashkey__(self):
		if self.exists():
			if self.is_file():
				return self.__class__.__name__, 1, self.size_bytes, self.creation_date, self.modification_date
			else:
				return self.__class__.__name__, 2, [x.__hashkey__() for x in self.list(show_size=False)]

		else:
			return self.__class__.__name__, 0, self._path

	def get_absolute(self):
		"""
		:rtype: str
		"""
		return get_absolute_path(path=self.path)

	@property
	def absolute(self):
		"""
		:rtype: str
		"""
		return self.get_absolute()

	@property
	def absolute_path(self):
		"""
		:rtype: str
		"""
		return self.get_absolute()

	@classmethod
	def get_current_directory(cls, show_size=False):
		"""
		:rtype: Path
		"""
		return cls(path='.', show_size=show_size)

	def get_parent_directory(self, absolute=False):
		"""
		:type absolute: bool
		:rtype: Path
		"""
		if absolute:
			return Path(path=get_parent_directory(self.absolute_path))
		else:
			string_except_name_and_extension = self._path[:-len(self.name_and_extension)]
			if len(string_except_name_and_extension) > 0:
				return Path(path=string_except_name_and_extension)
			else:
				return self.get_current_directory(show_size=self._show_size)

	@property
	def parent_directory(self):
		"""
		:rtype: Path
		"""
		return self.get_parent_directory(absolute=False)

	def __parents__(self):
		"""
		:rtype: list[Path]
		"""
		if self.parent_directory is not None:
			return [self.parent_directory]
		else:
			return []

	def __children__(self):
		"""
		:rtype: list[Path]
		"""
		if self.is_directory():
			return self.list()
		else:
			return []

	def __hash__(self):
		return self.absolute_path

	@property
	def path(self):
		"""
		:rtype: str
		"""
		return self._path

	@property
	def pretty_path(self):
		"""
		:rtype: str
		"""
		backslashes_replaced = self.path.replace('\\', '/')
		multiple_slashes_removed = re.sub('/+', '/', backslashes_replaced)
		return multiple_slashes_removed

	@property
	def value(self):
		"""
		:rtype: str
		"""
		return self.path

	@property
	def name_and_extension(self):
		"""
		:rtype: str
		"""
		return get_basename(path=self.absolute_path)

	full_name = name_and_extension

	@property
	def extension(self):
		"""
		:rtype: str
		"""
		extension_with_dot = os.path.splitext(self.path)[1]
		if len(extension_with_dot) > 0:
			return extension_with_dot[1:]
		else:
			return extension_with_dot

	@property
	def name(self):
		"""
		:rtype: str
		"""
		return self.name_and_extension.rsplit('.', 1)[0]

	@property
	def creation_date(self):
		return get_creation_date(self.path)

	@property
	def modification_date(self):
		return get_modification_date(self.path)

	def get_size_bytes(self):
		"""
		:rtype: int or float
		"""
		if self.is_file():
			return get_file_size_bytes(path=self.path)
		else:
			return sum([x.size_bytes for x in self.list()])

	@property
	def size_bytes(self):
		"""
		:rtype: int or float
		"""
		if self._size is None:
			self._size = self.get_size_bytes()
		return self._size

	def get_size_kb(self, binary=True):
		"""
		:rtype: int or float
		"""
		if binary:
			return self.size_bytes/(2**10)
		else:
			return self.size_bytes/1e3

	def get_size_mb(self, binary=True):
		"""
		:rtype: int or float
		"""
		if binary:
			return self.size_bytes/(2**20)
		else:
			return self.size_bytes/1e6

	def get_size_gb(self, binary=True):
		"""
		:rtype: int or float
		"""
		if binary:
			return self.size_bytes/(2**30)
		else:
			return self.size_bytes/1e6

	def get_size(self, binary=True):
		"""
		:rtype: tuple
		"""
		main_unit = 'B' if binary else 'b'
		if self.size_bytes <= 1e3:
			return self.size_bytes, 'B'
		elif self.size_bytes <= 1e6:
			return self.get_size_kb(binary=binary), 'K' + main_unit
		elif self.size_bytes <= 1e9:
			return self.get_size_mb(binary=binary), 'M' + main_unit
		else:
			return self.get_size_gb(binary=binary), 'G' + main_unit

	def exists(self):
		"""
		:rtype: bool
		"""
		return path_exists(path=self.path)

	def is_file(self):
		"""
		:rtype: bool
		"""
		return path_is_file(path=self.path)

	def is_directory(self):
		return not self.is_file()

	@property
	def type(self):
		"""
		:rtype: str
		"""
		if not self.exists():
			return 'nonexistent path'
		elif self.is_file():
			return 'file'
		else:
			return 'directory'

	def __truediv__(self, other):
		"""
		:type other: Path or str
		:rtype: Path
		"""
		if isinstance(other, str):
			other_string = other
		elif isinstance(other, self.__class__):
			other_string = other.path
		else:
			raise TypeError(f'{other} is a {type(other)} but it should either be string or {self.__class__}')
		self_path = '' if self.path == '.' else self.path

		return Path(
			path=os.path.join(self_path, other_string),
			show_size=self._show_size
		)

	def __add__(self, other):
		"""
		:type other: str
		:rtype: S3Path
		"""

		if isinstance(other, str):
			if other.startswith('.'):  # other is an extension
				left = self._path.rstrip('/')
				return self.__class__(path=f'{left}{other}', show_size=self._show_size)
			else:
				return self.__truediv__(other)
		else:
			return self.__truediv__(other)

	def _sort_key(self):
		return self.type, self.get_absolute()

	def __lt__(self, other):
		"""
		:type other: Path
		:rtype: bool
		"""
		return self._sort_key() < other._sort_key()

	def __gt__(self, other):
		"""
		:type other: Path
		:rtype: bool
		"""
		return self._sort_key() > other._sort_key()

	def __le__(self, other):
		"""
		:type other: Path
		:rtype: bool
		"""
		return self._sort_key() <= other._sort_key()

	def __ge__(self, other):
		"""
		:type other: Path
		:rtype: bool
		"""
		return self._sort_key() >= other._sort_key()

	def __eq__(self, other):
		"""
		:type other: Path
		:rtype: bool
		"""
		return self._sort_key() == other._sort_key()

	def __ne__(self, other):
		"""
		:type other: Path
		:rtype: bool
		"""
		return self._sort_key() != other._sort_key()

	def __contains__(self, item):
		if isinstance(item, Path):
			path = item.path
		else:
			path = item
		return path in list_directory(path=self.path)

	def get_num_files(self):
		if self.is_directory():
			return len([x for x in list_directory(path=self.path)])
		else:
			raise NotADirectoryError(f'{self.path} is not a directory!')

	def is_empty(self):
		return self.get_num_files() == 0

	def list(self, show_size=None):
		"""
		:rtype: list[Path]
		"""
		if show_size is not None:
			self._show_size = show_size
		result = [self / x for x in list_directory(path=self.path)]
		result = [x for x in result if x.name != '']
		result.sort()
		return result

	@property
	def directories(self):
		"""
		:rtype: list[Path]
		"""
		return [x for x in self.list() if x.is_directory()]

	@property
	def files(self):
		"""
		:rtype: list[Path]
		"""
		return [x for x in self.list() if x.is_file()]

	def get(self, full_name):
		return [x for x in self.list() if x.full_name == full_name][0]

	def make_directory(self, name=None, ignore_if_exists=True, echo=0):
		if name:
			path = self / name
		else:
			path = self

		if echo:
			print(f'Making directory "{path.absolute_path}"')
		make_dir(path=path.path, ignore_if_exists=ignore_if_exists)

		return path

	def make_parent_directory(self, ignore_if_exists=True, echo=0):
		if self.parent_directory:
			self.parent_directory.make_directory(ignore_if_exists=ignore_if_exists, echo=echo)
		return self.parent_directory

	def delete(self, name=None, echo=0):
		if name:
			to_delete = self / name
		else:
			to_delete = self
		if echo:
			print(f'Deleting "{to_delete.absolute_path}"')
		delete(path=to_delete.path)

	def delete_directory(self, name):
		delete_dir(path=(self / name).path)

	def save(self, obj, method='pickle', mode='wb', echo=0):
		path = self.path
		if not path.endswith('.pickle'):
			path = f'{path}.pickle'

		if not self.parent_directory.exists():
			self.parent_directory.make_dir()
		_pickle(path=path, obj=obj, method=method, mode=mode, echo=echo)
		return path

	def load(self, method='pickle', mode='rb', echo=0):
		"""
		:param str method: pickle or dill
		:param str mode: 'rb' or ...
		:param bool or int echo:
		:rtype: object
		"""
		return _unpickle(path=self.path, method=method, mode=mode, echo=echo)

	def read_lines(self, name=None, encoding='utf8'):
		"""
		:type name: str or NoneType
		:type encoding: str
		:rtype: list[str]
		"""
		if name is None:
			path = self.path
		else:
			path = (self / name).path
		try:
			with open(path, encoding=encoding) as file:
				content = file.readlines()
		except Exception as e:
			warnings.warn(f'error reading file {path}')
			raise e
		return content

	def write_lines(self, lines, name=None, append=False, encoding='utf8'):
		"""
		:type lines: list[str]
		:type name: str or NoneType
		:type append: bool
		:type encoding: str
		"""
		if name is None:
			path = self.path
		else:
			path = (self / name).path
		try:
			with open(path, mode='a' if append else 'w', encoding=encoding) as file:
				file.writelines(lines)
		except Exception as e:
			warnings.warn(f'error writing file {path}')
			raise e

	def zip(self, zip_path=None, compression=ZIP_DEFLATED, delete_original=False, echo=0):
		"""
		:type zip_path: NoneType or Path or str
		:type compression: int
		:rtype: Path
		"""
		if isinstance(zip_path, self.__class__):
			zip_path = zip_path.path

		if self.is_file():
			zip_path = zip_path or f'{self.path}.zip'
			result = zip_file(path=self.path, compression=compression, zip_path=zip_path, echo=echo)
		else:
			zip_path = zip_path or f'{self.path}.dir.zip'
			result = zip_directory(path=self.path, compression=compression, zip_path=zip_path, echo=echo)

		if delete_original:
			self.delete()

		return Path(path=result)

	def unzip(self, unzip_path=None, delete_original=False):
		"""
		:type unzip_path: str or NoneType or Path
		:rtype: Path
		"""
		if isinstance(unzip_path, self.__class__):
			unzip_path = unzip_path.path

		if unzip_path is None:
			directory = self.parent_directory
		else:
			directory = Path(unzip_path)

		zipped_directory_extension = '.dir.zip'
		zipped_file_extension = '.zip'
		if self.name_and_extension.endswith(zipped_directory_extension):
			unzip_path = directory / self.path[:-len(zipped_directory_extension)]
		elif self.name_and_extension.endswith(zipped_file_extension):
			unzip_path = directory / self.path[:-len(zipped_file_extension)]
		else:
			raise ValueError('unknown extension!')

		unzip(path=self.path, unzip_path=directory.path)

		if delete_original:
			self.delete()

		return Path(path=unzip_path)

	def is_zipfile(self):
		"""
		:rtype: bool
		"""
		return is_zipfile(self.path)

	def run(self, command):
		if not self.is_directory():
			raise TypeError(f'{self.absolute} is not a directory')
		else:
			working_directory = os.getcwd()
			os.chdir(self.absolute)
			result = os.system(command)
			os.chdir(working_directory)
			return result

	def is_inside(self, path):
		"""
		checks if self is inside another path
		:type path: Path
		:rtype: bool
		"""
		if not path.is_directory():
			raise NotADirectoryError(path)
		return self.absolute_path.startswith(path.absolute_path)

	def contains(self, path):
		"""
		checks if self contains another path
		:type path: Path
		:rtype: bool
		"""
		return path.is_inside(path=self)

	def is_the_same_file(self, other):
		"""
		checks if self is the same file as path
		:type other: Path
		:rtype: bool
		"""
		if not self.exists():
			FileNotFoundError(self)

		if not other.exists():
			FileNotFoundError(other)

		if not self.is_file():
			raise NotAFileError(self)

		if not other.is_file():
			raise NotAFileError(other)

		return compare_files(self.absolute_path, other.absolute_path)

	def is_the_same_directory(self, other):
		"""
		checks if self is the same directory as path
		:type other: Path
		:rtype: bool
		"""
		if not self.exists():
			DirectoryNotFoundError(self)

		if not other.exists():
			DirectoryNotFoundError(other)

		if not self.is_directory():
			raise NotADirectoryError(self)

		if not other.is_directory():
			raise NotADirectoryError(other)

		self_file_names = {f.name_and_extension: f for f in self.files}
		other_file_names = {f.name_and_extension: f for f in other.files}

		for name, file in self_file_names.items():
			if name not in other_file_names:
				return False
			if not file.is_the_same_file(other_file_names[name]):
				return False

		for name in other_file_names.keys():
			if name not in self_file_names:
				return False

		self_dir_names = {d.name_and_extension: d for d in self.directories}
		other_dir_names = {d.name_and_extension: d for d in other.directories}

		for name, directory in self_dir_names.items():
			if name not in other_dir_names:
				return False

		for name in other_dir_names.keys():
			if name not in self_dir_names:
				return False

		for name, directory in self_dir_names.items():
			other_directory = other_dir_names[name]

			if not directory.is_the_same_directory(other_directory):
				return False

		return True

	def mimic(self, other, ignore_function=None, echo=1):
		"""
		syncs self with other path which must be a directory by mimicking it
		:type other: Path
		:type ignore_function: callable or NoneType
		:rtype: Path
		"""
		if echo:
			print(f'"{self.absolute_path}" mimicking "{other.absolute_path}" ')
		if not self.exists():
			self.make_directory()
		if not other.exists():
			raise PathDoesNotExistError(other)
		if other.is_file():
			raise NotADirectoryError(other)
		if self.is_inside(path=other):
			raise DiskError(f'"{self.path}" is inside "{other.path}"!')
		if self.contains(path=other):
			raise DiskError(f'"{self.path}" contains "{other.path}"!')

		self_files = {file.name_and_extension: file for file in self.files}
		other_files = {file.name_and_extension: file for file in other.files}

		if ignore_function is None:
			def ignore_function(x):
				return False

		for name, file in self_files.items():
			if ignore_function(file):
				continue

			elif name not in other_files:
				file.delete(echo=echo)

		for name, other_file in other_files.items():
			if ignore_function(other_file):
				continue

			elif name not in self_files:
				self_file = self / name
				if ignore_function(self_file):
					continue
				else:
					other_file.copy(new_path=self_file.absolute_path, echo=echo)

			else:
				self_file = self_files[name]
				if ignore_function(self_file):
					continue

				elif not other_file.is_the_same_file(self_file):
					self_file.delete(echo=echo)
					other_file.copy(new_path=self_file.absolute_path, echo=echo)

		self_directories = {d.name_and_extension: d for d in self.directories}
		other_directories = {d.name_and_extension: d for d in other.directories}

		for name, directory in self_directories.items():
			if ignore_function(directory):
				continue
			elif name not in other_directories:
				directory.delete(echo=echo)

		for name, other_directory in other_directories.items():
			if ignore_function(other_directory):
				continue

			elif name not in self_directories:
				self_directory = self / name
				if ignore_function is not None and ignore_function(self_directory):
					continue

				else:
					other_directory.copy(new_path=self_directory.absolute_path, echo=echo)
			else:
				self_directory = self_directories[name]
				if ignore_function(self_directory):
					continue
				else:
					self_directory.mimic(other_directory, ignore_function=ignore_function, echo=echo)

	# aliases

	ls = list
	dir = list
	md = make_directory
	make_dir = make_directory
	del_dir = delete_directory
	delete_dir = delete_directory
	pickle = save
	unpickle = load
	replicate = mimic
	is_same_file = is_the_same_file
	is_same_directory = is_the_same_directory
	is_the_same_dir = is_the_same_directory
	is_same_dir = is_same_directory
