# Button Pages: Custom Action, State Indicator Entity & State Value

## Summary

This change brings Button Pages (entity01-entity32) to feature parity with Hardware Buttons by adding three new optional fields per button:

- **Custom Action** - arbitrary HA action(s) executed on short click, before the standard entity toggle
- **State Indicator Entity** - an alternate entity whose state drives the button's on/off indicator, instead of the controlled entity
- **State Value** - when set, the button is "on" when the State Indicator Entity's state equals this string (instead of requiring a binary on/off entity)

These fields are entirely optional.  Existing configurations are unaffected; all three default to empty/inactive values.

## Motivation

Hardware Buttons already support Custom Action and State Indicator Entity.  Button Pages did not, limiting what users could do with the 32 configurable buttons across 4 pages.

A key use case is **scene tracking**: showing which Hue/HA scene is currently
active.  HA scenes are stateless ("fire and forget"), so there is no built-in
way to show a scene button as "on".  The combination of Custom Action + State
Indicator Entity + State Value enables this with minimal HA-side configuration
and zero binary sensor helpers.

## What Changed

### New Blueprint Inputs (per button, x32)

| Input | Type | Default | Description |
| ----- | ---- | ------- | ----------- |
| `entityNN_custom_action` | `action` | `[]` | Additional action(s) to run when the button is clicked |
| `entityNN_state_entity` | `entity` | `""` | Entity whose state drives the button indicator |
| `entityNN_state_value` | `text` | `""` | When set, button is "on" when state entity's state matches this value |

### State Entity Selector

Added `input_select` to the `&hardware-button-state-selector` domain filter, allowing `input_select` helpers to be selected as state indicator entities (for both button pages and hardware buttons).

### Variables (`buttons_pages.buttons`)

Each button entry in the list now includes:

```yaml
state_entity: !input 'entityNN_state_entity'
state_value: !input 'entityNN_state_value'
```

### State Triggers

32 additional state triggers added (one per `entityNN_state_entity`), all with `id: trigger_buttonpage_state`.  These fire the existing state update handler when a state indicator entity changes.

### Rendering Logic (`&display_button_page_button`)

- Added `state_entity_id` variable: resolves to `state_entity` if valid, otherwise falls back to the button's own entity
- Added `state_value` variable: extracted from `repeat.item.state_value`
- Modified `btn_state` calculation:
  - If `state_value` is non-empty: `state_entity_state == state_value`
  - Otherwise: existing on/off logic using `state_entity_state` (which itself falls back to `entity_state` when no state entity is configured)
- Flash-reset for momentary entities (scenes, scripts, buttons): skipped when a custom `state_entity` is configured, allowing persistent state indication

### Click Handler (Button Pages short click)

A 32-branch `choose` block runs the corresponding `!input entityNN_custom_action` before the standard `*short_press_action_call` toggle.  Empty custom actions (the default) are no-ops.

After the standard action completes, the click handler re-renders all buttons on
the current page (with a 300ms delay to allow state changes to propagate).  This
ensures immediate visual feedback for custom actions that modify a state indicator
entity (e.g., setting an `input_select` for scene tracking), without relying
solely on parallel state trigger instances.

### State Update Handler

The `for_each` filter now matches buttons where either `entity == trigger.entity_id` OR `state_entity == trigger.entity_id`, so state changes on the indicator entity trigger a re-render.

## No Firmware Changes

All changes are confined to the blueprint YAML.  The ESPHome firmware and Nextion display firmware are unaffected; they continue to receive the same button state commands.

---

## Use Case: Scene Tracking (Hue-style)

### Problem

You have scene buttons on a Button Page and want the active scene to show as "on" while others show as "off", similar to how the Philips Hue app displays active scenes.

### Prerequisites

- Scenes configured in HA (e.g., `scene.dining_room_savanna_sunset`, `scene.dining_room_island_warmth`)
- A light entity representing the target group (e.g., `light.dining_room`)

### Step 1: Create an Input Select Helper

**Settings > Devices & Services > Helpers > Create Helper > Dropdown**

| Field | Value |
| ----- | ----- |
| Name | Dining Room Active Scene |
| Entity ID | `input_select.dining_room_active_scene` |
| Options | `scene.dining_room_savanna_sunset`, `scene.dining_room_island_warmth`, `none` |

Using full scene entity IDs as option values keeps things consistent with the blueprint's State Value field.

### Step 2: Create a "Clear on Light Off" Automation

Create an automation that resets the tracker when the light group turns off (e.g., via physical switch, another automation, or the HA UI):

```yaml
automation:
  - alias: "Clear dining room scene tracker on light off"
    trigger:
      - platform: state
        entity_id: light.dining_room
        to: "off"
    action:
      - action: input_select.select_option
        target:
          entity_id: input_select.dining_room_active_scene
        data:
          option: "none"
```

### Step 3: Configure Each Scene Button in the Blueprint

For **Savanna Sunset** (e.g., Button Page 1, Button 1):

| Blueprint Field | Value |
| --------------- | ----- |
| Entity | `scene.dining_room_savanna_sunset` |
| Custom Action | *(see below)* |
| State Indicator Entity | `input_select.dining_room_active_scene` |
| State Value | `scene.dining_room_savanna_sunset` |

**Custom Action** (using the visual action builder):

1. Open the blueprint configuration
2. Under Button Page 1, Button 1, find **Custom action**
3. Click **Add Action**
4. Search for "Input select: Select option" and select it
5. Under **Targets**, click **Choose entity** and select `input_select.dining_room_active_scene`
6. Under **Option**, type: `scene.dining_room_savanna_sunset`

For **Island Warmth** (e.g., Button Page 1, Button 2):

| Blueprint Field | Value |
| --------------- | ----- |
| Entity | `scene.dining_room_island_warmth` |
| Custom Action | *(same steps, different option value)* |
| State Indicator Entity | `input_select.dining_room_active_scene` |
| State Value | `scene.dining_room_island_warmth` |

**Custom Action** (same process):

1. **Add Action** > "Input select: Select option"
2. **Target entity**: `input_select.dining_room_active_scene`
3. **Option**: `scene.dining_room_island_warmth`

### How It Works at Runtime

1. User taps "Savanna Sunset"
2. **Custom Action** fires: sets `input_select` to `scene.dining_room_savanna_sunset`
3. **Standard Action** fires: `scene.turn_on` activates the scene
4. `input_select` state now matches the button's State Value; button renders as **on**
5. User taps "Island Warmth"
6. Custom Action updates `input_select` to the new scene
7. Savanna Sunset button: `input_select` state no longer matches its State Value; renders as **off**
8. Island Warmth button: `input_select` state matches; renders as **on**
9. Someone turns the light off (any method)
10. Automation clears `input_select` to `none`; all scene buttons render as **off**

### HA Objects Summary

| Type | Count | Purpose |
| ---- | ----- | ------- |
| `input_select` | 1 per room | Tracks the last-activated scene |
| Automation | 1 per room | Clears tracker when lights turn off |

No template sensors or binary sensors required.
