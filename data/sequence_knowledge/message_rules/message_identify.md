## Message Identification Rules

### Core Rules for Extracting Messages (Interactions)
| Rule Name                      | Trigger Condition                                                                 | Action                                                                 | Example                                  | Related Terms/Structures          |
|--------------------------------|-----------------------------------------------------------------------------------|-----------------------------------------------------------------------|-----------------------------------------|-----------------------------------|
| **M1 (Message Construction)**  | The **object (noun)** is not an actor and includes **modifiers or possessive structures**. | Combine the object with modifiers/possessives to form the full message. | "Enter user's password" → Message="Enter password" | Object (noun), Modifiers, Possessive |

---

## Additional Guidelines

### 1. ​**Hierarchy Handling**
- ​**Level 1 Structure**: Subjects/objects directly tied to the root verb (e.g., "User [verb] logs in").
- ​**Primary Actor**: The first level 1 subject is prioritized as the core system actor.

### 2. ​**Composite Message Handling**
- ​**Possessive Structures**: Use terms like "of" or apostrophes to link objects (e.g., "User's account" → Message="Account").
- ​**Modifiers**: Attach adverbs/adjectives to actions (e.g., "Quickly process" → Message="Process quickly").

### 3. ​**Workflow Steps**
1. ​**Parse Text**: Identify verbs, subjects, and objects.
2. ​**Identify Objects**: Apply P1-P3 to extract senders, receivers, and actors.
3. ​**Build Messages**: Use M1 to combine non-actor objects with modifiers.

---

## Example

### Input Requirements
1. "The user submits an order to the system."
2. "The system validates the payment details."


### Message Identification
| Step | Rule Applied       | Result                          |
|------|--------------------|---------------------------------|
| 1    | M1 (Message)       | Message="Submit order"          |
| 2    | M1 (Message)       | Message="Validate payment details" |


