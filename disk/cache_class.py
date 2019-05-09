import atexit
import functools
from .hard_folder_class import HardFolder
from slytherin.hash import hash_object
import warnings


class Dictionary:
	def __init__(self):
		self._dictionary = dict()

	def __getitem__(self, item):
		hashed_key = hash_object(item, base=64)
		return self._dictionary[hashed_key][1]

	def __setitem__(self, key, value):
		hashed_key = hash_object(key, base=64)
		self._dictionary[hashed_key] = (key, value)

	def __contains__(self, item):
		hashed_key = hash_object(item, base=64)
		return hashed_key in self._dictionary

	def __str__(self):
		return str({
			str(key_value[0]): key_value[1]
			for hashed_key, key_value in self._dictionary.items()
		})

	def __repr__(self):
		return str(self)

	def __delitem__(self, key):
		hashed_key = hash_object(key, base=64)
		del self._dictionary[hashed_key]

	def keys(self):
		return [key_value[0] for hashed_key, key_value in self._dictionary.items()]

	def pop(self, item):
		hashed_key = hash_object(item, base=64)
		return self._dictionary.pop(hashed_key)[1]

	@property
	def size(self):
		return len(self._dictionary)

class Cache:
	def __init__(self, on_disk=True, path=None, buffer_max=10000):
		self._on_disk = on_disk
		self._buffer = Dictionary()
		self._buffer_max = buffer_max
		self._stats = {
			'set_success': 0, 'get_success': 0, 'get_failure': 0, 'set_failure': 0, 'set_time': None, 'get_time': None
		}
		self._children = []
		if on_disk:
			if path is None:
				raise ValueError('On-disk cache needs a path!')
			else:
				self._hard_folder = HardFolder(path=path)
			atexit.register(self.empty_buffer)

	def __del__(self):
		self.empty_buffer()
		atexit.unregister(self.empty_buffer)

	def __getitem__(self, item):
		try:
			if self._on_disk:
				if item in self._buffer:
					result = self._buffer[item]
				else:
					result = self._hard_folder[item]
			else:
				result = self._buffer[item]
		except Exception as e:
			self._stats['get_failure'] += 1
			raise e

		self._stats['get_success'] += 1
		return result

	def __setitem__(self, key, value):
		try:
			self._buffer[key] = value
		except Exception as e:
			self._stats['set_failure'] += 1
			raise e

		if self._buffer.size > self._buffer_max:
			self.empty_buffer()
		self._stats['set_success'] += 1

	def __contains__(self, item):
		if item in self._buffer:
			return True
		elif self._on_disk:
			return item in self._hard_folder

	def __delitem__(self, key):
		if key in self._buffer:
			del self._buffer[key]
			if key in self._hard_folder:
				del self._hard_folder[key]
		elif key in self._hard_folder:
			del self._hard_folder[key]
		else:
			raise KeyError(f'{key} does not exist in either buffer or hard folder!')

	@property
	def path(self):
		return self._hard_folder._path.string

	@property
	def statistics(self):
		result = {self.path: self._stats.copy()}
		for child in self._children:
			for key, value in child.statistics.items():
				result[key] = value
		return result

	def empty_buffer(self):
		"""
		empties the buffer of cache
		"""
		if self._on_disk:
			keys = list(self._buffer.keys())
			for key in keys:
				self._hard_folder[key] = self._buffer.pop(key)
		else:
			raise RuntimeError('Cannot empty the buffer! There is no hard_folder!')

	def make_cached(
			self, function, id=None, condition_function=None, sub_directory=None, key_args=True, key_kwargs=True
	):
		"""
		:param callable function: function to be cached
		:param Cache cache:
		:param int or str id: a unique identifier for function
		:param callable condition_function: a function that determines if the result is worthy of caching
		:param str if_error: what to do if error happens: warning, error, print, ignore
		:param list[int] or bool key_args: either True/False for including/excluding all args in the hash key or a list of indices of args to be included
		:param list[str] or bool key_kwargs: either True/False for including/excluding all kwargs in the hash key or a list of the kwargs to be included
		:rtype: callable
		"""
		if sub_directory is None:
			return make_cached(
				function=function, cache=self, id=id, condition_function=condition_function,
				key_args=key_args, key_kwargs=key_kwargs
			)
		else:
			sub_path = self._hard_folder._path + sub_directory
			sub_cache = self.__class__(path=sub_path.path, on_disk=self._on_disk)
			self._children.append(sub_cache)
			return make_cached(
				function=function, cache=sub_cache, id=id, condition_function=condition_function
			)


def make_cached(
		function, cache, id=0, condition_function=None, if_error='warning', key_args=True, key_kwargs=True
):
	"""
	:param callable function: function to be cached
	:param Cache cache:
	:param int or str id: a unique identifier for function
	:param callable condition_function: a function that determines if the result is worthy of caching
	:param str if_error: what to do if error happens: warning, error, print, ignore
	:param list[int] or bool key_args: either True/False for including/excluding all args in the hash key or a list of indices of args to be included
	:param list[str] or bool key_kwargs: either True/False for including/excluding all kwargs in the hash key or a list of the kwargs to be included
	:rtype: callable
	"""
	if not isinstance(key_args, (bool, list)):
		raise TypeError('key_args should be either boolean or list.')
	if not isinstance(key_kwargs, (bool, list)):
		raise TypeError('key_kwargs should be either boolean or list.')

	if_error = if_error.lower()[0]
	@functools.wraps(function)
	def wrapper(*args, **kwargs):
		if key_args == True:
			args_in_key = args
		elif isinstance(key_args, list):
			args_in_key = tuple(map(args.__getitem__, key_args))
		else:
			args_in_key = None

		if key_kwargs == True:
			kwargs_in_key = kwargs
		elif isinstance(key_kwargs, list):
			kwargs_in_key = {key: kwargs[key] for key in key_kwargs}
		else:
			kwargs_in_key = None

		key = (id, function.__name__, function.__doc__, args_in_key, kwargs_in_key)

		if key in cache:
			try:
				return cache[key]
			except EOFError as e:
				if if_error == 'w':  # warning
					warnings.warn(str(e))
				elif if_error == 'e':  # error
					raise e
				elif if_error == 'p':  # print
					print(e)
				# else: ignore

		result = function(*args, **kwargs)
		if condition_function is None:
			cache[key] = result
		elif condition_function(result, *args, **kwargs):
			cache[key] = result
		return result
	wrapper.cache = cache
	wrapper.empty_buffer = cache.empty_buffer

	return wrapper
