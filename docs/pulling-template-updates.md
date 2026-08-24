# Pulling later template updates

Scaffolding is a one-time copy, not a live link. When `mloda-plugin-template`
gains a fix you want (a new CI check, a workflow correction, a doc improvement),
there is no automated job that delivers it. Pulling it in is a deliberate,
manual step, described here.

This is intentional: an automated sync would overwrite the renames and edits
that made the scaffold *yours*.

## Add the template as a remote

Once per clone:

```bash
git remote add template https://github.com/mloda-ai/mloda-plugin-template.git
git fetch template
```

`template` is now a normal remote. Nothing is applied yet.

## Find what you are missing

List template commits since you scaffolded, newest last:

```bash
git log --oneline --reverse template/main
```

Apply them oldest-first — a later commit often assumes an earlier one.

## Cherry-pick

```bash
git cherry-pick <sha>
```

Expect conflicts. Scaffolding rewrote files that template commits also touch,
so even a small update can need a decision from you. The two cases below are
the ones you will actually hit.

### Conflicts in `pyproject.toml`

This is the common one, and it happens even for commits that never touch your
package directory. `customize.sh` rewrote `name`, `description` and `authors`,
so any template commit editing a nearby line conflicts against your values.

Picking up a dependency cap looks like this:

```
<<<<<<< HEAD
authors = [{ name = "A", email = "a@b.c" }]
dependencies = ["mloda>=0.10.0", "mloda-testing>=0.3.2"]
=======
authors = [{ name = "Your Name placeholder", email = "placeholder@placeholder.com" }]
# mloda capped below 0.11.0 until the upgrade is evaluated.
dependencies = ["mloda>=0.10.0,<0.11.0", "mloda-testing>=0.3.2"]
>>>>>>> (chore(deps): cap mloda below 0.11.0)
```

The rule is the same every time: **keep your identity fields, take the
template's substantive change.** Here that means your `authors` line and the
template's capped `dependencies` line.

### Conflicts inside your renamed package directory

A template commit touching `placeholder/` does *not* usually reintroduce a
`placeholder/` directory in your repo. Git's rename detection maps
`placeholder/...` onto your renamed package, and the conflict lands inside the
correct file. The marker shows the mapping on both sides:

```
<<<<<<< HEAD:acme/extenders/my_plugin/tests/test_my_extender.py
from acme.extenders.my_plugin import MyExtender
=======
from placeholder.extenders.my_plugin.my_extender import MyExtender
>>>>>>> (fix(customize): ...):placeholder/extenders/my_plugin/tests/test_my_extender.py
```

So what conflicts is the **import lines**, not the paths: `customize.sh`
rewrote `from placeholder.` to `from <your_package>.`, and the template commit
still says `placeholder`. Resolve by keeping your package name and taking the
template's change to the rest of the line.

Rename detection is a heuristic, not a guarantee. If a commit both moves a file
and rewrites it heavily, git may fall back to reintroducing the literal
`placeholder/` path. If you see `placeholder/` appear in `git status`, abort and
apply that commit by hand instead:

```bash
git cherry-pick --abort
```

## Confirm before moving on

```bash
tox
```

Run it after each cherry-pick rather than after all of them, so a failure points
at one commit.

Check that nothing reintroduced the template's placeholder strings:

```bash
git grep -n placeholder -- . ':!docs/'
```

The `tox` placeholder check enforces this for `pyproject.toml`, but a
hand-resolved conflict can leave `placeholder` elsewhere.
