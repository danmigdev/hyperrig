"""Offline board-audio audit for an integral UltraRig G -> HyperRig MINI port.

Produces decoded preimages and patch requirements, never patched firmware.
The MINI stock firmware is an evidence source, not the candidate DSP backend.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hyperrig.jieli import unpack_app, unpack_fwsc
from tools.disassemble import codec, relative_target, table

BASE = 0x02000000


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def checked(path, digest):
    raw = path.read_bytes()
    if sha(raw) != digest:
        raise ValueError('source identity changed: ' + str(path))
    return raw


def main():
    manifest = json.loads((ROOT / 'research/input-manifest.json').read_text(encoding='utf-8'))
    g_source = next(v for v in manifest['firmware_images'] if v['file'] == 'm571_g_app.bin')
    g, _, _ = unpack_app(checked(ROOT / g_source['path'], g_source['sha256']))
    mini_digest = manifest['tank_mini']['sha256']
    _, contents = unpack_fwsc(checked(ROOT / 'artifacts/tank-mini/TANK-MINI.fwsc', mini_digest))
    mini, _, _ = unpack_app(contents['flash.bin'][0x4000:])
    isa = table.load()

    def region(blob, start, end, name, decode=True):
        data = blob[start - BASE:end - BASE]
        if len(data) != end - start:
            raise ValueError('out-of-range evidence: ' + name)
        result = {'name': name, 'cpu_start': hex(start), 'cpu_end_exclusive': hex(end),
                  'app_area_offset': hex(start - BASE), 'app_bin_offset': hex(start - BASE - 0x120),
                  'logical_flash_offset': hex(start - BASE + 0x4000), 'bytes': len(data),
                  'sha256': sha(data), 'preimage_hex': data.hex()}
        if decode:
            rows, address = [], start
            while address < end:
                decoded = codec.decode(isa, blob, address - BASE)
                if decoded is None:
                    raise ValueError('undecoded instruction at ' + hex(address))
                instruction, fields, size = decoded
                if address + size > end:
                    raise ValueError('region ends inside instruction: ' + name)
                text = codec.format(instruction, fields)
                row = {'address': hex(address), 'bytes': size, 'text': text}
                target = relative_target(address, size, text)
                if target is not None:
                    row['direct_target'] = hex(target)
                rows.append(row)
                address += size
            result['instructions'] = rows
        return result

    g_regions = [region(g, a, b, n) for a, b, n in (
        (0x020053a4, 0x020053c6, 'G board-specific preamble'),
        (0x020053c6, 0x020053d0, 'G ALNK clock pre-enable'),
        (0x020053d0, 0x020053ee, 'G iis_platform_data setup'),
        (0x020053f6, 0x02005422, 'G IRQ11, driver, rate and channel start calls'),
        (0x02005148, 0x02005194, 'G nominal 48000 setter and ALNK0 clock fields'),
        (0x0200541e, 0x02005422, 'G channel-start call: post-start hook site'),
        (0x02001864, 0x0200187c, 'G GPIO bank resolver'),
        (0x02002bd8, 0x02002bec, 'G nominal timing helper'),
        (0x02015858, 0x020158c2, 'G panel serializer conflicts with MINI codec bus'),
        (0x0201755c, 0x02017570, 'G panel serializer caller and cache check'),
    )]
    mini_regions = [region(mini, a, b, n) for a, b, n in (
        (0x02006960, 0x020069bc, 'MINI codec bus GPIO initialization'),
        (0x02006dce, 0x02006e08, 'MINI codec address/write and 22-record initializer'),
        (0x02006e36, 0x02006e58, 'MINI dual ALNK clock selector'),
        (0x0200717c, 0x0200718c, 'MINI codec init call before audio task'),
        (0x02007214, 0x02007244, 'MINI PA9 sequence around codec/ALNK start'),
    )]
    board = g_regions[0]
    calls = [v for v in board['instructions'] if v['text'].startswith('call ')]
    if [r.get('direct_target') for r in calls] != ['0x2004998'] * 4:
        raise ValueError('G board preamble no longer consists of four GPIO output calls')
    literals = [v['text'] for v in board['instructions']]
    for required in ('r0 = 32', 'r0 = 33', 'r0 = 37', 'r0 = 9', 'r6 = 1'):
        if required not in literals:
            raise ValueError('G board literal changed: ' + required)
    if g_regions[5]['instructions'][0].get('direct_target') != '0x2005194':
        raise ValueError('G post-start hook call changed')
    panel_call = region(g, 0x02017568, 0x0201756c, 'G panel serializer call')
    if panel_call['preimage_hex'] != 'bfea76f1' or panel_call['instructions'][0].get('direct_target') != '0x2015858':
        raise ValueError('G panel writer call changed')
    rate_text = '\n'.join(v['text'] for v in g_regions[4]['instructions'])
    for required in ('r2 = 48000', '[r2+0] |= 0x2000000', '[r2+0] |= 0x100', '[r2+0] &= 0xFFFFFDFF'):
        if required not in rate_text:
            raise ValueError('G 48000 clock contract changed: ' + required)
    g_pins = list(g[0x35360:0x35367])
    mini_pins = list(mini[0x35e27:0x35e2e])
    if g_pins != [7, 8, 9, 10, 4, 5, 6] or mini_pins != [4, 5, 6, 7, 8, 9, 10]:
        raise ValueError('ALNK pin tables changed')
    codec_table = mini[0x35e35:0x35e35 + 88]
    if sha(codec_table) != '1032b05743d45148e6aecd2bdc6834ab54804d154362c545d9949a49461c415d':
        raise ValueError('MINI codec script changed')
    records = [{'register': f'0x{r:04x}', 'value': f'0x{v:04x}'}
               for r, v in struct.iter_unpack('>HH', codec_table)]
    # The GPIO resolver indexes this table by pin>>4, not an inferred package map.
    banks = struct.unpack_from('<9I', g, 0x3a2a4)
    if banks[0] != 0x50000 or banks[2] != 0x50080:
        raise ValueError('G GPIO bank map changed')
    report = {
        'project': 'HyperRig', 'scope': 'Integral original G firmware port; MINI stock is hardware evidence only',
        'sources': {'G_container_path': g_source['path'], 'G_container_sha256': g_source['sha256'],
                    'G_decoded_sha256': sha(g), 'MINI_fwsc_sha256': mini_digest,
                    'MINI_decoded_sha256': sha(mini)},
        'address_space': 'Preimages are decoded app-area bytes, not encrypted raw NOR bytes. Logical flash is app-area offset +0x4000.',
        'g_regions': g_regions, 'mini_regions': mini_regions,
        'shared_alnk': {'controller_base': '0x00012e00', 'irq': 11, 'G_pin_group_index': 0,
            'MINI_pin_group_index': 1, 'G_table_row': g_pins, 'MINI_table_row': mini_pins,
            'clock_gpio_numbers': [4, 5, 6], 'tx0_gpio': 7, 'rx1_gpio': 8,
            'channels': {'TX': 0, 'RX': 1}, 'data_bits': 24, 'slot_bits': 32,
            'buffer_bytes_per_channel': 1024, 'half_frames': 64, 'length_register': 128,
            'G_con0_before_enable_derived': '0x0180', 'MINI_con0_before_enable': '0x0180',
            'G_con1_after_enable_derived': '0x00d5', 'MINI_con1_after_enable': '0x00d5',
            'G_con3_derived': '0x83', 'MINI_con3_44100_or_48000': '0x83',
            'electrical_frame_measurement': False, 'pin_table_patch_needed': False},
        'clock_comparison': {'G_label': 48000, 'MINI_stock_label': 44100,
            'G_master_CLK_CON2': '(old | 0x100) & ~0x200',
            'MINI_48000_CLK_CON2': '(old & ~0xf00) | 0x500',
            'ALNK0_bits_9_8_in_both_48000_paths': 1,
            'difference_bits_11_10': 'MINI also selects ALNK1; G preserves it. ALNK0 is used here.',
            'G_explicit_PLL_CON1_output_enable': '0x02000000',
            'automatic_clock_patch_recommended': False,
            'physical_48000_verified': False,
            'nominal_divider_hypothesis': '160000000/(13*256) = 48076.923 Hz, not measured'},
        'codec': {'MINI_bus': {'SDA': 'PA1', 'SCL': 'PA2', 'address_byte': '0x36',
                'wire_record': '16-bit register then 16-bit data, big endian',
                'mode': 'stock drives high and low; SDA released for ACK only'},
            'table': region(mini, 0x02035e35, 0x02035e8d, 'MINI codec 22-record script', decode=False),
            'records': records, 'same_table_occurs_in_G': codec_table in g,
            'first_8_table_bytes_occur_in_G': codec_table[:8] in g,
            'G_audio_start_scope': 'No MINI codec replay in the decoded G setup path; absence of a byte pattern is not proof about every G path.',
            'register_map_compatible_with': 'NAU88L21/NAU88L21C', 'physical_identity_confirmed': False,
            'stock_osr': 256, 'rate_policy': 'Do not silently replace stock OSR or claim 48 kHz qualified from register ACK alone.'},
        'board_gpio': {'G_audio_start': {'PC0': 1, 'PC1': 1, 'PC5': 1, 'PA9': 0},
            'G_gpio_bank_table_cpu': '0x0203a2a4', 'G_port_a': hex(banks[0]), 'G_port_c': hex(banks[2]),
            'MINI_sequence': ['PA9=0', '100000 nop-loop iterations', 'codec init then ALNK start',
                              '100000 nop-loop iterations', 'PA9=1'],
            'G_PC0_PC1_PC5_electrical_roles_known': False, 'PA9_analog_mute_identity_proven': False,
            'delay_microseconds_calibrated': False},
        'patch_requirements': [
            {'site': 'G panel serializer call', 'cpu': '0x02017568', 'span_bytes': 4,
             'action': 'Replace or suppress the G PA0..PA3 serializer before enabling the MINI codec bus. See the separate panel port audit.',
             'preimage_hex': panel_call['preimage_hex'],
             'requirements': ['The runtime writer toggles PA2 and finally pulls PA1 low; this is a proven conflict, not merely unresolved ownership.',
                 'An app-level command filter does not disable the firmware panel task.',
                 'A diagnostic no-op alone does not provide the final MINI panel functionality.']},
            {'site': 'G board-specific preamble', 'cpu': '0x020053a4', 'span_bytes': 34,
             'action': 'Replace G-specific PC0/PC1/PC5 writes with MINI board initialization/codec-bus hook; retain r6=1 and normal callee-saved ABI.',
             'requirements': ['Keep PA9 low until codec transaction and audio start policy succeeds.',
                 'Use a G-owned/decoded system clock for bus delays; never reference MINI RAM global0x01c1e32c.',
                 'Resolve PA1/PA2 ownership and GPIO locking against G panel/background tasks.',
                 'New code/data placement and error branch must be linked and verified before patching.']},
            {'site': 'G channel-start call: post-start hook site', 'cpu': '0x0200541e', 'span_bytes': 4,
             'action': 'Preserve original G0x02005194 channel start, then perform the MINI post-start delay/PA9 transition only on successful board setup.',
             'requirements': ['Retain all original G DSP/RTOS/IRQ processing.', 'Define failure cleanup before enabling an analog output.']},
            {'site': 'G nominal 48000 setter and ALNK0 clock fields', 'cpu': '0x02005148', 'span_bytes': 76,
             'action': 'Inspection point only: preserve G ALNK0 rate selection; difference0x100/0x500 is not an ALNK0 mismatch.'},
        ],
        'panel': {'physical_mapping_complete': False,
            'known_requirement': 'G four-switch/knob assumptions must be mapped to MINI independently; app logical IDs do not identify GPIO.',
            'proven_codec_bus_conflict': {'writer': '0x02015858', 'caller': panel_call,
                'gpio_bank': '0x00050000', 'pins': ['PA0', 'PA1', 'PA2', 'PA3'],
                'serializer_bits': 29, 'clock': 'PA2', 'inverted_data': 'PA3',
                'final_line_actions': ['PA0 high', 'PA1 low'],
                'cache_address': '0x01c1f208', 'audio_overlap': ['PA1=SDA', 'PA2=SCL']},
            'separate_panel_audit': 'research/mini-panel-port.json',
            'remaining_audio_conflicts': ['Other full-firmware GPIO/clock owners and lock policy', 'PC0/PC1/PC5 roles on MINI']},
        'primary_clock_reference': {
            'url': 'https://raw.githubusercontent.com/amitv87/fw-AC79_AIoT_SDK/ffbb2a8d925682ba6880d643a83a63ee0691ec09/include_lib/driver/cpu/wl82/clock_hw.h',
            'sha256': 'ae1ea1b672b3855f6b0e2378d9ee1583e1b87614ed617db3d41f001681f855ae',
            'scope': 'ALNK0 SEL/EN8/9 and ALNK1 SEL/EN10/11 names in #if0; corroborated by the pinned SDK iis_set_sample_rate bitcode.',
            'documentary_only': True},
        'existing_evidence': ['research/audio-map.json', 'research/mini-codec.json', 'research/mini-clock.json'],
        'firmware_patched': False, 'hardware_accessed': False,
        'verifier_sha256': sha(Path(__file__).read_bytes()),
    }
    (ROOT / 'research/mini-audio-port.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'shared_ALNK0': report['shared_alnk'],
                      'patch_sites': report['patch_requirements'], 'hardware_accessed': False}, indent=2))


if __name__ == '__main__':
    main()
