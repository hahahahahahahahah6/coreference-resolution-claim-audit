# Documentation claim auditor

An offline, deterministic, standard-library-only auditor for documentation about
mention linking. Requires Python 3.9 or later. No network, telemetry, model
execution, or file writes are performed by the auditor.

## Usage

```sh
python3 -m pip install .
coreference-resolution-claim-audit audit .
python3 -m coreference_resolution_claim_audit audit . --json
coreference-resolution-claim-audit audit . --verbose --ignore vendor/ --ignore examples/
coreference-resolution-claim-audit audit . --fail-on medium
coreference-resolution-claim-audit --version
```

The repository defaults to the current directory. Exit status is 0 when no
finding reaches the threshold, 2 when one does, and 1 for usage or IO errors.
The default threshold is high. JSON output is a list of findings; each has
an identifier, severity, path, verdict, message, and matched phrases.
Verbose decisions and scan scope go to standard error. Ignore prefixes are
repeatable and match repository-relative paths.

## Scope and rules

Scans the root README and Markdown files below docs. Test fixtures under a
tests directory receive medium severity. Python evidence is searched throughout
the repository, excluding version control, bytecode caches, virtual environments,
and build output. Each evidence route must be complete within one module.
Aliases and chained calls are recognized; local function or class definitions
shadow imported route names. Unparseable Python modules supply no evidence.

Fenced code blocks are excluded; inline code remains prose. Phrase matching is
case insensitive and uses exact substrings, without stemming or hyphen changes.
Denial spans are removed first. Longest-first matching with span blanking makes
each occurrence match once under its longest phrase. A positive claim without
evidence is high severity; a denial contradicted by evidence is high severity.
A denial without source evidence passes. Findings use these identifiers:

```text
documented-coreference-resolution-claim-false
documented-no-coreference-resolution-claim-false
```

## Differentiation

These neighboring tools check span finding, syntactic attachment, phrase
structure, polarity, and passage condensing, respectively:

```text
named-entity-recognition-claim-audit
dependency-parsing-claim-audit
constituency-parsing-claim-audit
sentiment-claim-audit
summarization-claim-audit
```

This auditor checks mention linking. Those other tasks alone do not supply
evidence for linked mentions.

## Limitations

Static patterns are not semantic judgement. Exact phrases miss restatements.
Generic method names on unrelated objects still count as evidence; for example:

```python
unrelated.resolve_coreference()
```

Predictor checkpoint identifiers containing the substring below are trusted on
name alone, without downloading or inspecting weights:

```text
coref
```

The following integrations count when pipe wiring and a chain attribute read
occur in one module. This shows use of the checked feature, not correctness
of the resulting mention clusters:

```text
coreferee: add_pipe("coreferee") plus ._.coref_chains
neuralcoref: add_to_pipe(...) plus ._.coref_clusters
```

Construction and prediction pairs are matched statically, without executing
control flow or checking runtime types. Comments, string literals, imports,
and references alone supply no evidence. No subprocess invocation supplies
evidence. This tool cannot assess model quality or whether a claim is true
for every input.

## Development

```sh
python3 -m unittest discover
python3 -m build
```

Distributed under the MIT license.
