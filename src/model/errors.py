

class EndpointTechnologyNotSupported(Exception):
    def __init__(self, given: str) -> None:
        super().__init__(f"Endpoint technology \"{given}\" is not supported.")


class OntologyFrameworkNotSupported(Exception):
    def __init__(self, given: str) -> None:
        super().__init__(f"Ontology framework \"{given}\" is not supported.")

class OntologyFrameworkNotSupported(Exception):
    def __init__(self, given: str) -> None:
        super().__init__(f"Ontology framework \"{given}\" is not supported.")


class CantGetInfoOfBlankNode(Exception):
    def __init__(self) -> None:
        super().__init__(f"Can not get information from a blank node.")


class HTTPError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class NotExistingEndpoint(Exception):
    def __init__(self, endpoint_url: str) -> None:
        super().__init__(f"The endpoint <{endpoint_url}> does not exist in current configuration.")


class NotExistingDataSet(Exception):
    def __init__(self, data_set_name: str) -> None:
        super().__init__(f"The data_set named <{data_set_name}> does not exist in current configuration.")


class MalformedCSV(Exception):
    def __init__(self) -> None:
        super().__init__(f"CSV parsing went wrong, the file is probably malformed: the file format (column names) needs to be respected in order to import it.")
