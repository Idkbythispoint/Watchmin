# Technical Debt Registry

This file tracks technical debt in the Watchmin project according to the requirements specified in AGENTS.md.

## Open Technical Debt

```
ID: DEBT-2025-001
Title: Plain text API key storage vulnerability
Date: 2025-01-23
Found by: code-analysis-agent
Source: legacy
Description: OpenAI API keys are stored in plain text in openai.key file without encryption. Keys are also cached in memory and potentially logged.
Impact: Security vulnerability - API keys can be easily extracted from filesystem or memory dumps, leading to unauthorized API usage and potential billing fraud.
Root cause: Initial rapid development focused on functionality over security best practices.
Severity: Large
Estimated Cost (USD): $25,000
Confidence: High
Proposed Fix: Implement secure key storage using system keyring, encrypt stored keys, add key rotation support, audit logging for key access, and environment variable validation.
Owner: security-team
Status: open
Related: apihandlers/OAIKeys.py lines 19-27, 36-37
```

```
ID: DEBT-2025-002
Title: Broad exception handling masking errors
Date: 2025-01-23
Found by: code-analysis-agent
Source: legacy
Description: Multiple locations use broad except Exception clauses that catch and mask all errors without proper logging or specific handling. This makes debugging and error recovery difficult.
Impact: Reduced observability, harder debugging, potential for silent failures, and degraded error recovery capabilities.
Root cause: Defensive programming approach without proper error handling strategy.
Severity: Medium
Estimated Cost (USD): $8,500
Confidence: Medium
Proposed Fix: Replace broad exception handlers with specific exception types, add structured logging, implement proper error recovery strategies, and add error telemetry.
Owner: platform-team
Status: open
Related: watchers/base_watcher.py lines 150-153, watchers/fixers/tools_handler.py lines 44-50, 110-116, apihandlers/OAIKeys.py lines 39-42
```

```
ID: DEBT-2025-003
Title: Inconsistent configuration management
Date: 2025-01-23
Found by: code-analysis-agent
Source: legacy
Description: Configuration is handled through multiple mechanisms: JSON files, environment variables, hardcoded defaults, and class-level defaults. No validation or schema enforcement.
Impact: Configuration drift, inconsistent behavior across environments, difficult troubleshooting, and potential runtime errors from invalid config values.
Root cause: Organic growth of configuration needs without architectural planning.
Severity: Medium
Estimated Cost (USD): $12,000
Confidence: Medium
Proposed Fix: Implement unified configuration schema with validation, standardize config loading priority, add configuration validation at startup, and create configuration documentation.
Owner: platform-team
Status: open
Related: internal/confighandler.py, config.cfg, main.py lines 10-26
```

```
ID: DEBT-2025-004
Title: Naive error detection using string matching
Date: 2025-01-23
Found by: code-analysis-agent
Source: legacy
Description: Error detection relies on simple string matching for keywords like error, exception, traceback in lowercase. This approach has high false positive/negative rates.
Impact: Missed critical errors, false alarms triggering unnecessary repairs, and inefficient use of LLM API calls leading to increased costs.
Root cause: MVP implementation focused on basic functionality.
Severity: Medium
Estimated Cost (USD): $15,000
Confidence: High
Proposed Fix: Implement structured log parsing, pattern recognition using regex or ML, context-aware error classification, and configurable detection rules.
Owner: ml-team
Status: open
Related: watchers/base_watcher.py lines 198-203
```

```
ID: DEBT-2025-005
Title: Race conditions in temporary file management
Date: 2025-01-23
Found by: code-analysis-agent
Source: legacy
Description: Temporary Python files are created with hardcoded names without proper cleanup, leading to race conditions when multiple processes execute code simultaneously.
Impact: File conflicts between concurrent executions, potential security issues from leftover temp files, and execution failures in multi-user environments.
Root cause: Simple implementation without considering concurrent usage scenarios.
Severity: Small
Estimated Cost (USD): $1,500
Confidence: High
Proposed Fix: Use Python's tempfile module for atomic temporary file creation, implement proper cleanup in finally blocks, and add unique naming based on process/thread IDs.
Owner: platform-team
Status: open
Related: watchers/fixers/tools_handler.py lines 65-123
```

```
ID: DEBT-2025-006
Title: Thread safety issues in process output buffers
Date: 2025-01-23
Found by: code-analysis-agent
Source: legacy
Description: Global process_output_buffers dictionary and instance output_buffer deques are accessed by multiple threads without proper synchronization mechanisms.
Impact: Race conditions leading to data corruption, inconsistent log data, potential crashes in high-concurrency scenarios, and unreliable error detection.
Root cause: Single-threaded development approach extended to multi-threaded usage without proper synchronization design.
Severity: Medium
Estimated Cost (USD): $6,000
Confidence: Medium
Proposed Fix: Implement thread-safe collections using threading.Lock, use queue.Queue for thread-safe operations, add atomic operations for buffer management, and implement proper cleanup for dead processes.
Owner: platform-team
Status: open
Related: watchers/base_watcher.py lines 13-17, 195-196
```

```
ID: DEBT-2025-007
Title: Limited test coverage and missing mocks
Date: 2025-01-23
Found by: code-analysis-agent
Source: legacy
Description: Test infrastructure exists but lacks comprehensive coverage, especially for error scenarios. External dependencies like OpenAI API are not properly mocked, making tests unreliable and expensive.
Impact: Reduced confidence in deployments, expensive test runs due to real API calls, flaky tests dependent on external services, and difficulty reproducing bugs.
Root cause: Fast development prioritizing features over comprehensive testing infrastructure.
Severity: Medium
Estimated Cost (USD): $18,000
Confidence: Medium
Proposed Fix: Implement comprehensive mock framework for external dependencies, add unit tests for all core functionality, create integration test scenarios, and add automated test coverage reporting.
Owner: qa-team
Status: open
Related: tests/ directory, simple_watchmin_test.py, run_full_test.py
```

```
ID: DEBT-2025-008
Title: Hardcoded model names and API dependencies
Date: 2025-01-23
Found by: code-analysis-agent
Source: legacy
Description: Model names like o3-mini and gpt-4o-mini are hardcoded in configuration defaults. No fallback mechanism if models become unavailable or deprecated.
Impact: Service disruption when OpenAI deprecates models, vendor lock-in preventing easy switching to alternative LLM providers, and potential cost optimization missed due to inflexibility.
Root cause: Direct integration without abstraction layer for LLM providers.
Severity: Small
Estimated Cost (USD): $4,500
Confidence: High
Proposed Fix: Create LLM provider abstraction layer, implement model availability checking with fallbacks, add support for multiple providers (Anthropic, local models), and create model cost optimization strategies.
Owner: platform-team
Status: open
Related: internal/confighandler.py lines 160-161, 164
```

## Fixed Technical Debt

*No fixed technical debt entries yet*

## Deferred Technical Debt

*No deferred technical debt entries yet*

---

**Last Updated:** 2025-01-23  
**Total Estimated Cost:** $90,500  
**Next Review Date:** 2025-02-23