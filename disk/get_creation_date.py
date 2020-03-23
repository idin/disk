import os
import platform


def get_creation_date(path):
	"""
	From: https://stackoverflow.com/questions/237079/how-to-get-file-creation-modification-date-times-in-python
	Try to get the date that a file was created, falling back to when it was
	last modified if that isn't possible.
	See http://stackoverflow.com/a/39501288/1709587 for explanation.
	"""
	if platform.system() == 'Windows':
		return os.path.getctime(path)
	else:
		stat = os.stat(path)
		try:
			return stat.st_birthtime
		except AttributeError:
			# We're probably on Linux. No easy way to get creation dates here,
			# so we'll settle for when its content was last modified.
			return stat.st_mtime


def get_modification_date(path):
	return os.path.getmtime(path)
