# ECE461_Team17_Phase1
Phase 1 code for the CLI package registry project

#### TODO 
- update this file

#### Reproducibility metric

###### How it works

The Reproducibility Metric evaluates whether example code snippets provided in a model’s README can be executed successfully in a clean, isolated environment. Each snippet is scored on a scale from 0.0 to 1.0. A score of 1.0 indicates that the code ran successfully without errors, demonstrating a fully reproducible example. A score of 0.5 is assigned when the snippet fails due to minor, fixable issues — for example, missing imports, undefined symbols, or missing files that clearly indicate an otherwise functional example. These cases suggest the author provided a nearly complete snippet that would work with small adjustments. A score of 0.0 is given when the snippet fails irrecoverably (e.g., syntax or indentation errors), contains unsafe operations, or produces runtime crashes that prevent reproducibility.

###### Security measures

To ensure the metric runs safely, each code snippet is executed within a temporary, sandboxed environment using strict controls. The system prohibits execution of unsafe operations such as file I/O, network access, subprocess calls, or use of eval and exec. All snippets are written to short-lived temporary directories that are automatically cleaned up after execution. Additionally, timeouts are enforced to prevent long-running or hanging processes, and only Python code is evaluated. These measures ensure that the reproducibility analysis cannot compromise the host environment or access external resources, while still providing accurate feedback on the quality and reliability of code examples.

#### Reviewedeness metric

###### How it works

The ReviewedenessMetric estimates what portion of a repository’s merged pull requests went through code review. It queries the GitHub API for closed PRs, filters for those that were merged, and then counts how many had review comments or assigned reviewers. The ratio of reviewed-to-total merged PRs becomes the metric value, clamped between 0 and 1.

###### Design rationale

We use merged PRs as a proxy for code introduction since they reflect actual code integrated into the main branch. Checking for review comments or requested reviewers provides a lightweight but practical signal of peer review activity without requiring commit-level diff analysis. Returning -1 for missing repos and caching latency helps keep results consistent with the project’s metric spec and performance monitoring design.