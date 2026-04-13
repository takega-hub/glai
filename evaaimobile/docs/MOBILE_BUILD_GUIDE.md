# EVA AI Mobile App - Build Guide

## Overview

This guide provides comprehensive instructions for building the EVA AI mobile application for both Android and iOS platforms. The application is built using React Native and integrates with the web application for testing and development.

## Prerequisites

### System Requirements

- **Node.js**: >= 22.11.0 (as specified in package.json)
- **npm**: Latest version
- **Git**: For version control
- **React Native CLI**: @react-native-community/cli 20.1.0

### Platform-Specific Requirements

#### Android Development
- **Java Development Kit (JDK)**: Version 17-20
- **Android Studio**: Latest version
- **Android SDK**: API Level 36 (Android 14)
- **Android Build Tools**: 36.0.0
- **Android NDK**: 27.1.12297006

#### iOS Development (macOS only)
- **Xcode**: Latest version
- **CocoaPods**: For dependency management
- **iOS Simulator**: For testing

## Environment Setup

### 1. Clone and Setup

```bash
# Clone the repository
git clone [YOUR_REPOSITORY_URL]
cd evaaimobile

# Install dependencies
npm install

# For iOS (macOS only)
cd ios && pod install && cd ..
```

### 2. Environment Configuration

Create environment files based on your web application configuration:

```bash
# Copy example environment file
cp .env.example .env

# Edit with your web app URLs and API endpoints
nano .env
```

### 3. Verify Setup

Run the React Native doctor to check your environment:

```bash
npx @react-native-community/cli doctor
```

## Android Development

### Environment Setup

1. **Install Android Studio**
   - Download from [Android Studio Official Site](https://developer.android.com/studio)
   - Install with default settings
   - Start Android Studio and complete setup wizard

2. **Configure Android SDK**
   - Open Android Studio → Settings → Appearance & Behavior → System Settings → Android SDK
   - Install Android SDK Platform 36
   - Install Android SDK Build-Tools 36.0.0
   - Install Android SDK Platform-Tools

3. **Set Environment Variables**

   Add to your shell profile (`~/.bashrc`, `~/.zshrc`, or `~/.profile`):

   ```bash
   export ANDROID_HOME=$HOME/Android/Sdk
   export PATH=$PATH:$ANDROID_HOME/emulator
   export PATH=$PATH:$ANDROID_HOME/tools
   export PATH=$PATH:$ANDROID_HOME/tools/bin
   export PATH=$PATH:$ANDROID_HOME/platform-tools
   ```

4. **Install JDK 17-20**
   - Download OpenJDK from [Adoptium](https://adoptium.net/)
   - Set JAVA_HOME environment variable

### Building Android App

#### Development Build

```bash
# Start Metro bundler
npm start

# In a new terminal, run Android build
npm run android
```

#### Production Build

```bash
# Clean build
cd android
./gradlew clean

# Generate release APK
./gradlew assembleRelease

# Generate release AAB (for Play Store)
./gradlew bundleRelease
```

#### Build Outputs

- **APK**: `android/app/build/outputs/apk/release/app-release.apk`
- **AAB**: `android/app/build/outputs/bundle/release/app-release.aab`

### Android Configuration

#### App Signing (Production)

1. **Generate Keystore**
   ```bash
   keytool -genkey -v -keystore my-release-key.keystore -alias my-key-alias -keyalg RSA -keysize 2048 -validity 10000
   ```

2. **Configure Signing**
   - Place keystore in `android/app/`
   - Update `android/app/build.gradle` with signing configuration
   - Set up `~/.gradle/gradle.properties` with passwords

#### Permissions

The app requires these permissions (configured in `android/app/src/main/AndroidManifest.xml`):
- Internet access
- Camera access (for image picker)
- Storage access (for file uploads)

## iOS Development (macOS only)

### Environment Setup

1. **Install Xcode**
   - Download from Mac App Store
   - Install command line tools: `xcode-select --install`

2. **Install CocoaPods**
   ```bash
   sudo gem install cocoapods
   ```

3. **Configure iOS Project**
   ```bash
   cd ios
   pod install
   cd ..
   ```

### Building iOS App

#### Development Build

```bash
# Start Metro bundler
npm start

# In a new terminal, run iOS build
npm run ios
```

#### Production Build

1. **Configure App Signing**
   - Open `ios/evaaimobile.xcworkspace` in Xcode
   - Select your Apple Developer account
   - Configure signing certificates and provisioning profiles

2. **Archive and Export**
   ```bash
   cd ios
   xcodebuild -workspace evaaimobile.xcworkspace -scheme evaaimobile -configuration Release archive -archivePath evaaimobile.xcarchive
   ```

#### Build Outputs

- **IPA**: Generated through Xcode Organizer or command line tools

### iOS Configuration

#### Required Capabilities

Configure in Xcode project settings:
- Associated Domains (for deep linking)
- Camera usage description
- Photo library usage description
- Network access

## Web Application Integration

### API Endpoints

Configure your web application URLs in the environment configuration:

```bash
# Development
REACT_APP_API_URL=http://localhost:3000/api
REACT_APP_WEB_URL=http://localhost:3000

# Production
REACT_APP_API_URL=https://your-domain.com/api
REACT_APP_WEB_URL=https://your-domain.com
```

### Testing Integration

1. **Local Development**
   - Start your web application locally
   - Configure mobile app to point to local web app
   - Test API communication

2. **Staging Environment**
   - Deploy web app to staging server
   - Configure mobile app for staging URLs
   - Test full integration

3. **Production Environment**
   - Deploy web app to production
   - Update mobile app configuration
   - Test production integration

## Testing

### Unit Tests

```bash
# Run all tests
npm test

# Run tests with coverage
npm run test -- --coverage
```

### Integration Tests

```bash
# Android integration tests
npm run android -- --variant=debug

# iOS integration tests
npm run ios -- --configuration=Debug
```

### Device Testing

1. **Physical Devices**
   - Enable USB debugging (Android)
   - Trust developer (iOS)
   - Connect device and run builds

2. **Emulators/Simulators**
   - Android Emulator: Create AVD in Android Studio
   - iOS Simulator: Available in Xcode

## Deployment

### Android Deployment

#### Google Play Store

1. **Prepare Release**
   ```bash
   cd android
   ./gradlew bundleRelease
   ```

2. **Upload to Play Console**
   - Log into [Google Play Console](https://play.google.com/console)
   - Create new release
   - Upload AAB file
   - Fill in release notes

#### Alternative Distribution

- **APK Distribution**: Direct download from web app
- **Firebase App Distribution**: Beta testing
- **Enterprise Distribution**: Internal company distribution

### iOS Deployment

#### App Store

1. **Archive App**
   ```bash
   cd ios
   xcodebuild -workspace evaaimobile.xcworkspace -scheme evaaimobile archive
   ```

2. **Upload to App Store Connect**
   - Use Xcode Organizer or Transporter app
   - Log into [App Store Connect](https://appstoreconnect.apple.com)
   - Create new app version
   - Upload build

#### TestFlight Beta Testing

- Upload build to App Store Connect
- Add testers via TestFlight
- Collect feedback before App Store release

## Troubleshooting

### Common Issues

#### Android Issues

**Build fails with JDK version error**
- Ensure JDK 17-20 is installed
- Set JAVA_HOME correctly
- Restart terminal after setting environment variables

**ADB not found**
- Install Android SDK Platform-Tools
- Add to PATH environment variable
- Restart ADB server: `adb kill-server && adb start-server`

**Build fails with Gradle error**
- Clean build: `./gradlew clean`
- Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Clear Gradle cache: `./gradlew --stop && rm -rf ~/.gradle/caches`

#### iOS Issues

**Pod install fails**
- Update CocoaPods: `sudo gem install cocoapods`
- Update pod repo: `pod repo update`
- Delete `ios/Pods` and reinstall: `rm -rf ios/Pods && cd ios && pod install`

**Xcode build fails**
- Open `.xcworkspace` not `.xcodeproj`
- Clean build folder: `Cmd+Shift+K`
- Reset simulator: Device → Erase All Content and Settings

**Signing issues**
- Check Apple Developer account is valid
- Ensure certificates and provisioning profiles are current
- Verify bundle identifier matches provisioning profile

### Performance Optimization

#### Android Optimization

- Enable ProGuard/R8 for release builds
- Optimize images and assets
- Use Hermes JavaScript engine
- Enable RAM bundle and inline requires

#### iOS Optimization

- Enable bitcode for App Store builds
- Optimize launch screen and assets
- Use Hermes JavaScript engine
- Profile with Xcode Instruments

## Monitoring and Analytics

### Crash Reporting

- **Firebase Crashlytics**: Real-time crash reporting
- **Sentry**: Error tracking and performance monitoring

### Analytics

- **Firebase Analytics**: User behavior tracking
- **Google Analytics**: Web and mobile analytics integration

### Performance Monitoring

- **Firebase Performance**: App performance metrics
- **React Native Performance**: Custom performance tracking

## Security Considerations

### Data Protection

- Encrypt sensitive data in transit and at rest
- Use secure storage for authentication tokens
- Implement proper certificate pinning

### API Security

- Use HTTPS for all API communications
- Implement proper authentication and authorization
- Validate and sanitize all user inputs

### Build Security

- Use code obfuscation for release builds
- Implement anti-tampering measures
- Regular security audits and updates

## Resources and Links

### Official Documentation

- [React Native Official Docs](https://reactnative.dev/)
- [Android Developer Guide](https://developer.android.com/guide)
- [iOS Developer Documentation](https://developer.apple.com/documentation/)

### Development Tools

- [Android Studio](https://developer.android.com/studio)
- [Xcode](https://developer.apple.com/xcode/)
- [React Native Debugger](https://github.com/jhen0409/react-native-debugger)

### Testing and Distribution

- [Google Play Console](https://play.google.com/console)
- [App Store Connect](https://appstoreconnect.apple.com)
- [Firebase Console](https://console.firebase.google.com/)

### Community and Support

- [React Native Community](https://reactnative.dev/community/overview)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/react-native)
- [React Native GitHub](https://github.com/facebook/react-native)

## Support

For issues and questions:
1. Check this documentation first
2. Search existing issues in the repository
3. Create a new issue with detailed information
4. Contact the development team

---

**Last Updated**: $(date +"%Y-%m-%d")
**Version**: 1.0.0
**Maintained By**: EVA AI Development Team