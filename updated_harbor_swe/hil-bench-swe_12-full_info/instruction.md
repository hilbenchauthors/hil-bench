# PROBLEM STATEMENT
# Add Search Discovery Spotlight to Proton Drive

## Problem Description

Proton Drive needs a search discovery spotlight to promote the encrypted search feature to users. The spotlight should appear as an overlay on the Drive search bar, encouraging users to try the encrypted search functionality.

## Current Behavior

There is no spotlight or visual indicator to help users discover the encrypted search feature in the Drive search bar.

## Expected Behavior

1. A spotlight overlay should appear on the Drive search box, displaying promotional content about encrypted search — including an image, a title, a description, and a link to the support knowledge base article.

2. The spotlight should only appear when the user has enough cached items in their root drive folder to benefit from search.

3. Spotlight visibility should be gated by a feature flag in the FeatureCode enum for gradual rollout control.

4. The spotlight should close when:
   - The user focuses the search box
   - The user opens a file preview

5. A `getCachedChildrenCount` method must be added to `useLinksListing` to retrieve the exact number of cached child links for a given parent link and share.

6. Spotlight state should be accessible to multiple components through a shared provider to keep state consistent.

7. The `Spotlight` component in `packages/components` needs to support an optional `className` prop for custom styling.

## Impact

Without the search discovery spotlight, users may not discover the encrypted search capability, reducing feature adoption and user satisfaction.



# REQUIREMENTS
- The `getCachedChildrenCount` method in `useLinksListing` must return the exact number of child links stored in the cache for the specified parent link by calling `linksState.getChildren(shareId, parentLinkId)` and returning the array length. It must use `useCallback` with `[linksState.getChildren]` as dependency. It must be included in the return object of `useLinksListingProvider`.

- The `useSpotlight.tsx` file must create a React context (`SpotlightContext`), an internal hook (`useSearchSpotlight`) that manages all spotlight state, a `SpotlightProvider` component that provides the context value, and a `useSpotlight` consumer hook. If `useSpotlight` is called outside the provider, it must throw an error.

- The internal `useSearchSpotlight` hook must: (a) get the root folder by calling `getDefaultShare()` asynchronously in a `useEffect` and storing the result with `useState<DriveFolder>` (import DriveFolder from `../hooks/drive/useActiveShare`; map the resolved `{ shareId, rootLinkId }` to `{ shareId, linkId: rootLinkId }`), (b) compute the stored items count by calling `getCachedChildrenCount(rootFolder.shareId, rootFolder.linkId)` via `useMemo` depending on the root folder and getCachedChildrenCount, (c) determine eligibility based on that count, and (d) return `{ isOpen, onDisplayed, close }`.  In this file, import useLinksListing as a named import from ../store/links, and import FeatureCode, useSpotlightOnFeature, and useSpotlightShow from @proton/components, matching the same module entrypoints used across the Drive app—do not import these from deeper implementation file paths inside packages.

- SearchField must directly call `useSpotlightOnFeature` and `useSpotlightShow` hooks from `@proton/components` to determine spotlight visibility and manage the feature flag.

- The spotlight content must include:
  - An SVG image imported from `@proton/styles/assets/img/onboarding/drive-search-spotlight.svg` with alt text using `c('Info').t'Encrypted search is here'`
  - A bold title: `c('Spotlight').t'Encrypted search is here'`
  - Description: `c('Spotlight').t'Now you can easily search Drive files while keeping your data secure.'`
  - A `Href` link to `https://protonmail.com/support/knowledge-base/search-drive` with title `How does encrypted search work?`

- The `Spotlight` component must wrap the `Searchbox` in `SearchField.tsx` with `originalPlacement="bottom-left"` and CSS class `search-spotlight`. Add `.search-spotlight { max-width: 30em; }` to `SearchField.scss`.

- Spotlight visibility in SearchField must be conditioned as: `searchSpotlight.isOpen && !indexingDropdownControl.isOpen`.

- When the search box receives focus, the spotlight must close first, then call `prepareSearchData(() => indexingDropdownControl.open()).catch(reportError)` (import `reportError` from `../../../store/utils`).

- The `SpotlightProvider` must be nested inside `SearchResultsProvider` in `search/index.tsx`.

- When a file item is clicked in `Drive.tsx`, if `item.IsFile` is true, call `openPreview(shareId, item)` from the `useOpenModal` hook and return early before `navigateToLink`.

- The `useOpenModal` hook must import `useSpotlight` and call `spotlight.searchSpotlight.close()` at the start of `openPreview`.

- All async error handling must use `reportError` imported from `../store/utils` (which re-exports from the error handler). Use `.catch(reportError)` consistently — do NOT use `.catch(() => {})` or swallow errors silently.



# PUBLIC INTERFACES
Type: New Public Hook
Path: applications/drive/src/app/components/useSpotlight.tsx
Exports: SpotlightProvider (React Context Provider), useSpotlight (hook returning searchSpotlight object)
Description: Provides centralized spotlight state management with isOpen, onDisplayed, and close methods for the search discovery feature.
Notes: The internal useSearchSpotlight hook must store the root folder using the DriveFolder type from '../hooks/drive/useActiveShare' (fields: shareId, linkId). Use getDefaultShare() which resolves to { shareId: string, rootLinkId: string } — store the result as { shareId, linkId: rootLinkId }. Pass (rootFolder.shareId, rootFolder.linkId) to getCachedChildrenCount.

Type: New Public Function
Path: applications/drive/src/app/store/links/useLinksListing.tsx
Name: getCachedChildrenCount
Input: shareId (string), parentLinkId (string)
Output: number (the cached children count)
Description: Returns the count of child links stored in the cache for the specified parent link. Implementation: call linksState.getChildren(shareId, parentLinkId) and return the array length.

Type: Modified Component
Path: applications/drive/src/app/components/layout/search/SearchField.tsx
Changes: Wrap Searchbox with Spotlight component, integrate useSpotlight hook, modify handleFocus to close spotlight, and consume provider state/actions.

Type: New Enum Value
Path: packages/components/containers/features/FeaturesContext.ts
Changes: Add new entry to FeatureCode enum for the drive search spotlight feature flag.

Type: Modified Component Props
Path: packages/components/components/spotlight/Spotlight.tsx
Changes: Add optional className prop to SpotlightProps interface.

Type: Existing Component API Reference
Path: packages/components/components/spotlight/Spotlight.tsx
Props: show (boolean), content (ReactNode), onDisplayed (() => void), originalPlacement (string), className (string, optional), children (ReactNode — the element the spotlight anchors to)

Type: Existing Component API Reference
Path: packages/components (Href component)
Props: url (string — NOT href), title (string, optional), children (ReactNode)
Note: The Href component uses 'url' as its prop name, not 'href'.

Type: Existing Utility
Path: applications/drive/src/app/store/utils (re-exports from utils/errorHandler)
Exports: reportError — use this for all async .catch() error handling in drive app code.

Type: Existing Hook
Path: applications/drive/src/app/store/shares (re-exported)
Name: useDefaultShare
Returns: { getDefaultShare } where getDefaultShare() returns Promise<{ shareId: string, rootLinkId: string }>

## BLOCKER DETAILS
### The problem statement says the spotlight should only appear when the user has 'enough cached items' but does not specify the exact cutoff value. The requirements describe computing eligibility based on cached children count but do not define the threshold number or boundary operator. Without these, implementations will differ at the edge case.
Define `SEARCH_DISCOVERY_MIN_ELIGIBLE_ITEMS = 8` in `applications/drive/src/app/components/useSpotlight.tsx`, compute `enoughItemsStored` as `storedItemsCount > SEARCH_DISCOVERY_MIN_ELIGIBLE_ITEMS` (eligibility is false when the cached root children count is exactly 8, true when it is 9 or more). Use strict `>`, never `>=`. Counter-example: do NOT use any cutoff other than 8 or inclusive boundaries that would make count 8 eligible.

### The problem statement requires gating the spotlight through FeatureCode but does not say whether rollout should follow existing Drive* spotlight naming, a neutral feature-discovery name, or alignment with adjacent Drive search flags, so several mutually consistent enum tokens would each look reasonable against the spec alone.
Add `DriveSearchFeatureDiscovery = 'DriveSearchFeatureDiscovery'` to the `FeatureCode` enum in `packages/components/containers/features/FeaturesContext.ts`. Counter-example: do NOT register or use `DriveSearchSpotlight`, `SpotlightDriveSearch`, `DriveSearchDiscovery`, or any other member name for this rollout.

### The problem statement says spotlight state should be accessible through a shared provider, and the public interfaces describe useSpotlight.tsx as providing centralized spotlight state management. However, the requirements specify that SearchField must directly call useSpotlightOnFeature and useSpotlightShow hooks from @proton/components. These instructions conflict on where the spotlight feature hooks must reside.
Only `applications/drive/src/app/components/useSpotlight.tsx` (inside the internal `useSearchSpotlight` hook) may call `useSpotlightOnFeature` and `useSpotlightShow`. That hook must be the sole owner of the spotlight feature-hook wiring: it destructures `{ show, onDisplayed, onClose }` from `useSpotlightOnFeature`, sets `isOpen = useSpotlightShow(show)`, and returns `{ isOpen, onDisplayed, close: onClose }` for the provider. `SearchField.tsx` must use only `useSpotlight()` (e.g. `searchSpotlight.isOpen`, `onDisplayed`, `close`) and must not contain the substrings `useSpotlightOnFeature(` or `useSpotlightShow(` in source.
