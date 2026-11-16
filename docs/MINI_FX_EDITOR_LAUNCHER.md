# HyperRig MINI FX editor

Open `tools/launch_hyperrig_editor.cmd` by double-clicking it. The existing `tools/launch_mini_fx_editor.cmd` shortcut now opens the same English product. It starts an isolated Edge window and a temporary localhost server, without UAC. The launcher dismisses the introductory tour using a real click and clicks Connect once. Select **Tank-M HyperRig (COM3)** in the browser's USB serial chooser. The editor then performs its real PING and initial reads.

The product bundle is `build/hyperrig-mini-english-editor`, derived from the preserved `build/hyperrig-mini-fx-editor` baseline. Its USB policy enables volume, preset save/reload, and effect add/parameter/enable/remove (`GAIN`, `PLOAD`, `PSAVE`, `SNAPSAVE`, `FXA`, `FXP`, `FXE`, `FXR`). Effect insertion is limited to the supported serial append locations. Firmware updates, routing changes, bulk operations and BLE writes are not granted. Qualification uses the real retained-preset, effect benchmark and removal evidence; it does not claim that every effect parameter or acoustic latency has been tested. English UI and GitHub reporting are checked offline as described in [ENGLISH_PRODUCT.md](ENGLISH_PRODUCT.md).

Offline check and an explicitly named session:

```powershell
python tools/launch_hyperrig_editor.py --check-only
python tools/launch_hyperrig_editor.py --execute --output build/hyperrig-editor-session-new
```

Keep only one editor connected to the MINI. To close a named session with an observed native port close and server shutdown:

```powershell
python tools/launch_hyperrig_editor.py --close-session build/hyperrig-editor-session-new
```

Closing the browser also stops the temporary server. An observation error during manual window closure concerns the host's ability to observe cleanup; it is not evidence of a firmware fault. A new launch verifies the sealed bundle and its local app files, without replaying the large historical flash traces.

## UI smoke procedure for the operator

Use actual clicks/keyboard events and read back the resulting firmware state. Do not invoke mutation functions directly or assign hidden editor state.

1. Append a Post effect using `#chain .cell.tail > .add`. Open Dynamics with `#menu .mcr[data-cat="dynamics"]`, then choose the actual **Noise Gate** button under `#menuSub`. Read the assigned ID from the new chain block/editor and FXS; do not assume an ID.
2. With that block selected, focus the first `#edKnobs .knob` and press ArrowDown once. Compare its displayed value with the effective FXS parameter. Wait for the original command queue to finish before another action.
3. Click `#edOn` to bypass, verify FXS, then click again to enable if desired. `aria-pressed="true"` means bypassed.
4. Optional persistent FX check: while the effect is still present, open `#presetBtn`, choose bank `#banks [data-bank="0"]`, and save to `#pList [data-preset="1"] [data-a="s"]` only after PLIST confirms slot 1 is free. Preserve the original UI-generated name. Reload with focus on `#pList [data-preset="1"] .n` and Enter, and verify the saved effect/parameter. This creates a real retained preset; it is not a temporary operation or a power-cycle test.
5. Select the effect again and click `#edDel` to remove it from the live chain, then verify that both the chain and FXS no longer contain its ID. Removal from the live chain does not erase a preset saved in step 4.

The initial bundle records `UI_FX_interactions_physically_tested=false` at build time. The subsequent [real UI smoke](MINI_FX_UI.md) passed on 16 November: add, parameter change, bypass, enable, save, remove and reload were observed through the interface and verified against native USB replies. That separate evidence preserves the original bundle qualification.

## Historical launch sources

These hashes identify the original physical-test launch sources at Git revision
`882ccb1`; they do not identify the current English launcher or updated shortcut.

- `tools/launch_mini_fx_editor.py`: `c0371984bbd617a2a5cf54f62e06fc51359d0d9bc8457b569342260b23938381`
- `tools/launch_mini_fx_editor.cmd`: `f417d2a7d9150aee1015c23b298cb61f33365eaa2e7107a1321e49618afa33bc`
- `tests/test_mini_fx_editor_launcher.py`: `93ff416899eedcae2e67c97105849a358c79f96214b0506995abd1123cfffd0a`
- FX qualifier: `63744b846ee08a3c928a91ffa96649e8174d8316c771e6ea50b69daf636a4612`
- Real FX bundle manifest: `a76f3b40825750cf3c52955fc7b36b008ccd75cd140755f9d0ebf7686d249221`

Six focused offline tests and the actual bundle check passed. Independent review found no blocker. The existing volume/preset launcher and bundle remain separate.
