# Classification Rules for Functional and Non-Functional Requirements

## 1. Definition-Level Classification Rules

### 1.1 Functional Requirements
- ​**Core Definition**: Describes the specific behaviors or tasks the system must perform, often expressed as "The system shall..." or "The user can...".  
- ​**Key Characteristics**:  
  - Directly corresponds to executable operations for business goals (e.g., user login, file upload, data export);  
  - Can be visualized through use case diagrams or user stories (e.g., "Users can register an account via email").  

### 1.2 Non-Functional Requirements
- ​**Core Definition**: Specifies the quality attributes of the system when performing functions, often expressed as "The system shall operate under... conditions" or "Must meet... standards".  
- ​**Key Characteristics**:  
  - Focuses on system-wide properties such as performance, security, and maintainability;  
  - Often measured using quantifiable metrics (e.g., response time ≤ 2 seconds, availability ≥ 99.9%).  

---

## 2. Criteria for Differentiation and Examples

| ​**Criterion**           | ​**Functional Requirements**       | ​**Non-Functional Requirements** | ​**Example Comparison**                                                      |
|--------------------------|-----------------------------------|---------------------------------|-----------------------------------------------------------------------------|
| ​**Behavior Description** | Specifies the system's actions    | Describes conditions or quality of execution | Functional: Users can submit approval requests; Non-Functional: Average processing time ≤ 30 minutes |
| ​**Quantifiability**      | Typically not directly quantifiable | Must define measurable metrics  | Functional: The system supports file upload; Non-Functional: Concurrent uploads ≥ 1000 files/second |
| ​**Design Relevance**     | Directly related to user workflows | Related to system architecture and internal design | Functional: Generate monthly sales reports; Non-Functional: Code complexity ≤ 15 (module level) |
| ​**Scope of Impact**      | Implementation of individual features | System-wide properties across modules | Functional: Supports multi-language switching; Non-Functional: Interface loading delay ≤ 0.5 seconds |

---

## 3. Extended Classification Framework (FURPS+ Model)

Based on the Unified Process (UP) standard, non-functional requirements can be further categorized into:  
1. ​**Usability**: Ease of use, completeness of help documentation  
2. ​**Reliability**: Fault recovery time, fault tolerance  
3. ​**Performance**: Throughput, resource utilization  
4. ​**Supportability**: Maintainability, internationalization support  
5. ​**Other Constraints**: Legal compliance, hardware compatibility  

---

## 4. Common Misclassification Scenarios

- ​**Security Requirements**:  
  - Functional: Users must log in with two-factor authentication (specific action);  
  - Non-Functional: Encryption must comply with AES-256 standards (quality attribute).  
- ​**Interface Requirements**:  
  - Functional: The system must call a third-party payment API (behavior description);  
  - Non-Functional: Failed API calls must retry within 5 seconds (execution condition).  

---

By following these rules, functional and non-functional requirements can be systematically distinguished, ensuring comprehensive coverage of system characteristics during the requirements analysis phase. Specific examples include high-concurrency design for e-commerce systems or performance optimization for approval workflows in OA systems.