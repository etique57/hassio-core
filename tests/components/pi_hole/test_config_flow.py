"""Test pi_hole config flow."""
from homeassistant.components.pi_hole.const import CONF_STATISTICS_ONLY, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import (
    CONF_CONFIG_ENTRY,
    CONF_CONFIG_FLOW_API_KEY,
    CONF_CONFIG_FLOW_USER,
    NAME,
    _create_mocked_hole,
    _patch_config_flow_hole,
)


def _flow_next(hass: HomeAssistant, flow_id: str):
    return next(
        flow
        for flow in hass.config_entries.flow.async_progress()
        if flow["flow_id"] == flow_id
    )


async def test_flow_user(hass: HomeAssistant):
    """Test user initialized flow."""
    mocked_hole = _create_mocked_hole()
    with _patch_config_flow_hole(mocked_hole):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {}
        _flow_next(hass, result["flow_id"])

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_CONFIG_FLOW_USER,
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "api_key"
        assert result["errors"] is None
        _flow_next(hass, result["flow_id"])

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_CONFIG_FLOW_API_KEY,
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == NAME
        assert result["data"] == CONF_CONFIG_ENTRY

        # duplicated server
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data=CONF_CONFIG_FLOW_USER,
        )
        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "already_configured"


async def test_flow_statistics_only(hass: HomeAssistant):
    """Test user initialized flow with statistics only."""
    mocked_hole = _create_mocked_hole()
    with _patch_config_flow_hole(mocked_hole):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {}
        _flow_next(hass, result["flow_id"])

        user_input = {**CONF_CONFIG_FLOW_USER}
        user_input[CONF_STATISTICS_ONLY] = True
        config_entry_data = {**CONF_CONFIG_ENTRY}
        config_entry_data[CONF_STATISTICS_ONLY] = True
        config_entry_data.pop(CONF_API_KEY)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=user_input,
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == NAME
        assert result["data"] == config_entry_data


async def test_flow_user_invalid(hass: HomeAssistant):
    """Test user initialized flow with invalid server."""
    mocked_hole = _create_mocked_hole(True)
    with _patch_config_flow_hole(mocked_hole):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONF_CONFIG_FLOW_USER
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {"base": "cannot_connect"}
