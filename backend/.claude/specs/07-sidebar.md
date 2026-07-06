# Spec 07: Sidebar


## Overview

## Depends on
- Step 06: Answers


## Database changes


## 12. Expected Behavior


## Rules for implementation

- create an animated, closable right `SideBar` side navigation menu 
- put hamburger icon in NavBar to the right side
- inside of side bar implement autocomplete filter for questions
- keep question filter after selecting the question, and display bellow `Answer for question:` with question text
- create section `Answers` below the filter, without title
- on select question 
   -- select all answers from table `answers` which satisfy at least one word of selected question, use SOUNDEX function, treat  `clicks_to_Fixed` for them equal 0
   -- join answers from question assigned-answers
   -- order all answers by `clicks_to_Fixed` desc
   
   -- display one of the answers with two buttons `Fixed` and `Not Fixed`
   -- on click to `Not Fixed` show next `answer`, 
   -- on click on `Fixed`, if row exists in table `question_answers` increment `clicks_to_Fixed`, otherwise create a new row in table `question_answers` with `clicks_to_Fixed` equal to 1
   -- keep history of clicks in separate table `History`
   -- for answers use ` ↗` as text for link
   -- in SideBar for answers use ` ↗` as text for link, with no underscore
   -- in NavBar put links SignOut and Theme, as the dropdown,  bellow the user name
   - instead of simle autocomplete, download and implement, everywhere, autocomplete from `tom-select` js library, use `debunce` for fetching the result, Run `yarn add tom-select`



## Definition of done
