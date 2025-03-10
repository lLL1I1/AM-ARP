# Use Case Model Relationship Specification (Enhanced Edition)

---

## Core Relationship Types

### 1. Actor-Use Case Association Rules (UR Series)

| Relationship Type       | Rule ID   | Trigger Characteristics                                                                 | Visualization           | Example                    |
|-------------------------|-----------|-----------------------------------------------------------------------------------------|-------------------------|----------------------------|
| ​**Actor Association**   | UR-Rule1  | Subject-Predicate (S-P/S-P-O) structure where subject/object are actors                  | `Actor ↔ Use Case`      | `User ↔ Submit Order`      |
| ​**Directional Association** | UR-Rule2  | Contains directional prepositions ("from/to") followed by an actor                     | `Actor → Use Case`      | `System → Generate Report` |
| ​**Target Association**   | UR-Rule3  | Verb-Object + "to/for" + target actor structure                                         | `Initiator ↔ Use Case ↔ Receiver` | `User ↔ Send Notification ↔ Admin` |
| ​**Resource Association** | UR-Rule4  | Verb-Object + "from" + source actor structure                                           | `User ↔ Use Case ↔ Resource System` | `Customer ↔ Check Balance ↔ Bank System` |

---

### 2. Use Case Relationship Rules (CR Series)

| Relationship Type     | Rule ID   | Trigger Characteristics                  | Visualization            | Example                    |
|-----------------------|-----------|-----------------------------------------|--------------------------|----------------------------|
| ​**Include Relationship** | CR-Rule1  | "Must", "Requires verification" statements | `Use CaseA -->> Use CaseB` | `Place Order → Verify Payment` |
| ​**Extend Relationship** | CR-Rule2  | "If...then", "Special cases" conditional clauses | `Use CaseA ..>> Use CaseB` | `Modify Order → Upgrade Plan` |
| ​**Generalization Relationship** | CR-Rule3  | "Multiple types", "Special scenarios" classifications | `Use CaseA --|> Use CaseB` | `VIP Operation → Standard Operation` |

---

## Mandatory Relationship Type Constraints
```text
Identified relationships must belong to one of the following four categories:
1. Actor Association (UR Series)
2. Include Relationship (CR-Rule1)
3. Extend Relationship (CR-Rule2)
4. Generalization Relationship (CR-Rule3)

Creation of undefined relationship types is prohibited