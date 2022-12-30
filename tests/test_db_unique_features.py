##!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import unittest

from gbd_core.query_builder import GBDQuery
from gbd_core.database import Database
from gbd_core.schema import Schema

from tests import util

class DatabaseTestCase(unittest.TestCase):

    feat = "unique_feature"
    val1 = "value1"
    val2 = "value2"
    defv = "empty"

    def setUp(self) -> None:
        self.file = util.get_random_unique_filename('test', '.db')
        self.name = Schema.dbname_from_path(self.file)
        self.db = Database([self.file], verbose=False)
        self.db.create_feature(self.feat, default_value=self.defv)
        self.db.set_values(self.feat, self.val1, ["a", "b", "c"])
        return super().setUp()

    def tearDown(self) -> None:
        if os.path.exists(self.file):
            os.remove(self.file)
        return super().tearDown()

    def query(self, feat, val):
        qb = GBDQuery(self.db)
        q = qb.build_query("{}={}".format(feat, val))
        return [ hash for (hash, ) in self.db.query(q) ]

    def dump(self):
        import sqlite3
        conn = sqlite3.connect(self.file)
        for line in conn.iterdump():
            print(line)
        conn.close()

    # Test that the feature values are initialized correctly in test setup
    def test_unique_feature_values_exist(self):
        res = self.query(self.feat, self.val1)
        self.assertEqual(len(res), 3)
        self.assertSetEqual(set(res), set(["a", "b", "c"]))

    # Overwrite one value and check if it is set correctly and that the other values are still there
    def test_unique_feature_values_overwrite(self):
        self.db.set_values(self.feat, self.val2, ["a"])
        res = self.query(self.feat, self.val1)
        self.assertEqual(len(res), 2)
        self.assertSetEqual(set(res), set(["b", "c"]))
        res2 = self.query(self.feat, self.val2)
        self.assertEqual(len(res2), 1)
        self.assertSetEqual(set(res2), set(["a"]))

    # Delete specific hash-value pair and check if it is deleted (=set to default value) and that the other values are still there
    def test_unique_feature_values_delete_hash_value(self):
        self.db.delete(self.feat, [ self.val1 ], ["a"])
        res = self.query(self.feat, self.val1)
        self.assertEqual(len(res), 2)
        self.assertSetEqual(set(res), set(["b", "c"]))
        res = self.query(self.feat, self.defv)
        self.assertEqual(len(res), 1)
        self.assertSetEqual(set(res), set(["a"]))

    # Delete specific hash and check if it is deleted (=set to default value) and that the other values are still there
    def test_unique_feature_values_delete_hash(self):
        self.db.delete(self.feat, [ ], ["a"])
        res = self.query(self.feat, self.val1)
        self.assertEqual(len(res), 2)
        self.assertSetEqual(set(res), set(["b", "c"]))
        res = self.query(self.feat, self.defv)
        self.assertEqual(len(res), 1)
        self.assertSetEqual(set(res), set(["a"]))

    # Delete specific value and check if it is deleted (=set to default value) and that the other values are still there
    def test_unique_feature_values_delete_value(self):
        self.db.delete(self.feat, [ self.val1 ], [ ])
        res = self.query(self.feat, self.val1)
        self.assertEqual(len(res), 0)
        res = self.query(self.feat, self.defv)
        self.assertEqual(len(res), 3)
        self.assertSetEqual(set(res), set([ "a", "b", "c" ]))

    # Delete feature
    def test_unique_feature_delete(self):
        self.db.delete_feature(self.feat)
        self.assertFalse(self.db.fexists(self.feat))
