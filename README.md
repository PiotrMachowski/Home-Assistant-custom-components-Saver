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
        position: "{{ attributes_current_position | int }}"
```