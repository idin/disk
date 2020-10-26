class DiskError(RuntimeError):
	pass


class SaveError(DiskError):
	pass


class LoadError(DiskError):
	pass


class RenameError(DiskError):
	pass


class PathDoesNotExistError(DiskError):
	pass


class PathExistsError(DiskError):
	pass


class NotAFileError(FileNotFoundError):
	pass


class DirectoryNotFoundError(NotADirectoryError):
	pass
