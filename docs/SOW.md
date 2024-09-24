# SOW

## Project Title
[CS457 Quiz Game](https://github.com/seredomi/cs457-project)

## Team
* Sereno Dominguez
* Max Sandoval

## Project Objective
Create an interactive game that allows students of CS 457 to answer questions from the Chapter Reviews.

## Scope
**Inclusions:**
* Game is hosted from a server that allows users to connect and play the game
* Players can connect by entering the server's IP and port
* Players can select which chapters they'd like to include in their game session
* Players can select how many questions they'd like to answer
* Players can optionally choose random question order
* Players are prompted with immediate results after each question
* Players are prompted with aggregated results at the end of each session

**Exclusions:**
* Original quiz questions that the team comes up with
* Any quiz question which involves pictures or other non-textual media
* Fuzzy answer interpretation. Players will answer in a multiple-choice fashion only

## Deliverables
* Questions in CSV file(s) or SQLite DB
* Working Python server script
* Working Python client script
* Automated testing suite
* Documentation
* Presentation of working program

## Timeline
**Key Milestones:**
| Milestone | Estimated Completion Date |
| -- | -- |
| Aggregate question data and store in CSV files or SQLite DB | Sep 30 |
| Server script reads question data and represents programmatically | Oct 10 |
| Server script accepts incoming connections, manages game sessions | Oct 20 |
| Client script connects to server, manages game sessions | Oct 30 |
| CLI for questions back and forth implemented on both sides | Nov 10 |
| CLI for entire game sessions implemented on both sides | Nov 20 |

**Task Breakdown:**
| Task | Est. Hrs | Status |
| -- | -- | -- |
| Aggregate question data (continuous) | 3 | Ch1=IP, Ch2=IP|
| Instantiate SQLite DB | 1 | |
| Populate DB with question data | 2 | |
| Server script reads and stores question data | 3 | |
| Server script accepts incoming connections | 2 | |
| Client script connects to server | 2 | |
| CLI implemented for a single question | 3 | |
| Results returned for single questions | 1 |  |
| CLI implemented for entire game sessions | 4 | |
| Results returned for entire game sessions | 2 | |
| Testing suite (continuous) | 4 | |

## Technical Requirements

**Hardware:**
* Server
  * Needs static IP, minimal bandwidth to service at least 10 simultaneous connections (text data only)
  * Needs minimal processsing power to compute game sessions for 10 simultaneous connections
* Client
    * Needs very minimal bandwidth and processing power to service its single session

**Software:**
* Server
  * Python 3.11^
    * sqlite, socket, threading, pytest, click libraries 
* Client
  * Python 3.11^
    * pytest, click libraries
  * GlobalProtect VPN if server is hosted on CSU Lab computer (it likely will be)

## Assumptions
* Consistent network connectivity on both client and server
* Access to GlobalProtect VPN from client
* Sufficient bandwidth, computing power, and RAM on both ends (very minimal)

## Roles and Responsibilities
| Name | Roles | Responsibilities |
| -- | -- | -- |
| Sereno | Developer, Tester | Write code, Implement tests |
| Max | Developer, Project Manager | Write code, Ensure deadlines are met |

## Communication Plan
* Use Discord for video chats and text updates
* Sprint planning meeting before each Sprint
* Sprint retrospective after each Sprint
* Regular video calls twice a week (coordinated on a case-by-case basis since there are only two of us and we are both remote)
* Additional meetings can be scheduled as needed when issues arise

## Additional Notes
N/A