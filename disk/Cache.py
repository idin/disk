import atexit
import functools
from .HardFolder import HardFolder
from .hash import hash


class Dictionary:
	def __init__(self):
		self._dictionary = dict()

	def __getitem__(self, item):
		hashed_key = hash(item, base=64)
		return self._dictionary[hashed_key][1]

	def __setitem__(self, key, value):
		hashed_key = hash(key, base=64)
		self._dictionary[hashed_key] = (key, value)

	def __contains__(self, item):
		hashed_key = hash(item, base=64)
		return hashed_key in self._dictionary

	def __str__(self):
		return str({
			str(key_value[0]): key_value[1]
			for hashed_key, key_value in self._dictionary.items()
		})

	def __repr__(self):
		return str(self)

	def __delitem__(self, key):
		hashed_key = hash(key, base=64)
		del self._dictionary[hashed_key]

	def keys(self):
		return [key_value[0] for hashed_key, key_value in self._dictionary.items()]

	def pop(self, item):
		hashed_key = hash(item, base=64)
		return self._dictionary.pop(hashed_key)[1]

class Cache:
	def __init__(self, on_disk=True, path=None):
		self._on_disk = on_disk
		self._buffer = Dictionary()
		if on_disk:
			if path is None:
				raise ValueError('On-disk cache needs a path!')
			else:
				self._hard_folder = HardFolder(path=path)
			atexit.register(self.empty_buffer)

	def __del__(self):
		self.empty_buffer()

	def __getitem__(self, item):
		if self._on_disk:
			if item in self._buffer:
				return self._buffer[item]
			else:
				return self._hard_folder[item]
		else:
			return self._buffer[item]

	def __setitem__(self, key, value):
		self._buffer[key] = value

	def __contains__(self, item):
		if item in self._buffer:
			return True
		elif self._on_disk:
			return item in self._hard_folder

	def empty_buffer(self):
		if self._on_disk:
			keys = list(self._buffer.keys())
			for key in keys:
				self._hard_folder[key] = self._buffer.pop(key)
		else:
			raise RuntimeError('Cannot empty the buffer! There is no hard_folder!')

	def make_cached(self, function):
		return make_cached(function=function, cache=self)


def make_cached(function, cache):
	"""
	:param callable function: function to be cached
	:param Cache cache:
	:rtype: callable
	"""
	@functools.wraps(function)
	def wrapper(*args, **kwargs):
		key = (function.__name__, function.__doc__, args, kwargs)
		if key in cache:
			return cache[key]
		else:
			result = function(*args, **kwargs)
			cache[key] = result
			return result
	return wrapper
