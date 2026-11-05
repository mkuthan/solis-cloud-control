import pytest
from homeassistant.helpers.entity import EntityDescription

from custom_components.solis_cloud_control.entity import SolisCloudControlEntity


class _CountingEntity(SolisCloudControlEntity):
    update_calls = 0

    def _update_attrs(self) -> None:
        self.update_calls += 1


class TestSolisCloudControlEntity:
    def test_available_when_coordinator_last_update_failed(self, mock_coordinator):
        mock_coordinator.last_update_success = False

        entity = SolisCloudControlEntity(
            coordinator=mock_coordinator,
            entity_description=EntityDescription(key="any_key", name="any name"),
            cids=1,
        )

        assert entity.available is False

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


class TestRefreshAttrs:
    @pytest.mark.parametrize(
        ("coordinator_data", "expected_calls"),
        [
            ({1: "any value", 2: "any value"}, 1),
            ({1: "any value"}, 0),
            ({1: "any value", 2: None}, 0),
        ],
    )
    def test_updates_attrs_only_when_data_present(self, mock_coordinator, coordinator_data, expected_calls):
        entity = _CountingEntity(
            coordinator=mock_coordinator,
            entity_description=EntityDescription(key="any_key", name="any name"),
            cids=[1, 2],
        )
        mock_coordinator.data = coordinator_data

        entity._refresh_attrs()

        assert entity.update_calls == expected_calls
