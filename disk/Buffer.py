from slytherin.hash import hash_object
from datetime import datetime


class Buffer:
	def __init__(self):
		self._dictionary = dict()

	def __getstate__(self):
		return self._dictionary

	def __setstate__(self, state):
		self._dictionary = state

	def __hashkey__(self):
		return (self.__class__.__name__, id(self))

	def __getitem__(self, item):
		hashed_key = hash_object(item, base=64)
		return self._dictionary[hashed_key][1]

	def __setitem__(self, key, value):
		hashed_key = hash_object(key, base=64)
		self._dictionary[hashed_key] = (key, value, datetime.now())

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

	def get_time(self, item):
		hashed_key = hash_object(item, base=64)
		return self._dictionary[hashed_key][2]

	def keys(self):
		return [key_value[0] for hashed_key, key_value in self._dictionary.items()]

	def pop(self, item):
		hashed_key = hash_object(item, base=64)
		return self._dictionary.pop(hashed_key)[1]

	def pop_item_and_time(self, item):
		hashed_key = hash_object(item, base=64)
		item_and_time = self._dictionary.pop(hashed_key)
		return item_and_time[1], item_and_time[2]

	@property
	def size(self):
		return len(self._dictionary)