---
name: Bug Report
about: Report a bug or issue with the integration
title: '[Bug] '
labels: 'bug'
assignees: ''

---

## Description
Provide a clear and concise description of the bug.

## Steps to Reproduce
Provide detailed steps to reproduce the issue:

1. 
2. 
3. 

## Expected Behavior
Describe what you expected to happen.

## Actual Behavior
Describe what actually happens.

## Environment
- Home Assistant Version:
- Integration Version:
- Inverter Model:
- Inverter Model ID:
- Data Logger Model:
- Installation Method: [HACS / Manual]

## Diagnostics
Please download and attach the diagnostics file from the integration:

1. Go to [Settings > Devices & services](https://my.home-assistant.io/redirect/integrations/)
2. Select "Solis Cloud Control" integration
3. Click on the device
4. Click "Download diagnostics"

> [!NOTE]
> The diagnostics file is automatically redacted and does not contain sensitive information like API keys or full serial numbers.

```json
[Paste diagnostics content here if you cannot attach the file]
```

## Logs
Please include relevant logs from Home Assistant. To enable debug logging for this integration:

1. Add the following to your `configuration.yaml`:
   ```yaml
   logger:
     default: warning
     logs:
       custom_components.solis_cloud_control: debug
   ```
2. Restart Home Assistant
3. Reproduce the issue
4. Check the logs at [Settings > System > Logs](https://my.home-assistant.io/redirect/logs/)

```text
[Paste relevant log entries here]
```

## Screenshots
If applicable, add screenshots to help explain the problem.

## Additional Context
Add any other context about the problem here. For example:
- Does the issue occur consistently or intermittently?
- Did this work in a previous version?
- Are there any error messages displayed in the UI?
- Have you made any recent changes to your setup?

## Possible Solution
(Optional) If you have suggestions on how to fix the bug, please share them here.
