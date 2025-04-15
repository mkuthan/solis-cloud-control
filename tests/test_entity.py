import pytest
from homeassistant.helpers.entity import EntityDescription

from custom_components.solis_cloud_control.entity import SolisCloudControlEntity

_ANY_CID = -1


@pytest.fixture
def entity(mock_coordinator):
    return SolisCloudControlEntity(
        coordinator=mock_coordinator,
        entity_description=EntityDescription(
            key="test_entity",
            name="Test Entity",
        ),
        cid=_ANY_CID,
    )


class TestSolisCloudControlEntity:
    def test_available(self, entity):
        entity.coordinator.data = {_ANY_CID: "any value"}
        assert entity.available

    def test_available_cid_none(self, entity):
        entity.coordinator.data = {_ANY_CID: None}
        assert not entity.available
