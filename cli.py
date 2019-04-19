#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import os
import re
import sys
from os.path import exists

import server
from main.core.http_client import is_url
from main.core.util import eprint, read_hashes, confirm
from main.interface import gbd_api


def cli_hash(args):
    eprint('Hashing Benchmark: {}'.format(args.path))
    print(gbd_api.hash_file(args.path))


def cli_import(args):
    eprint('Importing Data from CSV-File: {}'.format(args.path))
    gbd_api.import_file(args.db, args.path, args.key, args.source, args.target)


def cli_init(args):
    if args.path is not None:
        eprint('Removing invalid benchmarks from path: {}'.format(args.path))
        eprint('Registering benchmarks from path: {}'.format(args.path))
        gbd_api.init_database(args.db, args.path)
    else:
        gbd_api.init_database(args.db)


# entry for modify command
def cli_group(args):
    if args.name.startswith("__"):
        eprint("Names starting with '__' are reserved for system tables")
        return
    if gbd_api.check_group_exists(args.db, args.name):
        eprint("Group {} does already exist".format(args.name))
    elif not args.remove and not args.clear:
        eprint("Adding or modifying group '{}', unique {}, type {}, default-value {}".format(args.name,
                                                                                             args.unique
                                                                                             is not None,
                                                                                             args.type,
                                                                                             args.unique))
        gbd_api.add_attribute_group(args.db, args.name, args.type, args.unique)
        return
    if not gbd_api.check_group_exists(args.db, args.name):
        eprint("Group '{}' does not exist".format(args.name))
        return
    if args.remove and confirm("Delete group '{}'?".format(args.name)):
        gbd_api.remove_attribute_group(args.db, args.name)
    else:
        if args.clear and confirm("Clear group '{}'?".format(args.name)):
            gbd_api.clear_group(args.db, args.name)
    return


# entry for query command
def cli_get(args):
    if is_url(args.db) and not exists(args.db):
        try:
            hashes = gbd_api.query_request(args.db, args.query, server.USER_AGENT_CLI)
        except ValueError:
            print("Path does not exist or cannot connect")
            return
    else:
        try:
            hashes = gbd_api.query_search(args.db, args.query)
        except ValueError as e:
            print(e)
            return
    process_hashes(hashes, args.union, args.intersection)
    print(*hashes, sep='\n')
    return


def process_hashes(hashes, union, intersection):
    if union:
        inp = read_hashes()
        gbd_api.hash_union(hashes, inp)
    elif intersection:
        inp = read_hashes()
        gbd_api.hash_intersection(hashes, inp)
    return


# associate an attribute with a hash and a value
def cli_set(args):
    hashes = read_hashes()
    if args.remove and (args.force or confirm("Delete tag '{}' from '{}'?".format(args.value, args.name))):
        gbd_api.remove_attribute(args.db, args.name, args.value, hashes)
    else:
        gbd_api.set_attribute(args.db, args.name, args.value, hashes, args.force)


def cli_resolve(args):
    hashes = read_hashes()
    if is_url(args.db) and not exists(args.db):
        try:
            print(gbd_api.resolve_request(args.db, list(hashes), args.name, args.collapse,
                                          args.pattern, server.USER_AGENT_CLI))
        except ValueError as e:
            print(e)
        return
    result = gbd_api.resolve(args.db, hashes, args.name, args.pattern, args.collapse)
    for element in result:
        print(','.join(element))


def cli_info(args):
    if args.name is not None:
        if args.values:
            info = gbd_api.get_group_values(args.db, args.name)
            print(*info, sep='\n')
        else:
            info = gbd_api.get_group_info(args.db, args.name)
            print('name: {}'.format(info.get('name')))
            print('type: {}'.format(info.get('type')))
            print('uniqueness: {}'.format(info.get('uniqueness')))
            print('default value: {}'.format(info.get('default')))
            print('number of entries: {}'.format(*info.get('entries')))
    else:
        result = gbd_api.get_database_info(args.db)
        print("DB '{}' was created with version: {} and HASH version: {}".format(result.get('name'),
                                                                                 result.get('version'),
                                                                                 result.get('hash-version')))
        print("Found tables:")
        print(*gbd_api.get_all_tables(args.db))


# define directory type for argparse
def directory_type(dir):
    if not os.path.isdir(dir):
        raise argparse.ArgumentTypeError('{0} is not a directory'.format(dir))
    if os.access(dir, os.R_OK):
        return dir
    else:
        raise argparse.ArgumentTypeError('{0} is not readable'.format(dir))


def file_type(path):
    if not os.path.isfile(path):
        raise argparse.ArgumentTypeError('{0} is not a regular file'.format(path))
    if os.access(path, os.R_OK):
        return path
    else:
        raise argparse.ArgumentTypeError('{0} is not readable'.format(path))


def column_type(s):
    pat = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")
    if not pat.match(s):
        raise argparse.ArgumentTypeError('group-name:{0} does not match regular expression {1}'.format(s, pat.pattern))
    return s


def main():
    parser = argparse.ArgumentParser(description='Access and maintain the global benchmark database.')

    parser.add_argument('-d', "--db", help='Specify database to work with', default=gbd_api.DEFAULT_DATABASE, nargs='?')

    subparsers = parser.add_subparsers(help='Available Commands:')

    parser_init = subparsers.add_parser('init', help='Initialize Database')
    parser_init.add_argument('path', type=directory_type, help="Path to benchmarks")
    parser_init.add_argument('-r', '--remove', help='Remove hashes with invalid paths from benchmark table',
                             action='store_true')
    parser_init.set_defaults(func=cli_init)

    parser_hash = subparsers.add_parser('hash', help='Print hash for a single file')
    parser_hash.add_argument('path', type=file_type, help="Path to one benchmark")
    parser_hash.set_defaults(func=cli_hash)

    parser_import = subparsers.add_parser('import', help='Import attributes from comma-separated csv-file with header')
    parser_import.add_argument('path', type=file_type, help="Path to csv-file")
    parser_import.add_argument('-k', '--key', type=column_type,
                               help="Name of the key column (the hash-value of the problem)", required=True)
    parser_import.add_argument('-s', '--source', type=column_type, help="Source name of column to import (in csv-file)",
                               required=True)
    parser_import.add_argument('-t', '--target', type=column_type, help="Target name of column to import (in Database)",
                               required=True)
    parser_import.set_defaults(func=cli_import)

    # define info
    parser_reflect = subparsers.add_parser('info', help='Get information, Display Groups')
    parser_reflect.add_argument('name', type=column_type, help='Display Details on Group, info of Database if none',
                                nargs='?')
    parser_reflect.add_argument('-v', '--values', action='store_true', help='Display Distinct Values of Group if given')
    parser_reflect.set_defaults(func=cli_info)

    # define create command sub-structure
    parser_group = subparsers.add_parser('group', help='Create or modify an attribute group')
    parser_group.add_argument('name', type=column_type, help='Name of group to create (or modify)')
    parser_group.add_argument('-u', '--unique', help='Specify if the group stores unique or '
                              '(by default) several attributes per benchmark (expects default value which has to match '
                              'type if set)')
    parser_group.add_argument('-t', '--type', help='Specify the value type of the group (default: text)',
                              default="text", choices=['text', 'integer', 'real'])
    parser_group.add_argument('-r', '--remove', action='store_true',
                              help='If group exists: remove the group with the specified name')
    parser_group.add_argument('-c', '--clear', action='store_true',
                              help='If group exists: remove all values in the group with the specified name')
    parser_group.set_defaults(func=cli_group)

    # define set command sub-structure
    parser_tag = subparsers.add_parser('set',
                                       help='Associate attribues with benchmarks (hashes read line-wise from stdin)')
    parser_tag.add_argument('name', type=column_type, help='Name of attribute group')
    parser_tag.add_argument('-v', '--value', help='Attribute value', required=True)
    parser_tag.add_argument('-r', '--remove', action='store_true',
                            help='Remove attribute from hashes if present, instead of adding it')
    parser_tag.add_argument('-f', '--force', action='store_true', help='Overwrite existing values')
    parser_tag.set_defaults(func=cli_set)

    # define find command sub-structure
    parser_query = subparsers.add_parser('get', help='Query the benchmark database')
    parser_query.add_argument('query', help='Specify a query-string (e.g. "variables > 100 and path like %%mp1%%")',
                              nargs='?')
    parser_query.add_argument('-u', '--union', help='Read hashes from stdin and create union with query results',
                              action='store_true')
    parser_query.add_argument('-i', '--intersection',
                              help='Read hashes from stdin and create intersection with query results',
                              action='store_true')
    parser_query.set_defaults(func=cli_get)

    # define resolve command
    parser_resolve = subparsers.add_parser('resolve', help='Resolve Hashes')
    parser_resolve.add_argument('name', type=column_type, help='Name of group to resolve against',
                                default=["benchmarks"], nargs='*')
    parser_resolve.add_argument('-c', '--collapse', action='store_true', help='Show only one representative per hash')
    parser_resolve.add_argument('-p', '--pattern', help='Substring that must occur in path')
    parser_resolve.set_defaults(func=cli_resolve)

    # evaluate arguments
    if len(sys.argv) > 1:
        args = parser.parse_args()
        args.func(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
