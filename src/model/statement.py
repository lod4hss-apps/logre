from .onto_entity import OntoEntity
from .onto_property import OntoProperty


class Statement:

    subject: OntoEntity
    predicate: OntoProperty
    object: OntoEntity

    def __init__(self, subject: OntoEntity, predicate: OntoProperty, object: OntoEntity):
        self.subject = subject
        self.predicate = predicate
        self.object = object


    def to_dict(self) -> dict:
        return { 
            **self.subject.to_dict(prefix='subject_'),
            **self.predicate.to_dict(prefix='predicate_'),
            **self.object.to_dict(prefix='object_'),
        }
    
    @staticmethod
    def from_dict(obj: dict) -> 'Statement':
        subject = OntoEntity.from_dict(obj, prefix='subject_')
        predicate = OntoProperty.from_dict(obj, prefix='predicate_')
        object = OntoEntity.from_dict(obj, prefix='object_')
        
        return Statement(subject, predicate, object)

