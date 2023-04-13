import json
import os.path
import sys


class JSONFilesystem:
    """
    Helper class creating a pseudo-filesystem represented as a nested series of JSON-like dictionaries, in order to
    allow for a compact representation of symbol SVG elements
    """

    def __init__(self):
        self.json: dict = {}

    def __repr__(self):
        return str(self.json)

    def get_contents_at_path(self, path):
        """
        Returns the contents of the pseudo-filesystem at the given path.
        :param path: The path to search in
        :return: A Python object representing the contents at the given path, or None if it can't be found.
        """
        path_list = os.path.normpath(path).split(os.sep)
        cursor_element = self.json
        for path_element in path_list[:-1]:
            if path_element in cursor_element.keys():
                # "Folder" exists
                cursor_element = cursor_element[path_element]
            else:
                raise FileNotFoundError(path)

        if path_list[-1] not in cursor_element.keys():
            raise FileNotFoundError(path)

        return cursor_element[path_list[-1]]

    def set_contents_at_path(self, path, contents, create_if_nonexistent=False):
        """
        Sets the contents of the pseudo-filesystem at the given path
        :param path: The path to the "file" to write
        :param contents: The contents to set the resulting file to
        :param create_if_nonexistent: Whether to create the path to the given item if it doesn't already exist; defaults to false.
        :return:
        """
        path_list = os.path.normpath(path).split(os.sep)

        # print(path_list[:-1])
        cursor_element = self.json
        for path_element in path_list[:-1]:
            if path_element in cursor_element.keys():
                # It exists
                cursor_element = cursor_element[path_element]
            else:
                if create_if_nonexistent:
                    # It doesn't exist; create it
                    cursor_element[path_element] = {}
                    cursor_element = cursor_element[path_element]
                else:
                    print(f"ERROR: path \"{path}\" doesn't exist in the JSONFilesystem", file=sys.stderr)
                    raise FileNotFoundError

        cursor_element[path_list[-1]] = contents

    def get_dump_string(self):
        """
        Returns a JSON dump of the contents of the pseudo-filesystem
        """
        return json.dumps(self.json)

    def dump_to_file(self, filepath):
        """
        Write a JSON dump of the pseudo-filesystem to disk at the specified filepath.
        :param filepath:
        """
        with open(filepath, 'w') as out_file:
            json.dump(self.json, out_file)

    def read_from_file(self, filepath):
        """
        Reads values into the pseudo-filesystem from the JSON file located on disk at the specified path.
        :param filepath:
        :return:
        """
        with open(filepath, 'r') as in_file:
            self.json = json.load(in_file)
