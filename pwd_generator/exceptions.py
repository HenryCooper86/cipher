class PasswordGeneratorError(Exception):
    pass


class EncryptionError(PasswordGeneratorError):
    pass


class ValidationError(PasswordGeneratorError):
    pass
