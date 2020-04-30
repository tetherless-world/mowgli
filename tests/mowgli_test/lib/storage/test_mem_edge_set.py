from mowgli.lib.cskg.edge import Edge
from mowgli.lib.storage.mem_edge_set import MemEdgeSet


def test_add(edge: Edge):
    MemEdgeSet().add(edge)


def test_get_extant(edge: Edge):
    edge_set = MemEdgeSet()
    edge_set.add(edge)
    assert edge_set.get(object_=edge.object, predicate=edge.predicate, subject=edge.subject) == edge


def test_get_nonextant(edge: Edge):
    assert MemEdgeSet().get(object_=edge.object, predicate=edge.predicate, subject=edge.subject) is None