from mowgli.lib.cskg.node import Node

try:
    from mowgli.lib.storage.persistent_node_id_set import PersistentNodeIdSet
except ImportError:
    PersistentNodeIdSet = None

if PersistentNodeIdSet is not None:
    def test_construction(tmpdir):
        node_id_set = PersistentNodeIdSet(name=tmpdir.mkdir("test"), create_if_missing=True)
        with node_id_set as node_id_set:
            pass
        assert node_id_set.closed


    def test_add(node: Node, tmpdir):
        with PersistentNodeIdSet(name=tmpdir.mkdir("test"), create_if_missing=True) as node_id_set:
            node_id_set.add(node.id)


    def test_get_extant(node: Node, tmpdir):
        with PersistentNodeIdSet(name=tmpdir.mkdir("test"), create_if_missing=True) as node_id_set:
            node_id_set.add(node.id)
            assert node.id in node_id_set


    def test_get_nonextant(node: Node, tmpdir):
        with PersistentNodeIdSet(name=tmpdir.mkdir("test"), create_if_missing=True) as node_id_set:
            assert node.id not in node_id_set