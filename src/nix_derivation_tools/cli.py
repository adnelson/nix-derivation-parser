"""CLI providing some useful derivation-related utilities."""

import argparse
import sys
import json
import requests

from servenix.client.sendnix import StoreObjectSender

from nix_derivation_tools.derivation import Derivation
from nix_derivation_tools.derivation_diff import diff_derivations

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
    p_preview.add_argument("derivation_paths", nargs="+",
                          help="Paths to derivations.")
    p_preview.add_argument("-c", "--binary-cache",
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
        derivs = []
        for path in args.derivation_paths:
            if "!" in path:
                # This syntax allows the user to specify particular
                # output(s) of a derivation to check, rather than just
                # the derivation itself.
                path, out = path.split("!")
                outputs = out.split(",")
            else:
                outputs = None
            derivs.append((Derivation.parse_derivation_file(path), outputs))
        needed, existing, on_server = {}, {}, {}
        for deriv, outputs in derivs:
            deriv.needed_to_build(outputs=outputs,
                                  derivs_needed=needed,
                                  derivs_existing=existing)
        if len(needed) > 0 and args.binary_cache is not None:
            sender = StoreObjectSender(endpoint=args.binary_cache)
            # Query the server for missing paths. Start by trying a
            # multi-query because it's faster; if the server doesn't
            # implement that behavior then try individual queries.
            paths_to_ask = []
            # Make a dictionary mapping paths back to the
            # derivations/outputs they came from.
            path_mapping = {}
            for deriv, outs in needed.items():
                for out in outs:
                    path = deriv.output_mapping[out]
                    paths_to_ask.append(path)
                    path_mapping[path] = (deriv, out)
            url = "{}/query-paths".format(args.binary_cache)
            data = json.dumps(paths_to_ask)
            headers = {"Content-Type": "application/json"}
            auth = sender._get_auth()
            resp = requests.get(url, headers=headers, data=data, auth=auth)
            resp.raise_for_status()
            for path, is_on_server in resp.json().items():
                if is_on_server is False:
                    continue
                deriv, out_name = path_mapping[path]
                # First, remove these from the `needed` set, because
                # we can fetch them from the server.
                needed[deriv].remove(out_name)
                if len(needed[deriv]) == 0:
                    del needed[deriv]
                if deriv not in on_server:
                    on_server[deriv] = set()
                on_server[deriv].add(out_name)
        def print_set(action, s):
            if len(s) > 0:
                print("These derivation outputs {}:".format(action))
                for deriv, outs in s.items():
                    print("  {} -> {}".format(deriv.path, ", ".join(outs)))
        print_set("need to be built", needed)
        print_set("will be fetched", on_server)
        if args.show_existing:
            print_set("already exist", existing)
    else:
        sys.exit("Command {} not implemented".format(repr(args.command)))

if __name__ == "__main__":
    main()
