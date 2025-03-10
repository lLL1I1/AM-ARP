# Class Identification Rules (C-Rules)

---

## Core Rules

| Rule ID    | Rule Name                          | Description                                                                 | Example                                                                 | Notes                                                                 |
|------------|------------------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------|-----------------------------------------------------------------------|
| ​**C-Rule1**​ | Extract Common & Proper Nouns     | Identify common nouns (e.g., objects/concepts) and proper nouns (e.g., systems) as candidate classes | "Customer" (common noun) and "ERP_System" (proper noun) → Classes: `Customer`, `ERP_System` | Uses NLP tools to detect noun-based terms                           |
| ​**C-Rule2**​ | Map SVO Structures                | Extract subject and object nouns in Subject-Verb-Object (SVO) sentences as classes | "User submits Order" → Classes: `User`, `Order`                        | Verbs (e.g., "submits") may map to methods or associations           |
| ​**C-Rule3**​ | Filter Prepositional Phrases       | Ignore nouns following prepositions (e.g., "of", "in") as standalone classes | "System records details ​**of**​ Candidate" → Classes: `System`, `Candidate` | Prepositional phrases modify attributes/methods, not independent classes |
| ​**C-Rule4**​ | Identify Inheritance Hierarchies  | Extract superclass-subclass relationships from "IsA" constructs             | "E_Bike ​**is a**​ Vehicle" → Classes: `E_Bike` (subclass), `Vehicle` (superclass) | Supports multi-level inheritance                                   |
| ​**O-Rule5**​ | Resolve Compound Nouns            | Treat the first noun in "Noun+Noun" phrases as a class, the second as an attribute/instance | "Car_Model" → Class: `Car` with attribute `model`                       | Handles nested noun structures                                      |

---

## Usage Guidelines

### 1. Priority Order
```text
1. Inheritance (C-Rule4) > SVO structures (C-Rule2) > Common nouns (C-Rule1)
2. Compound noun resolution (O-Rule5) overrides preposition filtering (C-Rule3)