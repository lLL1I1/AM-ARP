# Attribute Identification Rules (A-Rules)

| Rule ID   | Rule Name                   | Trigger Conditions                                                                 | Processing Logic                                                                 | Example                                                                 | Notes                                                                 |
|-----------|-----------------------------|------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------|----------------------------------------------------------------------|
| A-Rule1   | Adjective-Modified Nouns    | Sentence contains nouns modified by adjectives                                    | Extract the nouns as attributes                                                | "Sales order items contain description, price, total" → description, price, total (Class: SalesOrderItem) | Focuses on explicit property listing                                |
| A-Rule2   | Is-Property-of Structure    | Phrases like "is-property-of" or "identified by"                                   | Extract the noun after the phrase as an attribute of the preceding class       | "Student is identified by student_id" → student_id (Class: Student)   | Used for explicit ownership declarations                            |
| A-Rule3   | Possessive Modifiers        | Nouns modified by 's or "of"                                                       | Extract the possessed noun as an attribute of the owner class                  | "Student's address" → address (Class: Student)                        | Handles genitive case constructs                                    |
| A-Rule4   | HasA Relationship           | Sentences with "has/have" verbs                                                    | Extract the noun after the verb as an attribute of the subject class            | "Librarian has name" → name (Class: Librarian)                         | Captures explicit ownership relationships                          |
| A-Rule5   | Pronominal Possession       | Nouns following possessive pronouns (e.g., "his/her/their")                       | Extract the noun after the pronoun as an attribute of the antecedent class      | "Candidate updates his details" → details (Class: Candidate)          | Relies on coreference resolution for class mapping                  |
| A-Rule6   | Consecutive Nouns           | Noun + noun sequences                                                             | Treat the last noun as an attribute of the preceding noun (as class)            | "Shoe size" → size (Class: Shoe)                                       | Filters compound terms not representing attributes                 |
| A-Rule7   | Underscore Notation         | Nouns joined by underscores                                                        | Split and map the second noun as an attribute of the first noun (as class)     | "Student_name" → name (Class: Student)                                | Common in database/document schemas                                 |
| A-Rule8   | Unique Identifier Concepts  | Nouns with uniqueness indicators ("unique", "ID", "code", "date")                 | Extract the noun as an attribute of the preceding class                        | "Order number is unique" → number (Class: Order)                      | Targets key identifiers in domain models                            |

---

## Usage Notes

1. ​**Rule Priority**:
   - Syntactic patterns (A-Rule2-4, A-Rule6-7) > Lexical patterns (A-Rule1, A-Rule5, A-Rule8)
   - A-Rule8 applies to both attribute extraction and datatype identification

2. ​**Technical Dependencies**:
```text
- POS Tagging: For adjective/noun detection (A-Rule1, A-Rule5)
- Dependency Parsing: To identify possessive constructs (A-Rule3) and HasA relationships (A-Rule4)
- Coreference Resolution: For A-Rule5's pronoun antecedent matching
- Domain Lexicons: Required for A-Rule8's uniqueness keywords