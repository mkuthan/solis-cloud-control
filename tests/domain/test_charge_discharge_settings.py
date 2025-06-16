import pytest

from custom_components.solis_cloud_control.domain.charge_discharge_settings import (
    ChargeDischargeSettings,
    ChargeDischargeSettingsVariant1,
    ChargeDischargeSettingsVariant2,
)


@pytest.fixture
def variant1_data():
    return "0,0,09:00,10:00,11:00,12:00,50,0,12:30,13:30,14:30,15:30,0,100,16:00,17:00,18:00,19:00"


@pytest.fixture
def variant2_data():
    return "0,0,09:00-10:00,11:00-12:00,50,0,12:30-13:30,14:30-15:30,0,100,16:00-17:00,18:00-19:00"


class TestChargeDischargeSettings:
    def test_create_variant1(self, variant1_data):
        result = ChargeDischargeSettings.create(variant1_data)

        assert isinstance(result, ChargeDischargeSettingsVariant1)

    def test_create_variant2(self, variant2_data):
        result = ChargeDischargeSettings.create(variant2_data)

        assert isinstance(result, ChargeDischargeSettingsVariant2)

    @pytest.mark.parametrize(
        "data",
        [None, "", "invalid data"],
    )
    def test_create_invalid_format(self, data: str):
        result = ChargeDischargeSettings.create(data)
        assert result is None


@pytest.fixture
def variant1_settings(variant1_data):
    return ChargeDischargeSettings.create(variant1_data)


class TestChargeDischargeSettingsVariant1:
    def test_get_charge_current(self, variant1_settings):
        assert variant1_settings.get_charge_current(1) == 0.0
        assert variant1_settings.get_charge_current(2) == 50.0
        assert variant1_settings.get_charge_current(3) == 0.0

    def test_get_discharge_current(self, variant1_settings):
        assert variant1_settings.get_discharge_current(1) == 0.0
        assert variant1_settings.get_discharge_current(2) == 0.0
        assert variant1_settings.get_discharge_current(3) == 100.0

    def test_get_charge_time_slot(self, variant1_settings):
        assert variant1_settings.get_charge_time_slot(1) == "09:00-10:00"
        assert variant1_settings.get_charge_time_slot(2) == "12:30-13:30"
        assert variant1_settings.get_charge_time_slot(3) == "16:00-17:00"

    def test_get_discharge_time_slot(self, variant1_settings):
        assert variant1_settings.get_discharge_time_slot(1) == "11:00-12:00"
        assert variant1_settings.get_discharge_time_slot(2) == "14:30-15:30"
        assert variant1_settings.get_discharge_time_slot(3) == "18:00-19:00"

    def test_set_charge_current(self, variant1_settings):
        variant1_settings.set_charge_current(1, 99.0)
        assert (
            variant1_settings.to_value()
            == "99,0,09:00,10:00,11:00,12:00,50,0,12:30,13:30,14:30,15:30,0,100,16:00,17:00,18:00,19:00"
        )

    def test_set_discharge_current(self, variant1_settings):
        variant1_settings.set_discharge_current(1, 99.0)
        assert (
            variant1_settings.to_value()
            == "0,99,09:00,10:00,11:00,12:00,50,0,12:30,13:30,14:30,15:30,0,100,16:00,17:00,18:00,19:00"
        )

    def test_set_charge_time_slot(self, variant1_settings):
        variant1_settings.set_charge_time_slot(1, "23:00-23:59")
        assert (
            variant1_settings.to_value()
            == "0,0,23:00,23:59,11:00,12:00,50,0,12:30,13:30,14:30,15:30,0,100,16:00,17:00,18:00,19:00"
        )

    def test_set_discharge_time_slot(self, variant1_settings):
        variant1_settings.set_discharge_time_slot(1, "23:00-23:59")
        assert (
            variant1_settings.to_value()
            == "0,0,09:00,10:00,23:00,23:59,50,0,12:30,13:30,14:30,15:30,0,100,16:00,17:00,18:00,19:00"
        )


@pytest.fixture
def variant2_settings(variant2_data):
    return ChargeDischargeSettings.create(variant2_data)


class TestChargeDischargeSettingsVariant2:
    def test_get_charge_current(self, variant2_settings):
        assert variant2_settings.get_charge_current(1) == 0.0
        assert variant2_settings.get_charge_current(2) == 50.0
        assert variant2_settings.get_charge_current(3) == 0.0

    def test_get_discharge_current(self, variant2_settings):
        assert variant2_settings.get_discharge_current(1) == 0.0
        assert variant2_settings.get_discharge_current(2) == 0.0
        assert variant2_settings.get_discharge_current(3) == 100.0

    def test_get_charge_time_slot(self, variant2_settings):
        assert variant2_settings.get_charge_time_slot(1) == "09:00-10:00"
        assert variant2_settings.get_charge_time_slot(2) == "12:30-13:30"
        assert variant2_settings.get_charge_time_slot(3) == "16:00-17:00"

    def test_get_discharge_time_slot(self, variant2_settings):
        assert variant2_settings.get_discharge_time_slot(1) == "11:00-12:00"
        assert variant2_settings.get_discharge_time_slot(2) == "14:30-15:30"
        assert variant2_settings.get_discharge_time_slot(3) == "18:00-19:00"

    def test_set_charge_current(self, variant2_settings):
        variant2_settings.set_charge_current(1, 99.0)
        assert (
            variant2_settings.to_value()
            == "99,0,09:00-10:00,11:00-12:00,50,0,12:30-13:30,14:30-15:30,0,100,16:00-17:00,18:00-19:00"
        )

    def test_set_discharge_current(self, variant2_settings):
        variant2_settings.set_discharge_current(1, 99.0)
        assert (
            variant2_settings.to_value()
            == "0,99,09:00-10:00,11:00-12:00,50,0,12:30-13:30,14:30-15:30,0,100,16:00-17:00,18:00-19:00"
        )

    def test_set_charge_time_slot(self, variant2_settings):
        variant2_settings.set_charge_time_slot(1, "23:00-23:59")
        assert (
            variant2_settings.to_value()
            == "0,0,23:00-23:59,11:00-12:00,50,0,12:30-13:30,14:30-15:30,0,100,16:00-17:00,18:00-19:00"
        )

    def test_set_discharge_time_slot(self, variant2_settings):
        variant2_settings.set_discharge_time_slot(1, "23:00-23:59")
        assert (
            variant2_settings.to_value()
            == "0,0,09:00-10:00,23:00-23:59,50,0,12:30-13:30,14:30-15:30,0,100,16:00-17:00,18:00-19:00"
        )
