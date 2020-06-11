## Configuration

In configuration.yaml:
```yaml
saver:
```

## Available services

### Save state
```yaml
service: saver.save_state
data:
  entity_id: cover.living_room
```

### Restore state
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
```yaml
service: saver.delete
data:
  entity_id: cover.living_room
```

### Set variable
```yaml
service: saver.set_variable
data:
  name: counter
```

### Delete variable
```yaml
service: saver.delete_variable
data:
  name: counter
```

### Execute script
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
