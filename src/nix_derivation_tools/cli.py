"""CLI providing some useful derivation-related utilities."""

import argparse
import os
import sys

from nix_derivation_tools.derivation import Derivation
from nix_derivation_tools.derivation_diff import diff_derivations
from nix_derivation_tools.preview import print_preview

def get_args():
    """Parse command-line arguments."""
    p_root = argparse.ArgumentParser(description="Derivation Utilities")
    subparsers = p_root.add_subparsers(title="Command", dest="command")
    subparsers.required = True

    # 'show' command
    p_show = subparsers.add_parser("show", help="Show a derivation.")
    p_show.add_argument("derivation_path", help="Path to the derivation.")
    p_show.add_argument("--json", action="store_const", const="json",
                        dest="format", help="JSON format.")
    p_show.add_argument("--yaml", action="store_const", const="yaml",
                        dest="format", help="YAML format.")
    p_show.add_argument("-p", "--pretty", action="store_true", default=False,
                        help="Pretty-print.")
    p_show.add_argument("-A", "--attribute", help="Attribute to show.")
    p_show.add_argument("-e", "--env-var",
                        help="Environmant variable to show.")
    p_show.add_argument("-o", "--output",
                        help="Show the path of the given output.")
    p_show.set_defaults(format="string")

    # 'diff' command
    p_diff = subparsers.add_parser("diff", help="Diff two derivations.")
    p_diff.add_argument("first", help="Path to the first derivation.")
    p_diff.add_argument("second", help="Path to the second derivation.")

    # 'sdiff' command
    p_sdiff = subparsers.add_parser("sdiff", help="Diff smartly.")
    p_sdiff.add_argument("first", help="Path to the first derivation.")
    p_sdiff.add_argument("second", help="Path to the second derivation.")

    # 'preview' command
    p_preview = subparsers.add_parser("preview",
                                     help="Show paths needed to build a derivation.")
    p_preview.add_argument("derivation_paths", nargs="*",
                          help="Paths to derivations.")
    p_preview.add_argument("-c", "--binary-cache",
                           default=os.environ.get("NIX_REPO_HTTP"),
                           help="URL of a binary cache to query for paths.")
    p_preview.add_argument("--show-existing", action="store_true",
                           default=False, help="Show paths already existing.")
    return p_root.parse_args()


def main():
    """Main entry point."""
    args = get_args()
    if args.command == "show":
        path = args.derivation_path
        if "!" in path:
            path = path.split("!")[0]
        deriv = Derivation.parse_derivation_file(path)
        print(deriv.display(
            attribute=args.attribute,
            env_var=args.env_var,
            output=args.output,
            format=args.format,
            pretty=args.pretty))
    elif args.command == "diff":
        first = Derivation.parse_derivation_file(args.first)
        second = Derivation.parse_derivation_file(args.second)
        print(first.diff(second))
    elif args.command == "sdiff":
        first = Derivation.parse_derivation_file(args.first)
        second = Derivation.parse_derivation_file(args.second)
        diff = diff_derivations(first, second)
        if isinstance(diff, str):
            print(diff)
        else:
            description, left, right = diff
            print("{} differs:".format(description))
            print("Left:")
            print(left)
            print("Right:")
            print(right)
    elif args.command == "preview":
        if len(args.derivation_paths) > 0:
            paths = args.derivation_paths
        elif not sys.stdin.isatty():
            paths = (p.strip() for p in sys.stdin)
        else:
            sys.exit("No path arguments given")
        print_preview(paths, binary_cache=args.binary_cache,
                      show_existing=args.show_existing)
    else:
        sys.exit("Command {} not implemented".format(repr(args.command)))

if __name__ == "__main__":
    main()
