| 关系类型   | 识别特征                                                                 |
|--------|-------------------------------------------------------------------------|
| **继承** | 空心三角形箭头 + 实线（子类指向父类）<br>`extends`/`implements` 关键字       |
| **实现** | 空心三角形箭头 + 虚线（实现类指向接口）<br>`implements` 关键字                 |
| **关联** | 普通箭头 + 实线（导航方向）<br>代码层面包含对方类的成员变量                          |
| **聚合** | 空心菱形箭头 + 实线（整体指向部分）<br>`has-a` 语义                               |
| **组合** | 实心菱形箭头 + 实线（强所属关系）<br>成员对象生命周期与整体一致                        |
| **依赖** | 普通箭头 + 虚线<br>代码层面存在：方法参数/局部变量/静态调用等临时性使用关系                 |
| **特殊标记** | 多重性标识（`1..*`/`0..1`）<br>角色名称标注（例：`employer` ↔ `employee`）       |

# UML Relationship Identification Rules

---

## Relationship Attributes (RA-Rules)

| Rule Name         | Trigger Conditions                          | Processing Logic                                                                 | Example                                      | Notes                                                                 |
|-------------------|---------------------------------------------|---------------------------------------------------------------------------------|----------------------------------------------|-----------------------------------------------------------------------|
| ​**RA-Rule**​       | Adverbs indicating time, place, degree      | Map adverbs to relationship attributes                                          | "User pays ​**immediately**" → `time: immediately` | Applies to adverbial modifiers of actions                           |

---

## Association Rules (AS-Rules)

| Rule Name         | Trigger Conditions                          | Processing Logic                                                                 | Example                                      | Notes                                                                 |
|-------------------|---------------------------------------------|---------------------------------------------------------------------------------|----------------------------------------------|-----------------------------------------------------------------------|
| ​**AS-Rule 1**​     | Verb + preposition phrases (e.g., "has", "works for") | Extract noun pairs as classes; use phrase as association label                  | "User ​**works for**​ Department" → `User ⟷ Department (works for)` | Prioritizes explicit relationship phrases                           |
| ​**AS-Rule 2**​     | Compound verb phrases (e.g., "savings-checking")     | Split verbs and link related noun classes                                       | "Account supports ​**savings-checking**" → `Account ⟷ Account` | Common in domain-specific operations                                |
| ​**AS-Rule 3**​     | Subject-Verb-Object (SVO) structure          | Create bidirectional association between subject and object                     | "Customer ​**places**​ Order" → `Customer ⟷ Order (places)` | Defaults to bidirectional unless direction is explicit              |
| ​**AS-Rule 4**​     | Transitive verbs between two classes        | Create unidirectional association from subject to object                        | "System ​**records**​ Employer details" → `System → Employer (records)` | Uses verb directionality for arrow orientation                      |

---

## Multiplicity Rules (MR-Rules)

| Rule Name         | Trigger Conditions                          | Processing Logic                                                                 | Example                                      | Notes                                                                 |
|-------------------|---------------------------------------------|---------------------------------------------------------------------------------|----------------------------------------------|-----------------------------------------------------------------------|
| ​**MR-Rule**​       | Indefinite articles, plural nouns, numbers  | Infer multiplicity from quantifiers                                            | "Member borrows ​**books**" → `1..*`          | Plural nouns default to `*`; explicit numbers override (e.g., "2")   |

---

## Participation Type Rules (PT-Rules)

| Rule Name         | Trigger Conditions                          | Processing Logic                                                                 | Example                                      | Notes                                                                 |
|-------------------|---------------------------------------------|---------------------------------------------------------------------------------|----------------------------------------------|-----------------------------------------------------------------------|
| ​**PT-Rule 1**​     | Singular nouns with "each" or "only"        | Set cardinality to `1`                                                         | "**Each**​ department has ​**one**​ manager" → `1..1` | Explicit quantifiers take precedence                                 |
| ​**PT-Rule 2**​     | Modal verbs (e.g., "must", "may")           | Map "must" to mandatory (`1`), "may" to optional (`0..1`)                       | "User ​**must**​ log in" → `mandatory`         | Context-dependent interpretation                                     |

---

## Aggregation/Composition Rules (AG-Rules)

| Rule Name         | Trigger Conditions                          | Processing Logic                                                                 | Example                                      | Notes                                                                 |
|-------------------|---------------------------------------------|---------------------------------------------------------------------------------|----------------------------------------------|-----------------------------------------------------------------------|
| ​**AG-Rule 1**​     | "contains", "consists of" phrases           | Map to composition (strong ownership)                                           | "Library ​**contains**​ Books" → `Library ◆─ Books` | "Contains" implies lifecycle dependency                             |
| ​**AG-Rule 2**​     | "has", "holds" verbs                        | Map to aggregation (weak ownership)                                            | "Company ​**has**​ Departments" → `Company ─○ Departments` | Distinguish whole-part relationships                               |
| ​**AG-Rule 3**​     | "is part of" phrases                        | Reverse aggregation direction                                                   | "Chapter ​**is part of**​ Book" → `Book ◆─ Chapter` | Direction follows phrase structure                                 |
| ​**AG-Rule 4**​     | Collective nouns (e.g., "team", "group")     | Auto-map to aggregation                                                         | "**Team**​ includes Engineers" → `Team ─○ Engineers` | Requires domain knowledge validation                               |

---

## Generalization Rules (GE-Rules)

| Rule Name         | Trigger Conditions                          | Processing Logic                                                                 | Example                                      | Notes                                                                 |
|-------------------|---------------------------------------------|---------------------------------------------------------------------------------|----------------------------------------------|-----------------------------------------------------------------------|
| ​**GE-Rule 1**​     | "is a", "is a type of" phrases              | Create inheritance from subclass to superclass                                  | "Car ​**is a**​ Vehicle" → `Car → Vehicle`     | Simple inheritance                                                  |
| ​**GE-Rule 2**​     | "may be X or Y" constructs                  | Map to multiple inheritance/polymorphism                                       | "User ​**may be**​ Customer or Admin" → `Customer, Admin → User` | Handles OR conditions                                               |
| ​**GE-Rule 3**​     | "is a category of" phrases                 | Reverse inheritance direction                                                  | "GoldService ​**is a category of**​ Service" → `Service ← GoldService` | Phrase dictates hierarchy direction                                |
| ​**GE-Rule 4**​     | Multiple inheritance statements             | Create multi-parent inheritance                                                | "Frog ​**is Amphibian and Carnivore**" → `Frog → Amphibian, Carnivore` | Requires explicit conjunction                                     |

---

## Dependency Rules (DE-Rules)

| Rule Name         | Trigger Conditions                          | Processing Logic                                                                 | Example                                      | Notes                                                                 |
|-------------------|---------------------------------------------|---------------------------------------------------------------------------------|----------------------------------------------|-----------------------------------------------------------------------|
| ​**DE-Rule 1**​     | "depends on", "requires" verbs              | Map to transient dependency                                                    | "Payment ​**requires**​ Gateway" → `Payment ╌╌> Gateway` | Dashed arrow for temporary usage                                   |
| ​**DE-Rule 2**​     | "supports X but not Y" constructs           | Handle conditional/exclusion dependencies                                      | "OS ​**supports**​ Windows ​**but not**​ macOS" → `OS → Windows`, exclude macOS | Processes AND/NOT logic                                            |

---

## Recursive Relationship Rules (RR-Rules)

| Rule Name         | Trigger Conditions                          | Processing Logic                                                                 | Example                                      | Notes                                                                 |
|-------------------|---------------------------------------------|---------------------------------------------------------------------------------|----------------------------------------------|-----------------------------------------------------------------------|
| ​**RR-Rule**​       | Same class as subject and object           | Create self-association                                                        | "Employee ​**manages**​ Employee" → `Employee ⟷ Employee (manages)` | Verify semantic validity (e.g., hierarchy vs. data loop)           |

---

### Usage Guidelines  
1. ​**Priority Order**:  
   - Explicit phrases (e.g., AG-Rule 1) > Structural patterns (e.g., AS-Rule 3) > Lexical patterns (e.g., AS-Rule 4)  
   - Composition (◆─) over Aggregation (─○)  

2. ​**Conflict Resolution**:  
   ```text  
   - Directional rules override bidirectional defaults  
   - Quantifiers (e.g., "must", "each") override inferred multiplicity  