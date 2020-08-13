[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)
[![Community Forum](https://img.shields.io/badge/Community-Forum-41BDF5.svg?style=popout)](https://community.home-assistant.io/t/custom-component-saver/204249)
[![buymeacoffee_badge](https://img.shields.io/badge/Donate-buymeacoffe-ff813f?style=flat)](https://www.buymeacoffee.com/PiotrMachowski)

# Saver

This custom component allows you to save current state of any entity and use its data later to restore it.

Additionally you can create simple variables and use their values in scripts.

## Installation

### HACS
You can install this custom component using [HACS](https://hacs.xyz/).

### Manual
To manually install this custom component you have to copy the contents of `custom_components/saver/` to `<your config dir>/custom_components/saver/`.
## Configuration

### GUI
From the Home Assistant front page go to **Configuration** and then select **Integrations** from the list.

Use the plus button in the bottom right to add a new integration called **Saver**.

The success dialog will appear or an error will be displayed in the popup.

### YAML
In configuration.yaml:
```yaml
saver:
```

## Available services

### Save state
Saves the state and parameters of the entity.
```yaml
service: saver.save_state
data:
  entity_id: cover.living_room
```

### Restore state
Executes the script using saved state of the entity.

To use state of an entity you have to use a following value in a template: `state`.

To use state attribute (in this case `current_position`) of an entity you have to use a following value in a template: `attr_current_position`.

```yaml
service: saver.restore_state
data:
  entity_id: cover.living_room
  restore_script:
    - service: cover.set_cover_position
      data_template:
        entity_id: cover.living_room
        position: "{{ attr_current_position | int }}"
    - service: input_text.set_value
      data_template:
        entity_id: input_text.cover_description
        value: "Cover is now {{ state }}"
```

### Delete saved state
Deletes a saved state for an entity.
```yaml
service: saver.delete
data:
  entity_id: cover.living_room
```

### Set variable
Sets the value to the variable.
```yaml
service: saver.set_variable
data:
  name: counter
  value: 3
```

### Delete variable
Deletes a saved variable.
```yaml
service: saver.delete_variable
data:
  name: counter
```

### Execute script
Executes a script using all saved entities and variables.

To use state of an entity (in this case `cover.living_room`) you have to use a following value in a template: `cover_living_room_state`.

To use state attribute (in this case `current_position`) of an entity you have to use a following value in a template: `cover_living_room_attr_current_position`.

```yaml
service: saver.execute
data:
  script:
    - service: cover.set_cover_position
      data_template:
        entity_id: cover.living_room
        position: "{{ cover_living_room_attr_current_position | int }}"
    - service: input_text.set_value
      data_template:
        entity_id: input_text.cover_description
        value: "Cover is now {{ cover_living_room_state }}"
    - service: input_text.set_value
      data_template:
        entity_id: input_text.counter_description
        value: "Counter has value {{ counter }}"
```

### Clear
Deletes all saved data.
```yaml
service: saver.clear
```

## Using in templates
It is possible to use saved data in templates via `saver.saver` entity:
```yaml
script:
  - service: cover.set_cover_position
    data_template:
      entity_id: cover.living_room
      position: "{{ state_attr('saver.saver', 'entities')['cover.living_room'].attributes.current_position | int }}"
  - service: input_text.set_value
    data_template:
      entity_id: input_text.cover_description
      value: "Cover is now {{ state_attr('saver.saver', 'entities')['cover.living_room'].state }}"
  - service: input_text.set_value
    data_template:
      entity_id: input_text.counter_description
      value: "Counter has value {{ state_attr('saver.saver', 'variables')["counter"] }}"
```

<a href="https://www.buymeacoffee.com/PiotrMachowski" target="_blank"><img src="https://bmc-cdn.nyc3.digitaloceanspaces.com/BMC-button-images/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: auto !important;width: auto !important;" ></a>
