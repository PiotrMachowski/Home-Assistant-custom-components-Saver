[![HACS Default][hacs_shield]][hacs]
[![GitHub Latest Release][releases_shield]][latest_release]
[![GitHub All Releases][downloads_total_shield]][releases]
[![Installations][installations_shield]][releases]
[![Community Forum][community_forum_shield]][community_forum]<!-- piotrmachowski_support_badges_start -->
[![Ko-Fi][ko_fi_shield]][ko_fi]
[![buycoffee.to][buycoffee_to_shield]][buycoffee_to]
[![PayPal.Me][paypal_me_shield]][paypal_me]
[![Revolut.Me][revolut_me_shield]][revolut_me]
<!-- piotrmachowski_support_badges_end -->


[hacs_shield]: https://img.shields.io/static/v1.svg?label=HACS&message=Default&style=popout&color=green&labelColor=41bdf5&logo=HomeAssistantCommunityStore&logoColor=white
[hacs]: https://hacs.xyz/docs/default_repositories

[latest_release]: https://github.com/PiotrMachowski/Home-Assistant-custom-components-Saver/releases/latest
[releases_shield]: https://img.shields.io/github/release/PiotrMachowski/Home-Assistant-custom-components-Saver.svg?style=popout

[releases]: https://github.com/PiotrMachowski/Home-Assistant-custom-components-Saver/releases
[downloads_total_shield]: https://img.shields.io/github/downloads/PiotrMachowski/Home-Assistant-custom-components-Saver/total

[installations_shield]: https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fanalytics.home-assistant.io%2Fcustom_integrations.json&query=%24.saver.total&style=popout&color=41bdf5&label=analytics

[community_forum_shield]: https://img.shields.io/static/v1.svg?label=%20&message=Forum&style=popout&color=41bdf5&logo=HomeAssistant&logoColor=white
[community_forum]: https://community.home-assistant.io/t/custom-component-saver/204249


# Saver

This custom component allows you to save current state of any entity and use its data later to restore it.

Additionally, you can create simple variables and use their values in scripts.

## Installation

### Using [HACS](https://hacs.xyz/) (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=PiotrMachowski&repository=Home-Assistant-custom-components-Saver&category=Integration)

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

### Using UI

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=saver)

From the Home Assistant front page go to **Configuration** and then select **Integrations** from the list.

Use the "plus" button in the bottom right to add a new integration called **Saver**.

The success dialog will appear or an error will be displayed in the popup.

### YAML (Deprecated)

Add following code in configuration.yaml:
```yaml
saver:
```

## Available services

### Save state
Saves the state and parameters of the entity. Supports saving multiple entities.
```yaml
service: saver.save_state
data:
  entity_id: cover.living_room
```

### Restore state
Restores saved states (only for entities that support it). Supports restoring multiple entities.
```yaml
service: saver.restore_state
data:
  entity_id: cover.living_room
```

Optional attributes: 
  - `delete_after_run`: allows to disable removing saved states after restoring them (default: `true`).
  - `transition`: Number that represents the time (in seconds) the light should take to transition to the new state.
```yaml
service: saver.restore_state
data:
  entity_id: 
    - cover.living_room
    - light.living_room
  delete_after_run: false
  transition: 3
```

### Delete saved state
Deletes a saved state for an entity.
```yaml
service: saver.delete
data:
  entity_id: cover.living_room
```

### Delete saved states by regex
Deletes saved states for entities that match provided regex.
```yaml
service: saver.delete_regex
data:
  entity_id_regex: light.living_room.*
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

### Delete variables by regex
Deletes saved variables that match provided regex.
```yaml
service: saver.delete_variable_regex
data:
  regex: "counter_\\d+"
```

### Clear
Deletes all saved data.
```yaml
service: saver.clear
```


## Using saved values in templates
It is possible to use saved data in templates using `saver_entity` and `saver_variable` functions:
```yaml
{{ saver_entity("sun.sun") }}  # returns saved state of "sun.sun" entity
{{ saver_entity("sun.sun", "azimuth") }}  # returns "azimuth" attribute of saved "sun.sun" entity
{{ saver_variable("counter") }}  # returns saved variable "counter"
```

## Events

After the completion of the services mentioned before, the following events are fired:

| **Service Function**      | **Event ID**                          | **Provided Arguments**    |
|---------------------------|---------------------------------------|---------------------------|
| **save_state**            | event_saver_saved_entity              | entity_id                 |
| **restore_state**         | event_saver_restored                  | entity_id                 |
| **delete**                | event_saver_deleted_entity            | entity_id                 |
| **delete_regex**          | event_saver_deleted_entity_by_regex   | entity_id_regex, entities |
| **clear**                 | event_saver_cleared                   |                           |
| **set_variable**          | event_saver_saved_variable            | variable, value           |
| **delete_variable**       | event_saver_deleted_variable          | variable                  |
| **delete_variable_regex** | event_saver_deleted_variable_by_regex | variables, regex          |

The events can be used to trigger further automations that depend on the completion of the services. The documentation is provided [here](https://www.home-assistant.io/docs/automation/trigger/#event-trigger). 


<!-- piotrmachowski_support_links_start -->

## Support

If you want to support my work with a donation you can use one of the following platforms:

<table>
  <tr>
    <th>Platform</th>
    <th>Payment methods</th>
    <th>Link</th>
    <th>Comment</th>
  </tr>
  <tr>
    <td>Ko-fi</td>
    <td>
      <li>PayPal</li>
      <li>Credit card</li>
    </td>
    <td>
      <a href='https://ko-fi.com/piotrmachowski' target='_blank'><img height='35px' src='https://storage.ko-fi.com/cdn/kofi6.png?v=6' border='0' alt='Buy Me a Coffee at ko-fi.com' />
    </td>
    <td>
      <li>No fees</li>
      <li>Single or monthly payment</li>
    </td>
  </tr>
  <tr>
    <td>buycoffee.to</td>
    <td>
      <li>BLIK</li>
      <li>Bank transfer</li>
    </td>
    <td>
      <a href="https://buycoffee.to/piotrmachowski" target="_blank"><img src="https://buycoffee.to/btn/buycoffeeto-btn-primary.svg" height="35px" alt="Postaw mi kawę na buycoffee.to"></a>
    </td>
    <td></td>
  </tr>
  <tr>
    <td>PayPal</td>
    <td>
      <li>PayPal</li>
    </td>
    <td>
      <a href="https://paypal.me/PiMachowski" target="_blank"><img src="https://www.paypalobjects.com/webstatic/mktg/logo/pp_cc_mark_37x23.jpg" border="0" alt="PayPal Logo" height="35px" style="height: auto !important;width: auto !important;"></a>
    </td>
    <td>
      <li>No fees</li>
    </td>
  </tr>
  <tr>
    <td>Revolut</td>
    <td>
      <li>Revolut</li>
      <li>Credit Card</li>
    </td>
    <td>
      <a href="https://revolut.me/314ma" target="_blank"><img src="https://assets.revolut.com/assets/favicons/favicon-32x32.png" height="32px" alt="Revolut"></a>
    </td>
    <td>
      <li>No fees</li>
    </td>
  </tr>
</table>

### Powered by
[![PyCharm logo.](https://resources.jetbrains.com/storage/products/company/brand/logos/jetbrains.svg)](https://jb.gg/OpenSourceSupport)


[ko_fi_shield]: https://img.shields.io/static/v1.svg?label=%20&message=Ko-Fi&color=F16061&logo=ko-fi&logoColor=white

[ko_fi]: https://ko-fi.com/piotrmachowski

[buycoffee_to_shield]: https://shields.io/badge/buycoffee.to-white?style=flat&labelColor=white&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAABhmlDQ1BJQ0MgcHJvZmlsZQAAKJF9kT1Iw1AUhU9TpaIVh1YQcchQnayIijhKFYtgobQVWnUweemP0KQhSXFxFFwLDv4sVh1cnHV1cBUEwR8QVxcnRRcp8b6k0CLGC4/3cd49h/fuA4R6malmxzigapaRisfEbG5FDLzChxB6MIZ+iZl6Ir2QgWd93VM31V2UZ3n3/Vm9St5kgE8knmW6YRGvE09vWjrnfeIwK0kK8TnxqEEXJH7kuuzyG+eiwwLPDBuZ1BxxmFgstrHcxqxkqMRTxBFF1ShfyLqscN7irJarrHlP/sJgXltOc53WEOJYRAJJiJBRxQbKsBClXSPFRIrOYx7+QcefJJdMrg0wcsyjAhWS4wf/g9+zNQuTE25SMAZ0vtj2xzAQ2AUaNdv+PrbtxgngfwautJa/UgdmPkmvtbTIEdC3DVxctzR5D7jcAQaedMmQHMlPSygUgPcz+qYcELoFulfduTXPcfoAZGhWSzfAwSEwUqTsNY93d7XP7d+e5vx+AIahcq//o+yoAAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH5wETCy4vFNqLzwAAAVpJREFUOMvd0rFLVXEYxvHPOedKJnKJhrDLuUFREULE7YDCMYj+AydpsCWiaKu29hZxiP4Al4aWwC1EdFI4Q3hqEmkIBI8ZChWXKNLLvS0/Qcza84V3enm/7/s878t/HxGkeTaIGziP+EB918nawu7Dq1d0e1+2J2bepnk2jFEUVVF+qKV51o9neBCaugfge70keoxxUbSWjrQ+4SUyzKZ5NlnDZdzGG7w4DIh+dtZEFntDA98l8S0MYwctNGrYz9WqKJePFLq80g5Sr+EHlnATp+NA+4qLaZ7FfzMrzbMBjGEdq8GrJMZnvAvFC/8wfAwjWMQ8XmMzaW9sdevNRgd3MFhvNpbaG1u/Dk2/hOc4gadVUa7Um425qii/7Z+xH9O4jwW8Cqv24Tru4hyeVEU588cfBMgpPMI9nMFe0BkFzVOYrYqycyQgQJLwTC2cDZCPeF8V5Y7jGb8BUpRicy7OU5MAAAAASUVORK5CYII=

[buycoffee_to]: https://buycoffee.to/piotrmachowski

[buy_me_a_coffee_shield]: https://img.shields.io/static/v1.svg?label=%20&message=Buy%20me%20a%20coffee&color=6f4e37&logo=buy%20me%20a%20coffee&logoColor=white

[buy_me_a_coffee]: https://www.buymeacoffee.com/PiotrMachowski

[paypal_me_shield]: https://img.shields.io/static/v1.svg?label=%20&message=PayPal.Me&logo=paypal

[paypal_me]: https://paypal.me/PiMachowski

[revolut_me_shield]: https://img.shields.io/static/v1.svg?label=%20&message=Revolut&logo=revolut

[revolut_me]: https://revolut.me/314ma
<!-- piotrmachowski_support_links_end -->