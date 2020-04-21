class AstroError(Exception):
    pass


class StructureError(AstroError):
    pass


class BuildError(AstroError):
    pass


class UploadError(AstroError):
    pass


class InvalidDistributionError(UploadError):
    pass


class InvalidMetaError(UploadError):
    pass


class GliaApiError(UploadError):
    pass


class MultipleMatchesError(AstroError):
    pass


def multiple_candidates_error(mod_part, candidates):
    return MultipleMatchesError(
        "Multiple matches found for '{}':".format(mod_part) + "\n" + "\n".join(candidates)
    )
