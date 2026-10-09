# Evaluation

## Overview

AI Incident Commander is designed to investigate incidents using a combination of deterministic diagnostic tools and LLM-based reasoning.

Because the reasoning layer is probabilistic, correctness cannot be evaluated by checking whether the LLM produces exactly the same output on every run.

The evaluation strategy therefore focuses on whether an investigation reaches a useful and sufficiently supported result.

The MVP provides five deterministic scenarios that serve as the foundation for evaluation:

```text
1. database_pool_exhaustion
2. bad_deployment
3. payment_provider_degradation
4. traffic_spike
5. insufficient_evidence
```

Each scenario contains known diagnostic data and an expected investigation outcome.

The formal automated evaluation framework is intentionally deferred until after the MVP is published. The scenarios and evaluation criteria are defined now so that the future framework has a clear contract.


## Evaluation Philosophy

The system should not be evaluated solely by asking:

> Did the LLM guess the expected root cause?

That would encourage brittle behavior.

Instead, evaluation should consider:

```text 
Evidence
   ↓
Hypotheses
   ↓
Evaluation
   ↓
Investigation result
```

A good investigation should:

1. collect relevant evidence
2. avoid unsupported claims
3. generate plausible hypotheses
4. distinguish supported from inconclusive hypotheses
5. avoid treating missing evidence as proof
6. produce a useful result even when evidence is insufficient

This is especially important for the `insufficient_evidence` scenario.


## Evaluation Scenarios

### Scenario 1 — Database Connection Pool Exhaustion

#### Scenario identifier

```text 
database_pool_exhaustion
```

#### Investigation context

The service experiences database connection failures.

Expected diagnostic signals include:

- database connection timeout
- failed database connection acquisition
- elevated error rate
- recent deployment
- associated commit
- historical incident involving database connection pool exhaustion

#### Expected investigation behavior

The investigation should identify the database connectivity problem as the central signal.

A useful investigation should correlate:

```text  
database connection errors
        +
elevated error rate
        +
recent deployment
```

Historical information may provide additional supporting context.

#### Important constraint

The available evidence does not necessarily prove the exact mechanism responsible for the connection failure.

For example, the evidence may support:

> A recent deployment is associated with the incident.

without proving:

> The deployment reduced the database pool size.

Therefore, a hypothesis about the exact mechanism may legitimately be evaluated as `inconclusive`.

This distinction is part of the expected behavior.


### Scenario 2 — Bad Deployment

#### Scenario identifier

```text 
bad_deployment
```

#### Investigation context

The checkout service experiences a significant increase in errors following a recent deployment.

Expected signals include:

- checkout errors
- elevated error rate
- recent deployment
- associated commit
- historical incident with a related pattern

#### Expected investigation behavior

The investigation should connect:

```text
recent deployment
        +
associated commit
        +
error-rate increase
        +
checkout-related errors
```

A strong hypothesis should explain the relationship between these observations.

For example:

> The recent deployment introduced a defect in the checkout validation flow, causing the observed increase in errors.

The hypothesis should be supported by the deployment, commit, logs, and metrics when those observations are available.


### Scenario 3 — Payment Provider Degradation

#### Scenario identifier

```text 
payment_provider_degradation
```

#### Investigation context

The service experiences failures caused by an external payment provider.

Expected signals include:

- payment provider request timeout
- payment provider HTTP 503 responses
- elevated error rate
- historical incident involving elevated provider errors

There is no relevant recent deployment or commit.

#### Expected investigation behavior

The investigation should recognize the external dependency as the most relevant signal.

A strong result should correlate:

```text 
provider timeout
        +
provider HTTP 503
        +
elevated error rate
        +
historical provider incident
```

The investigation should not invent a recent deployment as the cause simply because deployments are available as a diagnostic tool.

This scenario therefore tests whether the reasoning layer can distinguish relevant evidence from irrelevant diagnostic dimensions.


### Scenario 4 — Traffic Spike

#### Scenario identifier

```text 
traffic_spike
```

#### Investigation context

The service is experiencing a significant increase in traffic accompanied by saturation symptoms.

Expected signals include:

- increasing request queue depth
- worker timeout
- increased request rate
- elevated error rate
- historical incident associated with traffic saturation

There is no relevant deployment or commit.

#### Expected investigation behavior

A useful investigation should correlate:

```text 
increased request rate
        +
queue growth
        +
worker timeout
        +
increased error rate
```

Historical information may reinforce the hypothesis.

The investigation should not require every possible signal to be collected.

Because tool selection is LLM-driven, a run that collects strong metric and historical evidence may still be considered useful even if it does not collect every available log.

The evaluation should therefore focus on **evidence sufficiency and relevance**, not exact tool-call sequences.


### Scenario 5 — Insufficient Evidence

#### Scenario identifier

```text 
insufficient_evidence
```

#### Investigation context

The service has:

- a generic internal error
- elevated error rate
- no deployments
- no commits
- no historical incidents

There is insufficient evidence to identify a specific root cause.

#### Expected investigation behavior

The investigation should avoid inventing a root cause.

A valid result is:

```text
evidence > 0
hypotheses = []
```

or, depending on the available evidence, hypotheses that are explicitly evaluated as inconclusive.

The critical requirement is:

> Lack of evidence must not be converted into unsupported certainty.

This scenario is particularly important because it tests whether the system can express uncertainty rather than always producing a plausible-sounding answer.


## Evaluation Dimensions

The future evaluation framework should measure several independent dimensions.

### 1. Root Cause Accuracy

Measures whether the investigation identifies the expected underlying problem.

For scenarios where the evidence supports a clear explanation:

```text 
correct root cause
incorrect root cause
no root cause
```

The metric should not require an exact string match.

Different wording can represent the same underlying explanation.

For example:

```text 
"checkout validation regression"
```

and:

```text
"recent checkout validation change introduced by the deployment"
```

may represent the same root cause.

Evaluation should therefore be semantic rather than purely textual when possible.


### 2. Evidence Relevance

Measures whether the collected evidence actually contributes to understanding the incident.

Relevant evidence:

```text
error_rate = 22.7%
recent deployment = deploy-456
commit = "Refactor checkout validation flow"
```

Irrelevant evidence:

```text 
unrelated historical incident
```

The evaluation should reward useful evidence rather than simply counting the number of tool calls.

More evidence is not necessarily better evidence.


### 3. Evidence Sufficiency

Measures whether the investigation collected enough information to support its hypotheses.

For example:

```text 
Hypothesis:
"The recent deployment introduced the checkout regression."

Evidence:
    deployment
    commit
    error-rate increase
    checkout errors
```

provides a stronger basis than:

```text 
Hypothesis:
"The recent deployment caused the incident."

Evidence:
    deployment exists
```

This dimension helps distinguish plausible reasoning from evidence-backed reasoning.


### 4. Hypothesis Quality

A good hypothesis should:

- be relevant to the incident
- explain observed evidence
- avoid inventing facts
- remain appropriately scoped
- distinguish observations from interpretations

The system should not reward highly specific hypotheses when the available evidence does not justify that specificity.

For example:

```text
Evidence:
"database connection timeout"

Bad hypothesis:
"The connection pool was reduced from 50 to 10."

Reason:
No evidence establishes those numbers.
```

A better hypothesis would be:

```text
"The recent deployment may have introduced a change
that contributed to database connection exhaustion."
```


### 5. Evaluation Correctness

The evaluation stage should correctly classify hypotheses as:

```text 
supported
contradicted
inconclusive
```

The classification must be grounded in the collected evidence.

For example:

```text 
Hypothesis:
"The payment provider is returning errors."

Evidence:
    provider HTTP 503
    provider timeout

Verdict:
    supported
```

Whereas:

```text
Hypothesis:
"The deployment reduced the database connection pool."

Evidence:
    recent deployment
    database timeout

Verdict:
    inconclusive
```

The evidence indicates temporal correlation but does not prove the specific implementation change.


### 6. Recommendation Correctness

A future version of the investigation result may contain explicit recommendations.

Examples:

```text 
Rollback deployment
Investigate connection pool configuration
Investigate external payment provider
Scale worker capacity
```

The evaluation framework should determine whether a recommendation is appropriate for the evidence.

This metric is currently defined but not part of the MVP result model.

The MVP does not yet persist a separate `Recommendation`.


### 7. Unsupported Claims

The evaluation should explicitly penalize claims that cannot be supported by collected evidence.

Examples include:

```text
"The deployment changed the database pool size to 10."
```

when no evidence contains that information.

Or:

```text
"The payment provider was healthy before the incident."
```

when no evidence establishes that fact.

Unsupported claims are particularly important because an incident investigation system must be trustworthy, not merely plausible.


## Tool Usage Evaluation

Tool selection should also be evaluated, but not by requiring one exact sequence.

A scenario may have several valid investigation strategies.

For example, for a deployment-related incident, these may all be useful:

```text
search_logs
query_metrics
get_recent_deployments
get_commit
```

or:

```text
search_logs
query_metrics
get_recent_deployments
search_historical_incidents
```

The evaluation should therefore ask:

> Did the selected tools provide enough relevant information to support the resulting investigation?

rather than:

> Did the model call exactly these four tools?

This is important because the tool-selection stage is probabilistic.


## Scenario Ground Truth

Each scenario should define deterministic ground truth.

Conceptually:

```text 
Scenario
├── identifier
├── expected_root_cause
├── required_evidence
├── acceptable_evidence
├── irrelevant_signals
└── expected_behavior
```

For example:

```text 
bad_deployment

expected_root_cause:
    checkout regression introduced by recent deployment

required evidence:
    deployment
    associated commit
    elevated error rate

acceptable evidence:
    relevant logs
    historical incident

irrelevant signals:
    unrelated dependency data
```

The `insufficient_evidence` scenario has a different type of ground truth:

```text
expected_root_cause:
    none

expected_behavior:
    do not assert a specific root cause
```

This distinction allows the evaluation system to test both:

```text
Can the system identify a cause?
```

and:

```text
Can the system correctly recognize when it cannot?
```


## Evaluation Should Be Scenario-Aware

The meaning of evidence depends on the scenario.

For example, `request_rate` is highly relevant to:

```text 
traffic_spike
```

but may be unavailable or irrelevant in:

```text
database_pool_exhaustion
```

Therefore, the evaluation framework should not define one global list of mandatory tool calls.

Instead, each scenario defines its own expectations.

This allows the same tool to have different relevance depending on the investigation context.


## Expected vs. Actual

A future evaluation run should conceptually compare:

```text 
Scenario Ground Truth
        │
        ▼
Expected Investigation
        │
        │ compare
        ▼
Actual Investigation Result
```

The comparison should examine:

```text
Root cause
Evidence
Hypotheses
Evaluations
Recommendations
Unsupported claims
```

The output should be structured enough to support regression testing.

For example:

```json 
{
  "scenario": "bad_deployment",
  "root_cause_accuracy": true,
  "evidence_relevance": 0.9,
  "hypothesis_quality": 0.9,
  "unsupported_claims": 0,
  "evaluation_correctness": true
}
```

The exact scoring implementation is intentionally left for the post-MVP evaluation phase.


## Deterministic Test Scenarios vs. LLM Evaluation

The project uses two complementary testing strategies.

### Deterministic tests

Used to verify application behavior such as:

- tool validation
- tool execution
- workflow routing
- persistence
- lifecycle transitions
- unavailable diagnostic data
- domain validation

These tests should produce deterministic pass/fail results.

### LLM evaluation

Used to assess behavior such as:

- usefulness of tool selection
- hypothesis quality
- evidence relevance
- root-cause accuracy
- unsupported claims

These results may vary between runs because the reasoning layer is probabilistic.

The two approaches should not be conflated.

```text
Software tests
    → "Does the system behave according to its contract?"

LLM evaluation
    → "How good is the investigation produced by the reasoning system?"
```


## Evaluation Boundaries for the MVP

The MVP currently establishes:

- five deterministic scenarios
- deterministic mock-platform data
- structured investigation results
- evidence/hypothesis/evaluation separation
- unsupported-claim constraints
- explicit insufficient-evidence behavior

The following are intentionally deferred:

- automated evaluation runner
- aggregate evaluation metrics
- semantic root-cause matching
- LLM-as-a-judge
- evaluation dashboards
- large scenario datasets
- statistical comparison between models
- prompt optimization based on evaluation scores

These capabilities belong to the post-MVP evaluation phase.


## Why Evaluation Is Designed This Way

The system is intended to demonstrate engineering discipline around AI systems rather than simply demonstrate that an LLM can produce an answer.

The key principle is:

> AI output should be evaluated against explicit expectations and evidence, not only judged by whether it sounds reasonable.

The deterministic scenarios make the system reproducible.

The structured investigation result makes outputs machine-evaluable.

The separation between evidence, hypotheses, and evaluations makes unsupported reasoning easier to detect.

The `insufficient_evidence` scenario ensures that successful behavior sometimes means **not reaching a conclusion**.


## Summary

The evaluation strategy is based on five deterministic scenarios:

```text 
database_pool_exhaustion
bad_deployment
payment_provider_degradation
traffic_spike
insufficient_evidence
```

The main evaluation dimensions are:

```text
Root cause accuracy
Evidence relevance
Evidence sufficiency
Hypothesis quality
Evaluation correctness
Recommendation correctness
Unsupported claims
```

Tool usage is evaluated based on the quality and sufficiency of collected evidence rather than exact tool-call sequences.

The MVP defines the scenarios and evaluation contract but intentionally defers the full automated evaluation framework.

This keeps the MVP focused while leaving a clear path toward systematic AI evaluation after publication.