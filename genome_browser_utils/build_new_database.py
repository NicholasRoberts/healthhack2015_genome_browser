#!/usr/bin/python

import MySQLdb
import re
import os
import csv
import sys
import string
from sqlalchemy import create_engine, desc

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, MetaData

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.automap import automap_base


def generate_sql_dict_from_csv(naming_csv):
    transactions = []
    engine = create_engine(
        "mysql+pymysql://root:mysqlroot@localhost/hgcentral")
    Base = automap_base()
    Base.prepare(engine, reflect=True)
    Session = sessionmaker(bind=engine)
    db = Session()
    Genome = Base.classes.defaultDb
    with open(naming_csv, 'rb') as f:
        reader = csv.reader(f)
        print "reading headers..."
        header = reader.next()
        for rownum, row in enumerate(reader):
            print "reading data..."
            proc_row =  row[0].split(";")
	    print len(proc_row)
            splitName = proc_row[1].split()
            genomes = map(lambda x: {'name': x.name, 'abbrev': x.genome}, db.query(
                Genome).all())
            name = splitName[0][
                :3].lower() + splitName[1][0].upper() + splitName[1][1:3].lower()
            prior_versions = filter(lambda x: not x.startswith(name), map(lambda x: x['name'], genomes))
            all = string.maketrans('', '')
            nodigs = all.translate(all, string.digits)
            if name in prior_versions:
                name += str(max(map(lambda x: int(x.translate(all, nodigs)), prior_versions)) + 1)
            else:
                name += '1'
            sql_dict = { "name": "%s" % name, "desc": "%s" % name, "nib": "/gbdb/%s" % name, "organism": "%s" % proc_row[1], "defaultPos": "%s" % proc_row[2], "active": 1, "orderKey": rownum, "genome": "%s" % proc_row[3], "scientificName": "%s" % proc_row[4], "htmlPath": "/gbdb/%s/html/description.html" % name, "hgNearOk": 0, "hgPbOk": 0, "sourceName": "%s" % proc_row[5], "taxId": "%s" % proc_row[6] }
            transactions.append(sql_dict)

    return transactions

def execute_sql_queries(transactions):
    # Step 11
    # setting up the MySQL connection
    try:
        print "opening database"
        db = MySQLdb.connect(host="localhost", user="root", passwd="mysqlroot", db="hgcentral")
        dbcursor = db.cursor()
        for trans in transactions:
            for x,y in trans.iteritems():
                print "%s: %s" % (x,y)

            dbcursor.execute("""INSERT INTO dbDb (name, description, nibPath, organism, defaultPos, active, orderKey, genome, scientificName, htmlPath, hgNearOk, hgPbOk, sourceName, taxId) VALUES (%(name)s, %(desc)s, %(nib)s, %(organism)s, %(defaultPos)s, %(active)s, %(orderKey)s, %(genome)s, %(scientificName)s, %(htmlPath)s, %(hgNearOk)s, %(hgPbOk)s, %(sourceName)s, %(taxId)s)""", trans)

            print "entered successfully into DBDB"

            dbcursor.execute("""INSERT INTO defaultDb (genome, name) VALUES (%(genome)s, %(name)s)""", trans)
            dbcursor.execute("""INSERT INTO genomeClade (genome, clade, priority) VALUES (%(genome)s, 'insect', 10)""", trans)

        '''
        DELETE FROM `dbDb` where `orderKey` = 1 or `orderKey` =2
        '''
        return 0
    except Exception as e:
        print e
        print "Opening database failed"
        return 1045

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "usage: build_new_database.py <filename>"
        sys.exit()

    if not os.path.isfile(sys.argv[1]):
        print "%s is not a file" % sys.argv[1]
        print "usage: build_new_database.py <filename>"
        sys.exit()

    transactions = generate_sql_dict_from_csv(sys.argv[1])
    execute_sql_queries(transactions)
