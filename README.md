# Solis Cloud Control API Integration

This is very initial version of the Solis Cloud Control API integration for Home Assistant.
It allows you to read and control various settings of your Solis inverter.

See [issue tracker](https://github.com/mkuthan/solis-cloud-control/issues) for further plans.

## Installation

The integration is not currently available in [HACS](https://www.hacs.xyz/). However, you can install it manually by following these steps:

Clone the repository into your Home Assistant filesystem:

```bash
git clone https://github.com/mkuthan/solis-cloud-control.git
```

Create a symlink to the `custom_components` directory:

```bash
ln -s solis-cloud-control/custom_components custom_components/solis_cloud_control
```

Restart Home Assistant and search for "Solis Cloud Control" in the integrations page.

> [!TIP]
> For updates on HACS availability, see [issue #7](https://github.com/mkuthan/solis-cloud-control/issues/7).

## Configuration

Configure Solis Cloud Control integration with:

* Solis API key
* Solis Token
* Solis Inverter Serial Number

## Features

![Inverter Controls](inverter-controls.png)

### Functional

* ⚡ Storage Modes: "Self-Use", "Feed-In Priority"
* 🛠️ "Battery Reserve" and "Allow Grid Charging" options as Storage Mode attributes
* ⏱️ Charge/Discharge Slots
* 🔋 Battery Reserve SOC, Over Discharge SOC and Force Charge SOC

* 📦 Batch reading of all inverter settings in a single request to fit within the API limits
* 🔄 Retry logic for API requests to mitigate API stability issues
* 🏡 Best Home Assistant practices for integration development 😜

## Local Development

Install dependencies (once):

```bash
uv sync
```

Run the integration locally:

```bash
./scripts/run
```
