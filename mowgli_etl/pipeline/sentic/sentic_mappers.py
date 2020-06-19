from typing import Optional, Union
from urllib.parse import quote

from mowgli_etl.model.concept_net_predicates import RELATED_TO
from mowgli_etl.model.edge import Edge
from mowgli_etl.model.node import Node
from mowgli_etl.pipeline.sentic.sentic_constants import (
    SENTIC_DATASOURCE_ID,
    SENTIC_NAMESPACE,
)


def sentic_id(id: str) -> str:
    return f"{SENTIC_NAMESPACE}:{quote(id)}"


def sentic_node(*, id: str, label: str = None, sentic_type: str) -> Node:
    if label is None:
        label = id
    return Node(
        datasource=SENTIC_DATASOURCE_ID,
        id=sentic_id(id),
        label=label,
        other={"sentic_type": sentic_type},
    )


def sentic_edge(
    *,
    subject: str,
    object_: str,
    weight: Optional[float] = None,
) -> Edge:

    return Edge(
        datasource=SENTIC_DATASOURCE_ID,
        subject=subject,
        object=object_,
        predicate=RELATED_TO,
        weight=weight,
    )
