# Spec: Vector search


## Overview

## Depends on
- Step 9: Documents

## Routes

## Database changes

## Create table


## 12. Expected Behavior


## Files to change
- `app.py` 

## Files to create

## New dependencies
No new dependencies. 


## Rules for implementation
- use vector search for searching pdfs for some question
- inside of SideBar when searching for all answers from table `answers`, use vector search (faiss index),  which satisfy selected question, treat  `clicks_to_Fixed` for them equal 0

## Definition of done
