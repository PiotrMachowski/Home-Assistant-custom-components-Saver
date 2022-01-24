[![HACS Default][hacs_shield]][hacs]
[![GitHub Latest Release][releases_shield]][latest_release]
[![GitHub All Releases][downloads_total_shield]][releases]
[![Community Forum][community_forum_shield]][community_forum]
[![Buy me a coffee][buy_me_a_coffee_shield]][buy_me_a_coffee]
[![PayPal.Me][paypal_me_shield]][paypal_me]


[hacs_shield]: https://img.shields.io/static/v1.svg?label=HACS&message=Default&style=popout&color=green&labelColor=41bdf5&logo=HomeAssistantCommunityStore&logoColor=white
[hacs]: https://hacs.xyz/docs/default_repositories

[latest_release]: https://github.com/PiotrMachowski/Home-Assistant-custom-components-Saver/releases/latest
[releases_shield]: https://img.shields.io/github/release/PiotrMachowski/Home-Assistant-custom-components-Saver.svg?style=popout

[releases]: https://github.com/PiotrMachowski/Home-Assistant-custom-components-Saver/releases
[downloads_total_shield]: https://img.shields.io/github/downloads/PiotrMachowski/Home-Assistant-custom-components-Saver/total

[community_forum_shield]: https://img.shields.io/static/v1.svg?label=%20&message=Forum&style=popout&color=41bdf5&logo=HomeAssistant&logoColor=white
[community_forum]: https://community.home-assistant.io/t/custom-component-saver/204249

[buy_me_a_coffee_shield]: https://img.shields.io/static/v1.svg?label=%20&message=Buy%20me%20a%20coffee&color=6f4e37&logo=buy%20me%20a%20coffee&logoColor=white
[buy_me_a_coffee]: https://www.buymeacoffee.com/PiotrMachowski

[paypal_me_shield]: https://img.shields.io/static/v1.svg?label=%20&message=PayPal.Me&logo=paypal
[paypal_me]: https://paypal.me/PiMachowski

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=saver)

# Saver

This custom component allows you to save current state of any entity and use its data later to restore it.

Additionally you can create simple variables and use their values in scripts.

## Installation

### Using [HACS](https://hacs.xyz/) (recommended)

This integration can be installed using HACS.
To do it search for `Saver` in *Integrations* section.

### Manual

To install this integration manually you have to download [*saver.zip*](https://github.com/PiotrMachowski/Home-Assistant-custom-components-Saver/releases/latest/download/saver.zip) and extract its contents to `config/custom_components/saver` directory:
```bash
mkdir -p custom_components/saver
cd custom_components/saver
wget https://github.com/PiotrMachowski/Home-Assistant-custom-components-Saver/releases/latest/download/saver.zip
unzip saver.zip
rm saver.zip
```

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
<a href="https://paypal.me/PiMachowski" target="_blank"><img src="https://www.paypalobjects.com/webstatic/mktg/logo/pp_cc_mark_37x23.jpg" border="0" alt="PayPal Logo" style="height: auto !important;width: auto !important;"></a>
