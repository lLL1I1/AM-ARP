# Actor Identification Rules (AC-Rules)

| Rule ID    | Rule Name                      | Trigger Conditions                                                                 | Processing Logic                                                                 | Example                                                                 | Notes                                                                 |
|------------|--------------------------------|------------------------------------------------------------------------------------|----------------------------------------------------------------------------------|------------------------------------------------------------------------|-----------------------------------------------------------------------|
| AC-Rule 1  | Common Noun Subject Extraction | Sentence subject contains a common noun (`<NN>`)                                  | Extract the noun as a candidate actor                                             | `User<subj> submits order` → Actor: "User"                             | For basic noun identification                                         |
| AC-Rule 2  | Proper Noun External Actor     | Sentence subject contains a proper noun (`<NNP>`)                                 | Map to external system actors                                                    | `Alipay<subj> initiates request` → External Actor: "Alipay"         | Proper nouns typically represent external systems/organizations      |
| AC-Rule 3  | S-P/S-P-O Structure Mapping    | Sentence follows Subject-Predicate (S-P) or Subject-Predicate-Object (S-P-O) form | Directly extract syntactic subject as actor                                       | `User<subj> logs into system` → Actor: "User"                         | Requires dependency parsing results                                  |
| AC-Rule 4  | Pure Noun Phrase Mapping       | Subject is a pure noun phrase (noun + noun only)                                   | Map entire noun phrase as actor                                                   | `Customer Manager<subj> reviews application` → Actor: "Customer Manager" | Filters phrases with adjectives (e.g., "Premium User")              |
| AC-Rule 5  | Consecutive Noun Filter        | Last word of consecutive nouns not in exclusion list `[number, code, date...]`     | Retain as valid actor                                                             | `Company staff` → Valid; `User ID` → Filtered                        | Exclusion list can be domain-extended                                |
| AC-Rule 6  | Geo/Person Name Exclusion      | Subject is location name (`<LOC>`), person name (`<PER>`), etc.                    | Ignore                                                                            | `Beijing<subj>'s request` → Ignored                                  | Requires Named Entity Recognition (NER)                              |
| AC-Rule 7  | System Subject Exclusion        | Subject contains "system" or equivalent                                            | Ignore                                                                            | `Payment System<subj> generates bill` → Ignored                      | Prevents system itself from being considered as actor                |
| AC-Rule 8  | Action Initiator Validation    | Subject is semantic initiator of the action (verb analysis)                        | Only retain genuine action initiators                                              | `Order<subj> is canceled by user` → "Order" invalid, identify "User" | Requires Semantic Role Labeling (SRL)                                |

---

## Usage Notes
1. ​**Rule Priority**:
   - Exclusion rules (AC-Rule 5-7) > Extraction rules (AC-Rule 1-4)
   - AC-Rule 8 serves as final semantic validation layer

2. ​**Technical Dependencies**:
```text
- POS Tagging: <NN>/<NNP> tags from NLP tools
- Dependency Parsing: <subj> tags for syntactic roles
- NER: For AC-Rule 6 implementation
- SRL: For AC-Rule 8 validation