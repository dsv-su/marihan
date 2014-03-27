#! /usr/bin/env python
# -*- coding: utf-8 -*-

__author__    = 'Simon Jarbrant'
__copyright__ = 'Copyright 2014, Department of Computer and System Sciences, Stockholm University'

__maintainer__ = 'Simon Jarbrant'
__email__      = 'simon@dsv.su.se'
__version__    = '0.0.2a'

import sys, argparse, json, git
from git import *

projects     = ''
buildProject = ''
buildName    = ''
rootPath     = ''

def checkCircularDependencies( projectname, dependencies ):
	print 'checking dependencies for ' + projectname + '...'

	# add the current project to the dependencies
	if projectname not in dependencies:
		dependencies.append(projectname)
	else:
		print 'error: circular dependency found'
		sys.exit()

	# load the full project from the build-file so that we have its dependencies
	project = projects.get(projectname)

	# loop through this project's dependencies and check them
	if 'requires' in project:
		for dependency in project.get('requires'):
			if dependency in dependencies:
				print 'error: circular dependency found'
				sys.exit()
			else:
				# loop through this dependency's dependencies
				checkCircularDependencies( dependency, dependencies )

	return


def fetchModule( name, module ):
	global rootPath

	if 'repo' not in module:
		print 'error: module doesn\'t have the \'repo\' option set'
		sys.exit()

	# get the relative destination for the module
	clonePath = ''
	if rootPath != '':
		clonePath = rootPath + '/'

	# if the module has a path specified, use that
	if 'path' in module:
		clonePath += module.get('path') + '/'
	else:
		print 'warning: module ' + name + ' doesn\'t have a path specified'

	# add module name to clonePath
	clonePath += name

	# if there's a branch specified, use that - otherwise default to master
	branch = 'master'
	if 'branch' in module:
		branch = module.get('branch')

	repo = Repo.clone_from(module.get('repo'), clonePath, branch=branch)

	# if there's a tag specified, try to checkout that
	if 'tag' in module:
		repo.git.checkout('tags/' + module.get('tag'))

	return


def buildProject( project ):
	# build project requirements first
	if 'requires' in project:
		for dependency in project.get('requires'):
			print 'processing dependency: ' + dependency
			if dependency not in projects:
				print 'error: cannot find build declaration for project ' + dependency
				sys.exit()

			# build dependency
			buildProject( projects.get(dependency) )

	# now proceed with building project
	if 'modules' not in project:
		print 'warning: project has no modules, skipping'
	else:
		for name, module in project.get('modules').iteritems():
			fetchModule( name, module )

	return


def main():
	global projects, buildTarget, buildName, rootPath

	# parse cli arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('-m', '--make', help='Target build to make', required=True)
	args = parser.parse_args()

	# set build project to make
	buildName = args.make

	# open buildfile and parse contents
	buildFile = open('build.json', 'r')
	projects = json.load(buildFile)

	# only continue if we have a valid target
	if buildName not in projects:
		print 'error: unknown build target \'' + buildName + '\''
		sys.exit()

	# extract the buildtarget from the list of available projects
	buildTarget = projects.get(buildName)

	# check for circular dependencies
	checkCircularDependencies(buildName, [])

	# set install path
	if 'root' in buildTarget:
		rootPath = buildTarget.get('root')
	else:
		print 'warning: project has no root location specified, cloning in current dir'

	print 'ok, I\'m building project ' + buildName + ' now :)'

	# build target
	buildProject( buildTarget )
	print 'project ' + buildName + ' built'

main()