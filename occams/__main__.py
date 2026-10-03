"""``python -m occams`` — start, which today means: load the config or refuse.

Prints the refusal reasons, never the accepted values (S7: money stays out of
every record that could be published; a log line is such a record).
``--schema`` prints every required key with no values.
"""

from __future__ import annotations

import sys

from occams.config import ConfigRefused, load, schema


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--schema" in argv:
        print(schema())
        return 0
    if argv and argv[0] == "refusals":
        from occams.refusals import main as refusals_main

        return refusals_main(argv[1:])
    if argv and argv[0] == "whatif":
        from occams.whatif import main as whatif_main

        return whatif_main(argv[1:])
    if argv and argv[0] == "loop":
        from occams.loop import main as loop_main

        return loop_main(argv[1:])
    if argv and argv[0] == "ingest":
        from occams.ingest import main as ingest_main

        return ingest_main(argv[1:])
    if argv and argv[0] == "spread":
        from occams.spread import main as spread_main

        return spread_main(argv[1:])
    if argv and argv[0] == "site":
        from occams.console.site import main as site_main

        return site_main(argv[1:])
    if argv and argv[0] == "init":
        from occams.doctor import init_main

        return init_main(argv[1:])
    if argv and argv[0] == "doctor":
        from occams.doctor import doctor_main

        return doctor_main(argv[1:])
    if argv and argv[0] == "classifier":
        from occams.proposers.regime import main as classifier_main

        return classifier_main(argv[1:])
    if argv and argv[0] == "survey":
        from occams.survey.grid import main as survey_main

        return survey_main(argv[1:])
    if argv and argv[0] == "universe":
        from occams.universe import main as universe_main

        return universe_main(argv[1:])
    if argv and argv[0] == "calendar":
        from occams.calendar import main as calendar_main

        return calendar_main(argv[1:])
    if argv and argv[0] == "console":
        from occams.console import main as console_main

        return console_main(argv[1:])
    if argv and argv[0] == "programme":
        if len(argv) > 1 and argv[1] == "stop":
            from occams.stopping import main as stop_main

            return stop_main(argv[2:])
        from occams.console.programme import main as programme_main

        return programme_main(argv[1:])
    if argv and argv[0] == "register":
        from occams.register.heads import main as heads_main

        return heads_main(argv[1:])
    if argv and argv[0] == "reproduce":
        from occams.reproduce import main as reproduce_main

        return reproduce_main(argv[1:])
    if argv and argv[0] == "conclude":
        from occams.conclude import main as conclude_main

        return conclude_main(argv[1:])
    if argv and argv[0] == "question":
        from occams.question import main as question_main

        return question_main(argv[1:])
    path = argv[0] if argv else None
    try:
        cfg = load(path)
    except ConfigRefused as e:
        print("REFUSED to start.")
        for r in e.reasons:
            print(f"  - {r}")
        return 2
    runnable = sorted(ax.value for ax, a in cfg.alpha.axes.items() if a.runnable)
    print(f"config accepted from {cfg.path}: {len(runnable)} runnable axes {runnable}; "
          f"currency {cfg.capital.currency}; values not printed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
