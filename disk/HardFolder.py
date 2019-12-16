from .Path import Path
from slytherin.hash import hash_object
from datetime import datetime
import atexit
from zipfile import ZIP_DEFLATED


# HardFolder is a directory that acts like a dictionary, objects are saved to a directory and retrieved from it
class HardFolder:
	def __init__(self, path):
		if isinstance(path, self.__class__):
			self._path = path._path
			self._items = path._items
		else:
			self._path = Path(string=path)
			self._path.make_directory(ignore_if_exists=True)
			self._items = {}

		if self.keys_path.exists() and len(self._items) == 0:
			self._items = self.keys_path.load(method='pickle')
		atexit.register(self.save_keys)

	_STATE_ATTRIBUTES_ = ['_path', '_items']

	def __repr__(self):
		return f'<HardFolder:{self._path.path}>'

	def __str__(self):
		return repr(self)

	def __getstate__(self):
		return {key: getattr(self, key) for key in self._STATE_ATTRIBUTES_}

	def __setstate__(self, state):
		for key, value in state.items():
			setattr(self, key, value)
		self._path.make_directory(ignore_if_exists=True)
		if self.keys_path.exists():
			self._items = self.keys_path.load(method='pickle')
		atexit.register(self.save_keys)

	def __hashkey__(self):
		return (self.__class__.__name__, self._path.path)

	def zip(self, delete_directory=False, compression=ZIP_DEFLATED, zip_path=None, echo=0):
		"""
		:type delete_directory: bool
		:type compression: int
		:rtype: Path
		"""
		self.save_keys()
		return self._path.zip(compression=compression, delete_original=delete_directory, zip_path=zip_path, echo=echo)

	@classmethod
	def from_zip(cls, path, delete_original=False, unzip_path=None):
		"""
		:type path: str or Path
		:type delete_original: bool
		:rtype: HardFolder
		"""
		zip_path = Path(string=path)
		unzip_path = zip_path.unzip(delete_original=delete_original, unzip_path=unzip_path)
		return cls(path=unzip_path)

	@property
	def keys_path(self):
		return self._path + 'keys.pickle'

	def save_keys(self):
		self.keys_path.save(obj=self._items, method='pickle')

	def _get_path(self, key, method='pickle'):
		return self._path + f'{hash_object(key, base=32)}.{method}'

	def _get_metadata_path(self, key):
		return self._path + f'{hash_object(key, base=32)}_metadata.pickle'

	def _get_path_and_method(self, item):
		the_path = self._get_path(key=item, method='pickle')
		if the_path.exists():
			return the_path, 'pickle'
		else:
			the_path = self._get_path(key=item, method='dill')
			if the_path.exists():
				return the_path, 'dill'
			else:
				raise KeyError(f'The item: "{item}" does not exist in {self}!')

	def set_item(self, key, value, time):
		self._items[hash_object(key, base=32)] = key
		if callable(value):
			methods = ['dill', 'pickle']
		else:
			methods = ['pickle', 'dill']

		method = methods[0]
		first_path = self._get_path(key=key, method=method)
		file_name = None
		try:
			first_path.save(obj=(key, value), method=method)
			file_name = first_path.name_and_extension
		except Exception as first_error:
			if first_path.exists():
				first_path.delete()
			method = methods[1]
			second_path = self._get_path(key=key, method=method)
			try:
				second_path.save(obj=(key, value), method=method)
				file_name = second_path.name_and_extension
			except Exception as second_error:
				if second_path.exists():
					second_path.delete()
					print(first_error)
					print(second_error)
					raise second_error

		self._get_metadata_path(key=key).save(obj={'time': time, 'method': method, 'key': key, 'file_name': file_name})

	def __contains__(self, item):
		pickle_exists = self._get_path(key=item, method='pickle').exists()
		dill_exists = self._get_path(key=item, method='dill').exists()
		return pickle_exists or dill_exists

	def __setitem__(self, key, value):
		self.set_item(key=key, value=value, time=datetime.now())

	def __getitem__(self, item):
		the_path, method = self._get_path_and_method(item=item)
		key, value = the_path.load(method=method)
		if key != item:
			raise ValueError(f'item:"{item}" and key:"{key}" are different!')
		return value

	def __delitem__(self, key):
		the_path, _ = self._get_path_and_method(item=key)
		the_path.delete()
		del self._items[hash_object(key, base=32)]
		self._get_metadata_path(key=key).delete()

	def get_time(self, item):
		return self.get_metadata(item=item)['time']

	def keys(self):
		return self._items.values()

	def get_metadata(self, item):
		return self._get_metadata_path(key=item).load(method='pickle')

	@property
	def metadata_filenames(self):
		for filename in self._path.list():
			if filename.name_and_extension.endswith('_metadata.pickle'):
				yield filename

	@property
	def metadata(self):
		for filename in self.metadata_filenames:
			yield filename.load(method='pickle')

	def get_size(self, item):
		the_path, _ = self._get_path_and_method(item=item)
		return the_path.get_size()


class SoftFolder:
	def __init__(self):
		self._objects = {}
		self._metadata = {}

	@staticmethod
	def get_hash(key):
		return hash_object(key, base=32)

	def __contains__(self, item):
		return self.get_hash(item) in self._objects

	def __setitem__(self, key, value):
		hash_key = self.get_hash(key=key)
		self._objects[hash_key] = value
		self._metadata[hash_key] = {'time': datetime.now(), 'key': key}

	def __getitem__(self, item):
		hash_key = self.get_hash(key=item)
		return self._objects[hash_key]

	def __delitem__(self, key):
		hash_key = self.get_hash(key=key)
		del self._objects[hash_key]
		del self._metadata[hash_key]

	def keys(self):
		return [metadata['key'] for metadata in self._metadata.values()]


