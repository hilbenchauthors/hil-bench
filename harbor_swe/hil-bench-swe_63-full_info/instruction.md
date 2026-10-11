# PROBLEM STATEMENT
**Title: Display SmartBanner on all mobile browsers for Proton Mail and Proton Calendar**

**Description**

The Proton Mail and Proton Calendar web clients currently do not consistently display a promotional banner ("SmartBanner") on Android and iOS mobile browsers. Today, the banner's download-link flow is still coupled to product-specific setup, and differences in that setup have led to inconsistent behavior between the two products and across mobile contexts. The goal of this task is to make the SmartBanner behave consistently for Proton Mail and Proton Calendar on supported mobile devices. The fix may require updates in both the runtime banner flow and any product-specific Mail/Calendar setup that currently participates in that flow.

**Expected Behavior**

- The SmartBanner should be visible to users accessing from supported mobile browsers (Android/iOS) if they have not previously used a Proton native mobile app.
- The banner should not be displayed if it is detected that the user has already used a Proton native mobile app.
- Promoted links in the banner must correctly redirect to the corresponding store (Google Play or App Store), depending on the product and platform used.
- The SmartBanner component may be useful for other Proton applications that have a mobile counterpart in the future.
- The show/hide decision should be driven only by the explicit eligibility rules of this task; legacy browser- or version-specific heuristics outside those rules must not independently suppress the banner.


# REQUIREMENTS
- The `SmartBanner` component must accept a prop named `app` of type `SmartBannerApp`, which identifies whether the banner corresponds to Proton Mail or Proton Calendar.
- The `SmartBannerApp` type must be defined as a union of `APPS.PROTONCALENDAR` and `APPS.PROTONMAIL`.
- The banner must only be displayed if the detected operating system is Android or iOS. Devices running any other operating system must not render the banner.
- The banner should only appear in mobile contexts where tapping "Download" is expected to open the relevant app store reliably.
- The banner must not be rendered for a given product if the user has previously used that same product's native mobile application, as determined from the user's settings.
- For this iteration, keep the implementation close to the existing SmartBanner integration in each product and avoid broad architectural changes outside the component flow itself. Reuse the current per-product store-link setup, and ensure the links still point to the correct store for the corresponding product and platform.
- The `SmartBanner` component must be integrated into the Calendar app's main view. Specifically, it must be rendered inside the `TopBanners` component in `CalendarContainerView`. (The Mail app already renders the SmartBanner inside the TopBanners component in PrivateLayout.)
- The logic that determines whether the banner should be rendered must combine both the OS check and the native app usage check. The banner must only be shown if the device is running Android or iOS and the user has not previously used the native mobile app for the same product identified by the `app` prop.
- Do not add extra browser-specific or OS-version-specific suppression rules.
- The file `useSmartBanner.ts` should return either a store URL string or null. It should return a URL only when the device is on a supported mobile platform and the user has not previously used the same product's native mobile app.
- Should determine prior native-app usage by consulting user setting indicators. If usage is detected, the hook should return null.
- The file should provide the correct store link using the existing per-product setup for the corresponding platform and product.
- Any product-specific setup cleanup that this task requires must be scoped to Mail and Calendar template setup only. 
- The file should render nothing when the hook returns null. When the hook returns a URL, it should render a link/button whose accessible name is "Download" and whose href is exactly that URL.
- The file `types.d.ts` should export a `SmartBannerApp` type defined as `APPS.PROTONCALENDAR | APPS.PROTONMAIL`. This type should be used for the `app` prop in SmartBanner.tsx, for the argument in useSmartBanner.ts, and for the parameter in useSmartBannerTelemetry.ts.



# PUBLIC INTERFACES
No new public interface files are introduced in this task.

## BLOCKER DETAILS
### The problem statement says the current SmartBanner download-link flow is coupled to product-specific setup and that the fix should make Mail and Calendar behave consistently even if the two products do not expose identical setup today. However, the requirements also say that, for this iteration, the developer should keep the implementation close to the existing SmartBanner integration in each product and should reuse the current per-product store-link setup where possible. These directives conflict: the problem statement pushes toward making the behavior consistent across products despite their setup differences, while the requirements push toward preserving the current per-product integration approach instead of unifying the source of truth.
Do NOT use the metadata-based runtime approach (`document.querySelector`). Instead, use `MAIL_MOBILE_APP_LINKS` for Proton Mail and `CALENDAR_MOBILE_APP_LINKS` for Proton Calendar, both imported from `@proton/shared/lib/constants`. Access the `playStore` property for Android devices and the `appStore` property for iOS devices. Build a mapping object keyed by app name to look up the correct link set, then index by `isAndroid ? 'playStore' : 'appStore'`.

### The problem statement says the fix may require changes in product-specific Mail/Calendar setup that currently participates in the SmartBanner flow, but it does not identify which concrete setup artifacts those are. 
Product-specific setup changes must target exactly these two files: `applications/mail/src/app.ejs` and `applications/calendar/src/app.ejs`. In `applications/mail/src/app.ejs`, remove exactly these two meta tags: `<meta name=\"apple-itunes-app\" content=\"app-id=979659905\">` and `<meta name=\"google-play-app\" content=\"app-id=ch.protonmail.android\">`. In `applications/calendar/src/app.ejs`, remove exactly this meta tag: `<meta name=\"google-play-app\" content=\"app-id=me.proton.android.calendar\">`.

### The requirements state that the banner should only appear in mobile contexts where tapping 'Download' is expected to open the relevant app store reliably, but they do not define which standalone or PWA contexts satisfy that condition. Multiple valid interpretations exist: suppress the banner in standalone mode on all platforms uniformly, suppress only on platforms where standalone mode is known to break store links, or treat standalone launches as acceptable if the developer believes the store can still be opened. A developer cannot determine from this requirement alone whether standalone mode on Android, iOS, both, or neither should be considered a supported mobile context for showing the banner.
Standalone/PWA mode breaks App Store redirect links on iOS but not on Android. On Android, the intent system can resolve Play Store links even from standalone/PWA contexts, so the banner remains functional. On iOS, standalone WKWebView contexts cannot process universal links to the App Store, so the banner link is non-functional and the banner must be suppressed. The standalone exclusion must apply only on iOS. Do NOT apply the standalone exclusion on Android. Regular iOS browser sessions (including Safari) remain supported contexts for rendering the banner. Do NOT add Safari-specific or iOS-version-based suppression (for example, any `isSafari` + `getOS().version` gating) because that is outside this exclusion.
