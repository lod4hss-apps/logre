from enum import Enum
from graphly.schema import Model
from graphly.models import SHACL


class ModelFramework(str, Enum):
    """
    Enumeration of supported model frameworks.

    Attributes:
        SHACL (str): Represents the SHACL framework.
        NO_FRAMEWORK (str): Indicates that no framework is being used.
    """
    SHACL = 'SHACL'
    NO_FRAMEWORK = 'No Framework'


def get_model_framework(model_framework_name: str) -> Model:
    """
    Returns the class corresponding to the specified model framework name.

    Args:
        model_framework_name (str): Name of the model framework ('SHACL' or 'No Framework').

    Returns:
        Model: `SHACL` class if the name is 'SHACL', otherwise the generic `Model` class for 'No Framework'.

    Raises:
        ValueError: If the provided framework name does not match any known Model framework.
    """
    framework = ModelFramework(model_framework_name)

    if framework == ModelFramework.SHACL:
        return SHACL
    elif framework == ModelFramework.NO_FRAMEWORK:
        return Model