# Sequence Diagram Message Sequence Rules

## 1. ​**Time Sequence Basics**​  
   - ​**Vertical direction**​ represents time flow (**top → bottom**).  
   - ​**Message numbering**​ uses hierarchical formats (e.g., `1`, `1.1`, `2`).  

---

## 2. ​**Concurrency Detection**​  
   - ​**Horizontally aligned messages**​ indicate parallel execution.  
   - ​**Overlapping activation bars**​ (rectangles) represent concurrent operations.  

---

## 3. ​**Combined Fragment Identification**​  
| Fragment Type   | Identification Features                                                                 | Example                              |  
|-----------------|-----------------------------------------------------------------------------------------|--------------------------------------|  
| ​**alt**​         | Dashed box with ​**conditional branches**​ (e.g., `[balance > 0]` / `else`).             | ![alt fragment](img/alt_example.png) |  
| ​**loop**​        | Box labeled `loop` + ​**iteration condition**​ (e.g., `loop 3 times`).                   | `loop while data_available`         |  
| ​**opt**​         | Single-condition box for ​**optional execution**.                                        | `[user_logged_in]`                  |  
| ​**par**​         | Horizontally divided regions indicating ​**parallel execution**.                        | ![par fragment](img/par_example.png) |  

---

## 4. ​**Timing Constraints**​  
   - ​**Time labels**: Use `{t ≤ 2s}` format to specify time bounds.  
   - ​**Strict ordering**: Marked with `strict` combined fragments.  
     ```  
     strict {  
       A -> B: Message 1  
       B -> C: Message 2  
     }  
     ```  

---

### Notes:  
1. ​**Time flow alignment**: Ensure all messages follow top-to-bottom chronological order unless explicitly marked for concurrency.  
2. ​**Fragment nesting**: Combined fragments (e.g., `alt`, `loop`) can be nested to represent complex logic.  
3. ​**Tool compatibility**: Most UML tools (e.g., PlantUML, Lucidchart) support these notations.  

---

Save this as `sequence_diagram_rules.md` for documentation or team guidelines. Adjust examples or syntax based on your tooling preferences.