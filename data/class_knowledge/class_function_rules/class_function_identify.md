# Method Identification Rules (M-Rules)

---

## Core Rules

| Rule ID    | Rule Name                     | Trigger Conditions                                                                 | Processing Logic                                                                 | Example                                                            | Notes                                                                 |
|------------|-------------------------------|------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|--------------------------------------------------------------------|-----------------------------------------------------------------------|
| **M-Rule1** | Lexical Verb Extraction       | Sentences with general-purpose verbs (e.g., see, want, create)                     | Map verbs to methods of the associated noun/class                              | "User **views** order" → `User.view()`                             | Targets descriptive actions (non-operational)                       |
| **M-Rule2** | Action Verb Extraction        | Sentences with operational verbs (e.g., calculate, start, validate)               | Map verbs to methods of the associated noun/class                              | "System **calculates** total" → `System.calculateTotal()`          | Focuses on domain-specific operations                              |
| **M-Rule3** | Verb-Object Phrase Mapping    | Verb + noun phrases without explicit subject                                       | Assign to the contextual subject class                                         | "**Submit order**" (context: User) → `User.submitOrder()`          | Requires dependency analysis for subject resolution                |
| **M-Rule4** | SVO Structure Mapping         | Full Subject-Verb-Object sentences                                                | Verb → method of subject class; object → parameter                             | "Customer **pays** invoice" → `Customer.pay(Invoice)`              | Maintains action directionality                                    |

---

## Usage Guidelines

### 1. Priority Order
```text
1. SVO structures (M-Rule4) > Verb-object phrases (M-Rule3) 
2. Action verbs (M-Rule2) > Lexical verbs (M-Rule1)