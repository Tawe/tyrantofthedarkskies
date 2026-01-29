# Armor Templates

Base armor templates per [docs/armor_system.md](../../docs/armor_system.md). Each template defines slot, base DR, damage types, and max HP (durability).

**Fields:** `template_id` or `id`, `name`, `description`, `slot` (head|chest|arms|legs|shield), `weight`, `base_dr`, `primary_damage_type`, `damage_types` (array), `max_hp`.

Final armor items can be built from template + optional material modifier via `create_armor_item(template_id, modifier_id)`.
