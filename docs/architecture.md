# Belay ecosystem architecture

Final topology decided 2026-07-23 (decision record: harness-engineering store,
`research/2026-07-23-factory-product-topology.md` and `docs/19`–`docs/25`).
Three diagrams: the repo ecosystem, the activation planes inside Belay, and
the flow-of-flows loop (how user-created flows become part of Belay).

## 1. The ecosystem — repos and how knowledge/artifacts move

```mermaid
flowchart TB
    subgraph STORE["harness-engineering (public knowledge store)"]
        practices["Practices 01-10<br/>taxonomy, research"]
        metaskills["Engineering skills:<br/>eval-engineer, skill-optimizer,<br/>harness-designer, harness-auditor"]
    end

    subgraph BELAY["belay (ONE public repo: product + machinery + full suite)"]
        harness["harness/<br/>skills, agents, scripts, schemas"]
        machinery["Meta plane:<br/>flow builder, eval authoring,<br/>skill optimization, token meter"]
        suite["Full eval suite:<br/>5 personas, Harbor tasks,<br/>verifiers, judge rubrics, CI"]
        docsdir["docs/: design history D1-D16,<br/>architecture, CONTRIBUTING"]
    end

    subgraph INSTANCES["Private user instances (the tesseracts)"]
        inst1["User A instance<br/>template + tailored flows + data"]
        inst2["User B instance<br/>(contributors are users too)"]
    end

    FACTORY["adhd-personal-finance-harness<br/>(old factory repo)"]

    STORE -- "pinned COPY of skills + assets<br/>(refreshed deliberately,<br/>never a runtime dependency)" --> BELAY
    STORE -. "same copy mechanism for<br/>every future harness repo" .-> OTHER["other harness repos"]
    FACTORY -- "one-time migration:<br/>5 personas + fixtures, persona-bot/judge,<br/>D1-D15, release tooling — then ARCHIVE" --> BELAY
    BELAY -- "Use this template / clone + push<br/>(NEVER GitHub fork - forks cannot be private)" --> INSTANCES
    BELAY -- "tagged releases + dist zip<br/>(sanitization gate at packaging)" --> INSTANCES
```

## 2. Inside Belay — the three activation planes

Same repo, three capability planes, **three different activation mechanisms**
(practices/05 §Activation planes). This is what makes shipping the machinery
safe for a user who "just wants to install and use."

```mermaid
flowchart LR
    subgraph USERQ["User intents"]
        fin["'reconcile my month'<br/>'should I buy this?'"]
        meta["'create a new workflow for X'<br/>'/extend'"]
    end

    subgraph DOMAIN["DOMAIN plane - triggers on user intent"]
        flows["Finance flows:<br/>/onboarding, /monthly-prep,<br/>/reconcile-month, /purchase-check,<br/>/welcome-back + tailored flows"]
    end

    subgraph GUARD["GUARDRAIL plane - WIRED, never triggered"]
        verify["Deterministic verifiers:<br/>validate_workspace, ledger_verify,<br/>reconciliation (exact Decimal math)"]
        judge["LLM judge vs rubric<br/>(shame-free checks)"]
    end

    subgraph METAP["META plane - explicit invocation or schedule ONLY"]
        builder["Flow builder<br/>(creates skill + evals together)"]
        evaleng["Eval authoring<br/>(Harbor tasks, verifier fixtures)"]
        skillopt["skill-optimizer<br/>(nightly, scheduled, gated)"]
    end

    fin -- "description triggering" --> flows
    meta -- "explicit only" --> METAP
    flows -- "each flow step CALLS its verifiers<br/>(wired in the flow definition)" --> GUARD
    builder -- "new flow ships with<br/>wired guardrails + its evals" --> flows
    skillopt -- "staged proposals,<br/>adopt only after suite green" --> flows

    ISOLATION["Trigger-isolation eval cases in the suite:<br/>finance queries NEVER fire the meta plane,<br/>meta queries NEVER launch finance flows"]
    ISOLATION -.- DOMAIN
    ISOLATION -.- METAP
```

## 3. The flow of flows — usage, feedback, contribution, release

Contributors are users: they experiment in their own instances, and what
proves out gets generalized into Belay through the gated path.

```mermaid
flowchart TB
    belaymain["belay main branch<br/>(contributors work here)"]
    release["Tagged release + dist zip<br/>gates: frozen anchor sub-suite +<br/>FRESH-SEED fixture regeneration +<br/>sanitization scan"]
    instance["Private instance<br/>template namespace (upgradable)<br/>+ local namespace (never touched)"]
    usage["Daily usage:<br/>flows run, guardrails verify,<br/>skill-optimizer refines nightly"]
    newflow["User requests new flow -><br/>meta plane builds it WITH evals,<br/>staged, user adopts"]
    feedback["Feedback:<br/>issues, suggested workflows,<br/>instance-born flows that proved out"]
    contrib["Contributor (also a user)<br/>generalizes the flow:<br/>de-personalize + ANONYMIZATION gate +<br/>component evals + trigger evals"]
    pr["Pull request to belay"]
    ci["PR CI gate:<br/>deterministic suite green +<br/>trigger-isolation cases green"]

    belaymain --> release
    release -- "install / upgrade<br/>(template namespace only)" --> instance
    instance --> usage
    usage --> newflow
    newflow --> usage
    usage -- "opt-in, personal data never" --> feedback
    feedback --> contrib
    contrib --> pr
    pr --> ci
    ci -- "green: merge" --> belaymain
    ci -- "red: fix or reject" --> contrib
```

## The rules that hold it together

1. **Flows trigger, guardrails wire, meta invokes** — a gate left to
   probabilistic skill-triggering is not a gate; every flow calls its
   verifiers as steps. Plane isolation is itself eval-tested.
2. **No flow without evals** — the old factory's iron rule #1, now a runtime
   law: the flow builder creates the flow's evals and wired guardrails at
   creation, in the instance exactly as in the repo.
3. **Instances are private template copies, never GitHub forks** — forks of
   public repos cannot be made private, and instances hold personal data.
4. **Two namespaces in every instance** — template-owned paths (upgrades may
   overwrite) vs local paths (upgrades never touch).
5. **Anonymization at the contribution edge** — instance-born content passes
   the sanitization mindset (previously the release gate) before it enters a
   PR; personal data never leaves the instance.
6. **Key-free by design** — verification and self-extension run on the user's
   Claude subscription alone (deterministic verifiers, in-session judging,
   mock/handoff optimization backends).
7. **The store feeds by copy** — harness-engineering knowledge and skills
   arrive as pinned snapshots, refreshed deliberately; no runtime dependency.
