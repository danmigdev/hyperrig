/* The records and the names of eight scenes (scenes.c), and where the application's code finds them: it adds its own offsets, 11936 for a
 * record and 3248 for a name, which are those of its state, to a base. */
.section .bss.hyperrig_scenes,"aw",@nobits
.balign 4
.global hyperrig_scenes
hyperrig_scenes:
    .space 2080
.global hyperrig_scene_names
hyperrig_scene_names:
    .space 128
.global hyperrig_scene_base
.set hyperrig_scene_base, hyperrig_scenes - 11936
.global hyperrig_name_base
.set hyperrig_name_base, hyperrig_scene_names - 3248
