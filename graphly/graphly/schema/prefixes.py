from typing import Iterator, List
from graphly.schema.prefix import Prefix


class Prefixes:
    """
    A container class for managing multiple Prefix instances, allowing addition, removal, searching, and URI conversion.

    Attributes:
        prefix_list (List[Prefix]): A list storing the Prefix objects.

    Methods:
        __init__(prefix_list: List[Prefix] = []):
            Initialize the container with an optional list of Prefix objects.
        has(short: str) -> bool:
            Check if a Prefix with the given short prefix exists.
        shorten(uri: str) -> str:
            Shorten a full URI using the appropriate prefix in the container.
        lengthen(uri: str) -> str:
            Expand a shortened URI using the appropriate prefix in the container.
        add(prefix: Prefix) -> None:
            Add a new Prefix to the container.
        remove(short: str) -> None:
            Remove a new Prefix from the container.
        find(short: str) -> Prefix | None:
            Find a Prefix by its short prefix.
        __len__() -> int:
            Get the number of Prefix objects in the container.
        __iter__() -> Iterator[Prefix]:
            Return an iterator over the Prefix objects in the container.
    """

    prefix_list: List[Prefix]


    def __init__(self, prefix_list: List[Prefix] = []) -> None:
        """
        Initializes a Prefixes container holding a list of Prefix instances.

        Parameters:
            prefix_list (List[Prefix], optional): A list of Prefix objects to initialize the container. Defaults to an empty list.
        """
        self.prefix_list = prefix_list


    def has(self, short: str) -> bool:
        """
        Checks if a Prefix with the given short prefix exists in the container.

        Parameters:
            short (str): The short prefix to check for.

        Returns:
            bool: True if a Prefix with the specified short prefix exists, False otherwise.
        """
        for p in self.prefix_list:
            if p.short == short:
                return True
        return False


    def shorten(self, uri: str) -> str:
        """
        Shortens a full URI using the right prefix in the container.

        Parameters:
            uri (str): The full URI to be shortened.

        Returns:
            str: The URI with matching prefix replaced by its short forms.
        """
        to_return = uri
        for p in self.prefix_list:
            to_return = p.shorten(to_return)
        return to_return
    
    
    def lengthen(self, uri: str) -> str:
        """
        Expands a shortened URI using the right prefix in the container to its full forms.

        Parameters:
            uri (str): The shortened URI to be expanded.

        Returns:
            str: The full URI with short prefix replaced by its corresponding long URL.
        """
        to_return = uri
        for p in self.prefix_list:
            to_return = p.lengthen(to_return)
        return to_return


    def add(self, prefix: Prefix) -> None:
        """
        Adds a new Prefix instance to the container.

        Parameters:
            prefix (Prefix): The Prefix object to add to the list.
        """
        self.prefix_list.append(prefix)


    def remove(self, prefix: Prefix) -> None:
        """
        Remove a prefix from the prefix list by its attributes.

        Args:
            short (str): The short name of the prefix to remove.
            long (str): The long name of the prefix to remove.

        Returns:
            None
        """
        self.prefix_list = [p for p in self.prefix_list if p.short != prefix.short and p.long != prefix.long]


    def find(self, short: str) -> Prefix | None:
        """
        Finds a Prefix in the container by its short prefix.

        Parameters:
            short (str): The short prefix to search for.

        Returns:
            Prefix | None: The matching Prefix object, or None if no match is found.
        """
        for p in self.prefix_list:
            if p.short == short:
                return p
        return None
    
    def shorts(self) -> List[str]:
        return [p.short for p in self.prefix_list]


    def __len__(self) -> int:
        """
        Returns the number of Prefix instances in the container.

        Returns:
            int: The count of prefixes in the list.
        """
        return len(self.prefix_list)


    def __iter__(self) -> Iterator[Prefix]:
        """
        Returns an iterator over the Prefix instances in the container.

        Returns:
            Iterator[Prefix]: An iterator for traversing the list of Prefix objects.
        """
        return iter(self.prefix_list)