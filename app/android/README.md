# HyperRig for Android

This project packages the HyperRig editor for Bluetooth use on Android. The files in `www` come from the installed Windows editor; their notices are included here. Firmware installation and USB are not supported by this build.

Install Node.js, JDK 21 and Android SDK platform 36 and build tools 36.0.0, then run:

```
npm ci
npx cap sync android
cd android
gradlew assembleDebug
```

The debug APK is at `android/app/build/outputs/apk/debug/app-debug.apk`. Enable Bluetooth and hold A and B on the pedal for three seconds to allow pairing.
