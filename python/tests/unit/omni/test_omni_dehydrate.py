import pickle
import pytest
import json
from typing import Annotated
from plantangenet.omni.observable import Observable
from plantangenet.omni import Omni
from plantangenet.policy import Policy, Identity


class SampleOmni(Omni):
    value = Observable(field_type=int, default=0)
    count = Observable(field_type=int, default=42)


def test_omni_dehydrate_rehydrate():
    policy = Policy(logger=None, namespace="test")
    identity = Identity(id="user1", nickname="Test User",
                        metadata={}, roles=[])
    policy.add_identity(identity)
    omni = SampleOmni(value=0, count=42)
    omni._omni__session = identity
    omni._omni__policy = policy
    omni.value = 123
    omni.count = 99
    data = pickle.dumps(omni)
    omni2 = pickle.loads(data)
    assert omni2.value == 123
    assert omni2.count == 99
    assert getattr(omni2._omni__session, 'id', None) == "user1"
    _ = omni2.value
    _ = omni2.count


def test_structured_dehydration():
    policy = Policy(logger=None, namespace="test")
    identity = Identity(id="user1", nickname="Test User",
                        metadata={}, roles=[])
    policy.add_identity(identity)
    omni = SampleOmni(value=0, count=42)
    omni._omni__session = identity
    omni._omni__policy = policy
    data = omni.dict()
    omni2 = SampleOmni(**data)
    assert omni2.value == 0
    assert omni2.count == 42
