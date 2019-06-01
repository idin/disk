from .HardFolder import HardFolder
from .Buffer import Buffer

import atexit
import functools
import warnings


class Cache:
	def __init__(self, on_disk=True, path=None, buffer_max=1000):
		self._on_disk = on_disk
		self._buffer = Buffer()
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
		else:
			self._hard_folder = None

	@property
	def hard_folder(self):
		"""
		:rtype: HardFolder
		"""
		return self._hard_folder

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
		return self.hard_folder._path.string

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
				item_and_time = self._buffer.pop_item_and_time(key)
				self.hard_folder.set_item(key=key, value=item_and_time[0], time=item_and_time[1])
		else:
			raise RuntimeError('Cannot empty the buffer! There is no hard_folder!')

	def empty_all_buffers(self):
		self.empty_buffer()
		for child in self._children:
			child.empty_all_buffers()

	def make_cached(
			self, function, id=None, condition_function=None, if_error='warning', sub_directory=None,
			key_args=True, key_kwargs=True
	):
		"""
		:param callable function: function to be cached
		:param int or str id: a unique identifier for function
		:param callable condition_function: a function that determines if the result is worthy of caching
		:param str if_error: what to do if error happens: warning, error, print, ignore
		:param str sub_directory: name of a sub directory inside the cache directory to be used, optional
		:param list[int] or bool key_args: either True/False for including/excluding all args in the hash key or a list of indices of args to be included
		:param list[str] or bool key_kwargs: either True/False for including/excluding all kwargs in the hash key or a list of the kwargs to be included
		:rtype: callable
		"""
		if sub_directory is None:
			return make_cached(
				function=function, cache=self, id=id, condition_function=condition_function,
				if_error=if_error, key_args=key_args, key_kwargs=key_kwargs
			)
		else:
			sub_path = self._hard_folder._path + sub_directory
			sub_cache = self.__class__(path=sub_path.path, on_disk=self._on_disk)
			self._children.append(sub_cache)
			return make_cached(
				function=function, cache=sub_cache, id=id, condition_function=condition_function,
				if_error=if_error, key_args=key_args, key_kwargs=key_kwargs
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
		if isinstance(key_args, list):
			args_in_key = tuple(map(args.__getitem__, key_args))
		elif key_args:
			args_in_key = args
		else:
			args_in_key = None

		if isinstance(key_kwargs, list):
			kwargs_in_key = {key: kwargs[key] for key in key_kwargs}
		elif key_kwargs:
			kwargs_in_key = kwargs
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
		elif condition_function(result=result, args=args, kwargs=kwargs):
			cache[key] = result

		return result
	wrapper.cache = cache
	wrapper.empty_buffer = cache.empty_buffer

	return wrapper
