"""Offline image/order evidence checks; no hardware classes or commands."""
import copy
import struct
import unittest

from tools import inspect_mini_installed as inspector


def fixture():
    stock = b'\x35' * inspector.CAPACITY
    candidate = bytearray(stock[inspector.APP_START:inspector.APP_END])
    candidate[:4096] = b'\x45' * 4096
    candidate[4096:8192] = b'\x67' * 4096
    candidate = bytes(candidate)
    observed = stock[:inspector.APP_START] + candidate + stock[inspector.APP_END:]
    return stock, stock, candidate, observed


def evidence(preimage, candidate, order):
    journal, trace = [], []
    for cdb, data_hash, expected_reply in inspector.expected_stateful_commands(preimage, candidate, order):
        opcode = int.from_bytes(cdb[:2], 'big')
        address = int.from_bytes(cdb[2:6] if opcode == 0xFC7A else cdb[10:14], 'big')
        if opcode == 0xFB7C:
            reply = b''
        elif opcode == 0xFD87:
            reply = candidate[address - inspector.APP_START:address - inspector.APP_START + 256]
        else:
            reply = cdb[:2] + bytes(14)
        digest = inspector.sha(reply)
        assert expected_reply is None or digest == expected_reply
        journal.extend(({'event':'command_intent', 'opcode':f'{opcode:04x}',
                         'cdb_hex':cdb.hex(), 'data_out_sha256':data_hash},
                        {'event':'command_reply', 'opcode':f'{opcode:04x}',
                         'sha256':digest, 'bytes':len(reply)}))
        trace.extend(({'stage':'writer', 'state':'before', 'cdb':cdb.hex()},
                      {'stage':'writer', 'state':'after', 'cdb':cdb.hex(),
                       'response_bytes':len(reply), 'response_sha256':digest, 'response_hex':reply.hex()}))
        if opcode in (0xFD87, 0xFC7D, 0xFC80):
            width = 4096 if opcode == 0xFC80 else 256
            raw = candidate[address - inspector.APP_START:address - inspector.APP_START + width]
            event = {0xFD87:'page_echo_verified', 0xFC7D:'page_program_verified', 0xFC80:'sector_verified'}[opcode]
            entry = {'event':event, 'address':address, 'sha256':inspector.sha(raw)}
            if width == 4096: entry['program_page_order'] = inspector.page_order(address)
            journal.append(entry)
    return journal, trace


class InstalledInspectorTests(unittest.TestCase):
    def test_complete_NOR_and_external_regions_compared_byte_for_byte(self):
        stock, before, candidate, observed = fixture()
        result = inspector.compare_nor(stock, before, candidate, observed)
        self.assertEqual(result['sector_order'], [0x5000, 0x4000])
        self.assertEqual(sum(x['bytes'] for x in result['preserved_regions']), inspector.CAPACITY - len(candidate))
        self.assertEqual(len(result['already_matching_sectors']), 124)

    def test_modified_external_regions_or_candidate_page_are_rejected(self):
        stock, before, candidate, observed = fixture()
        for offset in (0, 0x3FFF, 0x4000, 0x81FFF, 0x82000, 0xBE000, 0xBF000, 0xFF000, 0xFFFFF):
            changed = bytearray(observed);changed[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                inspector.compare_nor(stock, before, candidate, bytes(changed))

    def test_preimage_outside_app_must_match_unit_backup(self):
        stock, before, candidate, observed = fixture()
        changed = bytearray(before);changed[0xBE000] ^= 1
        with self.assertRaises(ValueError): inspector.compare_nor(stock, bytes(changed), candidate, observed)

    def test_exact_staging_echo_erase_program_finish_header_last(self):
        _, before, candidate, _ = fixture();order = [0x5000, 0x4000]
        journal, trace = evidence(before, candidate, order)
        result = inspector.inspect_history(journal, trace, before, candidate, order)
        self.assertEqual((result['erase_commands'], result['program_commands'], result['expected_WREN_count']), (2, 32, 34))
        self.assertEqual(result['program_order'][-16:], list(range(0x4100, 0x5000, 256)) + [0x4000])
        self.assertTrue(result['header_sector_last'] and result['header_page_last'])

    def test_fifth_install_54_sector_geometry_and_counters(self):
        stock = b'\x35' * inspector.CAPACITY
        candidate = b'\x67' * (inspector.APP_END - inspector.APP_START)
        before = bytearray(stock)
        before[0x5000:0x4DA00] = candidate[0x1000:0x49A00]
        before[0x4DA00:0x4E000] = b'\xff' * 0x600
        before = bytes(before)
        observed = stock[:0x4000] + candidate + stock[0x82000:]
        images = inspector.compare_nor(stock, before, candidate, observed)
        order = list(range(0x4D000, 0x82000, 4096)) + [0x4000]
        self.assertEqual(images['sector_order'], order)
        self.assertEqual(len(images['already_matching_sectors']), 72)
        journal, trace = evidence(before, candidate, order)
        result = inspector.inspect_history(journal, trace, before, candidate, order)
        self.assertEqual((result['erase_commands'], result['program_commands'], result['expected_WREN_count']),
                         (54, 864, 918))
        self.assertEqual(result['program_order'][-1], 0x4000)
        self.assertEqual(2 * len(candidate) + 40960 * len(order), 3244032)

    def test_changed_stage_payload_or_echo_response_rejected(self):
        _, before, candidate, _ = fixture();order = [0x5000, 0x4000]
        for opcode, event, field in (('fb7c','command_intent','data_out_sha256'), ('fd87','command_reply','sha256')):
            journal, trace = evidence(before, candidate, order)
            target = next(x for x in journal if x['event'] == event and x['opcode'] == opcode)
            target[field] = '0' * 64
            with self.subTest(opcode=opcode), self.assertRaises(ValueError):
                inspector.inspect_history(journal, trace, before, candidate, order)

    def test_duplicate_mutation_or_missing_reply_is_rejected(self):
        _, before, candidate, _ = fixture();order = [0x5000, 0x4000]
        for mode in ('duplicate', 'missing'):
            journal, trace = evidence(before, candidate, order)
            index = next(i for i, x in enumerate(journal) if x['event']=='command_intent' and x['opcode']=='fc7b')
            if mode == 'duplicate': journal[index:index] = copy.deepcopy(journal[index:index+2])
            else: del journal[index+1]
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                inspector.inspect_history(journal, trace, before, candidate, order)

    def test_header_first_or_out_of_range_sector_rejected(self):
        _, before, candidate, _ = fixture()
        journal, trace = evidence(before, candidate, [0x5000, 0x4000])
        for order in ([0x4000,0x5000], [0x5000,0x5000,0x4000], [0x3000,0x4000]):
            with self.subTest(order=order), self.assertRaises(ValueError):
                inspector.inspect_history(journal, trace, before, candidate, order)

    def test_transport_mutation_failure_not_hidden_by_successful_journal(self):
        _, before, candidate, _ = fixture();order = [0x5000, 0x4000]
        journal, trace = evidence(before, candidate, order)
        row = next(x for x in trace if x['state']=='after' and x['cdb'].startswith('fc7d'))
        row.update(state='error', native_transfer={'win32_error':31})
        with self.assertRaises(ValueError): inspector.inspect_history(journal, trace, before, candidate, order)

    def test_read_query_failure_is_reported_but_never_counted_as_mutation(self):
        _, before, candidate, _ = fixture();order = [0x5000, 0x4000]
        journal, trace = evidence(before, candidate, order)
        command = 'fc7e' + 'ff' * 14
        trace.extend(({'state':'before','stage':'writer','cdb':command},
                      {'state':'error','stage':'writer','cdb':command,'native_transfer':{'win32_error':31}}))
        result = inspector.inspect_history(journal, trace, before, candidate, order)
        self.assertEqual(result['read_query_errors'], 1)
        self.assertEqual(result['program_commands'], 32)


if __name__ == '__main__': unittest.main()
