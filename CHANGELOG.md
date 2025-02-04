# Changelog

All notable changes to this project will be documented in this file.

## v1.7.3 - Date 2025-02-04

Change list_graph query

## v1.7.2 - Date 2025-02-03

Allows to directly load a configuration if it has one present on disk ("logre-config.toml")

## v1.7.1 - Date 2025-01-31

Bug corrections

## v1.7.0 - Date 2025-01-31

Make all the endpoint configuration handled in toml files, that needs to be uploaded/downloaded on the GUI.
Deploy on Streamlit cloud

## v1.6.6 - Date 2025-01-27

Force usage of local pipenv in order to avoid conda lib to be accessed

## v1.6.5 - Date 2025-01-27

Add the option of "Technology" when setting an endpoint

## v1.6.4 - Date 2025-01-24

Update make file:
- Add verbose recipes
- Make python version easily changeable

## v1.6.3 - Date 2025-01-23

Make Credentials endpoint dependant

## v1.6.2 - Date 2025-01-23

Update prefixes

## v1.6.1 - Date 2025-01-23

Rename folders

## v1.6.0 - Date 2025-01-22

Import turtle file in dedicated graph capabilities
Add username and password management

## v1.5.2 - Date 2025-01-18

Better message when endpoint is not selected

## v1.5.1 - Date 2025-01-18

Delete triple
Delete entity

## v1.5.0 - Date 2025-01-17

Allow to create an entity
Allow to create a triple

## v1.4.0 - Date 2025-01-15

Rework Endpoint configuration page
Add the graph handling to the endpoint configuration page
Add endpoint selection in the menu
Add graph activation in the menu
Change queries so that they work only on selected graphs
Implement "global" prefixes, and replace in results

## v1.3.1 - Date 2025-01-14

Change the makefile so that it updates "alone", when running `make start`

## v1.3.0 - Date: 2025-01-13

Add the "entity card": display triples of an entity.
Also create the "find entity" form, to select an entity.

## v1.2.0 - Date: 2025-01-10

Add the possibility to save and chose among saved queries in the SPARQL editor

## v1.1.0 - Date: 2025-01-08

Add the possibility to save and chose among saved endpoints.
Persists on disk.

## v1.0.0 - Date: 2025-01-08

First release of the tool, with a simple, minimal SPARQL editor.

Set up of the installation process