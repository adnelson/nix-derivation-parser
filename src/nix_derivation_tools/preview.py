"""Preview what will be built when building a derivation."""
import json
import sys

import requests
from servenix.client.sendnix import StoreObjectSender

from nix_derivation_tools.derivation import Derivation

def print_preview(paths, binary_cache=None, show_existing=False):
    """Print the result of a `preview_build` operation."""
    def print_set(action, s):
        if len(s) > 0:
            print("These derivation outputs {}:".format(action))
            for deriv, outs in s.items():
                print("  {} -> {}".format(deriv.path, ", ".join(outs)))
    needed, existing, on_server = preview_build(paths, binary_cache)
    print_set("need to be built", needed)
    print_set("will be fetched", on_server)
    if show_existing:
        print_set("already exist", existing)


def preview_build(paths, binary_cache=None):
    """Given some derivation paths, generate three sets:

    * Set of derivations which need to be built from scratch
    * Set of derivations which can be fetched from a binary cache
    * Set of derivations which already exist.

    Of course, the second set will be empty if no binary cache is given.
    """
    needed, on_server, existing = {}, {}, {}
    for path in paths:
        if "!" in path:
            # This syntax allows the user to specify particular
            # output(s) of a derivation to check, rather than just
            # the derivation itself.
            path, out = path.split("!")
            outputs = out.split(",")
        else:
            outputs = None
        deriv = Derivation.parse_derivation_file(path)
        deriv.needed_to_build(outputs=outputs,
                              derivs_needed=needed,
                              derivs_existing=existing)
    if len(needed) > 0 and binary_cache is not None:
        sender = StoreObjectSender(endpoint=binary_cache)
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
        url = "{}/query-paths".format(binary_cache)
        data = json.dumps(paths_to_ask)
        headers = {"Content-Type": "application/json"}
        auth = sender._get_auth()
        try:
            resp = requests.get(url, headers=headers, data=data, auth=auth)
            resp.raise_for_status()
            # Grab all of the paths which the server said it had.
            paths_on_server = (path for path, on_server in resp.json().items()
                               if on_server is True)
        except requests.HTTPError as err:
            print("Endpoint {} does not support the /query-paths route. "
                  "Querying paths individually.".format(binary_cache),
                  file=sys.stderr)
            if err.response.status_code != 404:
                raise
            paths_on_server = []
            for path in paths_to_ask:
                print("Querying for path {}".format(path), file=sys.stderr)
                prefix = path.split("-")[0]
                url = "{}/{}.narinfo".format(binary_cache, prefix)
                resp = requests.get(url, auth=auth)
                if resp.status_code == 200:
                    paths_on_server.append(path)
        for path in paths_on_server:
            deriv, out_name = path_mapping[path]
            # First, remove these from the `needed` set, because
            # we can fetch them from the server.
            needed[deriv].remove(out_name)
            if len(needed[deriv]) == 0:
                del needed[deriv]
            if deriv not in on_server:
                on_server[deriv] = set()
            on_server[deriv].add(out_name)
    return needed, on_server, existing