# HyperRig for Android

The Android project uses the editor bundle produced by `tools/build_mini_dev_editor.py`.
Generated web files are not kept in the repository. Firmware installation and USB are not supported.

With Node.js 22 or newer, JDK 21, Android SDK platform 36 and build-tools 36.0.0 installed:

```
python tools/build_android_editor.py --bundle build/release-parts/editor --output build/android-editor --tone3000-key PATH_TO_KEY
```

The debug APK is at `build/android-editor/android/app/build/outputs/apk/debug/app-debug.apk`.
Enable Bluetooth and hold A and B on the pedal for three seconds to allow pairing.
The key file contains only the TONE3000 publishable key (`t3k_pub_...`); secret keys are refused.
Omit the option to build without TONE3000. The key is included in the APK. The mobile Select flow
uses Chrome Custom Tabs with PKCE and the callback `com.hyperrig.editor://tone3000/callback`; this
redirect URI must be allowed for the key if its TONE3000 client has a redirect allowlist. Tokens stay
in memory and are forgotten when the app process ends. The browser's own sign-in may remain.

The build applies a checked Android adapter to the bundle's TONE3000 script; all other editor files
are kept byte for byte. To check an existing APK against its editor and key, run:

```
python tools/build_android_editor.py --bundle build/release-parts/editor --check PATH_TO_APK --tone3000-key PATH_TO_KEY
python -m unittest tests.test_android_builder
node app/android/test-tone3000.cjs
```
