# Solis Cloud Control Integration

[![CI](https://github.com/mkuthan/solis-cloud-control/actions/workflows/ci.yml/badge.svg)](https://github.com/mkuthan/solis-cloud-control/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/mkuthan/solis-cloud-control/graph/badge.svg?token=19S6622V10)](https://codecov.io/gh/mkuthan/solis-cloud-control)
![GitHub Release](https://img.shields.io/github/v/release/mkuthan/solis-cloud-control)

This is the Solis Cloud Control API integration for Home Assistant.
It allows you to read and control various settings of your Solis inverter.
See my blog post for inspiration how to use this integration: [Home Assistant Solar Energy Management](https://mkuthan.github.io/blog/2025/04/12/home-assistant-solar/).

> [!NOTE]
> If your primary goal is to monitor data from the Solis Cloud Monitoring API, you might want to explore the [Solis Sensor Integration](https://github.com/hultenvp/solis-sensor/).  
> Both integrations are complementary and can be used together to enhance your Home Assistant setup.

## Installation

Use [HACS](https://www.hacs.xyz/) to install the integration:

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click on the three dots menu in the top right corner
4. Select "Custom repositories"
5. Add `https://github.com/mkuthan/solis-cloud-control` as an Integration
6. Click "Add"
7. Go back to the Integrations page
8. Click on the "+" button in the bottom right corner
9. Search for "Solis Cloud Control"
10. Click on "Install" to add the integration to your Home Assistant instance
11. Restart Home Assistant

## Configuration

1. Go to "Configuration" > "Integrations"
2. Click on the "+" button in the bottom right corner
3. Search for "Solis Cloud Control"
4. Click on "Solis Cloud Control" to add the integration
5. Enter your Solis API key and token
6. Select the inverter you want to control from the list

## Features

* ⚡ Control storage modes: "Self-Use", "Feed-In Priority" and "Off-Grid"
* ⏱️ Schedule charge and discharge slots
* ⚖️ Set maximum export power
* 🛠️ Access "Battery Reserve" and "Allow Grid Charging" options as Storage Mode attributes

![Inverter Controls](inverter_controls.png)

It also provides battery related sensors:

![Inverter Sensors](inverter_sensors.png)

The integration also meets several non-functional requirements:

* 📦 Batch reading of all inverter settings in a single request to fit within the Solis Cloud API limits
* 🔄 Retry logic for API requests to mitigate API stability issues
* 🏡 Best Home Assistant practices for integration development 😜

## Supported devices

* Solis Hybrid Inverter S6-EH3P12
* Solis Datalogger S2-WL-ST

## Local Development

Install dependencies (once):

```bash
uv sync
```

Run the integration locally:

```bash
./scripts/run
```

Run a single test:

```bash
pytest --cov-fail-under=0 tests/test_init.py
```

## Release

To release a new version, create a new tag and push it to the repository:

```bash
git tag v1.0.1
git push origin v1.0.1
```
