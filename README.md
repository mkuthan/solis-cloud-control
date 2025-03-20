# Solis Cloud Control API Integration

This is very initial version of the Solis Cloud Control API integration for Home Assistant.
It allows you to read and control various settings of your Solis inverter.
Doesn't support sensors, switches, or other entities yet - only basic read and control actions crafted for automations.

## Read Inverter Settings

Storage Mode

```yaml
action: solis_cloud_control.read
data:
  cid: 636
```

Charge Time Slot 1

```yaml
action: solis_cloud_control.read
data:
  cid: 5946
```

Charge Time Slot 1 Switch

```yaml
action: solis_cloud_control.read
data:
  cid: 5916
```

Charge Time Slot 1 Current

```yaml
action: solis_cloud_control.read
data:
  cid: 5948
```

Charge Time Slot 1 Battery SOC

```yaml
action: solis_cloud_control.read
data:
  cid: 5928
```

Discharge Time Slot 1

```yaml
action: solis_cloud_control.read
data:
  cid: 5964
```

Discharge Time Slot 1 Switch

```yaml
action: solis_cloud_control.read
data:
  cid: 5922
```

Discharge Time Slot 1 Current

```yaml
action: solis_cloud_control.read
data:
  cid: 5967
```

Discharge Time Slot 1 Battery SOC

```yaml
action: solis_cloud_control.read
data:
  cid: 5965
```

## Control Storage Mode

Self-Use Mode - No Grid Charging, Backup Mode On

```yaml
action: solis_cloud_control.control
data:
  cid: 636
  value: "17"
```

Feed-In Priority Mode - No Grid Charging, Backup Mode On:

```yaml
action: solis_cloud_control.control
data:
  cid: 636
  value: "80"
```
