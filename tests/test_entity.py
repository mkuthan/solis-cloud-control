import pytest
from homeassistant.helpers.entity import EntityDescription

from custom_components.solis_cloud_control.entity import SolisCloudControlEntity


class TestSolisCloudControlEntity:
    @pytest.mark.parametrize(
        ("coordinator_data", "expected_available"),
        [
            ({1: "any value"}, True),
            ({}, False),
            ({1: None}, False),
            ({2: "any value"}, False),
        ],
    )
    def test_available_single_cid(self, mock_coordinator, coordinator_data, expected_available):
        entity = SolisCloudControlEntity(
            coordinator=mock_coordinator,
            entity_description=EntityDescription(key="any_key", name="any name"),
            cids=1,
        )
        mock_coordinator.data = coordinator_data
        assert entity.available == expected_available

    @pytest.mark.parametrize(
        ("coordinator_data", "expected_available"),
        [
            ({1: "any value", 2: "any value"}, True),
            ({1: "any value"}, False),
            ({1: "any value", 2: None}, False),
            ({}, False),
        ],
    )
    def test_available_multiple_cids(
        self,
        mock_coordinator,
        coordinator_data,
        expected_available,
    ):
        entity = SolisCloudControlEntity(
            coordinator=mock_coordinator,
            entity_description=EntityDescription(key="any_key", name="any name"),
            cids=[1, 2],
        )
        mock_coordinator.data = coordinator_data
        assert entity.available == expected_available
