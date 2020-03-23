from .pickle_function import pickle as _pickle
from .pickle_function import unpickle as _unpickle
from .individual_functions import *
from .zip import zip_file
from .zip import zip_directory
from .zip import unzip
from .get_creation_date import get_creation_date
from .get_creation_date import get_modification_date

import re
from zipfile import ZIP_DEFLATED
from zipfile import is_zipfile
from pathlib import Path as _Path
import warnings
import os


def get_parent_directory(path):
	return str(_Path(path).parent.absolute())


class Path:
	def __init__(self, string, show_size=False):
		"""
		:type string: str or Path
		:type show_size: bool
		"""
		if isinstance(string, self.__class__) or not isinstance(string, str):
			string = string.path
		self._string = string
		self._size = None
		self._show_size = show_size

	def __str__(self):
		return self.__repr__()

	def __repr__(self):
		string = self.name_and_extension
		if self._show_size:
			size, unit = self.get_size()
			return f'{self.type}: {string} - {round(size, 3)} {unit}'
		else:
			return f'{self.type}: {string}'

	def __getstate__(self):
		return {
			'string': self._string,
			'size': self._size,
			'show_size': self._show_size
		}

	def __setstate__(self, state):
		self._string = state['string']
		self._size = state['size']
		self._show_size = state['show_size']

	def __hashkey__(self):
		if self.exists():
			if self.is_file():
				return self.__class__.__name__, 1, self.size_bytes, self.creation_date, self.modification_date
			else:
				return self.__class__.__name__, 2, [x.__hashkey__() for x in self.list(show_size=False)]

		else:
			return self.__class__.__name__, 0, self._string

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
		return cls(string='.', show_size=show_size)

	@property
	def parent_directory(self):
		"""
		:rtype: Path
		"""
		return self.__class__(string=get_parent_directory(self.absolute_path))

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
	def string(self):
		"""
		:rtype: str
		"""
		return self._string

	@property
	def path(self):
		"""
		:rtype: str
		"""
		return self.string

	@property
	def pretty_path(self):
		"""
		:rtype: str
		"""
		backslashes_replaced = self.string.replace('\\', '/')
		multiple_slashes_removed = re.sub('/+', '/', backslashes_replaced)
		return multiple_slashes_removed

	@property
	def value(self):
		"""
		:rtype: str
		"""
		return self.string

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

	def __add__(self, other):
		"""
		:type other: Path or str
		:rtype: Path
		"""
		if isinstance(other, str):
			other_string = other
		elif isinstance(other, self.__class__):
			other_string = other.string
		else:
			raise TypeError(f'{other} is a {type(other)} but it should either be string or {self.__class__}')
		self_string = '' if self.string == '.' else self.string

		return self.__class__(
			string=os.path.join(self_string, other_string),
			show_size=self._show_size
		)

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

	def list(self, show_size=None):
		"""
		:rtype: list[Path]
		"""
		if show_size is not None:
			self._show_size = show_size
		result = [self+x for x in list_directory(path=self.path)]
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

	def make_directory(self, name=None, ignore_if_exists=True):
		if name:
			path = self+name
		else:
			path = self

		make_dir(path=path.path, ignore_if_exists=ignore_if_exists)

		return path

	def make_parent_directory(self, ignore_if_exists=True):
		if self.parent_directory:
			self.parent_directory.make_directory(ignore_if_exists=ignore_if_exists)
		return self.parent_directory

	def delete(self, name=None):
		if name:
			to_delete = self + name
		else:
			to_delete = self
		delete(path=to_delete.path)

	def delete_directory(self, name):
		delete_dir(path=(self+name).path)

	def save(self, obj, method='pickle', mode='wb', echo=0):
		if not self.parent_directory.exists():
			self.parent_directory.make_dir()
		_pickle(path=self.path, obj=obj, method=method, mode=mode, echo=echo)

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
			path = (self + name).path
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
			path = (self + name).path
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
			zip_path = zip_path or self.path + '.zip'
			result = zip_file(path=self.path, compression=compression, zip_path=zip_path, echo=echo)
		else:
			zip_path = zip_path or self.path + '.dir.zip'
			result = zip_directory(path=self.path, compression=compression, zip_path=zip_path, echo=echo)

		if delete_original:
			self.delete()

		return self.__class__(string=result)

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
			unzip_path = directory + self.path[:-len(zipped_directory_extension)]
		elif self.name_and_extension.endswith(zipped_file_extension):
			unzip_path = directory + self.path[:-len(zipped_file_extension)]
		else:
			raise ValueError('unknown extension!')

		unzip(path=self.path, unzip_path=directory.path)

		if delete_original:
			self.delete()

		return self.__class__(string=unzip_path)

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

	# aliases
	ls = list
	dir = list
	md = make_directory
	make_dir = make_directory
	del_dir = delete_directory
	delete_dir = delete_directory
	pickle = save
	unpickle = load
