"""(WIP) Diffing of derivations."""
from datadiff import diff

def diff_derivations(left, right):
    """Return a diff of one derivation with anright.

    Returns the first difference between them in this order:

    * Derivation name (not the full path, just the `name` attribute).
    * Output names
    * Input files (non-derivation)
    * Input derivations or outputs of those derivations
    * Build environment
    * Builder
    * Builder args
    * System
    """
    if left.name != right.name:
        return ("name", left.name, right.name)
    onames_l, onames_r = left.output_names, right.output_names
    if onames_l != onames_r:
        return ("output names", onames_l - onames_r, onames_r - onames_l)
    ifiles_l, ifiles_r = left.input_files, right.input_files
    if ifiles_l != ifiles_r:
        return ("input files", ifiles_l - ifiles_r, ifiles_r - ifiles_l)
    iderivs_l, iderivs_r = left.input_derivations, right.input_derivations
    if iderivs_l != iderivs_r:
        # First check the set of derivations used by each one.
        derivps_l, derivps_r = set(iderivs_l.keys()), set(iderivs_r.keys())
        if derivps_l != derivps_r:
            return ("input derivation paths", derivps_l - derivps_r,
                    derivps_r - derivps_l)
        else:
            # If there's no difference there, find the first input for
            # which the two derivations use different output(s).
            for i_deriv, outs in left.input_derivations.items():
                right_outs = right.input_derivations[i_deriv]
                outs, right_outs = set(outs), set(right_outs)
                if outs != right_outs:
                    return ("outputs of derivation {}".format(i_deriv),
                            outs - right_outs, right_outs - outs)
    if left.environment != right.environment:
        return diff(left.environment, right.environment)
    return "equal"
