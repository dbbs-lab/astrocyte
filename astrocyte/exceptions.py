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
