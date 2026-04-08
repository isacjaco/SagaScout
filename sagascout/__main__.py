"""
SagaScout CLI entry-point.

Usage examples::

    sagascout scout analyze --matches matches.json
    sagascout archivist parse --data tree.json
    sagascout oracle research --query "Smith family" --languages en es
    sagascout diplomat draft --recipient '{"id":"r1","country":"US"}' --purpose initial_contact

Run ``sagascout --help`` or ``sagascout <command> --help`` for full usage.
"""

import argparse
import json
import sys


def _cmd_scout(args: argparse.Namespace) -> None:
    from sagascout.agents.scout import Scout

    scout = Scout()

    if args.sub == "analyze":
        if args.matches:
            with open(args.matches, encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list):
                data = {"matches": data}
        else:
            data = {"matches": []}
        result = scout.process(data)
        print(json.dumps(result, indent=2))

    elif args.sub == "import-ancestry":
        result = scout.import_ancestry_csv(args.file)
        print(json.dumps(result, indent=2))

    elif args.sub == "import-23andme":
        result = scout.import_23andme_csv(args.file)
        print(json.dumps(result, indent=2))


def _cmd_archivist(args: argparse.Namespace) -> None:
    from sagascout.agents.archivist import Archivist

    archivist = Archivist()

    if args.sub == "parse":
        with open(args.data, encoding="utf-8") as fh:
            data = json.load(fh)
        result = archivist.process({"action": "parse", "data": data})
        print(json.dumps(result, indent=2))

    elif args.sub == "parse-gedcom":
        result = archivist.parse_gedcom(args.file)
        print(json.dumps(result, indent=2))

    elif args.sub == "export-gedcom":
        archivist_loaded = archivist
        if args.input:
            from sagascout.persistence import load_agent_state
            archivist_loaded = load_agent_state(Archivist, args.input)
        result = archivist_loaded.export_gedcom(args.output)
        print(json.dumps(result, indent=2))

    elif args.sub == "query":
        if args.input:
            from sagascout.persistence import load_agent_state
            archivist = load_agent_state(Archivist, args.input)
        query_data = {"type": args.type, "person_id": args.person_id}
        result = archivist.process({"action": "query", "data": query_data})
        print(json.dumps(result, indent=2))


def _cmd_oracle(args: argparse.Namespace) -> None:
    from sagascout.agents.oracle import Oracle

    config = {}
    if getattr(args, "live", False):
        config["live_search"] = True
    if getattr(args, "translation_provider", None):
        config["translation_provider"] = args.translation_provider

    oracle = Oracle(config=config)

    if args.sub == "research":
        languages = args.languages or ["en"]
        countries = args.countries or []
        result = oracle.process({
            "action": "research",
            "query": args.query,
            "languages": languages,
            "countries": countries,
        })
        print(json.dumps(result, indent=2))

    elif args.sub == "translate":
        languages = args.languages or oracle.supported_languages
        result = oracle.process({
            "action": "translate",
            "query": args.query,
            "languages": languages,
        })
        print(json.dumps(result, indent=2))

    elif args.sub == "search-archives":
        countries = args.countries or []
        result = oracle.process({
            "action": "search_archives",
            "query": args.query,
            "countries": countries,
        })
        print(json.dumps(result, indent=2))


def _cmd_diplomat(args: argparse.Namespace) -> None:
    from sagascout.agents.diplomat import Diplomat

    diplomat = Diplomat()

    if args.sub == "draft":
        recipient = json.loads(args.recipient) if args.recipient else {}
        result = diplomat.process({
            "action": "draft",
            "recipient": recipient,
            "purpose": args.purpose or "initial_contact",
            "language": args.language or "en",
        })
        print(json.dumps(result, indent=2))

    elif args.sub == "analyze-culture":
        result = diplomat.process({
            "action": "analyze_culture",
            "country": args.country,
        })
        print(json.dumps(result, indent=2))


def build_parser() -> argparse.ArgumentParser:
    """Build and return the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="sagascout",
        description="SagaScout: Autonomous Lineage Intelligence CLI",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    # ---- scout ----
    scout_p = subparsers.add_parser("scout", help="DNA match analysis")
    scout_sub = scout_p.add_subparsers(dest="sub", metavar="SUBCOMMAND")
    analyze_p = scout_sub.add_parser("analyze", help="Analyze DNA matches")
    analyze_p.add_argument("--matches", metavar="FILE",
                           help="JSON file containing matches list")
    import_anc_p = scout_sub.add_parser("import-ancestry",
                                        help="Import AncestryDNA CSV")
    import_anc_p.add_argument("--file", required=True, metavar="FILE")
    import_23_p = scout_sub.add_parser("import-23andme",
                                       help="Import 23andMe CSV")
    import_23_p.add_argument("--file", required=True, metavar="FILE")

    # ---- archivist ----
    arch_p = subparsers.add_parser("archivist", help="Family tree operations")
    arch_sub = arch_p.add_subparsers(dest="sub", metavar="SUBCOMMAND")
    parse_p = arch_sub.add_parser("parse", help="Parse JSON tree data")
    parse_p.add_argument("--data", required=True, metavar="FILE")
    gedcom_p = arch_sub.add_parser("parse-gedcom", help="Parse GEDCOM file")
    gedcom_p.add_argument("--file", required=True, metavar="FILE")
    exp_ged_p = arch_sub.add_parser("export-gedcom", help="Export GEDCOM file")
    exp_ged_p.add_argument("--input", metavar="JSON_STATE_FILE",
                           help="Agent state JSON (optional)")
    exp_ged_p.add_argument("--output", required=True, metavar="FILE")
    query_p = arch_sub.add_parser("query", help="Query the family tree")
    query_p.add_argument("--type", required=True,
                         choices=["ancestors", "descendants", "siblings", "statistics"])
    query_p.add_argument("--person-id", dest="person_id", metavar="ID")
    query_p.add_argument("--input", metavar="JSON_STATE_FILE",
                         help="Agent state JSON (optional)")

    # ---- oracle ----
    oracle_p = subparsers.add_parser("oracle", help="Multilingual research")
    oracle_p.add_argument("--live", action="store_true",
                          help="Enable live HTTP searches")
    oracle_p.add_argument("--translation-provider", dest="translation_provider",
                          choices=["google"], help="Translation provider")
    oracle_sub = oracle_p.add_subparsers(dest="sub", metavar="SUBCOMMAND")
    research_p = oracle_sub.add_parser("research", help="Conduct research")
    research_p.add_argument("--query", required=True)
    research_p.add_argument("--languages", nargs="+")
    research_p.add_argument("--countries", nargs="+")
    translate_p = oracle_sub.add_parser("translate", help="Translate a query")
    translate_p.add_argument("--query", required=True)
    translate_p.add_argument("--languages", nargs="+")
    search_arch_p = oracle_sub.add_parser("search-archives",
                                          help="Search genealogy archives")
    search_arch_p.add_argument("--query", required=True)
    search_arch_p.add_argument("--countries", nargs="+")

    # ---- diplomat ----
    dipl_p = subparsers.add_parser("diplomat", help="Communication drafting")
    dipl_sub = dipl_p.add_subparsers(dest="sub", metavar="SUBCOMMAND")
    draft_p = dipl_sub.add_parser("draft", help="Draft outreach message")
    draft_p.add_argument("--recipient", metavar="JSON",
                         help='JSON string e.g. \'{"id":"r1","country":"US"}\'')
    draft_p.add_argument("--purpose",
                         choices=["initial_contact", "share_research",
                                  "request_information"])
    draft_p.add_argument("--language", metavar="LANG_CODE")
    culture_p = dipl_sub.add_parser("analyze-culture",
                                    help="Analyze cultural context")
    culture_p.add_argument("--country", required=True, metavar="ISO_CODE")

    return parser


def main() -> None:
    """Main CLI entry-point."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        "scout": _cmd_scout,
        "archivist": _cmd_archivist,
        "oracle": _cmd_oracle,
        "diplomat": _cmd_diplomat,
    }

    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    if not getattr(args, "sub", None):
        # Print subcommand help for the chosen command
        subparsers_actions = [
            a for a in parser._subparsers._group_actions  # type: ignore[union-attr]
            if hasattr(a, "_name_parser_map")
        ]
        for action in subparsers_actions:
            if args.command in action._name_parser_map:
                action._name_parser_map[args.command].print_help()
                break
        sys.exit(0)

    try:
        handler(args)
    except Exception as exc:  # pragma: no cover
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
