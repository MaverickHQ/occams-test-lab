Decision: publish
Date: 2026-09-26
By: MaverickHQ

The publication decision under R7, recorded by the author after reviewing
the repository as it stands at this commit ("this is good, reviewed and
ready to set to publish"). What is published is the repository and its
pages as a static site: the lab, the record and the results, as
`README.md` states under *What is published here*; the market data, the
author's configuration and every credential stay out, by construction.

Before this record: the whole-tree publication scan reports zero
unresolved hits, with 308 kept by the author's recorded decisions in
`tools/publication-decisions.toml` (M15.3); `make site` renders every page
and document through the publication check, clean (M15.2); the standing
checks are green on the CI machine, the clean-machine job among them
(M15.4). The history is published with the tree and is unchanged: every
verdict stamps its commit.

What this record permits: the `pages` workflow, which reads the three
lines above and deploys nothing without them, and the repository's
visibility, which is the author's setting on GitHub and not this file's
to change. The lab's product is its refusals; nothing published here
places an order or recommends a number.

---

**Amendment, 2026-10-03** (appended; nothing above is edited). The decision
to publish stands. One sentence above is superseded: "The history is
published with the tree and is unchanged."

The author decided that the public repository carries no history from
before publication. Two early commits carried a private address in their
metadata, and the author's words were "I don't want my email public". Of
the ways to keep it private the author chose a snapshot — "a new branch
with no history", published as the public `main` — over rewriting those
commits. The public repository therefore begins at a single commit that
holds the lab's tree as it stood, and it was created fresh, so that it has
never contained the earlier commits.

What that changes, and what it does not. The full history stays whole in a
private repository, archived and read-only. The commit ids the task list
cites, and the ids stamped on verdicts as `engine_sha`, name commits in
that private history; a reader of the public repository cannot inspect
them. Nothing else moved: the three hash-chained Registers, the forty-six
decisions and the dated log are published as they were, and the Registers'
chains verify. From the snapshot on, history is never rewritten; a ruleset
refuses a force-push or a deletion on `main` and a moved release tag, for
anyone.

The pre-publication audit of 2026-09-27 listed three other things that
publishing exposes, none of them a credential: the venue's name and a
help-centre article number in dated evidence, and the donor's figures in a
test fixture. The author confirmed each as kept, under the decisions
already recorded in `tools/publication-decisions.toml`.

The repository was set public by the author on 2026-10-03, and the site was
deployed the same day.
