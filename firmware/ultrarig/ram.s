; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.
; The ram area of the UltraRig G alpha11 v2/M5.71 application, 0x01c00000..0x01c2030c
; One assembly unit: the pieces follow in address order.
; TARGET_MINI selects the HyperRig MINI changes (tools/build_ultrarig_app.py --target mini).
.ifndef TARGET_MINI
.set TARGET_MINI, 0
.endif
; MINI_PRODUCT adds the HyperRig product changes to the MINI target; without it the MINI target is v4
; (tools/build_hyperrig_mini_image.py --product).
.ifndef MINI_PRODUCT
.set MINI_PRODUCT, 0
.endif
.section .ram,"ax",@progbits
ultrarig_ram_start:
.global L01c008b4
.global L01c00cc0
.global L01c00dd0
.global L01c00e62
.global L01c00f72
.global L01c00fdc
.global L01c0100e
.global L01c0344c
.global L01c03694
.global L01c0374a
.global L01c03766
.global L01c03812
.global L01c040a8
.global L01c04256
.global L01c1f088
.global L01c1f0c0
.global L01c1f0c8
.global L01c1f170
.global L01c1f180
.global L01c1f208
.global L01c1f22c
.global L01c1f234
.global L01c1f26c
.global L01c1f26e
.global L01c1f2b8
.global L01c1f370
.global L01c1f39c
.global L01c1f3a0
.global L01c1f3a4
.global L01c1f7d0
.global L01c1f7d4
.global L01c1f7d8
.global L01c1f7dc
.global L01c1f7e0
.global L01c1f7e4
.global L01c1f7f0
.global L01c1fa14
.global L01c1fa18
.global L01c1fa20
.global L01c1fa24
.global L01c1fa2d
.global L01c1fa30
.global L01c1fc4c
.global L01c1fc5c
.global L01c1fc60
.global L01c1fc64
.global L01c1fc6c
.global L01c1fc70
.global L01c1fc74
.global L01c1fc78
.global L01c1fc80
.global L01c1fc84
.global L01c1fc88
.global L01c1fc8c
.global L01c1fc90
.global L01c1fc94
.global L01c1fc98
.global L01c1fc9c
.global L01c1fca0
.global L01c1fca4
.global L01c1fca8
.global L01c200ac
.global L01c200c4
.global L01c20168
.global L01c2016c
.global L01c20170
.global L01c20174
.global L01c20178
.global L01c2017c
.global L01c20180
.global L01c20188
.global L01c2018e
.global L01c20218
.global L01c2022c
.global L01c20230
.global L01c20234
.global L01c20236
.global L01c2029c
.global L01c202a0
.global L01c202a4
.global L01c202a8
.global L01c202ac
.global L01c202b0
.global L01c202b4
.global L01c202ba
.global L01c202bc
.global L01c202cd
.global L01c202e8
.global L01c202f8
.global L01c2030c
.global L01c21370
.global L01c21374
.global L01c21378
.global L01c213f8
.global L01c213fc
.global L01c21400
.global L01c2140f
.global L01c2142f
.global L01c21450
.global L01c21454
.global L01c21455
.global L01c2145c
.global L01c214c4
.global L01c21714
.global L01c21718
.global L01c2171c
.global L01c21724
.global L01c21932
.global L01c21940
.global L01c21948
.global L01c2194c
.global L01c21950
.global L01c21954
.global L01c2195c
.global L01c21974
.global L01c21988
.global L01c21a20
.global L01c21a31
.global L01c21ac8
.global L01c21ad4
.global L01c21b24
.global L01c21b28
.global L01c21b6c
.global L01c21b7c
.global L01c21c34
.global L01c21c54
.global L01c21c58
.global L01c21c6c
.global L01c21c70
.global L01c21c78
.global L01c21c98
.global L01c21c9c
.global L01c21cb0
.global L01c21cb4
.global L01c21cb8
.global L01c2249c
.global L01c224a0
.global L01c24228
.global L01c2422c
.global L01c24358
.global L01c24420
.global L01c24520
.global L01c245a0
.global L01c246e4
.global L01c246e8
.global L01c246ec
.global L01c24790
.global L01c24d5c
.global L01c25390
.global L01c25394
.global L01c25434
.global L01c25438
.global L01c255dc
.global L01c256dc
.global L01c25c90
.global L01c25ce0
.global L01c25ce8
.global L01c25cf4
.global L01c25cf8
.global L01c25ed8
.global L01c25edc
.global L01c26024
.global L01c2603c
.global L01c26040
.global L01c26090
.global L01c26300
.global L01c26350
.global L01c26354
.global L01c26360
.global L01c267d0
.global L01c267d4
.global L01c267d8
.global L01c267e0
.global L01c26830
.global L01c26834
.global L01c26838
.global L01c2683c
.global L01c26840
.global L01c26844
.global L01c26848
.global L01c2684c
.global L01c26850
.global L01c26854
.global L01c26858
.global L01c2685c
.global L01c2685e
.global L01c26860
.global L01c26864
.global L01c26868
.global L01c26878
.global L01c2687c
.global L01c26880
.global L01c26884
.global L01c26886
.global L01c26888
.global L01c2688c
.global L01c26890
.global L01c268da
.global L01c268f0
.global L01c26928
.global L01c26930
.global L01c26b54
.global L01c26d54
.global L01c26e88
.global L01c26ec0
.global L01c26ef8
.global L01c26f00
.global L01c26f08
.global L01c26f44
.global L01c26fe4
.global L01c27064
.global L01c27099
.global L01c27150
.global L01c27204
.global L01c27734
.global L01c27784
.global L01c278ac
.global L01c27acc
.global L01c27cd4
.global L01c27cd5
.global L01c2a0d0
.global L01c2c220
.global L01c2c222
.global L01c2c228
.global L01c2e020
.global L01c2e074
.global L01c2e5a0
.global L01c2e5a1
.global L01c2f3a0
.global L01c2f9a0
.global L01c2fa38
.global L01c32db0
.global L01c32df0
.global L01c32e8a
.global L01c32fa0
.global L01c33190
.global L01c33240
.global L01c33320
.global L01c33610
.global L01c337f0
.global L01c340c0
.global L01c340c4
.global L01c340c8
.global L01c340cc
.global L01c34174
.global L01c34184
.global L01c34188
.global L01c34190
.global L01c34194
.global L01c34198
.global L01c3419c
.global L01c341a0
.global L01c341a4
.global L01c341a8
.global L01c341bc
.global L01c341c0
.global L01c343c4
.global L01c343c8
.global L01c343d0
.global L01c343d4
.global L01c343d8
.global L01c34418
.global L01c3441c
.global L01c34420
.global L01c34424
.global L01c34428
.global L01c34430
.global L01c34434
.global L01c34438
.global L01c3443c
.global L01c34440
.global L01c34448
.global L01c3444c
.global L01c34450
.global L01c34454
.global L01c34458
.global L01c3445c
.global L01c34468
.global L01c3446c
.global L01c34488
.global L01c34489
.global L01c3448a
.global L01c3448b
.global L01c3448c
.global L01c344b0
.global L01c344b4
.global L01c34720
.global L01c34734
.global L01c34748
.global L01c3475c
.global L01c34770
.global L01c34784
.global L01c34788
.global L01c3478c
.global L01c347dc
.global L01c3481c
.global L01c3486c
.global L01c34c6c
.global L01c34d10
.global L01c34d18
.global L01c350b8
.global L01c360b8
.global L01c363b8
.global L01c373b8
.global L01c373e4
.global L01c3740c
.global L01c3743c
.global L01c3748d
.global L01c37490
.global L01c37c28
.global L01c37ee8
.global L01c37fd0
.global audio_pause_queue_drained
.global audio_task_set_input
.global audio_task_task
.global audio_task_warmup
.global biquad_coefficients_counter
.global biquad_coefficients_q28
.global biquad_generator_scaled_exp
.global capture_async_worker
.global capture_dispatch_capabilities
.global capture_dispatch_load
.global capture_dispatch_probe
.global capture_live_read64
.global dsp_audio_path_cached
.global dsp_audio_path_input
.global dsp_initialization_q16
.global dsp_stage_active
.global dsp_stage_capability
.global effect_construction_mode_shift
.global effect_construction_packed_bias
.global effect_construction_signature
.global effect_construction_tail_pointer
.global effect_enable_fade
.global effect_enable_tail_type
.global effect_model_construction_curve20_setup
.global effect_model_construction_curve_sample
.global effect_model_construction_curve_setup
.global effect_model_construction_curve_state
.global effect_model_construction_finite_clamp
.global effect_model_construction_frequency_response
.global effect_model_construction_level_exp
.global effect_model_construction_object_mode
.global effect_model_construction_object_record
.global effect_model_construction_percent
.global effect_model_construction_pitch_curve
.global effect_model_construction_pitch_increment
.global effect_model_construction_pitch_limit_valid
.global effect_model_construction_pole_exp
.global effect_parameter_lifecycle_resource_decode_sample
.global effect_parameter_lifecycle_resource_delay_state
.global effect_parameter_lifecycle_resource_encode_group
.global effect_parameter_lifecycle_resource_extra_size
.global effect_parameter_lifecycle_resource_fingerprint36
.global effect_parameter_lifecycle_resource_fingerprint37
.global effect_parameter_lifecycle_resource_mode_callback
.global effect_parameter_lifecycle_resource_reset
.global effect_parameter_lifecycle_resource_sum3
.global effect_parameter_lifecycle_resource_sum4
.global effect_parameter_support_active_word
.global effect_parameter_support_capability
.global effect_parameter_support_clamp2
.global effect_parameter_support_clamp3
.global effect_parameter_support_clear_halfwords
.global effect_parameter_support_extra
.global effect_parameter_support_pack
.global effect_parameter_support_ratio
.global effect_parameter_support_selector
.global effect_parameter_support_time_rule
.global effect_processing_capture_probe
.global effect_processing_extra_cost
.global effect_processing_ir_active
.global effect_relocation_has_layout
.global effect_relocation_rebase
.global effect_relocation_rebase_within
.global effect_setup_buffer_selector
.global effect_setup_default_mode
.global effect_setup_estimate_slot
.global effect_setup_group_eligible
.global effect_setup_group_fixed
.global effect_setup_has_mode
.global effect_setup_ir_fallback_cost
.global effect_setup_ir_partition_cost
.global effect_setup_layout29
.global effect_setup_mode_cost
.global effect_setup_next_mode
.global effect_setup_pool_full
.global effect_setup_stereo_extra_cost
.global interrupt_and_stack_calls_aligned_call
.global interrupt_and_stack_calls_clock_word_set
.global interrupt_and_stack_calls_timer_interrupt
.global ir_convolution_reset
.global ir_convolution_size
.global ir_installation_gain_clamp
.global ir_processing_wait
.global parameter_set_parameter_order
.global phase3_p3_low_power_process_wait
.global phase3_p7_go_mask_usb_updata
.global phase3_p7_low_power_enter_and_exit
.global phase3_p7_sys_clk_source_set
.global preset_application_services_budget
.global ram_callbacks_aligned_size
.global ram_callbacks_clock_job
.global ram_callbacks_empty_hook
.global ram_callbacks_halfword_sum
.global ram_callbacks_idle_watch
.global ram_callbacks_input_block
.global ram_callbacks_job_busy
.global ram_callbacks_link_check
.global ram_callbacks_link_status
.global ram_callbacks_link_words
.global ram_callbacks_mode_class
.global ram_callbacks_mode_value
.global ram_callbacks_mode_width
.global ram_callbacks_output_block
.global ram_callbacks_pll_set
.global ram_callbacks_post_job
.global ram_callbacks_signed_max
.global ram_callbacks_timer_start
.global ram_callbacks_wait_job
.global ram_callbacks_zero_leaf
.global sample_leaves_capture_idle
.global sdk_RC16M_udelay
.global sdk___hw_nv_timer_is_runnig
.global sdk_sys_clk_source_rc_clk_off
.global stereo_budget_listed_mask
.global stereo_budget_listed_routes
.global storage_control_bus_enter
.global storage_control_cache_lines
.global storage_control_cache_region
.global storage_control_device_erase
.global storage_control_device_program
.global storage_control_device_read
.global storage_control_identify
.global storage_control_status_apply
.global storage_control_status_capture
.global storage_control_translate
.global storage_coordination_irq_enter
.global storage_coordination_irq_leave
.global storage_fault_acquire
.global storage_fault_exchange
.global storage_fault_masked_register
.global storage_fault_read_register
.global storage_fault_release
.global storage_fault_write_register
.global storage_platform_clock
.global storage_platform_enter
.global storage_platform_interrupt
.global storage_platform_leave
.global storage_platform_peer_resume
.global storage_platform_peer_stop
.global ultrarig_ram_start
.include "ram/01c00000_storage_control.s"
.include "ram/01c008b4_vendor.s"
.include "ram/01c008c4_phase3_p7.s"
.include "ram/01c009e2_vendor.s"
.include "ram/01c00a02_phase3_p7.s"
.include "ram/01c00ab2_vendor.s"
.include "ram/01c00ac8_phase3_p7.s"
.include "ram/01c00ae2_vendor.s"
.include "ram/01c00af8_phase3_p7.s"
.include "ram/01c00b80_storage_control.s"
.include "ram/01c00bb2_vendor.s"
.include "ram/01c00e2e_storage_coordination.s"
.include "ram/01c00e62_vendor.s"
.include "ram/01c00e86_storage_fault.s"
.include "ram/01c00f72_vendor.s"
.include "ram/01c00fb6_phase3_p7.s"
.include "ram/01c00fdc_vendor.s"
.include "ram/01c01058_dsp_audio_path.s"
.include "ram/01c010e4_storage_platform.s"
.include "ram/01c01234_audio_task.s"
.include "ram/01c012d8_switched_high_pass.s"
.include "ram/01c01544_pattern_removal.s"
.include "ram/01c01690_block_leaves.s"
.include "ram/01c019d8_block_shift.s"
.include "ram/01c01c92_block_gain.s"
.include "ram/01c01e5e_audio_task.s"
.include "ram/01c02dbc_ram_callbacks.s"
.include "ram/01c03278_interrupt_and_stack_calls.s"
.include "ram/01c03392_ram_callbacks.s"
.include "ram/01c0344c_vendor.s"
.include "ram/01c03524_phase3_p7.s"
.include "ram/01c0367a_vendor.s"
.include "ram/01c0383e_phase3_p7.s"
.include "ram/01c040a8_vendor.s"
.include "ram/01c041dc_storage_platform.s"
.include "ram/01c04256_vendor.s"
.include "ram/01c042b0_phase3_p3.s"
.include "ram/01c04410_interrupt_and_stack_calls.s"
.include "ram/01c0444e_ram_callbacks.s"
.include "ram/01c04588_capture_async.s"
.include "ram/01c04774_ram_callbacks.s"
.include "ram/01c04862_storage_platform.s"
.include "ram/01c0486c_ram_callbacks.s"
.include "ram/01c04882_audio_pause.s"
.include "ram/01c048a4_sample_leaves.s"
.include "ram/01c048c2_ram_callbacks.s"
.include "ram/01c04928_interrupt_and_stack_calls.s"
.include "ram/01c049f0_ram_callbacks.s"
.include "ram/01c04a7a_capture_dispatch.s"
.include "ram/01c04b34_ram_callbacks.s"
.include "ram/01c04bac_capture_dispatch.s"
.include "ram/01c04c42_audio_task.s"
.include "ram/01c04cd8_ram_callbacks.s"
.include "ram/01c04cda_capture_async.s"
.include "ram/01c05118_audio_task.s"
.include "ram/01c05160_biquad_coefficients.s"
.include "ram/01c0516e_biquad_generator.s"
.include "ram/01c05182_biquad_coefficients.s"
.include "ram/01c051a2_biquad_chain.s"
.include "ram/01c0539c_dsp_initialization.s"
.include "ram/01c053bc_dsp_audio_path.s"
.include "ram/01c0558c_dsp_stage.s"
.include "ram/01c055a8_stereo_budget.s"
.include "ram/01c055d2_dsp_stage.s"
.include "ram/01c05860_stereo_budget.s"
.include "ram/01c0588e_effect_processing.s"
.include "ram/01c05d02_effect_setup.s"
.include "ram/01c05d40_audio_task.s"
.include "ram/01c05d4a_effect_setup.s"
.include "ram/01c05e14_ram_callbacks.s"
.include "ram/01c05e7e_preset_application_services.s"
.include "ram/01c05e88_ram_callbacks.s"
.include "ram/01c05eb0_ir_installation.s"
.include "ram/01c05ec6_effect_parameter_lifecycle.s"
.include "ram/01c05ed6_effect_model_construction.s"
.include "ram/01c05eec_effect_relocation.s"
.include "ram/01c05f1c_effect_setup.s"
.include "ram/01c05ff2_effect_parameter_lifecycle.s"
.include "ram/01c05ffa_effect_relocation.s"
.include "ram/01c06004_effect_model_construction.s"
.include "ram/01c06028_ram_callbacks.s"
.include "ram/01c06038_effect_setup.s"
.include "ram/01c060e6_effect_parameter_support.s"
.include "ram/01c060fa_effect_construction.s"
.include "ram/01c0611a_effect_model_construction.s"
.include "ram/01c06466_effect_parameter_support.s"
.include "ram/01c06490_effect_model_construction.s"
.include "ram/01c06514_effect_construction.s"
.include "ram/01c06554_effect_parameter_support.s"
.include "ram/01c065a4_effect_setup.s"
.include "ram/01c065b4_effect_parameter_support.s"
.include "ram/01c065e2_effect_parameter_lifecycle.s"
.include "ram/01c067e0_effect_parameter_support.s"
.include "ram/01c067ea_effect_parameter_lifecycle.s"
.include "ram/01c06926_effect_parameter_support.s"
.include "ram/01c069b0_parameter_set.s"
.include "ram/01c069c6_effect_enable.s"
.include "ram/01c06b2c_effect_integrity.s"
.include "ram/01c06c08_drive_glide.s"
.include "ram/01c06c58_delay_line.s"
.include "ram/01c06cb8_tap_oscillator.s"
.include "ram/01c06f3c_drive_glide.s"
.include "ram/01c06f84_delay_line.s"
.include "ram/01c0735e_effect_processing.s"
.include "ram/01c0767e_noise_gate.s"
.include "ram/01c07986_effect_resampling.s"
.include "ram/01c07a4c_drive_dispatch.s"
.include "ram/01c07bf0_effect_cases.s"
.include "ram/01c089e8_wet_mix.s"
.include "ram/01c08a76_effect_resampling.s"
.include "ram/01c08b34_effect_processing.s"
.include "ram/01c08b3e_effect_sample_processing.s"
.include "ram/01c08c76_effect_processing.s"
.include "ram/01c08c98_sample_leaves.s"
.include "ram/01c08d34_delay_reader.s"
.include "ram/01c08f80_looper_engine.s"
.include "ram/01c097b8_rate_leaves.s"
.include "ram/01c09932_ring_stages.s"
.include "ram/01c09a2e_rate_leaves.s"
.include "ram/01c09a7c_ring_stages.s"
.include "ram/01c09cda_rate_leaves.s"
.include "ram/01c09cfe_ring_stages.s"
.include "ram/01c09eaa_modulation.s"
.include "ram/01c09f22_rate_leaves.s"
.include "ram/01c09f3a_ring_stages.s"
.include "ram/01c0a774_rate_leaves.s"
.include "ram/01c0a7aa_ring_effect.s"
.include "ram/01c0af16_effect_type30_processing.s"
.include "ram/01c0b4b8_modulated_delay.s"
.include "ram/01c0b524_sample_leaves.s"
.include "ram/01c0b5d6_effect_sample_processing.s"
.include "ram/01c0be92_effect_type29_processing.s"
.include "ram/01c0deb6_effect_processing.s"
.include "ram/01c10818_dsp_stage.s"
.include "ram/01c11b00_dsp_dynamics_processing.s"
.include "ram/01c11d06_block_measurement.s"
.include "ram/01c11f46_ram_callbacks.s"
.include "ram/01c11f56_effect_processing.s"
.include "ram/01c11f66_dsp_stage.s"
.include "ram/01c11f76_effect_enable.s"
.include "ram/01c11faa_ir_processing.s"
.include "ram/01c123fa_ir_convolution.s"
.include "ram/01c12446_effect_processing.s"
.include "ram/01c1245c_ir_processing.s"
.include "ram/01c12556_capture_async.s"
.include "ram/01c12608_native_A2.s"
.include "ram/01c127de_capture_live.s"
.include "ram/01c12850_capture_dispatch.s"
.include "ram/01c12878_capture_live.s"
.include "ram/01c1296c_capture_dispatch.s"
.include "ram/01c129dc_capture_live.s"
.include "ram/01c13072_ram_callbacks.s"
.include "ram/01c13080_capture_async.s"
.include "ram/01c13082_capture_dispatch.s"
.include "ram/01c13088_ram_callbacks.s"
.include "ram/01c1308c_capture_dispatch.s"
.include "ram/01c1308e_ram_callbacks.s"
.include "ram/01c130b4_capture_live.s"
.include "ram/01c145fe_ir_processing.s"
.include "ram/01c15dec_biquad.s"
.include "ram/01c16222_soft_clip_drive.s"
.include "ram/01c16476_tilt_drive.s"
.include "ram/01c166d6_blended_drive.s"
.include "ram/01c16988_filtered_drive.s"
.include "ram/01c16bd4_crossover_drive.s"
.include "ram/01c16f0c_shaped_drive.s"
.include "ram/01c1721c_asymmetric_drive.s"
.include "ram/01c1746e_cubic_drive.s"
.include "ram/01c17718_waveshapers.s"
.include "ram/01c179ae_two_stage_drive.s"
.include "ram/01c17ca2_waveshapers.s"
.include "ram/01c17eba_two_pass_drive.s"
.include "ram/01c1827a_waveshapers.s"
.include "ram/01c184a4_drive_glide.s"
.include "ram/01c185aa_blend_leaves.s"
.include "ram/01c188c2_modulated_delay.s"
.include "ram/01c18f90_effect_sample_processing.s"
.include "ram/01c1958e_effect_signal.s"
.include "ram/01c19bee_effect_processing.s"
.include "ram/01c19d36_dsp_audio_path.s"
.include "ram/01c19ede_effect_processing.s"
.include "ram/01c19efa_sample_leaves.s"
.include "ram/01c19fba_noise_gate.s"
.include "ram/01c1a14c_dsp_stage.s"
.include "ram/01c1a2c4_block_measurement.s"
.include "ram/01c1a636_dsp_dynamics_processing.s"
.include "ram/01c1ab40_switched_high_pass.s"
.include "ram/01c1ae86_effect_resampling.s"
.include "ram/01c1b582_resampling_kernels.s"
.include "ram/01c1b6f4_antialiased_clip.s"
.include "ram/01c1b8d8_cubic_clip.s"
.include "ram/01c1bb24_asymmetric_clip.s"
.include "ram/01c1be10_scaled_clip.s"
.include "ram/01c1c144_polynomial_clip.s"
.include "ram/01c1c512_input_stage.s"
.include "ram/01c1c6a8_clamp_stage.s"
.include "ram/01c1c7d6_halved_clamp.s"
.include "ram/01c1c91e_mix_stage.s"
.include "ram/01c1caa4_tone_stage.s"
.include "ram/01c1cc0e_band_stage.s"
.include "ram/01c1cd12_drive_stage.s"
.include "ram/01c1cf3c_shelf_stage.s"
.include "ram/01c1d04e_gain_stage.s"
.include "ram/01c1d130_smooth_stage.s"
.include "ram/01c1d1ee_tilt_stage.s"
.include "ram/01c1d3b6_blend_stage.s"
.include "ram/01c1d4fc_filter_stage.s"
.include "ram/01c1d5cc_contour_stage.s"
.include "ram/01c1d74a_upsampler.s"
.include "ram/01c1da72_rate_leaves.s"
.include "ram/01c1dab2_diffusion_kernels.s"
.include "ram/01c1dd46_line_mixers.s"
.include "ram/01c1e3de_effect_type29_processing.s"
.include "ram/01c1e4a6_effect_type30_processing.s"
.include "ram/01c1e620_diffusion_kernels.s"
.include "ram/01c1e780_filter_kernels.s"
.include "ram/01c1ea96_diffusion_kernels.s"
.include "ram/01c1ebcc_filter_kernels.s"
.include "ram/01c1ecc4_resampling_kernels.s"
.include "ram/01c1ee40_effect_signal.s"
.include "ram/01c1f088_data.s"

; The bss: 97,604 bytes cleared by the start-up, placed by app.ld after the RAM image.
; A label marks each address the code or the data refers to.
.section .bss,"aw",@nobits
L01c2030c:
    .space 4196
L01c21370:
    .space 4
L01c21374:
    .space 4
L01c21378:
    .space 128
L01c213f8:
    .space 4
L01c213fc:
    .space 4
L01c21400:
    .space 15
L01c2140f:
    .space 32
L01c2142f:
    .space 33
L01c21450:
    .space 4
L01c21454:
    .space 1
L01c21455:
    .space 7
L01c2145c:
    .space 104
L01c214c4:
    .space 592
L01c21714:
    .space 4
L01c21718:
    .space 4
L01c2171c:
    .space 8
L01c21724:
    .space 526
L01c21932:
    .space 14
L01c21940:
    .space 8
L01c21948:
    .space 4
L01c2194c:
    .space 4
L01c21950:
    .space 4
L01c21954:
    .space 8
L01c2195c:
    .space 24
L01c21974:
    .space 20
L01c21988:
    .space 152
L01c21a20:
    .space 17
L01c21a31:
    .space 151
L01c21ac8:
    .space 12
L01c21ad4:
    .space 80
L01c21b24:
    .space 4
L01c21b28:
    .space 68
L01c21b6c:
    .space 16
L01c21b7c:
    .space 184
L01c21c34:
    .space 32
L01c21c54:
    .space 4
L01c21c58:
    .space 20
L01c21c6c:
    .space 4
L01c21c70:
    .space 8
L01c21c78:
    .space 32
L01c21c98:
    .space 4
L01c21c9c:
    .space 20
L01c21cb0:
    .space 4
L01c21cb4:
    .space 4
L01c21cb8:
    .space 2020
L01c2249c:
    .space 4
L01c224a0:
    .space 8
L01c224a8:
    .space 2048
L01c22ca8:
    .space 2048
L01c234a8:
    .space 2048
L01c23ca8:
    .space 704
L01c23f68:
    .space 704
L01c24228:
    .space 4
L01c2422c:
    .space 300
L01c24358:
    .space 200
L01c24420:
    .space 256
L01c24520:
    .space 128
L01c245a0:
    .space 324
L01c246e4:
    .space 4
L01c246e8:
    .space 4
L01c246ec:
    .space 164
L01c24790:
    .space 1484
L01c24d5c:
    .space 1588
L01c25390:
    .space 4
L01c25394:
    .space 160
L01c25434:
    .space 4
L01c25438:
    .space 420
L01c255dc:
    .space 256
L01c256dc:
    .space 1460
L01c25c90:
    .space 80
L01c25ce0:
    .space 8
L01c25ce8:
    .space 8
L01c25cf0:
    .space 4
L01c25cf4:
    .space 4
L01c25cf8:
    .space 480
L01c25ed8:
    .space 4
L01c25edc:
    .space 328
L01c26024:
    .space 24
L01c2603c:
    .space 4
L01c26040:
    .space 80
L01c26090:
    .space 624
L01c26300:
    .space 80
L01c26350:
    .space 4
L01c26354:
    .space 12
L01c26360:
    .space 1136
L01c267d0:
    .space 4
L01c267d4:
    .space 4
L01c267d8:
    .space 8
L01c267e0:
    .space 80
L01c26830:
    .space 4
L01c26834:
    .space 4
L01c26838:
    .space 4
L01c2683c:
    .space 4
L01c26840:
    .space 4
L01c26844:
    .space 4
L01c26848:
    .space 4
L01c2684c:
    .space 4
L01c26850:
    .space 4
L01c26854:
    .space 4
L01c26858:
    .space 4
L01c2685c:
    .space 2
L01c2685e:
    .space 2
L01c26860:
    .space 4
L01c26864:
    .space 4
L01c26868:
    .space 16
L01c26878:
    .space 4
L01c2687c:
    .space 4
L01c26880:
    .space 4
L01c26884:
    .space 2
L01c26886:
    .space 2
L01c26888:
    .space 4
L01c2688c:
    .space 4
L01c26890:
    .space 74
L01c268da:
    .space 22
L01c268f0:
    .space 56
L01c26928:
    .space 8
L01c26930:
    .space 548
L01c26b54:
    .space 512
L01c26d54:
    .space 308
L01c26e88:
    .space 56
L01c26ec0:
    .space 56
L01c26ef8:
    .space 8
L01c26f00:
    .space 8
L01c26f08:
    .space 60
L01c26f44:
    .space 160
L01c26fe4:
    .space 128
L01c27064:
    .space 53
L01c27099:
    .space 183
L01c27150:
    .space 180
L01c27204:
    .space 1328
L01c27734:
    .space 80
L01c27784:
    .space 296
L01c278ac:
    .space 544
L01c27acc:
    .space 520
L01c27cd4:
    .space 1
L01c27cd5:
    .space 9211
L01c2a0d0:
    .space 2064
L01c2a8e0:
    .space 3072
L01c2b4e0:
    .space 2568
L01c2bee8:
    .space 264
L01c2bff0:
    .space 304
L01c2c120:
    .space 256
L01c2c220:
    .space 2
L01c2c222:
    .space 6
L01c2c228:
    .space 7672
L01c2e020:
    .space 84
L01c2e074:
    .space 1324
L01c2e5a0:
    .space 1
L01c2e5a1:
    .space 3583
L01c2f3a0:
    .space 768
L01c2f6a0:
    .space 768
L01c2f9a0:
    .space 152
L01c2fa38:
    .space 3552
L01c30818:
    .space 548
L01c30a3c:
    .space 512
L01c30c3c:
    .space 312
L01c30d74:
    .space 272
L01c30e84:
    .space 2048
L01c31684:
    .space 512
L01c31884:
    .space 512
L01c31a84:
    .space 528
L01c31c94:
    .space 528
L01c31ea4:
    .space 264
L01c31fac:
    .space 512
L01c321ac:
    .space 1536
L01c327ac:
    .space 1536
L01c32dac:
    .space 2
L01c32dae:
    .space 2
L01c32db0:
    .space 64
L01c32df0:
    .space 154
L01c32e8a:
    .space 278
L01c32fa0:
    .space 184
L01c33058:
    .space 312
L01c33190:
    .space 176
L01c33240:
    .space 224
L01c33320:
    .space 464
L01c334f0:
    .space 288
L01c33610:
    .space 480
L01c337f0:
    .space 480
L01c339d0:
    .space 16
L01c339e0:
    .space 32
L01c33a00:
    .space 768
L01c33d00:
    .space 56
L01c33d38:
    .space 408
L01c33ed0:
    .space 432
L01c34080:
    .space 64
L01c340c0:
    .space 4
L01c340c4:
    .space 4
L01c340c8:
    .space 4
L01c340cc:
    .space 164
L01c34170:
    .space 4
L01c34174:
    .space 4
L01c34178:
    .space 4
L01c3417c:
    .space 4
L01c34180:
    .space 4
L01c34184:
    .space 4
L01c34188:
    .space 4
L01c3418c:
    .space 4
L01c34190:
    .space 4
L01c34194:
    .space 4
L01c34198:
    .space 4
L01c3419c:
    .space 4
L01c341a0:
    .space 4
L01c341a4:
    .space 4
L01c341a8:
    .space 4
L01c341ac:
    .space 16
L01c341bc:
    .space 4
L01c341c0:
    .space 4
L01c341c4:
    .space 512
L01c343c4:
    .space 4
L01c343c8:
    .space 4
L01c343cc:
    .space 4
L01c343d0:
    .space 4
L01c343d4:
    .space 4
L01c343d8:
    .space 64
L01c34418:
    .space 4
L01c3441c:
    .space 4
L01c34420:
    .space 4
L01c34424:
    .space 4
L01c34428:
    .space 4
L01c3442c:
    .space 4
L01c34430:
    .space 4
L01c34434:
    .space 4
L01c34438:
    .space 4
L01c3443c:
    .space 4
L01c34440:
    .space 4
L01c34444:
    .space 4
L01c34448:
    .space 4
L01c3444c:
    .space 4
L01c34450:
    .space 4
L01c34454:
    .space 4
L01c34458:
    .space 4
L01c3445c:
    .space 4
L01c34460:
    .space 4
L01c34464:
    .space 4
L01c34468:
    .space 4
L01c3446c:
    .space 4
L01c34470:
    .space 4
L01c34474:
    .space 20
L01c34488:
    .space 1
L01c34489:
    .space 1
L01c3448a:
    .space 1
L01c3448b:
    .space 1
L01c3448c:
    .space 1
L01c3448d:
    .space 3
L01c34490:
    .space 4
L01c34494:
    .space 4
L01c34498:
    .space 4
L01c3449c:
    .space 12
L01c344a8:
    .space 4
L01c344ac:
    .space 4
L01c344b0:
    .space 4
L01c344b4:
    .space 620
L01c34720:
    .space 20
L01c34734:
    .space 20
L01c34748:
    .space 20
L01c3475c:
    .space 20
L01c34770:
    .space 20
L01c34784:
    .space 4
L01c34788:
    .space 4
L01c3478c:
    .space 80
L01c347dc:
    .space 64
L01c3481c:
    .space 80
L01c3486c:
    .space 1024
L01c34c6c:
    .space 164
L01c34d10:
    .space 8
L01c34d18:
    .space 928
L01c350b8:
    .space 4096
L01c360b8:
    .space 768
L01c363b8:
    .space 4096
L01c373b8:
    .space 44
L01c373e4:
    .space 40
L01c3740c:
    .space 48
L01c3743c:
    .space 80
L01c3748c:
    .space 1
L01c3748d:
    .space 3
L01c37490:
    .space 1944
L01c37c28:
    .space 704
L01c37ee8:
    .space 232
L01c37fd0:
    .space 128
