from plantangenet.policy.identity import Identity
from plantangenet.policy.policy import Policy
from plantangenet.policy.statement import Statement
import uuid

# Permissive policy: allow all actions for all roles
allow_all_statement = Statement(
    id=str(uuid.uuid4()),
    role_ids=["player", "referee", "stats"],
    effect="allow",
    action=["*"],
    resource=["*"],
    condition={},
    delivery=None,
    cost=None,
    capabilities=None
)

policy = Policy(policies=[allow_all_statement])
identity = Identity(id="demo", nickname="demo", roles=[
                    "player", "referee", "stats"])
