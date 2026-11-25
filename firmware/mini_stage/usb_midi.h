/* SPDX-License-Identifier: MIT */
/* From upstream/m-bootloader (include/usb_midi.h); see THIRD_PARTY.md. */
#ifndef HYPERRIG_STAGE_USB_MIDI_H
#define HYPERRIG_STAGE_USB_MIDI_H
#include <stdbool.h>
#include <stdint.h>
void usb_midi_start(void);
void usb_midi_poll(void);
bool usb_midi_configured(void);
/* Sends one whole F0..F7 message, polling until it has gone or the host has gone. */
void usb_midi_send(const uint8_t *data, uint32_t size);
void usb_midi_stop(void);
/* The loader's: one byte of a SysEx message from the host. */
void hrs_midi_byte(uint8_t byte);
#endif
