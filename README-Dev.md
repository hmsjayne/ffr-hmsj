# Final Fantasy Randomizer: HMS Jayne Prototype
Development guide


## Example of how to modify something, given a data type.

```python
enemy_stats_stream = rom.open_bytestream(0x1DE044, 194 * 32)
new_enemy_stats_stream = Output()
for index in range(0, 194):
    enemy = EnemyStats(enemy_stats_stream)
    enemy.max_hp = int(enemy.max_hp * 0.1)
    enemy.write(new_enemy_stats_stream)

rom = rom.apply_patch(0x1DE044, new_enemy_stats_stream.get_buffer())
```

More details coming soon(er or later).