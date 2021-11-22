import json
import os.path


class JSONFilesystem:

    def __init__(self):
        self.json:dict = {}

    def __repr__(self):
        return str(self.json)

    def get_contents_at_path(self, path):
        path_list = os.path.normpath(path).split(os.sep)
        cursor_element = self.json
        for path_element in path_list[:-1]:
            if path_element in cursor_element.keys():
                # "Folder" exists
                cursor_element = cursor_element[path_element]
            else:
                # print(f'ERROR: File not found "{path}" in JSONFilesystem')
                raise FileNotFoundError(path)

        if path_list[-1] not in cursor_element.keys():
            # print(f'ERROR: File not found "{path}" in JSONFilesystem')
            raise FileNotFoundError(path)

        return cursor_element[path_list[-1]]

    def set_contents_at_path(self, path, contents, create_if_nonexistent=False):
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
                    print(f"ERROR: path \"{path}\" doesn't exist in the JSONFilesystem")

        cursor_element[path_list[-1]] = contents

    def get_dump_string(self):
        return json.dumps(self.json)

    def dump_to_file(self, filepath):
        with open(filepath, 'w') as out_file:
            json.dump(self.json, out_file)

    def read_from_file(self, filepath):
        with open(filepath, 'r') as in_file:
            self.json = json.load(in_file)
