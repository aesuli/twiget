# TwiGet

TwiGet is a python package for the management of the queries on filtered stream of the Twitter API, and the collection of tweets from it.

It can be used as a command line tool ([`twiget-cli`](#command-line-tool-twiget-cli)) or as a python class ([`TwiGet`](#python-class-twiget)).

## Installation

```
> pip install twiget
```

The command installs the package and also makes the `twiget-cli` command available. 

## Command line tool: twiget-cli

TwiGet implements a command line interface that can be started with the command:
```
> twiget-cli
```
When launched without arguments the program searches for a `.twiget.conf` file in the `HOME` directory (the directory pointed by the `$HOME` or `%userprofile%` environment variable).
The file must contain in the first line the [__bearer token__](https://developer.twitter.com/en/docs/authentication/oauth-2-0/bearer-tokens) that allows the program to access the Twitter API.

Alternatively, the name of the file from which to obtain the bearer token can be given as argument when starting the program:
```
> twiget-cli -b path_to_file/with_token.txt
```

__NOTE: store the bearer token in a file with minimum access permissions. Never share it. Revoke any tokens that may have been made public.__

Another optional argument is the path where to save collected tweets.
By default, a `data` subdirectory is created in the current working directory.
```
> twiget-cli -s ./save_dir
```

#### prompt
When started, twiget-cli shown the available commands, and the queries currently registered for the given bearer token (queries are permanently stored on Twitter's servers).
```
TwiGet 0.1.1

Available commands (type help <command> for details):
create, delete, exit, help, list, refresh, save_to, size, start, stop

Registered queries:
	ID=1385892384573355842	query="#usa"	tag="usa"
	ID=1405490304970434817	query="bts"	tag="bts"
```
The command prompt tells if twiget-cli is currently collecting tweets, the number of collected tweets, and the save path.
```
[not collecting (0 since last start), save path "data"]>
```
When collecting tweets, the prompt is automatically refreshed every time a given number of tweets is collected (see [the refresh command](#refresh)).
### Commands

#### create

Format:
```
> create <tag> <query>
```
Creates a filtering rule, associated to a given tag name.  
Collected tweets are saved in json format in a file named `<tag>.json`, in the given save path. 
Tag name is the first argument of the command and cannot contain spaces.  
Any word after the tag defines the query.
[Info on how to define rules](https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/integrate/build-a-rule).  

Example:
```
[not collecting (0 since last start), save path "data"]>create usa jow biden
Tweets matching the query "jow biden" will be saved in the file data/usa.json
ID=1395720345987340524
```

#### list
Format:
```
> list
```
Lists the queries, their ID and their tag, currently registered for the filtered stream.

Example:
```
[not collecting (0 since last start), save path "data"]> list
Registered queries:
	ID=1385892384573355842	query="#usa"	tag="usa"
	ID=13905490304970434817	query="bts"	tag="bts"
	ID=1395720345987340524	query="joe biden"	tag="usa"
```

#### delete
Format:
```
> delete <ID>
```
Deletes a query, given its ID.

Example:
```
[not collecting (0 since last start), save path "data"]> delete 1385892384573355842
```

#### start
Format:
```
> start
```

Starts a background process that collects tweets from the filtered stream and puts them in json files, according to the tag they are associated to.

Collection continues until a `stop` or a `exit` command is entered. 
To let TwiGet collect data for longer periods of time, I suggest to use TwiGet within a virtual terminal session, using, e.g.,  `screen` or `tmux`. 

_Note: create and delete command can be issued also when collecting tweets. The collection process is updated immediately._

Example:
```
[not collecting (0 since last start), save path "data"]> start
[collecting (0 since last start), save path "data"]>
```
#### stop
Format:
```
> stop
```
Stop data collections.

Example:
```
[collecting (3000 since last start), save path "data"]> stop
[not collecting (3152 since last start), save path "data"]> 
```

#### save_to
Format:
```
> save_to <path>
```
Sets the path where json files are saved.

_Note: changing path while collecting tweets will immediately create new json file in the new path, leaving all tweets collected until that moment in the old path. 

Example:
```
[not collecting (0 since last start), save path "data"]> save_to ../my_project
[not collecting (0 since last start), save path "../my_project"]> 
```
#### size
Format:
```
> size <size>
```
Sets the maximum size in bytes of json files.
When a json file reaches this size, a new file with an incremented index (e.g., tag_0.json, tag_1.json, tag_2.json...) is created.

Example:
```
[not collecting (0 since last start), save path "data"]> size 1000000
```
#### refresh
Format:
```
> refresh <count>
```
Sets the number of collected tweets that triggers an automatic refresh of the prompt. 

Example:
```
[not collecting (0 since last start), save path "data"]> refresh 10000
```


## Python class: TwiGet

TwiGet core functionalities are implemented in a python class, which can be directly used in python code.

```python
from twiget import TwiGet

bearer = 'put here the bearer token'

collector = TwiGet(bearer)

# Adding a filtering rule
# https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/api-reference/post-tweets-search-stream-rules
query = 'support vector machine'
tag = 'ml'
answer = collector.add_rule(query, tag)
# returns the parsed json answer from the server.
print(answer)

# Listing the current filtering rules
# https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/api-reference/get-tweets-search-stream-rules
answer = collector.get_rules()
# returns the parsed json answer from the server.
print(answer)

# Delete some rules by giving their ID
# https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/api-reference/post-tweets-search-stream-rules
ids = [48573094587309485,3029834285720978]
answer = collector.delete_rules(ids)
# returns the parsed json answer from the server.
print(answer)

# Adding a callback
# The data argument contains the content and information about the retrieved tweet
# https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/api-reference/get-tweets-search-stream
def print_tag(data):
    print(data['matching_rules'][0]['tag'])
    
answer = collector.add_callback('print tag', print_tag)
# returns the parsed json answer from the server.
print(answer)


# Getting callbacks
callbacks = collector.get_callbacks()
# returns a list with the names of the callbacks.
print(callbacks)

# Delete a callback
collector.delete_callback('print tag')

# Starting tweet collection
collector.start_getting_stream()

# Checking status of collection
running = collector.is_getting_stream()
# returns a boolean. True if collection is active.
print(running)

# Stopping tweet collection
collector.stop_getting_stream()
```

## License

Author: [Andrea Esuli](http://esuli.it)

BSD 3-Clause License, see [license file](COPYING)
