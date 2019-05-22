from .Path import Path
from slytherin.hash import hash_object
from datetime import datetime
from pickle import PicklingError
import atexit

# HardFolder is a directory that acts like a dictionary, objects are saved to a directory and retrieved from it
class HardFolder:
	def __init__(self, path):
		self._path = Path(string=path)
		self._path.make_directory(ignore_if_exists=True)
		self._items = {}
		if self.keys_path.exists():
			self._items = self.keys_path.load(method='pickle')
		atexit.register(self.save_keys)

	@property
	def keys_path(self):
		return self._path + 'keys.pickle'

	def save_keys(self):
		self.keys_path.save(obj=self._items, method='pickle')

	def _get_path(self, key, method='pickle'):
		return self._path + f'{hash_object(key, base=32)}.{method}'

	def _get_metadata_path(self, key):
		return self._path + f'{hash_object(key, base=32)}_metadata.pickle'

	def __contains__(self, item):
		pickle_exists = self._get_path(key=item, method='pickle').exists()
		dill_exists = self._get_path(key=item, method='dill').exists()
		return pickle_exists or dill_exists

	def __setitem__(self, key, value):
		self._items[hash_object(key, base=32)] = key
		if callable(value):
			methods = ['dill', 'pickle']
		else:
			methods = ['pickle', 'dill']

		method = methods[0]
		first_path = self._get_path(key=key, method=method)
		try:
			first_path.save(obj=(key, value), method=method)
		except Exception as first_error:
			if first_path.exists():
				first_path.delete()
			method = methods[1]
			second_path = self._get_path(key=key, method=method)
			try:
				second_path.save(obj=(key, value), method=method)
			except Exception as second_error:
				if second_path.exists():
					second_path.delete()
					print(first_error)
					print(second_error)
					raise second_error

		self._get_metadata_path(key=key).save(obj={'time': datetime.now(), 'method': method})

	def _get_path_and_method(self, item):
		the_path = self._get_path(key=item, method='pickle')
		if the_path.exists():
			return the_path, 'pickle'
		else:
			the_path = self._get_path(key=item, method='dill')
			if the_path.exists():
				return the_path, 'dill'
			else:
				raise KeyError(f'The item: "{item}" does not exist in the Folder!')

	def __getitem__(self, item):
		the_path, method = self._get_path_and_method(item=item)
		key, value = the_path.load(method=method)
		if key != item:
			raise ValueError(f'item:"{item}" and key:"{key}" are different!')
		return value

	def __delitem__(self, key):
		the_path, _ = self._get_path_and_method(item=key)
		the_path.delete()
		del self._items[key]
		self._get_metadata_path(key=key).delete()

	def keys(self):
		return self._items.values()

	def get_metadata(self, item):
		return self._get_metadata_path(key=item).load(method='pickle')

	def get_size(self, item):
		the_path, _ = self._get_path_and_method(item=item)
		return the_path.get_size()