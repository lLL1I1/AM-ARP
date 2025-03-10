# Use Case Identification Rules (UC-Rules)

---

## Core Rules

| Rule ID     | Rule Name                     | Trigger Conditions                                                                 | Processing Logic                                                                 | Example                                                                 | Notes                                                                 |
|-------------|-------------------------------|------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------|-----------------------------------------------------------------------|
| ​**UC-Rule1**​ | Core Action Extraction        | Sentences with intentional verbs (e.g., "want", "need") initiated by an actor     | Map verbs to actor-related use cases                                            | "User ​**wants**​ to log in" → Use Case: `Log In`                        | Validate actor-verb logical relationships                            |
| ​**UC-Rule2**​ | Transitive Action Extraction  | Action verbs requiring direct objects (e.g., "send", "buy")                       | Extract "verb + object" as complete use case                                     | "User ​**sends email**" → Use Case: `Send Email`                         | Filter non-functional objects (e.g., "send time" → ignore)         |
| ​**UC-Rule3**​ | Phrasal Action Extraction     | Verb + preposition/adverb combinations forming meaningful actions                 | Treat phrase as single use case                                                 | "User ​**logs into system**" → Use Case: `Log Into System`              | Exclude non-action phrases (e.g., "run quickly" → keep "run")       |
| ​**UC-Rule4**​ | Functional Action Extraction  | Verb followed by functional noun                                                   | Combine as use case name                                                        | "System ​**generates report**" → Use Case: `Generate Report`            | Filter non-functional nouns (e.g., "generate time" → ignore)        |
| ​**UC-Rule5**​ | Actor-Bound Use Case          | Actions initiated by identified actors (verbs or verb phrases)                   | Bind actions to the actor's use case list                                       | "Customer ​**places order**" → Use Case: `Place Order` (Actor: Customer) | Requires prior actor identification                                  |
| ​**UC-Rule6**​ | Cross-Actor Interaction       | Actions involving two identified actors/business entities                        | Create interaction use case between actors                                      | "User ​**pays invoice**" → Use Case: `Pay Invoice` (User ↔ Invoice)     | Verify objects as business entities (not attributes)                |
| ​**UC-Rule7**​ | Structural Verb Filter        | Verbs describing system structure (e.g., "contain", "include")                   | Ignore non-interactive verbs                                                   | "System ​**contains**​ validation module" → No use case generated        | Maintain exclusion list (e.g., "consist of", "comprise")           |

---

## Usage Guidelines

### 1. Priority Order
```text
1. Cross-actor interactions (UC-Rule6) > Functional actions (UC-Rule4) > Core actions (UC-Rule1)
2. Actor-bound rules (UC-Rule5) override generic extraction

### 2. Conflict Resolution

#### Ambiguous Actions  
```text
"Admin reviews user-submitted application" →  
  - UC-Rule5: "Admin reviews application" (correct mapping)  
  - False binding risk: "User submits application" (requires context analysis to reject)  