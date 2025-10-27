# ECE461_Team17_Phase1
Phase 1 code for the CLI package registry project

#### TODO 
- update this file

#### Reproducibility metric

###### How it works

The Reproducibility Metric evaluates whether example code snippets provided in a model’s README can be executed successfully in a clean, isolated environment. Each snippet is scored on a scale from 0.0 to 1.0. A score of 1.0 indicates that the code ran successfully without errors, demonstrating a fully reproducible example. A score of 0.5 is assigned when the snippet fails due to minor, fixable issues — for example, missing imports, undefined symbols, or missing files that clearly indicate an otherwise functional example. These cases suggest the author provided a nearly complete snippet that would work with small adjustments. A score of 0.0 is given when the snippet fails irrecoverably (e.g., syntax or indentation errors), contains unsafe operations, or produces runtime crashes that prevent reproducibility.

###### Security measures

To ensure the metric runs safely, each code snippet is executed within a temporary, sandboxed environment using strict controls. The system prohibits execution of unsafe operations such as file I/O, network access, subprocess calls, or use of eval and exec. All snippets are written to short-lived temporary directories that are automatically cleaned up after execution. Additionally, timeouts are enforced to prevent long-running or hanging processes, and only Python code is evaluated. These measures ensure that the reproducibility analysis cannot compromise the host environment or access external resources, while still providing accurate feedback on the quality and reliability of code examples.