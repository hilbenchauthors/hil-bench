# PROBLEM STATEMENT

### Title
Decouple payment token verification from token creation

### Description
The current payment-token flow mixes token creation with modal-based verification inside `createPaymentToken`. That coupling makes the flow harder to reuse across payment surfaces, harder to test in isolation, and harder to adapt when a caller wants to prepare verification behavior ahead of time.

### Current Behavior
`createPaymentToken` receives `createModal`, renders `PaymentVerificationModal` directly, and manages the verification lifecycle itself. Consumers therefore depend on one embedded verification experience and cannot pre-bind or swap the verification strategy.

### Expected Behavior
The verification step should be extracted behind reusable helpers so that `createPaymentToken` no longer owns modal creation. Token creation should interpret the initial tokenization response and delegate follow-up verification work to an injected callback when additional work is required.

The refactor should preserve the status-driven payment-token flow:
- immediately usable tokenization results should resolve as a `TokenPaymentMethod` without extra verification UI.
- tokenization results that are not immediately usable should continue through the injected verification callback using the verification payload.
- terminal payment-token failures should surface without launching or leaving behind stale verification UI.

The default verification implementation should continue to use `PaymentVerificationModal` and preserve the existing redirect/polling behavior through the `process` flow.



# REQUIREMENTS

- A new constant named `verify` should be defined in `PaymentStep`, `PayInvoiceModal`, `CreditsModal`, `EditCardModal`, and `SubscriptionModal` by calling `getDefaultVerifyPayment` with the local modal/API dependencies.

- A new constant named `createPaymentToken` should be defined in those same consumers by calling `getCreatePaymentToken(verify)`.

- The direct `createModal` argument should be removed from the object passed to `createPaymentToken` in those updated consumers.

- The existing `createPaymentToken` function in `paymentTokenHelper.tsx` must be refactored in-place: remove `createModal` from its destructured parameter object and add `verify: VerifyPayment` in its place. The refactored `createPaymentToken` keeps its full implementation body (status checks, `fetchPaymentToken` call, `verify` call) and remains a standalone exported function.

- The logic that renders `PaymentVerificationModal` and wires its handlers should be removed from inside `createPaymentToken`.

- When verification is required, `createPaymentToken` should call `verify` with a single object containing `mode`, `Payment`, `Token`, `ApprovalURL`, and `ReturnHost`.

- The refactor must continue to support flows where no new card payload is available before verification begins. The internal `Payment` variable in `createPaymentToken` must be declared as `CardPayment | undefined` (not just `CardPayment`), because `isExistingPayment(params)` paths leave `Payment` uninitialized.

- A new function named `getCreatePaymentToken` should be defined in `paymentTokenHelper.tsx`; it accepts a `verify` parameter of type `VerifyPayment` and returns a thin currying wrapper that internally calls `createPaymentToken({ verify, mode, api, params }, amountAndCurrency?)` — it must NOT duplicate the implementation; it simply pre-binds the `verify` argument and delegates to the existing `createPaymentToken`.

- A new type alias named `VerifyPayment` should be defined to represent a function that receives an object with the properties `mode`, `Payment`, `Token`, `ApprovalURL`, and `ReturnHost`, and returns a `Promise<TokenPaymentMethod>`.

- A new function named `getDefaultVerifyPayment` should be defined to return a `VerifyPayment` implementation backed by `PaymentVerificationModal`.

- The `getDefaultVerifyPayment` implementation should internally define the verification callback, create a `PaymentVerificationModal`, and connect the verification lifecycle to the asynchronous verification process through an `AbortController`.

- The extracted default verifier should preserve the existing verification experience while remaining compatible with deterministic timer-based tests.

- Any tokenization response that does not yield STATUS_CHARGEABLE must be forwarded to `verify` so the verification callback governs all non-chargeable outcomes, including terminal failure statuses.

- All user-facing error messages in payment helpers must use the `c('Error').t` internationalization pattern (e.g. `throw new Error(c('Error').t`descriptive message`)`).

- The verification flow should continue using `process` to perform redirect handling and status polling until the flow resolves, is cancelled, or reaches a terminal state.

- The refactoring must not change `usePayPal` or any non-payment-token verification flow.

- The five consumer files that must be updated are: `applications/account/src/app/signup/PaymentStep.tsx`, `packages/components/containers/invoices/PayInvoiceModal.tsx`, `packages/components/containers/payments/CreditsModal.tsx`, `packages/components/containers/payments/EditCardModal.tsx`, `packages/components/containers/payments/subscription/SubscriptionModal.tsx`. Each consumer must import `getDefaultVerifyPayment` and `getCreatePaymentToken` (not `createPaymentToken` directly), define `const verify = getDefaultVerifyPayment(createModal, api)` and `const createPaymentToken = getCreatePaymentToken(verify)`, and remove `createModal` from the call-site argument object.



# PUBLIC INTERFACES

- Path: `packages/components/containers/payments/paymentTokenHelper.tsx`
- Name: `VerifyPayment`
- Type: type
- Input: `params: { mode?: 'add-card'; Payment?: CardPayment; Token: string; ApprovalURL?: string; ReturnHost?: string }`
- Output: `Promise<TokenPaymentMethod>`
- Description: Public type alias representing the verification callback used by `createPaymentToken`. Implementations receive the token verification payload and must resolve to a `TokenPaymentMethod`.

- Path: `packages/components/containers/payments/paymentTokenHelper.tsx`
- Name: `getCreatePaymentToken`
- Type: function
- Input: `verify: VerifyPayment`
- Output: `(args: { mode?: 'add-card'; api: Api; params: WrappedCardPayment | TokenPaymentMethod | ExistingPayment }, amountAndCurrency?: AmountAndCurrency) => Promise<TokenPaymentMethod>`
- Description: Public factory function that returns a specialized `createPaymentToken` wrapper bound to a verification implementation. The returned function forwards token-creation requests using the provided verification strategy.

- Path: `packages/components/containers/payments/paymentTokenHelper.tsx`
- Name: `getDefaultVerifyPayment`
- Type: function
- Input: `createModal: (modal: JSX.Element) => void`, `api: Api`
- Output: `VerifyPayment`
- Description: Public factory that creates the default verification handler used for payment token verification flows. It returns an async verification function that opens a `PaymentVerificationModal`, resolves with a `TokenPaymentMethod` when verification succeeds, and rejects when the verification flow closes or fails. Internally it coordinates the redirect and polling process using the provided modal and API dependencies.

## BLOCKER DETAILS
### The extracted default card verifier must decide whether verification should begin automatically when the modal mounts or wait for an explicit user action, but the task never specifies the exact startup parameterization for `PaymentVerificationModal`. What launch policy and `initialProcess` value should the default verifier use?
Start verification only from the modal submit path: pass `onProcess` and OMIT `initialProcess` entirely. The modal must not auto-start the process on mount — do NOT pass `initialProcess` at all (not even as `undefined`). The `onProcess` callback should create a new `AbortController`, start the redirect/polling flow using the controller's signal, and return an object `{ promise, abort }` where `promise` is the process result and `abort` is the controller. This ensures timer-driven test determinism because the process only starts when the user explicitly submits.

### The requirements state that `createPaymentToken` should call `verify` with an object containing `ApprovalURL` and `ReturnHost`, and that `getDefaultVerifyPayment` should create a `PaymentVerificationModal`. However, neither the problem statement nor the requirements define whether `ApprovalURL` and `ReturnHost` should be passed as props on `PaymentVerificationModal` or kept private to the verifier's internal `process` call. Choosing the wrong ownership boundary changes both the extracted interface and downstream coupling.
Keep `ApprovalURL` and `ReturnHost` private to the verifier/process boundary and do NOT add them as `PaymentVerificationModal` props. The modal should only receive display-oriented props: `mode`, `payment` (the CardPayment object), and `token` (the Token string). The redirect metadata is consumed exclusively within the verifier's internal call to `process({ Token, api, ReturnHost, ApprovalURL, signal })`, not forwarded to the modal component. Do NOT write `<PaymentVerificationModal ApprovalURL={ApprovalURL} ReturnHost={ReturnHost} ... />`.

### The problem statement specifies that terminal payment-token failures should surface without launching or leaving behind stale verification UI. The requirements state that any tokenization response that does not yield STATUS_CHARGEABLE must be forwarded to `verify` so the verification callback governs all non-chargeable outcomes, including terminal failure statuses. These instructions directly conflict regarding how terminal statuses such as STATUS_FAILED and STATUS_CONSUMED should be handled.
Use this exact status partition inside `createPaymentToken`, after the `STATUS_CHARGEABLE` early return and before calling `verify`: (1) if `Status === STATUS_FAILED`, throw `new Error(c('Error').t`Payment process failed`)`. (2) if `Status === STATUS_CONSUMED`, throw `new Error(c('Error').t`Payment process consumed`)`. (3) if `Status === STATUS_NOT_SUPPORTED`, throw `new Error(c('Error').t`Payment process not supported`)`. (4) if `Status !== STATUS_PENDING`, throw `new Error(c('Error').t`Unknown payment token status`)`. Only after all these guards should `createPaymentToken` call `return verify({ mode, Payment, Token, ApprovalURL, ReturnHost })`. Terminal statuses must never reach `verify`.
