#!python
import json
import os
import re
import sys
from cmd import Cmd
from pathlib import Path
from threading import Lock
from typing import Dict, TextIO

import twiget
from twiget import TwiGet


class TwiGetCLIBase(Cmd):
    MIN_REFRESH = 10
    DEFAULT_REFRESH = 1000

    def __init__(self, bearer: str):
        super().__init__()

        self._twiget = TwiGet(bearer)

        self._refresh = self.DEFAULT_REFRESH
        self._count = 0
        self._twiget.add_callback('counter', self._counter)

        print(f'TwiGet {twiget.__version__}')
        print()
        print('Available commands (type help <command> for details):')
        print(', '.join([name[3:] for name in self.get_names() if name[:3] == 'do_']))
        print()
        print('Reminder: add -is:retweet to a rule to exclude retweets from results, and to get only original content.')
        self.do_list('')
        print()

    def _counter(self, data):
        self._count += 1
        if self._count % self._refresh == 0:
            print(os.linesep + self.prompt, end='')

    @property
    def prompt(self) -> str:
        return f'[{"collecting" if self._twiget.is_getting_stream() else "not collecting"} ({self._count} since last start)]> '

    def emptyline(self):
        pass

    def do_exit(self, args):
        if self._twiget.is_getting_stream():
            print('Stopping collection of tweets.')
            self._twiget.stop_getting_stream()
        sys.exit(0)

    def help_exit(self):
        print('Exit the program')

    def do_list(self, args):
        data = self._twiget.get_rules()
        data = data.get('data', None)
        print('Registered queries:')
        found = False
        if data:
            for entry in data:
                found = True
                print(f"\tID={entry['id']}\tquery=\"{entry['value']}\"\ttag=\"{entry['tag']}\"")
        if not found:
            print('\tno registered queries')

    def help_list(self):
        print(
            'Lists the queries, their ID and their tag, currently registered for the filtered stream.')

    def do_start(self, args):
        self._count = 0
        self._twiget.start_getting_stream()

    def help_start(self):
        print('Starts the collection of tweets. Continues if already collecting (resets counter).')

    def do_stop(self, args):
        self._twiget.stop_getting_stream()

    def help_stop(self):
        print('Stops the collection of tweets. Nothing happens if already not collecting.')

    def do_create(self, args):
        values = args.split(' ', 1)
        if len(values) != 2:
            print('Create command requires a tag and a query.')
        else:
            answer = self._twiget.add_rule(values[1], values[0])
            print(f"ID={answer['data'][0]['id']}")

    def help_create(self):
        print('Creates a filtering rule, associated to a given tag name.')
        print(
            'Info on how to define rules at https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/integrate/build-a-rule')
        print('Collected tweets are saved in json format in a file named <tag>.json, in the given save path.')
        print('Tag name is the first argument and cannot contain spaces.')
        print('Any word after the tag defines the query.')
        print('Reminder: add -is:retweet to a rule to exclude retweets from results, and to get only original content.')
        print('Format:')
        print('\t>create <tag> <query>')
        print('Example:')
        print('\t>create usa joe biden')
        print('\tTweets matching the query "joe biden" will be saved in the file <save_path>/usa.json')

    def do_delete(self, args):
        answer = self._twiget.delete_rules([args])
        if 'errors' in answer:
            print(f'Error: {answer["errors"][0]["message"]}')

    def help_delete(self):
        print('Deletes filtering rules with the given ID.')
        print('ID of rules can be obtained by using the list command.')
        print('Format:')
        print('\t>delete <ID>')

    def do_refresh(self, args):
        if len(args):
            try:
                value = int(args)
                if value >= self.MIN_REFRESH:
                    self._refresh = value
                else:
                    print(f'Refresh value cannot be smaller than {self.MIN_REFRESH}')
            except ValueError:
                print(f'Cannot parse {args} into an integer number.')
        print(f'Automatically refreshing prompt every {self._refresh} collected tweets.')

    def help_refresh(self):
        print(
            f'Sets the refresh rate, i.e. how many collected tweets trigger an automatic refresh of the prompt (default: {self.DEFAULT_REFRESH}).')
        print('Format:')
        print('\t>refresh <number>')


class TwiGetCLI(TwiGetCLIBase):
    DEFAULT_SAVE_PATH = Path('data')
    MIN_MAX_FILE_SIZE = 1024 * 100
    DEFAULT_MAX_FILE_SIZE = 1024 * 1024 * 10

    def __init__(self, bearer: str, save_path: Path = None):
        super().__init__(bearer)

        self._max_file_size = self.DEFAULT_MAX_FILE_SIZE

        if save_path is None:
            save_path = self.DEFAULT_SAVE_PATH
        save_path.mkdir(exist_ok=True)
        self._save_path = save_path
        self._files: Dict[str, TextIO] = dict()
        self._files_lock = Lock()
        self._twiget.add_callback('save_to_file', self._save_to_file)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        for tag in list(self._files):
            try:
                print(f'Closing file {self._files[tag].name}')
                self._files[tag].close()
                del self._files[tag]
            except:
                pass

    def _new_file(self, tag, idx=0):
        is_new = False
        while True:
            filename = self._save_path / f'{tag}_{idx}.json'
            if filename.exists():
                if filename.stat().st_size < self._max_file_size:
                    break
                else:
                    idx += 1
            else:
                is_new = True
                break
        if is_new:
            print(f'Creating file {filename}')
        else:
            print(f'Appending to file {filename}')
        return open(filename, mode='ta', encoding='utf-8')

    def _save_to_file(self, data):
        tag = data['matching_rules'][0]['tag']

        with self._files_lock:
            output_file: TextIO = self._files.get(tag, None)
            if not output_file:
                output_file = self._new_file(tag)
                self._files[tag] = output_file
            if output_file.tell() > self._max_file_size:
                old_name = output_file.name
                output_file.close()
                old_idx = int(re.findall('_([0-9]+).json$', old_name)[0])
                output_file = self._new_file(tag, old_idx)
                self._files[tag] = output_file

            json.dump(data, output_file)
            print(file=output_file)

    @property
    def prompt(self) -> str:
        return f'[{"collecting" if self._twiget.is_getting_stream() else "not collecting"} ({self._count} since last start), save path \"{self._save_path}\"]> '

    def do_create(self, args):
        values = args.split(' ', 1)
        if len(values) != 2:
            print('Create command requires a tag and a query.')
        else:
            print(
                f'Tweets matching the query "{values[1]}" will be saved in the file {self._save_path}/{values[0]}.json')
            answer = self._twiget.add_rule(values[1], values[0])
            print(f"ID={answer['data'][0]['id']}")

    def do_save_to(self, args):
        new_path = Path(args)
        if new_path != self._save_path:
            new_path.mkdir(exist_ok=True)
            with self._files_lock:
                self._save_path = new_path
                for tag in list(self._files):
                    try:
                        print(f'Closing file {self._files[tag].name}')
                        self._files[tag].close()
                        del self._files[tag]
                    except:
                        pass

    def help_save_to(self):
        print('Defines the path where the json files that store the tweets will be placed.')
        print('The path can be either absolute or relative to the current working directory.')
        print('If the path does not exist it is created.')
        print('Format:')
        print('\t>save_to <path>')

    def do_size(self, args):
        if len(args):
            try:
                value = int(args)
                if value >= self.MIN_MAX_FILE_SIZE:
                    self._max_file_size = value
                else:
                    print(f'File size cannot be smaller than {self.MIN_MAX_FILE_SIZE}')
            except ValueError:
                print(f'Cannot parse {args} into an integer number.')
        print(f'Maximum file size is set to {self._max_file_size}.')

    def help_size(self):
        print(
            f'Sets the maximum file size, in bytes, for the json files (default: {self.DEFAULT_MAX_FILE_SIZE}).')
        print('A distinct file is created for each tag.')
        print('File name format is <tag>_<idx>.json, where <idx> is a integer.')
        print('A new file is created whenever the current reaches the maximum size.')
        print('Format:')
        print('\t>size <number>')


def main():
    default_bearer_filename = '.twiget.conf'

    if len(sys.argv) > 1:
        if len(set(sys.argv[1:]).intersection({'-h', '--h', '--help', '-help', '-?', '/?', '/h'})) > 0:
            print(f'Usage: {sys.argv[0]} [-b bearer_filename] [-s save path]')
            print(f'\t Default bearer_filename is {default_bearer_filename} in home directory')
            print(f'\t Default save path is "{TwiGetCLI.DEFAULT_SAVE_PATH}"')
            exit()

    try:
        bearer_idx = sys.argv.index('-b') + 1
    except ValueError:
        bearer_filename = Path.home() / default_bearer_filename
    else:
        bearer_filename = sys.argv[bearer_idx]

    try:
        save_path_idx = sys.argv.index('-s') + 1
    except ValueError:
        save_path = None
    else:
        save_path = sys.argv[save_path_idx]

    try:
        with open(bearer_filename, mode='rt', encoding='utf-8') as input_file:
            bearer = input_file.readline().strip()
    except:
        print(f'Cannot load the bearer token from {bearer_filename}')
        exit(-1)

    with TwiGetCLI(bearer, save_path) as cli:
        cli.cmdloop()


if __name__ == '__main__':
    main()
