# -*- coding: utf-8 -*-
#
# PhotosTitleSetter, by Rasmus Berggrén
# 2015-05-19

import sqlite3
import os

LIBRARY_PATH_FROM_LIBROOT = "/Database/apdb/Library.apdb"
BACKUP_PATH = os.path.expanduser("~/Library/Application Support/copyTitles/")

def removeExtension(fileName):
	return os.path.splitext(fileName)[0]

def getConnection(libPath):
	libConn = sqlite3.connect(libPath)

	return libConn

def checkTitles(newLibConn, description, emptyString):
	"""Informs the user about the state of image titles in a library."""
	newLib = newLibConn.cursor()

	print("\nChecking the " + description + " library.")
	newLib.execute("SELECT count(*) FROM RKVersion")
	print("Found " + str(newLib.fetchone()[0]) + " image versions in the " + description + " library.")

	query = "SELECT count(*) FROM RKVersion WHERE name "
	if (emptyString == "NULL"): # in Photos libraries, empty titles are set to NULL
		query += "IS NOT NULL"
	else: # in iPhoto libraries, empty titles are empty
		query += "!= '" + emptyString + "'"
	newLib.execute(query)
	print(str(newLib.fetchone()[0]) + " with titles")

	query = "SELECT count(*) FROM RKVersion WHERE name "
	if (emptyString == "NULL"):
		query += "IS NULL"
	else:
		query += "= '" + emptyString + "'"
	newLib.execute(query)
	print(str(newLib.fetchone()[0]) + " without titles")

def askForLibPath(description):
	"""Asks the user for a path to a library. Returns the path."""
	pathFound = False

	while (not pathFound):
		path = raw_input("Drag the " + description + " library here and then press return/enter: \n").strip().replace("\ ", " ")

		if (os.path.splitext(path)[1] != ".apdb"): # if the user hasn't dragged in the actual database file
			path += LIBRARY_PATH_FROM_LIBROOT # presume the user dragged the library folder and add the path to the database file

		if (os.path.isfile(path)):
			pathFound = True
			print("OK, the " + description.lower() + " library database was found at " + "\"" + path + "\"")
		else:
			print("No library was found at that location. Please try again.")

	pathFound = False

	return path

def copyTitles(oldLibConn, newLibConn, verbose):
	"""Receives connections to two libraries. Finds images with matching uuids and copies over their titles."""
	oldLib = oldLibConn.cursor()
	newLib = newLibConn.cursor()

	oldLib.execute("SELECT name, uuid FROM RKVersion WHERE name != ''")

	oldInfo = oldLib.fetchone()
	i = 0

	while (oldInfo):
		query = "SELECT COUNT(*) FROM RKVersion WHERE uuid=?"
		uuidMatches = newLib.execute(query, (oldInfo[1],)).fetchone()[0]

		if (uuidMatches > 0): # if there is any uuid match
			if (verbose):
				print("Before: ")
				newLib.execute("SELECT name, uuid from RKVersion WHERE uuid=?", (oldInfo[1],)) 
				print(newLib.fetchone())

			query = "SELECT name FROM RKVersion WHERE uuid=?" 
			currentName = newLib.execute(query, (oldInfo[1],)).fetchone()[0]

			if (currentName == None): # if the new lib name is empty

				query = "UPDATE RKVersion SET name=? WHERE uuid=?"
				newLib.execute(query, oldInfo) # insert the old information into the new library
				i += 1

			if (verbose):
				print("After: ")
				newLib.execute("SELECT name, uuid from RKVersion WHERE uuid=?", (oldInfo[1],)) 
				print(newLib.fetchone())
				print("")

		oldInfo = oldLib.fetchone()

	print("")
	print(str(i) + " matches were found between the old and new library, where the new library names were also empty. There, titles were copied from the old library to the new.")

def copyFromFileNames(newLibConn, verbose):
	"""Receives a connection to a library. Sets titles for all the images in the library based on their file names."""
	newLibGet = newLibConn.cursor()
	newLibIns = newLibConn.cursor()

	newLibGet.execute("SELECT fileName, uuid FROM RKVersion WHERE name IS NULL")

	info = newLibGet.fetchone()
	i = 0

	while (info):
		if (verbose):
			print("Before:")
			newLibIns.execute("SELECT name, fileName, uuid FROM RKVersion WHERE uuid=?", (info[1],))
			print(newLibIns.fetchone())

		# 9138 ska andras

		name = removeExtension(info[0])
		infoToInsert = (name, info[1])

		query = "UPDATE RKVersion SET name=? WHERE uuid=?"
		newLibIns.execute(query, infoToInsert)

		i += 1

		if (verbose):
			print("After: ")
			newLibIns.execute("SELECT name, fileName, uuid FROM RKVersion WHERE uuid=?", (info[1],))
			print(newLibIns.fetchone())
			print("")

		info = newLibGet.fetchone()

	print("")
	print(str(i) + " titles were set in the new library based on the file names.")


if __name__ == "__main__":
	initialInfo = ("This script lets you choose an old iPhoto library and a new Photos library.\n"
		"The script tries to find image versions with the same UUID in the libraries and copies over the image titles from the old to the new library.\n"
		"The script then sets the remaining image titles in the new library based on the file names.\n"
		"The script only copies over titles to images that currently has no titles in the new library.\n"
		"\n"
		"ALWAYS have several backups of any important files. Make especially sure to back up both photo libraries before running this script.\n"
		"The author of this script takes no responsibility for any damage on any files or for any of the actions of this script.\n"
		"\n"
		"To continue, type \"y\" and press return or enter.\n"
	)

	if (raw_input(initialInfo) == "y"):
		oldLibPath = askForLibPath("OLD")
		newLibPath = askForLibPath("NEW")

		# oldLibPath = "libraryWithTitles/Library.apdb"
		# newLibPath = "libraryWithoutTitles/Library.apdb"

		# oldLibPath, newLibPath = backupFiles([oldLibPath, newLibPath])

		oldLibConn = getConnection(oldLibPath)
		newLibConn = getConnection(newLibPath)

		verbose = False

		checkTitles(oldLibConn, "OLD", "")
		if (raw_input("Copy titles from the old library to the new? (y) ") == "y"):
			copyTitles(oldLibConn, newLibConn, verbose)

		checkTitles(newLibConn, "NEW", "NULL")
		if (raw_input("Create the remaining titles in the new library based on the file names? (y) ") == "y"):
			copyFromFileNames(newLibConn, verbose)

		checkTitles(newLibConn, "NEW", "NULL")
		print("")

		if (raw_input("Save changes? (y)") == "y"):
			newLibConn.commit()
			newLibConn.close()
		else:
			newLibConn.rollback()
			print("All changes were discarded.")
			checkTitles(newLibConn, "NEW", "NULL")
			newLibConn.close()
