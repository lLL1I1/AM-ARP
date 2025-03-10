## Object Identification Rules

### Core Rules for Extracting Objects (Actors/Classes)
| Rule Name                      | Trigger Condition                                                                 | Action                                                                 | Example                                  | Related Terms/Structures          |
|--------------------------------|-----------------------------------------------------------------------------------|-----------------------------------------------------------------------|-----------------------------------------|-----------------------------------|
| ​**P1 (Sender Identification)**​ | A sentence contains a ​**subject (noun)**.                                        | Extract the subject noun as the message sender.                       | "User enters password" → Sender=User    | Subject (noun), Verb              |
| ​**P1 Additional Condition**​    | A sentence lacks a subject (noun).                                               | Discard the sentence.                                                 | "Validate password" → Discarded         | -                                 |
| ​**P2 (Primary Actor)**​         | The first ​**subject directly linked to the root verb**​ (hierarchy level 1).      | Mark this subject as the system's primary actor.                      | "User logs in" → Primary Actor=User     | Subject (noun), Verb, Hierarchy   |
| ​**P3 (Receiver Judgment)**​     | The ​**object (noun)**​ exists in the identified actors set.                       | If yes → Mark as receiver; If no → Treat as message content.          | "ATM verifies password" → Receiver=ATM | Object (noun), Actor Set          |


## Example

### Input Requirements
1. "The user submits an order to the system."
2. "The system validates the payment details."

### Object Identification
| Step | Rule Applied       | Result                          |
|------|--------------------|---------------------------------|
| 1    | P1 (Sender)        | Sender=User (Subject="user")    |
| 2    | P2 (Primary Actor) | Primary Actor=User              |
| 3    | P3 (Receiver)      | Receiver=System (Object="system") |
| 4    | P1 (Sender)        | Sender=System (Subject="system") |