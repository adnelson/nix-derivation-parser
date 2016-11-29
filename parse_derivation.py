import argparse
import ast
import json
import re
from subprocess import check_output, PIPE, Popen
import sys


class Derivation(object):
    """A Python representation of a derivation."""
    def __init__(self, outputs, input_derivations, input_files, system,
                 builder, builder_args, environment):
        """Initializer.

        :param outputs: The outputs this derivation will produce. Keys are
            output names, and values are nix store paths.
        :type outputs: ``dict`` of ``str`` -> ``str``
        :param input_derivations: Derivations required to build the
            expression. Keys are derivation paths, and values are lists of
            output names that this derivation will use.
        :type input_derivations: ``dict`` of ``str`` -> ``list`` of ``str``
        :param input_files: Store paths that aren't derivations, which
            are needed to build the expression.
        :type input_files: ``list`` of ``str``
        :param system: Architecture and OS the derivation is built on.
        :type syste: ``str``
        :param builder: Store path of the derivation's builder executable.
        :type builder: ``str``
        :param builder_args: Command-line arguments for the builder.
        :type builder_args: ``list`` of ``str``
        :param environment: Environment variables to set for the builder.
        :type environment: ``dict`` of ``str`` to ``str``
        """
        self.outputs = outputs
        self.input_derivations = input_derivations
        self.input_files = input_files
        self.system = system
        self.builder = builder
        self.builder_args = builder_args
        self.environment = environment

    def input_paths(self):
        """Set of all store paths needed to build the derivation.

        :return: A set of paths.
        :rtype: ``set`` of ``str``
        """
        paths = set(self.input_files)
        for deriv_path, outputs in self.input_derivations.items():
            input_deriv = Derivation.parse_derivation_file(deriv_path)
            for output in outputs:
                paths.add(input_deriv.outputs[output])
        return paths

    @staticmethod
    def parse_derivation(derivation_string):
        """Parse a derivation string into a Derivation.

        :param derivation_string: A string representation of a
            derivation, as returned by a call to `nix-instantiate`.
        :type derivation_string: ``str``

        :return: The parsed Derivation object.
        :rtype: :py:class:`Derivation`
        """
        if derivation_string.startswith("Derive(["):
            # Then trim off the initial 'Derive(' and final ')'
            derivation_string = derivation_string[7:-1]
        # Parse the string as a python literal; this is a safe
        # operation because the derivation will not contain any
        # function calls, or anything which isn't a valid python literal.
        derivation_list =  ast.literal_eval(derivation_string)
        outputs = {name: path for name, path, _, _ in derivation_list[0]}
        input_derivations = dict(derivation_list[1])
        input_files = derivation_list[2]
        system = derivation_list[3]
        builder = derivation_list[4]
        builder_args = derivation_list[5]
        environment = dict(derivation_list[6])
        return Derivation(
            outputs=outputs, input_derivations=input_derivations,
            input_files=input_files, system=system, builder=builder,
            builder_args=builder_args, environment=environment)

    @staticmethod
    def parse_derivation_file(derivation_path):
        """Parse a derivation from a file path.

        :param derivation_path: Path to a file containing a string
            representation of a derivation.
        :type derivation_path: ``str``

        :return: The parsed Derivation object.
        :rtype: :py:class:`Derivation`
        """
        with open(derivation_path, "rb") as f:
            source = f.read()
            return Derivation.parse_derivation(source)

def get_args():
    """Build argument parser and parse args."""
    parser = argparse.ArgumentParser(prog="parse-deriv")
    subparsers = parser.add_subparsers(title="Command", dest="command")
    subparsers.required = True
    p_build = subparsers.add_parser("build",
                                    help="Build and parse derivations.")
    p_build.add_argument("--args", help="Arguments to nix-instantiate.")
    p_parse = subparsers.add_parser("parse",
                                    help="Parse derivation paths.")
    p_parse.add_argument("derivation_paths", nargs="+",
                         help="Paths to the derivation files.")
    for subparser in (p_build, p_parse):
        subparser.add_argument("-A", "--attribute", default=None,
                               help="Show this attribute of the derivations.")
    return parser.parse_args()

def main():
    """Main entry point. Parse a derivation and print its inputs."""
    args = get_args()
    if args.command == "build":
        proc = Popen("nix-instantiate {}".format(args.args),
                     shell=True, stderr=PIPE, stdout=PIPE)
        out, err = proc.communicate()
        if proc.returncode != 0:
            sys.exit(err)
        else:
            deriv_paths = out.decode("utf-8").strip().split("\n")
    elif args.command == "parse":
        deriv_paths = args.derivation_paths
    derivations = {}
    for deriv_path in deriv_paths:
        # nix-instantiate might produce a path with a !<output> at the
        # end, to indicate that it's a particular output of that
        # expression. For now just trim this off.
        match = re.match(r"^(.*?\.drv)!\w+$", deriv_path)
        if match is not None:
            deriv_path = match.group(1)
        if deriv_path not in derivations:
            with open(deriv_path) as f:
                source = f.read()
            derivations[deriv_path] = Derivation.parse_derivation(source)
    if len(derivations) == 1:
        derivation = list(derivations.values())[0]
        if args.attribute is not None:
            to_show = getattr(derivation, args.attribute)
        else:
            to_show = vars(derivation)
    else:
        if args.attribute is not None:
            to_show = {path: getattr(derivation, args.attribute)
                       for path, derivation in derivations.items()}
        else:
            to_show = {path: vars(derivation)
                       for path, derivation in derivations.items()}
    print(json.dumps(to_show, indent=2))

    # paths = set()
    # for d in derivations.values():
    #     paths = paths.union(d.input_paths())
    # for path in paths:
    #     print(path)

if __name__ == "__main__":
    main()